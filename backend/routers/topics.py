from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from typing import List, Optional
from database import get_database
from models import TopicCreate, TopicUpdate, TopicResponse, TopicStatus, TopicCommentCreate, TopicCommentResponse, UserResponse, UserRole
from auth import get_current_active_user
from bson import ObjectId
from datetime import datetime
from utils import get_beijing_time
import os
import aiofiles
from config import settings
import uuid
from services.email_service import EmailService

router = APIRouter(prefix="/api/topics", tags=["课题管理"])


async def generate_topic_number(db) -> str:
    """
    生成课题号：DB+年月日+序列号
    例如：DB20260126001, DB20260126002, ...
    如果有1000个，则为：DB202601261000
    """
    now = get_beijing_time()
    date_str = now.strftime("%Y%m%d")  # 例如：20260126
    prefix = f"DB{date_str}"
    
    # 查找今天已有的最大序列号
    # 使用正则表达式匹配今天的课题号
    pattern = f"^{prefix}"
    existing_topics = await db.topics.find(
        {"topic_number": {"$regex": pattern}}
    ).sort("topic_number", -1).limit(1).to_list(length=1)
    
    if existing_topics:
        # 提取最后一个课题号的序列号部分
        last_number = existing_topics[0]["topic_number"]
        # 获取序列号部分（去掉前缀）
        sequence_str = last_number[len(prefix):]
        sequence = int(sequence_str) + 1
    else:
        sequence = 1
    
    # 格式化序列号，至少3位数字，不足补0
    sequence_str = str(sequence).zfill(3)
    topic_number = f"{prefix}{sequence_str}"
    
    return topic_number


