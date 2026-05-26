# 🎨 LandPPT 模板快速参考

## ✅ 状态：已成功集成 25 个专业模板

---

## 📚 模板分类速查

### 🏢 商务类 (3个)
- **商务** ⭐ (默认) - 深色商务风
- **简约答辩风** - 蓝白大学风
- **素白风** - 极简留白

### 🇨🇳 中国风 (5个)
- **中国风** - 传统元素
- **中式书卷风** - 古典书卷
- **宣纸风** - 宣纸质感
- **竹简风** - 竹简纹理
- **大气红** - 中国红

### 💻 科技风 (4个)
- **科技风** - HUD 风格
- **赛博朋克风** - 霓虹未来
- **终端风** - 编程终端
- **速度黄** - 动感速度

### 🎨 艺术风 (5个)
- **吉卜力风** - 宫崎骏动画
- **星月夜风** - 梵高风格
- **莫奈风** - 印象派油画
- **Toy风** - 玩具风格
- **饺子风** - 可爱主题

### 🌿 清新风 (5个)
- **清新风** - 清新自然
- **清新笔记** - 笔记风格
- **森林绿** - 森林主题
- **星月蓝** - 星空蓝色
- **日落大道** - 日落色调

### ✨ 现代风 (3个)
- **拟态风** - 拟态化设计
- **模糊玻璃** - 毛玻璃效果
- **五彩斑斓的黑** - 创意黑色

---

## 🚀 常用 API

```bash
# 获取所有模板
GET /api/ppt/templates/

# 获取默认模板
GET /api/ppt/templates/default

# 获取指定模板
GET /api/ppt/templates/{template_id}

# 获取模板 HTML
GET /api/ppt/templates/{template_id}/html

# 获取所有标签
GET /api/ppt/templates/tags/all

# 按标签筛选
GET /api/ppt/templates/?tag=科技风

# 重新导入（管理员）
POST /api/ppt/templates/import-landppt?force_reimport=true
```

---

## 💻 前端使用

```vue
<template>
  <LandPPTTemplateSelector
    v-model="selectedTemplateId"
    @select="onTemplateSelect"
  />
</template>

<script setup>
import LandPPTTemplateSelector from '@/components/LandPPTTemplateSelector.vue'

const selectedTemplateId = ref('')

function onTemplateSelect(template) {
  console.log('选中:', template.template_name)
}
</script>
```

---

## 🔧 重新导入模板

```bash
cd backend
python init_landppt_templates.py
```

---

## 📊 模板占位符

所有模板支持的 Jinja2 变量：

- `{{ page_title }}` - 页面标题
- `{{ main_heading }}` - 主标题
- `{{ page_content }}` - 内容（支持 HTML）
- `{{ current_page_number }}` - 当前页码
- `{{ total_page_count }}` - 总页数

---

## 🎯 场景推荐

| 场景 | 推荐模板 |
|------|---------|
| 商务汇报 | 商务、简约答辩风 |
| 技术分享 | 科技风、终端风 |
| 产品发布 | 赛博朋克风、速度黄 |
| 教育培训 | 清新笔记、素白风 |
| 艺术展示 | 莫奈风、吉卜力风 |
| 传统文化 | 中国风、竹简风 |

---

## 📁 关键文件

```
backend/
├── services/landppt_template_importer.py  # 导入器
├── routers/ppt_templates.py               # API
└── init_landppt_templates.py              # 初始化脚本

frontend/
└── src/components/LandPPTTemplateSelector.vue  # 选择器

docs/
├── LANDPPT_INTEGRATION_PLAN.md      # 集成方案
├── LANDPPT_TEMPLATES_GUIDE.md       # 使用指南
└── LANDPPT_INTEGRATION_SUMMARY.md   # 完成总结
```

---

## ⏭️ 下一步

1. **实现模板渲染引擎** - HTML → PPTX
2. **集成到 AI 生成流程** - 使用模板生成 PPT
3. **前端界面集成** - 在项目详情页添加模板选择

---

**🎉 25 个专业模板已就绪！**
