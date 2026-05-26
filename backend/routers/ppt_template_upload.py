"""
自定义 PPT 模板上传功能
支持上传 HTML 模板或 PPTX 模板
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional
from database import get_database
from auth import get_current_active_user
from models import UserResponse
from utils import get_beijing_time
from pydantic import BaseModel
import os
import json
import logging
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ppt/templates", tags=["PPT模板上传"])


class CustomTemplateCreate(BaseModel):
    """自定义模板创建"""
    template_name: str
    description: Optional[str] = None
    tags: list[str] = []


@router.post("/upload-html")
async def upload_html_template(
    template_name: str = Form(...),
    description: str = Form(""),
    tags: str = Form("[]"),  # JSON 字符串
    html_file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    上传自定义 HTML 模板
    
    HTML 模板必须包含以下占位符：
    - {{ page_title }} - 页面标题
    - {{ main_heading }} - 主标题
    - {{ page_content }} - 页面内容
    - {{ current_page_number }} - 当前页码
    - {{ total_page_count }} - 总页数
    """
    db = get_database()
    
    # 验证文件类型
    if not html_file.filename.endswith(('.html', '.htm')):
        raise HTTPException(status_code=400, detail="只支持 HTML 文件")
    
    # 读取 HTML 内容
    html_content = await html_file.read()
    html_template = html_content.decode('utf-8')
    
    # 验证必要的占位符
    required_placeholders = [
        "{{ page_title }}",
        "{{ main_heading }}",
        "{{ page_content }}",
        "{{ current_page_number }}",
        "{{ total_page_count }}"
    ]
    
    missing_placeholders = []
    for placeholder in required_placeholders:
        if placeholder not in html_template:
            missing_placeholders.append(placeholder)
    
    if missing_placeholders:
        raise HTTPException(
            status_code=400,
            detail=f"HTML 模板缺少必要的占位符: {', '.join(missing_placeholders)}"
        )
    
    # 解析标签
    try:
        tags_list = json.loads(tags)
    except:
        tags_list = []
    
    # 生成唯一的 template_id
    import time
    template_id = f"custom_{current_user.username}_{int(time.time())}"
    
    # 保存到数据库
    template_doc = {
        "template_id": template_id,
        "template_name": template_name,
        "description": description,
        "html_template": html_template,
        "tags": tags_list + ["自定义"],
        "is_default": False,
        "is_active": True,
        "is_builtin": False,
        "source": "custom",
        "created_by": current_user.id,
        "created_at": get_beijing_time(),
        "updated_at": get_beijing_time()
    }
    
    result = await db.ppt_templates.insert_one(template_doc)
    
    return {
        "message": "模板上传成功",
        "template_id": template_id,
        "template_name": template_name,
        "id": str(result.inserted_id)
    }


