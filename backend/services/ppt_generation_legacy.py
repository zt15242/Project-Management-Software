"""
Legacy PPT Generation Service (Migrated from ai_assistant.py)
Used as a fallback when LandPPT engine fails.
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from database import get_database
from utils import get_beijing_time
from utils.gemini_image import get_image_generator
import os
import io
import requests
from config import settings

async def get_active_ai_config(db):
    """获取激活的AI配置"""
    config = await db.ai_configs.find_one({"is_enabled": True})
    return config

async def create_pptx_from_draft(draft: dict) -> str:
    """
    高端 PPT 生成引擎：支持模板美化、自动配图、多页布局渲染
    """
    prs = Presentation()
    theme = draft.get("theme", "business_blue")
    
    # --- 1. 定义主题视觉规范 ---
    theme_colors = {
        "business_blue": (RGBColor(30, 58, 138), RGBColor(239, 246, 255)),
        "tech_dark": (RGBColor(15, 23, 42), RGBColor(30, 41, 59)),
        "clean_white": (RGBColor(0, 0, 0), RGBColor(255, 255, 255)),
        "vibrant_orange": (RGBColor(249, 115, 22), RGBColor(255, 247, 237)),
        "nature_green": (RGBColor(21, 128, 61), RGBColor(240, 253, 244)),
        "warm_red": (RGBColor(220, 38, 38), RGBColor(254, 242, 242))
    }
    accent_color, bg_accent = theme_colors.get(theme, (RGBColor(37, 99, 235), RGBColor(255,255,255)))
    
    # 获取 AI 配置（用于图片生成）
    db = get_database()
    ai_config = await db.ai_configs.find_one({"is_enabled": True})

    def apply_slide_template(slide, is_cover=False):
        """为幻灯片添加装饰性背景元素"""
        if is_cover:
            # 封面添加大块色块或装饰
            shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
            shape.fill.solid()
            shape.fill.fore_color.rgb = bg_accent
            shape.line.width = 0
            
            # 装饰线条
            line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.5), Inches(0.1), Inches(3))
            line.fill.solid()
            line.fill.fore_color.rgb = accent_color
            line.line.width = 0
        else:
            # 普通页顶部边框和页码装饰
            header_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.05))
            header_bar.fill.solid()
            header_bar.fill.fore_color.rgb = accent_color
            header_bar.line.width = 0

    async def get_smart_image(query, slide_data=None, theme_color="#1e3a8a"):
        """获取高质量图片 - 优先使用 Gemini Image API"""
        print(f"[DEBUG] get_smart_image 被调用: query={query}, slide_data={slide_data is not None}, ai_config={ai_config is not None}")
        try:
            # 尝试使用 Gemini Image API 生成专业PPT页面图片
            if slide_data and ai_config:
                print(f"[DEBUG] 准备调用 Gemini Image API")
                image_gen = get_image_generator()
                image_bytes = await image_gen.generate_ppt_slide_image(
                    slide_data=slide_data,
                    theme_color=theme_color,
                    style="professional",
                    ai_config=ai_config  # 传入 AI 配置
                )
                if image_bytes:
                    return io.BytesIO(image_bytes)
            else:
                print(f"[DEBUG] 跳过 Gemini Image API: slide_data={slide_data is not None}, ai_config={ai_config is not None}")
        except Exception as e:
            print(f"[Gemini Image] 生成失败，降级为 Unsplash: {str(e)}")
        
        # 降级方案：使用 Unsplash
        try:
            import requests
            img_res = requests.get(f"https://source.unsplash.com/featured/800x600?{query}", timeout=5)
            if img_res.status_code == 200:
                return io.BytesIO(img_res.content)
        except:
            pass
        return None

    # --- 2. 渲染封面 ---
    title_layout = prs.slide_layouts[6] # 使用空白布局自己画
    slide = prs.slides.add_slide(title_layout)
    apply_slide_template(slide, is_cover=True)
    
    # 标题文字
    tx_box = slide.shapes.add_textbox(Inches(1), Inches(1.5), Inches(8), Inches(2))
    tf = tx_box.text_frame
    tf.text = draft.get("title", "项目演示文稿")
    p = tf.paragraphs[0]
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = accent_color
    
    # 副标题
    tx_sub = slide.shapes.add_textbox(Inches(1), Inches(3.5), Inches(8), Inches(1))
    tf_sub = tx_sub.text_frame
    tf_sub.text = f"汇报人：AI 助手 | 汇报日期：{get_beijing_time().strftime('%Y-%m-%d')}"
    p_sub = tf_sub.paragraphs[0]
    p_sub.font.size = Pt(18)
    p_sub.font.color.rgb = RGBColor(100, 116, 139)

    # --- 3. 渲染内容页 ---
    for slide_data in draft.get("slides", []):
        slide = prs.slides.add_slide(prs.slide_layouts[6]) # 使用空白布局实现 Side-by-Side
        apply_slide_template(slide)
        
        # 渲染标题
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(1))
        title_tf = title_box.text_frame
        title_tf.text = slide_data.get("title", "章节内容")
        title_p = title_tf.paragraphs[0]
        title_p.font.size = Pt(28)
        title_p.font.bold = True
        title_p.font.color.rgb = accent_color
        
        # 注入演讲备注
        if slide_data.get("notes"):
            slide.notes_slide.notes_text_frame.text = slide_data["notes"]

        # 根据布局渲染内容
        layout = slide_data.get("layout", "split")
        
        if layout == "full":
            # 全图背景布局
            img_desc = slide_data.get("image_description") or slide_data.get("title")
            img_stream = await get_smart_image(img_desc, slide_data=slide_data) # 尝试使用 Gemini 生成
            if img_stream:
                try: 
                    slide.shapes.add_picture(img_stream, 0, 0, width=prs.slide_width)
                except: pass
            
            # 半透明遮罩
            overlay = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
            overlay.fill.solid()
            overlay.fill.fore_color.rgb = RGBColor(0,0,0)
            overlay.fill.transparency = 0.6
            overlay.line.width = 0
            
            # 文字居中
            title_box = slide.shapes.add_textbox(Inches(1), Inches(3), Inches(8), Inches(2))
            title_tf = title_box.text_frame
            title_tf.text = slide_data.get("title", "")
            title_tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            title_tf.paragraphs[0].font.size = Pt(36)
            title_tf.paragraphs[0].font.color.rgb = RGBColor(255,255,255)
            
        elif layout == "triple":
            # 三列布局
            for i, point in enumerate(slide_data.get("content", [])[:3]):
                col_box = slide.shapes.add_textbox(Inches(0.5 + i*3.1), Inches(1.5), Inches(2.8), Inches(4))
                col_tf = col_box.text_frame
                col_tf.word_wrap = True
                p = col_tf.paragraphs[0]
                p.text = str(point)
                p.font.size = Pt(14)
                p.font.color.rgb = RGBColor(71, 85, 105)
        else:
            # 经典的 Split 布局 (左字右图)
            left_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(5), Inches(5))
            left_tf = left_box.text_frame
            left_tf.word_wrap = True
            for point in slide_data.get("content", []):
                p = left_tf.add_paragraph()
                p.text = f"• {str(point)}"
                p.font.size = Pt(16)
            
            img_desc = slide_data.get("image_description")
            if img_desc:
                img_stream = await get_smart_image(img_desc, slide_data=slide_data)
                if img_stream:
                    try: slide.shapes.add_picture(img_stream, Inches(5.8), Inches(1.5), width=Inches(3.7))
                    except: pass

    # --- 4. 保存文件 ---
    upload_dir = os.path.join(settings.UPLOAD_DIR, "ppt")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{draft.get('title', 'PPT')}_{int(get_beijing_time().timestamp())}.pptx"
    filepath = os.path.join(upload_dir, filename)
    prs.save(filepath)
    return filepath
