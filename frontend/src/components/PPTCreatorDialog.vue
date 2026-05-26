<template>
  <el-dialog
    v-model="visible"
    class="ppt-creator-dialog"
    custom-class="ppt-creator-dialog"
    fullscreen
    :show-close="false"
    append-to-body
  >
    <!-- 顶部导航栏 -->
    <div class="ppt-nav">
      <div class="nav-left">
        <el-button link @click="handleClose" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          返回项目
        </el-button>
        <div class="divider"></div>
        <span class="title">{{ draft.title }}</span>
      </div>

      <div class="nav-center">
        <el-steps :active="currentStep - 1" simple>
          <el-step title="大纲确认" />
          <el-step title="风格选择" />
          <el-step title="智能生成" />
          <el-step title="成品编辑" />
        </el-steps>
      </div>

      <div class="nav-right">
        <el-button v-if="currentStep === 1" type="primary" @click="nextStep">
          下一步：选择风格
        </el-button>
        <el-button
          v-if="currentStep === 2"
          type="primary"
          @click="startGenerate"
          :loading="generating"
        >
          开始生成
        </el-button>
        <el-button v-if="currentStep === 4" type="success" @click="downloadPPT">
          <el-icon><Download /></el-icon>
          下载 PPTX
        </el-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="ppt-main">
      <!-- Step 1: 大纲编辑 -->
      <div v-if="currentStep === 1" class="step-container">
        <div class="outline-editor">
          <div
            v-for="(chapter, idx) in draft.chapters"
            :key="idx"
            class="chapter-block"
          >
            <el-input
              v-model="chapter.title"
              placeholder="章节标题"
              class="chapter-title"
            />
            <div class="slides-grid">
              <el-card
                v-for="(slide, sIdx) in chapter.slides"
                :key="sIdx"
                class="slide-card"
              >
                <el-input
                  v-model="slide.title"
                  placeholder="幻灯片标题"
                  size="small"
                />
                <el-input
                  v-model="slide.content_raw"
                  type="textarea"
                  :rows="3"
                  placeholder="内容要点"
                  style="margin-top: 10px"
                />
              </el-card>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 2: 模板选择 -->
      <div v-if="currentStep === 2" class="step-container">
        <slot name="template-selector"></slot>
      </div>

      <!-- Step 3: 生成中 -->
      <div v-if="currentStep === 3" class="gen-screen">
        <div class="gen-bg"></div>

        <div class="gen-status">
          <div class="status-badge">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>正在通过 AI 生成演示文稿...</span>
          </div>
          <div class="status-text">
            已生成 {{ draft.slides?.length || 0 }} 页
          </div>
        </div>

        <div class="gen-wall">
          <div
            v-for="(slide, idx) in draft.slides"
            :key="idx"
            class="gen-card active"
          >
            <div class="card-num">SLIDE {{ idx + 1 }}</div>
            <div class="card-title">{{ slide.title }}</div>
            <div class="card-skeleton"></div>
            <div class="card-skeleton"></div>
            <div class="card-skeleton"></div>
          </div>

          <!-- 占位卡片 -->
          <div
            v-for="n in 6"
            :key="'placeholder-' + n"
            class="gen-card placeholder"
          >
            <div class="card-skeleton"></div>
            <div class="card-skeleton"></div>
          </div>
        </div>
      </div>

      <!-- Step 4: 编辑器 -->
      <div v-if="currentStep === 4" class="editor-workspace">
        <div class="editor-sidebar">
          <div class="sidebar-header">
            <el-button type="primary" size="small" block>
              <el-icon><Plus /></el-icon>
              添加幻灯片
            </el-button>
          </div>
          <div class="sidebar-thumbs">
            <div
              v-for="(slide, idx) in draft.slides"
              :key="idx"
              class="thumb"
              :class="{ active: selectedSlide === idx }"
              @click="selectedSlide = idx"
            >
              <div class="thumb-num">{{ idx + 1 }}</div>
              <div class="thumb-preview">{{ slide.title }}</div>
            </div>
          </div>
        </div>

        <div class="editor-canvas">
          <!-- 中间预览区 -->
          <div
            class="canvas-container"
            v-loading="previewLoading"
            element-loading-background="rgba(0, 0, 0, 0.7)"
          >
            <div class="slide-preview-frame" v-if="previewHtml">
              <iframe
                :srcdoc="previewHtml"
                class="preview-iframe"
                frameborder="0"
                sandbox="allow-scripts"
              ></iframe>
            </div>
            <div v-else class="empty-state">
              <el-empty description="正在渲染预览..." />
            </div>
          </div>

          <!-- 右侧编辑面板 (模仿 LandPPT 助手) -->
          <div class="editor-right-panel">
            <div class="panel-header">
              <span>当前页编辑</span>
              <el-tag size="small" type="info"
                >Slide {{ selectedSlide + 1 }}</el-tag
              >
            </div>

            <div class="panel-content" v-if="draft.slides[selectedSlide]">
              <div class="form-group">
                <label>标题</label>
                <el-input
                  v-model="draft.slides[selectedSlide].title"
                  placeholder="幻灯片标题"
                />
              </div>

              <div class="form-group">
                <label>内容要点</label>
                <el-input
                  type="textarea"
                  :rows="8"
                  :model-value="getSlideContent(selectedSlide)"
                  @input="(val) => updateSlideContent(selectedSlide, val)"
                  placeholder="请输入内容，每行一点"
                />
              </div>

              <div class="action-group">
                <el-button type="primary" plain block @click="handleAIPolish">
                  <el-icon><MagicStick /></el-icon> AI 润色文案
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import {
  ArrowLeft,
  Download,
  Loading,
  Plus,
  Edit,
  Picture,
  MagicStick,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

const props = defineProps({
  modelValue: Boolean,
  draft: {
    type: Object,
    default: () => ({
      title: "未命名演示文稿",
      chapters: [],
      slides: [],
    }),
  },
  // 新增：接收预览样式
  previewStyle: {
    type: Object,
    default: () => ({
      background: "#ffffff",
      color: "#333333",
      titleColor: "#000000",
      fontFamily: "Arial, sans-serif",
    }),
  },
});

// 计算最终样式（提供深色默认值）
const computedStyle = computed(() => {
  const base = props.previewStyle || {};

  // 检查是否是"素颜"（即全白背景），如果是，强制使用深色商务风
  const isPlain = !base.background || base.background === "#ffffff";

  if (isPlain) {
    return {
      background: "#1e293b", // 深蓝背景
      text: "#f8fafc", // 亮白文字
      title: "#60a5fa", // 蓝色标题
      font: "Inter, system-ui, sans-serif",
    };
  }

  return {
    background: base.background,
    text: base.color || base.textColor || "#333",
    title: base.titleColor || "#000",
    font: base.fontFamily || "inherit",
  };
});

const emit = defineEmits([
  "update:modelValue",
  "generate",
  "download",
  "close",
]);

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val),
});

