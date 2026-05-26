"""
使用 LandPPT 模板生成 PPTX - 集成到 AI 助手
"""


async def create_pptx_from_draft_with_landppt(
    draft: dict,
    template_id: str = "商务"
) -> str:
    """
    使用 LandPPT 模板从草稿生成 PPTX
    
    Args:
        draft: PPT 草稿数据，包含：
            - title: PPT 标题
            - slides: 幻灯片列表，每个包含：
                - title: 页面标题
                - content: 内容列表
                - notes: 演讲备注（可选）
                - layout: 布局类型（可选）
        template_id: 模板 ID（默认：商务）
    
    Returns:
        生成的 PPTX 文件路径
    """
    from services.landppt_renderer import generate_pptx_from_template_id
    from config import settings
    import os
    from utils import get_beijing_time
    
    # 准备幻灯片数据
    slides_data = []
    
    for slide in draft.get("slides", []):
        # 格式化内容
        content = slide.get("content", [])
        
        # 如果内容是列表，保持列表格式
        # 如果需要更复杂的 HTML，可以在这里自定义
        if isinstance(content, list):
            # 转换为 HTML 列表
            content_html = '<ul class="content-points">'
            for item in content:
                content_html += f'<li>{item}</li>'
            content_html += '</ul>'
        else:
            content_html = str(content)
        
        slide_data = {
            "title": slide.get("title", ""),
            "content": content_html
        }
        
        slides_data.append(slide_data)
    
    # 生成输出路径
    upload_dir = os.path.join(settings.UPLOAD_DIR, "ppt")
    os.makedirs(upload_dir, exist_ok=True)
    
    filename = f"{draft.get('title', 'PPT')}_{int(get_beijing_time().timestamp())}.pptx"
    output_path = os.path.join(upload_dir, filename)
    
    # 使用 LandPPT 渲染引擎生成
    result_path = await generate_pptx_from_template_id(
        template_id=template_id,
        slides_data=slides_data,
        output_path=output_path,
        title=draft.get("title", "演示文稿")
    )
    
    return result_path
