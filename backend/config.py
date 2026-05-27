from pydantic_settings import BaseSettings
from typing import Optional, List


# 导出MongoDB配置，供独立任务使用
MONGODB_URL: str = "mongodb://localhost:27017"
DATABASE_NAME: str = "project_management"


class Settings(BaseSettings):
    # MongoDB配置
    MONGODB_URL: str = MONGODB_URL
    DATABASE_NAME: str = DATABASE_NAME
    
    # JWT配置
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时
    
    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    BASE_URL: str = "http://localhost:8000"  # 服务器公网地址,用于生成临时公开URL
    FRONTEND_URL: str = "http://localhost:3000"  # 前端地址,用于生成邮件链接
    PROJECT_ROOT: str = "/workspace"  # Git 项目根目录（Docker 中通过只读卷挂载）
    SYSTEM_REPO_URL: str = "https://github.com/zt15242/Project-Management-Software.git"
    SYSTEM_REPO_BRANCH: str = "main"
    SYSTEM_UPDATE_COMMAND: Optional[str] = None  # 可选：服务器侧自动更新命令
    APP_VERSION_FILE: str = "/app/VERSION"
    
    # BI数据源配置 - 配置系统支持的数据源类型
    # 只有在此列表中的数据源类型才会在前端显示
    # 可以通过环境变量 ENABLED_DATASOURCES 来覆盖，例如: ENABLED_DATASOURCES=mysql,mongodb
    ENABLED_DATASOURCES: List[str] = ["mongodb"]  # 默认只启用MongoDB
    
    # 阿里云通义千问语音识别配置
    DASHSCOPE_API_KEY: Optional[str] = None  # 阿里云DashScope API Key
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/api/v1"  # 北京地域
    DASHSCOPE_ASR_MODEL: str = "qwen3-asr-flash-filetrans"  # 长音频异步转写模型
    
    # OSS对象存储配置
    OSS_PROVIDER: Optional[str] = None  # OSS提供商: aliyun, tencent, 或 None(使用本地)
    OSS_ACCESS_KEY_ID: Optional[str] = None  # OSS Access Key ID
    OSS_ACCESS_KEY_SECRET: Optional[str] = None  # OSS Access Key Secret
    OSS_BUCKET_NAME: Optional[str] = None  # OSS Bucket名称
    OSS_REGION: Optional[str] = None  # OSS区域
    OSS_ENDPOINT: Optional[str] = None  # OSS自定义域名(可选)
    
    # Gemini Image API 配置 (用于生成高质量PPT图片)
    GEMINI_IMAGE_API_KEY: Optional[str] = None  # Gemini API Key
    GEMINI_IMAGE_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"  # Gemini API Base URL
    GEMINI_IMAGE_MODEL: str = "imagen-3.0-generate-001"  # Imagen 3 模型
    
    class Config:
        env_file = ".env"


settings = Settings()

