# PPT 模板系统 - 实现方案

## 🎯 目标

对接类似 1PPT.com 的专业模板库，让用户可以：
1. 选择不同的 PPT 模板风格
2. AI 自动应用模板样式
3. 生成更专业、更美观的 PPT

## 📊 系统架构

### 1. 模板数据结构

```python
# backend/models/ppt_template.py
class PPTTemplate:
    id: str
    name: str  # 模板名称：如"商务蓝"、"科技黑"、"简约白"
    category: str  # 分类：工作汇报、商业计划、教育培训等
    thumbnail: str  # 缩略图 URL
    
    # 设计规范
    colors: {
        "primary": "#1e3a8a",      # 主色
        "secondary": "#3b82f6",    # 辅助色
        "accent": "#f59e0b",       # 强调色
        "background": "#ffffff",   # 背景色
        "text": "#1f2937"          # 文字色
    }
    
    # 字体配置
    fonts: {
        "title": "思源黑体 Bold",
        "heading": "思源黑体 Medium",
        "body": "思源黑体 Regular"
    }
    
    # 布局配置
    layouts: {
        "cover": {...},      # 封面布局
        "content": {...},    # 内容布局
        "section": {...},    # 章节布局
        "ending": {...}      # 结束布局
    }
    
    # 装饰元素
    decorations: {
        "shapes": [...],     # 形状装饰
        "lines": [...],      # 线条装饰
        "icons": [...]       # 图标装饰
    }
```

### 2. 模板库管理

```python
# backend/routers/ppt_templates.py
from fastapi import APIRouter, Depends
from typing import List

router = APIRouter(prefix="/api/ppt-templates", tags=["PPT模板"])

@router.get("/", response_model=List[PPTTemplate])
async def get_templates(
    category: str = None,
    style: str = None
):
    """获取模板列表"""
    # 从数据库或配置文件获取模板
    pass

@router.get("/{template_id}")
async def get_template(template_id: str):
    """获取单个模板详情"""
    pass

@router.post("/")
async def create_template(template: PPTTemplate):
    """创建新模板（管理员功能）"""
    pass
```

### 3. 内置模板配置

```python
# backend/config/ppt_templates.py
BUILTIN_TEMPLATES = {
    "business_blue": {
        "name": "商务蓝",
        "category": "工作汇报",
        "thumbnail": "/templates/business_blue.png",
        "colors": {
            "primary": "#1e3a8a",
            "secondary": "#3b82f6",
            "accent": "#f59e0b",
            "background": "#ffffff",
            "text": "#1f2937"
        },
        "fonts": {
            "title": "思源黑体 Bold",
            "heading": "思源黑体 Medium",
            "body": "思源黑体 Regular"
        }
    },
    
    "tech_dark": {
        "name": "科技黑",
        "category": "产品发布",
        "thumbnail": "/templates/tech_dark.png",
        "colors": {
            "primary": "#0f172a",
            "secondary": "#1e293b",
            "accent": "#06b6d4",
            "background": "#0f172a",
            "text": "#f1f5f9"
        }
    },
    
    "nature_green": {
        "name": "自然绿",
        "category": "环保公益",
        "thumbnail": "/templates/nature_green.png",
        "colors": {
            "primary": "#15803d",
            "secondary": "#22c55e",
            "accent": "#fbbf24",
            "background": "#f0fdf4",
            "text": "#14532d"
        }
    },
    
    "warm_red": {
        "name": "中国红",
        "category": "节日庆典",
        "thumbnail": "/templates/warm_red.png",
        "colors": {
            "primary": "#dc2626",
            "secondary": "#ef4444",
            "accent": "#fbbf24",
            "background": "#fef2f2",
            "text": "#7f1d1d"
        }
    },
    
    "elegant_purple": {
        "name": "优雅紫",
        "category": "艺术设计",
        "thumbnail": "/templates/elegant_purple.png",
        "colors": {
            "primary": "#7c3aed",
            "secondary": "#a78bfa",
            "accent": "#f472b6",
            "background": "#faf5ff",
            "text": "#581c87"
        }
    },
    
    "minimal_gray": {
        "name": "极简灰",
        "category": "极简风格",
        "thumbnail": "/templates/minimal_gray.png",
        "colors": {
            "primary": "#374151",
            "secondary": "#6b7280",
            "accent": "#3b82f6",
            "background": "#f9fafb",
            "text": "#111827"
        }
    }
}
```

## 🎨 前端模板选择器

### 1. 模板选择组件

