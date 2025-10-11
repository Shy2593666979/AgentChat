<script lang="ts" setup>
import { ref, onMounted } from "vue"
import { ElMessage } from 'element-plus'
import { Plus, ArrowDown, ArrowRight, Edit, Check, Close } from "@element-plus/icons-vue"
import type { UploadProps, UploadUserFile } from "element-plus"
import { createAgentAPI, updateAgentAPI } from "../../../apis/agent"
import { uploadFileAPI } from "../../../apis/file"
import { Agent, AgentFormData } from "../../../type"

const fileList = ref<UploadUserFile[]>([])
const emits = defineEmits<(event: "update") => void>()
const visible = ref<boolean>(false)
const formRef = ref()
const eventType = ref("")
const id = ref('')
const uploadLoading = ref(false)

const form = ref<AgentFormData>({
  name: "",
  description: "",
  logo_url: "",
  system_prompt: "",
  llm_id: "",
  tool_ids: [],
  mcp_ids: [],
  knowledge_ids: [],
  enable_memory: false
})

const collapseItems = ref({
  aiModel: true,
  mcpAgent: false,
  knowledge: false,
  tools: false
})

const recommendedQuestions = ref([
  "你能帮助我理解复杂的文本内容吗？",
  "如何生成高质量的文本回答？",
  "你可以提供哪些步骤指导来完成特定任务？"
])

const rules = ref({
  system_prompt: [{ required: true, message: "系统提示词不能为空", trigger: "blur" }],
  llm_id: [{ required: true, message: "请选择大模型", trigger: "change" }],
})

const llmOptions = ref([
  { id: '1', name: 'GPT-4', model: 'gpt-4' },
  { id: '2', name: 'GPT-3.5-turbo', model: 'gpt-3.5-turbo' },
  { id: '3', name: 'Claude-3', model: 'claude-3' }
])

const toolOptions = ref([
  { id: '1', name: 'Web搜索', description: '网络搜索工具' },
  { id: '2', name: '代码执行', description: '代码运行工具' },
  { id: '3', name: '图片生成', description: '图片生成工具' }
])

const mcpOptions = ref([
  { id: '1', name: '天气服务', description: '天气查询服务' },
  { id: '2', name: '邮件服务', description: '邮件发送服务' }
])

const knowledgeOptions = ref([
  { id: '1', name: '技术文档', description: '技术相关文档' },
  { id: '2', name: '产品手册', description: '产品使用手册' }
])

onMounted(async () => { })

const open = async (event: string, item?: Agent) => {
  visible.value = true
  eventType.value = event
  fileList.value = []

  if (event === "create") {
    form.value = {
      name: "",
      description: "",
      logo_url: "",
      system_prompt: "你是一个智能助手 tmg-GPT，具有丰富的自然语言处理经验，擅长理解和生成文本内容，你的任务是帮助用户解决问题并提供信息支持，确保按照用户的指示执行任务。",
      llm_id: "",
      tool_ids: [],
      mcp_ids: [],
      knowledge_ids: [],
      enable_memory: false
    }
  } else {
    if (item) {
      fileList.value.push({
        url: item.logo_url,
        name: "avatar",
      })
      form.value = {
        name: item.name,
        description: item.description,
        logo_url: item.logo_url,
        system_prompt: item.system_prompt,
        llm_id: item.llm_id,
        tool_ids: item.tool_ids || [],
        mcp_ids: item.mcp_ids || [],
        knowledge_ids: item.knowledge_ids || [],
        enable_memory: item.enable_memory
      }
      id.value = item.agent_id
    }
  }
}

const close = () => {
  visible.value = false
}

const handleFileChange: UploadProps['onChange'] = async (uploadFile) => {
  if (uploadFile.raw) {
    await uploadAvatarFile(uploadFile.raw)
  }
}

const uploadAvatarFile = async (file: File) => {
  // 文件大小和类型检查
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isLt2M) {
    ElMessage.error('上传头像图片大小不能超过 2MB!')
    return
  }
  const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png'
  if (!isJpgOrPng) {
    ElMessage.error('上传头像图片只能是 JPG/PNG 格式!')
    return
  }
  
  // 开始上传
  uploadLoading.value = true
  try {
    const uploadFormData = new FormData()
    uploadFormData.append('file', file)
    
    const response = await uploadFileAPI(uploadFormData)
    
    if (response.data.status_code === 200) {
      form.value.logo_url = response.data.data
      ElMessage.success('头像上传成功')
    } else {
      ElMessage.error(response.data.status_message || '头像上传失败')
    }
  } catch (error) {
    console.error('头像上传失败:', error)
    ElMessage.error('头像上传失败')
  } finally {
    uploadLoading.value = false
  }
}

const handleConfirm = async () => {
  try {
    await formRef.value.validate()
    if (eventType.value === "create") {
      await createAgentAPI(form.value)
      ElMessage.success('智能体创建成功')
    } else {
      await updateAgentAPI({
        agent_id: id.value,
        ...form.value
      })
      ElMessage.success('智能体更新成功')
    }
    emits("update")
    close()
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error(eventType.value === "create" ? '创建失败' : '更新失败')
  }
}

