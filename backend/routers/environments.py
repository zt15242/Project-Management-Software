from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from database import get_database
from models import (
    EnvironmentCreate, EnvironmentUpdate, EnvironmentResponse,
    EnvironmentCookie, EnvironmentLoginRequest, UserResponse, UserRole
)
from auth import get_current_active_user
from bson import ObjectId
from datetime import datetime
from utils import get_beijing_time
import asyncio
import sys
import os
import json
import subprocess

router = APIRouter(prefix="/api/environments", tags=["环境管理"])


def mask_password(password: str) -> str:
    """密码脱敏"""
    if not password:
        return ""
    if len(password) <= 2:
        return "*" * len(password)
    return password[0] + "*" * (len(password) - 2) + password[-1]


async def auto_login_environment(url: str, username: str, password: str, env_name: str) -> dict:
    """
    通过subprocess调用独立的Selenium脚本进行登录
    Selenium不依赖asyncio，完全避免Windows平台问题
    """
    try:
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        script_path = os.path.join(parent_dir, "selenium_login.py")
        
        # 构建命令
        cmd = [
            sys.executable,  # Python解释器路径
            script_path,
            url,
            username,
            password,
            env_name
        ]
        
        # 在后台线程中执行subprocess
        loop = asyncio.get_event_loop()
        
        def run_subprocess():
            try:
                # Windows中文环境下需要特殊处理编码
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=60,  # 60秒超时
                    # 不指定encoding，使用bytes处理
                )
                
                # 手动解码，忽略无法解码的字符
                stdout = result.stdout.decode('utf-8', errors='ignore')
                stderr = result.stderr.decode('utf-8', errors='ignore')
                
                if result.returncode == 0:
                    # 解析JSON输出
                    try:
                        return json.loads(stdout)
                    except json.JSONDecodeError as e:
                        return {
                            "success": False,
                            "cookies": [],
                            "message": f"解析登录结果失败: {str(e)}\n输出: {stdout[:200]}"
                        }
                else:
                    return {
                        "success": False,
                        "cookies": [],
                        "message": f"登录脚本执行失败: {stderr[:500]}"
                    }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "cookies": [],
                    "message": "登录超时（60秒）"
                }
            except Exception as e:
                return {
                    "success": False,
                    "cookies": [],
                    "message": f"执行登录失败: {str(e)}"
                }
        
        # 在线程池中执行
        result = await loop.run_in_executor(None, run_subprocess)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "cookies": [],
            "message": f"登录失败: {str(e)}"
        }


