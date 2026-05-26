<template>
  <div class="enhanced-template-selector">
    <!-- 顶部操作栏 -->
    <div class="selector-header">
      <div class="header-left">
        <h3>选择 PPT 模板</h3>
        <el-tag type="info" size="small">
          共 {{ templates.length }} 个模板
        </el-tag>
      </div>
      <div class="header-right">
        <el-button type="primary" size="small" @click="showUploadDialog = true">
          <el-icon><Upload /></el-icon>
          上传自定义模板
        </el-button>
      </div>
    </div>

    <!-- 标签筛选 -->
    <div class="template-filters">
      <span class="filter-label">筛选：</span>
      <el-tag
        v-for="tag in allTags"
        :key="tag"
        :type="selectedTag === tag ? 'primary' : 'info'"
        :effect="selectedTag === tag ? 'dark' : 'plain'"
        class="tag-filter"
        @click="selectTag(tag)"
      >
        {{ tag }}
      </el-tag>
      <el-tag
        v-if="selectedTag"
        type="danger"
        effect="plain"
        class="tag-filter"
        @click="clearTag"
      >
        <el-icon><Close /></el-icon>
        清除筛选
      </el-tag>
    </div>

    <!-- 模板网格 -->
    <div v-loading="loading" class="template-grid">
      <div
        v-for="template in filteredTemplates"
        :key="template.template_id"
        class="template-card"
        :class="{ selected: selectedTemplateId === template.template_id }"
        @click="selectTemplate(template)"
      >
        <!-- 来源标记 -->
        <div class="source-badge">
          <el-tag v-if="template.is_default" type="success" size="small">
            默认
          </el-tag>
          <el-tag
            v-else-if="template.source === 'landppt'"
            type="primary"
            size="small"
          >
            内置
          </el-tag>
          <el-tag
            v-else-if="template.source === 'custom'"
            type="warning"
            size="small"
          >
            自定义
          </el-tag>
          <el-tag
            v-else-if="template.source === 'pptx_upload'"
            type="info"
            size="small"
          >
            PPTX
          </el-tag>
        </div>

        <!-- 模板预览 -->
        <div class="template-preview" :style="getPreviewStyle(template)">
          <div class="preview-placeholder">
            <el-icon :size="48">
              <Document />
            </el-icon>
            <p>{{ template.template_name }}</p>
          </div>
        </div>

        <!-- 模板信息 -->
        <div class="template-info">
          <h4 class="template-name">{{ template.template_name }}</h4>
          <p class="template-description">
            {{ template.description || "暂无描述" }}
          </p>

          <!-- 标签 -->
          <div class="template-tags">
            <el-tag
              v-for="tag in template.tags.slice(0, 3)"
              :key="tag"
              size="small"
              type="info"
              effect="plain"
            >
              {{ tag }}
            </el-tag>
            <el-tag
              v-if="template.tags.length > 3"
              size="small"
              type="info"
              effect="plain"
            >
              +{{ template.tags.length - 3 }}
            </el-tag>
          </div>
        </div>

        <!-- 选中标记 -->
        <div
          v-if="selectedTemplateId === template.template_id"
          class="selected-mark"
        >
          <el-icon><Check /></el-icon>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty
      v-if="!loading && filteredTemplates.length === 0"
      description="没有找到匹配的模板"
    >
      <el-button type="primary" @click="clearTag"> 清除筛选 </el-button>
    </el-empty>

    <!-- 上传对话框 -->
    <TemplateUploadDialog
      v-model="showUploadDialog"
      @success="handleUploadSuccess"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { Upload, Close, Document, Check } from "@element-plus/icons-vue";
import axios from "axios";
import TemplateUploadDialog from "./TemplateUploadDialog.vue";

const props = defineProps({
  modelValue: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["update:modelValue", "select"]);

const loading = ref(false);
const templates = ref([]);
const allTags = ref([]);
const selectedTag = ref(null);
const selectedTemplateId = ref(props.modelValue);
const showUploadDialog = ref(false);

// 过滤后的模板
const filteredTemplates = computed(() => {
  if (!selectedTag.value) {
    return templates.value;
  }
  return templates.value.filter((t) => t.tags.includes(selectedTag.value));
});

// 获取预览样式
function getPreviewStyle(template) {
  const gradients = [
    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    "linear-gradient(135deg, #30cfd0 0%, #330867 100%)",
  ];

  // 根据模板 ID 生成一个稳定的索引
  const hash = template.template_id
    .split("")
    .reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const index = hash % gradients.length;

  return {
    background: gradients[index],
  };
}

// 加载模板列表
async function loadTemplates() {
  loading.value = true;
  try {
    const token = localStorage.getItem("token");
    const res = await axios.get("/api/ppt/templates/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    templates.value = res.data.templates;

    // 如果没有选中模板，默认选中默认模板
    if (!selectedTemplateId.value) {
      const defaultTemplate = templates.value.find((t) => t.is_default);
      if (defaultTemplate) {
        selectTemplate(defaultTemplate);
      }
    }
  } catch (error) {
    ElMessage.error("加载模板失败: " + error.message);
  } finally {
    loading.value = false;
  }
}

// 加载所有标签
async function loadTags() {
  try {
    const token = localStorage.getItem("token");
    const res = await axios.get("/api/ppt/templates/tags/all", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    allTags.value = res.data.tags;
  } catch (error) {
    console.error("加载标签失败:", error);
  }
}

// 选择标签
function selectTag(tag) {
  selectedTag.value = tag;
}

// 清除标签筛选
function clearTag() {
  selectedTag.value = null;
}

// 选择模板
function selectTemplate(template) {
  selectedTemplateId.value = template.template_id;
  emit("update:modelValue", template.template_id);
  emit("select", template);
}

// 上传成功回调
function handleUploadSuccess(data) {
  ElMessage.success("模板上传成功！");
  // 重新加载模板列表
  loadTemplates();
  loadTags();
}

onMounted(() => {
  loadTemplates();
  loadTags();
});
</script>

<style scoped>
.enhanced-template-selector {
  width: 100%;
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e5e7eb;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.template-filters {
  margin-bottom: 20px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.filter-label {
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
}

.tag-filter {
  cursor: pointer;
  transition: all 0.3s;
}

.tag-filter:hover {
  transform: translateY(-2px);
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  min-height: 200px;
}

.template-card {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  background: white;
}

.template-card:hover {
  border-color: #3b82f6;
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.template-card.selected {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.source-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
}

.template-preview {
  height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.preview-placeholder {
  text-align: center;
}

.preview-placeholder p {
  margin: 10px 0 0 0;
  font-size: 14px;
  font-weight: 500;
}

.template-info {
  padding: 15px;
}

.template-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.template-description {
  margin: 0 0 10px 0;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 40px;
}

.template-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.selected-mark {
  position: absolute;
  bottom: 15px;
  right: 15px;
  width: 32px;
  height: 32px;
  background: #3b82f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}
</style>
