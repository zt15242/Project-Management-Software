from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from database import get_database
from models import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse, UserResponse, UserRole
from auth import get_current_active_user
from bson import ObjectId
from datetime import datetime
from utils import get_beijing_time

router = APIRouter(prefix="/api/projects", tags=["项目管理"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """创建新项目（仅管理员和项目经理）"""
    db = get_database()
    
    # 只有管理员和项目经理可以创建项目
    is_admin = current_user.role == UserRole.ADMIN
    is_pm_role = current_user.role == UserRole.PROJECT_MANAGER
    
    if not (is_admin or is_pm_role):
        raise HTTPException(
            status_code=403, 
            detail="没有权限创建项目，只有系统管理员和项目经理可以创建项目"
        )
    
    # 验证项目经理是否存在
    team_members = [current_user.id]
    if project.project_manager_id:
        # 检查项目经理是否存在
        pm = await db.users.find_one({"_id": ObjectId(project.project_manager_id)})
        if not pm:
            raise HTTPException(status_code=404, detail="项目经理不存在")
        # 将项目经理也加入团队成员
        if project.project_manager_id not in team_members:
            team_members.append(project.project_manager_id)
    
    project_dict = {
        "name": project.name,
        "description": project.description,
        "owner_id": current_user.id,
        "created_by": current_user.id,  # 确保添加 created_by 以兼容用户统计
        "project_manager_id": project.project_manager_id,
        "team_members": team_members,
        "start_date": project.start_date,
        "end_date": project.end_date,
        "is_active": True,
        "created_at": get_beijing_time(),
        "updated_at": get_beijing_time()
    }
    
    result = await db.projects.insert_one(project_dict)
    created_project = await db.projects.find_one({"_id": result.inserted_id})
    
    return ProjectResponse(
        id=str(created_project["_id"]),
        name=created_project["name"],
        description=created_project.get("description"),
        owner_id=created_project["owner_id"],
        project_manager_id=created_project.get("project_manager_id"),
        team_members=created_project["team_members"],
        start_date=created_project.get("start_date"),
        end_date=created_project.get("end_date"),
        is_active=created_project["is_active"],
        created_at=created_project["created_at"],
        updated_at=created_project["updated_at"]
    )


@router.get("/", response_model=ProjectListResponse)
async def get_projects(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取项目列表（支持搜索和分页）"""
    db = get_database()
    
    query = {}
    
    # 权限控制：管理员和项目经理看所有，其他人看参与的项目
    if current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER]:
        query["team_members"] = current_user.id
        
    # 搜索过滤
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    # 获取总数
    total = await db.projects.count_documents(query)
    
    # 获取分页数据，按创建时间倒序
    projects_cursor = db.projects.find(query).sort("created_at", -1).skip(skip).limit(limit)
    projects = await projects_cursor.to_list(length=limit)
    
    items = [
        ProjectResponse(
            id=str(project["_id"]),
            name=project["name"],
            description=project.get("description"),
            owner_id=project["owner_id"],
            project_manager_id=project.get("project_manager_id"),
            team_members=project["team_members"],
            start_date=project.get("start_date"),
            end_date=project.get("end_date"),
            is_active=project["is_active"],
            created_at=project["created_at"],
            updated_at=project["updated_at"]
        )
        for project in projects
    ]
    
    return ProjectListResponse(total=total, items=items)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取指定项目信息"""
    db = get_database()
    
    try:
        project = await db.projects.find_one({"_id": ObjectId(project_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查权限
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限访问该项目")
    
    return ProjectResponse(
        id=str(project["_id"]),
        name=project["name"],
        description=project.get("description"),
        owner_id=project["owner_id"],
        project_manager_id=project.get("project_manager_id"),
        team_members=project["team_members"],
        start_date=project.get("start_date"),
        end_date=project.get("end_date"),
        is_active=project["is_active"],
        created_at=project["created_at"],
        updated_at=project["updated_at"]
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """更新项目信息"""
    db = get_database()
    
    try:
        project = await db.projects.find_one({"_id": ObjectId(project_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 只有管理员、项目所有者或项目经理可以更新项目
    is_owner = current_user.id == project["owner_id"]
    is_pm = current_user.id == project.get("project_manager_id")
    if current_user.role != UserRole.ADMIN and not is_owner and not is_pm:
        raise HTTPException(status_code=403, detail="没有权限，只有管理员、项目所有者或项目经理可以修改项目")
    
    update_data = {k: v for k, v in project_update.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = get_beijing_time()
    
    # 如果更新了项目经理，需要验证并自动添加到团队成员
    if "project_manager_id" in update_data and update_data["project_manager_id"]:
        pm = await db.users.find_one({"_id": ObjectId(update_data["project_manager_id"])})
        if not pm:
            raise HTTPException(status_code=404, detail="项目经理不存在")
        # 如果项目经理不在团队中，添加进去
        if update_data["project_manager_id"] not in project["team_members"]:
            await db.projects.update_one(
                {"_id": ObjectId(project_id)},
                {"$addToSet": {"team_members": update_data["project_manager_id"]}}
            )
    
    await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$set": update_data}
    )
    
    updated_project = await db.projects.find_one({"_id": ObjectId(project_id)})
    
    return ProjectResponse(
        id=str(updated_project["_id"]),
        name=updated_project["name"],
        description=updated_project.get("description"),
        owner_id=updated_project["owner_id"],
        project_manager_id=updated_project.get("project_manager_id"),
        team_members=updated_project["team_members"],
        start_date=updated_project.get("start_date"),
        end_date=updated_project.get("end_date"),
        is_active=updated_project["is_active"],
        created_at=updated_project["created_at"],
        updated_at=updated_project["updated_at"]
    )


@router.post("/{project_id}/members/{user_id}", response_model=ProjectResponse)
async def add_team_member(
    project_id: str,
    user_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """添加团队成员到项目"""
    db = get_database()
    
    try:
        project = await db.projects.find_one({"_id": ObjectId(project_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 只有管理员和项目经理可以添加成员
    is_owner = current_user.id == project["owner_id"]
    is_pm = current_user.id == project.get("project_manager_id")
    if current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER] and not is_owner and not is_pm:
        raise HTTPException(
            status_code=403, 
            detail="没有权限，只有系统管理员、项目经理、项目所有者或项目负责人可以管理成员"
        )
    
    # 检查用户是否存在
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的用户ID")
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查用户是否已经在项目中
    if user_id in project["team_members"]:
        raise HTTPException(status_code=400, detail="用户已在项目中")
    
    await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {
            "$push": {"team_members": user_id},
            "$set": {"updated_at": get_beijing_time()}
        }
    )
    
    updated_project = await db.projects.find_one({"_id": ObjectId(project_id)})
    
    return ProjectResponse(
        id=str(updated_project["_id"]),
        name=updated_project["name"],
        description=updated_project.get("description"),
        owner_id=updated_project["owner_id"],
        project_manager_id=updated_project.get("project_manager_id"),
        team_members=updated_project["team_members"],
        start_date=updated_project.get("start_date"),
        end_date=updated_project.get("end_date"),
        is_active=updated_project["is_active"],
        created_at=updated_project["created_at"],
        updated_at=updated_project["updated_at"]
    )


@router.delete("/{project_id}/members/{user_id}", response_model=ProjectResponse)
async def remove_team_member(
    project_id: str,
    user_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """从项目中移除团队成员"""
    db = get_database()
    
    try:
        project = await db.projects.find_one({"_id": ObjectId(project_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 只有管理员和项目经理可以移除成员
    is_owner = current_user.id == project["owner_id"]
    is_pm = current_user.id == project.get("project_manager_id")
    if current_user.role not in [UserRole.ADMIN, UserRole.PROJECT_MANAGER] and not is_owner and not is_pm:
        raise HTTPException(
            status_code=403, 
            detail="没有权限，只有系统管理员、项目经理、项目所有者或项目负责人可以管理成员"
        )
    
    # 不能移除项目所有者和项目经理
    if user_id == project["owner_id"]:
        raise HTTPException(status_code=400, detail="不能移除项目所有者")
    
    if user_id == project.get("project_manager_id"):
        raise HTTPException(status_code=400, detail="不能移除项目经理，请先更改项目经理")
    
    await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {
            "$pull": {"team_members": user_id},
            "$set": {"updated_at": get_beijing_time()}
        }
    )
    
    updated_project = await db.projects.find_one({"_id": ObjectId(project_id)})
    
    return ProjectResponse(
        id=str(updated_project["_id"]),
        name=updated_project["name"],
        description=updated_project.get("description"),
        owner_id=updated_project["owner_id"],
        project_manager_id=updated_project.get("project_manager_id"),
        team_members=updated_project["team_members"],
        start_date=updated_project.get("start_date"),
        end_date=updated_project.get("end_date"),
        is_active=updated_project["is_active"],
        created_at=updated_project["created_at"],
        updated_at=updated_project["updated_at"]
    )
