"""
日报管理路由
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId

from models import DailyReportCreate, DailyReportUpdate, DailyReportResponse, DailyReportType
from database import get_database
from auth import get_current_user

router = APIRouter(prefix="/api/daily-reports", tags=["daily-reports"])


@router.post("/", response_model=DailyReportResponse, status_code=status.HTTP_201_CREATED)
async def create_daily_report(
    report: DailyReportCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建日报"""
    db = get_database()
    
    # 验证：任务类型必须有task_id
    if report.report_type == DailyReportType.TASK and not report.task_id:
        raise HTTPException(status_code=400, detail="任务类型日报必须关联任务")
    
    # 验证：课题类型必须有topic_id
    if report.report_type == DailyReportType.TOPIC and not report.topic_id:
        raise HTTPException(status_code=400, detail="课题类型日报必须关联课题")
    
    # 验证：日常运维类型必须有project_id
    if report.report_type == DailyReportType.MAINTENANCE and not report.project_id:
        raise HTTPException(status_code=400, detail="日常运维类型日报必须关联项目")
    
    task_title = None
    topic_title = None
    project_name = None
    
    # 如果是任务类型，验证任务存在并检查工时
    if report.report_type == DailyReportType.TASK and report.task_id:
        task = await db.tasks.find_one({"_id": ObjectId(report.task_id)})
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task_title = task.get("title")
        estimated_hours = task.get("estimated_hours") or 0
        actual_hours = task.get("actual_hours") or 0
        
        # 检查是否超出预计工时
        if actual_hours + report.hours > estimated_hours:
            raise HTTPException(
                status_code=400,
                detail=f"工时超出预计！预计{estimated_hours}小时，已用{actual_hours}小时，本次{report.hours}小时"
            )
    
    # 如果是课题类型，获取Bug标题
    if report.report_type == DailyReportType.TOPIC and report.topic_id:
        bug = await db.topics.find_one({"_id": ObjectId(report.topic_id)})
        if not bug:
            raise HTTPException(status_code=404, detail="课题不存在")
        topic_title = bug.get("title")
    
    # 如果是日常运维类型，获取项目名称
    if report.report_type == DailyReportType.MAINTENANCE and report.project_id:
        project = await db.projects.find_one({"_id": ObjectId(report.project_id)})
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        project_name = project.get("name")
    
    # 创建日报
    now = datetime.now()
    report_data = {
        "user_id": current_user.id,
        "report_date": report.report_date,
        "report_type": report.report_type.value,
        "project_id": report.project_id,
        "task_id": report.task_id,
        "topic_id": report.topic_id,
        "content": report.content,
        "hours": report.hours,
        "created_at": now,
        "updated_at": now
    }
    
    result = await db.daily_reports.insert_one(report_data)
    
    # 如果是任务类型，回写实际工时
    if report.report_type == DailyReportType.TASK and report.task_id:
        await db.tasks.update_one(
            {"_id": ObjectId(report.task_id)},
            [
                {"$set": {
                    "actual_hours": {"$add": [{"$ifNull": ["$actual_hours", 0]}, report.hours]},
                    "updated_at": now
                }}
            ]
        )
    
    # 返回创建的日报
    created_report = await db.daily_reports.find_one({"_id": result.inserted_id})
    
    return DailyReportResponse(
        id=str(created_report["_id"]),
        user_id=created_report["user_id"],
        user_name=current_user.full_name or current_user.username,
        report_date=created_report["report_date"],
        report_type=DailyReportType(created_report["report_type"]),
        project_id=created_report.get("project_id"),
        project_name=project_name,
        task_id=created_report.get("task_id"),
        task_title=task_title,
        topic_id=created_report.get("topic_id"),
        topic_title=topic_title,
        content=created_report["content"],
        hours=created_report["hours"],
        created_at=created_report["created_at"],
        updated_at=created_report["updated_at"]
    )


@router.get("/", response_model=List[DailyReportResponse])
async def get_daily_reports(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: Optional[str] = None,
    report_type: Optional[DailyReportType] = None,
    current_user: dict = Depends(get_current_user)
):
    """获取日报列表"""
    db = get_database()
    
    # 构建查询条件
    query = {}
    
    # 如果指定了用户ID
    if user_id:
        query["user_id"] = user_id
    
    # 如果指定了日期范围
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            date_query["$lte"] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        if date_query:
            query["report_date"] = date_query
    
    # 如果指定了类型
    if report_type:
        query["report_type"] = report_type.value
    
    # 查询日报
    reports_cursor = db.daily_reports.find(query).sort("report_date", -1)
    reports = await reports_cursor.to_list(length=None)
    
    # 获取所有用户信息
    users_cursor = db.users.find({})
    users = await users_cursor.to_list(length=None)
    user_map = {str(u["_id"]): u for u in users}
    
    # 获取所有任务信息
    task_ids = [r.get("task_id") for r in reports if r.get("task_id")]
    tasks = {}
    if task_ids:
        tasks_cursor = db.tasks.find({"_id": {"$in": [ObjectId(tid) for tid in task_ids]}})
        tasks_list = await tasks_cursor.to_list(length=None)
        tasks = {str(t["_id"]): t for t in tasks_list}
    
    # 获取所有课题信息
    topic_ids = [r.get("topic_id") for r in reports if r.get("topic_id")]
    bugs = {}
    if topic_ids:
        bugs_cursor = db.topics.find({"_id": {"$in": [ObjectId(bid) for bid in topic_ids]}})
        bugs_list = await bugs_cursor.to_list(length=None)
        bugs = {str(b["_id"]): b for b in bugs_list}
    
    # 获取所有项目信息
    project_ids = [r.get("project_id") for r in reports if r.get("project_id")]
    projects = {}
    if project_ids:
        projects_cursor = db.projects.find({"_id": {"$in": [ObjectId(pid) for pid in project_ids]}})
        projects_list = await projects_cursor.to_list(length=None)
        projects = {str(p["_id"]): p for p in projects_list}
    
    # 构造响应
    result = []
    for report in reports:
        user = user_map.get(report["user_id"], {})
        task_title = None
        topic_title = None
        project_name = None
        
        if report.get("task_id"):
            task = tasks.get(report["task_id"])
            if task:
                task_title = task.get("title")
        
        if report.get("topic_id"):
            bug = bugs.get(report["topic_id"])
            if bug:
                topic_title = bug.get("title")
        
        if report.get("project_id"):
            project = projects.get(report["project_id"])
            if project:
                project_name = project.get("name")
        
        result.append(DailyReportResponse(
            id=str(report["_id"]),
            user_id=report["user_id"],
            user_name=user.get("full_name", user.get("username", "未知用户")),
            report_date=report["report_date"],
            report_type=DailyReportType(report["report_type"]),
            project_id=report.get("project_id"),
            project_name=project_name,
            task_id=report.get("task_id"),
            task_title=task_title,
            topic_id=report.get("topic_id"),
            topic_title=topic_title,
            content=report["content"],
            hours=report["hours"],
            created_at=report["created_at"],
            updated_at=report["updated_at"]
        ))
    
    return result