@router.post("/upload-pptx")
async def upload_pptx_template(
    template_name: str = Form(...),
    description: str = Form(""),
    tags: str = Form("[]"),
    pptx_file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    上传 PPTX 文件并自动转换为 HTML 模板
    
    系统会自动提取 PPTX 的样式、颜色、布局信息，生成对应的 HTML 模板
    """
    db = get_database()
    
    # 验证文件类型
    if not pptx_file.filename.endswith(('.pptx', '.ppt')):
        raise HTTPException(status_code=400, detail="只支持 PPTX/PPT 文件")
    
    # 保存上传的文件
    upload_dir = os.path.join(settings.UPLOAD_DIR, "ppt_templates")
    os.makedirs(upload_dir, exist_ok=True)
    
    import time
    filename = f"{current_user.username}_{int(time.time())}_{pptx_file.filename}"
    file_path = os.path.join(upload_dir, filename)
    
    with open(file_path, "wb") as f:
        content = await pptx_file.read()
        f.write(content)
    
    # 使用转换器将 PPTX 转换为 HTML 模板
    from utils.pptx_to_html_converter import convert_pptx_to_html_template
    
    try:
        html_template, template_info = convert_pptx_to_html_template(file_path)
        
        logger.info(f"PPTX 转换成功: {template_info}")
        
        conversion_success = True
        conversion_info = template_info
    except Exception as e:
        logger.error(f"PPTX 转换失败: {e}")
        
        # 降级：使用基础 HTML 模板
        html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page_title }}</title>
    <style>
        body {
            width: 1280px;
            height: 720px;
            margin: 0;
            padding: 40px;
            background: white;
            font-family: 'Microsoft YaHei', sans-serif;
        }
        h1 {
            font-size: 48px;
            color: #333;
            margin-bottom: 30px;
        }
        .content {
            font-size: 24px;
            line-height: 1.8;
        }
        .footer {
            position: absolute;
            bottom: 20px;
            right: 40px;
            font-size: 18px;
            color: #666;
        }
    </style>
</head>
<body>
    <h1>{{ main_heading }}</h1>
    <div class="content">
        {{ page_content }}
    </div>
    <div class="footer">
        {{ current_page_number }} / {{ total_page_count }}
    </div>
</body>
</html>"""
        
        conversion_success = False
        conversion_info = {"error": str(e)}
    
    # 解析标签
    try:
        tags_list = json.loads(tags)
    except:
        tags_list = []
    
    # 生成模板 ID
    template_id = f"pptx_{current_user.username}_{int(time.time())}"
    
    # 保存到数据库
    template_doc = {
        "template_id": template_id,
        "template_name": template_name,
        "description": description + (f" (从 PPTX 自动转换)" if conversion_success else " (PPTX 转换失败，使用基础模板)"),
        "html_template": html_template,
        "pptx_source_path": file_path,  # 保存原始 PPTX 路径
        "conversion_info": conversion_info,  # 保存转换信息
        "tags": tags_list + ["自定义", "PPTX上传"],
        "is_default": False,
        "is_active": True,
        "is_builtin": False,
        "source": "pptx_upload",
        "created_by": current_user.id,
        "created_at": get_beijing_time(),
        "updated_at": get_beijing_time()
    }
    
    result = await db.ppt_templates.insert_one(template_doc)
    
    response_data = {
        "message": "PPTX 模板上传并转换成功" if conversion_success else "PPTX 上传成功，但转换失败，使用基础模板",
        "template_id": template_id,
        "template_name": template_name,
        "id": str(result.inserted_id),
        "conversion_success": conversion_success
    }
    
    if conversion_success:
        response_data["template_info"] = conversion_info
    else:
        response_data["error"] = conversion_info.get("error", "未知错误")
    
    return response_data


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """删除自定义模板"""
    db = get_database()
    
    # 查找模板
    template = await db.ppt_templates.find_one({"template_id": template_id})
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 检查权限：只能删除自己创建的模板或管理员可以删除任何模板
    if template.get("created_by") != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除此模板")
    
    # 不能删除内置模板
    if template.get("is_builtin", False):
        raise HTTPException(status_code=403, detail="不能删除内置模板")
    
    # 删除模板
    await db.ppt_templates.delete_one({"template_id": template_id})
    
    # 如果有关联的 PPTX 文件，也删除
    if template.get("pptx_source_path"):
        try:
            os.remove(template["pptx_source_path"])
        except:
            pass
    
    return {
        "message": "模板删除成功",
        "template_id": template_id
    }


@router.put("/{template_id}")
async def update_template(
    template_id: str,
    template_name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """更新模板信息"""
    db = get_database()
    
    # 查找模板
    template = await db.ppt_templates.find_one({"template_id": template_id})
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 检查权限
    if template.get("created_by") != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权修改此模板")
    
    # 构建更新数据
    update_data = {"updated_at": get_beijing_time()}
    
    if template_name is not None:
        update_data["template_name"] = template_name
    if description is not None:
        update_data["description"] = description
    if tags is not None:
        try:
            update_data["tags"] = json.loads(tags)
        except:
            pass
    if is_active is not None:
        update_data["is_active"] = is_active
    
    # 更新
    await db.ppt_templates.update_one(
        {"template_id": template_id},
        {"$set": update_data}
    )
    
    return {
        "message": "模板更新成功",
        "template_id": template_id
    }


@router.get("/my-templates")
async def get_my_templates(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取我创建的模板"""
    db = get_database()
    
    cursor = db.ppt_templates.find({"created_by": current_user.id})
    templates = await cursor.to_list(length=None)
    
    result = []
    for template in templates:
        result.append({
            "id": str(template["_id"]),
            "template_id": template["template_id"],
            "template_name": template["template_name"],
            "description": template.get("description", ""),
            "tags": template.get("tags", []),
            "is_active": template.get("is_active", True),
            "source": template.get("source", "custom"),
            "created_at": template.get("created_at")
        })
    
    return {
        "total": len(result),
        "templates": result
    }
