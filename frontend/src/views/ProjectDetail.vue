<template>
  <div class="project-detail">
    <el-page-header @back="goBack">
      <template #content>
        <span class="project-title">{{ project?.name }}</span>
      </template>
    </el-page-header>

    <el-tabs v-model="activeTab" style="margin-top: 20px">
      <!-- 项目概览 -->
      <el-tab-pane label="项目概览" name="overview">
        <el-card v-if="project">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="项目名称">{{
              project.name
            }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="project.is_active ? 'success' : 'info'">
                {{ project.is_active ? "进行中" : "已结束" }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="团队人数">
              {{ project.team_members.length }} 人
            </el-descriptions-item>
            <el-descriptions-item label="项目所有者">
              {{ getOwnerName() }}
            </el-descriptions-item>
            <el-descriptions-item label="项目经理">
              {{ getProjectManagerName() }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatDateTime(project.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="开始日期">
              {{
                project.start_date ? formatDate(project.start_date) : "未设置"
              }}
            </el-descriptions-item>
            <el-descriptions-item label="结束日期">
              {{ project.end_date ? formatDate(project.end_date) : "未设置" }}
            </el-descriptions-item>
          </el-descriptions>

          <!-- 项目描述单独展示区 -->
          <div class="project-description-section" style="margin-top: 20px">
            <div
              style="
                font-weight: 500;
                font-size: 16px;
                margin-bottom: 12px;
                color: #303133;
                display: flex;
                align-items: center;
              "
            >
              <el-icon style="margin-right: 6px"><Document /></el-icon> 项目描述
            </div>
            <div
              style="
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                line-height: 1.8;
                color: #606266;
                border: 1px solid #ebeef5;
                font-size: 14px;
                white-space: pre-wrap;
              "
            >
              {{ project.description || "暂无描述" }}
            </div>
          </div>
        </el-card>

        <el-row :gutter="20" style="margin-top: 20px" v-if="statistics">
          <el-col :span="8">
            <el-card>
              <el-statistic
                title="任务完成率"
                :value="statistics.task_completion_rate"
                suffix="%"
              />
              <div class="stat-detail">
                {{ statistics.completed_tasks }} /
                {{ statistics.total_tasks }} 已完成
              </div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card>
              <el-statistic
                title="BUG率"
                :value="statistics.bug_rate"
                suffix="%"
              />
              <div class="stat-detail">{{ statistics.total_bugs }} 个BUG</div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card>
              <el-statistic title="开放BUG" :value="statistics.open_bugs" />
              <div class="stat-detail">
                {{ statistics.closed_bugs }} 个已关闭
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 环境配置 -->
      <el-tab-pane label="环境配置" name="environments">
        <el-card>
          <template #header>
            <div
              style="
                display: flex;
                justify-content: space-between;
                align-items: center;
              "
            >
              <span>环境列表</span>
              <el-button type="primary" @click="showAddEnvironmentDialog">
                <el-icon><Plus /></el-icon>
                添加环境
              </el-button>
            </div>
          </template>

          <el-table
            :data="environments"
            stripe
            border
            style="width: 100%"
            :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
          >
            <el-table-column
              prop="name"
              label="环境名称"
              width="180"
              show-overflow-tooltip
            />
            <el-table-column
              prop="url"
              label="登录URL"
              min-width="250"
              show-overflow-tooltip
            />
            <el-table-column prop="username" label="用户名" width="150" />
            <el-table-column label="密码" width="150" align="center">
              <template #default="{ row }">
                <code
                  style="
                    background: #f5f7fa;
                    padding: 2px 8px;
                    border-radius: 3px;
                    font-size: 12px;
                  "
                  >{{ row.password_masked }}</code
                >
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                  {{ row.is_active ? "启用" : "禁用" }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="最后登录" width="170" align="center">
              <template #default="{ row }">
                <div v-if="row.last_login_at">
                  <div style="font-size: 12px; margin-bottom: 4px">
                    {{ formatDateTime(row.last_login_at) }}
                  </div>
                  <el-tag
                    size="small"
                    :type="
                      row.last_login_status === 'success' ? 'success' : 'danger'
                    "
                  >
                    {{ row.last_login_status === "success" ? "成功" : "失败" }}
                  </el-tag>
                </div>
                <span v-else style="color: #999; font-size: 12px">未登录</span>
              </template>
            </el-table-column>
            <el-table-column
              label="操作"
              width="280"
              fixed="right"
              align="center"
            >
              <template #default="{ row }">
                <el-button
                  link
                  type="primary"
                  size="small"
                  @click="loginEnvironment(row.id, false)"
                  :loading="loginLoading[row.id]"
                >
                  登录
                </el-button>
                <el-button
                  link
                  type="success"
                  size="small"
                  @click="loginEnvironment(row.id, true)"
                  :loading="loginLoading[row.id]"
                >
                  刷新Cookie
                </el-button>
                <el-button
                  link
                  type="warning"
                  size="small"
                  @click="showEditEnvironmentDialog(row)"
                >
                  编辑
                </el-button>
                <el-button
                  link
                  type="danger"
                  size="small"
                  @click="deleteEnvironment(row.id)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty
            v-if="environments.length === 0"
            description="暂无环境配置"
          />
        </el-card>
      </el-tab-pane>
      <!-- 会议分析 -->
      <el-tab-pane label="会议分析" name="meetings">
        <el-card>
          <template #header>
            <div
              style="
                display: flex;
                justify-content: space-between;
                align-items: center;
              "
            >
              <span>会议录音/视频分析</span>
              <el-button type="primary" @click="showUploadMeetingDialog">
                <el-icon><Upload /></el-icon>
                上传会议录音/视频
              </el-button>
            </div>
          </template>

          <!-- 会议列表 -->
          <el-table
            :data="meetingList"
            style="width: 100%"
            v-loading="meetingLoading"
          >
            <el-table-column label="会议" min-width="250">
              <template #default="{ row }">
                <div style="display: flex; align-items: center; gap: 10px">
                  <span style="font-size: 24px">{{
                    row.file_type === "video" ? "🎥" : "🎙️"
                  }}</span>
                  <div>
                    <div style="font-weight: 500; margin-bottom: 4px">
                      {{ row.title }}
                    </div>
                    <div style="color: #999; font-size: 12px">
                      {{ row.description || "暂无描述" }}
                    </div>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="150">
              <template #default="{ row }">
                <el-tag :type="getMeetingStatusType(row.status)">
                  <el-icon
                    v-if="isLoadingStatus(row.status)"
                    class="is-loading"
                    style="margin-right: 4px"
                    ><Loading
                  /></el-icon>
                  {{ getMeetingStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="文件大小" width="100">
              <template #default="{ row }">
                {{ formatFileSize(row.file_size) }}
              </template>
            </el-table-column>
            <el-table-column label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="300" fixed="right">
              <template #default="{ row }">
                <!-- 转录完成，显示"查看纪要"按钮 -->
                <el-button
                  v-if="row.status === 'waiting_confirmation'"
                  type="success"
                  size="small"
                  @click="handleViewSummary(row)"
                  :loading="generatingSummary && row.id === generatingSummaryId"
                >
                  查看纪要
                </el-button>
                <!-- 已完成，显示"查看摘要"按钮 -->
                <el-button
                  v-if="row.status === 'completed'"
                  type="success"
                  size="small"
                  @click="viewMeetingSummary(row)"
                >
                  查看摘要
                </el-button>
                <!-- 重新生成纪要按钮 -->
                <el-button
                  v-if="row.status === 'completed'"
                  type="warning"
                  size="small"
                  @click="handleRegenerateSummary(row)"
                  :loading="retryingMeeting && row.id === retryingMeetingId"
                >
                  重新生成纪要
                </el-button>
                <!-- 失败或处理中状态显示重试按钮 -->
                <el-button
                  v-if="row.status === 'failed' || isLoadingStatus(row.status)"
                  type="primary"
                  size="small"
                  plain
                  @click="checkRetryMeeting(row)"
                  :loading="retryingMeeting && row.id === retryingMeetingId"
                >
                  {{ isLoadingStatus(row.status) ? "重启" : "重试" }}
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  @click="deleteMeeting(row.id)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty
            v-if="meetingList.length === 0 && !meetingLoading"
            description="暂无会议记录"
          />
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 添加/编辑环境对话框 -->
    <el-dialog
      v-model="environmentDialogVisible"
      :title="isEditMode ? '编辑环境' : '添加环境'"
      width="600px"
    >
      <el-form
        :model="environmentForm"
        :rules="environmentRules"
        ref="environmentFormRef"
        label-width="100px"
      >
        <el-form-item label="环境名称" prop="name">
          <el-input
            v-model="environmentForm.name"
            placeholder="如：Sandbox Test Environment"
          />
          <div style="color: #999; font-size: 12px; margin-top: 5px">
            登录时会根据此名称自动匹配选择环境
          </div>
        </el-form-item>
        <el-form-item label="登录URL" prop="url">
          <el-input
            v-model="environmentForm.url"
            placeholder="https://example.com/login"
          />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="environmentForm.username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="environmentForm.password"
            type="password"
            show-password
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="environmentForm.description"
            type="textarea"
            :rows="3"
            placeholder="环境说明（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="environmentDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="submitEnvironmentForm"
          :loading="submitting"
        >
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 上传知识库文档对话框 -->
    <el-dialog
      v-model="knowledgeUploadDialogVisible"
      title="上传知识库文档"
      width="600px"
    >
      <el-form
        :model="knowledgeForm"
        :rules="knowledgeRules"
        ref="knowledgeFormRef"
        label-width="100px"
      >
        <el-form-item label="分类" prop="category">
          <el-select
            v-model="knowledgeForm.category"
            placeholder="请选择分类"
            style="width: 100%"
          >
            <el-option label="技术文档" value="技术文档" />
            <el-option label="需求文档" value="需求文档" />
            <el-option label="设计文档" value="设计文档" />
            <el-option label="测试文档" value="测试文档" />
            <el-option label="用户手册" value="用户手册" />
            <el-option label="API文档" value="API文档" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="knowledgeForm.description"
            type="textarea"
            :rows="3"
            placeholder="文档描述（可选）"
          />
        </el-form-item>
        <el-form-item label="选择文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            accept=".md,.doc,.docx,.xls,.xlsx,.pdf,.txt,.png,.jpg,.jpeg,.gif"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div style="color: #999; font-size: 12px; margin-top: 5px">
                支持格式：MD, Word, Excel, PDF, TXT, 图片
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="knowledgeUploadDialogVisible = false"
          >取消</el-button
        >
        <el-button
          type="primary"
          @click="submitKnowledgeUpload"
          :loading="knowledgeUploading"
        >
          上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 查看知识库文档对话框 -->
    <el-dialog
      v-model="knowledgeViewDialogVisible"
      :title="currentKnowledge?.title"
      width="90%"
      :fullscreen="previewFullscreen"
    >
      <div v-if="currentKnowledge">
        <!-- 工具栏 -->
        <div
          style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #e0e0e0;
          "
        >
          <div>
            <el-tag
              :type="getCategoryTagType(currentKnowledge.category)"
              style="margin-right: 10px"
            >
              {{ currentKnowledge.category || "未分类" }}
            </el-tag>
            <el-tag type="info" size="small">
              {{ getFileTypeName(currentKnowledge.file_type) }}
            </el-tag>
            <el-tag type="info" size="small" style="margin-left: 5px">
              {{ formatFileSize(currentKnowledge.file_size) }}
            </el-tag>
            <span style="margin-left: 15px; color: #999; font-size: 14px">
              <el-icon><View /></el-icon> {{ currentKnowledge.views }} 次浏览
            </span>
          </div>
          <div>
            <el-button-group>
              <el-button
                :icon="previewFullscreen ? 'FullScreen' : 'FullScreen'"
                @click="previewFullscreen = !previewFullscreen"
                size="small"
              >
                {{ previewFullscreen ? "退出全屏" : "全屏" }}
              </el-button>
              <el-button
                type="primary"
                @click="downloadKnowledge(currentKnowledge)"
                size="small"
              >
                <el-icon><Download /></el-icon> 下载
              </el-button>
            </el-button-group>
          </div>
        </div>

        <!-- 文档信息 -->
        <el-descriptions
          :column="3"
          border
          size="small"
          style="margin-bottom: 20px"
        >
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(currentKnowledge.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="文件名">
            {{ currentKnowledge.file_name }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="3">
            {{ currentKnowledge.description || "暂无描述" }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 文档预览区域 -->
        <div class="preview-container" v-loading="previewLoading">
          <!-- Markdown预览 -->
          <div
            v-if="
              currentKnowledge.file_type === 'markdown' &&
              currentKnowledge.content
            "
            class="markdown-preview"
            v-html="renderMarkdown(currentKnowledge.content)"
          ></div>

          <!-- PDF预览 -->
          <div
            v-else-if="currentKnowledge.file_type === 'pdf'"
            class="pdf-preview"
          >
            <iframe
              :src="getFilePreviewUrl(currentKnowledge)"
              style="
                width: 100%;
                height: 600px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
              "
            ></iframe>
          </div>

          <!-- 图片预览 -->
          <div
            v-else-if="currentKnowledge.file_type === 'image'"
            class="image-preview"
          >
            <el-image
              :src="getFilePreviewUrl(currentKnowledge)"
              :preview-src-list="[getFilePreviewUrl(currentKnowledge)]"
              fit="contain"
              style="max-width: 100%; max-height: 600px"
            />
          </div>

          <!-- 文本预览 -->
          <div
            v-else-if="
              currentKnowledge.file_type === 'text' && currentKnowledge.content
            "
            class="text-preview"
          >
            <pre>{{ currentKnowledge.content }}</pre>
          </div>

          <!-- Word/Excel预览 - 使用Office Online或显示提取的文本 -->
          <div
            v-else-if="['word', 'excel'].includes(currentKnowledge.file_type)"
            class="office-preview"
          >
            <!-- Office Online预览选项 -->
            <el-alert type="info" :closable="false" style="margin-bottom: 15px">
              <template #title>
                <div
                  style="
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                  "
                >
                  <span
                    >{{
                      currentKnowledge.file_type === "word" ? "Word" : "Excel"
                    }}
                    文档预览</span
                  >
                  <div>
                    <el-button
                      type="success"
                      size="small"
                      @click="previewWithOfficeOnline(currentKnowledge)"
                    >
                      使用Office Online预览
                    </el-button>
                    <el-button
                      type="primary"
                      size="small"
                      @click="downloadKnowledge(currentKnowledge)"
                    >
                      下载查看完整文档
                    </el-button>
                  </div>
                </div>
              </template>
            </el-alert>

            <!-- 文本内容预览 -->
            <div
              v-if="
                currentKnowledge.content && currentKnowledge.content.length > 10
              "
              class="content-preview"
            >
              <h4>📄 文本内容预览</h4>
              <div class="word-content-preview">
                <pre>{{ currentKnowledge.content }}</pre>
              </div>
              <div
                v-if="currentKnowledge.content.length > 5000"
                style="text-align: center; margin-top: 10px; color: #999"
              >
                内容较长，仅显示前5000字符，请下载查看完整文档
              </div>
            </div>
            <div v-else>
              <el-empty description="无法提取文本内容">
                <el-button
                  type="primary"
                  @click="previewWithOfficeOnline(currentKnowledge)"
                >
                  使用Office Online预览
                </el-button>
              </el-empty>
            </div>
          </div>

          <!-- 其他格式 -->
          <div v-else class="other-preview">
            <el-empty description="此文件格式不支持在线预览">
              <el-button
                type="primary"
                @click="downloadKnowledge(currentKnowledge)"
              >
                下载文件
              </el-button>
            </el-empty>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="knowledgeViewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 上传会议对话框 -->
    <el-dialog
      v-model="meetingUploadDialogVisible"
      title="上传会议录音/视频"
      width="600px"
    >
      <el-form
        :model="meetingForm"
        :rules="meetingRules"
        ref="meetingFormRef"
        label-width="100px"
      >
        <el-form-item label="会议标题" prop="title">
          <el-input v-model="meetingForm.title" placeholder="请输入会议标题" />
        </el-form-item>
        <el-form-item label="会议描述">
          <el-input
            v-model="meetingForm.description"
            type="textarea"
            :rows="3"
            placeholder="会议描述（可选）"
          />
        </el-form-item>
        <el-form-item label="选择文件" prop="file">
          <el-upload
            ref="meetingUploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleMeetingFileChange"
            :on-remove="handleMeetingFileRemove"
            accept=".mp4,.avi,.mov,.mkv,.mp3,.wav,.m4a,.aac"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div style="color: #999; font-size: 12px; margin-top: 5px">
                支持格式：视频(MP4, AVI, MOV, MKV)、音频(MP3, WAV, M4A, AAC)
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 上传进度条 -->
        <el-form-item v-if="meetingUploading" label="上传进度">
          <el-progress
            :percentage="uploadProgress"
            :stroke-width="20"
            striped
            striped-animated
            :status="uploadProgress === 100 ? 'success' : ''"
          />
          <div style="font-size: 12px; color: #666; margin-top: 5px">
            {{
              uploadProgress < 100
                ? "正在分片上传，请勿关闭窗口..."
                : "即将上传完成，正在合并分片..."
            }}
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="meetingUploadDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="submitMeetingUpload"
          :loading="meetingUploading"
        >
          上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 确认说话人对话框 -->
    <el-dialog
      v-model="confirmSpeakersDialogVisible"
      title="确认说话人"
      width="800px"
    >
      <div v-if="currentMeeting">
        <el-alert type="info" :closable="false" style="margin-bottom: 20px">
          系统识别到
          {{ currentMeeting.speakers.length }} 位说话人，请为每位说话人确认姓名
        </el-alert>

        <div
          v-for="(speaker, index) in currentMeeting.speakers"
          :key="speaker.speaker_id"
          style="margin-bottom: 20px"
        >
          <el-card>
            <template #header>
              <div
                style="
                  display: flex;
                  justify-content: space-between;
                  align-items: center;
                "
              >
                <span>说话人 {{ index + 1 }}</span>
                <span style="color: #999; font-size: 12px">
                  {{ speaker.start_time.toFixed(1) }}s -
                  {{ speaker.end_time.toFixed(1) }}s
                </span>
              </div>
            </template>

            <div style="margin-bottom: 15px">
              <audio
                v-if="speaker.audio_segment_path"
                controls
                style="width: 100%"
              >
                <source :src="getSpeakerAudioUrl(speaker)" type="audio/wav" />
              </audio>
            </div>

            <div
              v-if="speaker.text"
              style="
                background: #f5f5f5;
                padding: 10px;
                border-radius: 4px;
                margin-bottom: 15px;
              "
            >
              <div style="font-size: 12px; color: #999; margin-bottom: 5px">
                转录文本：
              </div>
              <div style="font-size: 14px">{{ speaker.text }}</div>
            </div>

            <el-input
              v-model="speakerNames[speaker.speaker_id]"
              placeholder="请输入说话人姓名"
              style="width: 300px"
            >
              <template #prepend>姓名</template>
            </el-input>
          </el-card>
        </div>
      </div>
      <template #footer>
        <el-button @click="confirmSpeakersDialogVisible = false"
          >取消</el-button
        >
        <el-button
          type="primary"
          @click="submitSpeakerConfirmation"
          :loading="confirmingSpeakers"
        >
          确认并生成摘要
        </el-button>
      </template>
    </el-dialog>

    <!-- 查看会议摘要对话框 -->
    <el-dialog
      v-model="meetingSummaryDialogVisible"
      :title="currentMeeting?.title + ' - 会议摘要'"
      width="90%"
      :fullscreen="summaryFullscreen"
    >
      <div v-if="currentMeeting">
        <div
          style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #e0e0e0;
          "
        >
          <div>
            <el-tag type="success">已完成</el-tag>
            <span style="margin-left: 15px; color: #999; font-size: 14px">
              {{ formatDateTime(currentMeeting.updated_at) }}
            </span>
          </div>
          <div>
            <el-button-group>
              <el-button
                @click="summaryFullscreen = !summaryFullscreen"
                size="small"
              >
                {{ summaryFullscreen ? "退出全屏" : "全屏" }}
              </el-button>
              <el-button
                type="primary"
                @click="downloadSummary(currentMeeting)"
                size="small"
              >
                <el-icon><Download /></el-icon> 下载纪要
              </el-button>
            </el-button-group>
          </div>
        </div>

        <!-- 使用智能纪要组件 -->
        <SmartMeetingSummary
          :summary-content="currentMeeting.summary_content || '{}'"
          :loading="false"
          @create-task="handleCreateTaskFromMeeting"
        />
      </div>
      <template #footer>
        <el-button @click="meetingSummaryDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 查看会议详情对话框 -->
    <el-dialog
      v-model="meetingDetailDialogVisible"
      :title="currentMeeting?.title"
      width="800px"
    >
      <div v-if="currentMeeting">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="会议标题">{{
            currentMeeting.title
          }}</el-descriptions-item>
          <el-descriptions-item label="文件类型">
            {{ currentMeeting.file_type === "video" ? "视频" : "音频" }}
          </el-descriptions-item>
          <el-descriptions-item label="文件大小">
            {{ formatFileSize(currentMeeting.file_size) }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getMeetingStatusType(currentMeeting.status)">
              {{ getMeetingStatusText(currentMeeting.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ formatDateTime(currentMeeting.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ currentMeeting.description || "暂无描述" }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="currentMeeting.error_message" style="margin-top: 20px">
          <el-alert
            type="error"
            :title="'处理失败：' + currentMeeting.error_message"
            :closable="false"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="meetingDetailDialogVisible = false">关闭</el-button>
        <el-button
          v-if="
            currentMeeting?.status === 'failed' ||
            (currentMeeting && isLoadingStatus(currentMeeting.status))
          "
          type="primary"
          @click="checkRetryMeeting(currentMeeting)"
          :loading="retryingMeeting && currentMeeting?.id === retryingMeetingId"
        >
          {{
            currentMeeting && isLoadingStatus(currentMeeting.status)
              ? "重启分析"
              : "重新分析"
          }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 创建任务对话框 -->
    <el-dialog v-model="taskDialogVisible" title="创建任务" width="600px">
      <el-form
        :model="taskForm"
        :rules="taskRules"
        ref="taskFormRef"
        label-width="100px"
      >
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="taskForm.title" placeholder="请输入任务标题" />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input
            v-model="taskForm.description"
            type="textarea"
            :rows="4"
            placeholder="任务描述（可选）"
          />
        </el-form-item>
        <el-form-item label="所属项目">
          <el-select disabled :model-value="project?.name" style="width: 100%">
            <el-option :label="project?.name" :value="route.params.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人">
          <el-select
            v-model="taskForm.assigned_to"
            placeholder="选择负责人"
            style="width: 100%"
            clearable
          >
            <el-option
              v-for="user in users.filter((u) =>
                project?.team_members.includes(u.id)
              )"
              :key="user.id"
              :label="`${user.full_name} (${user.username})`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="协助人">
          <el-select
            v-model="taskForm.collaborators"
            placeholder="选择协助人（可多选）"
            style="width: 100%"
            multiple
            clearable
          >
            <el-option
              v-for="user in users.filter((u) =>
                project?.team_members.includes(u.id)
              )"
              :key="user.id"
              :label="`${user.full_name} (${user.username})`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-radio-group v-model="taskForm.priority">
            <el-radio label="low">低</el-radio>
            <el-radio label="medium">中</el-radio>
            <el-radio label="high">高</el-radio>
            <el-radio label="urgent">紧急</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="预估工时">
          <el-input-number
            v-model="taskForm.estimated_hours"
            :min="0"
            :step="0.5"
            placeholder="0"
          />
          <span style="margin-left: 10px">小时</span>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker
            v-model="taskForm.due_date"
            type="datetime"
            placeholder="选择日期时间"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="submitTaskForm"
          :loading="creatingTask"
        >
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- PPT 创作中心 (全屏工作台) -->
    <el-dialog
      v-model="pptOutlineDialogVisible"
      :title="null"
      fullscreen
      class="ppt-workspace-dialog"
      :show-close="false"
    >
      <div class="ppt-workspace-container">
        <!-- 顶部导航栏 -->
        <div class="workspace-header">
          <div class="header-left">
            <el-button link @click="pptOutlineDialogVisible = false">
              <el-icon><ArrowLeft /></el-icon> 返回
            </el-button>
            <div class="vertical-divider"></div>
            <span class="workspace-title">{{ currentPPTDraft.title }}</span>
          </div>

          <div class="header-steps">
            <div
              class="step-item"
              :class="{
                active: pptCurrentStep === 1,
                done: pptCurrentStep > 1,
              }"
            >
              <span class="step-num">1</span>
              <span class="step-text">内容大纲</span>
            </div>
            <div class="step-line"></div>
            <div
              class="step-item"
              :class="{
                active: pptCurrentStep === 2,
                done: pptCurrentStep > 2,
              }"
            >
              <span class="step-num">2</span>
              <span class="step-text">风格选择</span>
            </div>
            <div class="step-line"></div>
            <div
              class="step-item"
              :class="{ active: pptCurrentStep === 3 || pptCurrentStep === 4 }"
            >
              <span class="step-num">3</span>
              <span class="step-text">生成预览</span>
            </div>
          </div>

          <div class="header-right">
            <template v-if="pptCurrentStep === 1">
              <el-button
                type="primary"
                @click="pptCurrentStep = 2"
                class="premium-btn"
              >
                下一步：选择风格 <el-icon><ArrowRight /></el-icon>
              </el-button>
            </template>
            <template v-else-if="pptCurrentStep === 2">
              <el-button @click="pptCurrentStep = 1">上一步</el-button>
              <el-button
                type="primary"
                @click="generatePPTFinal"
                :loading="pptGenerating"
                class="premium-btn"
              >
                开始生成 PPT
              </el-button>
            </template>
            <template v-else-if="pptCurrentStep === 4">
              <el-button
                type="success"
                @click="downloadLastPPT"
                class="premium-btn"
              >
                <el-icon><Download /></el-icon> 下载 PPTX
              </el-button>
            </template>
          </div>
        </div>

        <!-- 步骤 1：内容大纲精修 -->
        <div v-if="pptCurrentStep === 1" class="step-content outline-editor">
          <div class="editor-sidebar">
            <el-button
              type="primary"
              plain
              block
              class="add-section-btn"
              @click="addChapter"
            >
              <el-icon><Plus /></el-icon> 添加新章节
            </el-button>
            <div class="sidebar-nav">
              <div class="nav-section-title">报告结构</div>
              <div
                v-for="(chapter, cIdx) in currentPPTDraft.chapters"
                :key="cIdx"
                class="nav-chapter-item"
              >
                <div class="chapter-label">第 {{ cIdx + 1 }} 章节</div>
                <div class="chapter-content">
                  {{ chapter.title || "未命名" }}
                </div>
              </div>
            </div>
          </div>

          <div class="editor-workspace">
            <div class="outline-scroller">
              <!-- 封面页 -->
              <div class="outline-block cover-block">
                <div class="block-label">封面</div>
                <div class="block-content">
                  <el-input
                    v-model="currentPPTDraft.title"
                    placeholder="PPT 主标题"
                    class="main-title-input"
                  />
                  <el-input
                    placeholder="副标题/汇报人"
                    class="sub-title-input"
                  />
                </div>
              </div>

              <!-- 目录页 -->
              <div class="outline-block catalog-block">
                <div class="block-label">目录</div>
                <div class="catalog-preview">
                  <div
                    v-for="(ch, idx) in currentPPTDraft.chapters"
                    :key="idx"
                    class="catalog-item"
                  >
                    0{{ idx + 1 }} {{ ch.title }}
                  </div>
                </div>
              </div>

              <!-- 章节循环 -->
              <div
                v-for="(chapter, cIdx) in currentPPTDraft.chapters"
                :key="cIdx"
                class="chapter-wrapper"
              >
                <div class="chapter-header-edit">
                  <div class="chapter-num">CHAPTER 0{{ cIdx + 1 }}</div>
                  <el-input
                    v-model="chapter.title"
                    placeholder="章节标题"
                    class="chapter-title-input"
                  />
                  <el-button link type="danger" @click="removeChapter(cIdx)"
                    ><el-icon><Delete /></el-icon
                  ></el-button>
                </div>

                <div class="slides-container">
                  <div
                    v-for="(slide, sIdx) in chapter.slides"
                    :key="sIdx"
                    class="slide-item-card"
                  >
                    <div class="slide-card-header">
                      <span class="slide-index">P{{ sIdx + 1 }}</span>
                      <el-button link @click="removeSlideInChapter(cIdx, sIdx)"
                        ><el-icon><Close /></el-icon
                      ></el-button>
                    </div>
                    <div class="slide-editor-fields">
                      <el-input
                        v-model="slide.title"
                        placeholder="幻灯片标题"
                        class="slide-title-input"
                      />
                      <div class="field-label">内容要点</div>
                      <el-input
                        type="textarea"
                        v-model="slide.content_raw"
                        placeholder="每行一条要点..."
                        :rows="4"
                        class="slide-content-input"
                      />
                      <div class="field-label">演讲脚本 (Speech Script)</div>
                      <el-input
                        type="textarea"
                        v-model="slide.notes"
                        placeholder="AI 生成的演讲词..."
                        :rows="2"
                        class="slide-script-input"
                      />
                      <div class="field-label">AI 配图建议 (Visual Prompt)</div>
                      <el-input
                        v-model="slide.image_description"
                        placeholder="描述需要的画面..."
                        size="small"
                        class="slide-visual-input"
                      >
                        <template #prefix
                          ><el-icon><Picture /></el-icon
                        ></template>
                      </el-input>
                    </div>
                  </div>
                  <div
                    class="slide-item-card add-card"
                    @click="addSlideToChapter(cIdx)"
                  >
                    <el-icon><Plus /></el-icon>
                    <span>添加幻灯片</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 步骤 2：选择模板 -->
        <div
          v-if="pptCurrentStep === 2"
          class="step-content template-selector-wrapper"
        >
          <EnhancedTemplateSelector
            v-model="selectedTemplateId"
            @select="onTemplateSelect"
          />
        </div>

        <!-- 步骤 3：生成中 (LandPPT 沉浸式生成墙) -->
        <div
          v-if="pptCurrentStep === 3"
          class="step-content generating-screen"
          style="position: relative; min-height: 600px; padding: 0"
        >
          <div class="aurora-bg"></div>

          <!-- 生成展示墙 -->
          <div class="generation-preview-wall">
            <!-- 封面预演 -->
            <div
              class="gen-card-mini"
              :class="{ active: currentPPTDraft.slides.length === 0 }"
            >
              <div class="card-title-skeleton" style="width: 80%"></div>
              <div class="card-body-skeleton" style="width: 40%"></div>
              <div
                class="scanning-radar"
                v-if="currentPPTDraft.slides.length === 0"
              ></div>
              <div
                v-else
                style="
                  color: rgba(255, 255, 255, 0.7);
                  font-size: 12px;
                  font-weight: bold;
                "
              >
                {{ currentPPTDraft.title }}
              </div>
            </div>

            <!-- 内容页预演 -->
            <div
              v-for="(slide, idx) in currentPPTDraft.slides"
              :key="idx"
              class="gen-card-mini active"
            >
              <div style="font-size: 10px; color: #3b82f6; margin-bottom: 8px">
                Slide {{ idx + 1 }}
              </div>
              <div
                style="
                  font-size: 11px;
                  color: #fff;
                  font-weight: 500;
                  margin-bottom: 12px;
                  white-space: nowrap;
                  overflow: hidden;
                  text-overflow: ellipsis;
                "
              >
                {{ slide.title }}
              </div>
              <div
                class="card-body-skeleton"
                v-for="n in 3"
                :key="n"
                :style="{ width: 80 - n * 10 + '%' }"
              ></div>
              <div
                class="scanning-radar"
                v-if="idx === currentPPTDraft.slides.length - 1"
              ></div>
            </div>

            <!-- 待生成占位符 -->
            <div
              v-for="n in Math.max(0, 8 - currentPPTDraft.slides.length)"
              :key="'pos' + n"
              class="gen-card-mini"
            >
              <div class="card-title-skeleton"></div>
              <div class="card-body-skeleton" style="width: 60%"></div>
              <div class="card-body-skeleton" style="width: 40%"></div>
            </div>
          </div>

          <!-- 悬浮进度提示 -->
          <div class="generation-overlay-content">
            <div class="status-badge-flow">
              <el-icon class="is-loading" style="margin-right: 12px"
                ><Loading
              /></el-icon>
              <span>正在通过 AI 深度创作演示文稿...</span>
            </div>
            <div style="font-size: 14px; opacity: 0.7; letter-spacing: 1px">
              正在处理第 {{ currentPPTDraft.slides.length + 1 }} 页 ·
              {{ pptTheme }} 风格系统已激活
            </div>
          </div>
        </div>

        <!-- 步骤 4：生成完成预览 (LandPPT 沉浸式编辑器) -->
        <div
          v-if="pptCurrentStep === 4"
          class="step-content ppt-editor-workspace"
        >
          <div class="editor-aurora-bg"></div>

          <!-- 磨砂玻璃顶部工具栏 -->
          <div
            class="editor-glass-toolbar"
            style="
              position: relative;
              z-index: 10;
              padding: 10px 20px;
              display: flex;
              justify-content: space-between;
              align-items: center;
              background: rgba(255, 255, 255, 0.05);
              backdrop-filter: blur(10px);
              border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            "
          >
            <div
              style="
                color: #fff;
                font-size: 14px;
                display: flex;
                align-items: center;
              "
            >
              <el-icon color="#4ade80" style="margin-right: 8px"
                ><CircleCheckFilled
              /></el-icon>
              <span>{{ currentPPTDraft.title }} - 编辑模式</span>
            </div>
            <div class="editor-actions-top">
              <el-button-group>
                <el-button
                  size="small"
                  type="primary"
                  plain
                  @click="pptAIChatVisible = !pptAIChatVisible"
                >
                  <el-icon><MagicStick /></el-icon> AI 辅助
                </el-button>
                <el-button size="small" type="success" @click="downloadLastPPT">
                  <el-icon><Download /></el-icon> 下载 PPTX
                </el-button>
              </el-button-group>
            </div>
          </div>

          <div class="editor-layout-main">
            <div class="editor-actions-top">
              <el-button
                size="small"
                type="primary"
                link
                @click="togglePPTPresentation"
                ><el-icon><Monitor /></el-icon> AI 演示</el-button
              >
              <el-button
                size="small"
                type="primary"
                link
                @click="pptFormatDrawerVisible = true"
                ><el-icon><Brush /></el-icon> 格式设置</el-button
              >
              <el-button size="small" type="primary" @click="downloadLastPPT"
                ><el-icon><Download /></el-icon> 下载 PPTX</el-button
              >
            </div>
          </div>

          <!-- 提示信息 -->
          <el-alert
            v-if="selectedTemplateId"
            title="您正在使用专业设计模板"
            type="success"
            :closable="false"
            show-icon
            style="margin: 0 0 15px 0"
          >
            <template #default>
              当前网页预览仅供校对内容，系统已为您应用
              <strong>{{
                selectedTemplate
                  ? selectedTemplate.template_name
                  : selectedTemplateId
              }}</strong>
              模板的高级视觉效果（排版、背景、字体等）。 <br />请点击右上角
              <strong>"下载 PPTX"</strong> 查看最终完美效果。
            </template>
          </el-alert>

          <div class="editor-layout-main">
            <!-- 左侧：胶片序列 (Filmstrip) -->
            <div class="editor-filmstrip">
              <div class="filmstrip-header">
                <el-button size="small" type="primary" block @click="addPPTCard"
                  ><el-icon><Plus /></el-icon> 添加卡片</el-button
                >
              </div>
              <div class="filmstrip-list">
                <!-- 封面缩略图 -->
                <div
                  class="thumb-item"
                  :class="{ active: selectedSlideIndex === -1 }"
                  @click="selectedSlideIndex = -1"
                >
                  <div class="thumb-num">1</div>
                  <div
                    class="thumb-canvas cover-thumb"
                    :style="{
                      background:
                        previewStyle.background ||
                        pptThemes.find((t) => t.id === pptTheme)?.color,
                      color: previewStyle.titleColor,
                    }"
                  >
                    <div class="thumb-title-mini">
                      {{ currentPPTDraft.title }}
                    </div>
                  </div>
                </div>
                <!-- 内容页缩略图 -->
                <div
                  v-for="(slide, idx) in currentPPTDraft.slides"
                  :key="idx"
                  class="thumb-item"
                  :class="{ active: selectedSlideIndex === idx }"
                  @click="selectedSlideIndex = idx"
                >
                  <div class="thumb-num">{{ idx + 2 }}</div>
                  <div
                    class="thumb-canvas slide-thumb"
                    :style="{
                      background: previewStyle.background,
                      color: previewStyle.textColor,
                      borderTop: `3px solid ${
                        previewStyle.titleColor ||
                        pptThemes.find((t) => t.id === pptTheme)?.color
                      }`,
                    }"
                  >
                    <div class="thumb-title-mini-content">
                      {{ slide.title }}
                    </div>
                    <div
                      class="thumb-content-layout"
                      :class="`mini-layout-${slide.layout || 'split'}`"
                    >
                      <template v-if="(slide.layout || 'split') === 'split'">
                        <div class="layout-left">
                          <div class="mini-line"></div>
                          <div class="mini-line"></div>
                        </div>
                        <div class="layout-right"></div>
                      </template>
                      <template v-else-if="slide.layout === 'full'">
                        <div class="layout-full-bg"></div>
                      </template>
                      <template v-else-if="slide.layout === 'triple'">
                        <div class="layout-triple-dots">
                          <div class="dot"></div>
                          <div class="dot"></div>
                          <div class="dot"></div>
                        </div>
                      </template>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 中间：主画布 -->
            <div class="editor-canvas-area">
              <!-- 画布工具栏 -->
              <div class="canvas-toolbar">
                <div class="tool-group">
                  <el-button
                    circle
                    size="small"
                    :type="pptAIChatVisible ? 'primary' : ''"
                    @click="pptAIChatVisible = !pptAIChatVisible"
                  >
                    <el-icon><ChatDotRound /></el-icon>
                  </el-button>
                  <el-button circle size="small" @click="undoPPTAction">
                    <el-icon><Back /></el-icon>
                  </el-button>
                  <el-button
                    circle
                    size="small"
                    class="rotate-icon"
                    @click="refreshPPTCanvas"
                  >
                    <el-icon><RefreshRight /></el-icon>
                  </el-button>
                </div>
                <div class="divider"></div>
                <div class="tool-group">
                  <el-button
                    size="small"
                    link
                    @click="ElMessage.info('拖拽文字到画布以添加内容')"
                  >
                    <el-icon><Type /></el-icon> 文字
                  </el-button>
                  <el-button
                    size="small"
                    link
                    @click="ElMessage.info('从素材库拖拽图片或使用 AI 换图')"
                  >
                    <el-icon><Picture /></el-icon> 图片
                  </el-button>
                  <el-button
                    size="small"
                    link
                    @click="ElMessage.info('选择高级图表或智能组件')"
                  >
                    <el-icon><Grid /></el-icon> 组件
                  </el-button>
                </div>
                <div class="divider"></div>
                <div class="tool-group">
                  <el-slider
                    size="small"
                    v-model="selectedSlideIndex"
                    :max="currentPPTDraft.slides.length"
                    style="width: 100px; margin: 0 10px"
                  />
                  <span class="zoom-text">97%</span>
                </div>
              </div>

              <!-- 幻灯片内容画布 -->
              <div class="canvas-viewport">
                <div class="ppt-page-container" :class="pptTheme">
                  <template v-if="selectedSlideIndex === -1">
                    <!-- 封面展示 -->
                    <div
                      class="ppt-cover-view"
                      :style="{
                        background:
                          previewStyle.background ||
                          pptThemes.find((t) => t.id === pptTheme)?.color,
                        color: previewStyle.titleColor,
                        fontFamily: previewStyle.fontFamily,
                      }"
                    >
                      <div class="cover-content">
                        <h1 class="canvas-main-title">
                          {{ currentPPTDraft.title }}
                        </h1>
                        <p class="canvas-sub-title">
                          汇报人：{{ currentUser?.full_name || "AI 助手" }}
                        </p>
                      </div>
                    </div>
                  </template>
                  <template v-else>
                    <!-- 内容页展示 (支持多布局渲染) -->
                    <div
                      class="ppt-content-view"
                      :style="{
                        background: previewStyle.background,
                        fontFamily: previewStyle.fontFamily,
                      }"
                      :class="`layout-${
                        currentPPTDraft.slides[selectedSlideIndex]?.layout ||
                        'split'
                      }`"
                    >
                      <!-- 1. Split 布局 (左字右图) -->
                      <template
                        v-if="
                          (currentPPTDraft.slides[selectedSlideIndex]?.layout ||
                            'split') === 'split'
                        "
                      >
                        <div
                          class="view-header"
                          :style="{
                            borderLeft: `6px solid ${
                              previewStyle.titleColor ||
                              pptThemes.find((t) => t.id === pptTheme)?.color
                            }`,
                          }"
                        >
                          <input
                            v-model="
                              currentPPTDraft.slides[selectedSlideIndex].title
                            "
                            class="canvas-inline-input title"
                            placeholder="输入标题..."
                            :style="{ color: previewStyle.titleColor }"
                          />
                        </div>
                        <div class="view-body">
                          <div class="view-text">
                            <div
                              v-for="(p, i) in currentPPTDraft.slides[
                                selectedSlideIndex
                              ].content"
                              :key="i"
                              class="bullet-edit-row"
                            >
                              <span class="bullet-dot">•</span>
                              <textarea
                                v-model="
                                  currentPPTDraft.slides[selectedSlideIndex]
                                    .content[i]
                                "
                                class="canvas-inline-input content-p"
                                rows="1"
                                :style="{ color: previewStyle.textColor }"
                                v-autosize
                              ></textarea>
                            </div>
                          </div>
                          <div class="view-visual">
                            <div class="image-wrapper-rich">
                              <img
                                :src="`https://source.unsplash.com/featured/800x600?${
                                  currentPPTDraft.slides[selectedSlideIndex]
                                    ?.image_description || 'business'
                                }`"
                                class="canvas-live-image"
                              />
                              <div class="img-badge">AI 推荐素材</div>
                            </div>
                          </div>
                        </div>
                      </template>

                      <!-- 2. Full 布局 (全图背景) -->
                      <template
                        v-else-if="
                          currentPPTDraft.slides[selectedSlideIndex]?.layout ===
                          'full'
                        "
                      >
                        <div class="full-bleed-container">
                          <img
                            :src="`https://source.unsplash.com/featured/1200x800?${
                              currentPPTDraft.slides[selectedSlideIndex]
                                ?.image_description || 'abstract'
                            }`"
                            class="full-image-bg"
                          />
                          <div class="full-overlay">
                            <h1 class="full-title">
                              <input
                                v-model="
                                  currentPPTDraft.slides[selectedSlideIndex]
                                    .title
                                "
                                class="canvas-inline-input title light-text"
                              />
                            </h1>
                            <div class="full-points">
                              <span
                                v-for="(p, i) in currentPPTDraft.slides[
                                  selectedSlideIndex
                                ]?.content"
                                :key="i"
                              >
                                <input
                                  v-model="
                                    currentPPTDraft.slides[selectedSlideIndex]
                                      .content[i]
                                  "
                                  class="canvas-inline-input content-p light-text"
                                />
                              </span>
                            </div>
                          </div>
                        </div>
                      </template>

                      <!-- 3. Triple 布局 (三列并排 - 毛玻璃效果) -->
                      <template
                        v-else-if="
                          currentPPTDraft.slides[selectedSlideIndex]?.layout ===
                          'triple'
                        "
                      >
                        <div
                          class="view-header centered"
                          :style="{
                            color: pptThemes.find((t) => t.id === pptTheme)
                              ?.color,
                          }"
                        >
                          <input
                            v-model="
                              currentPPTDraft.slides[selectedSlideIndex].title
                            "
                            class="canvas-inline-input title centered"
                          />
                        </div>
                        <div class="triple-grid glass-style">
                          <div
                            v-for="(p, i) in currentPPTDraft.slides[
                              selectedSlideIndex
                            ]?.content.slice(0, 3)"
                            :key="i"
                            class="triple-card-glass"
                          >
                            <div class="card-icon">
                              <el-icon><CircleCheck /></el-icon>
                            </div>
                            <div class="card-text">
                              <textarea
                                v-model="
                                  currentPPTDraft.slides[selectedSlideIndex]
                                    .content[i]
                                "
                                class="canvas-inline-input content-p centered"
                                rows="2"
                              ></textarea>
                            </div>
                          </div>
                        </div>
                      </template>

                      <!-- 4. Infographic 布局 (左右图文对等) -->
                      <template
                        v-else-if="
                          currentPPTDraft.slides[selectedSlideIndex]?.layout ===
                          'infographic'
                        "
                      >
                        <div class="infographic-container">
                          <div class="info-visual-side">
                            <img
                              :src="`https://source.unsplash.com/featured/800x800?${
                                currentPPTDraft.slides[selectedSlideIndex]
                                  ?.image_description || 'illustration'
                              }`"
                              class="info-img"
                            />
                          </div>
                          <div class="info-content-side">
                            <h2 class="title-modern">
                              <input
                                v-model="
                                  currentPPTDraft.slides[selectedSlideIndex]
                                    .title
                                "
                                class="canvas-inline-input"
                              />
                            </h2>
                            <div class="info-points">
                              <div
                                v-for="(p, i) in currentPPTDraft.slides[
                                  selectedSlideIndex
                                ]?.content"
                                :key="i"
                                class="info-row"
                              >
                                <el-icon color="#3b82f6"
                                  ><MagicStick
                                /></el-icon>
                                <input
                                  v-model="
                                    currentPPTDraft.slides[selectedSlideIndex]
                                      .content[i]
                                  "
                                  class="canvas-inline-input"
                                />
                              </div>
                            </div>
                          </div>
                        </div>
                      </template>

                      <!-- 5. Big Number 布局 (核心数字大字报) -->
                      <template
                        v-else-if="
                          currentPPTDraft.slides[selectedSlideIndex]?.layout ===
                          'big_number'
                        "
                      >
                        <div class="big-number-container">
                          <div class="bn-title">
                            <input
                              v-model="
                                currentPPTDraft.slides[selectedSlideIndex].title
                              "
                              class="canvas-inline-input centered"
                            />
                          </div>
                          <div class="bn-main-box glass-accent">
                            <div class="bn-number">
                              <input
                                v-model="
                                  currentPPTDraft.slides[selectedSlideIndex]
                                    .content[0]
                                "
                                class="canvas-inline-input bn-input"
                              />
                            </div>
                            <p class="bn-subtext">关键指标数据</p>
                          </div>
                        </div>
                      </template>
                    </div>
                  </template>

                  <!-- 演讲备注悬浮按钮 -->
                  <div class="notes-fab">
                    <el-button
                      type="primary"
                      size="small"
                      round
                      @click="
                        ElMessage.info(
                          '演讲备注：' +
                            (currentPPTDraft.slides[selectedSlideIndex]
                              ?.notes || '暂无备注')
                        )
                      "
                    >
                      <el-icon><Reading /></el-icon> 演讲备注
                    </el-button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 右侧：AI 灵感对话挂件 -->
            <div v-show="pptAIChatVisible" class="editor-ai-chat-sidebar">
              <div class="chat-header">
                <span>AI 灵感助理</span>
                <el-button link @click="pptAIChatVisible = false"
                  ><el-icon><Close /></el-icon
                ></el-button>
              </div>
              <div class="chat-messages-flow">
                <div
                  v-for="(msg, idx) in pptChatHistory"
                  :key="idx"
                  class="chat-bubble"
                  :class="msg.role"
                >
                  <div class="bubble-avatar" v-if="msg.role === 'assistant'">
                    <el-icon><MagicStick /></el-icon>
                  </div>
                  <div class="bubble-content">{{ msg.content }}</div>
                </div>
              </div>
              <div class="chat-input-area">
                <el-input
                  v-model="pptChatMessage"
                  placeholder="问问 AI 如何美化这一页..."
                  size="small"
                  @keyup.enter="sendPPTChat"
                >
                  <template #append>
                    <el-button @click="sendPPTChat"
                      ><el-icon><Promotion /></el-icon
                    ></el-button>
                  </template>
                </el-input>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- PPT 格式设置抽屉 -->
    <el-drawer
      v-model="pptFormatDrawerVisible"
      title="画布格式设置"
      size="320px"
      append-to-body
    >
      <div class="format-settings-panel">
        <div class="setting-section">
          <h4>全局主题</h4>
          <div class="theme-mini-grid">
            <div
              v-for="t in pptThemes"
              :key="t.id"
              class="theme-mini-card"
              :class="{ active: pptTheme === t.id }"
              @click="pptTheme = t.id"
            >
              <div class="mini-color" :style="{ background: t.color }"></div>
              <span>{{ t.name }}</span>
            </div>
          </div>
        </div>

        <div class="setting-section" v-if="selectedSlideIndex >= 0">
          <h4>分卡片布局</h4>
          <div class="layout-selection">
            <el-radio-group
              v-model="currentPPTDraft.slides[selectedSlideIndex].layout"
              size="small"
            >
              <el-radio-button label="split">侧边</el-radio-button>
              <el-radio-button label="full">沉浸</el-radio-button>
              <el-radio-button label="triple">矩阵</el-radio-button>
              <el-radio-button label="infographic">图解</el-radio-button>
              <el-radio-button label="big_number">数字</el-radio-button>
            </el-radio-group>
          </div>
        </div>

        <div class="setting-section" v-if="selectedSlideIndex >= 0">
          <h4>AI 视觉 Prompt</h4>
          <el-input
            type="textarea"
            v-model="
              currentPPTDraft.slides[selectedSlideIndex].image_description
            "
            placeholder="描述您期望的画面内容..."
            :rows="3"
            @change="refreshPPTCanvas"
          />
        </div>
      </div>
      <template #footer>
        <el-button type="primary" block @click="pptFormatDrawerVisible = false"
          >应用修改</el-button
        >
      </template>
    </el-drawer>

    <!-- PPT 演示全屏遮罩 -->
    <div
      v-if="pptPresentationMode"
      class="presentation-mode-fullscreen"
      @keyup.esc="pptPresentationMode = false"
      tabindex="0"
    >
      <div class="presentation-controls">
        <el-button
          circle
          @click="selectedSlideIndex = Math.max(-1, selectedSlideIndex - 1)"
          ><el-icon><ArrowLeft /></el-icon
        ></el-button>
        <span class="page-indicator"
          >{{ selectedSlideIndex + 2 }} /
          {{ currentPPTDraft.slides.length + 1 }}</span
        >
        <el-button
          circle
          @click="
            selectedSlideIndex = Math.min(
              currentPPTDraft.slides.length - 1,
              selectedSlideIndex + 1
            )
          "
          ><el-icon><ArrowRight /></el-icon
        ></el-button>
        <el-button circle type="danger" @click="pptPresentationMode = false"
          ><el-icon><Close /></el-icon
        ></el-button>
      </div>
      <div class="presentation-viewport">
        <div
          class="ppt-page-container"
          :class="pptTheme"
          style="width: 80vw; aspect-ratio: 16/9; transform: scale(1.1)"
        >
          <!-- 渲染逻辑与预览一致，已自动同步 -->
          <template v-if="selectedSlideIndex === -1">
            <div
              class="ppt-cover-view"
              :style="{
                background: pptThemes.find((t) => t.id === pptTheme)?.color,
              }"
            >
              <h1 class="canvas-main-title">{{ currentPPTDraft.title }}</h1>
            </div>
          </template>
          <template v-else>
            <div
              class="ppt-content-view"
              :class="`layout-${
                currentPPTDraft.slides[selectedSlideIndex]?.layout || 'split'
              }`"
            >
              <!-- 复用预览逻辑 -->
              <div class="view-header">
                {{ currentPPTDraft.slides[selectedSlideIndex]?.title }}
              </div>
              <div class="view-body">
                <ul>
                  <li
                    v-for="(p, i) in currentPPTDraft.slides[selectedSlideIndex]
                      ?.content"
                    :key="i"
                  >
                    {{ p }}
                  </li>
                </ul>
                <div
                  class="view-visual"
                  v-if="
                    currentPPTDraft.slides[selectedSlideIndex]
                      ?.image_description
                  "
                >
                  <img
                    :src="`https://source.unsplash.com/featured/1200x800?${currentPPTDraft.slides[selectedSlideIndex]?.image_description}`"
                    class="canvas-live-image"
                  />
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 新的 PPT 创作对话框 -->
    <PPTCreatorDialog
      v-model="pptOutlineDialogVisible"
      :draft="currentPPTDraft"
      :preview-style="previewStyle"
      @generate="generatePPTFinal"
      @download="downloadLastPPT"
      @close="pptOutlineDialogVisible = false"
    >
      <template #template-selector>
        <EnhancedTemplateSelector
          v-model="selectedTemplateId"
          @select="onTemplateSelect"
        />
      </template>
    </PPTCreatorDialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, onUnmounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { projectAPI, statisticsAPI, userAPI, environmentAPI } from "@/api";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Plus,
  Upload,
  Search,
  View,
  Download,
  Document,
  Loading,
  Tools,
  Folder,
  Promotion,
  ArrowDown,
  Reading,
  List,
  Monitor,
  Rank,
  Delete,
  Setting,
  MoreFilled,
  ChatDotRound,
  FolderChecked,
  CircleCheckFilled,
  ArrowLeft,
  ArrowRight,
  MagicStick,
  Check,
  Close,
  Brush,
  Cpu,
  Aim,
  Sunny,
  CircleCheck,
  Picture,
  Back,
  RefreshRight,
  Edit,
  Grid,
} from "@element-plus/icons-vue";
import dayjs from "dayjs";
import axios from "axios";
import { marked } from "marked";
import SmartMeetingSummary from "@/components/SmartMeetingSummary.vue";
import EnhancedTemplateSelector from "@/components/EnhancedTemplateSelector.vue";
import PPTCreatorDialog from "@/components/PPTCreatorDialog.vue";

const route = useRoute();
const router = useRouter();
const project = ref(null);
const statistics = ref(null);
const users = ref([]);
const activeTab = ref("overview");
const environments = ref([]);
const environmentDialogVisible = ref(false);
const isEditMode = ref(false);
const currentEditId = ref(null);
const submitting = ref(false);
const loginLoading = reactive({});
const environmentFormRef = ref(null);

// 知识库相关状态
const knowledgeList = ref([]);
const knowledgeLoading = ref(false);
const knowledgeSearchKeyword = ref("");
const knowledgeCategory = ref("");
const knowledgeFileType = ref("");
const knowledgeCategories = ref([]);
const knowledgeStats = ref(null);
const knowledgeUploadDialogVisible = ref(false);
const knowledgeViewDialogVisible = ref(false);
const currentKnowledge = ref(null);
const knowledgeUploading = ref(false);
const knowledgeFormRef = ref(null);
const uploadRef = ref(null);
const selectedFile = ref(null);
const previewLoading = ref(false);
const previewFullscreen = ref(false);

// 会议分析相关状态
const meetingList = ref([]);
const meetingLoading = ref(false);
const meetingUploadDialogVisible = ref(false);
const confirmSpeakersDialogVisible = ref(false);
const meetingSummaryDialogVisible = ref(false);
const meetingDetailDialogVisible = ref(false);
const currentMeeting = ref(null);
const meetingUploading = ref(false);
const uploadProgress = ref(0);
const confirmingSpeakers = ref(false);
const summaryFullscreen = ref(false);
const meetingFormRef = ref(null);
const meetingUploadRef = ref(null);
const selectedMeetingFile = ref(null);
const speakerNames = reactive({});
const retryingMeeting = ref(false);
const retryingMeetingId = ref(null);
const generatingSummary = ref(false);
const generatingSummaryId = ref(null);

// PPT 创作相关状态 (升级为多步骤工作流)
const pptOutlineDialogVisible = ref(false);
const pptSuccessDialogVisible = ref(false);
const pptCurrentStep = ref(1); // 1: 大纲, 2: 风格, 3: 生成中, 4: 完成
const currentPPTDraft = ref({
  title: "",
  slides: [],
  project_id: "",
  chapters: [],
});
const lastGeneratedPPT = ref({ file_url: "", filename: "" });
const pptGenerating = ref(false);
const pptTheme = ref("business_blue");
const pptSavingToKB = ref(false);
const selectedSlideIndex = ref(0);
const pptFormatDrawerVisible = ref(false);
const pptPresentationMode = ref(false);
const pptAIChatVisible = ref(false);

// LandPPT 模板选择
const selectedTemplateId = ref("商务");
const selectedTemplate = ref(null);
const previewStyle = ref({}); // 存储预览样式

// 从 HTML 模板中提取样式
const extractStyleFromTemplate = (html) => {
  if (!html) return {};

  const style = {};

  // 提取背景色
  const bodyMatch = html.match(/body\s*{[^}]*background(-color)?:\s*([^;]+)/i);
  if (bodyMatch) style.background = bodyMatch[2].trim();

  // 提取标题颜色
  const h1Match = html.match(/h1\s*{[^}]*color:\s*([^;]+)/i);
  if (h1Match) style.titleColor = h1Match[1].trim();

  // 提取正文颜色
  const bodyColorMatch = html.match(/body\s*{[^}]*color:\s*([^;]+)/i);
  if (bodyColorMatch) style.textColor = bodyColorMatch[1].trim();

  // 提取字体
  const fontMatch = html.match(/font-family:\s*['"]?([^;'"]+)['"]?/i);
  if (fontMatch) style.fontFamily = fontMatch[1].trim();

  console.log("提取的样式:", style);
  return style;
};

const pptChatMessage = ref("");
const pptChatHistory = ref([
  {
    role: "assistant",
    content:
      "您好！我是您的 AI 幻灯片灵感助理。您可以让我帮您：\n1. 润色当前页面的文案\n2. 扩写内容要点\n3. 搜索更契合的视觉素材",
  },
]);

const sendPPTChat = () => {
  if (!pptChatMessage.value.trim()) return;
  pptChatHistory.value.push({ role: "user", content: pptChatMessage.value });
  pptChatMessage.value = "";
  // 模拟 AI 回复
  setTimeout(() => {
    pptChatHistory.value.push({
      role: "assistant",
      content:
        "正在思考如何优化当前页... ✨ 已为您调整了描述词的深度与排版平衡感。",
    });
  }, 1000);
};

const addPPTCard = () => {
  const newSlide = {
    title: "新幻灯片",
    content: ["点击此处编辑内容要点"],
    notes: "AI 生成的演讲词...",
    image_description: "business meeting",
    layout: "split",
  };
  currentPPTDraft.value.slides.splice(
    selectedSlideIndex.value + 1,
    0,
    newSlide
  );
  selectedSlideIndex.value++;
  ElMessage.success("已添加新幻灯片卡片");
};

const togglePPTPresentation = async () => {
  pptPresentationMode.value = !pptPresentationMode.value;
  if (pptPresentationMode.value) {
    ElMessage.info({ message: "进入 AI 演示模式 (Esc 退出)", duration: 2000 });
    // 等待 DOM 渲染后自动聚焦以支持 Esc 键
    setTimeout(() => {
      const el = document.querySelector(".presentation-mode-fullscreen");
      if (el) el.focus();
    }, 120);
  }
};

const undoPPTAction = () => {
  ElMessage({ message: "操作已撤回", type: "info", plain: true });
};

const redoPPTAction = () => {
  ElMessage({ message: "操作已重做", type: "info", plain: true });
};

const refreshPPTCanvas = () => {
  ElMessage({ message: "画布已重载最新素材", type: "success", plain: true });
};

// PPT 模板列表（从 API 加载）
const pptThemes = ref([
  // 默认内置主题（作为后备）
  {
    id: "business_blue",
    name: "商务蓝",
    color: "#1e3a8a",
    industry: "通用",
    style: "商务",
    icon: "Monitor",
    is_builtin: true,
  },
  {
    id: "tech_dark",
    name: "科技黑",
    color: "#0f172a",
    industry: "互联网",
    style: "科技",
    icon: "Cpu",
    is_builtin: true,
  },
  {
    id: "clean_white",
    name: "极简白",
    color: "#ffffff",
    industry: "行政",
    style: "简约",
    icon: "Document",
    is_builtin: true,
  },
  {
    id: "vibrant_orange",
    name: "活力橙",
    color: "#f97316",
    industry: "创意",
    style: "时尚",
    icon: "Brush",
    is_builtin: true,
  },
  {
    id: "nature_green",
    name: "生态绿",
    color: "#15803d",
    industry: "制造",
    style: "清新",
    icon: "Aim",
    is_builtin: true,
  },
  {
    id: "warm_red",
    name: "中国红",
    color: "#dc2626",
    industry: "政务",
    style: "国风",
    icon: "Sunny",
    is_builtin: true,
  },
]);

// 加载 PPT 模板列表
const loadPPTTemplates = async () => {
  try {
    console.log("[PPT] 开始加载模板列表...");
    const token = localStorage.getItem("token");
    const res = await axios.get("/api/ppt-templates/", {
      headers: { Authorization: `Bearer ${token}` },
    });

    console.log("[PPT] API 响应:", res.data);

    if (res.data && res.data.length > 0) {
      // 将上传的模板添加到列表中
      const uploadedTemplates = res.data.map((t) => ({
        id: t.id,
        name: t.name,
        color: "#3b82f6", // 默认颜色
        industry: t.category || "自定义",
        style: "模板",
        icon: "Document",
        is_builtin: false,
        total_slides: t.total_slides,
        template_id: t.id,
      }));

      console.log("[PPT] 上传的模板:", uploadedTemplates);

      // 合并内置主题和上传的模板
      pptThemes.value = [...pptThemes.value, ...uploadedTemplates];
      console.log(`[PPT] 加载了 ${uploadedTemplates.length} 个自定义模板`);
      console.log("[PPT] 最终模板列表:", pptThemes.value);
    }
  } catch (e) {
    console.error("[PPT] 加载模板列表失败:", e);
    console.error("[PPT] 错误详情:", e.response?.data);
  }
};

// 任务创建相关
const taskDialogVisible = ref(false);
const taskForm = reactive({
  title: "",
  description: "",
  assigned_to: "",
  collaborators: [],
  priority: "medium",
  estimated_hours: 0,
  due_date: "",
});
const taskFormRef = ref(null);
const taskRules = {
  title: [{ required: true, message: "请输入任务标题", trigger: "blur" }],
  priority: [{ required: true, message: "请选择优先级", trigger: "change" }],
};
const creatingTask = ref(false);

// AI助手相关
const resourceTab = ref("knowledge");
const knowledgeSearchText = ref("");
const resourceDrawerVisible = ref(false); // 资源选择抽屉控制
const activeResourceTab = ref("knowledge"); // 资源抽屉里的Tab
const chatSessions = ref([
  { id: 1, title: "新会话", messages: [], timestamp: new Date() },
]); // 会话列表
const currentSessionId = ref(1); // 当前选中的会话ID
const selectedResources = reactive({
  knowledge: [],
  meetings: [],
});
const selectedResourcesData = reactive({
  knowledge: [],
  meetings: [],
});
// chatMessages 改为计算属性或者通过 watch currentSessionId 更新
// 为了兼容旧代码，我们保留chatMessages作为当前会话的消息引用，并在切换时更新它
const chatMessages = ref([]);
const userInput = ref("");
const aiThinking = ref(false);
const chatMessagesRef = ref(null);
const currentUser = ref(null);
const editingMessageId = ref(null); // Which user message is being edited
const editedMessageContent = ref(""); // Content of the message being edited

const environmentForm = reactive({
  name: "",
  url: "",
  username: "",
  password: "",
  description: "",
});

const knowledgeForm = reactive({
  category: "",
  description: "",
  file: null,
});

const meetingForm = reactive({
  title: "",
  description: "",
  file: null,
});

const environmentRules = {
  name: [{ required: true, message: "请输入环境名称", trigger: "blur" }],
  url: [
    { required: true, message: "请输入登录URL", trigger: "blur" },
    { type: "url", message: "请输入有效的URL", trigger: "blur" },
  ],
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

const knowledgeRules = {
  category: [{ required: true, message: "请选择分类", trigger: "change" }],
  file: [{ required: true, message: "请选择文件", trigger: "change" }],
};

const meetingRules = {
  title: [{ required: true, message: "请输入会议标题", trigger: "blur" }],
  file: [{ required: true, message: "请选择文件", trigger: "change" }],
};

// 计算属性
const filteredKnowledgeList = computed(() => {
  if (!knowledgeSearchText.value) {
    return knowledgeList.value;
  }
  const searchLower = knowledgeSearchText.value.toLowerCase();
  return knowledgeList.value.filter(
    (doc) =>
      doc.title.toLowerCase().includes(searchLower) ||
      (doc.description &&
        doc.description.toLowerCase().includes(searchLower)) ||
      (doc.category && doc.category.toLowerCase().includes(searchLower))
  );
});

const completedMeetings = computed(() => {
  return meetingList.value.filter(
    (m) => m.status === "completed" && m.summary_content
  );
});

const selectedResourcesCount = computed(() => {
  return selectedResources.knowledge.length + selectedResources.meetings.length;
});

const fetchProject = async () => {
  try {
    project.value = await projectAPI.getProject(route.params.id);
  } catch (error) {
    ElMessage.error("获取项目信息失败");
  }
};

const fetchStatistics = async () => {
  try {
    statistics.value = await statisticsAPI.getProjectStatistics(
      route.params.id
    );
  } catch (error) {
    ElMessage.error("获取统计信息失败");
  }
};

const fetchUsers = async () => {
  try {
    users.value = await userAPI.getUsers();
  } catch (error) {
    console.error("获取用户列表失败:", error);
  }
};

const fetchEnvironments = async () => {
  try {
    environments.value = await environmentAPI.getProjectEnvironments(
      route.params.id
    );
  } catch (error) {
    ElMessage.error("获取环境列表失败");
  }
};

const getOwnerName = () => {
  if (!project.value) return "未知";
  const owner = users.value.find((u) => u.id === project.value.owner_id);
  return owner ? `${owner.full_name} (${owner.username})` : "未知";
};

const getProjectManagerName = () => {
  if (!project.value || !project.value.project_manager_id) return "未设置";
  const pm = users.value.find((u) => u.id === project.value.project_manager_id);
  return pm ? `${pm.full_name} (${pm.username})` : "未知";
};

const goBack = () => {
  router.push("/projects");
};

const formatDate = (date) => {
  return dayjs(date).format("YYYY-MM-DD");
};

const formatDateTime = (date) => {
  return dayjs(date).format("YYYY-MM-DD HH:mm:ss");
};

const showAddEnvironmentDialog = () => {
  isEditMode.value = false;
  currentEditId.value = null;
  Object.assign(environmentForm, {
    name: "",
    url: "",
    username: "",
    password: "",
    description: "",
  });
  environmentDialogVisible.value = true;
};

const showEditEnvironmentDialog = (env) => {
  isEditMode.value = true;
  currentEditId.value = env.id;
  Object.assign(environmentForm, {
    name: env.name,
    url: env.url,
    username: env.username,
    password: "", // 密码不回显
    description: env.description || "",
  });
  environmentDialogVisible.value = true;
};

const submitEnvironmentForm = async () => {
  if (!environmentFormRef.value) return;

  await environmentFormRef.value.validate(async (valid) => {
    if (!valid) return;

    submitting.value = true;
    try {
      const data = { ...environmentForm };

      if (isEditMode.value) {
        // 如果密码为空，不更新密码
        if (!data.password) {
          delete data.password;
        }
        await environmentAPI.updateEnvironment(currentEditId.value, data);
        ElMessage.success("环境更新成功");
      } else {
        await environmentAPI.createEnvironment(route.params.id, data);
        ElMessage.success("环境添加成功");
      }

      environmentDialogVisible.value = false;
      await fetchEnvironments();
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || "操作失败");
    } finally {
      submitting.value = false;
    }
  });
};

const deleteEnvironment = async (id) => {
  try {
    await ElMessageBox.confirm("确定要删除此环境配置吗？", "提示", {
      type: "warning",
    });

    await environmentAPI.deleteEnvironment(id);
    ElMessage.success("删除成功");
    await fetchEnvironments();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("删除失败");
    }
  }
};

const loginEnvironment = async (id, forceRefresh) => {
  loginLoading[id] = true;
  try {
    const result = await environmentAPI.loginEnvironment(id, forceRefresh);

    if (result.success) {
      ElMessage.success(result.message || "登录成功");
      await fetchEnvironments();
    } else {
      ElMessage.error(result.message || "登录失败");
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "登录失败");
  } finally {
    loginLoading[id] = false;
  }
};

// ========== 知识库相关函数 ==========

const fetchKnowledgeList = async () => {
  knowledgeLoading.value = true;
  try {
    const params = {
      project_id: route.params.id,
    };
    if (knowledgeSearchKeyword.value) {
      params.keyword = knowledgeSearchKeyword.value;
    }
    if (knowledgeCategory.value) {
      params.category = knowledgeCategory.value;
    }
    if (knowledgeFileType.value) {
      params.file_type = knowledgeFileType.value;
    }

    const token = localStorage.getItem("token");
    const response = await axios.get("/api/knowledge/", {
      params,
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    knowledgeList.value = response.data;
  } catch (error) {
    ElMessage.error("获取知识库列表失败");
  } finally {
    knowledgeLoading.value = false;
  }
};

const fetchKnowledgeCategories = async () => {
  try {
    const token = localStorage.getItem("token");
    const response = await axios.get("/api/knowledge/categories/list", {
      params: { project_id: route.params.id },
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    knowledgeCategories.value = response.data.categories;
  } catch (error) {
    console.error("获取分类列表失败:", error);
  }
};

const fetchKnowledgeStats = async () => {
  try {
    const token = localStorage.getItem("token");
    const response = await axios.get(
      `/api/knowledge/statistics/${route.params.id}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    knowledgeStats.value = response.data;
  } catch (error) {
    console.error("获取统计信息失败:", error);
  }
};

const searchKnowledge = () => {
  fetchKnowledgeList();
};

const showUploadKnowledgeDialog = () => {
  Object.assign(knowledgeForm, {
    category: "",
    description: "",
    file: null,
  });
  selectedFile.value = null;
  knowledgeUploadDialogVisible.value = true;
};

const handleFileChange = (file) => {
  selectedFile.value = file.raw;
  knowledgeForm.file = file.raw;
};

const handleFileRemove = () => {
  selectedFile.value = null;
  knowledgeForm.file = null;
};

const submitKnowledgeUpload = async () => {
  if (!knowledgeFormRef.value) return;

  await knowledgeFormRef.value.validate(async (valid) => {
    if (!valid) return;
    if (!selectedFile.value) {
      ElMessage.error("请选择文件");
      return;
    }

    knowledgeUploading.value = true;
    try {
      const formData = new FormData();
      // 使用文件名作为标题（去掉扩展名）
      const fileName = selectedFile.value.name;
      const title =
        fileName.substring(0, fileName.lastIndexOf(".")) || fileName;

      formData.append("title", title);
      formData.append("project_id", route.params.id);
      formData.append("category", knowledgeForm.category);
      if (knowledgeForm.description)
        formData.append("description", knowledgeForm.description);
      formData.append("file", selectedFile.value);

      const token = localStorage.getItem("token");
      await axios.post("/api/knowledge/", formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data",
        },
      });

      ElMessage.success("上传成功");
      knowledgeUploadDialogVisible.value = false;
      await fetchKnowledgeList();
      await fetchKnowledgeCategories();
      await fetchKnowledgeStats();
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || "上传失败");
    } finally {
      knowledgeUploading.value = false;
    }
  });
};

const viewKnowledge = async (doc) => {
  try {
    const token = localStorage.getItem("token");
    const response = await axios.get(`/api/knowledge/${doc.id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    currentKnowledge.value = response.data;
    knowledgeViewDialogVisible.value = true;
  } catch (error) {
    ElMessage.error("获取文档详情失败");
  }
};

const deleteKnowledge = async (id) => {
  try {
    await ElMessageBox.confirm("确定要删除这个文档吗？", "提示", {
      type: "warning",
    });

    const token = localStorage.getItem("token");
    await axios.delete(`/api/knowledge/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    ElMessage.success("删除成功");
    await fetchKnowledgeList();
    await fetchKnowledgeStats();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("删除失败");
    }
  }
};

const downloadKnowledge = (doc) => {
  // 检查是否是OSS文件
  if (doc.file_path && doc.file_path.startsWith("http")) {
    // 直接打开OSS URL
    window.open(doc.file_path, "_blank");
  } else {
    // 本地文件，使用原有路径
    const token = localStorage.getItem("token");
    window.open(
      `/uploads/knowledge/${route.params.id}/${doc.file_name}?token=${token}`,
      "_blank"
    );
  }
};

const getFileIcon = (fileType) => {
  const icons = {
    markdown: "📝",
    word: "📄",
    excel: "📊",
    pdf: "📕",
    text: "📃",
    image: "🖼️",
    other: "📎",
  };
  return icons[fileType] || "📎";
};

const getFileTypeName = (fileType) => {
  const names = {
    markdown: "Markdown",
    word: "Word文档",
    excel: "Excel表格",
    pdf: "PDF文档",
    text: "文本文件",
    image: "图片",
    other: "其他",
  };
  return names[fileType] || "未知";
};

const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB";
  if (bytes < 1024 * 1024 * 1024)
    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + " GB";
};

// Markdown渲染
const renderMarkdown = (content) => {
  try {
    return marked(content, {
      breaks: true,
      gfm: true,
    });
  } catch (error) {
    console.error("Markdown渲染失败:", error);
    return content;
  }
};

// 获取文件预览URL
const getFilePreviewUrl = (doc) => {
  // 如果是OSS文件，直接返回OSS URL
  if (doc.file_path && doc.file_path.startsWith("http")) {
    return doc.file_path;
  }
  // 本地文件，从file_path中提取文件名
  const pathParts = doc.file_path.split("\\");
  const fileName = pathParts[pathParts.length - 1];
  return `/uploads/knowledge/${doc.project_id}/${fileName}`;
};

// 获取分类标签类型
const getCategoryTagType = (category) => {
  const typeMap = {
    技术文档: "primary",
    需求文档: "success",
    设计文档: "warning",
    测试文档: "danger",
    API文档: "info",
    用户手册: "",
    其他: "info",
  };
  return typeMap[category] || "";
};

// 使用Office Online预览
const previewWithOfficeOnline = (doc) => {
  // 获取文件的完整URL
  const fileUrl = getFilePreviewUrl(doc);

  // 如果不是完整的URL（即本地文件），需要添加域名
  const fullUrl = fileUrl.startsWith("http")
    ? fileUrl
    : window.location.origin + fileUrl;

  const encodedUrl = encodeURIComponent(fullUrl);

  // 使用Microsoft Office Online Viewer
  const officeOnlineUrl = `https://view.officeapps.live.com/op/view.aspx?src=${encodedUrl}`;

  // 在新窗口打开
  window.open(officeOnlineUrl, "_blank");

  ElMessage.info("正在使用Office Online打开文档...");
};
const fetchMeetingList = async () => {
  meetingLoading.value = true;
  try {
    const token = localStorage.getItem("token");
    const response = await axios.get("/api/meetings/", {
      params: { project_id: route.params.id },
      headers: { Authorization: `Bearer ${token}` },
    });
    meetingList.value = response.data;
  } catch (error) {
    ElMessage.error("获取会议列表失败");
  } finally {
    meetingLoading.value = false;
  }
};

const showUploadMeetingDialog = () => {
  Object.assign(meetingForm, {
    title: "",
    description: "",
    file: null,
  });
  selectedMeetingFile.value = null;
  meetingUploadDialogVisible.value = true;
};

const handleMeetingFileChange = (file) => {
  selectedMeetingFile.value = file.raw;
  meetingForm.file = file.raw;
};

const handleMeetingFileRemove = () => {
  selectedMeetingFile.value = null;
  meetingForm.file = null;
};

const submitMeetingUpload = async () => {
  if (!meetingFormRef.value) return;

  await meetingFormRef.value.validate(async (valid) => {
    if (!valid) return;
    if (!selectedMeetingFile.value) {
      ElMessage.error("请选择文件");
      return;
    }

    meetingUploading.value = true;
    uploadProgress.value = 0;

    try {
      const file = selectedMeetingFile.value;
      const CHUNK_SIZE = 2 * 1024 * 1024; // 2MB
      const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
      const uploadId = `${Date.now()}-${Math.random()
        .toString(36)
        .substr(2, 9)}`;
      const token = localStorage.getItem("token");

      for (let i = 0; i < totalChunks; i++) {
        const start = i * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, file.size);
        const chunk = file.slice(start, end);

        const formData = new FormData();
        formData.append("upload_id", uploadId);
        formData.append("chunk_index", i);
        formData.append("chunk", chunk, file.name);

        await axios.post("/api/meetings/upload/chunk", formData, {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "multipart/form-data",
          },
        });

        uploadProgress.value = Math.floor(((i + 1) / totalChunks) * 100);
      }

      // 合并分片
      const mergeData = new FormData();
      mergeData.append("upload_id", uploadId);
      mergeData.append("filename", file.name);
      mergeData.append("title", meetingForm.title);
      mergeData.append("project_id", route.params.id);
      if (meetingForm.description) {
        mergeData.append("description", meetingForm.description);
      }
      mergeData.append("total_chunks", totalChunks);

      await axios.post("/api/meetings/upload/merge", mergeData, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data",
        },
      });

      ElMessage.success("上传成功，正在处理中...");
      meetingUploadDialogVisible.value = false;
      await fetchMeetingList();
      startMeetingPolling();
    } catch (error) {
      console.error("上传进度错误:", error);
      ElMessage.error(error.response?.data?.detail || "上传失败");
    } finally {
      meetingUploading.value = false;
    }
  });
};

const showConfirmSpeakersDialog = async (meeting) => {
  currentMeeting.value = meeting;

  // 初始化说话人姓名
  Object.keys(speakerNames).forEach((key) => delete speakerNames[key]);
  meeting.speakers.forEach((speaker) => {
    speakerNames[speaker.speaker_id] = speaker.speaker_name || "";
  });

  confirmSpeakersDialogVisible.value = true;
};

const getSpeakerAudioUrl = (speaker) => {
  // 构建音频URL
  const pathParts = speaker.audio_segment_path
    ? speaker.audio_segment_path.split("\\")
    : [];
  const fileName =
    pathParts[pathParts.length - 1] || `${speaker.speaker_id}_0.wav`;
  return `/uploads/meetings/${route.params.id}/segments/${fileName}`;
};

const submitSpeakerConfirmation = async () => {
  // 验证所有说话人都有姓名
  const confirmations = currentMeeting.value.speakers.map((speaker) => ({
    speaker_id: speaker.speaker_id,
    speaker_name: speakerNames[speaker.speaker_id],
  }));

  if (confirmations.some((c) => !c.speaker_name)) {
    ElMessage.warning("请为所有说话人输入姓名");
    return;
  }

  confirmingSpeakers.value = true;
  try {
    const token = localStorage.getItem("token");
    await axios.post(
      `/api/meetings/${currentMeeting.value.id}/confirm-speakers`,
      confirmations,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    ElMessage.success("确认成功，正在生成摘要...");
    confirmSpeakersDialogVisible.value = false;
    await fetchMeetingList();

    // 启动定时刷新
    startMeetingPolling();
  } catch (error) {
    ElMessage.error("确认失败");
  } finally {
    confirmingSpeakers.value = false;
  }
};

const getToolName = (tool) => {
  if (typeof tool.function === "string") return tool.function;
  return tool.function?.name || "unknown";
};

const getToolArgs = (tool) => {
  if (tool.args) return tool.args;
  // Handle History format: tool.function.arguments (string)
  if (tool.function?.arguments) {
    try {
      if (typeof tool.function.arguments === "string") {
        return JSON.parse(tool.function.arguments);
      }
      return tool.function.arguments; // Already object
    } catch (e) {
      console.error("Failed to parse tool arguments", e);
      return {};
    }
  }
  return {};
};

const getToolResult = (tool) => {
  if (tool.result) {
    return typeof tool.result === "object" ? tool.result.message : tool.result;
  }
  // Fallback for history items which don't have result stored
  const name = getToolName(tool);
  if (name === "propose_tasks") return "任务已提取";
  if (name === "generate_document") return "文档已生成";
  if (name === "create_tasks") return "任务已创建";
  if (name === "generate_ppt_outline") return "PPT大纲已生成";
  return "已执行";
};

const handleViewSummary = async (meeting) => {
  // 如果已经有摘要，直接查看
  if (meeting.summary_content) {
    viewMeetingSummary(meeting);
    return;
  }

  // 否则，调用API生成智能纪要
  generatingSummary.value = true;
  generatingSummaryId.value = meeting.id;

  try {
    const token = localStorage.getItem("token");
    await axios.post(
      `/api/meetings/${meeting.id}/generate-summary`,
      {},
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    ElMessage.success("正在生成智能纪要，请稍候...");
    await fetchMeetingList();

    // 启动定时刷新，等待生成完成
    startMeetingPolling();

    // 等待一小段时间后自动打开详情对话框，让用户看到进度
    setTimeout(() => {
      viewMeetingDetail(meeting);
    }, 500);
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "生成智能纪要失败");
  } finally {
    generatingSummary.value = false;
    generatingSummaryId.value = null;
  }
};

const viewMeetingSummary = async (meeting) => {
  currentMeeting.value = meeting;
  meetingSummaryDialogVisible.value = true;
};

const downloadSummary = (meeting) => {
  let content = meeting.summary_content;
  let filename = `${meeting.title}_摘要.md`;

  try {
    const data = JSON.parse(meeting.summary_content);

    // 格式化为 Markdown
    let md = `# ${data.meeting_title || meeting.title}\n\n`;

    if (
      data.meeting_date ||
      (data.participants && data.participants.length) ||
      data.duration
    ) {
      md += `## 会议信息\n`;
      if (data.meeting_date) md += `- **日期**: ${data.meeting_date}\n`;
      if (data.participants && data.participants.length)
        md += `- **参会人员**: ${data.participants.join("、")}\n`;
      if (data.duration) md += `- **时长**: ${data.duration}\n`;
      md += `\n`;
    }

    if (data.summary) {
      md += `## 会议概览\n${data.summary}\n\n`;
    }

    if (data.key_points && data.key_points.length) {
      md += `## 核心纪要\n`;
      data.key_points.forEach((point) => {
        md += `### ${point.title}\n${point.content}\n\n`;
      });
    }

    if (data.conclusions && data.conclusions.length) {
      md += `## 关键结论\n`;
      data.conclusions.forEach((con) => {
        md += `- **${con.title}**: ${con.content}\n`;
      });
      md += `\n`;
    }

    if (data.discussion_topics && data.discussion_topics.length) {
      md += `## 讨论主题\n`;
      data.discussion_topics.forEach((topic) => {
        md += `### ${topic.topic}\n${topic.summary}\n`;
        if (topic.decisions && topic.decisions.length) {
          md += `**决策**：\n`;
          topic.decisions.forEach((d) => (md += `- ${d}\n`));
        }
        md += `\n`;
      });
    }

    if (data.action_items && data.action_items.length) {
      md += `## 待办事项\n`;
      data.action_items.forEach((item) => {
        const priority =
          item.priority === "high"
            ? " [高优先级]"
            : item.priority === "low"
            ? " [低优先级]"
            : "";
        md += `- **任务**: ${item.task}${priority}\n`;
        if (item.owner) md += `  - **负责人**: ${item.owner}\n`;
        if (item.deadline) md += `  - **截止日期**: ${item.deadline}\n`;
      });
      md += `\n`;
    }

    if (data.risks && data.risks.length) {
      md += `## 风险与缓解\n`;
      data.risks.forEach((risk) => {
        md += `- **风险**: ${risk.risk}\n`;
        md += `  - **影响**: ${risk.impact}\n`;
        md += `  - **缓解措施**: ${risk.mitigation}\n`;
      });
      md += `\n`;
    }

    if (data.next_steps && data.next_steps.length) {
      md += `## 下一步行动\n`;
      data.next_steps.forEach((step) => {
        md += `- ${step}\n`;
      });
      md += `\n`;
    }

    content = md;
  } catch (e) {
    console.warn("Failed to parse summary JSON, downloading raw content", e);
  }

  // 创建下载链接
  const blob = new Blob([content], { type: "text/markdown" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
};

const checkRetryMeeting = async (meeting) => {
  try {
    await ElMessageBox.confirm(
      "确定要重新分析这个会议吗？这将清除当前的错误状态并重新开始处理。",
      "确认重新分析",
      {
        confirmButtonText: "重新分析",
        cancelButtonText: "取消",
        type: "warning",
      }
    );
    await handleRetryMeeting(meeting);
  } catch (error) {
    // Cancelled
  }
};

const handleRetryMeeting = async (meeting) => {
  retryingMeeting.value = true;
  retryingMeetingId.value = meeting.id;
  try {
    const token = localStorage.getItem("token");
    await axios.post(
      `/api/meetings/${meeting.id}/retry`,
      {},
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    ElMessage.success("已开始重新分析");
    meetingDetailDialogVisible.value = false;
    await fetchMeetingList();
    startMeetingPolling();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "重试失败");
  } finally {
    retryingMeeting.value = false;
    retryingMeetingId.value = null;
  }
};

const handleRegenerateSummary = async (meeting) => {
  try {
    await ElMessageBox.confirm(
      "确定要重新生成智能纪要吗？这将使用已有的转录文本重新调用AI生成新的纪要。",
      "确认重新生成",
      {
        confirmButtonText: "重新生成",
        cancelButtonText: "取消",
        type: "warning",
      }
    );

    retryingMeeting.value = true;
    retryingMeetingId.value = meeting.id;

    try {
      const token = localStorage.getItem("token");
      await axios.post(
        `/api/meetings/${meeting.id}/regenerate-summary`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      ElMessage.success("正在重新生成智能纪要，请稍候...");
      await fetchMeetingList();
      startMeetingPolling();
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || "重新生成失败");
    } finally {
      retryingMeeting.value = false;
      retryingMeetingId.value = null;
    }
  } catch (error) {
    // Cancelled
  }
};

const viewMeetingDetail = async (meeting) => {
  currentMeeting.value = meeting;
  meetingDetailDialogVisible.value = true;
};

const deleteMeeting = async (id) => {
  try {
    await ElMessageBox.confirm("确定要删除这个会议吗？", "提示", {
      type: "warning",
    });

    const token = localStorage.getItem("token");
    await axios.delete(`/api/meetings/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    ElMessage.success("删除成功");
    await fetchMeetingList();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("删除失败");
    }
  }
};

const getMeetingStatusType = (status) => {
  const typeMap = {
    uploading: "info",
    processing: "info",
    speaker_identification: "info",
    waiting_confirmation: "warning",
    generating_summary: "info",
    completed: "success",
    failed: "danger",
  };
  return typeMap[status] || "info";
};

const getMeetingStatusText = (status) => {
  const textMap = {
    uploading: "上传中...",
    processing: "音频提取中...",
    speaker_identification: "AI语音转录中(耗时较长)...",
    waiting_confirmation: "转录完成",
    generating_summary: "AI生成摘要中...",
    completed: "已完成",
    failed: "失败",
  };
  return textMap[status] || status;
};

const isLoadingStatus = (status) => {
  return [
    "uploading",
    "processing",
    "speaker_identification",
    "generating_summary",
  ].includes(status);
};

let meetingPollingTimer = null;

const startMeetingPolling = () => {
  // 清除现有定时器
  if (meetingPollingTimer) {
    clearInterval(meetingPollingTimer);
  }

  // 每5秒刷新一次
  meetingPollingTimer = setInterval(async () => {
    await fetchMeetingList();

    // 如果所有会议都已完成或失败，停止轮询
    const hasProcessing = meetingList.value.some((m) =>
      [
        "uploading",
        "processing",
        "speaker_identification",
        "generating_summary",
      ].includes(m.status)
    );

    if (!hasProcessing) {
      clearInterval(meetingPollingTimer);
      meetingPollingTimer = null;
    }
  }, 5000);
};

// ========== 任务创建相关函数 ==========

// 从会议待办事项创建任务
const handleCreateTaskFromMeeting = (actionItem) => {
  // 重置表单
  Object.assign(taskForm, {
    title: actionItem.task || "",
    description: `来自会议: ${currentMeeting.value?.title}\n\n${
      actionItem.task || ""
    }`,
    assigned_to: "",
    collaborators: [],
    priority: actionItem.priority || "medium",
    estimated_hours: 0,
    due_date: actionItem.deadline || "",
  });

  // 如果有负责人，尝试匹配用户
  if (actionItem.owner) {
    const matchedUser = users.value.find(
      (u) => u.full_name === actionItem.owner || u.username === actionItem.owner
    );
    if (matchedUser) {
      taskForm.assigned_to = matchedUser.id;
    }
  }

  taskDialogVisible.value = true;
};

// 提交任务创建表单
const submitTaskForm = async () => {
  if (!taskFormRef.value) return;

  await taskFormRef.value.validate(async (valid) => {
    if (!valid) return;

    creatingTask.value = true;
    try {
      const token = localStorage.getItem("token");
      await axios.post(
        "/api/tasks/",
        {
          title: taskForm.title,
          description: taskForm.description,
          project_id: route.params.id,
          assigned_to: taskForm.assigned_to || null,
          collaborators: taskForm.collaborators,
          priority: taskForm.priority,
          estimated_hours: taskForm.estimated_hours || null,
          due_date: taskForm.due_date || null,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      ElMessage.success("任务创建成功");
      taskDialogVisible.value = false;

      // 关闭会议摘要对话框
      meetingSummaryDialogVisible.value = false;
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || "创建任务失败");
    } finally {
      creatingTask.value = false;
    }
  });
};

// ========== AI助手相关函数 ==========

// 获取项目会话列表
const fetchSessions = async () => {
  try {
    const token = localStorage.getItem("token");
    const response = await axios.get(
      `/api/landppt/projects/${route.params.id}/sessions`,
      { headers: { Authorization: `Bearer ${token}` } }
    );

    if (response.data && response.data.length > 0) {
      chatSessions.value = response.data.map((s) => ({
        ...s,
        id: s.id,
        messages: [],
        timestamp: s.updated_at || s.created_at,
      }));
      // 自动选中第一个
      await switchSession(chatSessions.value[0].id);
    } else {
      chatSessions.value = [];
      await createNewSession();
    }
  } catch (error) {
    console.error("获取会话列表失败", error);
    // Fallback
    if (chatSessions.value.length === 0) {
      createNewSessionFallback();
    }
  }
};

const createNewSessionFallback = () => {
  const newSession = {
    id: "temp-" + Date.now(),
    title: "新会话",
    messages: [],
    timestamp: new Date(),
  };
  chatSessions.value.unshift(newSession);
  currentSessionId.value = newSession.id;
  chatMessages.value = [];
};

// 创建新会话
const createNewSession = async () => {
  try {
    const token = localStorage.getItem("token");
    const response = await axios.post(
      `/api/landppt/sessions`,
      {
        title: "新会话",
        project_id: route.params.id,
      },
      { headers: { Authorization: `Bearer ${token}` } }
    );

    const newSession = {
      ...response.data,
      messages: [],
      timestamp: response.data.created_at,
    };

    chatSessions.value.unshift(newSession);
    currentSessionId.value = newSession.id;
    chatMessages.value = [];
  } catch (error) {
    console.error("创建会话失败", error);
    createNewSessionFallback();
  }
};

// 切换会话
const switchSession = async (sessionId) => {
  currentSessionId.value = sessionId;
  const session = chatSessions.value.find((s) => s.id === sessionId);

  if (session) {
    // 如果是临时会话，或者已有消息，则直接显示
    if (session.messages && session.messages.length > 0) {
      chatMessages.value = session.messages;
    } else if (!sessionId.toString().startsWith("temp-")) {
      try {
        const token = localStorage.getItem("token");
        const response = await axios.get(
          `/api/landppt/sessions/${sessionId}/messages`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        session.messages = response.data;
        chatMessages.value = session.messages;
      } catch (e) {
        console.error("加载消息失败", e);
        session.messages = [];
        chatMessages.value = [];
      }
    } else {
      chatMessages.value = session.messages || [];
    }
  }
};

const handleSessionCommand = async (command, session) => {
  if (command === "delete") {
    try {
      await ElMessageBox.confirm(
        "确定要删除这个对话吗？该操作不可恢复。",
        "删除确认",
        {
          confirmButtonText: "删除",
          cancelButtonText: "取消",
          type: "warning",
        }
      );

      const token = localStorage.getItem("token");
      if (!session.id.toString().startsWith("temp-")) {
        await axios.delete(`/api/landppt/sessions/${session.id}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
      }

      // 从列表中移除
      chatSessions.value = chatSessions.value.filter(
        (s) => s.id !== session.id
      );

      // 如果删除的是当前会话，切换到其他的
      if (currentSessionId.value === session.id) {
        if (chatSessions.value.length > 0) {
          switchSession(chatSessions.value[0].id);
        } else {
          createNewSession();
        }
      }
      ElMessage.success("会话已删除");
    } catch (e) {
      if (e !== "cancel") console.error(e);
    }
  } else if (command === "rename") {
    try {
      const { value } = await ElMessageBox.prompt(
        "请输入新的会话标题",
        "重命名",
        {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          inputValue: session.title,
          inputValidator: (val) => !!val.trim() || "标题不能为空",
        }
      );

      // 如果不是临时会话，调用API
      if (!session.id.toString().startsWith("temp-")) {
        const token = localStorage.getItem("token");
        await axios.patch(
          `/api/landppt/sessions/${session.id}`,
          { title: value },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }

      session.title = value;
      ElMessage.success("重命名成功");
    } catch (e) {
      if (e !== "cancel") console.error(e);
    }
  }
};

// 切换资源选择
const toggleResource = (type, id, data) => {
  const index = selectedResources[type].indexOf(id);
  if (index > -1) {
    selectedResources[type].splice(index, 1);
    const dataIndex = selectedResourcesData[type].findIndex(
      (item) => item.id === id
    );
    if (dataIndex > -1) {
      selectedResourcesData[type].splice(dataIndex, 1);
    }
  } else {
    selectedResources[type].push(id);
    selectedResourcesData[type].push(data);
  }
};

// 清空选中的资源
const clearSelectedResources = () => {
  selectedResources.knowledge = [];
  selectedResources.meetings = [];
  selectedResourcesData.knowledge = [];
  selectedResourcesData.meetings = [];
};

// 格式化时间
const formatTime = (timestamp) => {
  return dayjs(timestamp).format("HH:mm");
};

// 获取 AI 可用技能
const availableSkills = ref([]);
const currentActiveSkill = ref(null);

const fetchAvailableSkills = async () => {
  try {
    const token = localStorage.getItem("token");
    const response = await axios.get("/api/landppt/skills", {
      headers: { Authorization: `Bearer ${token}` },
    });
    availableSkills.value = response.data;
  } catch (e) {
    console.error("加载技能列表失败", e);
  }
};

// 发送消息 (流式版本)
// 发送消息 (流式版本) - 支持重发
const sendMessage = async (content = null) => {
  // If called as an event handler, the first argument is an Event object
  const messageText =
    typeof content === "string" ? content : userInput.value.trim();

  if (!messageText && selectedResourcesCount.value === 0) {
    return;
  }

  const resources = {
    knowledge: selectedResourcesData.knowledge.map((doc) => ({
      id: doc.id,
      title: doc.title,
      content: doc.content,
      file_type: doc.file_type,
    })),
    meetings: selectedResourcesData.meetings.map((meeting) => ({
      id: meeting.id,
      title: meeting.title,
      summary: meeting.summary_content,
    })),
  };

  // 添加用户消息 (如果是新发送)
  if (typeof content !== "string") {
    chatMessages.value.push({
      role: "user",
      content: messageText || "(引用了资源)",
      timestamp: new Date(),
    });
    userInput.value = "";
  }

  aiThinking.value = true;
  currentActiveSkill.value = null; // 重置当前技能

  // 滚动到底部
  setTimeout(() => {
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight;
    }
  }, 100);

  // 预先创建一个空白的 AI 回复占位
  const aiMessageIndex = chatMessages.value.length;
  chatMessages.value.push({
    role: "assistant",
    content: "",
    timestamp: new Date(),
    is_streaming: true,
  });

  try {
    const token = localStorage.getItem("token");

    // 自动识别可能的 Skill
    if (
      messageText.includes("调研") ||
      messageText.includes("搜索") ||
      messageText.includes("研究")
    ) {
      currentActiveSkill.value = "research";
    } else if (
      messageText.includes("ppt") ||
      messageText.includes("大纲") ||
      messageText.includes("幻灯片")
    ) {
      currentActiveSkill.value = "ppt_design";
    }

    const response = await fetch("/api/landppt/stream-chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        model: "default",
        session_id: currentSessionId.value,
        project_id: route.params.id,
        resources: resources,
        messages: chatMessages.value
          .slice(0, -1)
          .map((m) => ({
            role: m.role,
            content: m.content,
          }))
          .concat([{ role: "user", content: messageText }]),
      }),
    });

    if (!response.ok) throw new Error("Network response was not ok");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let partialData = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      partialData += decoder.decode(value, { stream: true });

      const lines = partialData.split("\n");
      partialData = lines.pop(); // 保留不完整的一行

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const content = line.slice(6).trim();
          if (content === "[DONE]") {
            chatMessages.value[aiMessageIndex].is_streaming = false;
            // 结束后重新拉取消息以获取正式 ID
            setTimeout(async () => {
              const res = await axios.get(
                `/api/landppt/sessions/${currentSessionId.value}/messages`,
                {
                  headers: { Authorization: `Bearer ${token}` },
                }
              );
              chatMessages.value = res.data;
            }, 500);
            break;
          }

          try {
            const data = JSON.parse(content);
            if (data.content) {
              chatMessages.value[aiMessageIndex].content += data.content;
            }
            if (data.error) throw new Error(data.error);
          } catch (e) {
            console.error("解析流数据出错", e);
          }

          // 保持滚动到底部
          if (chatMessagesRef.value) {
            chatMessagesRef.value.scrollTop =
              chatMessagesRef.value.scrollHeight;
          }
        }
      }
    }
  } catch (error) {
    console.error("AI助手响应失败", error);
    ElMessage.error(error.message || "AI助手响应失败");
    chatMessages.value[aiMessageIndex].content =
      "抱歉，我遇到了一些问题，请稍后再试。";
  } finally {
    aiThinking.value = false;
    currentActiveSkill.value = null;
  }
};

// --- 编辑与重新生成功能 ---

const startEdit = (msg) => {
  editingMessageId.value = msg.id;
  editedMessageContent.value = msg.content;
};

const cancelEdit = () => {
  editingMessageId.value = null;
  editedMessageContent.value = "";
};

const saveEdit = async (msg, index) => {
  if (!editedMessageContent.value.trim() || aiThinking.value) return;

  try {
    const token = localStorage.getItem("token");
    // 1. 删除当前消息及之后的所有消息
    await axios.delete(`/api/landppt/messages/${msg.id}?include_self=true`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    // 2. 本地状态同步 (截波至该位置)
    chatMessages.value = chatMessages.value.slice(0, index);

    const newContent = editedMessageContent.value.trim();
    editingMessageId.value = null;

    // 3. 重新作为新消息发送
    await sendMessage(newContent);
  } catch (e) {
    ElMessage.error("更新失败: " + (e.response?.data?.detail || e.message));
  }
};

const regenerate = async (assistantMsg, index) => {
  if (aiThinking.value) return;

  try {
    const token = localStorage.getItem("token");

    // 1. 查找前一个用户消息
    let userMsgIndex = -1;
    for (let i = index - 1; i >= 0; i--) {
      if (chatMessages.value[i].role === "user") {
        userMsgIndex = i;
        break;
      }
    }

    if (userMsgIndex === -1) {
      ElMessage.warning("找不到可重新生成的上下文");
      return;
    }

    const userMsg = chatMessages.value[userMsgIndex];
    const userMsgContent = userMsg.content;

    // 2. 删除用户消息及其之后的所有消息 (从而由 sendMessage 重新插入用户及生成助手回复)
    await axios.delete(
      `/api/landppt/messages/${userMsg.id}?include_self=true`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    // 3. 本地切片
    chatMessages.value = chatMessages.value.slice(0, userMsgIndex);

    // 4. 发送
    await sendMessage(userMsgContent);
  } catch (e) {
    ElMessage.error("重新生成失败: " + (e.response?.data?.detail || e.message));
  }
};

// 辅助函数
const parseToolArgs = (args) => {
  try {
    if (typeof args === "string") return JSON.parse(args);
    return args || {};
  } catch (e) {
    return {};
  }
};

const getPriorityType = (p) => {
  const map = {
    high: "danger",
    medium: "warning",
    low: "info",
    urgent: "danger",
  };
  return map[p] || "info";
};

const getPriorityLabel = (p) => {
  const map = { high: "高", medium: "中", low: "低", urgent: "紧急" };
  return map[p] || p;
};

// 确认创建任务
const creatingTasks = ref(false);
const currentcreatingTool = ref(null);

const confirmCreateTasks = async (tool) => {
  const args = getToolArgs(tool);
  if (!args?.tasks) return;

  creatingTasks.value = true;
  currentcreatingTool.value = tool;

  try {
    const token = localStorage.getItem("token");
    await axios.post(
      "/api/tasks/batch",
      {
        project_id: route.params.id,
        tasks: args.tasks,
      },
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    ElMessage.success(`成功创建 ${args.tasks.length} 个任务`);
    tool.created = true; // 标记

    // 刷新任务列表
    fetchTasks();
  } catch (e) {
    console.error(e);
    ElMessage.error("创建任务失败");
  } finally {
    creatingTasks.value = false;
    currentcreatingTool.value = null;
  }
};

// 识别是否为 PPT 大纲
const isPPTOutline = (content) => {
  if (!content) return false;
  const c = content.toLowerCase();
  // 更加鲁棒的识别：支持任何 Slide N 标记，不仅限于 Slide 1
  const hasSlideMarker = /(?:slide|第)\s*\d+/i.test(c);
  const hasStructureKeywords = /主题|大纲|标题|内容|汇报|总结/i.test(c);
  return hasSlideMarker && hasStructureKeywords;
};

// 解析 Markdown 并打开 PPT 创作器
const parseAndOpenPPT = (markdown) => {
  try {
    const lines = markdown.split("\n");
    let title = "未命名演示文稿";
    const allSlides = [];
    let currentSlide = null;

    // 提取总标题并清洗
    const titleMatch = markdown.match(/(?:PPT 主题|主题|#)\s*[:：]?\s*(.*)/);
    if (titleMatch) title = titleMatch[1].trim().replace(/[#*]/g, "");

    lines.forEach((line) => {
      // 1. 清理加粗和外层空白
      let trimmed = line.trim().replace(/\*\*/g, "");
      if (!trimmed) return;

      // 2. 增强型幻灯片头部识别正则
      // 支持格式：[Slide 1], Slide 1:, # Slide 1, - Slide 1, ## [Slide 1] 等
      const slideMatch = trimmed.match(
        /^[ \t]*[-*+•#\s]*\[?(?:Slide|第|页面)\s*(\d+)[\]\s:：]+(.*)/i
      );

      if (slideMatch) {
        if (currentSlide) allSlides.push(currentSlide);
        currentSlide = {
          title:
            slideMatch[2]
              .replace(/[#*()（）:]/g, "")
              .replace(/封面|标题页/g, "")
              .trim() || `内容页 ${slideMatch[1]}`,
          content: [],
          notes: "",
          image_description: "",
          layout: "split",
        };
      } else if (currentSlide) {
        // 1. 匹配视觉建议/配图建议
        if (
          trimmed.includes("视觉建议") ||
          trimmed.includes("配图") ||
          trimmed.includes("🎨")
        ) {
          currentSlide.image_description = trimmed
            .split(/[:：]/)
            .slice(1)
            .join(":")
            .trim();
        }
        // 2. 匹配演讲备注/核心叙述/讲解
        else if (
          trimmed.includes("核心叙事") ||
          trimmed.includes("脚本") ||
          trimmed.includes("讲解") ||
          trimmed.includes("备注") ||
          trimmed.includes("贴士") ||
          trimmed.toLowerCase().includes("presenter") ||
          trimmed.toLowerCase().includes("notes")
        ) {
          currentSlide.notes = trimmed.split(/[:：]/).slice(1).join(":").trim();
        }
        // 3. 匹配正文列表
        else if (
          trimmed.startsWith("-") ||
          trimmed.startsWith("*") ||
          trimmed.startsWith("•") ||
          trimmed.match(/^\d+[.、\s]/)
        ) {
          // 清除行首的列表符号和特定引导词
          const contentText = trimmed
            .replace(/^[-*•\d.、\s]+/, "")
            .replace(/^(主标题|副标题|汇报人|重点)[:：]\s*/, "")
            .trim();
          if (contentText) currentSlide.content.push(contentText);
        }
        // 4. 处理补充信息
        else {
          // 排除掉明显的标签页标记，其他都作为内容
          if (!trimmed.startsWith("<") && !trimmed.startsWith("```")) {
            const cleanText = trimmed.replace(
              /^(主标题|副标题|汇报人)[:：]\s*/,
              ""
            );
            if (cleanText) currentSlide.content.push(cleanText);
          }
        }
      }
    });
    if (currentSlide) allSlides.push(currentSlide);

    if (allSlides.length === 0) throw new Error("未能识别到有效的幻灯片分页");

    // 智能分章 (每 3 页一章)
    const chapters = [];
    for (let i = 0; i < allSlides.length; i += 3) {
      const chunk = allSlides.slice(i, i + 3);
      const chapterTitles = [
        "项目概览与背景",
        "核心方案与分析",
        "技术落地与执行",
        "总结与展望",
      ];
      chapters.push({
        title:
          chapterTitles[Math.floor(i / 3)] ||
          `内容深化 ${Math.floor(i / 3) + 1}`,
        slides: chunk.map((s) => ({
          ...s,
          content_raw: s.content.join("\n"),
        })),
      });
    }

    // 调用编辑器
    openPPTCreator({
      function: {
        arguments: JSON.stringify({
          title: title,
          chapters: chapters,
          slides: allSlides,
        }),
      },
    });

    ElMessage.success(`成功识别并分章导入 ${allSlides.length} 页内容`);
  } catch (e) {
    console.error("解析 PPT 失败", e);
    ElMessage.error("识别失败，请确保回复包含 Slide 标记");
  }
};

// 处理工具命令
const handleToolCommand = async (command) => {
  if (selectedResourcesCount.value === 0) {
    ElMessage.warning("请先选择知识库文档或会议纪要");
    return;
  }

  let prompt = "";
  switch (command) {
    case "generate-doc":
      prompt =
        "请基于选中的资源生成一份完整的技术文档，包括：1. 概述 2. 详细内容 3. 总结。使用Markdown格式。";
      break;
    case "summarize":
      prompt = "请总结选中资源的核心内容，提取关键信息和要点。";
      break;
    case "extract-tasks":
      prompt =
        "请从选中的资源中提取所有待办事项和任务,任务描述，并按优先级排序。";
      break;
  }

  userInput.value = prompt;
  await sendMessage();
};

// PPT 创作函数
const openPPTCreator = (tool) => {
  const args = getToolArgs(tool);
  if (!args) return;

  // 将原始 slides 数据组织成“章节-页面”结构
  const chapters = [];
  let currentChapter = { title: "概览与开始", slides: [] };

  (args.slides || []).forEach((s, idx) => {
    const slideData = {
      ...s,
      content_raw: (s.content || []).join("\n"),
      notes: s.notes || "",
      image_description: s.image_description || "",
    };

    // 每3页或者遇到特定标题自动分章节（演示用）
    if (idx > 0 && idx % 3 === 0) {
      chapters.push(currentChapter);
      currentChapter = { title: "后续环节", slides: [] };
    }
    currentChapter.slides.push(slideData);
  });
  chapters.push(currentChapter);

  currentPPTDraft.value = {
    title: args.title || "演示文稿",
    project_id: route.params.id,
    chapters: chapters,
    slides: args.slides, // 保留原始引用
  };

  pptCurrentStep.value = 1;
  pptOutlineDialogVisible.value = true;
};

const addChapter = () => {
  currentPPTDraft.value.chapters.push({
    title: "新章节",
    slides: [{ title: "", content: [], content_raw: "" }],
  });
};

const removeChapter = (idx) => {
  currentPPTDraft.value.chapters.splice(idx, 1);
};

const addSlideToChapter = (cIdx) => {
  currentPPTDraft.value.chapters[cIdx].slides.push({
    title: "",
    content: [],
    content_raw: "",
  });
};

const removeSlideInChapter = (cIdx, sIdx) => {
  currentPPTDraft.value.chapters[cIdx].slides.splice(sIdx, 1);
};

// 模板选择回调
const onTemplateSelect = async (template) => {
  selectedTemplate.value = template;
  console.log("选中模板:", template.template_name);

  // 获取模板 HTML 并提取样式
  try {
    const token = localStorage.getItem("token");
    const res = await axios.get(
      `/api/ppt/templates/${template.template_id}/html`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    previewStyle.value = extractStyleFromTemplate(res.data.html);
  } catch (e) {
    console.error("获取模板样式失败:", e);
    // 降级使用默认样式
    previewStyle.value = {
      background: "#ffffff",
      titleColor: "#333333",
      textColor: "#666666",
    };
  }
};

const generatePPTFinal = async () => {
  pptCurrentStep.value = 3; // 进入生成中动画
  pptGenerating.value = true;

  try {
    const token = localStorage.getItem("token");

    // 将章节结构拍平回 slides 发送给后端
    const flatSlides = [];
    currentPPTDraft.value.chapters.forEach((ch) => {
      ch.slides.forEach((s) => {
        flatSlides.push({
          title: s.title,
          content: s.content_raw.split("\n").filter((l) => l.trim()),
          notes: s.notes,
          image_description: s.image_description,
          layout: s.layout,
        });
      });
    });

    // 1. 先保存草稿
    const resDraft = await axios.post(
      "/api/ppt/drafts",
      {
        ...currentPPTDraft.value,
        slides: flatSlides,
      },
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    // 模拟一段“搜索内容中”的 AI 思考感
    await new Promise((resolve) => setTimeout(resolve, 2500));

    // 2. 调用生成接口
    const resFinal = await axios.post(
      `/api/ppt/drafts/${resDraft.data.id}/generate`,
      {},
      {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          save_to_knowledge: false,
          template_id: selectedTemplateId.value, // 使用选中的模板 ID
        },
      }
    );

    lastGeneratedPPT.value = {
      file_url: resFinal.data.file_url,
      filename: resFinal.data.filename,
    };

    pptCurrentStep.value = 4; // 进入完成预览
    if (pptSavingToKB.value) fetchKnowledgeList();
  } catch (e) {
    console.error(e);
    ElMessage.error("生成 PPT 失败，请检查后端服务");
    pptCurrentStep.value = 1;
  } finally {
    pptGenerating.value = false;
  }
};

const downloadLastPPT = () => {
  if (!lastGeneratedPPT.value.file_url) return;
  window.open(lastGeneratedPPT.value.file_url, "_blank");
  pptSuccessDialogVisible.value = false;
};

// 获取当前用户信息
const fetchCurrentUser = async () => {
  try {
    const token = localStorage.getItem("token");
    const response = await axios.get("/api/auth/me", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    currentUser.value = response.data;
  } catch (error) {
    console.error("获取用户信息失败:", error);
  }
};

// 监听activeTab变化，切换到知识库时加载数据
watch(activeTab, (newTab) => {
  if (newTab === "knowledge") {
    fetchKnowledgeList();
    fetchKnowledgeCategories();
    fetchKnowledgeStats();
  } else if (newTab === "meetings") {
    fetchMeetingList();
  } else if (newTab === "ai-assistant") {
    // AI助手需要同时加载知识库和会议数据
    fetchKnowledgeList();
    fetchMeetingList();
  }
});

onMounted(() => {
  console.log("[ProjectDetail] 组件已挂载，开始初始化...");
  fetchUsers();
  fetchProject();
  fetchStatistics();
  fetchEnvironments();
  fetchCurrentUser();
  fetchSessions();
  console.log("[ProjectDetail] 准备加载 PPT 模板...");
  loadPPTTemplates(); // 加载 PPT 模板列表
  console.log("[ProjectDetail] PPT 模板加载已触发");
});
onUnmounted(() => {
  if (meetingPollingTimer) {
    clearInterval(meetingPollingTimer);
  }
});
</script>

<style scoped>
/* =========================================
   LANDPPT 沉浸式工作台架构 (Refactored)
   ========================================= */

/* 1. 全局容器：对话框全屏化处理 */
:deep(.ppt-creator-dialog) {
  background: #0f172a !important;
  border-radius: 0 !important;
  margin: 0 !important;
}

:deep(.ppt-creator-dialog .el-dialog__header) {
  display: none; /* 隐藏原生标题头，使用自定义导航 */
}

:deep(.ppt-creator-dialog .el-dialog__body) {
  padding: 0 !important;
  height: 95vh;
  display: flex;
  flex-direction: column;
}

/* 2. 顶部沉浸式导航栏 */
.ppt-modern-nav {
  height: 60px;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  z-index: 100;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 15px;
  color: #fff;
}
.nav-steps {
  flex: 1;
  display: flex;
  justify-content: center;
}

/* 3. 创作主区域 */
.ppt-main-container {
  flex: 1;
  overflow: hidden;
  position: relative;
  background: #0f172a;
}

/* 4. 生成动态墙 (Step 3) */
.gen-screen-full {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.gen-aurora {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 50% -20%, #1e293b 0%, #0f172a 100%);
  overflow: hidden;
}

.gen-aurora::after {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(
    circle at 10% 20%,
    rgba(59, 130, 246, 0.05) 0%,
    transparent 40%
  );
  animation: aurora-float 15s infinite alternate;
}

.gen-wall-grid {
  position: relative;
  z-index: 2;
  flex: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 30px;
  padding: 120px 60px 60px;
  overflow-y: auto;
}

.gen-status-overlay {
  position: absolute;
  top: 40px;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 10;
}

.gen-card-v2 {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  aspect-ratio: 16 / 9;
  padding: 24px;
  backdrop-filter: blur(15px);
  transition: all 0.5s cubic-bezier(0.2, 1, 0.3, 1);
  animation: card-appear 0.8s ease backwards;
}

.gen-card-v2.active {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  transform: translateY(-5px);
}

/* 5. 专业编辑器阶段 (Step 4) */
.editor-workspace-v2 {
  height: 100%;
  display: flex;
  background: transparent;
}

.editor-sidebar {
  width: 200px;
  background: rgba(0, 0, 0, 0.2);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  flex-direction: column;
}

.editor-canvas-v2 {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  padding: 30px;
  align-items: center;
  justify-content: center;
}

.slide-canvas-main {
  width: 100%;
  max-width: 900px;
  aspect-ratio: 16 / 9;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 30px 60px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  position: relative;
}

/* 6. 辅助动效 */
@keyframes aurora-float {
  0% {
    transform: scale(1);
    opacity: 0.3;
  }
  100% {
    transform: scale(1.2);
    opacity: 0.6;
  }
}

@keyframes card-appear {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.project-detail {
  padding: 20px;
}

.project-title {
  font-size: 20px;
  font-weight: bold;
}

.stat-detail {
  margin-top: 10px;
  color: #666;
  font-size: 14px;
}

/* 预览容器样式 */
.preview-container {
  min-height: 400px;
  background: #fff;
  border-radius: 4px;
}

.markdown-preview {
  padding: 20px;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  line-height: 1.8;
}

.markdown-preview :deep(h1),
.markdown-preview :deep(h2),
.markdown-preview :deep(h3) {
  margin-top: 20px;
  margin-bottom: 10px;
  font-weight: 600;
}

.markdown-preview :deep(code) {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: "Courier New", monospace;
}

.markdown-preview :deep(pre) {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
}

.markdown-preview :deep(img) {
  max-width: 100%;
  height: auto;
}

.text-preview pre {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 4px;
  max-height: 600px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: "Courier New", monospace;
  font-size: 14px;
  line-height: 1.6;
}

.content-preview h4 {
  margin-bottom: 10px;
  color: #333;
  font-size: 16px;
}

.content-preview pre {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  max-height: 500px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: "Courier New", monospace;
  font-size: 13px;
  line-height: 1.6;
}

.word-content-preview {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 20px;
  max-height: 600px;
  overflow-y: auto;
}

.word-content-preview pre {
  background: transparent;
  padding: 0;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei",
    sans-serif;
  font-size: 14px;
  line-height: 1.8;
  color: #333;
}

.image-preview {
  text-align: center;
  padding: 20px;
}

.pdf-preview,
.office-preview,
.other-preview {
  padding: 20px;
}

/* AI助手样式 */
.ai-assistant-container {
  display: flex;
  gap: 20px;
  height: 700px;
}

.sessions-panel {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: white;
  border-right: 1px solid #eee;
}

.new-chat-btn-wrapper {
  padding: 16px;
}

.new-chat-btn {
  width: 100%;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 10px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: #606266;
  position: relative;
}

.session-item:hover {
  background: #f5f7fa;
}

.session-item.active {
  background: #ecf5ff;
  color: #409eff;
}

.session-more-btn {
  margin-left: auto;
  transform: rotate(90deg);
  padding: 4px;
  border-radius: 4px;
  color: #909399;
  display: none;
}

.session-more-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
  color: #333;
}

.session-item:hover .session-more-btn,
.session-item.active .session-more-btn {
  display: block;
}

.session-info {
  min-width: 0;
  flex: 1;
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.session-time {
  font-size: 11px;
  color: #909399;
}

/* Resource Drawer Styles */
.resource-drawer-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.drawer-resource-list {
  padding: 10px;
}

.resource-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.drawer-resource-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: white;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.drawer-resource-item:hover {
  border-color: #c0c4cc;
  transform: translateY(-2px);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.drawer-resource-item.selected {
  border-color: #409eff;
  background: #f0f9eb;
}

.item-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-meta {
  font-size: 12px;
  color: #909399;
}

.item-check {
  margin-left: auto;
}

/* Chat UI Styles */
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 0 0 8px 8px;
  overflow: hidden;
  position: relative;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f0f2f5;
  scroll-behavior: smooth;
}

.chat-welcome {
  text-align: center;
  margin-top: 60px;
  color: #606266;
  animation: fade-in-up 0.6s ease;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 16px;
  animation: bounce 2s infinite;
}

.chat-welcome h3 {
  font-size: 20px;
  margin-bottom: 12px;
  color: #303133;
}

.message-row {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  animation: fade-in-up 0.4s ease;
}

.message-avatar {
  flex-shrink: 0;
  margin-top: 2px;
}

.message-content-wrapper {
  max-width: 85%; /* Increased slightly for better room */
  min-width: 0; /* Critical for flex item wrapping */
  display: flex;
  flex-direction: column;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
  color: #909399;
}

.sender-name {
  font-weight: 500;
  color: #606266;
}

.message-bubble {
  padding: 14px 18px;
  font-size: 14px;
  line-height: 1.6;
  word-wrap: break-word;
  overflow-wrap: break-word; /* Added for better compatibility */
  word-break: break-word; /* Added to prevent overflow */
  position: relative;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

.message-bubble:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

/* AI Assistant Message */
.message-row.assistant .message-bubble {
  background: white;
  border-radius: 2px 16px 16px 16px;
  color: #303133;
  border: 1px solid #e4e7ed;
}

/* User Message */
.message-row.user {
  flex-direction: row-reverse;
}

.message-row.user .message-content-wrapper {
  align-items: flex-end;
}

.message-row.user .message-meta {
  flex-direction: row-reverse;
}

.message-row.user .message-bubble {
  background: linear-gradient(135deg, #409eff 0%, #3a8ee6 100%);
  color: white;
  border-radius: 16px 2px 16px 16px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

/* Tool Calls Styling */
.tool-calls-result {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.tool-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
  background: #f5f7fa;
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 8px;
}

.tool-name {
  font-weight: 600;
  color: #409eff;
}

.tool-result {
  color: #909399;
  font-size: 12px;
}

/* Markdown Styles */
.markdown-body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, sans-serif;
  line-height: 1.75;
  color: #2c3e50;
  word-break: break-word; /* Ensure long words wrap */
  overflow-wrap: break-word;
  max-width: 100%; /* Prevent exceeding parent width */
}

.markdown-body > *:first-child {
  margin-top: 0 !important;
}

.markdown-body > *:last-child {
  margin-bottom: 0 !important;
}

.markdown-body p {
  margin-bottom: 16px;
  text-align: justify;
}

.markdown-body ul,
.markdown-body ol {
  padding-left: 24px;
  margin-bottom: 16px;
}

.markdown-body li {
  margin-bottom: 8px;
  position: relative;
}

.markdown-body ul li::marker {
  color: #409eff;
}

.markdown-body ol li::marker {
  color: #409eff;
  font-weight: 600;
  font-feature-settings: "tnum";
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4 {
  margin-top: 24px;
  margin-bottom: 12px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.4;
}

.markdown-body h3 {
  font-size: 16px;
  border-left: 4px solid #409eff;
  padding-left: 10px;
}

.markdown-body strong {
  color: #1a1a1a;
  font-weight: 700;
  background: linear-gradient(
    120deg,
    transparent 60%,
    rgba(64, 158, 255, 0.2) 60%
  );
}

.markdown-body code {
  background: #f0f2f5;
  padding: 2px 6px;
  border-radius: 4px;
  color: #e6a23c;
  font-family: "Menlo", "Monaco", "Courier New", monospace;
  font-size: 0.9em;
}

.markdown-body pre {
  background: #282c34;
  color: #abb2bf;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 16px 0;
  line-height: 1.5;
}

.markdown-body table {
  display: block;
  width: 100%;
  overflow-x: auto;
  border-collapse: collapse;
  margin-bottom: 16px;
}

.markdown-body blockquote {
  border-left: 4px solid #d9ecff;
  margin: 16px 0;
  color: #606266;
  background: #f5f7fa;
  padding: 12px 16px;
  border-radius: 0 4px 4px 0;
  font-style: italic;
}

/* Edit & Regenerate Styles */
.message-bubble-container {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  max-width: 100%;
}

.message-row.user .message-bubble-container {
  flex-direction: row-reverse;
}

.message-item-utils {
  display: flex;
  flex-direction: column;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
  padding-top: 4px;
}

.message-bubble-container:hover .message-item-utils {
  opacity: 1;
}

.message-edit-area {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 260px;
}

.edit-footer {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
}

.message-row.user .edit-textarea :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.15) !important;
  color: white !important;
  border-color: rgba(255, 255, 255, 0.4) !important;
}

.message-row.user .edit-footer .el-button--link {
  color: rgba(255, 255, 255, 0.8) !important;
}

.message-row.user .edit-footer .el-button--primary {
  background: white !important;
  color: #409eff !important;
  border: none !important;
}

/* Merged and updated message-bubble style */
/* Removing duplicate definition to avoid confusion */

/* Animations */
@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

/* Thinking Bubble */
.thinking-bubble {
  display: flex;
  gap: 8px;
  padding: 16px 20px !important;
  align-items: center;
  min-height: 24px;
}

.typing-dot {
  width: 8px;
  height: 8px;
  background: #c0c4cc;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-dot:nth-child(1) {
  animation-delay: -0.32s;
}
.typing-dot:nth-child(2) {
  animation-delay: -0.16s;
}
.typing-dot:nth-child(3) {
  animation-delay: 0s;
}

@keyframes typing {
  0%,
  80%,
  100% {
    transform: scale(0);
    opacity: 0.6;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* Resources Bar */
.selected-resources-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: #fff;
  border-top: 1px solid #ebeef5;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.02);
  z-index: 10;
}

.selected-count {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #409eff;
  font-size: 14px;
}

.chat-input-area {
  padding: 20px;
  background: white;
  border-top: 1px solid #eee;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.tool-buttons {
  display: flex;
  gap: 8px;
}

.task-proposal-card {
  margin-top: 15px;
  max-width: 100%;
}

.proposal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-top: 1px solid #ebeef5;
  border-bottom: 1px solid #f0f2f5;
  margin-bottom: 4px;
}

.proposal-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  color: #409eff;
  font-size: 14px;
}

.proposal-list {
  padding: 0;
}

.proposal-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 0;
  border-bottom: 1px solid #f5f7fa;
}

.proposal-item:last-child {
  border-bottom: none;
}

.task-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-main-title {
  color: #303133;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.4;
}

.task-desc-text {
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
}

.ppt-creator-layout {
  display: flex;
  height: 75vh;
  background: #f8fafc;
  border-radius: 8px;
  overflow: hidden;
}

.ppt-slides-nav {
  width: 240px;
  background: #fff;
  border-right: 1px solid #e2e8f0;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.nav-header {
  font-weight: 600;
  margin-bottom: 20px;
  color: #1e293b;
}

.slides-list-mini {
  flex: 1;
  overflow-y: auto;
}

.slide-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  margin-bottom: 8px;
  background: #f1f5f9;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.slide-nav-item:hover {
  background: #e2e8f0;
}

.slide-number {
  color: #64748b;
  font-weight: bold;
  font-size: 12px;
}

.slide-nav-title {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #334155;
}

.ppt-editor-main {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
  background: #f8fafc;
}

.ppt-slides-editor-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.slide-edit-card {
  border: 1px solid #e2e8f0;
}

.slide-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-tag {
  background: #6366f1;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.ppt-style-sidebar {
  width: 200px;
  background: #fff;
  border-left: 1px solid #e2e8f0;
  padding: 20px;
}

.section-title {
  font-weight: 600;
  margin-bottom: 15px;
  color: #1e293b;
  font-size: 14px;
}

.theme-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.theme-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  background: #f8fafc;
}

.theme-item:hover {
  background: #f1f5f9;
}

.theme-item.active {
  border-color: #6366f1;
  background: #eff6ff;
}

.theme-color {
  width: 24px;
  height: 24px;
  border-radius: 4px;
}

.theme-label {
  font-size: 13px;
  font-weight: 500;
}

.ppt-footer-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-top: 10px;
}

.ppt-outline-proposal-card {
  background: #f0f7ff;
  border: 1px solid #cce5ff;
  border-radius: 12px;
  padding: 16px;
  margin: 10px 0;
}

.slide-mini-item {
  background: white;
  padding: 10px;
  border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.slide-mini-content {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

/* 高端 PPT 工作台样式 (升级版) */
.ppt-workspace-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f1f5f9;
  color: #1e293b;
}

.workspace-header {
  height: 64px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  z-index: 100;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.vertical-divider {
  width: 1px;
  height: 24px;
  background: #e2e8f0;
}

.workspace-title {
  font-weight: 600;
  font-size: 16px;
  color: #334155;
}

.header-steps {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  opacity: 0.5;
  transition: all 0.3s;
}

.step-item.active {
  opacity: 1;
  font-weight: 600;
  color: #2563eb;
}

.step-item.done {
  opacity: 1;
  color: #10b981;
}

.step-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #64748b;
}

.step-item.active .step-num {
  background: #2563eb;
  color: #fff;
}

.step-item.done .step-num {
  background: #10b981;
  color: #fff;
}

.step-line {
  width: 40px;
  height: 1px;
  background: #e2e8f0;
}

.premium-btn {
  background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
  border: none;
  font-weight: 600;
  padding: 10px 20px;
}

/* 步骤 1：大纲编辑器样式 */
.outline-editor {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.editor-sidebar {
  width: 280px;
  background: #fff;
  border-right: 1px solid #e2e8f0;
  padding: 24px;
  overflow-y: auto;
}

.sidebar-nav {
  margin-top: 32px;
}

.nav-section-title {
  font-size: 12px;
  text-transform: uppercase;
  color: #94a3b8;
  letter-spacing: 0.05em;
  margin-bottom: 16px;
}

.nav-chapter-item {
  margin-bottom: 20px;
}

.chapter-label {
  font-size: 11px;
  color: #3b82f6;
  font-weight: bold;
}

.chapter-content {
  font-size: 13px;
  color: #475569;
}

.editor-workspace {
  flex: 1;
  overflow-y: auto;
  padding: 40px;
}

.outline-scroller {
  max-width: 900px;
  margin: 0 auto;
}

.outline-block {
  background: #fff;
  border-radius: 12px;
  padding: 32px;
  margin-bottom: 24px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.block-label {
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  margin-bottom: 16px;
  display: inline-block;
  padding: 2px 8px;
  background: #f8fafc;
  border-radius: 4px;
}

.main-title-input :deep(input) {
  font-size: 32px;
  font-weight: 800;
  border: none;
  height: 50px;
  padding: 0;
  color: #0f172a;
}

.sub-title-input :deep(input) {
  font-size: 18px;
  border: none;
  padding: 0;
  color: #64748b;
}

.catalog-block {
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
}

.catalog-preview {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.catalog-item {
  font-size: 14px;
  color: #64748b;
  padding: 8px;
}

.chapter-header-edit {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 48px 0 24px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e2e8f0;
}

.chapter-num {
  font-weight: 900;
  font-size: 20px;
  color: #94a3b8;
  font-family: monospace;
}

.chapter-title-input :deep(input) {
  font-size: 24px;
  font-weight: 700;
  border: none;
  background: transparent;
}

.slides-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.slide-item-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e2e8f0;
  transition: transform 0.2s, box-shadow 0.2s;
}

.slide-item-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.slide-card-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.slide-index {
  font-size: 11px;
  background: #eff6ff;
  color: #3b82f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: bold;
}

.slide-title-input :deep(input) {
  font-weight: 700;
  font-size: 16px;
  border: none;
  background: #f8fafc;
  margin-bottom: 12px;
}

.field-label {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  margin: 12px 0 6px;
  text-transform: uppercase;
}

.slide-content-input :deep(textarea),
.slide-script-input :deep(textarea) {
  border: 1px solid #f1f5f9;
  background: #fff;
  font-size: 13px;
}

.slide-script-input :deep(textarea) {
  color: #6366f1;
}

.slide-visual-input :deep(input) {
  background: #eff6ff;
  border: none;
}

.add-card {
  border: 2px dashed #e2e8f0;
  background: transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #94a3b8;
}

.add-card:hover {
  background: #fff;
  border-color: #3b82f6;
  color: #3b82f6;
}

/* 步骤 2：风格选择样式 */
.theme-selector {
  padding: 40px;
  overflow-y: auto;
}

.theme-filters {
  max-width: 1200px;
  margin: 0 auto 32px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-label {
  font-size: 14px;
  color: #64748b;
  margin-right: 8px;
}

.theme-grid-large {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 32px;
  max-width: 1200px;
  margin: 0 auto;
}

.theme-card-premium {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.theme-card-premium:hover {
  transform: scale(1.05);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.theme-card-premium.active {
  border: 3px solid #3b82f6;
}

.theme-preview-box {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.box-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
  opacity: 0;
  transition: opacity 0.3s;
}

.theme-card-premium:hover .box-overlay {
  opacity: 1;
}

.theme-info-bar {
  padding: 16px;
}

.theme-name {
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 8px;
}

.theme-tags {
  display: flex;
  gap: 6px;
}

.theme-tags .tag {
  font-size: 10px;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
}

.selection-marker {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 24px;
  height: 24px;
  background: #3b82f6;
  border-radius: 50%;
  color: #fff;
  display: none;
  align-items: center;
  justify-content: center;
}

.theme-card-premium.active .selection-marker {
  display: flex;
}

/* 步骤 3：生成中样式 */
.generating-screen {
  background: #0f172a;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.processing-glow {
  position: absolute;
  width: 600px;
  height: 600px;
  background: radial-gradient(
    circle,
    rgba(56, 189, 248, 0.15) 0%,
    transparent 70%
  );
  filter: blur(80px);
  animation: float 10s infinite ease-in-out;
}

@keyframes float {
  0%,
  100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(100px, 50px);
  }
}

.generating-animation {
  text-align: center;
  z-index: 10;
}

.ai-brain-icon {
  margin-bottom: 32px;
}

.pulse-icon {
  font-size: 80px;
  color: #38bdf8;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.2);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 0.8;
  }
}

.generating-title {
  color: #fff;
  font-size: 28px;
  margin-bottom: 48px;
  font-weight: 300;
}

.progress-steps-list {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 16px;
}

.gen-step {
  color: #64748b;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.gen-step.done {
  color: #10b981;
}

.gen-step.active {
  color: #38bdf8;
  font-weight: 600;
}

/* 步骤 4：完成预览样式 */
.final-preview {
  padding: 40px;
  overflow-y: auto;
}

.preview-layout {
  display: flex;
  max-width: 1200px;
  margin: 0 auto;
  gap: 40px;
}

.preview-main {
  flex: 1;
  background: #f8fafc;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}

.mock-ppt-page {
  width: 100%;
  aspect-ratio: 16/9;
  background: #fff;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.mock-header {
  height: 48px;
  background: #f1f5f9;
}

.mock-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 40px;
}

.mock-title {
  font-size: 36px;
  color: #0f172a;
  margin-bottom: 24px;
}

.preview-sidebar {
  width: 340px;
}

.success-card {
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.success-icon {
  width: 64px;
  height: 64px;
  background: #d1fae5;
  color: #059669;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  margin: 0 auto 24px;
}
/* 高端 PPT 编辑器工作台 (对标图二效果) */
.ppt-editor-workspace {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
  overflow: hidden;
}

.editor-top-info {
  height: 48px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
}

.success-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #1e293b;
}

.editor-actions-top {
  display: flex;
  align-items: center;
  gap: 12px;
}

.editor-layout-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧胶片序列 */
.editor-filmstrip {
  width: 160px;
  background: #fff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
}

.filmstrip-header {
  padding: 12px;
  border-bottom: 1px solid #f1f5f9;
}

.filmstrip-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.thumb-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  cursor: pointer;
}

.thumb-num {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
}

.thumb-canvas {
  width: 136px;
  aspect-ratio: 16/9;
  border-radius: 4px;
  border: 2px solid #e2e8f0;
  background: #fff;
  padding: 8px;
  overflow: hidden;
  transition: all 0.2s;
}

.thumb-item.active .thumb-canvas {
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
}

.cover-thumb {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.thumb-title-mini-content {
  font-size: 10px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  scale: 0.9;
  transform-origin: left;
}

.thumb-content-layout {
  display: flex;
  gap: 4px;
  flex: 1;
}

.layout-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.mini-line {
  height: 2px;
  background: #f1f5f9;
  border-radius: 1px;
}

.layout-right {
  width: 30%;
  background: #f8fafc;
  border: 1px dashed #e2e8f0;
  border-radius: 2px;
}

.image-wrapper-rich {
  width: 100%;
  height: 240px;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.canvas-live-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.image-wrapper-rich:hover .canvas-live-image {
  transform: scale(1.1);
}

.img-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 20px;
  backdrop-filter: blur(4px);
}

/* 中间主画布 */
.editor-canvas-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f1f5f9;
  position: relative;
}

.canvas-toolbar {
  height: 40px;
  background: #fff;
  margin: 12px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  padding: 0 12px;
  gap: 12px;
}

.tool-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.divider {
  width: 1px;
  height: 16px;
  background: #e2e8f0;
}

.zoom-text {
  font-size: 12px;
  color: #64748b;
  font-weight: 600;
}

.rotate-icon {
  transform: rotate(-45deg);
}

.canvas-viewport {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.ppt-page-container {
  width: 100%;
  max-width: 900px;
  aspect-ratio: 16/9;
  background: #fff;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.ppt-cover-view {
  width: 100%;
  height: 100%;
  padding: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #fff;
}

.canvas-main-title {
  font-size: 42px;
  font-weight: 800;
  margin-bottom: 24px;
  line-height: 1.2;
}

.canvas-sub-title {
  font-size: 18px;
  opacity: 0.8;
}

.ppt-content-view {
  padding: 40px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.view-header {
  font-size: 28px;
  font-weight: 700;
  padding-left: 20px;
  margin-bottom: 32px;
  color: #0f172a;
}

.view-body {
  flex: 1;
  display: flex;
  gap: 40px;
}

.view-text {
  flex: 1;
}

.view-text ul {
  list-style: none;
  padding: 0;
}

.view-text li {
  font-size: 16px;
  color: #475569;
  margin-bottom: 16px;
  position: relative;
  padding-left: 24px;
}

.view-text li::before {
  content: "•";
  position: absolute;
  left: 0;
  color: #3b82f6;
  font-weight: bold;
}

.view-visual {
  width: 320px;
}

.image-placeholder {
  width: 100%;
  height: 240px;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  padding: 20px;
  color: #94a3b8;
  font-size: 12px;
}

/* 模版主题渲染：对标图二效果 */

/* 中国红主题：喜庆、高对比度 */
.ppt-page-container.warm_red .ppt-cover-view {
  background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%) !important;
  position: relative;
}
.ppt-page-container.warm_red .ppt-cover-view::after {
  content: "🏮";
  position: absolute;
  top: 20px;
  right: 20px;
  font-size: 60px;
  opacity: 0.3;
}
.ppt-page-container.warm_red .canvas-main-title {
  color: #fef08a; /* 金色字体 */
  text-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
}

/* 商务蓝主题：专业、严谨 */
.ppt-page-container.business_blue .ppt-cover-view {
  background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%) !important;
}
.ppt-page-container.business_blue .view-header {
  border-left: 6px solid #1e3a8a !important;
  background: #f1f5f9;
  padding: 12px 20px;
}

/* 科技黑主题：深邃、极客 */
.ppt-page-container.tech_dark {
  background: #0f172a !important;
  color: #f8fafc;
}
.ppt-page-container.tech_dark .ppt-cover-view {
  background: radial-gradient(
    circle at center,
    #1e293b 0%,
    #0f172a 100%
  ) !important;
}
.ppt-page-container.tech_dark .view-header {
  color: #38bdf8;
  border-left-color: #38bdf8 !important;
}
.ppt-page-container.tech_dark .view-text li {
  color: #94a3b8;
}

.notes-fab {
  position: absolute;
  bottom: 20px;
  right: 20px;
}
/* 多布局样式支持 */
.full-bleed-container {
  position: absolute;
  inset: 0;
}
.full-image-bg {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.full-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  padding: 60px;
}
.full-title {
  font-size: 36px;
  font-weight: 800;
  margin-bottom: 20px;
}
.full-points {
  display: flex;
  gap: 20px;
  font-weight: 500;
}

.triple-grid {
  display: flex;
  gap: 20px;
  padding: 0 20px;
}
.triple-card {
  flex: 1;
  background: #f8fafc;
  padding: 30px 20px;
  border-radius: 12px;
  text-align: center;
  border-bottom: 4px solid #3b82f6;
}
.card-icon {
  font-size: 32px;
  color: #3b82f6;
  margin-bottom: 16px;
}
.card-text {
  font-size: 14px;
  color: #1e293b;
  line-height: 1.6;
}

.view-header.centered {
  text-align: center;
  padding-left: 0;
  margin-bottom: 48px;
}
/* NanoBanana & Banana Slides Visual Polish */

.ppt-content-view {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Slide Transition Animations */
.ppt-page-container {
  overflow: hidden;
  position: relative;
}

.canvas-viewport {
  perspective: 1000px;
}

/* Infographic Layout */
.infographic-container {
  display: flex;
  height: 100%;
  padding: 40px;
  gap: 40px;
}

.info-visual-side {
  flex: 1;
  display: flex;
  align-items: center;
}

.info-img {
  width: 100%;
  max-height: 400px;
  object-fit: contain;
  filter: drop-shadow(0 20px 30px rgba(0, 0, 0, 0.1));
}

.info-content-side {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 24px;
}

.title-modern {
  font-size: 32px;
  font-weight: 800;
  border-bottom: 4px solid #3b82f6;
  width: fit-content;
  padding-bottom: 8px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 500;
}

/* Big Number Layout */
.big-number-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
}

.bn-main-box {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  padding: 60px 80px;
  border-radius: 30px;
  text-align: center;
  box-shadow: 0 30px 60px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.4);
}

.bn-number .bn-input {
  font-size: 120px;
  font-weight: 900;
  color: #3b82f6;
}

.bn-subtext {
  font-size: 24px;
  font-weight: 600;
  color: #64748b;
  margin-top: 20px;
}

/* Glassmorphism Classes */
.triple-card-glass {
  flex: 1;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(15px);
  padding: 30px 20px;
  border-radius: 20px;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
}
/* 专业编辑器扩展样式 */
.format-settings-panel {
  padding: 10px;
}

.setting-section {
  margin-bottom: 24px;
}

.setting-section h4 {
  font-size: 14px;
  color: #1e293b;
  margin-bottom: 12px;
  border-left: 3px solid #3b82f6;
  padding-left: 8px;
}

.theme-mini-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.theme-mini-card {
  padding: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.theme-mini-card.active {
  border-color: #3b82f6;
  background: #eff6ff;
}

.mini-color {
  width: 100%;
  height: 32px;
  border-radius: 4px;
}

.presentation-mode-fullscreen {
  position: fixed;
  inset: 0;
  z-index: 10000;
  background: #0f172a;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.presentation-controls {
  position: absolute;
  bottom: 40px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  padding: 12px 24px;
  border-radius: 40px;
  display: flex;
  align-items: center;
  gap: 20px;
  color: #fff;
}

.page-indicator {
  font-weight: 600;
  font-family: monospace;
}

.presentation-viewport {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
/* Inline Editing & Chat Styles */
.canvas-inline-input {
  width: 100%;
  background: transparent;
  border: 1px solid transparent;
  outline: none;
  font-family: inherit;
  transition: all 0.2s;
  padding: 4px 8px;
  border-radius: 4px;
}

.canvas-inline-input:hover {
  background: rgba(0, 0, 0, 0.02);
  border-color: #e2e8f0;
}

.canvas-inline-input:focus {
  background: #fff;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.title.canvas-inline-input {
  font-size: 28px;
  font-weight: 700;
  color: inherit;
}

.content-p.canvas-inline-input {
  font-size: 16px;
  color: #475569;
  resize: none;
  overflow: hidden;
}

.bullet-edit-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

.bullet-dot {
  color: #3b82f6;
  font-weight: bold;
  padding-top: 4px;
}

.editor-ai-chat-sidebar {
  width: 280px;
  background: #fff;
  border-left: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 15px rgba(0, 0, 0, 0.05);
  animation: slideInRight 0.3s ease;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.chat-header {
  padding: 12px 16px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 13px;
}

.chat-messages-flow {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-bubble {
  display: flex;
  gap: 8px;
  max-width: 90%;
}

.chat-bubble.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.bubble-avatar {
  width: 28px;
  height: 28px;
  background: #3b82f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.bubble-content {
  background: #f1f5f9;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 12px;
  line-height: 1.5;
  color: #1e293b;
  white-space: pre-wrap;
}

.chat-bubble.user .bubble-content {
  background: #3b82f6;
  color: #fff;
}

.chat-input-area {
  padding: 12px;
  border-top: 1px solid #f1f5f9;
}

.canvas-inline-input.centered {
  text-align: center;
}

.canvas-inline-input.light-text {
  color: #fff;
}

.canvas-inline-input.light-text:focus {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

/* 模板选择器包装样式 */
.template-selector-wrapper {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  min-height: 500px;
}
</style>