@router.get("/{report_id}", response_model=DailyReportResponse)
async def get_daily_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取单个日报"""
    db = get_database()
    
    report = await db.daily_reports.find_one({"_id": ObjectId(report_id)})
    if not report:
        raise HTTPException(status_code=404, detail="日报不存在")
    
    # 获取用户信息
    user = await db.users.find_one({"_id": ObjectId(report["user_id"])})
    user_name = user.get("full_name", user.get("username", "未知用户")) if user else "未知用户"
    
    # 获取任务或Bug标题
    task_title = None
    topic_title = None
    
    if report.get("task_id"):
        task = await db.tasks.find_one({"_id": ObjectId(report["task_id"])})
        if task:
            task_title = task.get("title")
    
    if report.get("topic_id"):
        bug = await db.topics.find_one({"_id": ObjectId(report["topic_id"])})
        if bug:
            topic_title = bug.get("title")
    
    return DailyReportResponse(
        id=str(report["_id"]),
        user_id=report["user_id"],
        user_name=user_name,
        report_date=report["report_date"],
        report_type=DailyReportType(report["report_type"]),
        task_id=report.get("task_id"),
        task_title=task_title,
        topic_id=report.get("topic_id"),
        topic_title=topic_title,
        content=report["content"],
        hours=report["hours"],
        created_at=report["created_at"],
        updated_at=report["updated_at"]
    )


@router.put("/{report_id}", response_model=DailyReportResponse)
async def update_daily_report(
    report_id: str,
    report_update: DailyReportUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新日报"""
    db = get_database()
    
    # 查找日报
    report = await db.daily_reports.find_one({"_id": ObjectId(report_id)})
    if not report:
        raise HTTPException(status_code=404, detail="日报不存在")
    
    # 验证权限：只能修改自己的日报
    if report["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改他人的日报")
    
    # 准备更新数据
    update_data = {"updated_at": datetime.now()}
    
    if report_update.content is not None:
        update_data["content"] = report_update.content
    
    # 如果更新工时
    if report_update.hours is not None:
        old_hours = report["hours"]
        new_hours = report_update.hours
        hours_diff = new_hours - old_hours
        
        # 如果是任务类型，需要检查工时并更新
        if report["report_type"] == DailyReportType.TASK.value and report.get("task_id"):
            task = await db.tasks.find_one({"_id": ObjectId(report["task_id"])})
            if task:
                estimated_hours = task.get("estimated_hours") or 0
                actual_hours = task.get("actual_hours") or 0
                
                # 检查新工时是否超出预计
                if actual_hours + hours_diff > estimated_hours:
                    raise HTTPException(
                        status_code=400,
                        detail=f"工时超出预计！预计{estimated_hours}小时，已用{actual_hours}小时，调整后将超出"
                    )
                
                # 更新任务实际工时
                await db.tasks.update_one(
                    {"_id": ObjectId(report["task_id"])},
                    [
                        {"$set": {
                            "actual_hours": {"$add": [{"$ifNull": ["$actual_hours", 0]}, hours_diff]},
                            "updated_at": datetime.now()
                        }}
                    ]
                )
        
        update_data["hours"] = new_hours
    
    # 更新日报
    await db.daily_reports.update_one(
        {"_id": ObjectId(report_id)},
        {"$set": update_data}
    )
    
    # 返回更新后的日报
    return await get_daily_report(report_id, current_user)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_daily_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """删除日报"""
    db = get_database()
    
    # 查找日报
    report = await db.daily_reports.find_one({"_id": ObjectId(report_id)})
    if not report:
        raise HTTPException(status_code=404, detail="日报不存在")
    
    # 验证权限：只能删除自己的日报
    if report["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除他人的日报")
    
    # 如果是任务类型，需要回退实际工时
    if report["report_type"] == DailyReportType.TASK.value and report.get("task_id"):
        await db.tasks.update_one(
            {"_id": ObjectId(report["task_id"])},
            [
                {"$set": {
                    "actual_hours": {"$add": [{"$ifNull": ["$actual_hours", 0]}, -report["hours"]]},
                    "updated_at": datetime.now()
                }}
            ]
        )
    
    # 删除日报
    await db.daily_reports.delete_one({"_id": ObjectId(report_id)})
    
    return None
