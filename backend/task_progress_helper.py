
async def update_task_progress(task_id: str, progress: int, db=None):
    """更新后台任务进度和资源占用"""
    if not task_id:
        return
    
    if db is None:
        db = get_database()
    
    try:
        import psutil
        process = psutil.Process()
        cpu_percent = process.cpu_percent(interval=0.1)
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        await db.background_tasks.update_one(
            {"_id": ObjectId(task_id)},
            {
                "$set": {
                    "progress": progress,
                    "cpu_percent": cpu_percent,
                    "memory_mb": memory_mb,
                    "updated_at": get_beijing_time()
                }
            }
        )
        logger.info(f"更新任务进度: {task_id} -> {progress}%")
    except Exception as e:
        logger.warning(f"更新任务进度失败: {e}")


