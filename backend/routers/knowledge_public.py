from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import List, Optional
from database import get_database
from models import (
    KnowledgeCreate, KnowledgeUpdate, KnowledgeResponse, 
    KnowledgeFileType, KnowledgeStatus, KnowledgeSearchRequest,
    UserResponse, UserRole
)
from auth import get_current_active_user
from bson import ObjectId
from datetime import datetime, timedelta
from utils import get_beijing_time
from config import settings
import os
import aiofiles
import uuid
import mimetypes
import secrets
import hashlib

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])

# 临时访问令牌存储（生产环境建议使用Redis）
_temp_tokens = {}

# ... 保留原有的所有代码 ...

@router.get("/{knowledge_id}/public-url")
async def generate_public_url(
    knowledge_id: str,
    expires_minutes: int = 10,  # 默认10分钟有效期
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    生成文档的临时公开访问URL
    用于Office Online等外部服务访问
    """
    db = get_database()
    
    try:
        doc = await db.knowledge.find_one({"_id": ObjectId(knowledge_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的文档ID")
    
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 生成临时令牌（使用secrets生成安全的随机字符串）
    temp_token = secrets.token_urlsafe(32)
    
    # 计算过期时间
    expires_at = datetime.now() + timedelta(minutes=expires_minutes)
    
    # 存储令牌信息
    _temp_tokens[temp_token] = {
        "knowledge_id": knowledge_id,
        "file_path": doc["file_path"],
        "file_name": doc["file_name"],
        "expires_at": expires_at
    }
    
    # 构建公开URL
    # 注意：这里需要使用服务器的公网地址
    public_url = f"{settings.BASE_URL}/api/knowledge/public/{temp_token}"
    
    return {
        "public_url": public_url,
        "temp_token": temp_token,
        "expires_at": expires_at.isoformat(),
        "expires_in_seconds": expires_minutes * 60
    }


@router.get("/public/{temp_token}")
async def get_public_file(temp_token: str):
    """
    通过临时令牌访问文件（无需认证）
    用于Office Online等外部服务
    """
    # 检查令牌是否存在
    if temp_token not in _temp_tokens:
        raise HTTPException(status_code=404, detail="无效的访问令牌")
    
    token_info = _temp_tokens[temp_token]
    
    # 检查是否过期
    if datetime.now() > token_info["expires_at"]:
        # 清理过期令牌
        del _temp_tokens[temp_token]
        raise HTTPException(status_code=410, detail="访问令牌已过期")
    
    file_path = token_info["file_path"]
    file_name = token_info["file_name"]
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 返回文件
    # 设置正确的Content-Type以便Office Online识别
    media_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    
    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type=media_type,
        headers={
            "Access-Control-Allow-Origin": "*",  # 允许Office Online跨域访问
            "Cache-Control": "no-cache"
        }
    )


@router.delete("/public/{temp_token}")
async def revoke_public_url(
    temp_token: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """撤销临时访问令牌"""
    if temp_token in _temp_tokens:
        del _temp_tokens[temp_token]
        return {"message": "令牌已撤销"}
    else:
        raise HTTPException(status_code=404, detail="令牌不存在")


# 定期清理过期令牌的后台任务
async def cleanup_expired_tokens():
    """清理过期的临时令牌"""
    now = datetime.now()
    expired_tokens = [
        token for token, info in _temp_tokens.items()
        if now > info["expires_at"]
    ]
    for token in expired_tokens:
        del _temp_tokens[token]
    
    if expired_tokens:
        print(f"清理了 {len(expired_tokens)} 个过期令牌")
