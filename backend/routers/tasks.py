from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from database import get_database
from models import TaskCreate, TaskUpdate, TaskResponse, TaskStatus, UserResponse, UserRole
from auth import get_current_active_user
from bson import ObjectId
from datetime import datetime
from utils import get_beijing_time

router = APIRouter(prefix="/api/tasks", tags=["任务管理"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """创建新任务"""
    db = get_database()
    
    # 检查项目是否存在
    try:
        project = await db.projects.find_one({"_id": ObjectId(task.project_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查用户是否在项目团队中
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 如果指定了分配对象，检查该用户是否在项目团队中
    if task.assigned_to:
        if task.assigned_to not in project["team_members"]:
            raise HTTPException(status_code=400, detail="被分配用户不在项目团队中")
    
    # 验证协助人是否都在项目团队中
    if task.collaborators:
        for collaborator_id in task.collaborators:
            if collaborator_id not in project["team_members"]:
                raise HTTPException(status_code=400, detail="协助人必须在项目团队中")
    
    task_dict = {
        "title": task.title,
        "description": task.description,
        "project_id": task.project_id,
        "created_by": current_user.id,
        "assigned_to": task.assigned_to,
        "collaborators": task.collaborators if task.collaborators else [],
        "status": TaskStatus.TODO,
        "priority": task.priority,
        "estimated_hours": task.estimated_hours,
        "actual_hours": None,
        "due_date": task.due_date,
        "created_at": get_beijing_time(),
        "updated_at": get_beijing_time()
    }
    
    result = await db.tasks.insert_one(task_dict)
    created_task = await db.tasks.find_one({"_id": result.inserted_id})
    
    return TaskResponse(
        id=str(created_task["_id"]),
        title=created_task["title"],
        description=created_task.get("description"),
        project_id=created_task["project_id"],
        created_by=created_task["created_by"],
        assigned_to=created_task.get("assigned_to"),
        collaborators=created_task.get("collaborators", []),
        status=created_task["status"],
        priority=created_task["priority"],
        estimated_hours=created_task.get("estimated_hours"),
        actual_hours=created_task.get("actual_hours"),
        due_date=created_task.get("due_date"),
        created_at=created_task["created_at"],
        updated_at=created_task["updated_at"]
    )



class TaskBatchItem(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: str = "medium"
    estimated_hours: Optional[float] = 0
    assigned_to: Optional[str] = None

class BatchCreateRequest(BaseModel):
    project_id: str
    tasks: List[TaskBatchItem]

@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def create_tasks_batch(
    batch: BatchCreateRequest,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """批量创建任务"""
    db = get_database()
    
    if not ObjectId.is_valid(batch.project_id):
        raise HTTPException(status_code=400, detail="无效的项目ID")
        
    project = await db.projects.find_one({"_id": ObjectId(batch.project_id)})
    if not project:
         raise HTTPException(status_code=404, detail="项目不存在")
         
    new_tasks = []
    current_time = get_beijing_time()
    
    for t in batch.tasks:
        task_dict = {
            "title": t.title,
            "description": t.description,
            "project_id": batch.project_id,
            "created_by": current_user.id,
            "assigned_to": t.assigned_to,
            "collaborators": [],
            "status": "todo",
            "priority": t.priority,
            "estimated_hours": t.estimated_hours,
            "actual_hours": None,
            "due_date": None,
            "created_at": current_time,
            "updated_at": current_time
        }
        new_tasks.append(task_dict)
        
    if new_tasks:
        await db.tasks.insert_many(new_tasks)
        
    return {"status": "success", "count": len(new_tasks)}


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    project_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    status: Optional[TaskStatus] = None,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取任务列表（支持过滤）"""
    db = get_database()
    
    query = {}
    
    if project_id:
        # 检查用户是否有权限访问该项目
        try:
            project = await db.projects.find_one({"_id": ObjectId(project_id)})
        except:
            raise HTTPException(status_code=400, detail="无效的项目ID")
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
            raise HTTPException(status_code=403, detail="没有权限")
        
        query["project_id"] = project_id
    else:
        # 如果没有指定项目，获取用户参与的所有项目
        if current_user.role == UserRole.ADMIN:
            projects = await db.projects.find().to_list(length=None)
        else:
            projects = await db.projects.find({"team_members": current_user.id}).to_list(length=None)
        
        project_ids = [str(p["_id"]) for p in projects]
        query["project_id"] = {"$in": project_ids}
    
    if assigned_to:
        query["assigned_to"] = assigned_to
    
    if status:
        query["status"] = status
    
    tasks = await db.tasks.find(query).to_list(length=None)
    
    return [
        TaskResponse(
            id=str(task["_id"]),
            title=task["title"],
            description=task.get("description"),
            project_id=task["project_id"],
            created_by=task["created_by"],
            assigned_to=task.get("assigned_to"),
            collaborators=task.get("collaborators", []),
            status=task["status"],
            priority=task["priority"],
            estimated_hours=task.get("estimated_hours"),
            actual_hours=task.get("actual_hours"),
            due_date=task.get("due_date"),
            created_at=task["created_at"],
            updated_at=task["updated_at"]
        )
        for task in tasks
    ]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取指定任务信息"""
    db = get_database()
    
    try:
        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的任务ID")
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(task["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    return TaskResponse(
        id=str(task["_id"]),
        title=task["title"],
        description=task.get("description"),
        project_id=task["project_id"],
        created_by=task["created_by"],
        assigned_to=task.get("assigned_to"),
        collaborators=task.get("collaborators", []),
        status=task["status"],
        priority=task["priority"],
        estimated_hours=task.get("estimated_hours"),
        actual_hours=task.get("actual_hours"),
        due_date=task.get("due_date"),
        created_at=task["created_at"],
        updated_at=task["updated_at"]
    )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """更新任务信息"""
    db = get_database()
    
    try:
        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的任务ID")
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(task["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 验证协助人是否都在项目团队中
    if task_update.collaborators is not None:
        for collaborator_id in task_update.collaborators:
            if collaborator_id not in project["team_members"]:
                raise HTTPException(status_code=400, detail="协助人必须在项目团队中")
    
    update_data = {k: v for k, v in task_update.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = get_beijing_time()
    
    await db.tasks.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": update_data}
    )
    
    updated_task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    
    return TaskResponse(
        id=str(updated_task["_id"]),
        title=updated_task["title"],
        description=updated_task.get("description"),
        project_id=updated_task["project_id"],
        created_by=updated_task["created_by"],
        assigned_to=updated_task.get("assigned_to"),
        collaborators=updated_task.get("collaborators", []),
        status=updated_task["status"],
        priority=updated_task["priority"],
        estimated_hours=updated_task.get("estimated_hours"),
        actual_hours=updated_task.get("actual_hours"),
        due_date=updated_task.get("due_date"),
        created_at=updated_task["created_at"],
        updated_at=updated_task["updated_at"]
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """删除任务"""
    db = get_database()
    
    try:
        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的任务ID")
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 只有任务创建者、项目所有者或管理员可以删除任务
    project = await db.projects.find_one({"_id": ObjectId(task["project_id"])})
    if (current_user.role != UserRole.ADMIN and 
        current_user.id != task["created_by"] and 
        current_user.id != project["owner_id"]):
        raise HTTPException(status_code=403, detail="没有权限")
    
    await db.tasks.delete_one({"_id": ObjectId(task_id)})
    
    return None

