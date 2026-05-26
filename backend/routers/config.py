from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from auth import get_current_active_user
from models import UserResponse, UserRole
from database import get_database
from bson import ObjectId

router = APIRouter(prefix="/api/config", tags=["配置管理"])


class ASRConfigRequest(BaseModel):
    api_key: Optional[str] = None  # 可选，如果为空则不更新
    base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    model: str = "qwen3-asr-flash-filetrans"
    server_base_url: str


class ASRConfigResponse(BaseModel):
    api_key_masked: str
    base_url: str
    model: str
    server_base_url: str


class OSSConfigRequest(BaseModel):
    provider: Optional[str] = None  # aliyun, tencent, 或 None
    access_key_id: Optional[str] = None
    access_key_secret: Optional[str] = None
    bucket_name: Optional[str] = None
    region: Optional[str] = None
    endpoint: Optional[str] = None


class OSSConfigResponse(BaseModel):
    provider: Optional[str]
    access_key_id_masked: str
    access_key_secret_masked: str
    bucket_name: Optional[str]
    region: Optional[str]
    endpoint: Optional[str]


# ==================== ASR配置API ====================

@router.get("/asr", response_model=ASRConfigResponse)
async def get_asr_config(current_user: UserResponse = Depends(get_current_active_user)):
    """获取ASR配置"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    db = get_database()
    config = await db.system_config.find_one({"config_type": "asr"})
    
    if not config:
        return ASRConfigResponse(
            api_key_masked="",
            base_url="https://dashscope.aliyuncs.com/api/v1",
            model="qwen3-asr-flash-filetrans",
            server_base_url="http://localhost:8000"
        )
    
    # 掩码API Key
    api_key = config.get("api_key", "")
    api_key_masked = api_key[:8] + "*" * (len(api_key) - 12) + api_key[-4:] if len(api_key) > 12 else "*" * len(api_key)
    
    return ASRConfigResponse(
        api_key_masked=api_key_masked,
        base_url=config.get("base_url", "https://dashscope.aliyuncs.com/api/v1"),
        model=config.get("model", "qwen3-asr-flash-filetrans"),
        server_base_url=config.get("server_base_url", "http://localhost:8000")
    )


@router.post("/asr")
async def save_asr_config(
    config: ASRConfigRequest,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """保存ASR配置到MongoDB"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    db = get_database()
    
    # 查找现有配置
    existing_config = await db.system_config.find_one({"config_type": "asr"})
    
    update_data = {
        "config_type": "asr",
        "base_url": config.base_url,
        "model": config.model,
        "server_base_url": config.server_base_url,
        "updated_by": current_user.id
    }
    
    # 只有提供了新的API Key才更新
    if config.api_key:
        update_data["api_key"] = config.api_key
    
    if existing_config:
        # 更新现有配置
        await db.system_config.update_one(
            {"config_type": "asr"},
            {"$set": update_data}
        )
    else:
        # 创建新配置
        update_data["created_by"] = current_user.id
        await db.system_config.insert_one(update_data)
    
    return {"message": "配置保存成功"}


