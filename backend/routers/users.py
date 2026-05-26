from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from database import get_database
from models import UserResponse, UserUpdate, UserRole, PasswordChange, UserStats, TaskStatus
from auth import get_current_active_user, get_password_hash, verify_password
from bson import ObjectId

router = APIRouter(prefix="/api/users", tags=["用户管理"])


@router.get("/", response_model=List[UserResponse])
async def get_users(current_user: UserResponse = Depends(get_current_active_user)):
    """获取所有用户列表"""
    db = get_database()
    users = await db.users.find().to_list(length=None)
    
    return [
        UserResponse(
            id=str(user["_id"]),
            username=user["username"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            is_active=user["is_active"],
            created_at=user["created_at"]
        )
        for user in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: UserResponse = Depends(get_current_active_user)):
    """获取指定用户信息"""
    db = get_database()
    
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的用户ID")
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return UserResponse(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        is_active=user["is_active"],
        created_at=user["created_at"]
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """更新用户信息"""
    db = get_database()
    
    # 只有管理员或用户本人可以更新信息
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="没有权限")
    
    try:
        user_id_obj = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="无效的用户ID")
    
    update_data = {k: v for k, v in user_update.dict(exclude_unset=True).items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="没有需要更新的数据")
    
    result = await db.users.update_one(
        {"_id": user_id_obj},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    updated_user = await db.users.find_one({"_id": user_id_obj})
    
    return UserResponse(
        id=str(updated_user["_id"]),
        username=updated_user["username"],
        email=updated_user["email"],
        full_name=updated_user["full_name"],
        role=updated_user["role"],
        is_active=updated_user["is_active"],
        created_at=updated_user["created_at"]
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, current_user: UserResponse = Depends(get_current_active_user)):
    """删除用户（仅管理员）"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="没有权限")
    
    db = get_database()
    
    try:
        user_id_obj = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="无效的用户ID")
    
    result = await db.users.delete_one({"_id": user_id_obj})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return None


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """修改密码"""
    db = get_database()
    
    # 获取用户信息
    user = await db.users.find_one({"_id": ObjectId(current_user.id)})
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 验证旧密码
    if not verify_password(password_data.old_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="旧密码不正确")
    
    # 更新密码
    hashed_password = get_password_hash(password_data.new_password)
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"hashed_password": hashed_password}}
    )
    
    return {"message": "密码修改成功"}


@router.get("/me/stats", response_model=UserStats)
async def get_user_stats(current_user: UserResponse = Depends(get_current_active_user)):
    """获取当前用户统计数据"""
    db = get_database()
    user_id = current_user.id
    
    # 统计创建的项目数
    created_projects = await db.projects.count_documents({"created_by": user_id})
    
    # 统计参与的项目数
    participated_projects = await db.projects.count_documents({"team_members": user_id})
    
    # 统计分配的任务数
    assigned_tasks = await db.tasks.count_documents({"assigned_to": user_id})
    
    # 统计完成的任务数
    completed_tasks = await db.tasks.count_documents({
        "assigned_to": user_id,
        "status": TaskStatus.COMPLETED
    })
    
    # 统计创建的课题数
    created_topics = await db.topics.count_documents({"created_by": user_id})
    
    # 统计分配的课题数
    assigned_topics = await db.topics.count_documents({"assigned_to": user_id})
    
    return UserStats(
        created_projects=created_projects,
        participated_projects=participated_projects,
        assigned_tasks=assigned_tasks,
        completed_tasks=completed_tasks,
        created_topics=created_topics,
        assigned_topics=assigned_topics
    )

