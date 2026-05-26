<template>
  <div class="landppt-template-selector">
    <!-- 标签筛选 -->
    <div class="template-filters">
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
        <!-- 默认标记 -->
        <div v-if="template.is_default" class="default-badge">
          <el-tag type="success" size="small">默认</el-tag>
        </div>

        <!-- 模板预览 -->
        <div class="template-preview">
          <div class="preview-placeholder">
            <i class="el-icon-document"></i>
            <p>{{ template.template_name }}</p>
          </div>
        </div>

        <!-- 模板信息 -->
        <div class="template-info">
          <h4 class="template-name">{{ template.template_name }}</h4>
          <p class="template-description">{{ template.description }}</p>

          <!-- 标签 -->
          <div class="template-tags">
            <el-tag
              v-for="tag in template.tags"
              :key="tag"
              size="small"
              type="info"
              effect="plain"
            >
              {{ tag }}
            </el-tag>
          </div>
        </div>

        <!-- 选中标记 -->
        <div
          v-if="selectedTemplateId === template.template_id"
          class="selected-mark"
        >
          <i class="el-icon-check"></i>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty
      v-if="!loading && filteredTemplates.length === 0"
      description="没有找到匹配的模板"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import axios from "axios";
import { ElMessage } from "element-plus";

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

// 过滤后的模板
const filteredTemplates = computed(() => {
  if (!selectedTag.value) {
    return templates.value;
  }
  return templates.value.filter((t) => t.tags.includes(selectedTag.value));
});

// 加载模板列表
async function loadTemplates() {
  loading.value = true;
  try {
    const res = await axios.get("/api/ppt/templates/");
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
    const res = await axios.get("/api/ppt/templates/tags/all");
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

onMounted(() => {
  loadTemplates();
  loadTags();
});
</script>

<style scoped>
.landppt-template-selector {
  width: 100%;
}

.template-filters {
  margin-bottom: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
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

.default-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
}

.template-preview {
  height: 160px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.preview-placeholder {
  text-align: center;
}

.preview-placeholder i {
  font-size: 48px;
  margin-bottom: 10px;
}

.preview-placeholder p {
  margin: 0;
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