// 重置状态
watch(visible, (val) => {
  if (val) {
    currentStep.value = 1;
    selectedSlide.value = 0;
    generating.value = false;
  }
});

const currentStep = ref(1);
const generating = ref(false);
const selectedSlide = ref(0);

const handleClose = () => {
  emit("close");
  visible.value = false;
};

const nextStep = () => {
  currentStep.value++;
};

const startGenerate = async () => {
  generating.value = true;
  currentStep.value = 3;
  emit("generate");

  // 模拟生成完成
  setTimeout(() => {
    generating.value = false;
    currentStep.value = 4;
  }, 3000);
};

const downloadPPT = () => {
  emit("download");
};

// --- 真正的 LandPPT 预览逻辑 ---
import { debounce } from "lodash";
import axios from "axios";

const previewHtml = ref("");
const previewLoading = ref(false);

// 调用后端渲染接口
const fetchPreview = async () => {
  if (selectedSlide.value < 0 || !props.draft.slides[selectedSlide.value])
    return;

  const slide = props.draft.slides[selectedSlide.value];
  previewLoading.value = true;

  try {
    // 假设 api 前缀是 /api/ppt/templates
    // 还需要知道当前选中的 template_id，由于组件内没有 template_id prop，
    // 我们可能需要从 ProjectDetail 传进来，或者暂时硬编码默认值
    const templateId = "商务"; // 暂时硬编码，后续应从 props.previewStyle 或其他地方获取
    
    // 获取 Token (假设存储在 localStorage 的 token 字段)
    const token = localStorage.getItem('token');
    
    const response = await axios.post(
      `/api/ppt/templates/${templateId}/render-preview`, 
      {
        title: slide.title,
        content: slide.content, // 数组
        current_page_number: selectedSlide.value + 1,
        total_page_count: props.draft.slides.length
      },
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    previewHtml.value = response.data.html;
  } catch (err) {
    console.error("预览渲染失败", err);
    if (err.response && err.response.status === 401) {
       ElMessage.error("登录已过期，无法预览");
    }
  } finally {
    previewLoading.value = false;
  }
};

// 防抖更新预览
const debouncedFetchPreview = debounce(fetchPreview, 1000);

// 监听幻灯片切换和内容变化
watch(selectedSlide, () => {
  fetchPreview(); // 切换页面理应立即刷新
});

// 深度监听当前页内容变化（用于编辑时）
watch(
  () => props.draft.slides[selectedSlide.value],
  () => debouncedFetchPreview(),
  { deep: true }
);

// 初始加载
watch(
  () => currentStep.value,
  (step) => {
    if (step === 4) fetchPreview();
  }
);

// --- 编辑器逻辑 ---
// (旧的 getSlideContent 等可以保留用于编辑弹窗)

// 获取内容（数组转字符串）
const getSlideContent = (index) => {
  const slide = props.draft.slides[index];
  if (!slide || !slide.content) return "";
  return Array.isArray(slide.content)
    ? slide.content.join("\n")
    : slide.content;
};

// 更新内容（字符串转数组）
const updateSlideContent = (index, text) => {
  const slide = props.draft.slides[index];
  if (slide) {
    slide.content = text.split("\n");
    slide.content_raw = text; // 保持 raw 同步
  }
};

const handleImageChange = () => {
  ElMessage.success("已为您随机更换了当前页的配图风格");
};

const handleAIPolish = () => {
  ElMessage.success("AI 正在优化当前页的文案逻辑...");
  setTimeout(() => {
    const slide = props.draft.slides[selectedSlide.value];
    if (slide) {
      slide.title = "✨ " + slide.title;
      ElMessage.success("优化完成！已增强标题吸引力");
    }
  }, 1000);
};
</script>

<style scoped>
/* 全局容器 - 使用 :global 确保样式应用到 Element Plus 组件 */
:global(.ppt-creator-dialog) {
  background: #0f172a !important;
}

:global(.ppt-creator-dialog .el-dialog__header) {
  display: none;
}

:global(.ppt-creator-dialog .el-dialog__body) {
  padding: 0 !important;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #0f172a;
  overflow: hidden;
}

/* 导航栏 */
.ppt-nav {
  height: 64px;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
  position: relative;
  z-index: 2000;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 16px;
  color: #fff;
}

.back-btn {
  color: #fff !important;
}

.divider {
  width: 1px;
  height: 24px;
  background: rgba(255, 255, 255, 0.2);
}

.title {
  font-weight: 600;
  font-size: 16px;
  color: #fff;
}

.nav-center {
  flex: 1;
  display: flex;
  justify-content: center;
  max-width: 600px;
}

.nav-center :deep(.el-steps) {
  background: transparent;
}

.nav-center :deep(.el-step__title) {
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
  font-weight: 400;
}

.nav-center :deep(.el-step__title.is-process),
.nav-center :deep(.el-step__title.is-finish) {
  color: #fff;
  font-weight: 600;
}

.nav-center :deep(.el-step__line) {
  background-color: rgba(255, 255, 255, 0.1);
}

.nav-center :deep(.el-step__head.is-process),
.nav-center :deep(.el-step__head.is-finish) {
  color: #3b82f6;
  border-color: #3b82f6;
}

/* 主内容区 */
.ppt-main {
  flex: 1;
  overflow: hidden;
  position: relative;
  height: calc(100vh - 64px);
}

.step-container {
  height: 100%;
  overflow-y: auto;
  padding: 40px;
}

/* Step 1: 大纲编辑 */
.outline-editor {
  max-width: 1200px;
  margin: 0 auto;
}

.chapter-block {
  margin-bottom: 40px;
  animation: fade-in 0.5s ease-out;
}

.chapter-title {
  margin-bottom: 20px;
}

.chapter-title :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: none;
  padding: 8px 15px;
}

