# 知识库文件预览问题说明

## 问题描述
Office Online预览出现"An error occurred"错误，无法正常预览Word和Excel文档。

## 原因分析

### 1. Office Online的工作原理
Office Online (view.officeapps.live.com) 需要：
- 文件URL必须是**公开可访问**的（不需要认证）
- 文件URL必须是**完整的HTTP/HTTPS地址**
- Office Online服务器需要能够**下载文件内容**

### 2. 当前实现的问题
```javascript
const fileUrl = encodeURIComponent(
  window.location.origin + getFilePreviewUrl(doc)
);
// 例如: http://114.66.56.200:6004/uploads/knowledge/xxx/file.docx
```

问题：
- ❌ 文件路径需要认证（token）
- ❌ Office Online无法访问需要认证的URL
- ❌ 内网地址Office Online无法访问

## 解决方案

### 方案1：使用本地预览（推荐）
不依赖Office Online，使用浏览器原生能力：

#### PDF文件
- ✅ 使用iframe直接预览
- ✅ 浏览器原生支持
- ✅ 无需外部服务

#### Word/Excel文件
- 📥 提供下载按钮
- 💡 提示用户下载后使用本地Office打开
- 🔄 或者后端转换为PDF后预览

### 方案2：后端文本提取（当前实现）
```python
# 后端已实现文本提取
- Word: 使用python-docx提取文本
- Excel: 使用openpyxl提取文本
```

优点：
- ✅ 无需外部服务
- ✅ 快速预览文本内容
- ✅ 适合快速查看

缺点：
- ⚠️ 丢失格式
- ⚠️ 无法显示图片/表格

### 方案3：生成临时公开链接
如果必须使用Office Online：

```python
# 后端实现
@router.get("/knowledge/{doc_id}/public-url")
async def generate_public_url(doc_id: str):
    # 1. 生成临时token（有效期5分钟）
    temp_token = generate_temp_token(doc_id, expires_in=300)
    
    # 2. 返回公开URL
    return {
        "url": f"{BASE_URL}/api/knowledge/public/{temp_token}",
        "expires_at": "..."
    }

@router.get("/knowledge/public/{temp_token}")
async def get_public_file(temp_token: str):
    # 验证临时token
    # 返回文件内容（无需认证）
    ...
```

### 方案4：转换为PDF（最佳体验）
```python
# 使用LibreOffice转换
import subprocess

def convert_to_pdf(input_file, output_file):
    subprocess.run([
        'libreoffice',
        '--headless',
        '--convert-to', 'pdf',
        '--outdir', output_dir,
        input_file
    ])
```

优点：
- ✅ 保留格式
- ✅ 浏览器原生支持
- ✅ 无需外部服务

## 推荐实现

### 短期方案（立即可用）
1. **PDF**: 继续使用iframe预览
2. **Word/Excel**: 
   - 显示提取的文本内容
   - 提供下载按钮
   - 移除Office Online选项（或添加说明）

### 长期方案（更好体验）
1. 后端添加文档转PDF功能
2. 所有文档统一转为PDF预览
3. 保留原文件下载

## 代码修改建议

### 前端修改
```vue
<!-- Word/Excel预览 -->
<div v-else-if="['word', 'excel'].includes(currentKnowledge.file_type)">
  <el-alert type="info" :closable="false">
    <template #title>
      <div style="display: flex; justify-content: space-between;">
        <span>{{ currentKnowledge.file_type === 'word' ? 'Word' : 'Excel' }} 文档</span>
        <el-button type="primary" size="small" @click="downloadKnowledge(currentKnowledge)">
          <el-icon><Download /></el-icon> 下载完整文档
        </el-button>
      </div>
    </template>
    <div>
      💡 提示：浏览器无法直接预览Office文档，请下载后使用本地Office软件打开查看完整内容。
    </div>
  </el-alert>
  
  <!-- 文本内容预览 -->
  <div v-if="currentKnowledge.content" class="content-preview">
    <h4>📄 文本内容预览（已提取）</h4>
    <div class="word-content-preview">
      <pre>{{ currentKnowledge.content }}</pre>
    </div>
    <el-alert type="warning" :closable="false" style="margin-top: 10px;">
      注意：此为提取的纯文本内容，不包含格式、图片、表格等元素。
    </el-alert>
  </div>
</div>
```

### 后端添加PDF转换（可选）
```python
# requirements.txt
unoconv  # 或 libreoffice

# 转换函数
async def convert_to_pdf(file_path: str) -> str:
    pdf_path = file_path.replace('.docx', '.pdf').replace('.xlsx', '.pdf')
    if os.path.exists(pdf_path):
        return pdf_path
    
    # 使用unoconv转换
    subprocess.run(['unoconv', '-f', 'pdf', file_path])
    return pdf_path
```

## 总结

- ❌ **不推荐**：Office Online（需要公开URL，部署复杂）
- ✅ **推荐**：文本提取 + 下载（当前实现，简单可靠）
- 🌟 **最佳**：转PDF预览（需要额外部署，体验最好）
