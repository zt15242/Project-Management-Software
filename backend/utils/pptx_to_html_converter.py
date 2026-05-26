"""
PPTX 转 HTML 模板转换器
将上传的 PPTX 文件转换为可用的 HTML 模板
"""
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.dml.color import RGBColor
import os
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PPTXToHTMLConverter:
    """PPTX 到 HTML 模板转换器"""
    
    def __init__(self, pptx_path: str):
        """
        初始化转换器
        
        Args:
            pptx_path: PPTX 文件路径
        """
        self.pptx_path = pptx_path
        self.prs = Presentation(pptx_path)
        
        # 获取幻灯片尺寸
        self.slide_width = self.prs.slide_width
        self.slide_height = self.prs.slide_height
        
        # 转换为像素（假设 96 DPI）
        self.width_px = int(self.slide_width.inches * 96)
        self.height_px = int(self.slide_height.inches * 96)
        
        logger.info(f"PPTX 尺寸: {self.width_px}x{self.height_px}")
    
    def _rgb_to_hex(self, rgb_color) -> str:
        """将 RGBColor 转换为十六进制颜色"""
        try:
            if hasattr(rgb_color, 'rgb'):
                r, g, b = rgb_color.rgb
                return f"#{r:02x}{g:02x}{b:02x}"
            return "#000000"
        except:
            return "#000000"
    
    def _extract_background_color(self) -> str:
        """提取背景颜色"""
        try:
            # 尝试从第一张幻灯片提取背景
            if len(self.prs.slides) > 0:
                slide = self.prs.slides[0]
                if hasattr(slide, 'background'):
                    fill = slide.background.fill
                    if hasattr(fill, 'fore_color'):
                        return self._rgb_to_hex(fill.fore_color)
            return "#ffffff"
        except:
            return "#ffffff"
    
    def _extract_text_styles(self) -> Dict[str, Any]:
        """提取文本样式"""
        styles = {
            "title": {
                "font_size": "48px",
                "font_weight": "bold",
                "color": "#333333"
            },
            "body": {
                "font_size": "24px",
                "font_weight": "normal",
                "color": "#666666"
            }
        }
        
        try:
            # 从第一张幻灯片提取样式
            if len(self.prs.slides) > 0:
                slide = self.prs.slides[0]
                
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        text_frame = shape.text_frame
                        if len(text_frame.paragraphs) > 0:
                            para = text_frame.paragraphs[0]
                            if len(para.runs) > 0:
                                run = para.runs[0]
                                font = run.font
                                
                                # 提取字体大小
                                if font.size:
                                    font_size_pt = font.size.pt
                                    
                                    # 判断是标题还是正文
                                    if font_size_pt > 30:
                                        styles["title"]["font_size"] = f"{int(font_size_pt)}px"
                                        if font.color and hasattr(font.color, 'rgb'):
                                            styles["title"]["color"] = self._rgb_to_hex(font.color)
                                    else:
                                        styles["body"]["font_size"] = f"{int(font_size_pt)}px"
                                        if font.color and hasattr(font.color, 'rgb'):
                                            styles["body"]["color"] = self._rgb_to_hex(font.color)
        except Exception as e:
            logger.warning(f"提取文本样式失败: {e}")
        
        return styles
    
    def _extract_layout_info(self) -> Dict[str, Any]:
        """提取布局信息"""
        layout_info = {
            "padding": "60px",
            "title_position": "top",
            "content_position": "center"
        }
        
        try:
            if len(self.prs.slides) > 0:
                slide = self.prs.slides[0]
                
                # 分析形状位置
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        # 计算相对位置
                        left_percent = (shape.left / self.slide_width) * 100
                        top_percent = (shape.top / self.slide_height) * 100
                        
                        # 根据位置判断是标题还是内容
                        if top_percent < 20:
                            layout_info["title_position"] = "top"
                        elif top_percent > 50:
                            layout_info["content_position"] = "bottom"
        except Exception as e:
            logger.warning(f"提取布局信息失败: {e}")
        
        return layout_info
    
    def convert_to_html_template(self) -> str:
        """
        将 PPTX 转换为 HTML 模板
        
        Returns:
            HTML 模板字符串
        """
        # 提取样式信息
        bg_color = self._extract_background_color()
        text_styles = self._extract_text_styles()
        layout_info = self._extract_layout_info()
        
        # 生成 HTML 模板
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{{{ page_title }}}}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        html {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #111827;
        }}
        
        body {{
            width: {self.width_px}px;
            height: {self.height_px}px;
            margin: 0;
            padding: {layout_info['padding']};
            background-color: {bg_color};
            font-family: 'Microsoft YaHei', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
            position: relative;
            overflow: hidden;
            flex-shrink: 0;
        }}
        
        .slide-container {{
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
        }}
        
        .slide-header {{
            margin-bottom: 40px;
        }}
        
        .slide-title {{
            font-size: {text_styles['title']['font_size']};
            font-weight: {text_styles['title']['font_weight']};
            color: {text_styles['title']['color']};
            margin: 0;
            line-height: 1.2;
        }}
        
        .slide-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            overflow: hidden;
        }}
        
        .content-main {{
            font-size: {text_styles['body']['font_size']};
            line-height: 1.6;
            color: {text_styles['body']['color']};
        }}
        
        .content-main ul {{
            list-style: none;
            padding: 0;
        }}
        
        .content-main li {{
            margin-bottom: 15px;
            padding-left: 30px;
            position: relative;
        }}
        
        .content-main li:before {{
            content: "▶";
            position: absolute;
            left: 0;
            color: {text_styles['title']['color']};
            font-size: 0.8em;
        }}
        
        .slide-footer {{
            position: absolute;
            bottom: 30px;
            right: 40px;
            font-size: 18px;
            color: #94a3b8;
            font-weight: 600;
        }}
        
        /* 响应式调整 */
        @media (max-width: {self.width_px}px) {{
            body {{
                width: 100vw;
                height: {(self.height_px / self.width_px) * 100}vw;
                max-height: 100vh;
            }}
        }}
    </style>
