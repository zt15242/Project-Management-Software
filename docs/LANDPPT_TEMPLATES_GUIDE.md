# 🎨 LandPPT 专业模板库 - 使用指南

## ✅ 已成功集成

**恭喜！** 您的系统已成功集成 LandPPT 的 25 个专业模板！

## 📚 模板列表

### 1. **商务类** (默认)
- **商务** - 现代简约的商务PPT模板，深色背景+蓝色主色调
- **简约答辩风** - 蓝白为主色调的大学答辩风格
- **素白风** - "少即是多"，极简留白设计

### 2. **中国风**
- **中国风** - 传统中国元素设计
- **中式书卷风** - 古典书卷风格
- **宣纸风** - 宣纸质感背景
- **竹简风** - 竹简颜色和纹理
- **大气红** - 中国红主题

### 3. **科技风**
- **科技风** - HUD风格边角装饰，科技感十足
- **赛博朋克风** - 霓虹光污染下的未来都市
- **终端风** - 编程终端风格
- **速度黄** - 动感速度主题

### 4. **艺术风**
- **吉卜力风** - 宫崎骏动画风格
- **星月夜风** - 梵高星月夜风格
- **莫奈风** - 印象派油画风格
- **Toy风** - 玩具风格设计
- **饺子风** - 可爱饺子主题

### 5. **清新风**
- **清新风** - 清新自然风格
- **清新笔记** - 简约清新的笔记风格
- **森林绿** - 森林绿色主题
- **星月蓝** - 星空蓝色主题
- **日落大道** - 日落色调

### 6. **现代风**
- **拟态风** - 拟态化设计风格
- **模糊玻璃** - 毛玻璃效果
- **五彩斑斓的黑** - 创意黑色主题

## 🚀 快速开始

### 1. 前端集成

在 `ProjectDetail.vue` 中使用模板选择器：

```vue
<template>
  <el-dialog title="AI PPT 创作" v-model="showPPTDialog" width="80%">
    <el-steps :active="currentStep" align-center>
      <el-step title="输入主题" />
      <el-step title="选择模板" />
      <el-step title="生成PPT" />
      <el-step title="完成" />
    </el-steps>

    <!-- Step 1: 输入主题 -->
    <div v-if="currentStep === 0">
      <el-input
        v-model="pptTopic"
        placeholder="请输入PPT主题，如：项目进展汇报"
        size="large"
      />
      <el-button type="primary" @click="nextStep">下一步</el-button>
    </div>

    <!-- Step 2: 选择模板 -->
    <div v-if="currentStep === 1">
      <LandPPTTemplateSelector
        v-model="selectedTemplateId"
        @select="onTemplateSelect"
      />
      <el-button @click="prevStep">上一步</el-button>
      <el-button type="primary" @click="generatePPT">开始生成</el-button>
    </div>

    <!-- Step 3: 生成中 -->
    <div v-if="currentStep === 2">
      <el-progress :percentage="progress" />
      <p>{{ progressMessage }}</p>
    </div>

    <!-- Step 4: 完成 -->
    <div v-if="currentStep === 3">
      <el-result icon="success" title="PPT 生成成功！">
        <template #extra>
          <el-button type="primary" @click="downloadPPT">下载 PPTX</el-button>
        </template>
      </el-result>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import LandPPTTemplateSelector from '@/components/LandPPTTemplateSelector.vue'

const currentStep = ref(0)
const pptTopic = ref('')
const selectedTemplateId = ref('')
const selectedTemplate = ref(null)

function onTemplateSelect(template) {
  selectedTemplate.value = template
  console.log('选中模板:', template.template_name)
}

function nextStep() {
  if (currentStep.value < 3) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

async function generatePPT() {
  currentStep.value = 2
  
  // 调用后端 API 生成 PPT
  const response = await axios.post('/api/ppt/generate', {
    topic: pptTopic.value,
    template_id: selectedTemplateId.value,
    project_id: projectId.value
  })
  
  // 轮询进度...
}
</script>
```

### 2. 后端 API 使用

#### 获取所有模板
```python
GET /api/ppt/templates/
```

响应：
```json
{
  "total": 25,
  "templates": [
    {
      "id": "...",
      "template_id": "商务",
      "template_name": "默认商务模板",
      "description": "现代简约的商务PPT模板...",
      "tags": ["默认", "商务", "现代", "简约", "深色"],
      "is_default": true,
      "is_active": true,
      "source": "landppt",
      "created_at": "2026-02-04T13:23:00Z"
    }
  ]
}
```

#### 获取默认模板
```python
GET /api/ppt/templates/default
```

#### 获取指定模板
```python
GET /api/ppt/templates/{template_id}
```

#### 获取模板 HTML（用于预览）
```python
GET /api/ppt/templates/{template_id}/html
```

#### 获取所有标签
```python
GET /api/ppt/templates/tags/all
```

#### 按标签筛选
```python
GET /api/ppt/templates/?tag=科技风
```

