<template>
  <el-dialog
    v-model="visible"
    title="上传自定义模板"
    width="600px"
    @close="handleClose"
  >
    <el-tabs v-model="activeTab">
      <!-- HTML 模板上传 -->
      <el-tab-pane label="上传 HTML 模板" name="html">
        <el-form :model="htmlForm" label-width="100px">
          <el-form-item label="模板名称" required>
            <el-input
              v-model="htmlForm.template_name"
              placeholder="请输入模板名称"
            />
          </el-form-item>

          <el-form-item label="描述">
            <el-input
              v-model="htmlForm.description"
              type="textarea"
              :rows="3"
              placeholder="请输入模板描述"
            />
          </el-form-item>

          <el-form-item label="标签">
            <div class="tags-input">
              <el-tag
                v-for="tag in htmlForm.tags"
                :key="tag"
                closable
                @close="removeTag(tag, 'html')"
                style="margin-right: 8px; margin-bottom: 8px"
              >
                {{ tag }}
              </el-tag>
              <el-input
                v-if="showTagInput"
                ref="tagInput"
                v-model="newTag"
                size="small"
                style="width: 120px"
                @keyup.enter="addTag('html')"
                @blur="addTag('html')"
              />
              <el-button v-else size="small" @click="showTagInput = true">
                + 添加标签
              </el-button>
            </div>
          </el-form-item>

          <el-form-item label="HTML 文件" required>
            <el-upload
              ref="htmlUpload"
              :auto-upload="false"
              :limit="1"
              accept=".html,.htm"
              :on-change="handleHtmlFileChange"
              :file-list="htmlFileList"
            >
              <el-button size="small" type="primary">
                <el-icon><Upload /></el-icon>
                选择文件
              </el-button>
              <template #tip>
                <div class="el-upload__tip">
                  只支持 .html 或 .htm 文件，必须包含必要的占位符
                </div>
              </template>
            </el-upload>
          </el-form-item>

          <el-alert
            title="HTML 模板必须包含以下占位符："
            type="info"
            :closable="false"
            style="margin-bottom: 20px"
          >
            <ul style="margin: 5px 0; padding-left: 20px">
              <li>&#123;&#123; page_title &#125;&#125;</li>
              <li>&#123;&#123; main_heading &#125;&#125;</li>
              <li>&#123;&#123; page_content &#125;&#125;</li>
              <li>&#123;&#123; current_page_number &#125;&#125;</li>
              <li>&#123;&#123; total_page_count &#125;&#125;</li>
            </ul>
          </el-alert>
        </el-form>
      </el-tab-pane>

      <!-- PPTX 模板上传 -->
      <el-tab-pane label="上传 PPTX 模板" name="pptx">
        <el-form :model="pptxForm" label-width="100px">
          <el-form-item label="模板名称" required>
            <el-input
              v-model="pptxForm.template_name"
              placeholder="请输入模板名称"
            />
          </el-form-item>

          <el-form-item label="描述">
            <el-input
              v-model="pptxForm.description"
              type="textarea"
              :rows="3"
              placeholder="请输入模板描述"
            />
          </el-form-item>

          <el-form-item label="标签">
            <div class="tags-input">
              <el-tag
                v-for="tag in pptxForm.tags"
                :key="tag"
                closable
                @close="removeTag(tag, 'pptx')"
                style="margin-right: 8px; margin-bottom: 8px"
              >
                {{ tag }}
              </el-tag>
              <el-input
                v-if="showPptxTagInput"
                ref="pptxTagInput"
                v-model="newPptxTag"
                size="small"
                style="width: 120px"
                @keyup.enter="addTag('pptx')"
                @blur="addTag('pptx')"
              />
              <el-button v-else size="small" @click="showPptxTagInput = true">
                + 添加标签
              </el-button>
            </div>
          </el-form-item>

          <el-form-item label="PPTX 文件" required>
            <el-upload
              ref="pptxUpload"
              :auto-upload="false"
              :limit="1"
              accept=".pptx,.ppt"
              :on-change="handlePptxFileChange"
              :file-list="pptxFileList"
            >
              <el-button size="small" type="primary">
                <el-icon><Upload /></el-icon>
                选择文件
              </el-button>
              <template #tip>
                <div class="el-upload__tip">
                  支持 .pptx 或 .ppt 文件，系统会自动提取样式并转换为 HTML 模板
                </div>
              </template>
            </el-upload>
          </el-form-item>

          <el-alert title="PPTX 转换说明：" type="warning" :closable="false">
            <ul style="margin: 5px 0; padding-left: 20px">
              <li>系统会自动提取背景颜色、文本样式、布局信息</li>
              <li>不支持图片、图表、动画等复杂元素</li>
              <li>建议使用样式简单统一的 PPTX 模板</li>
            </ul>
          </el-alert>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">
          {{ uploading ? "上传中..." : "上传" }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { Upload } from "@element-plus/icons-vue";
import axios from "axios";

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["update:modelValue", "success"]);

