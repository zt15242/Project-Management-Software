"""
Gemini Image API 集成模块
用于生成高质量的 PPT 页面图片 (基于 Imagen 3 / Nano Banana Pro)
"""
import httpx
import base64
import json
from typing import Optional, Dict, Any
from config import settings
import asyncio


class GeminiImageGenerator:
    """Gemini 图片生成器 - 专为 PPT 页面优化"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self.model = settings.GEMINI_IMAGE_MODEL
    
    async def generate_ppt_slide_image(
        self,
        slide_data: Dict[str, Any],
        theme_color: str = "#1e3a8a",
        style: str = "professional",
        aspect_ratio: str = "16:9",
        ai_config: Optional[Dict] = None
    ) -> Optional[bytes]:
        """
        生成单张 PPT 幻灯片图片
        
        Args:
            slide_data: 幻灯片数据 {title, content, layout, image_description}
            theme_color: 主题色
            style: 视觉风格 (professional/creative/minimal/infographic)
            aspect_ratio: 宽高比 (16:9 或 4:3)
            ai_config: AI配置（从数据库获取），包含 api_key 和 base_url
        
        Returns:
            图片的二进制数据 (PNG格式)
        """
        # 优先使用传入的 ai_config，其次使用初始化时的配置，最后使用环境变量
        api_key = None
        base_url = None
        
        if ai_config:
            api_key = ai_config.get("api_key")
            base_url = ai_config.get("base_url")
        
        if not api_key:
            api_key = self.api_key or settings.GEMINI_IMAGE_API_KEY
        
        if not base_url:
            base_url = self.base_url or settings.GEMINI_IMAGE_BASE_URL
        
        if not api_key:
            print("[Gemini Image] API Key 未配置，跳过图片生成")
            return None
        
        # 清理 base_url：移除 /chat/completions 等路径
        if base_url:
            base_url = base_url.strip()
            # 移除结尾的斜杠
            while base_url.endswith('/'):
                base_url = base_url[:-1]
            # 移除常见的路径后缀
            if base_url.endswith('/chat/completions'):
                base_url = base_url[:-len('/chat/completions')]
            if base_url.endswith('/v1'):
                # 保留 /v1
                pass
            
        print(f"[Gemini Image] 清理后的 Base URL: {base_url}")
        
        prompt = self._build_ppt_prompt(slide_data, theme_color, style)
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # 使用 Gemini 2.5 Flash Image API
                # 参考: https://vectorengine.apifox.cn/api-360310637
                
                # 构建请求 URL
                # 格式: /v1beta/models/gemini-2.5-flash-image:generateContent?key=
                url = f"{base_url}beta/models/gemini-2.5-flash-image:generateContent"
                
                # 构建请求体
                payload = {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
                
                print(f"[Gemini Image] 调用图片生成 API: {url}")
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"[Gemini Image] API 响应成功")
                    
                    # 解析响应格式
                    if "candidates" in result and len(result["candidates"]) > 0:
                        candidate = result["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            for part in parts:
                                # 查找 inlineData 中的图片（注意是驼峰命名）
                                if "inlineData" in part:
                                    inline_data = part["inlineData"]
                                    if "data" in inline_data:
                                        # Base64 编码的图片数据
                                        image_base64 = inline_data["data"]
                                        image_bytes = base64.b64decode(image_base64)
                                        print(f"[Gemini Image] 图片生成成功，大小: {len(image_bytes)} bytes")
                                        return image_bytes
                    
                    print(f"[Gemini Image] 响应中未找到图片数据")
                    print(f"[Gemini Image] 响应内容: {str(result)[:300]}")
                else:
                    print(f"[Gemini Image] API 返回状态码: {response.status_code}")
                    print(f"[Gemini Image] 响应内容: {response.text[:300]}")
                
                return None
                
        except Exception as e:
            print(f"[Gemini Image] 生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _build_ppt_prompt(
        self,
        slide_data: Dict[str, Any],
        theme_color: str,
        style: str
    ) -> str:
        """
        构建专业的 PPT 图片生成 Prompt
        参考 banana-slides 的 Prompt 工程
        """
        title = slide_data.get("title", "")
        content = slide_data.get("content", [])
        layout = slide_data.get("layout", "split")
        image_desc = slide_data.get("image_description", "")
        
        # 基础风格定义
        style_templates = {
            "professional": "professional business presentation, clean layout, corporate design",
            "creative": "creative modern design, vibrant colors, dynamic composition",
            "minimal": "minimalist design, lots of white space, elegant typography",
            "infographic": "infographic style, data visualization, modern flat design"
        }
        
        base_style = style_templates.get(style, style_templates["professional"])
        
        # 布局特定的 Prompt（使用中文）
        layout_prompts = {
            "split": f"""