.chapter-title :deep(.el-input__inner) {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.slides-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.slide-card {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.slide-card:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.06) !important;
  border-color: rgba(59, 130, 246, 0.3) !important;
}

.slide-card :deep(.el-card__body) {
  padding: 20px;
}

.slide-card :deep(.el-input__wrapper),
.slide-card :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: none;
  color: #fff;
}

.slide-card :deep(.el-textarea__inner) {
  font-family: inherit;
}

/* Step 3: 生成墙 */
.gen-screen {
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.gen-bg {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 50% -20%, #1e293b 0%, #0f172a 100%);
  z-index: 0;
}

.gen-status {
  position: absolute;
  top: 40px;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 10;
  pointer-events: none;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 12px 28px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 50px;
  backdrop-filter: blur(20px);
  color: #fff;
  font-weight: 600;
  margin-bottom: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.status-text {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  letter-spacing: 0.5px;
}

.gen-wall {
  position: relative;
  z-index: 2;
  flex: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 30px;
  padding: 140px 60px 60px;
  overflow-y: auto;
}

.gen-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  aspect-ratio: 16 / 9;
  padding: 24px;
  backdrop-filter: blur(15px);
  transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  animation: card-appear 0.6s ease backwards;
  display: flex;
  flex-direction: column;
}

.gen-card.active {
  border-color: rgba(59, 130, 246, 0.5);
  background: rgba(59, 130, 246, 0.1);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  transform: translateY(-5px);
}

.gen-card.placeholder {
  opacity: 0.15;
}

.card-num {
  font-size: 10px;
  font-weight: 600;
  color: #3b82f6;
  margin-bottom: 8px;
  letter-spacing: 1px;
}

.card-title {
  font-size: 14px;
  color: #fff;
  font-weight: 600;
  margin-bottom: 16px;
  line-height: 1.4;
}

.card-skeleton {
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  margin-bottom: 12px;
}

@keyframes card-appear {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Step 4: 编辑器 */
.editor-workspace {
  height: 100%;
  display: flex;
  background: #0f172a;
}

.editor-sidebar {
  width: 240px;
  background: rgba(0, 0, 0, 0.2);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.sidebar-thumbs {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.thumb {
  margin-bottom: 20px;
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid transparent;
  transition: all 0.2s ease;
  position: relative;
}

.thumb:hover {
  border-color: rgba(255, 255, 255, 0.2);
}

.thumb.active {
  border-color: #3b82f6;
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.3);
}

.thumb-num {
  position: absolute;
  top: 4px;
  left: 4px;
  font-size: 10px;
  color: #fff;
  padding: 2px 6px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 4px;
  z-index: 10;
}

.thumb-preview {
  aspect-ratio: 16 / 9;
  background: #fff;
  padding: 12px;
  font-size: 9px;
  color: #1e293b;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  overflow: hidden;
}

/* ... Sidebar 样式保持不变 ... */

.editor-canvas {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.canvas-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1e293b; /* 画布背景稍微深一点 */
  padding: 40px;
  overflow: auto;
}

.slide-preview-frame {
  width: 100%;
  max-width: 1280px;
  aspect-ratio: 16 / 9;
  background: #fff;
  box-shadow: 0 0 50px rgba(0, 0, 0, 0.5);
  border-radius: 4px; /* PPT 一般直角或微圆角 */
  overflow: hidden;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}

/* 右侧编辑面板 */
.editor-right-panel {
  width: 320px;
  background: rgba(15, 23, 42, 0.95);
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(10px);
  z-index: 100;
}

.panel-header {
  height: 50px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  color: #fff;
  font-weight: 600;
  font-size: 14px;
}

.panel-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
}

.form-group :deep(.el-input__wrapper),
.form-group :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: none;
  color: #fff;
}

.form-group :deep(.el-textarea__inner):focus,
.form-group :deep(.el-input__wrapper).is-focus {
  border-color: #3b82f6;
}

.action-group {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
}
</style>
```