const toggleCollapse = (key: keyof typeof collapseItems.value) => {
  collapseItems.value[key] = !collapseItems.value[key]
}

defineExpose({ open, close })
</script>

<template>
  <el-dialog 
    v-model="visible" 
    width="90%"
    class="agent-config-dialog"
    :show-close="false"
    destroy-on-close
  >
    <template #header>
      <div class="dialog-header">
        <div class="header-left">
          <el-icon class="header-icon"><Edit /></el-icon>
          <span class="header-title">{{ eventType === "create" ? "助手系统提示词与配置" : "编辑助手" }}</span>
        </div>
        <div class="header-actions">
          <el-button @click="handleConfirm" type="primary" :icon="Check">
            {{ eventType === "create" ? "创建" : "保存" }}
          </el-button>
          <el-button @click="close" :icon="Close" circle></el-button>
        </div>
      </div>
    </template>
    <div class="dialog-content">
      <!-- 左侧：系统提示词编辑区 -->
      <div class="left-panel">
        <h4>系统提示词</h4>
        <el-input
          v-model="form.system_prompt"
          type="textarea"
          :rows="24"
          placeholder="请输入系统提示词"
          class="prompt-textarea"
        />
      </div>
      <!-- 中间：四项配置 -->
      <div class="middle-panel">
        <div class="config-sections">
          <!-- AI模型配置 -->
          <div class="config-section">
            <div class="section-header" @click="toggleCollapse('aiModel')">
              <el-icon>
                <ArrowDown v-if="collapseItems.aiModel" />
                <ArrowRight v-else />
              </el-icon>
              <span>AI模型</span>
            </div>
            <div v-show="collapseItems.aiModel" class="section-content">
              <el-form-item label="选择模型" prop="llm_id">
                <el-select v-model="form.llm_id" placeholder="请选择大模型" style="width: 100%">
                  <el-option
                    v-for="llm in llmOptions"
                    :key="llm.id"
                    :label="llm.name"
                    :value="llm.id"
                  />
                </el-select>
              </el-form-item>
            </div>
          </div>
          <!-- MCP Agent -->
          <div class="config-section">
            <div class="section-header" @click="toggleCollapse('mcpAgent')">
              <el-icon>
                <ArrowDown v-if="collapseItems.mcpAgent" />
                <ArrowRight v-else />
              </el-icon>
              <span>MCP Agent</span>
            </div>
            <div v-show="collapseItems.mcpAgent" class="section-content">
              <el-form-item label="MCP服务器">
                <el-select
                  v-model="form.mcp_ids"
                  multiple
                  placeholder="请选择MCP服务器"
                  style="width: 100%"
                >
                  <el-option
                    v-for="mcp in mcpOptions"
                    :key="mcp.id"
                    :label="mcp.name"
                    :value="mcp.id"
                  />
                </el-select>
              </el-form-item>
            </div>
          </div>
          <!-- 知识库 -->
          <div class="config-section">
            <div class="section-header" @click="toggleCollapse('knowledge')">
              <el-icon>
                <ArrowDown v-if="collapseItems.knowledge" />
                <ArrowRight v-else />
              </el-icon>
              <span>知识库</span>
            </div>
            <div v-show="collapseItems.knowledge" class="section-content">
              <el-form-item label="选择知识库">
                <el-select
                  v-model="form.knowledge_ids"
                  multiple
                  placeholder="请选择知识库"
                  style="width: 100%"
                >
                  <el-option
                    v-for="knowledge in knowledgeOptions"
                    :key="knowledge.id"
                    :label="knowledge.name"
                    :value="knowledge.id"
                  />
                </el-select>
              </el-form-item>

            </div>
          </div>
          <!-- 工具 -->
          <div class="config-section">
            <div class="section-header" @click="toggleCollapse('tools')">
              <el-icon>
                <ArrowDown v-if="collapseItems.tools" />
                <ArrowRight v-else />
              </el-icon>
              <span>工具</span>
            </div>
            <div v-show="collapseItems.tools" class="section-content">
              <el-form-item label="选择工具">
                <el-select
                  v-model="form.tool_ids"
                  multiple
                  placeholder="请选择工具"
                  style="width: 100%"
                >
                  <el-option
                    v-for="tool in toolOptions"
                    :key="tool.id"
                    :label="tool.name"
                    :value="tool.id"
                  />
                </el-select>
              </el-form-item>
            </div>
          </div>
        </div>
      </div>
      <!-- 右侧：调试预览 -->
      <div class="right-panel">
        <div class="panel-header">
          <el-button type="warning" class="debug-btn">
            <el-icon><Edit /></el-icon>
            调试预览
          </el-button>
        </div>
        <div class="debug-content">
          <div class="config-status">
            <span class="status-text">配置已更新</span>
          </div>
          <div class="chat-preview">
            <div class="chat-message ai-message">
              <div class="message-avatar">
                <img v-if="form.logo_url" :src="form.logo_url" alt="助手头像" />
                <el-icon v-else><Plus /></el-icon>
              </div>
              <div class="message-content">
                <p>{{ form.description || '你好，我是智能助手 tmg-GPT，擅长理解和生成文本内容，随时准备帮助你解决问题并提供信息支持。' }}</p>
              </div>
            </div>
          </div>
          <div class="recommended-questions">
            <h4>推荐问题</h4>
            <div class="question-list">
              <div
                v-for="(question, index) in recommendedQuestions"
                :key="index"
                class="question-item"
              >
                {{ question }}
              </div>
            </div>
          </div>
          <div class="chat-input">
            <div class="input-wrapper">
              <el-icon class="input-icon"><Edit /></el-icon>
              <input type="text" placeholder="请输入问题" class="chat-input-field" />
              <el-button type="primary" class="send-btn">
                <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
            <div class="input-footer">
              <span>内容由AI生成，仅供参考！</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<style lang="scss" scoped>
