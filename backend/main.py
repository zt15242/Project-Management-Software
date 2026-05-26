import sys
import asyncio

# Windows Playwright 兼容性修复
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import traceback

from database import connect_to_mongo, close_mongo_connection
from routers import auth, users, projects, tasks, topics, statistics, notifications, bi, deployments, ai_config, environments, health, knowledge, meetings, daily_reports, background_tasks, config, ppt_service, ppt_templates, ppt_template_upload, landppt_chat, email_config
from config import settings
from services.environment_refresh_service import get_refresh_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    await connect_to_mongo()
    
    # 创建上传目录
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # 启动环境刷新定时任务
    refresh_service = get_refresh_service()
    refresh_service.start()
    print("[启动] 环境自动刷新服务已启动")
    
    yield
    
    # 关闭时
    refresh_service.stop()
    await close_mongo_connection()


app = FastAPI(
    title="项目管理系统",
    description="一个功能完善的项目管理系统API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# 注册路由
app.include_router(health.router, prefix="/api", tags=["健康检查"])
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(topics.router)
app.include_router(statistics.router)
app.include_router(notifications.router)
app.include_router(bi.router)
app.include_router(deployments.router)
app.include_router(ai_config.router)
app.include_router(environments.router)
app.include_router(knowledge.router)
app.include_router(meetings.router)
app.include_router(daily_reports.router)
app.include_router(background_tasks.router)
app.include_router(config.router)
app.include_router(email_config.router)

app.include_router(ppt_service.router)
app.include_router(ppt_templates.router)  # PPT 模板管理
app.include_router(ppt_template_upload.router)  # PPT 模板上传
app.include_router(landppt_chat.router)  # LandPPT AI 助手


@app.get("/")
async def root():
    return {
        "message": "项目管理系统API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = {
        "error": str(exc),
        "type": type(exc).__name__,
        "traceback": traceback.format_exc()
    }
    print(f"\n❌ 全局异常捕获:")
    print(f"路径: {request.method} {request.url}")
    print(f"错误: {error_detail}")
    print(f"详细堆栈:\n{traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )

