<template>
  <div class="code-viewer-container">
    <div class="file-sidebar">
      <div class="sidebar-header">
        <el-input
          v-model="filterText"
          placeholder="搜索文件..."
          prefix-icon="Search"
          clearable
        />
      </div>
      <el-tree
        ref="treeRef"
        :data="fileTree"
        :props="defaultProps"
        @node-click="handleNodeClick"
        highlight-current
        node-key="path"
        :filter-node-method="filterNode"
        class="file-tree"
      >
        <template #default="{ node, data }">
          <span class="custom-tree-node">
            <el-icon
              v-if="data.children && data.children.length > 0"
              class="icon"
              ><Folder
            /></el-icon>
            <el-icon v-else class="icon"><Document /></el-icon>
            <span class="node-label" :title="node.label">{{ node.label }}</span>
          </span>
        </template>
      </el-tree>
    </div>

    <div class="code-content" v-loading="loading">
      <div v-if="currentFile" class="file-header">
        <div class="file-info">
          <el-icon><Document /></el-icon>
          <span class="file-path">{{ currentFile }}</span>
        </div>
        <div class="actions">
          <el-button size="small" @click="copyContent">复制</el-button>
        </div>
      </div>

      <div v-if="content" class="code-body">
        <div class="line-numbers">
          <div v-for="n in lineCount" :key="n" class="line-number">{{ n }}</div>
        </div>
        <pre class="code-text"><code>{{ content }}</code></pre>
      </div>
      <el-empty v-else description="请选择一个文件查看内容" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { Search, Folder, Document } from "@element-plus/icons-vue";
import { deploymentAPI } from "@/api";
import { ElMessage } from "element-plus";

const props = defineProps({
  deploymentId: {
    type: String,
    required: true,
  },
  version: {
    type: Number,
    required: true,
  },
});

const loading = ref(false);
const filterText = ref("");
const treeRef = ref();
const fileTree = ref([]);
const currentFile = ref("");
const content = ref("");

const defaultProps = {
  children: "children",
  label: "label",
};

const lineCount = computed(() => {
  if (!content.value) return 0;
  return content.value.split("\n").length;
});

watch(filterText, (val) => {
  treeRef.value?.filter(val);
});

const filterNode = (value, data) => {
  if (!value) return true;
  return data.label.includes(value);
};

const buildFileTree = (files) => {
  const root = [];

  files.forEach((file) => {
    const parts = file.path.split("/");
    let currentLevel = root;

    parts.forEach((part, index) => {
      const isFile = index === parts.length - 1;
      const existingNode = currentLevel.find((node) => node.label === part);

      if (existingNode) {
        currentLevel = existingNode.children;
      } else {
        const newNode = {
          label: part,
          path: isFile ? file.path : null, // Only files have full path
          children: isFile ? [] : [],
        };
        currentLevel.push(newNode);
        currentLevel = newNode.children;
      }
    });
  });

  return root;
};

const loadFiles = async () => {
  try {
    const files = await deploymentAPI.getVersionFiles(
      props.deploymentId,
      props.version
    );
    fileTree.value = buildFileTree(files);
  } catch (error) {
    ElMessage.error("加载文件列表失败");
  }
};

const handleNodeClick = async (data) => {
  if (!data.path) return; // Directory

  currentFile.value = data.path;
  loading.value = true;

  try {
    const res = await deploymentAPI.getVersionFileContent(
      props.deploymentId,
      props.version,
      data.path
    );
    content.value = res.content;
  } catch (error) {
    console.error("加载文件内容失败:", error);
    ElMessage.error("加载文件内容失败");
    content.value = "";
  } finally {
    loading.value = false;
  }
};

const copyContent = async () => {
  if (!content.value) return;
  try {
    await navigator.clipboard.writeText(content.value);
    ElMessage.success("已复制到剪贴板");
  } catch (err) {
    ElMessage.error("复制失败");
  }
};

onMounted(() => {
  loadFiles();
});
</script>

<style scoped>
.code-viewer-container {
  display: flex;
  height: calc(100vh - 200px); /* Adjust based on dialog height */
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.file-sidebar {
  width: 300px;
  border-right: 1px solid #dcdfe6;
  display: flex;
  flex-direction: column;
  background-color: #f5f7fa;
}

.sidebar-header {
  padding: 10px;
  border-bottom: 1px solid #ebeef5;
}

.file-tree {
  flex: 1;
  overflow-y: auto;
  background-color: transparent;
}

.custom-tree-node {
  display: flex;
  align-items: center;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.icon {
  margin-right: 5px;
  font-size: 16px;
  color: #909399;
}

.node-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

.code-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #ffffff;
}

.file-header {
  height: 40px;
  padding: 0 15px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #ebeef5;
  background-color: #f5f7fa;
}

.file-info {
  display: flex;
  align-items: center;
  font-weight: bold;
  color: #606266;
}

.file-path {
  margin-left: 8px;
}

.code-body {
  flex: 1;
  display: flex;
  overflow: auto;
  position: relative;
}

.line-numbers {
  padding: 10px 0;
  background-color: #f0f0f0;
  border-right: 1px solid #dcdfe6;
  text-align: right;
  color: #999;
  user-select: none;
  min-width: 40px;
}

.line-number {
  padding: 0 8px;
  line-height: 20px;
  font-size: 13px;
  font-family: Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace;
}

.code-text {
  flex: 1;
  margin: 0;
  padding: 10px;
  overflow-x: auto;
  font-family: Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace;
  font-size: 13px;
  line-height: 20px;
  color: #333;
  white-space: pre;
}
</style>
