"""
PPT 模板管理 API - 基于 LandPPT 专业模板
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from database import get_database
from auth import get_current_active_user
from models import UserResponse
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/ppt/templates", tags=["PPT模板"])


class PPTTemplateResponse(BaseModel):
    """PPT 模板响应"""
    id: str
    template_id: str
    template_name: str
    description: str
    tags: List[str]
    is_default: bool
    is_active: bool
    source: str  # landppt, custom
    created_at: datetime


class PPTTemplateListResponse(BaseModel):
    """模板列表响应"""
    total: int
    templates: List[PPTTemplateResponse]


@router.get("/", response_model=PPTTemplateListResponse)
async def get_templates(
    category: Optional[str] = Query(None, description="按分类筛选"),
    tag: Optional[str] = Query(None, description="按标签筛选"),
    active_only: bool = Query(True, description="仅显示激活的模板"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取所有 PPT 模板"""
    db = get_database()
    
    # 构建查询条件
    query = {}
    if active_only:
        query["is_active"] = True
    if tag:
        query["tags"] = tag
    
    # 查询模板
    cursor = db.ppt_templates.find(query)
    templates = await cursor.to_list(length=None)
    
    # 转换格式
    template_list = []
    for template in templates:
        template_list.append(PPTTemplateResponse(
            id=str(template["_id"]),
            template_id=template["template_id"],
            template_name=template["template_name"],
            description=template.get("description", ""),
            tags=template.get("tags", []),
            is_default=template.get("is_default", False),
            is_active=template.get("is_active", True),
            source=template.get("source", "custom"),
            created_at=template.get("created_at", datetime.now())
        ))
    
    return PPTTemplateListResponse(
        total=len(template_list),
        templates=template_list
    )


@router.get("/default", response_model=PPTTemplateResponse)
async def get_default_template(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取默认模板"""
    db = get_database()
    
    template = await db.ppt_templates.find_one({"is_default": True})
    
    if not template:
        raise HTTPException(status_code=404, detail="未找到默认模板")
    
    return PPTTemplateResponse(
        id=str(template["_id"]),
        template_id=template["template_id"],
        template_name=template["template_name"],
        description=template.get("description", ""),
        tags=template.get("tags", []),
        is_default=True,
        is_active=template.get("is_active", True),
        source=template.get("source", "custom"),
        created_at=template.get("created_at", datetime.now())
    )


@router.get("/{template_id}", response_model=PPTTemplateResponse)
async def get_template(
    template_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取指定模板详情"""
    db = get_database()
    
    template = await db.ppt_templates.find_one({"template_id": template_id})
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return PPTTemplateResponse(
        id=str(template["_id"]),
        template_id=template["template_id"],
        template_name=template["template_name"],
        description=template.get("description", ""),
        tags=template.get("tags", []),
        is_default=template.get("is_default", False),
        is_active=template.get("is_active", True),
        source=template.get("source", "custom"),
        created_at=template.get("created_at", datetime.now())
    )


@router.get("/{template_id}/html")
async def get_template_html(
    template_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取模板的 HTML 内容（用于预览）"""
    db = get_database()
    
    template = await db.ppt_templates.find_one({"template_id": template_id})
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return {
        "template_id": template_id,
        "template_name": template["template_name"],
        "html_template": template.get("html_template", "")
    }


from fastapi import Body
from services.landppt_renderer import LandPPTTemplateRenderer

@router.post("/{template_id}/render-preview")
async def render_preview_slide(
    template_id: str,
    slide_data: dict = Body(..., description="幻灯片数据，包含title, content等"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    渲染单页 PPT 预览
    返回渲染后的 HTML 完整代码，包含内联 CSS
    """
    db = get_database()
    template = await db.ppt_templates.find_one({"template_id": template_id})
    if not template:
        # 尝试查找默认模板
        template = await db.ppt_templates.find_one({"is_default": True})
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
    
    html_template = template.get("html_template", "")
    renderer = LandPPTTemplateRenderer(html_template)
    
    # 简单的内容格式化逻辑 (模拟 Generator 中的逻辑)
    raw_content = slide_data.get("content", [])
    formatted_content = ""
    
    if isinstance(raw_content, list):
         items = "".join([f"<li>{item}</li>" for item in raw_content])
         formatted_content = f'<ul class="content-points">{items}</ul>'
    else:
         formatted_content = str(raw_content)
         # 如果不是HTML，简单包装
         if not formatted_content.strip().startswith("<"):
             formatted_content = f"<p>{formatted_content}</p>"

    # 构造渲染上下文
    render_context = {
        "page_title": slide_data.get("title", "未命名"),
        "main_heading": slide_data.get("title", "未命名"),
        "page_content": formatted_content,
        "current_page_number": slide_data.get("current_page_number", 1),
        "total_page_count": slide_data.get("total_page_count", 1)
    }
    
    try:
        html = renderer.render_html(render_context)
        return {"html": html}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"渲染失败: {str(e)}")


@router.get("/tags/all")
async def get_all_tags(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取所有模板标签"""
    db = get_database()
    
    # 聚合查询获取所有唯一标签
    pipeline = [
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags"}},
        {"$sort": {"_id": 1}}
    ]
    
    cursor = db.ppt_templates.aggregate(pipeline)
    tags = [doc["_id"] async for doc in cursor]
    
    return {
        "total": len(tags),
        "tags": tags
    }


@router.post("/import-landppt")
async def import_landppt_templates(
    force_reimport: bool = Query(False, description="强制重新导入"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """导入 LandPPT 模板（管理员功能）"""
    # 检查权限
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    db = get_database()
    
    from services.landppt_template_importer import import_landppt_templates
    
    try:
        imported_ids = await import_landppt_templates(db, force_reimport)
        
        return {
            "message": "模板导入成功",
            "imported_count": len(imported_ids),
            "template_ids": imported_ids
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
