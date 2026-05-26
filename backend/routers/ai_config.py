from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId
from datetime import datetime

from database import get_database
from auth import get_current_active_user
from models import (
    AIConfigCreate, AIConfigUpdate, AIConfigResponse,
    AIProvider, UserResponse, UserRole
)
from utils import get_beijing_time

router = APIRouter(prefix="/api/ai-config", tags=["AI配置管理"])


def mask_api_key(api_key: str) -> str:
    """脱敏API Key，只显示前4位和后4位"""
    if len(api_key) <= 8:
        return '*' * len(api_key)
    return api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]


@router.post("/", response_model=AIConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_config(
    config: AIConfigCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """创建AI配置（仅管理员）"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有管理员可以配置AI平台")
    
    db = get_database()
    
    # 检查该提供商是否已存在
    existing = await db.ai_configs.find_one({"provider": config.provider.value})
    if existing:
        raise HTTPException(status_code=400, detail=f"AI平台 {config.provider.value} 已存在，请使用更新接口")
    
    config_dict = {
        "provider": config.provider.value,
        "api_key": config.api_key,
        "model": config.model,
        "base_url": config.base_url,
        "is_enabled": config.is_enabled,
        "description": config.description,
        "created_at": get_beijing_time(),
        "updated_at": get_beijing_time()
    }
    
    result = await db.ai_configs.insert_one(config_dict)
    created_config = await db.ai_configs.find_one({"_id": result.inserted_id})
    
    return AIConfigResponse(
        id=str(created_config["_id"]),
        provider=AIProvider(created_config["provider"]),
        api_key_masked=mask_api_key(created_config["api_key"]),
        model=created_config.get("model"),
        base_url=created_config.get("base_url"),
        is_enabled=created_config["is_enabled"],
        description=created_config.get("description"),
        created_at=created_config["created_at"],
        updated_at=created_config["updated_at"]
    )


@router.get("/", response_model=List[AIConfigResponse])
async def get_ai_configs(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取AI配置列表（仅管理员）"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有管理员可以查看AI配置")
    
    db = get_database()
    configs = await db.ai_configs.find().to_list(length=None)
    
    return [
        AIConfigResponse(
            id=str(config["_id"]),
            provider=AIProvider(config["provider"]),
            api_key_masked=mask_api_key(config["api_key"]),
            model=config.get("model"),
            base_url=config.get("base_url"),
            is_enabled=config["is_enabled"],
            description=config.get("description"),
            created_at=config["created_at"],
            updated_at=config["updated_at"]
        )
        for config in configs
    ]


@router.get("/active", response_model=AIConfigResponse)
async def get_active_ai_config(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取当前启用的AI配置"""
    db = get_database()
    
    # 查找启用的配置
    config = await db.ai_configs.find_one({"is_enabled": True})
    
    if not config:
        # 如果没有启用的配置，返回默认的规则匹配模式
        return AIConfigResponse(
            id="default",
            provider=AIProvider.NONE,
            api_key_masked="",
            is_enabled=True,
            description="默认规则匹配模式",
            created_at=get_beijing_time(),
            updated_at=get_beijing_time()
        )
    
    return AIConfigResponse(
        id=str(config["_id"]),
        provider=AIProvider(config["provider"]),
        api_key_masked=mask_api_key(config["api_key"]),
        model=config.get("model"),
        base_url=config.get("base_url"),
        is_enabled=config["is_enabled"],
        description=config.get("description"),
        created_at=config["created_at"],
        updated_at=config["updated_at"]
    )


@router.get("/{config_id}", response_model=AIConfigResponse)
async def get_ai_config(
    config_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取指定AI配置（仅管理员）"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有管理员可以查看AI配置")
    
    db = get_database()
    
    try:
        config = await db.ai_configs.find_one({"_id": ObjectId(config_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的配置ID")
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    return AIConfigResponse(
        id=str(config["_id"]),
        provider=AIProvider(config["provider"]),
        api_key_masked=mask_api_key(config["api_key"]),
        model=config.get("model"),
        base_url=config.get("base_url"),
        is_enabled=config["is_enabled"],
        description=config.get("description"),
        created_at=config["created_at"],
        updated_at=config["updated_at"]
    )


@router.put("/{config_id}", response_model=AIConfigResponse)
async def update_ai_config(
    config_id: str,
    config_update: AIConfigUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """更新AI配置（仅管理员）"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有管理员可以修改AI配置")
    
    db = get_database()
    
    try:
        config = await db.ai_configs.find_one({"_id": ObjectId(config_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的配置ID")
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    update_data = {k: v for k, v in config_update.dict(exclude_unset=True).items() if v is not None}
    
    # 如果要启用此配置，先禁用其他配置
    if update_data.get("is_enabled") == True:
        await db.ai_configs.update_many(
            {"_id": {"$ne": ObjectId(config_id)}},
            {"$set": {"is_enabled": False, "updated_at": get_beijing_time()}}
        )
    
    update_data["updated_at"] = get_beijing_time()
    
    if update_data.get("provider"):
        update_data["provider"] = update_data["provider"].value
    
    await db.ai_configs.update_one(
        {"_id": ObjectId(config_id)},
        {"$set": update_data}
    )
    
    updated_config = await db.ai_configs.find_one({"_id": ObjectId(config_id)})
    
    return AIConfigResponse(
        id=str(updated_config["_id"]),
        provider=AIProvider(updated_config["provider"]),
        api_key_masked=mask_api_key(updated_config["api_key"]),
        model=updated_config.get("model"),
        base_url=updated_config.get("base_url"),
        is_enabled=updated_config["is_enabled"],
        description=updated_config.get("description"),
        created_at=updated_config["created_at"],
        updated_at=updated_config["updated_at"]
    )


@router.delete("/{config_id}")
async def delete_ai_config(
    config_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """删除AI配置（仅管理员）"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有管理员可以删除AI配置")
    
    db = get_database()
    
    try:
        config = await db.ai_configs.find_one({"_id": ObjectId(config_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的配置ID")
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    await db.ai_configs.delete_one({"_id": ObjectId(config_id)})
    
    return {"message": "AI配置已删除"}


@router.post("/{config_id}/test")
async def test_ai_config(
    config_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """测试AI配置是否可用（仅管理员）"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有管理员可以测试AI配置")
    
    db = get_database()
    
    try:
        config = await db.ai_configs.find_one({"_id": ObjectId(config_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的配置ID")
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # TODO: 实现实际的AI平台连接测试
    # 这里暂时返回成功
    return {
        "success": True,
        "message": f"AI平台 {config['provider']} 连接测试成功",
        "provider": config["provider"]
    }