请创建一个专业的 16:9 PPT 幻灯片，采用左右分栏布局：
- 左侧：标题 "{title}"（使用主题色 {theme_color}）
- 左侧：要点列表（清晰的层次结构）：
{self._format_bullet_points(content)}
- 右侧：{image_desc or '相关的专业插图'}
- 设计风格：{base_style}，高对比度文字，易读字体
- 质量要求：4K 分辨率，文字清晰，专业间距

重要：所有文字必须使用中文，字体使用中文字体（如思源黑体、微软雅黑）
""",
            "full": f"""
请创建一个震撼的全屏 16:9 PPT 幻灯片：
- 背景：沉浸式图片 - {image_desc or '抽象专业背景'}
- 中心：大号粗体标题 "{title}"（白色或浅色）
- 叠加层：半透明深色渐变，确保文字可读性
- 设计风格：{base_style}，电影级构图，高冲击力
- 质量要求：4K 分辨率，文字完美清晰

重要：所有文字必须使用中文，字体使用中文字体
""",
            "triple": f"""
请创建一个现代的 16:9 PPT 幻灯片，采用三列布局：
- 顶部：居中标题 "{title}"（使用主题色 {theme_color}）
- 三列：三个等宽卡片，带毛玻璃效果（glassmorphism）
- 内容：{self._format_triple_content(content)}
- 设计风格：{base_style}，现代 UI，柔和阴影
- 质量要求：4K 分辨率，清晰字体

重要：所有文字必须使用中文，字体使用中文字体
""",
            "infographic": f"""
请创建一个专业的 16:9 信息图表风格 PPT 幻灯片：
- 左侧：视觉插图 - {image_desc or '现代信息图表插图'}
- 右侧：标题 "{title}" 和结构化内容：
{self._format_bullet_points(content)}
- 设计风格：{base_style}，数据驱动，专业图表
- 质量要求：4K 分辨率，精确的文字渲染

重要：所有文字必须使用中文，字体使用中文字体（如思源黑体）
""",
            "big_number": f"""
请创建一个有冲击力的 16:9 PPT 幻灯片，聚焦核心指标：
- 顶部：小标题 "{title}"
- 中心：超大数字 "{content[0] if content else '0'}"（使用颜色 {theme_color}）
- 背景：柔和渐变或图案
- 设计风格：{base_style}，极简主义，高对比度
- 质量要求：4K 分辨率，粗体字体

重要：所有文字必须使用中文，字体使用中文字体
"""
        }
        
        prompt = layout_prompts.get(layout, layout_prompts["split"])
        
        # 添加通用质量要求（中文）
        prompt += f"""

关键要求：
- 文字必须完美清晰可读
- 使用专业的中文字体（如思源黑体、微软雅黑、苹方）
- 保持一致的配色方案，使用 {theme_color} 作为强调色
- 确保文字与背景之间有高对比度
- 专业的间距和对齐
- 16:9 宽高比（1920x1080 或 2048x1152）
- 照片级真实质量，细节清晰
- 所有文字内容必须使用简体中文
"""
        
        return prompt.strip()
    
    def _format_bullet_points(self, content: list) -> str:
        """格式化内容为 Prompt 中的要点"""
        if not content:
            return "  • Sample point 1\n  • Sample point 2"
        return "\n".join([f"  • {point}" for point in content[:5]])
    
    def _format_triple_content(self, content: list) -> str:
        """格式化三列内容"""
        if not content:
            return "Column 1 | Column 2 | Column 3"
        items = content[:3]
        while len(items) < 3:
            items.append("Additional point")
        return " | ".join(items)


# 全局单例
_image_generator = None

def get_image_generator() -> GeminiImageGenerator:
    """获取图片生成器单例"""
    global _image_generator
    if _image_generator is None:
        _image_generator = GeminiImageGenerator()
    return _image_generator
