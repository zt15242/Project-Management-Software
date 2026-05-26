# 📤 PPT 模板上传功能 - 使用指南

## ✅ 功能概述

现在系统支持**上传自定义 PPT 模板**！用户可以：

1. ✅ 上传 HTML 模板（推荐）
2. ✅ 上传 PPTX 文件作为模板（实验性）
3. ✅ 管理自己的模板（查看、更新、删除）
4. ✅ 使用自定义模板生成 PPT

---

## 🎨 支持的模板类型

### 1. HTML 模板（推荐）⭐

**优势**:
- 完全自定义样式
- 支持 CSS、JavaScript
- 渲染质量高
- 灵活性强

**要求**:
HTML 模板必须包含以下 Jinja2 占位符：

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ page_title }}</title>
    <style>
        /* 你的样式 */
    </style>
</head>
<body>
    <h1>{{ main_heading }}</h1>
    <div class="content">
        {{ page_content }}
    </div>
    <div class="footer">
        {{ current_page_number }} / {{ total_page_count }}
    </div>
</body>
</html>
```

**必需占位符**:
- `{{ page_title }}` - 页面标题
- `{{ main_heading }}` - 主标题
- `{{ page_content }}` - 页面内容（HTML）
- `{{ current_page_number }}` - 当前页码
- `{{ total_page_count }}` - 总页数

### 2. PPTX 文件（实验性）

**说明**:
- 上传 PPTX 文件后，系统会保存文件
- 当前使用基础 HTML 模板渲染
- 未来版本将支持 PPTX 转 HTML

---

## 📡 API 接口

### 1. 上传 HTML 模板

```http
POST /api/ppt/templates/upload-html
Content-Type: multipart/form-data
Authorization: Bearer {token}

template_name: "我的自定义模板"
description: "适合技术分享的模板"
tags: ["技术", "分享", "深色"]
html_file: template.html
```

**响应**:
```json
{
  "message": "模板上传成功",
  "template_id": "custom_username_1770182800",
  "template_name": "我的自定义模板",
  "id": "507f1f77bcf86cd799439011"
}
```

### 2. 上传 PPTX 模板

```http
POST /api/ppt/templates/upload-pptx
Content-Type: multipart/form-data
Authorization: Bearer {token}

template_name: "公司标准模板"
description: "公司官方 PPT 模板"
tags: ["官方", "标准"]
pptx_file: company_template.pptx
```

### 3. 获取我的模板

```http
GET /api/ppt/templates/my-templates
Authorization: Bearer {token}
```

**响应**:
```json
{
  "total": 3,
  "templates": [
    {
      "id": "...",
      "template_id": "custom_username_1770182800",
      "template_name": "我的自定义模板",
      "description": "适合技术分享的模板",
      "tags": ["技术", "分享", "深色", "自定义"],
      "is_active": true,
      "source": "custom",
      "created_at": "2026-02-04T13:40:00Z"
    }
  ]
}
```

### 4. 更新模板

```http
PUT /api/ppt/templates/{template_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "template_name": "新名称",
  "description": "新描述",
  "tags": "[\"新标签1\", \"新标签2\"]",
  "is_active": true
}
```

### 5. 删除模板

```http
DELETE /api/ppt/templates/{template_id}
Authorization: Bearer {token}
```

**注意**:
- 只能删除自己创建的模板
- 管理员可以删除任何模板
- 不能删除内置模板

---

## 💻 前端使用示例

### 1. 上传 HTML 模板

```vue
<template>
  <el-dialog title="上传自定义模板" v-model="showUploadDialog">
    <el-form :model="uploadForm">
      <el-form-item label="模板名称">
        <el-input v-model="uploadForm.template_name" />
      </el-form-item>
      
      <el-form-item label="描述">
        <el-input type="textarea" v-model="uploadForm.description" />
      </el-form-item>
      
      <el-form-item label="标签">
        <el-tag
          v-for="tag in uploadForm.tags"
          :key="tag"
          closable
          @close="removeTag(tag)"
        >
          {{ tag }}
        </el-tag>
        <el-input
          v-model="newTag"
          size="small"
          @keyup.enter="addTag"
          placeholder="输入标签后按回车"
        />
      </el-form-item>
      
      <el-form-item label="HTML 文件">
        <el-upload
          ref="upload"
          :auto-upload="false"
          :limit="1"
          accept=".html,.htm"
          :on-change="handleFileChange"
        >
          <el-button slot="trigger" size="small" type="primary">
            选择文件
          </el-button>
        </el-upload>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="showUploadDialog = false">取消</el-button>
      <el-button type="primary" @click="uploadTemplate">上传</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const uploadForm = ref({
  template_name: '',
  description: '',
  tags: []
})

const selectedFile = ref(null)

function handleFileChange(file) {
  selectedFile.value = file.raw
}