```vue
<!-- frontend/src/components/TemplateSelector.vue -->
<template>
  <div class="template-selector">
    <div class="template-categories">
      <el-button 
        v-for="cat in categories" 
        :key="cat"
        :type="selectedCategory === cat ? 'primary' : ''"
        @click="selectedCategory = cat"
      >
        {{ cat }}
      </el-button>
    </div>
    
    <div class="template-grid">
      <div 
        v-for="template in filteredTemplates" 
        :key="template.id"
        class="template-card"
        :class="{ selected: selectedTemplate === template.id }"
        @click="selectTemplate(template)"
      >
        <img :src="template.thumbnail" :alt="template.name" />
        <div class="template-info">
          <h4>{{ template.name }}</h4>
          <p>{{ template.category }}</p>
        </div>
        <div class="color-palette">
          <span 
            v-for="color in template.colors" 
            :key="color"
            :style="{ backgroundColor: color }"
          ></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'

const templates = ref([])
const selectedCategory = ref('全部')
const selectedTemplate = ref(null)

const categories = ['全部', '工作汇报', '商业计划', '产品发布', '教育培训', '节日庆典']

const filteredTemplates = computed(() => {
  if (selectedCategory.value === '全部') return templates.value
  return templates.value.filter(t => t.category === selectedCategory.value)
})

async function loadTemplates() {
  const res = await axios.get('/api/ppt-templates')
  templates.value = res.data
}

function selectTemplate(template) {
  selectedTemplate.value = template.id
  emit('select', template)
}

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.template-card {
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;
}

.template-card:hover {
  border-color: #3b82f6;
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.template-card.selected {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.color-palette {
  display: flex;
  height: 30px;
}

.color-palette span {
  flex: 1;
}
</style>
```

### 2. 集成到 PPT 创作流程

```vue
<!-- 在 ProjectDetail.vue 的 PPT 创作对话框中 -->
<el-dialog title="AI PPT 创作" v-model="showPPTDialog">
  <el-steps :active="currentStep" align-center>
    <el-step title="输入主题" />
    <el-step title="选择模板" />
    <el-step title="生成预览" />
    <el-step title="下载使用" />
  </el-steps>
  
  <!-- Step 1: 输入主题 -->
  <div v-if="currentStep === 0">
    <el-input 
      v-model="pptTopic" 
      placeholder="请输入PPT主题，如：项目进展汇报"
    />
  </div>
  
  <!-- Step 2: 选择模板 -->
  <div v-if="currentStep === 1">
    <TemplateSelector @select="onTemplateSelect" />
  </div>
  
  <!-- Step 3: 生成中 -->
  <div v-if="currentStep === 2">
    <GeneratingProgress :progress="progress" />
  </div>
  
  <!-- Step 4: 完成 -->
  <div v-if="currentStep === 3">
    <PPTPreview :file-url="pptFileUrl" />
  </div>
</el-dialog>
```

## 🔧 后端模板应用

### 修改 PPT 生成逻辑

```python
# backend/routers/ai_assistant.py
async def create_pptx_from_draft(draft: dict, template_id: str = None) -> str:
    """
    高端 PPT 生成引擎：支持模板应用
    """
    # 加载模板
    if template_id:
        template = await get_template(template_id)
    else:
        template = BUILTIN_TEMPLATES["business_blue"]  # 默认模板
    
    prs = Presentation()
    
    # 应用模板颜色
    accent_color = RGBColor.from_string(template["colors"]["primary"])
    bg_color = RGBColor.from_string(template["colors"]["background"])
    text_color = RGBColor.from_string(template["colors"]["text"])
    
    # 应用模板字体
    title_font = template["fonts"]["title"]
    body_font = template["fonts"]["body"]
    
    # 生成幻灯片时应用模板样式
    for slide_data in draft["slides"]:
        slide = create_slide_with_template(slide_data, template)
        prs.slides.add_slide(slide)
    
    return save_pptx(prs)
```

## 📦 实现步骤

### Phase 1: 基础模板系统（1-2天）
1. ✅ 创建模板数据模型
2. ✅ 实现 6 个内置模板
3. ✅ 创建模板 API 接口
4. ✅ 前端模板选择器

### Phase 2: 模板应用（2-3天）
1. ✅ 修改 PPT 生成逻辑
2. ✅ 应用模板颜色和字体
3. ✅ 应用模板布局
4. ✅ 测试各模板效果

### Phase 3: 高级功能（可选）
1. ⏳ 支持自定义模板上传
2. ⏳ 模板市场（用户分享模板）
3. ⏳ AI 推荐最适合的模板
4. ⏳ 模板预览和编辑

## 🎯 预期效果

用户体验：
1. 进入 PPT 创作
2. 输入主题："项目进展汇报"
3. 选择模板："商务蓝" 或 "中国红"
4. AI 生成符合模板风格的 PPT
5. 下载使用

## 💡 优势

相比 1PPT.com：
- ✅ **AI 自动填充内容** - 不需要手动编辑
- ✅ **智能图片生成** - Gemini Image API
- ✅ **一键生成** - 30秒-5分钟完成
- ✅ **完全可定制** - 可以添加无限模板

---

**您觉得这个方案如何？我可以立即开始实现！** 🚀
