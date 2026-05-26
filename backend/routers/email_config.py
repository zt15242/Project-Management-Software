from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
import uuid

from database import get_database
from models import EmailConfigCreate, EmailConfigUpdate, EmailConfigResponse, EmailVerifyRequest, UserResponse
from auth import get_current_active_user, get_current_admin_user
from services.email_service import EmailService
from utils import get_beijing_time

router = APIRouter(prefix="/api/email-config", tags=["邮局配置"])

@router.get("/status")
async def get_email_status():
    """公开接口：获取邮件配置状态"""
    db = get_database()
    config = await db.email_config.find_one({"is_enabled": True})
    return {"enabled": config is not None}

@router.get("", response_model=Optional[EmailConfigResponse])
async def get_email_config(_: UserResponse = Depends(get_current_admin_user)):
    db = get_database()
    config = await db.email_config.find_one({})
    if config:
        config["id"] = str(config.pop("_id"))
        return config
    return None

@router.post("", response_model=EmailConfigResponse)
async def create_or_update_email_config(config_in: EmailConfigCreate, _: UserResponse = Depends(get_current_admin_user)):
    db = get_database()
    existing = await db.email_config.find_one({})
    
    config_data = config_in.dict()
    now = get_beijing_time()
    
    if existing:
        config_data["updated_at"] = now
        await db.email_config.update_one({"_id": existing["_id"]}, {"$set": config_data})
        updated = await db.email_config.find_one({"_id": existing["_id"]})
        updated["id"] = str(updated.pop("_id"))
        return updated
    else:
        config_data["created_at"] = now
        config_data["updated_at"] = now
        result = await db.email_config.insert_one(config_data)
        new_config = await db.email_config.find_one({"_id": result.inserted_id})
        new_config["id"] = str(new_config.pop("_id"))
        return new_config

@router.post("/test")
async def test_email_config(test_email: str, _: UserResponse = Depends(get_current_admin_user)):
    config = await EmailService.get_config()
    if not config:
        raise HTTPException(status_code=400, detail="邮局服务未配置")
    
    subject = "测试邮件 - 项目管理系统"
    content = "这是一封来自项目管理系统的测试邮件，证明您的邮局配置已生效。"
    
    success = EmailService.send_email(config, test_email, subject, content)
    if success:
        return {"message": "测试邮件已发送"}
    else:
        raise HTTPException(status_code=500, detail="邮件发送失败，请检查配置")

@router.post("/send-code")
async def send_verification_code(request: EmailVerifyRequest):
    success, message = await EmailService.generate_and_send_code(request.email, request.purpose)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}
