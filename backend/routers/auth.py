from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from database import get_database
from models import UserCreate, UserResponse, Token, LoginRequest, UserRegisterRequest
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_active_user
)
from services.email_service import EmailService
from config import settings
from bson import ObjectId
from datetime import datetime
from utils import get_beijing_time

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserRegisterRequest):
    """注册新用户"""
    db = get_database()
    
    # 检查是否启用了邮件验证
    email_config = await db.email_config.find_one({"is_enabled": True})
    if email_config:
        if not user.code:
            raise HTTPException(status_code=400, detail="请输入邮箱验证码")
        
        # 验证验证码
        is_valid = await EmailService.verify_code(user.email, user.code)
        if not is_valid:
            raise HTTPException(status_code=400, detail="验证码错误或已过期")
    
    # 检查用户名是否已存在
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    existing_email = await db.users.find_one({"email": user.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    # 创建新用户
    user_dict = {
        "username": user.username,
        "email": user.email,
        "hashed_password": get_password_hash(user.password),
        "full_name": user.full_name,
        "role": user.role,
        "is_active": True,
        "created_at": get_beijing_time()
    }
    
    result = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    
    return UserResponse(
        id=str(created_user["_id"]),
        username=created_user["username"],
        email=created_user["email"],
        full_name=created_user["full_name"],
        role=created_user["role"],
        is_active=created_user["is_active"],
        created_at=created_user["created_at"]
    )


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """用户登录"""
    db = get_database()
    user = await db.users.find_one({"username": login_data.username})
    
    if not user or not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user["is_active"]:
        raise HTTPException(status_code=400, detail="用户未激活")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return current_user

