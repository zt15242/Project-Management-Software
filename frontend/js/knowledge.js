// 知识库管理
let currentProject = '';
let currentCategory = '';
let currentFileTypes = [];
let currentTags = [];

// 页面加载
document.addEventListener('DOMContentLoaded', async function () {
    checkAuth();
    await loadProjects();
    await loadCategories();
    await loadTags();
    await loadKnowledgeList();
    await loadStatistics();

    // 绑定事件
    document.getElementById('uploadForm').addEventListener('submit', handleUpload);
    document.getElementById('projectFilter').addEventListener('change', handleProjectFilter);

    // 文件类型筛选
    document.querySelectorAll('.filter-group input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', handleFileTypeFilter);
    });
});

// 加载项目列表
async function loadProjects() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/projects/`, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        if (response.ok) {
            const projects = await response.json();
            const projectFilter = document.getElementById('projectFilter');
            const docProject = document.getElementById('docProject');

            projects.forEach(project => {
                const option1 = document.createElement('option');
                option1.value = project.id;
                option1.textContent = project.name;
                projectFilter.appendChild(option1);

                const option2 = document.createElement('option');
                option2.value = project.id;
                option2.textContent = project.name;
                docProject.appendChild(option2);
            });
        }
    } catch (error) {
        console.error('加载项目失败:', error);
    }
}

// 加载分类列表
async function loadCategories() {
    try {
        const url = currentProject
            ? `${API_BASE_URL}/api/knowledge/categories/list?project_id=${currentProject}`
            : `${API_BASE_URL}/api/knowledge/categories/list`;

        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            const categoryList = document.getElementById('categoryList');

            if (data.categories.length === 0) {
                categoryList.innerHTML = '<div class="empty">暂无分类</div>';
            } else {
                categoryList.innerHTML = data.categories.map(cat =>
                    `<div class="category-item ${currentCategory === cat ? 'active' : ''}" 
                          onclick="selectCategory('${cat}')">
                        📁 ${cat}
                    </div>`
                ).join('');
            }
        }
    } catch (error) {
        console.error('加载分类失败:', error);
    }
}

// 加载标签列表
async function loadTags() {
    try {
        const url = currentProject
            ? `${API_BASE_URL}/api/knowledge/tags/list?project_id=${currentProject}`
            : `${API_BASE_URL}/api/knowledge/tags/list`;

        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            const tagList = document.getElementById('tagList');

            if (data.tags.length === 0) {
                tagList.innerHTML = '<div class="empty">暂无标签</div>';
            } else {
                tagList.innerHTML = data.tags.map(tag =>
                    `<span class="tag ${currentTags.includes(tag) ? 'active' : ''}" 
                           onclick="toggleTag('${tag}')">
                        ${tag}
                    </span>`
                ).join('');
            }
        }
    } catch (error) {
        console.error('加载标签失败:', error);
    }
}

// 加载统计信息
async function loadStatistics() {
    if (!currentProject) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/knowledge/statistics/${currentProject}`, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        if (response.ok) {
            const stats = await response.json();
            document.getElementById('totalDocs').textContent = stats.total_docs;
            document.getElementById('totalViews').textContent = stats.total_views;
        }
    } catch (error) {
        console.error('加载统计失败:', error);
    }
}

// 加载知识库列表
async function loadKnowledgeList() {
    const listContainer = document.getElementById('knowledgeList');
    listContainer.innerHTML = '<div class="loading">加载中...</div>';

    try {
        let url = `${API_BASE_URL}/api/knowledge/?`;
        const params = [];

        if (currentProject) params.push(`project_id=${currentProject}`);
        if (currentCategory) params.push(`category=${encodeURIComponent(currentCategory)}`);
        if (currentFileTypes.length > 0) {
            currentFileTypes.forEach(type => params.push(`file_type=${type}`));
        }

        url += params.join('&');

        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        if (response.ok) {
            const docs = await response.json();

            if (docs.length === 0) {
                listContainer.innerHTML = '<div class="empty-state">📭 暂无文档</div>';
            } else {
                listContainer.innerHTML = docs.map(doc => createDocCard(doc)).join('');
            }
        } else {
            listContainer.innerHTML = '<div class="error">加载失败</div>';
        }
    } catch (error) {
        console.error('加载知识库失败:', error);
        listContainer.innerHTML = '<div class="error">加载失败</div>';
    }
}