@router.post("/", response_model=EnvironmentResponse, status_code=status.HTTP_201_CREATED)
async def create_environment(
    project_id: str,
    environment: EnvironmentCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """创建环境配置"""
    db = get_database()
    
    # 验证项目是否存在
    try:
        project = await db.projects.find_one({"_id": ObjectId(project_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查权限
    is_owner = current_user.id == project["owner_id"]
    is_pm = current_user.id == project.get("project_manager_id")
    if current_user.role != UserRole.ADMIN and not is_owner and not is_pm:
        raise HTTPException(status_code=403, detail="没有权限，只有管理员、项目所有者或项目经理可以管理环境")
    
    # 创建环境配置
    env_dict = {
        "project_id": project_id,
        "name": environment.name,
        "url": environment.url,
        "username": environment.username,
        "password": environment.password,  # 实际应用中应该加密存储
        "description": environment.description,
        "is_active": True,
        "cookies": [],
        "last_login_at": None,
        "last_login_status": None,
        "created_by": current_user.id,
        "created_at": get_beijing_time(),
        "updated_at": get_beijing_time()
    }
    
    result = await db.environments.insert_one(env_dict)
    created_env = await db.environments.find_one({"_id": result.inserted_id})
    
    return EnvironmentResponse(
        id=str(created_env["_id"]),
        project_id=created_env["project_id"],
        name=created_env["name"],
        url=created_env["url"],
        username=created_env["username"],
        password_masked=mask_password(created_env["password"]),
        description=created_env.get("description"),
        is_active=created_env["is_active"],
        cookies=[EnvironmentCookie(**cookie) for cookie in created_env.get("cookies", [])],
        last_login_at=created_env.get("last_login_at"),
        last_login_status=created_env.get("last_login_status"),
        created_by=created_env["created_by"],
        created_at=created_env["created_at"],
        updated_at=created_env["updated_at"]
    )


@router.get("/project/{project_id}", response_model=List[EnvironmentResponse])
async def get_project_environments(
    project_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取项目的所有环境配置"""
    db = get_database()
    
    # 验证项目权限
    try:
        project = await db.projects.find_one({"_id": ObjectId(project_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限访问该项目")
    
    environments = await db.environments.find({"project_id": project_id}).to_list(length=None)
    
    return [
        EnvironmentResponse(
            id=str(env["_id"]),
            project_id=env["project_id"],
            name=env["name"],
            url=env["url"],
            username=env["username"],
            password_masked=mask_password(env["password"]),
            description=env.get("description"),
            is_active=env["is_active"],
            cookies=[EnvironmentCookie(**cookie) for cookie in env.get("cookies", [])],
            last_login_at=env.get("last_login_at"),
            last_login_status=env.get("last_login_status"),
            created_by=env["created_by"],
            created_at=env["created_at"],
            updated_at=env["updated_at"]
        )
        for env in environments
    ]


@router.put("/{environment_id}", response_model=EnvironmentResponse)
async def update_environment(
    environment_id: str,
    environment_update: EnvironmentUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """更新环境配置"""
    db = get_database()
    
    try:
        environment = await db.environments.find_one({"_id": ObjectId(environment_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的环境ID")
    
    if not environment:
        raise HTTPException(status_code=404, detail="环境不存在")
    
    # 检查项目权限
    project = await db.projects.find_one({"_id": ObjectId(environment["project_id"])})
    is_owner = current_user.id == project["owner_id"]
    is_pm = current_user.id == project.get("project_manager_id")
    if current_user.role != UserRole.ADMIN and not is_owner and not is_pm:
        raise HTTPException(status_code=403, detail="没有权限修改环境配置")
    
    update_data = {k: v for k, v in environment_update.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = get_beijing_time()
    
    await db.environments.update_one(
        {"_id": ObjectId(environment_id)},
        {"$set": update_data}
    )
    
    updated_env = await db.environments.find_one({"_id": ObjectId(environment_id)})
    
    return EnvironmentResponse(
        id=str(updated_env["_id"]),
        project_id=updated_env["project_id"],
        name=updated_env["name"],
        url=updated_env["url"],
        username=updated_env["username"],
        password_masked=mask_password(updated_env["password"]),
        description=updated_env.get("description"),
        is_active=updated_env["is_active"],
        cookies=[EnvironmentCookie(**cookie) for cookie in updated_env.get("cookies", [])],
        last_login_at=updated_env.get("last_login_at"),
        last_login_status=updated_env.get("last_login_status"),
        created_by=updated_env["created_by"],
        created_at=updated_env["created_at"],
        updated_at=updated_env["updated_at"]
    )


@router.delete("/{environment_id}")
async def delete_environment(
    environment_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """删除环境配置"""
    db = get_database()
    
    try:
        environment = await db.environments.find_one({"_id": ObjectId(environment_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的环境ID")
    
    if not environment:
        raise HTTPException(status_code=404, detail="环境不存在")
    
    # 检查项目权限
    project = await db.projects.find_one({"_id": ObjectId(environment["project_id"])})
    is_owner = current_user.id == project["owner_id"]
    is_pm = current_user.id == project.get("project_manager_id")
    if current_user.role != UserRole.ADMIN and not is_owner and not is_pm:
        raise HTTPException(status_code=403, detail="没有权限删除环境配置")
    
    await db.environments.delete_one({"_id": ObjectId(environment_id)})
    
    return {"message": "环境配置已删除"}


@router.post("/{environment_id}/login")
async def login_environment(
    environment_id: str,
    force_refresh: bool = False,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """登录环境并获取cookie"""
    db = get_database()
    
    try:
        environment = await db.environments.find_one({"_id": ObjectId(environment_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的环境ID")
    
    if not environment:
        raise HTTPException(status_code=404, detail="环境不存在")
    
    # 检查项目权限
    project = await db.projects.find_one({"_id": ObjectId(environment["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限访问该环境")
    
    # 如果不强制刷新且已有有效cookie，直接返回
    if not force_refresh and environment.get("cookies") and environment.get("last_login_status") == "success":
        last_login = environment.get("last_login_at")
        if last_login:
            # 检查cookie是否在24小时内
            time_diff = (get_beijing_time() - last_login).total_seconds()
            if time_diff < 86400:  # 24小时
                return {
                    "success": True,
                    "message": "使用缓存的登录信息",
                    "cookies": environment["cookies"],
                    "last_login_at": last_login
                }
    
    # 执行自动登录
    result = await auto_login_environment(
        url=environment["url"],
        username=environment["username"],
        password=environment["password"],
        env_name=environment["name"]
    )
    
    # 更新环境配置
    update_data = {
        "last_login_at": get_beijing_time(),
        "last_login_status": "success" if result["success"] else "failed",
        "updated_at": get_beijing_time()
    }
    
    if result["success"]:
        update_data["cookies"] = result["cookies"]
    
    await db.environments.update_one(
        {"_id": ObjectId(environment_id)},
        {"$set": update_data}
    )
    
    return result


@router.get("/{environment_id}/cookies")
async def get_environment_cookies(
    environment_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取环境的cookies"""
    db = get_database()
    
    try:
        environment = await db.environments.find_one({"_id": ObjectId(environment_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的环境ID")
    
    if not environment:
        raise HTTPException(status_code=404, detail="环境不存在")
    
    # 检查项目权限
    project = await db.projects.find_one({"_id": ObjectId(environment["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限访问该环境")
    
    return {
        "cookies": environment.get("cookies", []),
        "last_login_at": environment.get("last_login_at"),
        "last_login_status": environment.get("last_login_status")
    }


@router.post("/refresh-all")
async def refresh_all_environments(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """手动触发刷新所有环境的登录状态（仅管理员）"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有管理员可以执行此操作")
    
    from services.environment_refresh_service import get_refresh_service
    
    # 获取刷新服务并执行刷新
    refresh_service = get_refresh_service()
    
    # 在后台异步执行刷新任务
    asyncio.create_task(refresh_service.refresh_all_environments())
    
    return {
        "message": "环境刷新任务已启动，请稍后查看各环境的登录状态",
        "status": "started"
    }