const visible = ref(props.modelValue);
const activeTab = ref("html");
const uploading = ref(false);

// HTML 表单
const htmlForm = ref({
  template_name: "",
  description: "",
  tags: [],
});
const htmlFileList = ref([]);
const htmlFile = ref(null);

// PPTX 表单
const pptxForm = ref({
  template_name: "",
  description: "",
  tags: [],
});
const pptxFileList = ref([]);
const pptxFile = ref(null);

// 标签输入
const showTagInput = ref(false);
const showPptxTagInput = ref(false);
const newTag = ref("");
const newPptxTag = ref("");
const tagInput = ref(null);
const pptxTagInput = ref(null);

// 处理 HTML 文件选择
function handleHtmlFileChange(file) {
  htmlFile.value = file.raw;
  htmlFileList.value = [file];
}

// 处理 PPTX 文件选择
function handlePptxFileChange(file) {
  pptxFile.value = file.raw;
  pptxFileList.value = [file];
}

// 添加标签
function addTag(type) {
  const tag = type === "html" ? newTag.value : newPptxTag.value;
  const form = type === "html" ? htmlForm.value : pptxForm.value;

  if (tag && !form.tags.includes(tag)) {
    form.tags.push(tag);
  }

  if (type === "html") {
    newTag.value = "";
    showTagInput.value = false;
  } else {
    newPptxTag.value = "";
    showPptxTagInput.value = false;
  }
}

// 删除标签
function removeTag(tag, type) {
  const form = type === "html" ? htmlForm.value : pptxForm.value;
  const index = form.tags.indexOf(tag);
  if (index > -1) {
    form.tags.splice(index, 1);
  }
}

// 上传模板
async function handleUpload() {
  if (activeTab.value === "html") {
    await uploadHtmlTemplate();
  } else {
    await uploadPptxTemplate();
  }
}

// 上传 HTML 模板
async function uploadHtmlTemplate() {
  if (!htmlForm.value.template_name) {
    ElMessage.error("请输入模板名称");
    return;
  }

  if (!htmlFile.value) {
    ElMessage.error("请选择 HTML 文件");
    return;
  }

  uploading.value = true;

  try {
    const formData = new FormData();
    formData.append("template_name", htmlForm.value.template_name);
    formData.append("description", htmlForm.value.description);
    formData.append("tags", JSON.stringify(htmlForm.value.tags));
    formData.append("html_file", htmlFile.value);

    const response = await axios.post(
      "/api/ppt/templates/upload-html",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );

    ElMessage.success("HTML 模板上传成功！");
    emit("success", response.data);
    handleClose();
  } catch (error) {
    ElMessage.error(
      "上传失败: " + (error.response?.data?.detail || error.message)
    );
  } finally {
    uploading.value = false;
  }
}

// 上传 PPTX 模板
async function uploadPptxTemplate() {
  if (!pptxForm.value.template_name) {
    ElMessage.error("请输入模板名称");
    return;
  }

  if (!pptxFile.value) {
    ElMessage.error("请选择 PPTX 文件");
    return;
  }

  uploading.value = true;

  try {
    const formData = new FormData();
    formData.append("template_name", pptxForm.value.template_name);
    formData.append("description", pptxForm.value.description);
    formData.append("tags", JSON.stringify(pptxForm.value.tags));
    formData.append("pptx_file", pptxFile.value);

    const response = await axios.post(
      "/api/ppt/templates/upload-pptx",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );

    if (response.data.conversion_success) {
      ElMessage.success("PPTX 模板上传并转换成功！");
    } else {
      ElMessage.warning("PPTX 上传成功，但转换失败，已使用基础模板");
    }

    emit("success", response.data);
    handleClose();
  } catch (error) {
    ElMessage.error(
      "上传失败: " + (error.response?.data?.detail || error.message)
    );
  } finally {
    uploading.value = false;
  }
}

// 关闭对话框
function handleClose() {
  visible.value = false;
  emit("update:modelValue", false);

  // 重置表单
  htmlForm.value = {
    template_name: "",
    description: "",
    tags: [],
  };
  pptxForm.value = {
    template_name: "",
    description: "",
    tags: [],
  };
  htmlFileList.value = [];
  pptxFileList.value = [];
  htmlFile.value = null;
  pptxFile.value = null;
}

// 监听 props 变化
watch(
  () => props.modelValue,
  (val) => {
    visible.value = val;
  }
);
</script>

<style scoped>
.tags-input {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-upload__tip) {
  font-size: 12px;
  color: #909399;
  margin-top: 7px;
}
</style>