// 创建文档卡片
function createDocCard(doc) {
    const fileTypeIcons = {
        'markdown': '📝',
        'word': '📄',
        'excel': '📊',
        'pdf': '📕',
        'text': '📃',
        'image': '🖼️',
        'other': '📎'
    };

    const icon = fileTypeIcons[doc.file_type] || '📎';
    const fileSize = formatFileSize(doc.file_size);
    const createdAt = new Date(doc.created_at).toLocaleString('zh-CN');

    return `
        <div class="doc-card" onclick="viewDocument('${doc.id}')">
            <div class="doc-icon">${icon}</div>
            <div class="doc-info">
                <h3 class="doc-title">${doc.title}</h3>
                <p class="doc-description">${doc.description || '暂无描述'}</p>
                <div class="doc-meta">
                    <span class="meta-item">📁 ${doc.category || '未分类'}</span>
                    <span class="meta-item">📏 ${fileSize}</span>
                    <span class="meta-item">👁️ ${doc.views} 次浏览</span>
                    <span class="meta-item">🕐 ${createdAt}</span>
                </div>
                ${doc.tags && doc.tags.length > 0 ? `
                    <div class="doc-tags">
                        ${doc.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                ` : ''}
            </div>
            <div class="doc-actions">
                ${canPreviewOnline(doc.file_type) ? `
                    <button onclick="previewDocument('${doc.id}', '${doc.file_type}'); event.stopPropagation();" 
                            class="btn btn-sm btn-success">在线预览</button>
                ` : ''}
                <button onclick="downloadDocument('${doc.id}', '${doc.file_name}'); event.stopPropagation();" 
                        class="btn btn-sm btn-primary">下载</button>
                <button onclick="deleteDocument('${doc.id}'); event.stopPropagation();" 
                        class="btn btn-sm btn-danger">删除</button>
            </div>
        </div>
    `;
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
}

// 项目筛选
function handleProjectFilter(e) {
    currentProject = e.target.value;
    loadCategories();
    loadTags();
    loadKnowledgeList();
    loadStatistics();
}

// 文件类型筛选
function handleFileTypeFilter() {
    currentFileTypes = Array.from(document.querySelectorAll('.filter-group input[type="checkbox"]:checked'))
        .map(cb => cb.value);
    loadKnowledgeList();
}

// 选择分类
function selectCategory(category) {
    currentCategory = currentCategory === category ? '' : category;
    loadCategories();
    loadKnowledgeList();
}

// 切换标签
function toggleTag(tag) {
    const index = currentTags.indexOf(tag);
    if (index > -1) {
        currentTags.splice(index, 1);
    } else {
        currentTags.push(tag);
    }
    loadTags();
    loadKnowledgeList();
}

// 搜索知识库
async function searchKnowledge() {
    const keyword = document.getElementById('searchInput').value.trim();
    const listContainer = document.getElementById('knowledgeList');
    listContainer.innerHTML = '<div class="loading">搜索中...</div>';

    try {
        let url = `${API_BASE_URL}/api/knowledge/?`;
        const params = [];

        if (currentProject) params.push(`project_id=${currentProject}`);
        if (keyword) params.push(`keyword=${encodeURIComponent(keyword)}`);

        url += params.join('&');

        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        if (response.ok) {
            const docs = await response.json();

            if (docs.length === 0) {
                listContainer.innerHTML = '<div class="empty-state">🔍 未找到相关文档</div>';
            } else {
                listContainer.innerHTML = docs.map(doc => createDocCard(doc)).join('');
            }
        }
    } catch (error) {
        console.error('搜索失败:', error);
        listContainer.innerHTML = '<div class="error">搜索失败</div>';
    }
}

// 显示上传模态框
function showUploadModal() {
    document.getElementById('uploadModal').style.display = 'flex';
}

// 关闭上传模态框
function closeUploadModal() {
    document.getElementById('uploadModal').style.display = 'none';
    document.getElementById('uploadForm').reset();
}

// 处理文件上传
async function handleUpload(e) {
    e.preventDefault();

    const title = document.getElementById('docTitle').value;
    const projectId = document.getElementById('docProject').value;
    const category = document.getElementById('docCategory').value;
    const description = document.getElementById('docDescription').value;
    const tags = document.getElementById('docTags').value;
    const file = document.getElementById('docFile').files[0];

    if (!file) {
        alert('请选择文件');
        return;
    }

    const formData = new FormData();
    formData.append('title', title);
    formData.append('project_id', projectId);
    if (category) formData.append('category', category);
    if (description) formData.append('description', description);
    if (tags) formData.append('tags', tags);
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/api/knowledge/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`
            },
            body: formData
        });

        if (response.ok) {
            alert('上传成功！');
            closeUploadModal();
            loadKnowledgeList();
            loadCategories();
            loadTags();
            loadStatistics();
        } else {
            const error = await response.json();
            alert('上传失败：' + (error.detail || '未知错误'));
        }
    } catch (error) {
        console.error('上传失败:', error);
        alert('上传失败：' + error.message);
    }
}

// 查看文档详情
async function viewDocument(docId) {
    const modal = document.getElementById('detailModal');
    const content = document.getElementById('detailContent');

    modal.style.display = 'flex';
    content.innerHTML = '<div class="loading">加载中...</div>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/knowledge/${docId}`, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        if (response.ok) {
            const doc = await response.json();
            document.getElementById('detailTitle').textContent = doc.title;

            let html = `
                <div class="doc-detail">
                    <div class="detail-header">
                        <div class="detail-meta">
                            <span>📁 ${doc.category || '未分类'}</span>
                            <span>📏 ${formatFileSize(doc.file_size)}</span>
                            <span>👁️ ${doc.views} 次浏览</span>
                        </div>
                        ${doc.tags && doc.tags.length > 0 ? `
                            <div class="detail-tags">
                                ${doc.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                            </div>
                        ` : ''}
                    </div>
                    
                    ${doc.description ? `
                        <div class="detail-section">
                            <h3>描述</h3>
                            <p>${doc.description}</p>
                        </div>
                    ` : ''}
                    
                    <div class="detail-section">
                        <h3>文件信息</h3>
                        <div class="file-info-section">
                            <div class="info-row">
                                <span class="info-label">文件名：</span>
                                <span>${doc.file_name}</span>
                            </div>
                            ${doc.file_path && doc.file_path.startsWith('http') ? `
                                <div class="info-row">
                                    <span class="info-label">存储位置：</span>
                                    <span class="oss-badge">☁️ 对象存储(OSS)</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">文件链接：</span>
                                    <div class="file-link-actions">
                                        <input type="text" value="${doc.file_path}" readonly class="file-link-input" id="filePathInput_${doc.id}">
                                        <button onclick="copyFileLink('${doc.id}')" class="btn btn-sm btn-secondary">复制链接</button>
                                        <button onclick="window.open('${doc.file_path}', '_blank')" class="btn btn-sm btn-success">在线查看</button>
                                    </div>
                                </div>
                            ` : `
                                <div class="info-row">
                                    <span class="info-label">存储位置：</span>
                                    <span class="local-badge">💾 本地存储</span>
                                </div>
                            `}
                        </div>
                    </div>
                    
                    ${doc.content ? `
                        <div class="detail-section">
                            <h3>内容预览</h3>
                            <div class="content-preview">${escapeHtml(doc.content.substring(0, 2000))}${doc.content.length > 2000 ? '...' : ''}</div>
                        </div>
                    ` : ''}
                    
                    <div class="detail-actions">
                        ${canPreviewOnline(doc.file_type) ? `
                            <button onclick="previewDocument('${doc.id}', '${doc.file_type}')" class="btn btn-success">在线预览</button>
                        ` : ''}
                        <button onclick="downloadDocument('${doc.id}', '${doc.file_name}')" class="btn btn-primary">下载文件</button>
                    </div>
                </div>
            `;

            content.innerHTML = html;
        } else {
            content.innerHTML = '<div class="error">加载失败</div>';
        }
    } catch (error) {
        console.error('加载文档详情失败:', error);
        content.innerHTML = '<div class="error">加载失败</div>';
    }
}

// 关闭详情模态框
function closeDetailModal() {
    document.getElementById('detailModal').style.display = 'none';
}

// 判断文件是否支持在线预览
function canPreviewOnline(fileType) {
    // Office Online 支持的文件类型
    const supportedTypes = ['word', 'excel', 'powerpoint'];
    return supportedTypes.includes(fileType);
}

// 在线预览文档
async function previewDocument(docId, fileType) {
    try {
        // 1. 生成临时公开URL
        const response = await fetch(`${API_BASE_URL}/api/knowledge/${docId}/public-url?expires_minutes=10`, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        if (!response.ok) {
            throw new Error('生成预览链接失败');
        }

        const data = await response.json();
        const publicUrl = data.public_url;

        // 2. 构建 Office Online 预览 URL
        // 根据文件类型选择不同的预览服务
        let previewUrl;

        if (fileType === 'word') {
            // Word 文档
            previewUrl = `https://view.officeapps.live.com/op/view.aspx?src=${encodeURIComponent(publicUrl)}`;
        } else if (fileType === 'excel') {
            // Excel 表格
            previewUrl = `https://view.officeapps.live.com/op/view.aspx?src=${encodeURIComponent(publicUrl)}`;
        } else if (fileType === 'powerpoint') {
            // PowerPoint 演示文稿
            previewUrl = `https://view.officeapps.live.com/op/view.aspx?src=${encodeURIComponent(publicUrl)}`;
        } else {
            alert('该文件类型暂不支持在线预览');
            return;
        }

        // 3. 打开新窗口预览
        const previewWindow = window.open(previewUrl, '_blank');

        if (!previewWindow) {
            alert('无法打开预览窗口,请检查浏览器弹窗设置');
        } else {
            alert(`预览链接已生成,有效期 ${Math.floor(data.expires_in_seconds / 60)} 分钟`);
        }

    } catch (error) {
        console.error('预览失败:', error);
        alert('预览失败: ' + error.message);
    }
}

// 下载文档
async function downloadDocument(docId, fileName) {
    console.log('downloadDocument called with:', docId, fileName);
    try {
        // 获取文档详情以获取file_path
        const response = await fetch(`${API_BASE_URL}/api/knowledge/${docId}`, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        if (response.ok) {
            const doc = await response.json();
            console.log('Document data:', doc);
            console.log('file_path:', doc.file_path);
            console.log('Starts with http?', doc.file_path && doc.file_path.startsWith('http'));

            // 如果file_path是OSS URL（以http开头），直接使用
            if (doc.file_path && doc.file_path.startsWith('http')) {
                console.log('Opening OSS URL:', doc.file_path);
                window.open(doc.file_path, '_blank');
            } else {
                // 本地文件，使用原有路径
                const localUrl = `${API_BASE_URL}/uploads/knowledge/${docId}/${fileName}`;
                console.log('Opening local URL:', localUrl);
                window.open(localUrl, '_blank');
            }
        } else {
            alert('获取下载链接失败');
        }
    } catch (error) {
        console.error('下载失败:', error);
        alert('下载失败: ' + error.message);
    }
}

// 删除文档
async function deleteDocument(docId) {
    if (!confirm('确定要删除这个文档吗？')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/knowledge/${docId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        if (response.ok) {
            alert('删除成功！');
            loadKnowledgeList();
            loadStatistics();
        } else {
            const error = await response.json();
            alert('删除失败：' + (error.detail || '未知错误'));
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败：' + error.message);
    }
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 复制文件链接
function copyFileLink(docId) {
    const input = document.getElementById(`filePathInput_${docId}`);
    if (input) {
        input.select();
        document.execCommand('copy');
        alert('链接已复制到剪贴板');
    }
}

// 点击模态框外部关闭
window.onclick = function (event) {
    const uploadModal = document.getElementById('uploadModal');
    const detailModal = document.getElementById('detailModal');

    if (event.target === uploadModal) {
        closeUploadModal();
    }
    if (event.target === detailModal) {
        closeDetailModal();
    }
}