@router.post("/", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(
    topic: TopicCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """创建新课题"""
    db = get_database()
    
    # 检查项目是否存在
    try:
        project = await db.projects.find_one({"_id": ObjectId(topic.project_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查用户是否在项目团队中
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 如果指定了分配对象，检查该用户是否在项目团队中
    if topic.assigned_to:
        if topic.assigned_to not in project["team_members"]:
            raise HTTPException(status_code=400, detail="被分配用户不在项目团队中")
    
    # 生成课题号
    topic_number = await generate_topic_number(db)
    
    topic_dict = {
        "topic_number": topic_number,
        "title": topic.title,
        "description": topic.description,
        "project_id": topic.project_id,
        "created_by": current_user.id,
        "assigned_to": topic.assigned_to,
        "status": TopicStatus.OPEN if not topic.assigned_to else TopicStatus.ASSIGNED,
        "severity": topic.severity,
        "steps_to_reproduce": topic.steps_to_reproduce,
        "fix_description": None,
        "topic_images": topic.topic_images,  # 课题截图（base64）
        "fix_images": [],  # 修复截图（base64）
        "attachments": [],
        "created_at": get_beijing_time(),
        "updated_at": get_beijing_time()
    }
    
    result = await db.topics.insert_one(topic_dict)
    created_topic = await db.topics.find_one({"_id": result.inserted_id})
    
    # 如果分配了课题，创建通知并发送邮件
    if topic.assigned_to:
        notification = {
            "user_id": topic.assigned_to,
            "type": "topic_assigned",
            "title": "新的课题分配",
            "message": f"您有一个新的课题: {topic.title}",
            "topic_id": str(result.inserted_id),
            "project_id": topic.project_id,
            "is_read": False,
            "created_at": get_beijing_time()
        }
        await db.notifications.insert_one(notification)
        
        # 发送邮件提醒
        try:
            # 获取负责人信息
            assignee = await db.users.find_one({"_id": ObjectId(topic.assigned_to)})
            if assignee and assignee.get("email"):
                # 获取创建人信息
                creator = await db.users.find_one({"_id": ObjectId(current_user.id)})
                creator_name = creator.get("full_name", current_user.username) if creator else current_user.username
                
                # 获取邮件配置
                email_config = await EmailService.get_config()
                if email_config:
                    # 生成课题详情链接
                    topic_url = f"{settings.FRONTEND_URL}/topics/{str(result.inserted_id)}"
                    
                    # 构造邮件内容
                    subject = "您有一个新的课题，请及时处理"
                    content = f"""
                    <div style="padding: 20px; background-color: #f8fafc; font-family: 'Microsoft YaHei', sans-serif;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                            <h2 style="color: #1e293b; margin-bottom: 24px;">您有一个新的课题，请及时处理：</h2>
                            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                                <tr>
                                    <td style="padding: 12px 0; color: #64748b; width: 120px;">RequestNo 课题号</td>
                                    <td style="padding: 12px 0; color: #1e293b;">：</td>
                                    <td style="padding: 12px 0;">
                                        <a href="{topic_url}" style="color: #2563eb; text-decoration: none; font-weight: 600;">{topic_number}</a>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; color: #64748b;">ProblemTitle 问题标题</td>
                                    <td style="padding: 12px 0; color: #1e293b;">：</td>
                                    <td style="padding: 12px 0; color: #1e293b;">{topic.title}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; color: #64748b;">FromUser 流转自</td>
                                    <td style="padding: 12px 0; color: #1e293b;">：</td>
                                    <td style="padding: 12px 0; color: #1e293b;">{creator_name}</td>
                                </tr>
                            </table>
                            <div style="background-color: #fef2f2; padding: 15px; border-radius: 8px; margin-top: 20px;">
                                <p style="color: #dc2626; margin: 0; font-size: 14px;">
                                    <strong>注意：</strong>本邮件为系统自动发布，请勿回复
                                </p>
                            </div>
                            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                            <p style="color: #94a3b8; font-size: 12px; text-align: center;">项目管理系统 - 智能办公专家</p>
                        </div>
                    </div>
                    """
                    
                    # 发送邮件
                    EmailService.send_email(email_config, assignee["email"], subject, content)
                    print(f"[INFO] 课题创建邮件已发送至: {assignee['email']}")
        except Exception as e:
            # 邮件发送失败不影响课题创建
            print(f"[WARN] 发送课题创建邮件失败: {str(e)}")
    
    return TopicResponse(
        id=str(created_topic["_id"]),
        topic_number=created_topic["topic_number"],
        title=created_topic["title"],
        description=created_topic["description"],
        project_id=created_topic["project_id"],
        created_by=created_topic["created_by"],
        assigned_to=created_topic.get("assigned_to"),
        status=created_topic["status"],
        severity=created_topic["severity"],
        steps_to_reproduce=created_topic.get("steps_to_reproduce"),
        fix_description=created_topic.get("fix_description"),
        topic_images=created_topic.get("topic_images", []),
        fix_images=created_topic.get("fix_images", []),
        attachments=created_topic.get("attachments", []),
        created_at=created_topic["created_at"],
        updated_at=created_topic["updated_at"]
    )


@router.get("/")
async def get_topics(
    project_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    status: Optional[TopicStatus] = None,
    severity: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取课题列表（支持分页、过滤和搜索）"""
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
    
    if severity:
        query["severity"] = severity
    
    # 关键词搜索：支持课题号、标题、描述
    if keyword:
        query["$or"] = [
            {"topic_number": {"$regex": keyword, "$options": "i"}},
            {"title": {"$regex": keyword, "$options": "i"}},
            {"description": {"$regex": keyword, "$options": "i"}}
        ]
    
    # 计算总数
    total = await db.topics.count_documents(query)
    
    # 分页查询
    skip = (page - 1) * page_size
    topics = await db.topics.find(query).sort("created_at", -1).skip(skip).limit(page_size).to_list(length=page_size)
    
    items = [
        TopicResponse(
            id=str(topic["_id"]),
            topic_number=topic.get("topic_number", ""),
            title=topic["title"],
            description=topic["description"],
            project_id=topic["project_id"],
            created_by=topic["created_by"],
            assigned_to=topic.get("assigned_to"),
            status=topic["status"],
            severity=topic["severity"],
            steps_to_reproduce=topic.get("steps_to_reproduce"),
            fix_description=topic.get("fix_description"),
            topic_images=topic.get("topic_images", []),
            fix_images=topic.get("fix_images", []),
            attachments=topic.get("attachments", []),
            created_at=topic["created_at"],
            updated_at=topic["updated_at"]
        )
        for topic in topics
    ]
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取指定课题信息"""
    db = get_database()
    
    try:
        topic = await db.topics.find_one({"_id": ObjectId(topic_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的课题ID")
    
    if not topic:
        raise HTTPException(status_code=404, detail="课题不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(topic["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    return TopicResponse(
        id=str(topic["_id"]),
        topic_number=topic.get("topic_number", ""),
        title=topic["title"],
        description=topic["description"],
        project_id=topic["project_id"],
        created_by=topic["created_by"],
        assigned_to=topic.get("assigned_to"),
        status=topic["status"],
        severity=topic["severity"],
        steps_to_reproduce=topic.get("steps_to_reproduce"),
        fix_description=topic.get("fix_description"),
        topic_images=topic.get("topic_images", []),
        fix_images=topic.get("fix_images", []),
        attachments=topic.get("attachments", []),
        created_at=topic["created_at"],
        updated_at=topic["updated_at"]
    )


@router.put("/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: str,
    topic_update: TopicUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """更新课题信息"""
    db = get_database()
    
    try:
        topic = await db.topics.find_one({"_id": ObjectId(topic_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的课题ID")
    
    if not topic:
        raise HTTPException(status_code=404, detail="课题不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(topic["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    update_data = {k: v for k, v in topic_update.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = get_beijing_time()
    
    # 如果更新了负责人，检查新负责人是否在项目团队中
    if "assigned_to" in update_data and update_data["assigned_to"]:
        if update_data["assigned_to"] not in project["team_members"]:
            raise HTTPException(status_code=400, detail="负责人必须是项目团队成员")
    
    old_assigned_to = topic.get("assigned_to")
    new_assigned_to = update_data.get("assigned_to")
    
    # 如果负责人发生变化（流转课题）
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
                "type": "topic_transferred",
                "title": "课题已流转给您",
                "message": f"{operator_name} 将课题 '{topic['title']}' 流转给您处理",
                "topic_id": topic_id,
                "project_id": topic["project_id"],
                "is_read": False,
                "created_at": get_beijing_time()
            }
            await db.notifications.insert_one(notification_to_new)
        
        # 2. 如果不是创建人流转的，通知创建人
        if current_user.id != topic["created_by"]:
            notification_to_creator = {
                "user_id": topic["created_by"],
                "type": "topic_transferred",
                "title": "课题已被流转",
                "message": f"{operator_name} 将课题 '{topic['title']}' 流转给 {new_assignee_name}",
                "topic_id": topic_id,
                "project_id": topic["project_id"],
                "is_read": False,
                "created_at": get_beijing_time()
            }
            await db.notifications.insert_one(notification_to_creator)
        
        # 3. 如果有旧负责人且不是操作人本人，也通知旧负责人
        if old_assigned_to and old_assigned_to != current_user.id:
            notification_to_old = {
                "user_id": old_assigned_to,
                "type": "topic_transferred",
                "title": "课题已被流转",
                "message": f"{operator_name} 将课题 '{topic['title']}' 流转给 {new_assignee_name}",
                "topic_id": topic_id,
                "project_id": topic["project_id"],
                "is_read": False,
                "created_at": get_beijing_time()
            }
            await db.notifications.insert_one(notification_to_old)
    
    await db.topics.update_one(
        {"_id": ObjectId(topic_id)},
        {"$set": update_data}
    )
    
    updated_topic = await db.topics.find_one({"_id": ObjectId(topic_id)})
    
    return TopicResponse(
        id=str(updated_topic["_id"]),
        topic_number=updated_topic.get("topic_number", ""),
        title=updated_topic["title"],
        description=updated_topic["description"],
        project_id=updated_topic["project_id"],
        created_by=updated_topic["created_by"],
        assigned_to=updated_topic.get("assigned_to"),
        status=updated_topic["status"],
        severity=updated_topic["severity"],
        steps_to_reproduce=updated_topic.get("steps_to_reproduce"),
        fix_description=updated_topic.get("fix_description"),
        topic_images=updated_topic.get("topic_images", []),
        fix_images=updated_topic.get("fix_images", []),
        attachments=updated_topic.get("attachments", []),
        created_at=updated_topic["created_at"],
        updated_at=updated_topic["updated_at"]
    )


@router.post("/{topic_id}/upload", response_model=TopicResponse)
async def upload_topic_attachment(
    topic_id: str,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """上传课题附件"""
    db = get_database()
    
    try:
        topic = await db.topics.find_one({"_id": ObjectId(topic_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的课题ID")
    
    if not topic:
        raise HTTPException(status_code=404, detail="课题不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(topic["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 创建上传目录
    upload_dir = os.path.join(settings.UPLOAD_DIR, "topics", topic_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # 保存文件
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    # 更新课题附件列表
    relative_path = os.path.join("topics", topic_id, unique_filename)
    await db.topics.update_one(
        {"_id": ObjectId(topic_id)},
        {
            "$push": {"attachments": relative_path},
            "$set": {"updated_at": get_beijing_time()}
        }
    )
    
    updated_topic = await db.topics.find_one({"_id": ObjectId(topic_id)})
    
    return TopicResponse(
        id=str(updated_topic["_id"]),
        topic_number=updated_topic.get("topic_number", ""),
        title=updated_topic["title"],
        description=updated_topic["description"],
        project_id=updated_topic["project_id"],
        created_by=updated_topic["created_by"],
        assigned_to=updated_topic.get("assigned_to"),
        status=updated_topic["status"],
        severity=updated_topic["severity"],
        steps_to_reproduce=updated_topic.get("steps_to_reproduce"),
        fix_description=updated_topic.get("fix_description"),
        topic_images=updated_topic.get("topic_images", []),
        fix_images=updated_topic.get("fix_images", []),
        attachments=updated_topic.get("attachments", []),
        created_at=updated_topic["created_at"],
        updated_at=updated_topic["updated_at"]
    )


@router.post("/{topic_id}/retest", response_model=TopicResponse)
async def start_topic_retest(
    topic_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """开始复测课题"""
    db = get_database()
    
    try:
        topic = await db.topics.find_one({"_id": ObjectId(topic_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的课题ID")
    
    if not topic:
        raise HTTPException(status_code=404, detail="课题不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(topic["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 只有状态为IN_PROGRESS的课题才能提交复测
    if topic["status"] != TopicStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="只有处理中的课题才能提交复测")
    
    await db.topics.update_one(
        {"_id": ObjectId(topic_id)},
        {"$set": {"status": TopicStatus.TESTING, "updated_at": get_beijing_time()}}
    )
    
    # 获取提交人信息
    submitter = await db.users.find_one({"_id": ObjectId(current_user.id)})
    submitter_name = submitter.get("full_name", "开发人员") if submitter else "开发人员"
    
    # 通知课题创建者进行复测
    notification = {
        "user_id": topic["created_by"],
        "type": "topic_retest_submitted",
        "title": "课题已提交复测",
        "message": f"{submitter_name} 已修复课题 '{topic['title']}' 并提交复测，请尽快验证",
        "topic_id": topic_id,
        "project_id": topic["project_id"],
        "is_read": False,
        "created_at": get_beijing_time()
    }
    await db.notifications.insert_one(notification)
    
    updated_topic = await db.topics.find_one({"_id": ObjectId(topic_id)})
    
    return TopicResponse(
        id=str(updated_topic["_id"]),
        topic_number=updated_topic.get("topic_number", ""),
        title=updated_topic["title"],
        description=updated_topic["description"],
        project_id=updated_topic["project_id"],
        created_by=updated_topic["created_by"],
        assigned_to=updated_topic.get("assigned_to"),
        status=updated_topic["status"],
        severity=updated_topic["severity"],
        steps_to_reproduce=updated_topic.get("steps_to_reproduce"),
        fix_description=updated_topic.get("fix_description"),
        topic_images=updated_topic.get("topic_images", []),
        fix_images=updated_topic.get("fix_images", []),
        attachments=updated_topic.get("attachments", []),
        created_at=updated_topic["created_at"],
        updated_at=updated_topic["updated_at"]
    )


@router.post("/{topic_id}/close", response_model=TopicResponse)
async def close_topic(
    topic_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """关闭课题（复测成功）"""
    db = get_database()
    
    try:
        topic = await db.topics.find_one({"_id": ObjectId(topic_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的课题ID")
    
    if not topic:
        raise HTTPException(status_code=404, detail="课题不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(topic["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    await db.topics.update_one(
        {"_id": ObjectId(topic_id)},
        {"$set": {"status": TopicStatus.CLOSED, "updated_at": get_beijing_time()}}
    )
    
    # 获取复测人信息
    tester = await db.users.find_one({"_id": ObjectId(current_user.id)})
    tester_name = tester.get("full_name", "测试人员") if tester else "测试人员"
    
    # 通知课题负责人（开发人员）
    if topic.get("assigned_to"):
        notification_to_dev = {
            "user_id": topic["assigned_to"],
            "type": "topic_closed",
            "title": "课题复测通过",
            "message": f"{tester_name} 已验证课题 '{topic['title']}' 修复成功，复测通过并关闭",
            "topic_id": topic_id,
            "project_id": topic["project_id"],
            "is_read": False,
            "created_at": get_beijing_time()
        }
        await db.notifications.insert_one(notification_to_dev)
    
    updated_topic = await db.topics.find_one({"_id": ObjectId(topic_id)})
    
    return TopicResponse(
        id=str(updated_topic["_id"]),
        topic_number=updated_topic.get("topic_number", ""),
        title=updated_topic["title"],
        description=updated_topic["description"],
        project_id=updated_topic["project_id"],
        created_by=updated_topic["created_by"],
        assigned_to=updated_topic.get("assigned_to"),
        status=updated_topic["status"],
        severity=updated_topic["severity"],
        steps_to_reproduce=updated_topic.get("steps_to_reproduce"),
        fix_description=updated_topic.get("fix_description"),
        topic_images=updated_topic.get("topic_images", []),
        fix_images=updated_topic.get("fix_images", []),
        attachments=updated_topic.get("attachments", []),
        created_at=updated_topic["created_at"],
        updated_at=updated_topic["updated_at"]
    )


@router.post("/{topic_id}/reopen", response_model=TopicResponse)
async def reopen_topic(
    topic_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """复测失败，打回课题"""
    db = get_database()
    
    try:
        topic = await db.topics.find_one({"_id": ObjectId(topic_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的课题ID")
    
    if not topic:
        raise HTTPException(status_code=404, detail="课题不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(topic["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 复测失败后退回到"已分配"状态，需要重新接收
    await db.topics.update_one(
        {"_id": ObjectId(topic_id)},
        {"$set": {"status": TopicStatus.ASSIGNED, "updated_at": get_beijing_time()}}
    )
    
    # 获取复测人信息
    tester = await db.users.find_one({"_id": ObjectId(current_user.id)})
    tester_name = tester.get("full_name", "测试人员") if tester else "测试人员"
    
    # 通知课题负责人（开发人员）
    if topic.get("assigned_to"):
        notification = {
            "user_id": topic["assigned_to"],
            "type": "topic_reopened",
            "title": "课题复测失败",
            "message": f"{tester_name} 复测课题 '{topic['title']}' 未通过，已打回至'已分配'状态，请重新接收处理",
            "topic_id": topic_id,
            "project_id": topic["project_id"],
            "is_read": False,
            "created_at": get_beijing_time()
        }
        await db.notifications.insert_one(notification)
    
    updated_topic = await db.topics.find_one({"_id": ObjectId(topic_id)})
    
    return TopicResponse(
        id=str(updated_topic["_id"]),
        topic_number=updated_topic.get("topic_number", ""),
        title=updated_topic["title"],
        description=updated_topic["description"],
        project_id=updated_topic["project_id"],
        created_by=updated_topic["created_by"],
        assigned_to=updated_topic.get("assigned_to"),
        status=updated_topic["status"],
        severity=updated_topic["severity"],
        steps_to_reproduce=updated_topic.get("steps_to_reproduce"),
        fix_description=updated_topic.get("fix_description"),
        topic_images=updated_topic.get("topic_images", []),
        fix_images=updated_topic.get("fix_images", []),
        attachments=updated_topic.get("attachments", []),
        created_at=updated_topic["created_at"],
        updated_at=updated_topic["updated_at"]
    )


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """删除课题"""
    db = get_database()
    
    try:
        topic = await db.topics.find_one({"_id": ObjectId(topic_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的课题ID")
    
    if not topic:
        raise HTTPException(status_code=404, detail="课题不存在")
    
    # 只有课题创建者、项目所有者或管理员可以删除课题
    project = await db.projects.find_one({"_id": ObjectId(topic["project_id"])})
    if (current_user.role != UserRole.ADMIN and 
        current_user.id != topic["created_by"] and 
        current_user.id != project["owner_id"]):
        raise HTTPException(status_code=403, detail="没有权限")
    
    await db.topics.delete_one({"_id": ObjectId(topic_id)})
    
    return None


# 课题评论相关API
@router.get("/{topic_id}/comments", response_model=List[TopicCommentResponse])
async def get_topic_comments(
    topic_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取课题的所有评论"""
    db = get_database()
    
    try:
        topic = await db.topics.find_one({"_id": ObjectId(topic_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的课题ID")
    
    if not topic:
        raise HTTPException(status_code=404, detail="课题不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(topic["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 获取评论列表
    comments = await db.topic_comments.find({"topic_id": topic_id}).sort("created_at", 1).to_list(length=None)
    
    result = []
    for comment in comments:
        # 获取评论者信息
        user = await db.users.find_one({"_id": ObjectId(comment["user_id"])})
        user_name = user.get("full_name", "未知用户") if user else "未知用户"
        
        result.append(TopicCommentResponse(
            id=str(comment["_id"]),
            topic_id=comment["topic_id"],
            user_id=comment["user_id"],
            user_name=user_name,
            content=comment["content"],
            created_at=comment["created_at"]
        ))
    
    return result


# 辅助函数：后台异步发送课题消息邮件
def send_topic_comment_email_bg(email_config, recipient_email, topic_url, topic_number, topic_title, sender_name):
    try:
        subject = "您有一个新的课题消息，请及时查看"
        content = f"""
        <div style="padding: 20px; background-color: #f8fafc; font-family: 'Microsoft YaHei', sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h2 style="color: #1e293b; margin-bottom: 24px;">您有一个新的课题消息，请及时查看：</h2>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr>
                        <td style="padding: 12px 0; color: #64748b; width: 120px;">RequestNo 课题号</td>
                        <td style="padding: 12px 0; color: #1e293b;">：</td>
                        <td style="padding: 12px 0;">
                            <a href="{topic_url}" style="color: #2563eb; text-decoration: none; font-weight: 600;">{topic_number}</a>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 0; color: #64748b;">ProblemTitle 问题标题</td>
                        <td style="padding: 12px 0; color: #1e293b;">：</td>
                        <td style="padding: 12px 0; color: #1e293b;">{topic_title}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 0; color: #64748b;">FromUser 发送自</td>
                        <td style="padding: 12px 0; color: #1e293b;">：</td>
                        <td style="padding: 12px 0; color: #1e293b;">{sender_name}</td>
                    </tr>
                </table>
                <div style="background-color: #fef2f2; padding: 15px; border-radius: 8px; margin-top: 20px;">
                    <p style="color: #dc2626; margin: 0; font-size: 14px;">
                        <strong>注意：</strong>本邮件为系统自动发布，请勿回复
                    </p>
                </div>
                <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                <p style="color: #94a3b8; font-size: 12px; text-align: center;">项目管理系统 - 智能办公专家</p>
            </div>
        </div>
        """
        EmailService.send_email(email_config, recipient_email, subject, content)
        print(f"[INFO] 课题新消息邮件已成功异步发送至: {recipient_email}")
    except Exception as e:
        print(f"[WARN] 异步发送课题新消息邮件失败: {str(e)}")


@router.post("/{topic_id}/comments", response_model=TopicCommentResponse, status_code=status.HTTP_201_CREATED)
async def create_topic_comment(
    topic_id: str,
    comment: TopicCommentCreate,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """添加课题评论"""
    db = get_database()
    
    try:
        topic = await db.topics.find_one({"_id": ObjectId(topic_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的课题ID")
    
    if not topic:
        raise HTTPException(status_code=404, detail="课题不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(topic["project_id"])})
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 创建评论
    comment_dict = {
        "topic_id": topic_id,
        "user_id": current_user.id,
        "content": comment.content,
        "created_at": get_beijing_time()
    }
    
    result = await db.topic_comments.insert_one(comment_dict)
    created_comment = await db.topic_comments.find_one({"_id": result.inserted_id})
    
    # 通知相关人员（创建者和负责人）
    notify_users = set()
    
    # 正常逻辑：只发给他人
    if topic.get("created_by") and topic["created_by"] != current_user.id:
        notify_users.add(topic["created_by"])
    if topic.get("assigned_to") and topic["assigned_to"] != current_user.id:
        notify_users.add(topic["assigned_to"])
            
    print(f"[DEBUG] 发表评论，准备通知的用户ID列表: {list(notify_users)}")
    
    # 获取邮件配置
    email_config = None
    try:
        email_config = await EmailService.get_config()
        if not email_config:
            print("[WARN] 数据库中没有启用(is_enabled=True)的邮件配置")
    except Exception as e:
        print(f"[WARN] 获取邮件配置异常: {str(e)}")

    for user_id in notify_users:
        notification = {
            "user_id": user_id,
            "type": "topic_comment",
            "title": "课题新评论",
            "message": f"{current_user.full_name} 在课题 '{topic['title']}' 中添加了评论",
            "topic_id": topic_id,
            "project_id": topic["project_id"],
            "is_read": False,
            "created_at": get_beijing_time()
        }
        await db.notifications.insert_one(notification)
        
        # 异步发送邮件提醒
        if email_config:
            try:
                # 获取接收人邮箱信息
                recipient = await db.users.find_one({"_id": ObjectId(user_id)})
                if recipient and recipient.get("email"):
                    # 生成课题详情链接
                    topic_url = f"{settings.FRONTEND_URL}/topics/{topic_id}"
                    topic_number = topic.get('topic_number', '')
                    topic_title = topic.get('title', '')
                    sender_name = current_user.full_name
                    
                    print(f"[DEBUG] 将邮件任务加入后台: 发送至 {recipient['email']}")
                    background_tasks.add_task(
                        send_topic_comment_email_bg,
                        email_config,
                        recipient["email"],
                        topic_url,
                        topic_number,
                        topic_title,
                        sender_name
                    )
                else:
                    print(f"[WARN] 接收人 {user_id} 没有配置邮箱信息")
            except Exception as mail_err:
                print(f"[WARN] 准备发送邮件提醒时出错: {str(mail_err)}")
    
    return TopicCommentResponse(
        id=str(created_comment["_id"]),
        topic_id=created_comment["topic_id"],
        user_id=created_comment["user_id"],
        user_name=current_user.full_name,
        content=created_comment["content"],
        created_at=created_comment["created_at"]
    )