## 🎨 模板使用示例

### 在 PPT 生成中使用模板

```python
from database import get_database
from jinja2 import Template

async def generate_ppt_with_template(topic: str, template_id: str):
    db = get_database()
    
    # 1. 获取模板
    template = await db.ppt_templates.find_one({"template_id": template_id})
    if not template:
        template = await db.ppt_templates.find_one({"is_default": True})
    
    html_template = template["html_template"]
    
    # 2. 准备数据
    slide_data = {
        "page_title": "项目进展汇报",
        "main_heading": "项目进展汇报",
        "page_content": """
            <ul class="content-points">
                <li>完成核心功能开发</li>
                <li>用户增长200%</li>
                <li>营收突破500万</li>
            </ul>
        """,
        "current_page_number": 1,
        "total_page_count": 10
    }
    
    # 3. 渲染模板
    jinja_template = Template(html_template)
    rendered_html = jinja_template.render(**slide_data)
    
    # 4. 转换为 PPTX
    # 使用 playwright 将 HTML 转为图片，然后插入到 PPTX
    ...
    
    return pptx_path
```

## 📊 模板特点

### HTML 模板占位符

所有模板都支持以下 Jinja2 占位符：

- `{{ page_title }}` - 页面标题（用于 HTML title）
- `{{ main_heading }}` - 主标题
- `{{ page_content }}` - 页面内容（支持 HTML）
- `{{ current_page_number }}` - 当前页码
- `{{ total_page_count }}` - 总页数

### 内容样式类

模板提供了丰富的 CSS 类：

- `.content-points` - 要点列表
- `.highlight-box` - 高亮框
- `.stats-grid` - 统计数据网格
- `.stat-card` - 统计卡片
- `.chart-container` - 图表容器

### 示例：使用统计卡片

```html
<div class="stats-grid">
    <div class="stat-card">
        <span class="stat-number">200%</span>
        <span class="stat-label">用户增长</span>
    </div>
    <div class="stat-card">
        <span class="stat-number">500万</span>
        <span class="stat-label">营收突破</span>
    </div>
</div>
```

## 🔧 管理功能

### 重新导入模板（管理员）

如果需要重新导入或更新模板：

```bash
# 方法 1: 运行初始化脚本
cd backend
python init_landppt_templates.py

# 方法 2: 调用 API（需要管理员权限）
POST /api/ppt/templates/import-landppt?force_reimport=true
```

### 设置默认模板

```python
from database import get_database

async def set_default_template(template_id: str):
    db = get_database()
    
    # 取消所有模板的默认状态
    await db.ppt_templates.update_many(
        {},
        {"$set": {"is_default": False}}
    )
    
    # 设置新的默认模板
    await db.ppt_templates.update_one(
        {"template_id": template_id},
        {"$set": {"is_default": True}}
    )
```

## 🎯 最佳实践

### 1. 模板选择建议

- **商务汇报** → 商务、简约答辩风
- **技术分享** → 科技风、终端风
- **产品发布** → 赛博朋克风、速度黄
- **教育培训** → 清新笔记、素白风
- **艺术展示** → 莫奈风、吉卜力风
- **传统文化** → 中国风、竹简风

### 2. 内容适配

不同模板对内容长度有不同要求：

- **简约风格**（素白风、清新风）：适合少量文字，突出重点
- **丰富风格**（赛博朋克、莫奈风）：可以承载更多内容
- **商务风格**（商务、科技风）：平衡文字和视觉效果

### 3. 性能优化

- 模板 HTML 包含 CDN 资源（TailwindCSS、Chart.js、Font Awesome）
- 首次加载可能较慢，建议预加载常用模板
- 生成 PPTX 时可以缓存渲染结果

## 📝 自定义模板

如果需要创建自定义模板：

```python
from database import get_database
from utils import get_beijing_time

async def create_custom_template(template_data: dict):
    db = get_database()
    
    template_doc = {
        "template_id": "my_custom_template",
        "template_name": "我的自定义模板",
        "description": "这是我的自定义模板",
        "html_template": """<!DOCTYPE html>...""",
        "tags": ["自定义", "特殊"],
        "is_default": False,
        "is_active": True,
        "is_builtin": False,
        "source": "custom",
        "created_by": "user_id",
        "created_at": get_beijing_time(),
        "updated_at": get_beijing_time()
    }
    
    await db.ppt_templates.insert_one(template_doc)
```

## 🚀 下一步

1. ✅ **模板已导入** - 25 个专业模板可用
2. ⏭️ **集成到 PPT 生成流程** - 修改 `ai_assistant.py` 使用模板
3. ⏭️ **前端界面优化** - 在 ProjectDetail.vue 中集成模板选择器
4. ⏭️ **HTML 转 PPTX** - 实现 HTML 模板到 PPTX 的转换

---

**现在您拥有了专业级的 PPT 模板库！** 🎉

模板来源：[LandPPT](https://github.com/sligter/LandPPT)
