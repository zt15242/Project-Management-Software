from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import psutil
import asyncio
from bson import ObjectId

from database import get_database
from models import UserResponse
from routers.auth import get_current_active_user
from utils import get_beijing_time

router = APIRouter(prefix="/api/background-tasks", tags=["后台任务管理"])


class BackgroundTaskResponse(BaseModel):
    id: str
    task_type: str  # meeting_analysis, data_export, etc.
    task_name: str
    status: str  # running, paused, completed, failed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None  # 秒
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    progress: Optional[int] = None  # 0-100
    error_message: Optional[str] = None
    created_by: str
    related_id: Optional[str] = None  # 关联的会议ID、导出ID等
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


@router.get("/", response_model=List[BackgroundTaskResponse])
async def get_background_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取后台任务列表"""
    db = get_database()
    
    # 构建查询条件
    query = {}
    if status:
        query["status"] = status
    if task_type:
        query["task_type"] = task_type
    
    # 非管理员只能看到自己的任务
    if current_user.role != "admin":
        query["created_by"] = current_user.id
    
    tasks = await db.background_tasks.find(query).sort("created_at", -1).limit(100).to_list(100)
    
    result = []
    for task in tasks:
        # 计算持续时间
        duration = None
        if task.get("started_at") and task.get("completed_at"):
            duration = (task["completed_at"] - task["started_at"]).total_seconds()
        elif task.get("started_at") and task["status"] == "running":
            duration = (get_beijing_time() - task["started_at"]).total_seconds()
        
        result.append(BackgroundTaskResponse(
            id=str(task["_id"]),
            task_type=task["task_type"],
            task_name=task["task_name"],
            status=task["status"],
            created_at=task["created_at"],
            started_at=task.get("started_at"),
            completed_at=task.get("completed_at"),
            duration=duration,
            cpu_percent=task.get("cpu_percent"),
            memory_mb=task.get("memory_mb"),
            progress=task.get("progress"),
            error_message=task.get("error_message"),
            created_by=task["created_by"],
            related_id=task.get("related_id")
        ))
    
    return result


@router.get("/{task_id}", response_model=BackgroundTaskResponse)
async def get_background_task(
    task_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取单个后台任务详情"""
    db = get_database()
    
    try:
        task = await db.background_tasks.find_one({"_id": ObjectId(task_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的任务ID")
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 权限检查
    if current_user.role != "admin" and task["created_by"] != current_user.id:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 计算持续时间
    duration = None
    if task.get("started_at") and task.get("completed_at"):
        duration = (task["completed_at"] - task["started_at"]).total_seconds()
    elif task.get("started_at") and task["status"] == "running":
        duration = (get_beijing_time() - task["started_at"]).total_seconds()
    
    return BackgroundTaskResponse(
        id=str(task["_id"]),
        task_type=task["task_type"],
        task_name=task["task_name"],
        status=task["status"],
        created_at=task["created_at"],
        started_at=task.get("started_at"),
        completed_at=task.get("completed_at"),
        duration=duration,
        cpu_percent=task.get("cpu_percent"),
        memory_mb=task.get("memory_mb"),
        progress=task.get("progress"),
        error_message=task.get("error_message"),
        created_by=task["created_by"],
        related_id=task.get("related_id")
    )


@router.post("/{task_id}/pause")
async def pause_task(
    task_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """暂停任务"""
    db = get_database()
    
    try:
        task = await db.background_tasks.find_one({"_id": ObjectId(task_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的任务ID")
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 权限检查
    if current_user.role != "admin" and task["created_by"] != current_user.id:
        raise HTTPException(status_code=403, detail="没有权限")
    
    if task["status"] != "running":
        raise HTTPException(status_code=400, detail="只能暂停运行中的任务")
    
    # 更新状态
    await db.background_tasks.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {"status": "paused", "updated_at": get_beijing_time()}}
    )
    
    return {"message": "任务已暂停"}


@router.post("/{task_id}/resume")
async def resume_task(
    task_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """继续任务"""
    db = get_database()
    
    try:
        task = await db.background_tasks.find_one({"_id": ObjectId(task_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的任务ID")
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 权限检查
    if current_user.role != "admin" and task["created_by"] != current_user.id:
        raise HTTPException(status_code=403, detail="没有权限")
    
    if task["status"] != "paused":
        raise HTTPException(status_code=400, detail="只能继续已暂停的任务")
    
    # 更新状态
    await db.background_tasks.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {"status": "running", "updated_at": get_beijing_time()}}
    )
    
    return {"message": "任务已继续"}


@router.post("/{task_id}/stop")
async def stop_task(
    task_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """停止任务"""
    db = get_database()
    
    try:
        task = await db.background_tasks.find_one({"_id": ObjectId(task_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的任务ID")
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 权限检查
    if current_user.role != "admin" and task["created_by"] != current_user.id:
        raise HTTPException(status_code=403, detail="没有权限")
    
    if task["status"] not in ["running", "paused"]:
        raise HTTPException(status_code=400, detail="只能停止运行中或已暂停的任务")
    
    # 更新状态
    await db.background_tasks.update_one(
        {"_id": ObjectId(task_id)},
        {
            "$set": {
                "status": "stopped",
                "completed_at": get_beijing_time(),
                "updated_at": get_beijing_time()
            }
        }
    )
    
    return {"message": "任务已停止"}


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """删除任务记录"""
    db = get_database()
    
    try:
        task = await db.background_tasks.find_one({"_id": ObjectId(task_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的任务ID")
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 权限检查
    if current_user.role != "admin" and task["created_by"] != current_user.id:
        raise HTTPException(status_code=403, detail="没有权限")
    
    if task["status"] in ["running", "paused"]:
        raise HTTPException(status_code=400, detail="不能删除运行中或已暂停的任务")
    
    await db.background_tasks.delete_one({"_id": ObjectId(task_id)})
    
    return {"message": "任务已删除"}


@router.get("/stats/summary")
async def get_task_stats(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取任务统计信息"""
    db = get_database()
    
    query = {}
    if current_user.role != "admin":
        query["created_by"] = current_user.id
    
    total = await db.background_tasks.count_documents(query)
    running = await db.background_tasks.count_documents({**query, "status": "running"})
    paused = await db.background_tasks.count_documents({**query, "status": "paused"})
    completed = await db.background_tasks.count_documents({**query, "status": "completed"})
    failed = await db.background_tasks.count_documents({**query, "status": "failed"})
    
    return {
        "total": total,
        "running": running,
        "paused": paused,
        "completed": completed,
        "failed": failed
    }
