<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, ArrowDown, ArrowRight, Edit, Check, Close } from '@element-plus/icons-vue'
import type { UploadProps, UploadUserFile } from 'element-plus'
import { createAgentAPI, updateAgentAPI } from '../../../apis/agent'
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

const formData = reactive<AgentFormData>({
  name: '',
  description: '',
  logo_url: '',
  tool_ids: [],
  llm_id: '',
  mcp_ids: [],
  system_prompt: '',
  knowledge_ids: [],
  use_embedding: false
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
      use_embedding: agent.use_embedding
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

// 关闭对话框
const close = () => {
  visible.value = false
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
    use_embedding: false
  })
  fileList.value = []
  editingAgentId.value = ''
  formRef.value?.clearValidate()
}

// 处理文件上传
const handleFileChange: UploadProps['onChange'] = (uploadFile) => {
  if (uploadFile.raw) {
    // 这里可以添加文件上传到服务器的逻辑
    // 暂时使用本地预览URL
    formData.logo_url = URL.createObjectURL(uploadFile.raw)
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

defineExpose({ open, close })
</script>

<template>
  <el-dialog
    v-model="visible"
    :title="isEditing ? '编辑智能体' : '创建智能体'"
    :width="1400"
    destroy-on-close
    class="agent-form-dialog"
    :show-close="false"
  >
    <template #header>
      <div class="dialog-header">
        <div class="header-left">
          <el-icon class="header-icon"><Edit /></el-icon>
          <span class="header-title">{{ isEditing ? "编辑助手" : "助手配置" }}</span>
        </div>
        <div class="header-right">
          <el-button @click="close" :icon="Close" circle></el-button>
        </div>
      </div>
    </template>

    <div class="dialog-content">
      <!-- 左侧预览面板 -->
      <div class="left-panel">
        <div class="assistant-preview">
          <div class="assistant-header">
            <div class="assistant-avatar">
              <img v-if="formData.logo_url" :src="formData.logo_url" alt="头像" />
              <el-icon v-else><Plus /></el-icon>
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
        <el-form ref="formRef" :model="formData" :rules="rules" class="config-form">
          <!-- 基础配置 -->
          <div class="config-section">
            <div class="section-header" @click="toggleCollapse('basic')">
              <el-icon>
                <ArrowDown v-if="collapseItems.basic" />
                <ArrowRight v-else />
              </el-icon>
              <span>基础配置</span>
            </div>
            <div v-show="collapseItems.basic" class="section-content">
              <el-form-item label="助手头像">
                <el-upload
                  v-model:file-list="fileList"
                  class="avatar-uploader"
                  action="#"
                  :show-file-list="false"
                  :auto-upload="false"
                  :on-change="handleFileChange"
                  :on-remove="handleFileRemove"
                >
                  <img v-if="formData.logo_url" :src="formData.logo_url" class="avatar" />
                  <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
                </el-upload>
              </el-form-item>
              
              <el-form-item label="助手名称" prop="name">
                <el-input v-model="formData.name" placeholder="请输入助手名称" />
              </el-form-item>
              
              <el-form-item label="助手描述" prop="description">
                <el-input
                  v-model="formData.description"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入助手描述"
                />
              </el-form-item>
            </div>
          </div>

          <!-- AI模型配置 -->
          <div class="config-section">
            <div class="section-header" @click="toggleCollapse('aiModel')">
              <el-icon>
                <ArrowDown v-if="collapseItems.aiModel" />
                <ArrowRight v-else />
              </el-icon>
              <span>AI模型配置</span>
            </div>
            <div v-show="collapseItems.aiModel" class="section-content">
              <el-form-item label="选择模型" prop="llm_id">
                <el-select v-model="formData.llm_id" placeholder="请选择大模型" style="width: 100%">
                  <el-option
                    v-for="llm in llmOptions"
                    :key="llm.id"
                    :label="llm.name"
                    :value="llm.id"
                  />
                </el-select>
              </el-form-item>
              
              <el-form-item label="系统提示词" prop="system_prompt">
                <el-input
                  v-model="formData.system_prompt"
                  type="textarea"
                  :rows="6"
                  placeholder="请输入系统提示词"
                />
              </el-form-item>
            </div>
          </div>

          <!-- 知识库 -->
          <div class="config-section">
            <div class="section-header" @click="toggleCollapse('knowledgeBase')">
              <el-icon>
                <ArrowDown v-if="collapseItems.knowledgeBase" />
                <ArrowRight v-else />
              </el-icon>
              <span>知识库</span>
              <el-icon class="add-icon"><Plus /></el-icon>
            </div>
            <div v-show="collapseItems.knowledgeBase" class="section-content">
              <el-form-item label="选择知识库">
                <el-select
                  v-model="formData.knowledge_ids"
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
              <el-icon class="add-icon"><Plus /></el-icon>
            </div>
            <div v-show="collapseItems.tools" class="section-content">
              <el-form-item label="选择工具">
                <el-select
                  v-model="formData.tool_ids"
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

          <!-- 技能 -->
          <div class="config-section">
            <div class="section-header" @click="toggleCollapse('skills')">
              <el-icon>
                <ArrowDown v-if="collapseItems.skills" />
                <ArrowRight v-else />
              </el-icon>
              <span>技能</span>
              <el-icon class="add-icon"><Plus /></el-icon>
            </div>
            <div v-show="collapseItems.skills" class="section-content">
              <el-form-item label="MCP服务器">
                <el-select
                  v-model="formData.mcp_ids"
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
        </el-form>

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
          <el-button @click="close">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleSubmit"
            :loading="loading"
            :icon="Check"
          >
            {{ isEditing ? '保存' : '创建' }}
          </el-button>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<style lang="scss" scoped>
.agent-form-dialog {
  :deep(.el-dialog) {
    border-radius: 12px;
    padding: 0;
  }

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