.agent-config-dialog {
  :deep(.el-dialog) {
    border-radius: 12px;
    padding: 0;
    max-width: 1800px;
    min-width: 1200px;
  }
  :deep(.el-dialog__body) {
    padding: 0;
    height: 85vh;
    overflow: hidden;
  }
  .dialog-content {
    display: flex;
    height: 85vh;
    width: 100%;
    .left-panel {
      width: 25%;
      min-width: 300px;
      background-color: #fafbfc;
      border-right: 1px solid #e4e7ed;
      overflow-y: auto;
      flex-shrink: 0;
      padding: 32px 24px;
      h4 {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 16px;
      }
      .prompt-textarea {
        :deep(.el-textarea__inner) {
          font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
          font-size: 14px;
          line-height: 1.5;
          border-radius: 6px;
        }
      }
    }
    .middle-panel {
      width: 35%;
      min-width: 400px;
      background-color: #fff;
      border-right: 1px solid #e4e7ed;
      overflow-y: auto;
      flex-shrink: 0;
      padding: 32px 24px;
      .config-sections {
        .config-section {
          margin-bottom: 16px;
          border: 1px solid #e4e7ed;
          border-radius: 8px;
          background-color: #fafbfc;
          .section-header {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 16px;
            cursor: pointer;
            user-select: none;
            font-size: 15px;
            font-weight: 500;
            &:hover {
              background-color: #f0f2f5;
            }
            span {
              flex: 1;
              font-weight: 500;
            }
          }
          .section-content {
            padding: 16px;
            background-color: #fff;
            border-top: 1px solid #e4e7ed;
            .el-form-item {
              margin-bottom: 16px;
            }
          }
        }
      }
    }
    .right-panel {
      width: 40%;
      min-width: 400px;
      background-color: #fafbfc;
      overflow-y: auto;
      flex-shrink: 0;
      padding: 32px 24px;
      .panel-header {
        margin-bottom: 16px;
      }
      .debug-content {
        .config-status {
          text-align: center;
          margin-bottom: 20px;
          .status-text {
            color: #67c23a;
            font-size: 12px;
            border: 1px dashed #67c23a;
            padding: 4px 12px;
            border-radius: 4px;
            background-color: #f0f9ff;
          }
        }
        .chat-preview {
          margin-bottom: 20px;
          .chat-message {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
            .message-avatar {
              width: 32px;
              height: 32px;
              border-radius: 6px;
              overflow: hidden;
              display: flex;
              align-items: center;
              justify-content: center;
              background-color: #f0f2f5;
              img {
                width: 100%;
                height: 100%;
                object-fit: cover;
              }
            }
            .message-content {
              flex: 1;
              background-color: #fff;
              padding: 12px;
              border-radius: 8px;
              box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
              p {
                margin: 0;
                color: #303133;
                font-size: 14px;
                line-height: 1.5;
              }
            }
          }
        }
        .recommended-questions {
          margin-bottom: 20px;
          h4 {
            margin: 0 0 12px 0;
            font-size: 14px;
            color: #303133;
          }
          .question-list {
            .question-item {
              padding: 8px 12px;
              background-color: #f0f2f5;
              border-radius: 6px;
              margin-bottom: 8px;
              font-size: 13px;
              color: #606266;
              cursor: pointer;
              transition: all 0.3s;
              &:hover {
                background-color: #e6f7ff;
                color: #409eff;
              }
            }
          }
        }
        .chat-input {
          .input-wrapper {
            display: flex;
            align-items: center;
            background-color: #fff;
            border-radius: 8px;
            padding: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            .input-icon {
              color: #909399;
              margin-right: 8px;
            }
            .chat-input-field {
              flex: 1;
              border: none;
              outline: none;
              font-size: 14px;
              color: #303133;
              &::placeholder {
                color: #c0c4cc;
              }
            }
            .send-btn {
              margin-left: 8px;
              padding: 6px 12px;
              border-radius: 6px;
            }
          }
          .input-footer {
            text-align: center;
            margin-top: 8px;
            span {
              color: #909399;
              font-size: 12px;
            }
          }
        }
      }
    }
  }
}
</style>
