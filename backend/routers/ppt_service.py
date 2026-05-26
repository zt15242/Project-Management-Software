from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from database import get_database
from models import (
    PPTDraftCreate, PPTDraftUpdate, PPTDraftResponse,
    UserResponse, PPTSlide
)
from auth import get_current_active_user
from bson import ObjectId
from datetime import datetime
from utils import get_beijing_time
import os

router = APIRouter(prefix="/api/ppt", tags=["PPT创作"])

@router.post("/drafts", response_model=PPTDraftResponse)
async def create_ppt_draft(
    draft: PPTDraftCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """创建PPT草稿（大纲确认后）"""
    db = get_database()
    
    draft_doc = draft.dict()
    draft_doc["created_by"] = current_user.id
    draft_doc["created_at"] = get_beijing_time()
    draft_doc["updated_at"] = get_beijing_time()
    
    result = await db.ppt_drafts.insert_one(draft_doc)
    created_doc = await db.ppt_drafts.find_one({"_id": result.inserted_id})
    
    created_doc["id"] = str(created_doc["_id"])
    return PPTDraftResponse(**created_doc)

@router.get("/drafts/{draft_id}", response_model=PPTDraftResponse)
async def get_ppt_draft(
    draft_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取PPT草稿详情"""
    db = get_database()
    
    if not ObjectId.is_valid(draft_id):
        raise HTTPException(status_code=400, detail="无效的草稿ID")
        
    doc = await db.ppt_drafts.find_one({"_id": ObjectId(draft_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="草稿不存在")
        
    doc["id"] = str(doc["_id"])
    return PPTDraftResponse(**doc)

@router.put("/drafts/{draft_id}", response_model=PPTDraftResponse)
async def update_ppt_draft(
    draft_id: str,
    draft_update: PPTDraftUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """更新PPT草稿（内容、样式等）"""
    db = get_database()
    
    if not ObjectId.is_valid(draft_id):
        raise HTTPException(status_code=400, detail="无效的草稿ID")
        
    update_data = {k: v for k, v in draft_update.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = get_beijing_time()
    
    await db.ppt_drafts.update_one(
        {"_id": ObjectId(draft_id)},
        {"$set": update_data}
    )
    
    updated_doc = await db.ppt_drafts.find_one({"_id": ObjectId(draft_id)})
    updated_doc["id"] = str(updated_doc["_id"])
    return PPTDraftResponse(**updated_doc)

@router.post("/drafts/{draft_id}/generate")
async def generate_final_pptx(
    draft_id: str,
    template_id: str = "商务",  # 新增：模板 ID 参数
    save_to_knowledge: bool = False,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """根据大纲和样式生成最终的PPTX文件（使用 LandPPT 模板）"""
    db = get_database()
    
    if not ObjectId.is_valid(draft_id):
        raise HTTPException(status_code=400, detail="无效的草稿ID")
        
    draft = await db.ppt_drafts.find_one({"_id": ObjectId(draft_id)})
    if not draft:
        raise HTTPException(status_code=404, detail="草稿不存在")
    
    # 使用 LandPPT 模板渲染引擎生成 PPT
    from services.landppt_ai_integration import create_pptx_from_draft_with_landppt
    
    try:
        file_path = await create_pptx_from_draft_with_landppt(
            draft=draft,
            template_id=template_id
        )
    except Exception as e:
        # 如果 LandPPT 生成失败，降级到原有方法
        print(f"[LandPPT] 生成失败，降级到原有方法: {e}")
        from services.ppt_generation_legacy import create_pptx_from_draft
        file_path = await create_pptx_from_draft(draft)
    
    # 构建下载URL
    from config import settings
    base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
    rel_path = os.path.relpath(file_path, settings.UPLOAD_DIR).replace("\\", "/")
    final_file_url = f"{base_url}/uploads/{rel_path}"
    
    if save_to_knowledge:
        # 保存到知识库
        knowledge_doc = {
            "title": draft["title"],
            "project_id": draft["project_id"],
            "category": "演示文稿",
            "description": f"使用 {template_id} 模板生成的PPT",
            "file_type": "ppt",
            "file_name": os.path.basename(file_path),
            "file_path": final_file_url,
            "file_size": os.path.getsize(file_path),
            "created_by": current_user.id,
            "status": "published",
            "tags": ["AI生成", "PPT", f"模板:{template_id}"],
            "views": 0,
            "created_at": get_beijing_time(),
            "updated_at": get_beijing_time(),
            "storage_type": "local"
        }
        await db.knowledge.insert_one(knowledge_doc)
        
    return {
        "message": "PPT生成成功",
        "file_url": final_file_url,
        "filename": os.path.basename(file_path),
        "template_used": template_id
    }
