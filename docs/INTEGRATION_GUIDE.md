# 🔧 集成 LandPPT 模板选择器到项目详情页

## 📍 当前状态

**已完成**:
- ✅ 后端 API 已就绪
- ✅ 模板选择器组件已创建
- ✅ 模板上传组件已创建

**待完成**:
- ❌ 将模板选择器集成到 ProjectDetail.vue
- ❌ 传递 template_id 参数到生成 API

---

## 🔨 需要修改的文件

**文件**: `frontend/src/views/ProjectDetail.vue`

---

## 📝 修改步骤

### 步骤 1: 导入组件

在文件顶部的 `import` 区域添加：

```javascript
// 在其他 import 之后添加
import EnhancedTemplateSelector from '@/components/EnhancedTemplateSelector.vue'
```

**位置**: 约在第 20-50 行附近

---

### 步骤 2: 添加响应式变量

在 `<script setup>` 中添加模板相关的变量：

```javascript
// 在 pptTheme 等变量附近添加
const selectedTemplateId = ref('商务')  // 默认模板
const selectedTemplate = ref(null)
```

**位置**: 约在第 2700-2750 行附近（PPT 相关变量区域）

---

### 步骤 3: 替换步骤 2 的内容

**找到**: 第 1896-1935 行的步骤 2 内容

**替换为**:

```vue
<!-- 步骤 2：选择模板 -->
<div v-if="pptCurrentStep === 2" class="step-content template-selector-wrapper">
  <EnhancedTemplateSelector
    v-model="selectedTemplateId"
    @select="onTemplateSelect"
  />
</div>
```

---

### 步骤 4: 添加模板选择回调

在 `<script setup>` 中添加：

```javascript
// 在 generatePPTFinal 函数之前添加
const onTemplateSelect = (template) => {
  selectedTemplate.value = template
  console.log('选中模板:', template.template_name)
}
```

**位置**: 约在第 4350 行附近

---

### 步骤 5: 修改生成函数

**找到**: `generatePPTFinal` 函数（第 4360 行）

**修改**: 在调用生成 API 时添加 `template_id` 参数

**原代码** (第 4396-4407 行):
```javascript
const resFinal = await axios.post(
  `/api/ppt/drafts/${resDraft.data.id}/generate`,
  {},
  {
    headers: { Authorization: `Bearer ${token}` },
    params: {
      save_to_knowledge: pptSavingToKB.value,
      theme: pptTheme.value,  // 旧的参数
    },
  }
);
```

**修改为**:
```javascript
const resFinal = await axios.post(
  `/api/ppt/drafts/${resDraft.data.id}/generate`,
  {},
  {
    headers: { Authorization: `Bearer ${token}` },
    params: {
      save_to_knowledge: pptSavingToKB.value,
      template_id: selectedTemplateId.value,  // 新增：使用选中的模板
    },
  }
);
```

---

### 步骤 6: 添加样式（可选）

在 `<style scoped>` 中添加：

```css
/* 模板选择器包装 */
.template-selector-wrapper {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}
```

**位置**: 在 `<style scoped>` 区域的任意位置

---

## 📋 完整的修改清单

### 1. 导入组件
```javascript
import EnhancedTemplateSelector from '@/components/EnhancedTemplateSelector.vue'
```

### 2. 添加变量
```javascript
const selectedTemplateId = ref('商务')
const selectedTemplate = ref(null)
```

### 3. 添加回调函数
```javascript
const onTemplateSelect = (template) => {
  selectedTemplate.value = template
  console.log('选中模板:', template.template_name)
}
```

### 4. 替换步骤 2 的 HTML
```vue
<div v-if="pptCurrentStep === 2" class="step-content template-selector-wrapper">
  <EnhancedTemplateSelector
    v-model="selectedTemplateId"
    @select="onTemplateSelect"
  />
</div>
```

### 5. 修改 API 调用
```javascript
params: {
  save_to_knowledge: pptSavingToKB.value,
  template_id: selectedTemplateId.value,  // 使用模板 ID
}
```

---

## 🎯 预期效果

修改完成后：

1. **步骤 1**: 用户编辑 PPT 大纲
2. **步骤 2**: 用户选择模板（显示 25+ 个模板，支持上传）
3. **步骤 3**: 系统使用选中的模板生成 PPT
4. **步骤 4**: 显示生成结果

---

## 🧪 测试方法

1. 打开项目详情页
2. 点击 AI 助手
3. 输入"帮我创建一个项目进展汇报的 PPT"
4. AI 生成大纲后，点击"编辑并生成 PPT"
5. 在步骤 2 中选择不同的模板
6. 点击"开始生成 PPT"
7. 检查生成的 PPT 是否使用了选中的模板

---

## 📊 修改前后对比

### 修改前
```
步骤 2: 风格选择
- 显示 6 个简单主题（business_blue, tech_dark 等）
- 只能选择颜色主题
- 质量一般
```

### 修改后
```
步骤 2: 模板选择
- 显示 25+ 个专业模板
- 支持上传自定义模板
- 支持 PPTX 转换
- 专业级质量
```

---

## ⚠️ 注意事项

### 1. 保留旧代码（可选）
如果想保留旧的主题选择功能，可以注释掉而不是删除：

```vue
<!-- 旧的主题选择器（已弃用）
<div v-if="pptCurrentStep === 2" class="step-content theme-selector">
  ...
</div>
-->
```

### 2. 默认模板
确保 `selectedTemplateId` 的默认值是一个存在的模板 ID：
- `'商务'` - 推荐，是默认模板
- 或者在 `onMounted` 中动态获取默认模板

### 3. 错误处理
如果模板不存在，后端会降级到原有方法，所以不会影响功能。

---

## 🎉 完成后的效果

用户将看到：

```
┌─────────────────────────────────────────────┐
│ AI PPT 创作                          [×]   │
├─────────────────────────────────────────────┤
│ ① 内容大纲 → ② 模板选择 → ③ 生成预览       │
├─────────────────────────────────────────────┤
│                                             │
│ 选择 PPT 模板    共 28 个模板   [上传模板]  │
│                                             │
│ 筛选: [商务] [科技风] [清新风] ...          │
│                                             │
│ ┌────┐ ┌────┐ ┌────┐ ┌────┐               │
│ │商务│ │科技│ │清新│ │中国│               │
│ │[默认]│ │风 │ │笔记│ │风 │               │
│ └────┘ └────┘ └────┘ └────┘               │
│                                             │
│              [上一步] [开始生成 PPT]        │
└─────────────────────────────────────────────┘
```

---

**需要我帮你直接修改代码吗？** 🚀
