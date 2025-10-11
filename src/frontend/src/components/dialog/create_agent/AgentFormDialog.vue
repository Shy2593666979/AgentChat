<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, ArrowDown, ArrowRight, Edit, Check, Close } from '@element-plus/icons-vue'
import type { UploadProps, UploadUserFile } from 'element-plus'
import { createAgentAPI, updateAgentAPI } from '../../../apis/agent'
import { uploadFileAPI } from '../../../apis/file'
import { Agent, AgentFormData } from '../../../type'

const emits = defineEmits<{
  update: []
}>()

const visible = ref(false)
const loading = ref(false)
const formRef = ref()
const isEditing = ref(false)
const editingAgentId = ref('')
const fileList = ref<UploadUserFile[]>([])
const uploadLoading = ref(false)

const formData = reactive<AgentFormData>({
  name: '',
  description: '',
  logo_url: '',
  tool_ids: [],
  llm_id: '',
  mcp_ids: [],
  system_prompt: '',
  knowledge_ids: [],
  enable_memory: false
})

// 折叠面板状态
const collapseItems = ref({
  basic: true,
  aiModel: false,
  opening: false,
  knowledge: false,
  knowledgeBase: false,
  tools: false,
  skills: false
})

// 推荐问题
const recommendedQuestions = ref([
  "你能帮助我理解复杂的文本内容吗？",
  "如何生成高质量的文本回答？",
  "你可以提供哪些步骤指导来完成特定任务？"
])

const rules = {
  name: [{ required: true, message: '请输入智能体名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入智能体描述', trigger: 'blur' }],
  system_prompt: [{ required: true, message: '请输入系统提示词', trigger: 'blur' }],
  llm_id: [{ required: true, message: '请选择大模型', trigger: 'change' }]
}

// 模拟选项数据（实际项目中应该从API获取）
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

// 打开对话框
const open = (mode: 'create' | 'edit', agent?: Agent) => {
  visible.value = true
  isEditing.value = mode === 'edit'
  // 阻止背景滚动
  document.body.style.overflow = 'hidden'
  
  // 创建自定义遮罩层，确保覆盖所有内容
  setTimeout(() => {
    createCustomOverlay()
  }, 50)
  
  if (mode === 'edit' && agent) {
    editingAgentId.value = agent.agent_id
    Object.assign(formData, {
      name: agent.name,
      description: agent.description,
      logo_url: agent.logo_url,
      tool_ids: agent.tool_ids || [],
      llm_id: agent.llm_id,
      mcp_ids: agent.mcp_ids || [],
      system_prompt: agent.system_prompt,
      knowledge_ids: agent.knowledge_ids || [],
      enable_memory: agent.enable_memory
    })
    
    if (agent.logo_url) {
      fileList.value = [{
        name: 'avatar',
        url: agent.logo_url
      }]
    }
  } else {
    // 创建模式，重置表单
    resetForm()
  }
}

