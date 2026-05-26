# LandPPT 集成方案

## 📌 项目概述

**目标**: 将 [LandPPT](https://github.com/sligter/LandPPT) 的核心 PPT 生成能力集成到项目管理系统中，实现更专业、更强大的 AI PPT 生成功能。

**集成方式**: 模块化集成 - 提取 LandPPT 核心代码，适配到现有 MongoDB 数据库架构。

## 🎯 核心功能对比

### 当前系统 vs LandPPT

| 功能 | 当前系统 | LandPPT | 集成后 |
|------|---------|---------|--------|
| **AI 内容生成** | ✅ Gemini API | ✅ 多 AI 提供商 | ✅ 支持多 AI |
| **图片生成** | ✅ Gemini Image | ✅ DALL-E/SiliconFlow/Pollinations | ✅ 多图片源 |
| **模板系统** | ⚠️ 简单模板 | ✅ 丰富模板库 | ✅ 专业模板 |
| **文件处理** | ⚠️ 基础 | ✅ MinerU/MarkItDown | ✅ 高级解析 |
| **研究功能** | ❌ 无 | ✅ Tavily/SearXNG | ✅ 深度研究 |
| **并行生成** | ❌ 无 | ✅ 支持 | ✅ 提速 |
| **演讲稿生成** | ❌ 无 | ✅ 支持 | ✅ 完整功能 |
| **数据库** | MongoDB | SQLAlchemy | MongoDB (保持) |

## 🏗️ 架构设计

### 1. 数据库设计 (MongoDB)

```javascript
// ==================== PPT 项目集合 ====================
db.ppt_projects.insertOne({
  _id: ObjectId(),
  title: "项目进展汇报",
  project_id: "项目管理系统的项目ID",
  description: "面向投资人的项目进展汇报",
  
  // 工作流状态
  workflow_status: "outline_confirmed",  // draft, outline_confirmed, generating, completed, failed
  
  // AI 配置
  ai_config: {
    provider: "gemini",  // openai, claude, gemini, deepseek, etc.
    model: "gemini-2.0-flash-exp",
    temperature: 0.7
  },
  
  // 模板配置
  template: {
    template_id: "business_blue",
    name: "商务蓝",
    colors: {
      primary: "#1e3a8a",
      secondary: "#3b82f6",
      accent: "#f59e0b",
      background: "#ffffff",
      text: "#1f2937"
    },
    fonts: {
      title: "思源黑体 Bold",
      heading: "思源黑体 Medium",
      body: "思源黑体 Regular"
    }
  },
  
  // 大纲（AI 生成）
  outline: {
    slides: [
      {
        slide_number: 1,
        type: "cover",  // cover, content, section, ending
        title: "项目进展汇报",
        subtitle: "2026年度总结",
        layout: "full",  // full, split, triple, infographic, big_number
        content_points: [],
        speaker_notes: "欢迎各位投资人..."
      },
      {
        slide_number: 2,
        type: "content",
        title: "核心成果",
        layout: "split",
        content_points: [
          "完成核心功能开发",
          "用户增长200%",
          "营收突破500万"
        ],
        image_prompt: "professional business growth chart",
        speaker_notes: "本季度我们取得了..."
      }
    ]
  },
  
  // 生成的幻灯片（最终结果）
  generated_slides: [
    {
      slide_number: 1,
      title: "项目进展汇报",
      content_html: "<div>...</div>",  // HTML 格式的幻灯片内容
      image_url: "http://localhost:8000/uploads/ppt/images/slide_1.png",
      speaker_notes: "欢迎各位投资人...",
      generated_at: ISODate("2026-02-04T05:15:00Z")
    }
  ],
  
  // 文件信息
  files: {
    pptx_path: "/uploads/ppt/项目进展汇报_1770178237.pptx",
    pdf_path: "/uploads/ppt/项目进展汇报_1770178237.pdf",
    speaker_notes_docx: "/uploads/ppt/项目进展汇报_演讲稿.docx"
  },
  
  // 研究数据（可选）
  research_data: {
    enabled: true,
    queries: ["AI PPT trends 2026", "项目管理最佳实践"],
    results: [
      {
        query: "AI PPT trends 2026",
        source: "tavily",
        content: "...",
        url: "https://..."
      }
    ]
  },
  
  // 生成进度
  progress: {
    current_step: "generating_images",
    total_steps: 5,
    completed_steps: 3,
    percentage: 60,
    logs: [
      { timestamp: ISODate(), message: "开始生成大纲..." },
      { timestamp: ISODate(), message: "大纲生成完成" },
      { timestamp: ISODate(), message: "开始生成图片 (1/10)..." }
    ]
  },
  
  created_by: "user_id",
  created_at: ISODate(),
  updated_at: ISODate()
})

// ==================== PPT 模板集合 ====================
db.ppt_templates.insertOne({
  _id: ObjectId(),
  template_id: "business_blue",
  name: "商务蓝",
  category: "工作汇报",
  thumbnail: "/templates/thumbnails/business_blue.png",
  
  // 设计规范
  design: {
    colors: {
      primary: "#1e3a8a",
      secondary: "#3b82f6",
      accent: "#f59e0b",
      background: "#ffffff",
      text: "#1f2937"
    },
    fonts: {
      title: { name: "思源黑体", weight: "Bold", size: 44 },
      heading: { name: "思源黑体", weight: "Medium", size: 32 },
      body: { name: "思源黑体", weight: "Regular", size: 18 }
    },
    spacing: {
      slide_padding: 60,
      content_gap: 20
    }
  },
  
  // 布局定义
  layouts: {
    cover: {
      background_style: "gradient",
      title_position: "center",
      subtitle_position: "center_bottom"
    },
    split: {
      content_width: "50%",
      image_width: "50%",
      gap: 40
    },
    triple: {
      columns: 3,
      card_style: "glassmorphism"
    }
  },
  
  // 装饰元素
  decorations: {
    shapes: [
      { type: "circle", color: "#3b82f6", opacity: 0.1, position: "top_right" }
    ],
    lines: [
      { type: "horizontal", color: "#f59e0b", width: 4, position: "title_bottom" }
    ]
  },
  
  is_builtin: true,
  is_active: true,
  created_at: ISODate(),
  updated_at: ISODate()
})

// ==================== AI 提供商配置集合（扩展现有）====================
db.ai_configs.insertOne({
  _id: ObjectId(),
  provider: "gemini",
  api_key: "your_api_key",
  model: "gemini-2.0-flash-exp",
  base_url: "https://api.vectorengine.ai/v1",
  
  // 功能角色配置
  capabilities: {
    text_generation: true,
    image_generation: true,
    vision: true
  },
  
  // 按功能分配模型
  role_models: {
    outline_generation: "gemini-2.0-flash-exp",
    content_generation: "gemini-2.0-flash-exp",
    image_generation: "gemini-2.5-flash-image-preview",
    research: "gemini-2.0-flash-exp"
  },
  
  is_enabled: true,
  created_at: ISODate(),
  updated_at: ISODate()
})
```

### 2. 后端架构

```
backend/
├── routers/
│   ├── ppt_service.py          # PPT 服务路由（现有，需扩展）
│   ├── ppt_templates.py        # 模板管理路由（现有，需扩展）
│   └── ppt_landppt.py          # LandPPT 集成路由（新增）
│
├── services/
│   └── landppt/                # LandPPT 核心服务（新增）
│       ├── __init__.py
│       ├── project_manager.py  # PPT 项目管理
│       ├── outline_generator.py # 大纲生成
│       ├── content_generator.py # 内容生成
│       ├── image_generator.py   # 图片生成（多源）
│       ├── template_engine.py   # 模板引擎
│       ├── research_engine.py   # 研究引擎
│       ├── pptx_exporter.py     # PPTX 导出
│       └── speaker_notes.py     # 演讲稿生成
│
├── utils/
│   ├── ppt_template_parser.py  # 现有
│   ├── ppt_content_filler.py   # 现有
│   ├── gemini_image.py         # 现有
│   └── file_processors/        # 文件处理器（新增）
│       ├── mineru_parser.py    # PDF 解析
│       └── markitdown_parser.py # 多格式文档解析
│
└── models.py                   # 扩展 PPT 相关模型
```

## 🔧 实现步骤

### Phase 1: 基础设施搭建（1-2天）

#### 1.1 安装依赖
```bash
# LandPPT 核心依赖
pip install python-pptx pillow
pip install langchain langchain-openai langchain-anthropic langchain-google-genai
pip install playwright  # HTML 转 PDF
pip install tavily-python  # 研究功能
pip install magic-pdf  # MinerU PDF 解析
pip install markitdown  # 多格式文档转换
```

#### 1.2 创建数据库集合
```python
# backend/database.py - 添加新集合
async def init_ppt_collections():
    db = get_database()
    
    # PPT 项目集合
    await db.create_collection("ppt_projects")
    await db.ppt_projects.create_index([("project_id", 1)])
    await db.ppt_projects.create_index([("created_by", 1)])
    
    # PPT 模板集合
    await db.create_collection("ppt_templates")
    await db.ppt_templates.create_index([("template_id", 1)], unique=True)
    await db.ppt_templates.create_index([("category", 1)])
```

#### 1.3 扩展数据模型
```python
# backend/models.py - 添加 LandPPT 模型

class PPTSlideType(str, Enum):
    COVER = "cover"
    CONTENT = "content"
    SECTION = "section"
    ENDING = "ending"

class PPTLayoutType(str, Enum):
    FULL = "full"
    SPLIT = "split"
    TRIPLE = "triple"
    INFOGRAPHIC = "infographic"
    BIG_NUMBER = "big_number"

class PPTWorkflowStatus(str, Enum):
    DRAFT = "draft"
    OUTLINE_CONFIRMED = "outline_confirmed"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

class PPTOutlineSlide(BaseModel):
    slide_number: int
    type: PPTSlideType
    title: str
    subtitle: Optional[str] = None
    layout: PPTLayoutType
    content_points: List[str] = []
    image_prompt: Optional[str] = None
    speaker_notes: Optional[str] = None

class PPTProjectCreate(BaseModel):
    title: str
    project_id: str
    description: Optional[str] = None
    template_id: str = "business_blue"
    enable_research: bool = False
    research_queries: List[str] = []

class PPTProjectResponse(BaseModel):
    id: str
    title: str
    project_id: str
    workflow_status: PPTWorkflowStatus
    template: dict
    outline: Optional[dict] = None
    files: Optional[dict] = None
    progress: dict
    created_by: str
    created_at: datetime
    updated_at: datetime
```

### Phase 2: 核心服务实现（3-4天）

#### 2.1 项目管理服务
```python
# backend/services/landppt/project_manager.py

class PPTProjectManager:
    """PPT 项目管理器"""
    
    def __init__(self, db):
        self.db = db
    
    async def create_project(self, data: PPTProjectCreate, user_id: str):
        """创建 PPT 项目"""
        # 加载模板
        template = await self.db.ppt_templates.find_one(
            {"template_id": data.template_id}
        )
        
        project_doc = {
            "title": data.title,
            "project_id": data.project_id,
            "description": data.description,
            "workflow_status": "draft",
            "template": template["design"],
            "ai_config": await self._get_ai_config(),
            "research_data": {
                "enabled": data.enable_research,
                "queries": data.research_queries,
                "results": []
            },
            "progress": {
                "current_step": "initializing",
                "total_steps": 5,
                "completed_steps": 0,
                "percentage": 0,
                "logs": []
            },
            "created_by": user_id,
            "created_at": get_beijing_time(),
            "updated_at": get_beijing_time()
        }
        
        result = await self.db.ppt_projects.insert_one(project_doc)
        return str(result.inserted_id)
    
    async def update_progress(self, project_id: str, step: str, percentage: int, message: str):
        """更新生成进度"""
        await self.db.ppt_projects.update_one(
            {"_id": ObjectId(project_id)},
            {
                "$set": {
                    "progress.current_step": step,
                    "progress.percentage": percentage,
                    "updated_at": get_beijing_time()
                },
                "$push": {
                    "progress.logs": {
                        "timestamp": get_beijing_time(),
                        "message": message
                    }
                }
            }
        )
```

#### 2.2 大纲生成服务
```python
# backend/services/landppt/outline_generator.py

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

class OutlineGenerator:
    """PPT 大纲生成器"""
    
    def __init__(self, ai_config: dict):
        self.ai_config = ai_config
        self.llm = self._init_llm()
    
    def _init_llm(self):
        """初始化 LLM"""
        provider = self.ai_config["provider"]
        
        if provider == "gemini":
            return ChatGoogleGenerativeAI(
                model=self.ai_config["model"],
                api_key=self.ai_config["api_key"],
                base_url=self.ai_config.get("base_url")
            )
        elif provider == "openai":
            return ChatOpenAI(
                model=self.ai_config["model"],
                api_key=self.ai_config["api_key"],
                base_url=self.ai_config.get("base_url")
            )
        # ... 其他提供商
    
    async def generate_outline(self, topic: str, slide_count: int = 10, research_data: str = None):
        """生成 PPT 大纲"""
        
        prompt = f"""你是一个专业的 PPT 设计师。请为以下主题生成一个 {slide_count} 页的 PPT 大纲。

主题: {topic}

{f"参考资料:\\n{research_data}" if research_data else ""}

要求:
1. 第一页必须是封面（cover），包含主标题和副标题
2. 最后一页是结束页（ending），通常是"谢谢"或总结
3. 中间页面根据内容选择合适的布局：
   - split: 左侧文字 + 右侧图片（适合介绍、说明）
   - triple: 三列卡片布局（适合并列内容）
   - infographic: 信息图表（适合数据展示）
   - big_number: 大数字展示（适合关键指标）
4. 每页包含 3-5 个要点
5. 为需要图片的页面生成英文图片提示词

请以 JSON 格式返回，格式如下:
{{
  "slides": [
    {{
      "slide_number": 1,
      "type": "cover",
      "title": "主标题",
      "subtitle": "副标题",
      "layout": "full",
      "content_points": [],
      "image_prompt": null,
      "speaker_notes": "开场白..."
    }},
    ...
  ]
}}
"""
        
        response = await self.llm.ainvoke(prompt)
        outline = json.loads(response.content)
        return outline
```

#### 2.3 图片生成服务（多源支持）
```python
# backend/services/landppt/image_generator.py

class ImageGenerator:
    """多源图片生成器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.sources = ["gemini", "dalle", "unsplash", "pollinations"]
    
    async def generate_image(self, prompt: str, layout: str) -> str:
        """生成图片（支持降级）"""
        
        for source in self.sources:
            try:
                if source == "gemini":
                    return await self._generate_gemini(prompt, layout)
                elif source == "dalle":
                    return await self._generate_dalle(prompt, layout)
                elif source == "unsplash":
                    return await self._fetch_unsplash(prompt)
                elif source == "pollinations":
                    return await self._generate_pollinations(prompt)
            except Exception as e:
                print(f"[{source}] 生成失败: {e}, 尝试下一个源...")
                continue
        
        raise Exception("所有图片源都失败了")
    
    async def _generate_gemini(self, prompt: str, layout: str):
        """使用 Gemini Image API 生成"""
        # 复用现有的 gemini_image.py
        from utils.gemini_image import generate_slide_image
        return await generate_slide_image(prompt, layout, self.config)
    
    async def _generate_pollinations(self, prompt: str):
        """使用 Pollinations API"""
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}"
        # 下载并保存
        ...
```

#### 2.4 模板引擎
```python
# backend/services/landppt/template_engine.py

class TemplateEngine:
    """PPT 模板引擎"""
    
    def __init__(self, template_config: dict):
        self.template = template_config
    
    def apply_template_to_slide(self, slide, slide_data: dict):
        """应用模板样式到幻灯片"""
        
        # 应用颜色
        colors = self.template["colors"]
        
        # 应用字体
        fonts = self.template["fonts"]
        
        # 应用布局
        layout = slide_data["layout"]
        
        if layout == "split":
            return self._create_split_layout(slide, slide_data)
        elif layout == "triple":
            return self._create_triple_layout(slide, slide_data)
        # ... 其他布局
    
    def _create_split_layout(self, slide, data):
        """创建左右分栏布局"""
        # 左侧：标题 + 要点
        # 右侧：图片
        ...
```

### Phase 3: API 接口开发（2天）

```python
# backend/routers/ppt_landppt.py

from fastapi import APIRouter, Depends, BackgroundTasks
from services.landppt.project_manager import PPTProjectManager
from services.landppt.outline_generator import OutlineGenerator
from services.landppt.content_generator import ContentGenerator

router = APIRouter(prefix="/api/ppt/landppt", tags=["LandPPT"])

@router.post("/projects")
async def create_ppt_project(
    data: PPTProjectCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """创建 PPT 项目"""
    db = get_database()
    manager = PPTProjectManager(db)
    
    project_id = await manager.create_project(data, current_user.id)
    
    return {"project_id": project_id, "message": "项目创建成功"}

@router.post("/projects/{project_id}/generate-outline")
async def generate_outline(
    project_id: str,
    slide_count: int = 10,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """生成 PPT 大纲"""
    db = get_database()
    project = await db.ppt_projects.find_one({"_id": ObjectId(project_id)})
    
    # 后台任务：研究 + 生成大纲
    background_tasks.add_task(
        _generate_outline_task,
        project_id,
        project["title"],
        slide_count,
        project["research_data"]
    )
    
    return {"message": "大纲生成中..."}

async def _generate_outline_task(project_id, topic, slide_count, research_config):
    """后台任务：生成大纲"""
    db = get_database()
    manager = PPTProjectManager(db)
    
    # 1. 研究（如果启用）
    research_data = None
    if research_config["enabled"]:
        await manager.update_progress(project_id, "researching", 10, "正在进行深度研究...")
        # 调用 Tavily API
        research_data = await conduct_research(research_config["queries"])
    
    # 2. 生成大纲
    await manager.update_progress(project_id, "generating_outline", 30, "正在生成大纲...")
    
    project = await db.ppt_projects.find_one({"_id": ObjectId(project_id)})
    generator = OutlineGenerator(project["ai_config"])
    outline = await generator.generate_outline(topic, slide_count, research_data)
    
    # 3. 保存大纲
    await db.ppt_projects.update_one(
        {"_id": ObjectId(project_id)},
        {
            "$set": {
                "outline": outline,
                "workflow_status": "outline_confirmed",
                "updated_at": get_beijing_time()
            }
        }
    )
    
    await manager.update_progress(project_id, "outline_ready", 50, "大纲生成完成！")

@router.post("/projects/{project_id}/generate-ppt")
async def generate_final_ppt(
    project_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """生成最终 PPT"""
    background_tasks.add_task(_generate_ppt_task, project_id)
    return {"message": "PPT 生成中..."}

async def _generate_ppt_task(project_id):
    """后台任务：生成 PPT"""
    db = get_database()
    manager = PPTProjectManager(db)
    project = await db.ppt_projects.find_one({"_id": ObjectId(project_id)})
    
    # 1. 生成图片
    await manager.update_progress(project_id, "generating_images", 60, "正在生成图片...")
    image_gen = ImageGenerator(project["ai_config"])
    
    for slide in project["outline"]["slides"]:
        if slide.get("image_prompt"):
            image_url = await image_gen.generate_image(
                slide["image_prompt"],
                slide["layout"]
            )
            slide["image_url"] = image_url
    
    # 2. 应用模板生成 PPTX
    await manager.update_progress(project_id, "generating_pptx", 80, "正在生成 PPTX...")
    
    from services.landppt.pptx_exporter import PPTXExporter
    exporter = PPTXExporter(project["template"])
    pptx_path = await exporter.export(project["outline"])
    
    # 3. 生成演讲稿
    await manager.update_progress(project_id, "generating_notes", 90, "正在生成演讲稿...")
    
    from services.landppt.speaker_notes import SpeakerNotesGenerator
    notes_gen = SpeakerNotesGenerator(project["ai_config"])
    notes_path = await notes_gen.generate(project["outline"])
    
    # 4. 完成
    await db.ppt_projects.update_one(
        {"_id": ObjectId(project_id)},
        {
            "$set": {
                "files": {
                    "pptx_path": pptx_path,
                    "speaker_notes_docx": notes_path
                },
                "workflow_status": "completed",
                "updated_at": get_beijing_time()
            }
        }
    )
    
    await manager.update_progress(project_id, "completed", 100, "PPT 生成完成！")
```

### Phase 4: 前端集成（2-3天）

```vue
<!-- frontend/src/views/PPTLandPPT.vue -->
<template>
  <div class="landppt-container">
    <!-- 步骤指示器 -->
    <el-steps :active="currentStep" align-center>
      <el-step title="创建项目" />
      <el-step title="生成大纲" />
      <el-step title="确认大纲" />
      <el-step title="生成 PPT" />
      <el-step title="完成" />
    </el-steps>
    
    <!-- Step 1: 创建项目 -->
    <div v-if="currentStep === 0" class="step-content">
      <el-form :model="projectForm" label-width="120px">
        <el-form-item label="PPT 主题">
          <el-input v-model="projectForm.title" placeholder="如：项目进展汇报" />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input type="textarea" v-model="projectForm.description" />
        </el-form-item>
        
        <el-form-item label="选择模板">
          <TemplateSelector v-model="projectForm.template_id" />
        </el-form-item>
        
        <el-form-item label="启用研究">
          <el-switch v-model="projectForm.enable_research" />
        </el-form-item>
        
        <el-form-item v-if="projectForm.enable_research" label="研究关键词">
          <el-tag
            v-for="query in projectForm.research_queries"
            :key="query"
            closable
            @close="removeQuery(query)"
          >
            {{ query }}
          </el-tag>
          <el-input
            v-model="newQuery"
            size="small"
            @keyup.enter="addQuery"
            placeholder="输入关键词后按回车"
          />
        </el-form-item>
        
        <el-button type="primary" @click="createProject">创建项目</el-button>
      </el-form>
    </div>
    
    <!-- Step 2: 生成大纲 -->
    <div v-if="currentStep === 1" class="step-content">
      <el-progress :percentage="progress.percentage" :status="progressStatus" />
      <div class="progress-logs">
        <div v-for="log in progress.logs" :key="log.timestamp">
          {{ formatTime(log.timestamp) }}: {{ log.message }}
        </div>
      </div>
    </div>
    
    <!-- Step 3: 确认大纲 -->
    <div v-if="currentStep === 2" class="step-content">
      <OutlineEditor v-model="outline" @confirm="confirmOutline" />
    </div>
    
    <!-- Step 4: 生成 PPT -->
    <div v-if="currentStep === 3" class="step-content">
      <el-progress :percentage="progress.percentage" />
      <div class="slide-preview">
        <div v-for="slide in generatedSlides" :key="slide.slide_number">
          <img :src="slide.image_url" />
        </div>
      </div>
    </div>
    
    <!-- Step 5: 完成 -->
    <div v-if="currentStep === 4" class="step-content">
      <el-result icon="success" title="PPT 生成成功！">
        <template #extra>
          <el-button type="primary" @click="downloadPPTX">下载 PPTX</el-button>
          <el-button @click="downloadNotes">下载演讲稿</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const currentStep = ref(0)
const projectId = ref(null)
const progress = ref({ percentage: 0, logs: [] })

const projectForm = ref({
  title: '',
  description: '',
  template_id: 'business_blue',
  enable_research: false,
  research_queries: []
})

async function createProject() {
  const res = await axios.post('/api/ppt/landppt/projects', {
    ...projectForm.value,
    project_id: route.params.projectId
  })
  
  projectId.value = res.data.project_id
  currentStep.value = 1
  
  // 生成大纲
  await generateOutline()
}

async function generateOutline() {
  await axios.post(`/api/ppt/landppt/projects/${projectId.value}/generate-outline`)
  
  // 轮询进度
  pollProgress()
}

function pollProgress() {
  const interval = setInterval(async () => {
    const res = await axios.get(`/api/ppt/landppt/projects/${projectId.value}`)
    progress.value = res.data.progress
    
    if (res.data.workflow_status === 'outline_confirmed') {
      clearInterval(interval)
      outline.value = res.data.outline
      currentStep.value = 2
    }
  }, 2000)
}
</script>
```

## 📦 部署清单

### 1. 环境变量配置
```bash
# backend/.env

# LandPPT 配置
LANDPPT_ENABLED=true

# 研究功能
TAVILY_API_KEY=your_tavily_key
SEARXNG_URL=http://localhost:8080  # 可选

# 图片生成（多源）
GEMINI_IMAGE_API_KEY=your_key
OPENAI_API_KEY=your_key  # DALL-E
SILICONFLOW_API_KEY=your_key

# 文件处理
MINERU_ENABLED=true
```

### 2. 数据库迁移
```python
# backend/migrations/add_landppt_collections.py

async def migrate():
    db = get_database()
    
    # 创建集合
    await db.create_collection("ppt_projects")
    await db.create_collection("ppt_templates")
    
    # 创建索引
    await db.ppt_projects.create_index([("project_id", 1)])
    await db.ppt_templates.create_index([("template_id", 1)], unique=True)
    
    # 导入内置模板
    from config.builtin_templates import BUILTIN_TEMPLATES
    for template_id, template_data in BUILTIN_TEMPLATES.items():
        await db.ppt_templates.insert_one({
            "template_id": template_id,
            **template_data,
            "is_builtin": True,
            "created_at": get_beijing_time()
        })
```

## 🎯 优势总结

### 相比直接使用 LandPPT
1. ✅ **无缝集成** - 与现有项目管理系统完美融合
2. ✅ **MongoDB 原生** - 无需 SQLAlchemy，保持技术栈一致
3. ✅ **权限控制** - 复用现有用户和项目权限体系
4. ✅ **知识库联动** - 生成的 PPT 自动保存到知识库
5. ✅ **任务关联** - PPT 可以关联到具体任务和项目

### 相比当前系统
1. ✅ **专业模板** - 丰富的模板库
2. ✅ **多 AI 支持** - 不局限于 Gemini
3. ✅ **深度研究** - Tavily 搜索引擎集成
4. ✅ **并行生成** - 大幅提速
5. ✅ **演讲稿生成** - 完整的演示解决方案

## 📅 开发时间表

| 阶段 | 任务 | 时间 |
|------|------|------|
| Phase 1 | 基础设施搭建 | 1-2天 |
| Phase 2 | 核心服务实现 | 3-4天 |
| Phase 3 | API 接口开发 | 2天 |
| Phase 4 | 前端集成 | 2-3天 |
| **总计** | | **8-11天** |

## 🚀 下一步行动

1. **确认方案** - 确认集成方案是否符合需求
2. **环境准备** - 安装依赖，配置 API Key
3. **开始开发** - 按 Phase 顺序实施
4. **测试验证** - 每个 Phase 完成后测试
5. **上线部署** - 全部完成后部署到生产环境

---

**准备好开始了吗？我可以立即开始实现！** 🎨