@router.post("/asr/test")
async def test_asr_config(
    config: ASRConfigRequest,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """测试ASR配置"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        import httpx
        
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        test_url = f"{config.base_url}/tasks/test-connection"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(test_url, headers=headers)
            
            if response.status_code == 401:
                return {"success": False, "message": "API Key无效,请检查"}
            
            if response.status_code == 404:
                return {"success": True, "message": "连接成功! API Key有效"}
            
            return {"success": True, "message": "连接成功!"}
            
    except httpx.RequestError as e:
        return {"success": False, "message": f"网络连接失败: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"测试失败: {str(e)}"}


# ==================== OSS配置API ====================

@router.get("/oss", response_model=OSSConfigResponse)
async def get_oss_config(current_user: UserResponse = Depends(get_current_active_user)):
    """获取OSS配置"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    db = get_database()
    config = await db.system_config.find_one({"config_type": "oss"})
    
    if not config:
        return OSSConfigResponse(
            provider=None,
            access_key_id_masked="",
            access_key_secret_masked="",
            bucket_name=None,
            region=None,
            endpoint=None
        )
    
    # 掩码敏感信息
    access_key_id = config.get("access_key_id", "")
    access_key_secret = config.get("access_key_secret", "")
    
    access_key_id_masked = access_key_id[:4] + "*" * (len(access_key_id) - 8) + access_key_id[-4:] if len(access_key_id) > 8 else "*" * len(access_key_id)
    access_key_secret_masked = access_key_secret[:4] + "*" * (len(access_key_secret) - 8) + access_key_secret[-4:] if len(access_key_secret) > 8 else "*" * len(access_key_secret)
    
    return OSSConfigResponse(
        provider=config.get("provider"),
        access_key_id_masked=access_key_id_masked,
        access_key_secret_masked=access_key_secret_masked,
        bucket_name=config.get("bucket_name"),
        region=config.get("region"),
        endpoint=config.get("endpoint")
    )


@router.post("/oss")
async def save_oss_config(
    config: OSSConfigRequest,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """保存OSS配置到MongoDB"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    db = get_database()
    
    # 查找现有配置
    existing_config = await db.system_config.find_one({"config_type": "oss"})
    
    update_data = {
        "config_type": "oss",
        "provider": config.provider,
        "bucket_name": config.bucket_name,
        "region": config.region,
        "endpoint": config.endpoint,
        "updated_by": current_user.id
    }
    
    # 只有提供了新的密钥才更新
    if config.access_key_id:
        update_data["access_key_id"] = config.access_key_id
    if config.access_key_secret:
        update_data["access_key_secret"] = config.access_key_secret
    
    if existing_config:
        # 更新现有配置
        await db.system_config.update_one(
            {"config_type": "oss"},
            {"$set": update_data}
        )
    else:
        # 创建新配置
        update_data["created_by"] = current_user.id
        await db.system_config.insert_one(update_data)
    
    return {"message": "OSS配置保存成功"}


@router.post("/oss/test")
async def test_oss_config(
    config: OSSConfigRequest,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """测试OSS配置"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    if not config.provider:
        return {"success": False, "message": "请选择OSS提供商"}
    
    if not config.access_key_id or not config.access_key_secret:
        return {"success": False, "message": "请填写Access Key"}
    
    if not config.bucket_name:
        return {"success": False, "message": "请填写Bucket名称"}
    
    try:
        if config.provider == "aliyun":
            import oss2
            auth = oss2.Auth(config.access_key_id, config.access_key_secret)
            endpoint = config.endpoint or f"https://oss-{config.region}.aliyuncs.com"
            bucket = oss2.Bucket(auth, endpoint, config.bucket_name)
            
            try:
                bucket.get_bucket_info()
                return {"success": True, "message": "阿里云OSS连接成功!"}
            except Exception as e:
                return {"success": False, "message": f"连接失败: {str(e)}"}
            
        elif config.provider == "tencent":
            from qcloud_cos import CosConfig, CosS3Client
            cos_config = CosConfig(
                Region=config.region,
                SecretId=config.access_key_id,
                SecretKey=config.access_key_secret
            )
            client = CosS3Client(cos_config)
            
            try:
                client.list_objects(Bucket=config.bucket_name, MaxKeys=1)
                return {"success": True, "message": "腾讯云COS连接成功!"}
            except Exception as e:
                return {"success": False, "message": f"连接失败: {str(e)}"}
        else:
            return {"success": False, "message": "不支持的OSS提供商"}
            
    except ImportError as e:
        return {
            "success": False,
            "message": f"缺少SDK库: {str(e)}. 请安装 oss2 (阿里云) 或 cos-python-sdk-v5 (腾讯云)"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"测试失败: {str(e)}"
        }


# ==================== 辅助函数：从MongoDB获取配置 ====================

async def get_asr_config_from_db():
    """从MongoDB获取ASR配置（供其他模块使用）"""
    db = get_database()
    config = await db.system_config.find_one({"config_type": "asr"})
    return config if config else {}



async def get_oss_config_from_db():
    """从MongoDB获取OSS配置（供其他模块使用）"""
    db = get_database()
    config = await db.system_config.find_one({"config_type": "oss"})
    return config if config else {}

