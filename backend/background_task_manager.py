"""
后台任务管理模块
用于创建、更新和管理后台任务记录
"""
from bson import ObjectId
from utils import get_beijing_time
from database import get_database
import logging

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """后台任务管理器"""
    
    def __init__(self, db=None):
        self.db = db if db is not None else get_database()
        self.task_id = None
    
    async def create_task(self, task_type: str, task_name: str, created_by: str, related_id: str = None):
        """
        创建后台任务记录
        
        Args:
            task_type: 任务类型 (meeting_analysis, data_export, etc.)
            task_name: 任务名称
            created_by: 创建者ID
            related_id: 关联ID（如会议ID）
        
        Returns:
            str: 任务ID
        """
        try:
            task_doc = {
                "task_type": task_type,
                "task_name": task_name,
                "status": "running",
                "created_at": get_beijing_time(),
                "started_at": get_beijing_time(),
                "created_by": created_by,
                "related_id": related_id,
                "progress": 0,
                "cpu_percent": 0.0,
                "memory_mb": 0.0
            }
            
            result = await self.db.background_tasks.insert_one(task_doc)
            self.task_id = str(result.inserted_id)
            logger.info(f"✅ 创建后台任务: {self.task_id} - {task_name}")
            return self.task_id
        except Exception as e:
            logger.error(f"创建后台任务失败: {e}")
            return None
    
    async def update_progress(self, progress: int, message: str = None):
        """
        更新任务进度
        
        Args:
            progress: 进度百分比 (0-100)
            message: 可选的进度消息
        """
        if not self.task_id:
            return
        
        try:
            import psutil
            process = psutil.Process()
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            update_data = {
                "progress": progress,
                "cpu_percent": cpu_percent,
                "memory_mb": memory_mb,
                "updated_at": get_beijing_time()
            }
            
            if message:
                update_data["current_step"] = message
            
            await self.db.background_tasks.update_one(
                {"_id": ObjectId(self.task_id)},
                {"$set": update_data}
            )
            
            logger.info(f"📊 任务进度: {self.task_id} -> {progress}% {f'({message})' if message else ''}")
        except Exception as e:
            logger.warning(f"更新任务进度失败: {e}")
    
    async def complete(self):
        """标记任务为完成"""
        if not self.task_id:
            return
        
        try:
            await self.db.background_tasks.update_one(
                {"_id": ObjectId(self.task_id)},
                {
                    "$set": {
                        "status": "completed",
                        "progress": 100,
                        "completed_at": get_beijing_time(),
                        "updated_at": get_beijing_time()
                    }
                }
            )
            logger.info(f"✅ 任务完成: {self.task_id}")
        except Exception as e:
            logger.error(f"更新任务完成状态失败: {e}")
    
    async def fail(self, error_message: str):
        """
        标记任务为失败
        
        Args:
            error_message: 错误信息
        """
        if not self.task_id:
            return
        
        try:
            await self.db.background_tasks.update_one(
                {"_id": ObjectId(self.task_id)},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": error_message,
                        "completed_at": get_beijing_time(),
                        "updated_at": get_beijing_time()
                    }
                }
            )
            logger.info(f"❌ 任务失败: {self.task_id} - {error_message}")
        except Exception as e:
            logger.error(f"更新任务失败状态出错: {e}")
    
    async def pause(self):
        """暂停任务"""
        if not self.task_id:
            return
        
        try:
            await self.db.background_tasks.update_one(
                {"_id": ObjectId(self.task_id)},
                {
                    "$set": {
                        "status": "paused",
                        "updated_at": get_beijing_time()
                    }
                }
            )
            logger.info(f"⏸️ 任务暂停: {self.task_id}")
        except Exception as e:
            logger.error(f"暂停任务失败: {e}")
    
    async def resume(self):
        """继续任务"""
        if not self.task_id:
            return
        
        try:
            await self.db.background_tasks.update_one(
                {"_id": ObjectId(self.task_id)},
                {
                    "$set": {
                        "status": "running",
                        "updated_at": get_beijing_time()
                    }
                }
            )
            logger.info(f"▶️ 任务继续: {self.task_id}")
        except Exception as e:
            logger.error(f"继续任务失败: {e}")
    
    async def check_status(self):
        """
        检查任务状态
        
        Returns:
            str: 任务状态 (running, paused, stopped, etc.)
        """
        if not self.task_id:
            return "unknown"
        
        try:
            task = await self.db.background_tasks.find_one({"_id": ObjectId(self.task_id)})
            return task["status"] if task else "unknown"
        except Exception as e:
            logger.error(f"检查任务状态失败: {e}")
            return "unknown"


# 便捷函数
async def create_meeting_task(meeting_id: str, meeting_title: str, created_by: str, db=None):
    """
    创建会议分析任务
    
    Args:
        meeting_id: 会议ID
        meeting_title: 会议标题
        created_by: 创建者ID
        db: 数据库连接（可选）
    
    Returns:
        BackgroundTaskManager: 任务管理器实例
    """
    manager = BackgroundTaskManager(db)
    await manager.create_task(
        task_type="meeting_analysis",
        task_name=f"会议分析: {meeting_title}",
        created_by=created_by,
        related_id=meeting_id
    )
    return manager
