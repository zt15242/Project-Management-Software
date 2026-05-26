from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum
from utils import get_beijing_time


# 枚举类型
class UserRole(str, Enum):
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    DEVELOPER = "developer"
    TESTER = "tester"
    EXTERNAL_PERSONNEL = "external_personnel"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TopicStatus(str, Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    TESTING = "testing"
    CLOSED = "closed"
    REOPENED = "reopened"


class TopicSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# 用户模型
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.EXTERNAL_PERSONNEL


class UserRegisterRequest(UserCreate):
    code: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class UserStats(BaseModel):
    created_projects: int
    participated_projects: int
    assigned_tasks: int
    completed_tasks: int
    created_topics: int
    assigned_topics: int


class UserInDB(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool = True
    created_at: datetime


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


# 项目模型
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    project_manager_id: Optional[str] = None  # 项目经理
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_manager_id: Optional[str] = None  # 项目经理
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    project_manager_id: Optional[str] = None  # 项目经理
    team_members: List[str] = []
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    total: int
    items: List[ProjectResponse]


# 任务模型
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    project_id: str
    assigned_to: Optional[str] = None
    collaborators: List[str] = []  # 协助人列表
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_hours: Optional[float] = None
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    collaborators: Optional[List[str]] = None  # 协助人列表
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    due_date: Optional[datetime] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    project_id: str
    created_by: str
    assigned_to: Optional[str] = None
    collaborators: List[str] = []  # 协助人列表
    status: TaskStatus
    priority: TaskPriority
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# 课题模型
class TopicCreate(BaseModel):
    title: str
    description: str
    project_id: str
    assigned_to: Optional[str] = None
    severity: TopicSeverity = TopicSeverity.MEDIUM
    steps_to_reproduce: Optional[str] = None
    topic_images: List[str] = []  # 课题截图（base64）


class TopicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    status: Optional[TopicStatus] = None
    severity: Optional[TopicSeverity] = None
    steps_to_reproduce: Optional[str] = None
    fix_description: Optional[str] = None
    topic_images: Optional[List[str]] = None  # 课题截图（base64）
    fix_images: Optional[List[str]] = None  # 修复截图（base64）


class TopicResponse(BaseModel):
    id: str
    topic_number: str  # 课题号：DB+年月日+序列号
    title: str
    description: str
    project_id: str
    created_by: str
    assigned_to: Optional[str] = None
    status: TopicStatus
    severity: TopicSeverity
    steps_to_reproduce: Optional[str] = None
    fix_description: Optional[str] = None
    topic_images: List[str] = []  # 课题截图（base64）
    fix_images: List[str] = []  # 修复截图（base64）
    attachments: List[str] = []  # 保留旧的附件字段以兼容
    created_at: datetime
    updated_at: datetime


# 课题评论模型
class TopicCommentCreate(BaseModel):
    content: str


class TopicCommentResponse(BaseModel):
    id: str
    topic_id: str
    user_id: str
    user_name: str
    content: str
    created_at: datetime


# 认证模型
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# 统计模型
class ProjectStatistics(BaseModel):
    project_id: str
    project_name: str
    total_tasks: int
    completed_tasks: int
    task_completion_rate: float
    total_topics: int
    open_topics: int
    closed_topics: int
    topic_rate: float
    team_size: int


# BI相关枚举
class DataSourceType(str, Enum):
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    API = "api"
    CSV = "csv"


class ChartType(str, Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    TABLE = "table"
    AREA = "area"
    SCATTER = "scatter"


# BI数据源模型
class DataSourceCreate(BaseModel):
    name: str
    project_id: str
    type: DataSourceType
    config: dict  # 连接配置（主机、端口、数据库等）
    description: Optional[str] = None


class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[DataSourceType] = None
    config: Optional[dict] = None
    description: Optional[str] = None


class DataSourceResponse(BaseModel):
    id: str
    name: str
    project_id: str
    type: DataSourceType
    config: dict
    description: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime


# BI对象（表/集合）模型
class DataObjectResponse(BaseModel):
    name: str
    type: str  # table, collection, view
    fields: List[dict]  # 字段列表


# BI报表模型
class ReportCreate(BaseModel):
    name: str
    project_id: str
    datasource_id: str
    object_name: str  # 数据对象名称（表名/集合名）
    fields: List[str]  # 使用的字段列表
    chart_type: ChartType
    chart_config: dict  # 图表配置（x轴、y轴、维度、度量等）
    filter_config: Optional[dict] = None  # 过滤条件
    description: Optional[str] = None


class ReportUpdate(BaseModel):
    name: Optional[str] = None
    datasource_id: Optional[str] = None
    object_name: Optional[str] = None
    fields: Optional[List[str]] = None
    chart_type: Optional[ChartType] = None
    chart_config: Optional[dict] = None
    filter_config: Optional[dict] = None
    description: Optional[str] = None


class ReportResponse(BaseModel):
    id: str
    name: str
    project_id: str
    datasource_id: str
    object_name: str
    fields: List[str]
    chart_type: ChartType
    chart_config: dict
    filter_config: Optional[dict] = None
    description: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime


# BI仪表板模型
class DashboardCreate(BaseModel):
    name: str
    project_id: str
    report_ids: List[str] = []  # 包含的报表ID列表
    layout: dict  # 布局配置
    description: Optional[str] = None


class DashboardUpdate(BaseModel):
    name: Optional[str] = None
    report_ids: Optional[List[str]] = None
    layout: Optional[dict] = None
    description: Optional[str] = None


class DashboardResponse(BaseModel):
    id: str
    name: str
    project_id: str
    report_ids: List[str]
    layout: dict
    description: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime


# 代码发布相关枚举
class DeploymentType(str, Enum):
    LOGIC_CODE = "logic_code"  # 逻辑代码包
    PAGE_CODE = "page_code"    # 页面代码

class DeploymentStatus(str, Enum):
    PENDING = "pending"           # 待审核
    ANALYZING = "analyzing"       # AI分析中
    ANALYSIS_COMPLETED = "analysis_completed"  # 分析完成
    APPROVED = "approved"         # 审核通过
    REJECTED = "rejected"         # 审核拒绝
    DEPLOYING = "deploying"       # 部署中
    DEPLOYED = "deployed"         # 已部署
    FAILED = "failed"             # 部署失败

class RiskLevel(str, Enum):
    LOW = "low"           # 低风险
    MEDIUM = "medium"     # 中风险
    HIGH = "high"         # 高风险
    CRITICAL = "critical" # 严重风险


class AIProvider(str, Enum):
    NONE = "none"                      # 不使用AI（规则匹配）
    OPENAI = "openai"                  # OpenAI GPT
    QWEN = "qwen"                      # 阿里通义千问
    ZHIPU = "zhipu"                    # 智谱AI
    CLAUDE = "claude"                  # Anthropic Claude
    DEEPSEEK = "deepseek"              # DeepSeek
    GEMINI = "gemini"                  # Google Gemini


# AI配置模型
class AIConfigCreate(BaseModel):
    provider: AIProvider
    api_key: str
    model: Optional[str] = None        # 模型名称，如 gpt-4, qwen-max
    base_url: Optional[str] = None     # 自定义API地址
    is_enabled: bool = True
    description: Optional[str] = None

class AIConfigUpdate(BaseModel):
    provider: Optional[AIProvider] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    is_enabled: Optional[bool] = None
    description: Optional[str] = None

class AIConfigResponse(BaseModel):
    id: str
    provider: AIProvider
    api_key_masked: str                # 脱敏后的API Key
    model: Optional[str] = None
    base_url: Optional[str] = None
    is_enabled: bool
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# 代码发布模型
class CodeDeploymentCreate(BaseModel):
    """创建代码发布申请（包）"""
    title: str  # 包名称
    description: Optional[str] = None
    project_id: str
    deployment_type: DeploymentType
    environment_id: Optional[str] = None  # 关联的环境配置ID
    package_path: Optional[str] = None  # 包路径（如：other.oa.message）
    remote_package_id: Optional[str] = None  # 远程平台的包ID（自动获取）


class CodeDeploymentUpdate(BaseModel):
    """更新代码发布申请基本信息"""
    title: Optional[str] = None
    description: Optional[str] = None


class VersionUpload(BaseModel):
    """用于接收表单参数"""
    description: Optional[str] = None


class AIAnalysisResult(BaseModel):
    risk_level: RiskLevel
    code_quality_score: float  # 代码质量评分 0-100
    security_issues: List[dict] = []  # 安全问题列表
    performance_issues: List[dict] = []  # 性能问题列表
    code_smells: List[dict] = []  # 代码坏味道
    version_changes: List[dict] = []  # 版本变更详情
    file_analysis: List[dict] = []  # 文件分析结果
    suggestions: List[str] = []  # 改进建议
    analysis_time: datetime


class DeploymentReview(BaseModel):
    reviewer_id: str
    reviewer_name: str
    action: str  # approved, rejected
    comment: Optional[str] = None
    reviewed_at: datetime


class VersionInfo(BaseModel):
    """版本信息（子文档）"""
    version: int  # 版本号（自动递增：1, 2, 3...）
    description: Optional[str] = None
    status: DeploymentStatus
    file_path: Optional[str] = None  # zip文件路径
    file_size: Optional[int] = None  # 文件大小（字节）
    uploaded_by: str
    uploaded_at: datetime
    ai_analysis: Optional[AIAnalysisResult] = None
    review: Optional[DeploymentReview] = None
    deployed_at: Optional[datetime] = None
    deployment_response: Optional[dict] = None  # 远程接口返回的完整响应内容


class CodeDeploymentResponse(BaseModel):
    """代码发布申请响应（包含所有版本）"""
    id: str
    title: str  # 包名称
    description: Optional[str] = None
    project_id: str
    deployment_type: DeploymentType
    current_version: int  # 当前最新版本号
    versions: List[VersionInfo] = []  # 所有版本列表
    environment_id: Optional[str] = None  # 关联的环境配置ID
    package_path: Optional[str] = None  # 包路径
    remote_package_id: Optional[str] = None  # 远程平台的包ID
    created_by: str
    created_at: datetime
    updated_at: datetime


class VersionResponse(BaseModel):
    """单个版本响应"""
    deployment_id: str
    deployment_title: str
    version: int
    description: Optional[str] = None
    status: DeploymentStatus
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    uploaded_by: str
    uploaded_at: datetime
    ai_analysis: Optional[AIAnalysisResult] = None
    review: Optional[DeploymentReview] = None
    deployed_at: Optional[datetime] = None
    deployment_response: Optional[dict] = None  # 远程接口返回的完整响应内容


# 环境配置相关模型
class EnvironmentCreate(BaseModel):
    """创建环境配置"""
    name: str  # 环境名称，如：Sandbox Test Environment, 康乐保CRM沙盒环境
    url: str  # 登录URL
    username: str  # 登录用户名
    password: str  # 登录密码
    description: Optional[str] = None


class EnvironmentUpdate(BaseModel):
    """更新环境配置"""
    name: Optional[str] = None
    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class EnvironmentCookie(BaseModel):
    """环境Cookie信息"""
    name: str
    value: str
    domain: str
    path: str = "/"
    expires: Optional[float] = None
    httpOnly: bool = False
    secure: bool = False
    sameSite: Optional[str] = None


class EnvironmentResponse(BaseModel):
    """环境配置响应"""
    id: str
    project_id: str
    name: str
    url: str
    username: str
    password_masked: str  # 脱敏后的密码
    description: Optional[str] = None
    is_active: bool  # 是否启用
    cookies: List[EnvironmentCookie] = []  # 存储的cookies
    last_login_at: Optional[datetime] = None  # 最后登录时间
    last_login_status: Optional[str] = None  # 最后登录状态：success, failed
    created_by: str
    created_at: datetime
    updated_at: datetime


class EnvironmentLoginRequest(BaseModel):
    """环境登录请求"""
    environment_id: str
    force_refresh: bool = False  # 是否强制刷新cookie


# 知识库相关枚举
class KnowledgeFileType(str, Enum):
    """知识库文件类型"""
    MARKDOWN = "markdown"      # .md
    WORD = "word"              # .doc, .docx
    EXCEL = "excel"            # .xls, .xlsx
    PDF = "pdf"                # .pdf
    TEXT = "text"              # .txt
    IMAGE = "image"            # .png, .jpg, .jpeg, .gif
    PPT = "ppt"                # .ppt, .pptx
    OTHER = "other"            # 其他类型


class KnowledgeStatus(str, Enum):
    """知识库文档状态"""
    DRAFT = "draft"            # 草稿
    PUBLISHED = "published"    # 已发布
    ARCHIVED = "archived"      # 已归档


# 知识库模型
class KnowledgeCreate(BaseModel):
    """创建知识库文档"""
    title: str
    project_id: str
    category: Optional[str] = None  # 分类/标签
    description: Optional[str] = None
    tags: List[str] = []  # 标签列表


class KnowledgeUpdate(BaseModel):
    """更新知识库文档"""
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None  # 文本内容（仅用于markdown/text）
    tags: Optional[List[str]] = None
    status: Optional[KnowledgeStatus] = None


class KnowledgeResponse(BaseModel):
    """知识库文档响应"""
    id: str
    title: str
    project_id: str
    category: Optional[str] = None
    description: Optional[str] = None
    file_type: KnowledgeFileType
    file_name: str
    file_path: str
    file_size: int  # 字节
    content: Optional[str] = None  # 提取的文本内容
    tags: List[str] = []
    status: KnowledgeStatus
    views: int = 0  # 浏览次数
    created_by: str
    created_at: datetime
    updated_at: datetime


class KnowledgeSearchRequest(BaseModel):
    """知识库搜索请求"""
    project_id: Optional[str] = None
    keyword: Optional[str] = None  # 搜索关键词
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    file_type: Optional[KnowledgeFileType] = None
    status: Optional[KnowledgeStatus] = None


# ==================== 会议分析模块 ====================

class MeetingStatus(str, Enum):
    """会议分析状态"""
    UPLOADING = "uploading"  # 上传中
    PROCESSING = "processing"  # 处理中
    SPEAKER_IDENTIFICATION = "speaker_identification"  # 说话人识别中
    WAITING_CONFIRMATION = "waiting_confirmation"  # 等待用户确认说话人
    GENERATING_SUMMARY = "generating_summary"  # 生成摘要中
    COMPLETED = "completed"  # 完成
    FAILED = "failed"  # 失败


class SpeakerSegment(BaseModel):
    """说话人音频片段"""
    speaker_id: str  # 说话人ID（临时）
    speaker_name: Optional[str] = None  # 说话人姓名（用户确认后）
    start_time: float  # 开始时间（秒）
    end_time: float  # 结束时间（秒）
    audio_segment_path: Optional[str] = None  # 音频片段路径
    text: Optional[str] = None  # 转录文本


class MeetingCreate(BaseModel):
    """创建会议分析请求"""
    title: str
    project_id: str
    description: Optional[str] = None


class MeetingUpdate(BaseModel):
    """更新会议分析"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[MeetingStatus] = None


class SpeakerConfirmation(BaseModel):
    """说话人确认"""
    speaker_id: str
    speaker_name: str


class MeetingResponse(BaseModel):
    """会议分析响应"""
    id: str
    title: str
    project_id: str
    description: Optional[str] = None
    file_name: str
    file_path: str
    file_size: int
    file_type: str  # video/audio
    duration: Optional[float] = None  # 时长（秒）
    status: MeetingStatus
    speakers: List[SpeakerSegment] = []  # 说话人片段
    summary_content: Optional[str] = None  # 生成的摘要（Markdown）
    summary_file_path: Optional[str] = None  # 摘要文件路径
    error_message: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime


# 日报相关模型
class DailyReportType(str, Enum):
    TASK = "task"              # 任务相关
    TOPIC = "topic"            # 课题相关
    MAINTENANCE = "maintenance"  # 日常运维


class DailyReportCreate(BaseModel):
    """创建日报"""
    report_date: datetime  # 日报日期
    report_type: DailyReportType  # 日报类型
    project_id: Optional[str] = None  # 关联项目ID（类型为maintenance时必填）
    task_id: Optional[str] = None  # 关联任务ID（类型为task时必填）
    topic_id: Optional[str] = None  # 关联课题ID（类型为topic时必填）
    content: str  # 工作内容描述
    hours: float = Field(gt=0, le=24)  # 工时（小时），必须大于0且不超过24


class DailyReportUpdate(BaseModel):
    """更新日报"""
    content: Optional[str] = None
    hours: Optional[float] = Field(None, gt=0, le=24)


class DailyReportResponse(BaseModel):
    """日报响应"""
    id: str
    user_id: str
    user_name: str  # 用户姓名
    report_date: datetime
    report_type: DailyReportType
    project_id: Optional[str] = None
    project_name: Optional[str] = None  # 项目名称
    task_id: Optional[str] = None
    task_title: Optional[str] = None  # 任务标题
    topic_id: Optional[str] = None
    topic_title: Optional[str] = None  # 课题标题
    content: str
    hours: float
    created_at: datetime
    updated_at: datetime


# AI对话模型
class ChatMessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatToolCall(BaseModel):
    id: str
    type: str = "function"
    function: dict


class ChatMessage(BaseModel):
    id: Optional[str] = None
    role: ChatMessageRole
    content: Optional[str] = None
    tool_calls: Optional[List[ChatToolCall]] = None
    tool_call_id: Optional[str] = None
    created_at: datetime = Field(default_factory=get_beijing_time)


class ChatMessageUpdate(BaseModel):
    content: str


class ChatSessionCreate(BaseModel):
    title: str = "新会话"
    project_id: str


class ChatSessionUpdate(BaseModel):
    title: str


class ChatSessionResponse(BaseModel):
    id: str
    user_id: str
    project_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ChatHistoryResponse(BaseModel):
    session: ChatSessionResponse
    messages: List[ChatMessage]


# ==========================================
# PPT 创作模型
# ==========================================
class PPTSlide(BaseModel):
    title: str
    content: List[str]  # 每一行内容
    layout: str = "bullet"  # bullet, title, text, image
    notes: Optional[str] = None
    images: List[str] = [] # 图片URL列表

class PPTDraftBase(BaseModel):
    title: str
    project_id: str
    slides: List[PPTSlide]
    theme: str = "default"

class PPTDraftCreate(PPTDraftBase):
    pass

class PPTDraftUpdate(BaseModel):
    title: Optional[str] = None
    slides: Optional[List[PPTSlide]] = None
    theme: Optional[str] = None

class PPTDraftResponse(PPTDraftBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime


# ==========================================
# 邮件配置与验证模型
# ==========================================
class EmailConfigCreate(BaseModel):
    smtp_server: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    sender_email: str
    use_tls: bool = True
    is_enabled: bool = True

class EmailConfigUpdate(BaseModel):
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    sender_email: Optional[str] = None
    use_tls: Optional[bool] = None
    is_enabled: Optional[bool] = None

class EmailConfigResponse(BaseModel):
    id: str
    smtp_server: str
    smtp_port: int
    smtp_user: str
    sender_email: str
    use_tls: bool
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

class EmailVerifyRequest(BaseModel):
    email: EmailStr
    purpose: str = "register"

class EmailVerify(BaseModel):
    email: EmailStr
    code: str
    purpose: str = "register"
    created_at: datetime = Field(default_factory=get_beijing_time)
    expires_at: datetime