async function uploadTemplate() {
  if (!selectedFile.value) {
    ElMessage.error('请选择 HTML 文件')
    return
  }
  
  const formData = new FormData()
  formData.append('template_name', uploadForm.value.template_name)
  formData.append('description', uploadForm.value.description)
  formData.append('tags', JSON.stringify(uploadForm.value.tags))
  formData.append('html_file', selectedFile.value)
  
  try {
    const response = await axios.post(
      '/api/ppt/templates/upload-html',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    
    ElMessage.success('模板上传成功！')
    showUploadDialog.value = false
    
    // 刷新模板列表
    loadTemplates()
  } catch (error) {
    ElMessage.error('上传失败: ' + error.message)
  }
}
</script>
```

### 2. 使用自定义模板生成 PPT

```javascript
// 生成 PPT 时指定自定义模板
async function generatePPT() {
  const response = await axios.post(
    `/api/ppt/drafts/${draftId}/generate`,
    null,
    {
      params: {
        template_id: 'custom_username_1770182800',  // 自定义模板 ID
        save_to_knowledge: true
      }
    }
  )
  
  console.log('生成成功:', response.data)
}
```

---

## 📝 HTML 模板示例

### 示例 1: 简约风格

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{{ page_title }}</title>
    <style>
        body {
            width: 1280px;
            height: 720px;
            margin: 0;
            padding: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Microsoft YaHei', sans-serif;
            color: white;
        }
        
        h1 {
            font-size: 56px;
            font-weight: bold;
            margin-bottom: 40px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .content {
            font-size: 28px;
            line-height: 1.8;
        }
        
        .content ul {
            list-style: none;
            padding: 0;
        }
        
        .content li {
            margin-bottom: 20px;
            padding-left: 40px;
            position: relative;
        }
        
        .content li:before {
            content: "▶";
            position: absolute;
            left: 0;
            color: #ffd700;
        }
        
        .footer {
            position: absolute;
            bottom: 40px;
            right: 60px;
            font-size: 24px;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <h1>{{ main_heading }}</h1>
    <div class="content">
        {{ page_content }}
    </div>
    <div class="footer">
        {{ current_page_number }} / {{ total_page_count }}
    </div>
</body>
</html>
```

### 示例 2: 卡片风格

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{{ page_title }}</title>
    <style>
        body {
            width: 1280px;
            height: 720px;
            margin: 0;
            padding: 0;
            background: #f5f5f5;
            font-family: 'Microsoft YaHei', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .card {
            width: 1100px;
            height: 600px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            padding: 60px;
            position: relative;
        }
        
        h1 {
            font-size: 48px;
            color: #333;
            margin-bottom: 30px;
            border-bottom: 4px solid #3b82f6;
            padding-bottom: 20px;
        }
        
        .content {
            font-size: 24px;
            line-height: 1.8;
            color: #666;
        }
        
        .footer {
            position: absolute;
            bottom: 30px;
            right: 60px;
            font-size: 20px;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>{{ main_heading }}</h1>
        <div class="content">
            {{ page_content }}
        </div>
        <div class="footer">
            {{ current_page_number }} / {{ total_page_count }}
        </div>
    </div>
</body>
</html>
```

---

## 🔒 权限说明

| 操作 | 普通用户 | 管理员 |
|------|---------|--------|
| 上传模板 | ✅ | ✅ |
| 查看自己的模板 | ✅ | ✅ |
| 查看所有模板 | ✅ | ✅ |
| 更新自己的模板 | ✅ | ✅ |
| 更新他人的模板 | ❌ | ✅ |
| 删除自己的模板 | ✅ | ✅ |
| 删除他人的模板 | ❌ | ✅ |
| 删除内置模板 | ❌ | ❌ |

---

## ⚠️ 注意事项

### 1. HTML 模板要求
- 必须包含所有必需占位符
- 建议固定尺寸为 1280x720（16:9）
- 避免使用外部资源（CDN 可能加载失败）
- 测试不同内容长度的显示效果

### 2. 文件大小限制
- HTML 文件：建议 < 1MB
- PPTX 文件：建议 < 10MB

### 3. 安全性
- 上传的 HTML 会被渲染，请勿包含恶意代码
- 系统会验证必需占位符
- 仅创建者和管理员可以修改/删除模板

### 4. 性能
- 复杂的 HTML 模板可能增加渲染时间
- 建议优化 CSS 和 JavaScript
- 避免大量动画和特效

---

## 🎯 最佳实践

### 1. 模板设计
- 保持简洁，突出内容
- 使用清晰的字体和颜色
- 确保在不同内容长度下都能正常显示
- 测试多页 PPT 的一致性

### 2. 命名规范
- 模板名称：简洁明了，如"技术分享-深色"
- 标签：使用通用标签，便于筛选
- 描述：说明适用场景和特点

### 3. 测试流程
1. 上传模板
2. 创建测试 PPT 草稿
3. 使用自定义模板生成
4. 检查渲染效果
5. 根据需要调整模板

---

## 📊 完整功能对比

| 功能 | 内置模板 | 自定义 HTML | 自定义 PPTX |
|------|---------|------------|------------|
| 数量 | 25个 | 无限 | 无限 |
| 质量 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 自定义程度 | ❌ | ✅ 完全自定义 | ⚠️ 有限 |
| 上传 | ❌ | ✅ | ✅ |
| 管理 | ❌ | ✅ | ✅ |
| 推荐度 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

**🎉 现在你可以上传和管理自己的 PPT 模板了！**
