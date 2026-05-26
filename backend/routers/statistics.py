from fastapi import APIRouter, Depends, HTTPException
from typing import List
from database import get_database
from models import ProjectStatistics, UserResponse, UserRole, TaskStatus, TopicStatus
from auth import get_current_active_user
from bson import ObjectId

router = APIRouter(prefix="/api/statistics", tags=["统计看板"])


@router.get("/projects/{project_id}", response_model=ProjectStatistics)
async def get_project_statistics(
    project_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取指定项目的统计数据"""
    db = get_database()
    
    # 检查项目是否存在
    try:
        project = await db.projects.find_one({"_id": ObjectId(project_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查权限
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 统计任务数据
    total_tasks = await db.tasks.count_documents({"project_id": project_id})
    completed_tasks = await db.tasks.count_documents({
        "project_id": project_id,
        "status": TaskStatus.COMPLETED
    })
    
    task_completion_rate = 0.0
    if total_tasks > 0:
        task_completion_rate = (completed_tasks / total_tasks) * 100
    
    # 统计课题数据
    total_topics = await db.topics.count_documents({"project_id": project_id})
    open_topics = await db.topics.count_documents({
        "project_id": project_id,
        "status": {"$in": [TopicStatus.OPEN, TopicStatus.ASSIGNED, TopicStatus.IN_PROGRESS, 
                           TopicStatus.FIXED, TopicStatus.TESTING, TopicStatus.REOPENED]}
    })
    closed_topics = await db.topics.count_documents({
        "project_id": project_id,
        "status": TopicStatus.CLOSED
    })
    
    # 计算课题率（课题数量与任务数量的比率）
    topic_rate = 0.0
    if total_tasks > 0:
        topic_rate = (total_topics / total_tasks) * 100
    
    # 团队规模
    team_size = len(project["team_members"])
    
    return ProjectStatistics(
        project_id=project_id,
        project_name=project["name"],
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        task_completion_rate=round(task_completion_rate, 2),
        total_topics=total_topics,
        open_topics=open_topics,
        closed_topics=closed_topics,
        topic_rate=round(topic_rate, 2),
        team_size=team_size
    )


@router.get("/overview", response_model=List[ProjectStatistics])
async def get_all_projects_statistics(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取所有项目的统计概览"""
    db = get_database()
    
    # 获取用户有权限访问的项目
    if current_user.role == UserRole.ADMIN:
        projects = await db.projects.find().to_list(length=None)
    else:
        projects = await db.projects.find({"team_members": current_user.id}).to_list(length=None)
    
    statistics_list = []
    
    for project in projects:
        project_id = str(project["_id"])
        
        # 统计任务数据
        total_tasks = await db.tasks.count_documents({"project_id": project_id})
        completed_tasks = await db.tasks.count_documents({
            "project_id": project_id,
            "status": TaskStatus.COMPLETED
        })
        
        task_completion_rate = 0.0
        if total_tasks > 0:
            task_completion_rate = (completed_tasks / total_tasks) * 100
        
        # 统计课题数据
        total_topics = await db.topics.count_documents({"project_id": project_id})
        open_topics = await db.topics.count_documents({
            "project_id": project_id,
            "status": {"$in": [TopicStatus.OPEN, TopicStatus.ASSIGNED, TopicStatus.IN_PROGRESS, 
                               TopicStatus.FIXED, TopicStatus.TESTING, TopicStatus.REOPENED]}
        })
        closed_topics = await db.topics.count_documents({
            "project_id": project_id,
            "status": TopicStatus.CLOSED
        })
        
        # 计算课题率
        topic_rate = 0.0
        if total_tasks > 0:
            topic_rate = (total_topics / total_tasks) * 100
        
        # 团队规模
        team_size = len(project["team_members"])
        
        statistics_list.append(ProjectStatistics(
            project_id=project_id,
            project_name=project["name"],
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            task_completion_rate=round(task_completion_rate, 2),
            total_topics=total_topics,
            open_topics=open_topics,
            closed_topics=closed_topics,
            topic_rate=round(topic_rate, 2),
            team_size=team_size
        ))
    
    return statistics_list

