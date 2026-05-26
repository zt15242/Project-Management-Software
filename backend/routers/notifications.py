from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from database import get_database
from models import UserResponse
from auth import get_current_active_user
from bson import ObjectId
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/notifications", tags=["通知管理"])


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    message: str
    topic_id: Optional[str] = None
    project_id: Optional[str] = None
    is_read: bool
    created_at: datetime


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = False,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取当前用户的通知列表"""
    db = get_database()
    
    query = {"user_id": current_user.id}
    if unread_only:
        query["is_read"] = False
    
    notifications = await db.notifications.find(query).sort("created_at", -1).to_list(length=None)
    
    return [
        NotificationResponse(
            id=str(notification["_id"]),
            user_id=notification["user_id"],
            type=notification["type"],
            title=notification["title"],
            message=notification["message"],
            topic_id=notification.get("topic_id"),
            project_id=notification.get("project_id"),
            is_read=notification["is_read"],
            created_at=notification["created_at"]
        )
        for notification in notifications
    ]


@router.get("/unread/count")
async def get_unread_count(current_user: UserResponse = Depends(get_current_active_user)):
    """获取未读通知数量"""
    db = get_database()
    
    count = await db.notifications.count_documents({
        "user_id": current_user.id,
        "is_read": False
    })
    
    return {"count": count}


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """标记通知为已读"""
    db = get_database()
    
    try:
        notification = await db.notifications.find_one({"_id": ObjectId(notification_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的通知ID")
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 检查权限
    if notification["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="没有权限")
    
    await db.notifications.update_one(
        {"_id": ObjectId(notification_id)},
        {"$set": {"is_read": True}}
    )
    
    updated_notification = await db.notifications.find_one({"_id": ObjectId(notification_id)})
    
    return NotificationResponse(
        id=str(updated_notification["_id"]),
        user_id=updated_notification["user_id"],
        type=updated_notification["type"],
        title=updated_notification["title"],
        message=updated_notification["message"],
        topic_id=updated_notification.get("topic_id"),
        project_id=updated_notification.get("project_id"),
        is_read=updated_notification["is_read"],
        created_at=updated_notification["created_at"]
    )


@router.put("/read-all")
async def mark_all_notifications_as_read(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """标记所有通知为已读"""
    db = get_database()
    
    result = await db.notifications.update_many(
        {"user_id": current_user.id, "is_read": False},
        {"$set": {"is_read": True}}
    )
    
    return {"updated_count": result.modified_count}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """删除通知"""
    db = get_database()
    
    try:
        notification = await db.notifications.find_one({"_id": ObjectId(notification_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的通知ID")
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 检查权限
    if notification["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="没有权限")
    
    await db.notifications.delete_one({"_id": ObjectId(notification_id)})
    
    return None