// 创建自定义遮罩层
const createCustomOverlay = () => {
  // 先移除可能存在的旧遮罩
  removeCustomOverlay()
  
  // 创建新的遮罩层
  const overlay = document.createElement('div')
  overlay.id = 'custom-dialog-overlay'
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.6);
    z-index: 999999;
    pointer-events: auto;
    backdrop-filter: blur(4px);
  `
  
  // 添加到body
  document.body.appendChild(overlay)
  
  // 点击遮罩关闭弹窗
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      close()
    }
  })
}

// 移除自定义遮罩层
const removeCustomOverlay = () => {
  const existingOverlay = document.getElementById('custom-dialog-overlay')
  if (existingOverlay) {
    existingOverlay.remove()
  }
}

// 关闭对话框
const close = () => {
  visible.value = false
  // 移除自定义遮罩层
  removeCustomOverlay()
  // 恢复背景滚动
  document.body.style.overflow = 'auto'
  resetForm()
}

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    name: '',
    description: '',
    logo_url: '',
    tool_ids: [],
    llm_id: '',
    mcp_ids: [],
    system_prompt: '你是一个智能助手 tmg-GPT，具有丰富的自然语言处理经验，擅长理解和生成文本内容，你的任务是帮助用户解决问题并提供信息支持，确保按照用户的指示执行任务。',
    knowledge_ids: [],
    enable_memory: false
  })
  fileList.value = []
  editingAgentId.value = ''
  formRef.value?.clearValidate()
}

// 处理文件上传
const fileInput = ref<HTMLInputElement>()

const handleFileUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) {
    await uploadAvatarFile(file)
  }
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
      formData.logo_url = response.data.data
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

const handleFileRemove: UploadProps['onRemove'] = () => {
  formData.logo_url = ''
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true
    
    if (isEditing.value) {
      // 编辑智能体
      if (!editingAgentId.value) {
        ElMessage.error('缺少智能体ID，无法更新')
        loading.value = false
        return
      }
      
      const updateData = {
        agent_id: editingAgentId.value,
        ...formData
      }
      
      console.log('更新智能体数据:', updateData)
      await updateAgentAPI(updateData)
      ElMessage.success('智能体更新成功')
    } else {
      // 创建智能体
      console.log('创建智能体数据:', formData)
      await createAgentAPI(formData)
      ElMessage.success('智能体创建成功')
    }
    
    emits('update')
    // 移除自定义遮罩层
    removeCustomOverlay()
    // 恢复背景滚动
    document.body.style.overflow = 'auto'
    close()
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error(isEditing.value ? '更新失败' : '创建失败')
  } finally {
    loading.value = false
  }
}

// 切换折叠面板
const toggleCollapse = (key: keyof typeof collapseItems.value) => {
  collapseItems.value[key] = !collapseItems.value[key]
}

onUnmounted(() => {
  // 组件卸载时恢复背景滚动，防止影响其他页面
  document.body.style.overflow = 'auto'
  // 移除自定义遮罩层
  removeCustomOverlay()
})

defineExpose({ open, close })
</script>

<template>
  <!-- 使用Teleport直接渲染到body，绕过所有容器限制 -->
  <Teleport to="body">
    <div v-if="visible" class="custom-dialog-wrapper">
      <!-- 自定义弹窗结构，完全脱离Element UI -->
      <div class="custom-dialog-overlay" @click.self="close">
        <div class="custom-dialog" @click.stop>
          <!-- 弹窗头部 -->
          <div class="dialog-header">
            <div class="header-left">
              <svg class="header-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 17.25V21H6.75L17.81 9.94L14.06 6.19L3 17.25Z" fill="#409eff"/>
              </svg>
              <span class="header-title">{{ isEditing ? "编辑助手" : "助手配置" }}</span>
            </div>
            <div class="header-right">
              <button @click="close" class="close-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
          </div>

          <div class="dialog-content">
            <!-- 左侧预览面板 -->
            <div class="left-panel">
              <div class="assistant-preview">
                <div class="assistant-header">
                  <div class="assistant-avatar">
                    <img v-if="formData.logo_url" :src="formData.logo_url" alt="头像" />
                    <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 2L13.09 8.26L19 7L18.74 13.74L24 12L17.74 16.74L19 19L13.74 18.26L12 22L10.26 16.74L5 17L5.26 10.26L2 12L8.26 7.26L7 5L12.26 5.74L12 2Z" fill="#409eff"/>
                    </svg>
                  </div>
                  <div class="assistant-info">
                    <h3>{{ formData.name || '助手名称' }}</h3>
                    <p>{{ formData.description || '助手描述' }}</p>
                  </div>
                </div>

                <div class="preview-content">
                  <div class="section">
                    <h4>## 角色</h4>
                    <p>{{ formData.system_prompt || '你是一个智能助手...' }}</p>
                  </div>

                  <div class="section">
                    <h4>## 技能</h4>
                    <p>1. 理解和生成自然语言：</p>
                    <p>- 你能够理解用户的输入，识别其意图，并生成相应的文本回答。</p>
                    <p>- 通过上下文分析，你可以提供相关信息和建议，帮助用户更好地理解问题。</p>
                    <br>
                    <p>2. 执行任务和提供步骤指导：</p>
                    <p>- 当用户需要执行特定任务时，你可以根据用户的需求，提供清晰的步骤指导。</p>
                    <p>- 你能够将复杂的任务分解为简单易懂的步骤，确保用户能够顺利完成。</p>
                  </div>

                  <div class="section">
                    <h4>## 限制</h4>
                    <p>- 只讨论与文本生成和自然语言处理相关的内容，拒绝回答与这些主题无关的话题。</p>
                    <p>- 所有的输出内容必须按照指定的格式进行组织，不能随意更改架构要求。</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- 右侧配置面板 -->
            <div class="right-panel">
              <form @submit.prevent="handleSubmit" class="config-form">
                <!-- 基础配置 -->
                <div class="config-section">
                  <div class="section-header" @click="toggleCollapse('basic')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path v-if="collapseItems.basic" d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path v-else d="M9 18L15 12L9 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span>基础配置</span>
                  </div>
                  <div v-show="collapseItems.basic" class="section-content">
                    <div class="form-group">
                      <label>助手头像</label>
                      <div class="avatar-upload">
                        <input type="file" @change="handleFileUpload" accept="image/*" style="display: none" ref="fileInput">
                        <div class="avatar-preview" @click="!uploadLoading && fileInput?.click()" :class="{ 'uploading': uploadLoading }">
                          <div v-if="uploadLoading" class="upload-loading">
                            <div class="loading-spinner"></div>
                            <span>上传中...</span>
                          </div>
                          <img v-else-if="formData.logo_url" :src="formData.logo_url" alt="头像" />
                          <div v-else class="upload-placeholder">
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                              <path d="M12 5v14M5 12h14" stroke="#ddd" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            <span>点击上传头像</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div class="form-group">
                      <label>助手名称 *</label>
                      <input v-model="formData.name" type="text" placeholder="请输入助手名称" required />
                    </div>
                    
                    <div class="form-group">
                      <label>助手描述 *</label>
                      <textarea v-model="formData.description" rows="3" placeholder="请输入助手描述" required></textarea>
                    </div>
                  </div>
                </div>

                <!-- AI模型配置 -->
                <div class="config-section">
                  <div class="section-header" @click="toggleCollapse('aiModel')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path v-if="collapseItems.aiModel" d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path v-else d="M9 18L15 12L9 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span>AI模型配置</span>
                  </div>
                  <div v-show="collapseItems.aiModel" class="section-content">
                    <div class="form-group">
                      <label>选择模型 *</label>
                      <select v-model="formData.llm_id" required>
                        <option value="">请选择大模型</option>
                        <option v-for="llm in llmOptions" :key="llm.id" :value="llm.id">
                          {{ llm.name }}
                        </option>
                      </select>
                    </div>
                    
                    <div class="form-group">
                      <label>系统提示词 *</label>
                      <textarea v-model="formData.system_prompt" rows="6" placeholder="请输入系统提示词" required></textarea>
                    </div>
                  </div>
                </div>

                <!-- 知识库 -->
                <div class="config-section">
                  <div class="section-header" @click="toggleCollapse('knowledgeBase')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path v-if="collapseItems.knowledgeBase" d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path v-else d="M9 18L15 12L9 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span>知识库</span>
                    <svg class="add-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 2L13.09 8.26L19 7L18.74 13.74L24 12L17.74 16.74L19 19L13.74 18.26L12 22L10.26 16.74L5 17L5.26 10.26L2 12L8.26 7.26L7 5L12.26 5.74L12 2Z" fill="#409eff"/>
                    </svg>
                  </div>
                  <div v-show="collapseItems.knowledgeBase" class="section-content">
                    <div class="form-group">
                      <label>选择知识库</label>
                      <div class="multi-select">
                        <div v-for="knowledge in knowledgeOptions" :key="knowledge.id" class="checkbox-item">
                          <input 
                            type="checkbox" 
                            :id="'knowledge-' + knowledge.id"
                            :value="knowledge.id" 
                            v-model="formData.knowledge_ids"
                          />
                          <label :for="'knowledge-' + knowledge.id">{{ knowledge.name }}</label>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 工具 -->
                <div class="config-section">
                  <div class="section-header" @click="toggleCollapse('tools')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path v-if="collapseItems.tools" d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path v-else d="M9 18L15 12L9 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span>工具</span>
                    <svg class="add-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 2L13.09 8.26L19 7L18.74 13.74L24 12L17.74 16.74L19 19L13.74 18.26L12 22L10.26 16.74L5 17L5.26 10.26L2 12L8.26 7.26L7 5L12.26 5.74L12 2Z" fill="#409eff"/>
                    </svg>
                  </div>
                  <div v-show="collapseItems.tools" class="section-content">
                    <div class="form-group">
                      <label>选择工具</label>
                      <div class="multi-select">
                        <div v-for="tool in toolOptions" :key="tool.id" class="checkbox-item">
                          <input 
                            type="checkbox" 
                            :id="'tool-' + tool.id"
                            :value="tool.id" 
                            v-model="formData.tool_ids"
                          />
                          <label :for="'tool-' + tool.id">{{ tool.name }}</label>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 技能 -->
                <div class="config-section">
                  <div class="section-header" @click="toggleCollapse('skills')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path v-if="collapseItems.skills" d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path v-else d="M9 18L15 12L9 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span>技能</span>
                    <svg class="add-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 2L13.09 8.26L19 7L18.74 13.74L24 12L17.74 16.74L19 19L13.74 18.26L12 22L10.26 16.74L5 17L5.26 10.26L2 12L8.26 7.26L7 5L12.26 5.74L12 2Z" fill="#409eff"/>
                    </svg>
                  </div>
                  <div v-show="collapseItems.skills" class="section-content">
                    <div class="form-group">
                      <label>MCP服务器</label>
                      <div class="multi-select">
                        <div v-for="mcp in mcpOptions" :key="mcp.id" class="checkbox-item">
                          <input 
                            type="checkbox" 
                            :id="'mcp-' + mcp.id"
                            :value="mcp.id" 
                            v-model="formData.mcp_ids"
                          />
                          <label :for="'mcp-' + mcp.id">{{ mcp.name }}</label>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </form>

              <!-- 推荐问题 -->
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

              <!-- 操作按钮 -->
              <div class="action-buttons">
                <button type="button" @click="close" class="btn btn-cancel">取消</button>
                <button 
                  type="button" 
                  @click="handleSubmit"
                  :disabled="loading"
                  class="btn btn-primary"
                >
                  <span v-if="loading" class="loading-spinner"></span>
                  {{ isEditing ? '保存' : '创建' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style lang="scss">
// 全局样式，不使用scoped，确保能覆盖Element UI的默认样式
.agent-form-dialog {
  .el-dialog {
    border-radius: 12px;
    padding: 0;
    z-index: 1000000 !important;
  }
  
  .el-overlay {
    display: none !important; // 隐藏Element UI自带的遮罩，使用我们的自定义遮罩
  }
}

// 确保弹窗覆盖所有元素
.el-dialog__wrapper {
  z-index: 1000000 !important;
}

// 自定义遮罩层样式
#custom-dialog-overlay {
  z-index: 999999 !important;
}
</style>

<style lang="scss" scoped>
.agent-form-dialog {
  :deep(.el-dialog__body) {
    padding: 0;
  }

  .dialog-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid #e4e7ed;

    .header-left {
      display: flex;
      align-items: center;
      gap: 8px;

      .header-icon {
        color: #409eff;
      }

      .header-title {
        font-size: 18px;
        font-weight: 600;
      }
    }
  }

  .dialog-content {
    display: flex;
    height: 80vh;

    .left-panel {
      width: 50%;
      padding: 24px;
      background-color: #fafbfc;
      border-right: 1px solid #e4e7ed;
      overflow-y: auto;

      .assistant-preview {
        .assistant-header {
          display: flex;
          align-items: center;
          gap: 16px;
          margin-bottom: 24px;

          .assistant-avatar {
            width: 60px;
            height: 60px;
            border-radius: 12px;
            border: 2px dashed #d9d9d9;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;

            img {
              width: 100%;
              height: 100%;
              object-fit: cover;
            }
          }

          .assistant-info {
            flex: 1;

            h3 {
              margin: 0 0 8px 0;
              font-size: 18px;
              color: #303133;
            }

            p {
              margin: 0;
              color: #606266;
              font-size: 14px;
            }
          }
        }

        .preview-content {
          .section {
            margin-bottom: 24px;

            h4 {
              margin: 0 0 12px 0;
              font-size: 16px;
              color: #303133;
              font-weight: 600;
            }

            p {
              margin: 0 0 8px 0;
              color: #606266;
              line-height: 1.6;
              font-size: 14px;
            }
          }
        }
      }
    }

    .right-panel {
      width: 50%;
      padding: 24px;
      overflow-y: auto;

      .config-form {
        .config-section {
          margin-bottom: 16px;
          border: 1px solid #e4e7ed;
          border-radius: 8px;

          .section-header {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 16px;
            background-color: #f5f7fa;
            cursor: pointer;
            user-select: none;

            &:hover {
              background-color: #ecf5ff;
            }

            span {
              flex: 1;
              font-weight: 500;
            }

            .add-icon {
              margin-left: auto;
              color: #409eff;
              cursor: pointer;

              &:hover {
                color: #337ecc;
              }
            }
          }

          .section-content {
            padding: 16px;

            .el-form-item {
              margin-bottom: 16px;
            }
          }
        }
      }

      .avatar-upload {
        .avatar-preview {
          width: 80px;
          height: 80px;
          border: 2px dashed #ddd;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.3s ease;
          background: #fafafa;
          position: relative;
          
          &:hover:not(.uploading) {
            border-color: #409eff;
            background: #f0f7ff;
          }
          
          &.uploading {
            cursor: not-allowed;
            border-color: #409eff;
            background: #f0f7ff;
          }
          
          img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 10px;
          }
          
          .upload-loading {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            
            .loading-spinner {
              width: 20px;
              height: 20px;
              border: 2px solid #f3f3f3;
              border-top: 2px solid #409eff;
              border-radius: 50%;
              animation: spin 1s linear infinite;
            }
            
            span {
              font-size: 12px;
              color: #409eff;
            }
          }
          
          .upload-placeholder {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            
            span {
              font-size: 12px;
              color: #999;
            }
          }
        }
      }
      
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }

      .avatar-uploader {
        :deep(.el-upload) {
          border: 1px dashed #d9d9d9;
          border-radius: 6px;
          cursor: pointer;
          position: relative;
          overflow: hidden;
          transition: border-color 0.3s;
          width: 80px;
          height: 80px;
          display: flex;
          align-items: center;
          justify-content: center;

          &:hover {
            border-color: #409eff;
          }
        }

        .avatar {
          width: 80px;
          height: 80px;
          object-fit: cover;
          border-radius: 6px;
        }

        .avatar-uploader-icon {
          font-size: 28px;
          color: #8c939d;
        }
      }

      .recommended-questions {
        margin-top: 24px;
        padding-top: 24px;
        border-top: 1px solid #e4e7ed;

        h4 {
          margin: 0 0 16px 0;
          font-size: 16px;
          color: #303133;
        }

        .question-list {
          .question-item {
            padding: 12px 16px;
            background-color: #f0f2f5;
            border-radius: 8px;
            margin-bottom: 8px;
            font-size: 14px;
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

      .action-buttons {
        display: flex;
        justify-content: flex-end;
        gap: 12px;
        padding-top: 24px;
        border-top: 1px solid #e4e7ed;
        margin-top: 24px;
      }
    }
  }
}
</style> 