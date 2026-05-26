"""
健康检查路由
用于 Docker 容器健康检查和服务监控
"""

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from database import get_database
import time

router = APIRouter()

# 服务启动时间
start_time = time.time()


@router.get("/health")
async def health_check(db: AsyncIOMotorClient = Depends(get_database)):
    """
    健康检查端点
    返回服务运行状态和基本信息
    """
    try:
        # 检查数据库连接
        await db.command('ping')
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # 计算运行时间
    uptime = time.time() - start_time
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "service": "project-management-backend",
        "database": db_status,
        "uptime_seconds": round(uptime, 2),
        "timestamp": time.time()
    }


@router.get("/ready")
async def readiness_check(db: AsyncIOMotorClient = Depends(get_database)):
    """
    就绪检查端点
    检查服务是否准备好接收请求
    """
    try:
        # 检查数据库连接
        await db.command('ping')
        return {
            "status": "ready",
            "message": "Service is ready to handle requests"
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "message": f"Service is not ready: {str(e)}"
        }


@router.get("/live")
async def liveness_check():
    """
    存活检查端点
    检查服务进程是否存活
    """
    return {
        "status": "alive",
        "message": "Service is alive"
    }
