from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional
from database import get_database
from models import BugCreate, BugUpdate, BugResponse, BugStatus, BugCommentCreate, BugCommentResponse, UserResponse, UserRole
from auth import get_current_active_user
from bson import ObjectId
from datetime import datetime
from utils import get_beijing_time
import os
import aiofiles
from config import settings
import uuid

router = APIRouter(prefix="/api/bugs", tags=["BUG管理"])


@router.post("/", response_model=BugResponse, status_code=status.HTTP_201_CREATED)
async def create_bug(
    bug: BugCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """创建新BUG"""
    db = get_database()
    
    # 检查项目是否存在
    try:
        project = await db.projects.find_one({"_id": ObjectId(bug.project_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查用户是否在项目团队中
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 如果指定了分配对象，检查该用户是否在项目团队中
    if bug.assigned_to:
        if bug.assigned_to not in project["team_members"]:
            raise HTTPException(status_code=400, detail="被分配用户不在项目团队中")
    
    bug_dict = {
        "title": bug.title,
        "description": bug.description,
        "project_id": bug.project_id,
        "created_by": current_user.id,
        "assigned_to": bug.assigned_to,
        "status": BugStatus.OPEN if not bug.assigned_to else BugStatus.ASSIGNED,
        "severity": bug.severity,
        "steps_to_reproduce": bug.steps_to_reproduce,
        "fix_description": None,
        "bug_images": bug.bug_images,  # BUG截图（base64）
        "fix_images": [],  # 修复截图（base64）
        "attachments": [],
        "created_at": get_beijing_time(),
        "updated_at": get_beijing_time()
    }
    
    result = await db.bugs.insert_one(bug_dict)
    created_bug = await db.bugs.find_one({"_id": result.inserted_id})
    
    # 如果分配了BUG，创建通知
    if bug.assigned_to:
        notification = {
            "user_id": bug.assigned_to,
            "type": "bug_assigned",
            "title": "新的BUG分配",
            "message": f"您有一个新的BUG: {bug.title}",
            "bug_id": str(result.inserted_id),
            "project_id": bug.project_id,
            "is_read": False,
            "created_at": get_beijing_time()
        }
        await db.notifications.insert_one(notification)
    
    return BugResponse(
        id=str(created_bug["_id"]),
        title=created_bug["title"],
        description=created_bug["description"],
        project_id=created_bug["project_id"],
        created_by=created_bug["created_by"],
        assigned_to=created_bug.get("assigned_to"),
        status=created_bug["status"],
        severity=created_bug["severity"],
        steps_to_reproduce=created_bug.get("steps_to_reproduce"),
        fix_description=created_bug.get("fix_description"),
        bug_images=created_bug.get("bug_images", []),
        fix_images=created_bug.get("fix_images", []),
        attachments=created_bug.get("attachments", []),
        created_at=created_bug["created_at"],
        updated_at=created_bug["updated_at"]
    )


@router.get("/", response_model=List[BugResponse])
async def get_bugs(
    project_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    status: Optional[BugStatus] = None,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取BUG列表（支持过滤）"""
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
    
    bugs = await db.bugs.find(query).to_list(length=None)
    
    return [
        BugResponse(
            id=str(bug["_id"]),
            title=bug["title"],
            description=bug["description"],
            project_id=bug["project_id"],
            created_by=bug["created_by"],
            assigned_to=bug.get("assigned_to"),
            status=bug["status"],
            severity=bug["severity"],
            steps_to_reproduce=bug.get("steps_to_reproduce"),
            fix_description=bug.get("fix_description"),
            bug_images=bug.get("bug_images", []),
            fix_images=bug.get("fix_images", []),
            attachments=bug.get("attachments", []),
            created_at=bug["created_at"],
            updated_at=bug["updated_at"]
        )
        for bug in bugs
    ]


@router.get("/{bug_id}", response_model=BugResponse)
async def get_bug(
    bug_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取指定BUG信息"""
    db = get_database()
    
    try:
        bug = await db.bugs.find_one({"_id": ObjectId(bug_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的BUG ID")
    
    if not bug:
        raise HTTPException(status_code=404, detail="BUG不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(bug["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    return BugResponse(
        id=str(bug["_id"]),
        title=bug["title"],
        description=bug["description"],
        project_id=bug["project_id"],
        created_by=bug["created_by"],
        assigned_to=bug.get("assigned_to"),
        status=bug["status"],
        severity=bug["severity"],
        steps_to_reproduce=bug.get("steps_to_reproduce"),
        fix_description=bug.get("fix_description"),
        bug_images=bug.get("bug_images", []),
        fix_images=bug.get("fix_images", []),
        attachments=bug.get("attachments", []),
        created_at=bug["created_at"],
        updated_at=bug["updated_at"]
    )


@router.put("/{bug_id}", response_model=BugResponse)
async def update_bug(
    bug_id: str,
    bug_update: BugUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """更新BUG信息"""
    db = get_database()
    
    try:
        bug = await db.bugs.find_one({"_id": ObjectId(bug_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的BUG ID")
    
    if not bug:
        raise HTTPException(status_code=404, detail="BUG不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(bug["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    update_data = {k: v for k, v in bug_update.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = get_beijing_time()
    
    old_assigned_to = bug.get("assigned_to")
    new_assigned_to = update_data.get("assigned_to")
    
    # 如果负责人发生变化（流转BUG）
    if "assigned_to" in update_data and new_assigned_to != old_assigned_to:
        # 获取操作人信息
        operator = await db.users.find_one({"_id": ObjectId(current_user.id)})
        operator_name = operator.get("full_name", "某用户") if operator else "某用户"
        
        # 获取新负责人信息
        if new_assigned_to:
            new_assignee = await db.users.find_one({"_id": ObjectId(new_assigned_to)})
            new_assignee_name = new_assignee.get("full_name", "某用户") if new_assignee else "某用户"
        else:
            new_assignee_name = "未分配"
        
        # 1. 通知新负责人
        if new_assigned_to:
            notification_to_new = {
                "user_id": new_assigned_to,
                "type": "bug_transferred",
                "title": "BUG已流转给您",
                "message": f"{operator_name} 将BUG '{bug['title']}' 流转给您处理",
                "bug_id": bug_id,
                "project_id": bug["project_id"],
                "is_read": False,
                "created_at": get_beijing_time()
            }
            await db.notifications.insert_one(notification_to_new)
        
        # 2. 如果不是创建人流转的，通知创建人
        if current_user.id != bug["created_by"]:
            notification_to_creator = {
                "user_id": bug["created_by"],
                "type": "bug_transferred",
                "title": "BUG已被流转",
                "message": f"{operator_name} 将BUG '{bug['title']}' 流转给 {new_assignee_name}",
                "bug_id": bug_id,
                "project_id": bug["project_id"],
                "is_read": False,
                "created_at": get_beijing_time()
            }
            await db.notifications.insert_one(notification_to_creator)
        
        # 3. 如果有旧负责人且不是操作人本人，也通知旧负责人
        if old_assigned_to and old_assigned_to != current_user.id:
            notification_to_old = {
                "user_id": old_assigned_to,
                "type": "bug_transferred",
                "title": "BUG已被流转",
                "message": f"{operator_name} 将BUG '{bug['title']}' 流转给 {new_assignee_name}",
                "bug_id": bug_id,
                "project_id": bug["project_id"],
                "is_read": False,
                "created_at": get_beijing_time()
            }
            await db.notifications.insert_one(notification_to_old)
    
    await db.bugs.update_one(
        {"_id": ObjectId(bug_id)},
        {"$set": update_data}
    )
    
    updated_bug = await db.bugs.find_one({"_id": ObjectId(bug_id)})
    
    return BugResponse(
        id=str(updated_bug["_id"]),
        title=updated_bug["title"],
        description=updated_bug["description"],
        project_id=updated_bug["project_id"],
        created_by=updated_bug["created_by"],
        assigned_to=updated_bug.get("assigned_to"),
        status=updated_bug["status"],
        severity=updated_bug["severity"],
        steps_to_reproduce=updated_bug.get("steps_to_reproduce"),
        fix_description=updated_bug.get("fix_description"),
        bug_images=updated_bug.get("bug_images", []),
        fix_images=updated_bug.get("fix_images", []),
        attachments=updated_bug.get("attachments", []),
        created_at=updated_bug["created_at"],
        updated_at=updated_bug["updated_at"]
    )


@router.post("/{bug_id}/upload", response_model=BugResponse)
async def upload_bug_attachment(
    bug_id: str,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """上传BUG附件"""
    db = get_database()
    
    try:
        bug = await db.bugs.find_one({"_id": ObjectId(bug_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的BUG ID")
    
    if not bug:
        raise HTTPException(status_code=404, detail="BUG不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(bug["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 创建上传目录
    upload_dir = os.path.join(settings.UPLOAD_DIR, "bugs", bug_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # 保存文件
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    # 更新BUG附件列表
    relative_path = os.path.join("bugs", bug_id, unique_filename)
    await db.bugs.update_one(
        {"_id": ObjectId(bug_id)},
        {
            "$push": {"attachments": relative_path},
            "$set": {"updated_at": get_beijing_time()}
        }
    )
    
    updated_bug = await db.bugs.find_one({"_id": ObjectId(bug_id)})
    
    return BugResponse(
        id=str(updated_bug["_id"]),
        title=updated_bug["title"],
        description=updated_bug["description"],
        project_id=updated_bug["project_id"],
        created_by=updated_bug["created_by"],
        assigned_to=updated_bug.get("assigned_to"),
        status=updated_bug["status"],
        severity=updated_bug["severity"],
        steps_to_reproduce=updated_bug.get("steps_to_reproduce"),
        fix_description=updated_bug.get("fix_description"),
        bug_images=updated_bug.get("bug_images", []),
        fix_images=updated_bug.get("fix_images", []),
        attachments=updated_bug.get("attachments", []),
        created_at=updated_bug["created_at"],
        updated_at=updated_bug["updated_at"]
    )


@router.post("/{bug_id}/retest", response_model=BugResponse)
async def start_bug_retest(
    bug_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """开始复测BUG"""
    db = get_database()
    
    try:
        bug = await db.bugs.find_one({"_id": ObjectId(bug_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的BUG ID")
    
    if not bug:
        raise HTTPException(status_code=404, detail="BUG不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(bug["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 只有状态为IN_PROGRESS的BUG才能提交复测
    if bug["status"] != BugStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="只有处理中的BUG才能提交复测")
    
    await db.bugs.update_one(
        {"_id": ObjectId(bug_id)},
        {"$set": {"status": BugStatus.TESTING, "updated_at": get_beijing_time()}}
    )
    
    # 获取提交人信息
    submitter = await db.users.find_one({"_id": ObjectId(current_user.id)})
    submitter_name = submitter.get("full_name", "开发人员") if submitter else "开发人员"
    
    # 通知BUG创建者进行复测
    notification = {
        "user_id": bug["created_by"],
        "type": "bug_retest_submitted",
        "title": "BUG已提交复测",
        "message": f"{submitter_name} 已修复BUG '{bug['title']}' 并提交复测，请尽快验证",
        "bug_id": bug_id,
        "project_id": bug["project_id"],
        "is_read": False,
        "created_at": get_beijing_time()
    }
    await db.notifications.insert_one(notification)
    
    updated_bug = await db.bugs.find_one({"_id": ObjectId(bug_id)})
    
    return BugResponse(
        id=str(updated_bug["_id"]),
        title=updated_bug["title"],
        description=updated_bug["description"],
        project_id=updated_bug["project_id"],
        created_by=updated_bug["created_by"],
        assigned_to=updated_bug.get("assigned_to"),
        status=updated_bug["status"],
        severity=updated_bug["severity"],
        steps_to_reproduce=updated_bug.get("steps_to_reproduce"),
        fix_description=updated_bug.get("fix_description"),
        bug_images=updated_bug.get("bug_images", []),
        fix_images=updated_bug.get("fix_images", []),
        attachments=updated_bug.get("attachments", []),
        created_at=updated_bug["created_at"],
        updated_at=updated_bug["updated_at"]
    )


@router.post("/{bug_id}/close", response_model=BugResponse)
async def close_bug(
    bug_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """关闭BUG（复测成功）"""
    db = get_database()
    
    try:
        bug = await db.bugs.find_one({"_id": ObjectId(bug_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的BUG ID")
    
    if not bug:
        raise HTTPException(status_code=404, detail="BUG不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(bug["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    await db.bugs.update_one(
        {"_id": ObjectId(bug_id)},
        {"$set": {"status": BugStatus.CLOSED, "updated_at": get_beijing_time()}}
    )
    
    # 获取复测人信息
    tester = await db.users.find_one({"_id": ObjectId(current_user.id)})
    tester_name = tester.get("full_name", "测试人员") if tester else "测试人员"
    
    # 通知BUG负责人（开发人员）
    if bug.get("assigned_to"):
        notification_to_dev = {
            "user_id": bug["assigned_to"],
            "type": "bug_closed",
            "title": "BUG复测通过",
            "message": f"{tester_name} 已验证BUG '{bug['title']}' 修复成功，复测通过并关闭",
            "bug_id": bug_id,
            "project_id": bug["project_id"],
            "is_read": False,
            "created_at": get_beijing_time()
        }
        await db.notifications.insert_one(notification_to_dev)
    
    updated_bug = await db.bugs.find_one({"_id": ObjectId(bug_id)})
    
    return BugResponse(
        id=str(updated_bug["_id"]),
        title=updated_bug["title"],
        description=updated_bug["description"],
        project_id=updated_bug["project_id"],
        created_by=updated_bug["created_by"],
        assigned_to=updated_bug.get("assigned_to"),
        status=updated_bug["status"],
        severity=updated_bug["severity"],
        steps_to_reproduce=updated_bug.get("steps_to_reproduce"),
        fix_description=updated_bug.get("fix_description"),
        bug_images=updated_bug.get("bug_images", []),
        fix_images=updated_bug.get("fix_images", []),
        attachments=updated_bug.get("attachments", []),
        created_at=updated_bug["created_at"],
        updated_at=updated_bug["updated_at"]
    )


@router.post("/{bug_id}/reopen", response_model=BugResponse)
async def reopen_bug(
    bug_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """复测失败，打回BUG"""
    db = get_database()
    
    try:
        bug = await db.bugs.find_one({"_id": ObjectId(bug_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的BUG ID")
    
    if not bug:
        raise HTTPException(status_code=404, detail="BUG不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(bug["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 复测失败后退回到"已分配"状态，需要重新接收
    await db.bugs.update_one(
        {"_id": ObjectId(bug_id)},
        {"$set": {"status": BugStatus.ASSIGNED, "updated_at": get_beijing_time()}}
    )
    
    # 获取复测人信息
    tester = await db.users.find_one({"_id": ObjectId(current_user.id)})
    tester_name = tester.get("full_name", "测试人员") if tester else "测试人员"
    
    # 通知BUG负责人（开发人员）
    if bug.get("assigned_to"):
        notification = {
            "user_id": bug["assigned_to"],
            "type": "bug_reopened",
            "title": "BUG复测失败",
            "message": f"{tester_name} 复测BUG '{bug['title']}' 未通过，已打回至'已分配'状态，请重新接收处理",
            "bug_id": bug_id,
            "project_id": bug["project_id"],
            "is_read": False,
            "created_at": get_beijing_time()
        }
        await db.notifications.insert_one(notification)
    
    updated_bug = await db.bugs.find_one({"_id": ObjectId(bug_id)})
    
    return BugResponse(
        id=str(updated_bug["_id"]),
        title=updated_bug["title"],
        description=updated_bug["description"],
        project_id=updated_bug["project_id"],
        created_by=updated_bug["created_by"],
        assigned_to=updated_bug.get("assigned_to"),
        status=updated_bug["status"],
        severity=updated_bug["severity"],
        steps_to_reproduce=updated_bug.get("steps_to_reproduce"),
        fix_description=updated_bug.get("fix_description"),
        bug_images=updated_bug.get("bug_images", []),
        fix_images=updated_bug.get("fix_images", []),
        attachments=updated_bug.get("attachments", []),
        created_at=updated_bug["created_at"],
        updated_at=updated_bug["updated_at"]
    )


@router.delete("/{bug_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bug(
    bug_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """删除BUG"""
    db = get_database()
    
    try:
        bug = await db.bugs.find_one({"_id": ObjectId(bug_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的BUG ID")
    
    if not bug:
        raise HTTPException(status_code=404, detail="BUG不存在")
    
    # 只有BUG创建者、项目所有者或管理员可以删除BUG
    project = await db.projects.find_one({"_id": ObjectId(bug["project_id"])})
    if (current_user.role != UserRole.ADMIN and 
        current_user.id != bug["created_by"] and 
        current_user.id != project["owner_id"]):
        raise HTTPException(status_code=403, detail="没有权限")
    
    await db.bugs.delete_one({"_id": ObjectId(bug_id)})
    
    return None


# BUG评论相关API
@router.get("/{bug_id}/comments", response_model=List[BugCommentResponse])
async def get_bug_comments(
    bug_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取BUG的所有评论"""
    db = get_database()
    
    try:
        bug = await db.bugs.find_one({"_id": ObjectId(bug_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的BUG ID")
    
    if not bug:
        raise HTTPException(status_code=404, detail="BUG不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(bug["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 获取评论列表
    comments = await db.bug_comments.find({"bug_id": bug_id}).sort("created_at", 1).to_list(length=None)
    
    result = []
    for comment in comments:
        # 获取评论者信息
        user = await db.users.find_one({"_id": ObjectId(comment["user_id"])})
        user_name = user.get("full_name", "未知用户") if user else "未知用户"
        
        result.append(BugCommentResponse(
            id=str(comment["_id"]),
            bug_id=comment["bug_id"],
            user_id=comment["user_id"],
            user_name=user_name,
            content=comment["content"],
            created_at=comment["created_at"]
        ))
    
    return result


@router.post("/{bug_id}/comments", response_model=BugCommentResponse, status_code=status.HTTP_201_CREATED)
async def create_bug_comment(
    bug_id: str,
    comment: BugCommentCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """添加BUG评论"""
    db = get_database()
    
    try:
        bug = await db.bugs.find_one({"_id": ObjectId(bug_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的BUG ID")
    
    if not bug:
        raise HTTPException(status_code=404, detail="BUG不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(bug["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 创建评论
    comment_dict = {
        "bug_id": bug_id,
        "user_id": current_user.id,
        "content": comment.content,
        "created_at": get_beijing_time()
    }
    
    result = await db.bug_comments.insert_one(comment_dict)
    created_comment = await db.bug_comments.find_one({"_id": result.inserted_id})
    
    # 通知相关人员（创建者和负责人）
    notify_users = set()
    if bug.get("created_by") and bug["created_by"] != current_user.id:
        notify_users.add(bug["created_by"])
    if bug.get("assigned_to") and bug["assigned_to"] != current_user.id:
        notify_users.add(bug["assigned_to"])
    
    for user_id in notify_users:
        notification = {
            "user_id": user_id,
            "type": "bug_comment",
            "title": "BUG新评论",
            "message": f"{current_user.full_name} 在BUG '{bug['title']}' 中添加了评论",
            "bug_id": bug_id,
            "project_id": bug["project_id"],
            "is_read": False,
            "created_at": get_beijing_time()
        }
        await db.notifications.insert_one(notification)
    
    return BugCommentResponse(
        id=str(created_comment["_id"]),
        bug_id=created_comment["bug_id"],
        user_id=created_comment["user_id"],
        user_name=current_user.full_name,
        content=created_comment["content"],
        created_at=created_comment["created_at"]
    )