</head>
<body>
    <div class="slide-container">
        <div class="slide-header">
            <h1 class="slide-title">{{{{ main_heading }}}}</h1>
        </div>
        
        <div class="slide-content">
            <div class="content-main">
                {{{{ page_content }}}}
            </div>
        </div>
        
        <div class="slide-footer">
            {{{{ current_page_number }}}} / {{{{ total_page_count }}}}
        </div>
    </div>
</body>
</html>"""
        
        return html_template
    
    def extract_template_info(self) -> Dict[str, Any]:
        """
        提取模板信息（用于显示）
        
        Returns:
            模板信息字典
        """
        info = {
            "slide_count": len(self.prs.slides),
            "width": self.width_px,
            "height": self.height_px,
            "aspect_ratio": f"{self.width_px}:{self.height_px}",
            "background_color": self._extract_background_color(),
            "text_styles": self._extract_text_styles()
        }
        
        return info


def convert_pptx_to_html_template(pptx_path: str) -> Tuple[str, Dict[str, Any]]:
    """
    将 PPTX 文件转换为 HTML 模板
    
    Args:
        pptx_path: PPTX 文件路径
    
    Returns:
        (HTML 模板字符串, 模板信息字典)
    """
    converter = PPTXToHTMLConverter(pptx_path)
    html_template = converter.convert_to_html_template()
    template_info = converter.extract_template_info()
    
    return html_template, template_info


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) > 1:
        pptx_file = sys.argv[1]
        
        if os.path.exists(pptx_file):
            html, info = convert_pptx_to_html_template(pptx_file)
            
            print("=" * 60)
            print("模板信息:")
            print(f"  幻灯片数量: {info['slide_count']}")
            print(f"  尺寸: {info['width']}x{info['height']}")
            print(f"  背景颜色: {info['background_color']}")
            print("=" * 60)
            print("\nHTML 模板:")
            print(html)
            
            # 保存到文件
            output_file = pptx_file.replace('.pptx', '_template.html')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"\n✅ HTML 模板已保存到: {output_file}")
        else:
            print(f"❌ 文件不存在: {pptx_file}")
    else:
        print("用法: python pptx_to_html_converter.py <pptx_file>")
