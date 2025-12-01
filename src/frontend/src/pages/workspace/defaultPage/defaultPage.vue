<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MdPreview } from "md-editor-v3"
import "md-editor-v3/lib/style.css"
import { getWorkspacePluginsAPI, workspaceSimpleChatStreamAPI, type WorkSpaceSimpleTask } from '../../../apis/workspace'
import { getVisibleLLMsAPI, type LLMResponse } from '../../../apis/llm'
import { useUserStore } from '../../../store/user'

const userStore = useUserStore()

const router = useRouter()
const route = useRoute()
const inputMessage = ref('')
const selectedMode = ref('normal')
const plugins = ref<any[]>([])
const showModelSelector = ref(false)
const showToolSelector = ref(false)
const showSearchSelector = ref(false)
const selectedModel = ref<string>('')
const selectedModelId = ref<string>('')
const selectedTools = ref<string[]>([])
const showMcpSelector = ref(false)
const selectedMcpServers = ref<string[]>([])
const mcpServers = ref<any[]>([])
const webSearchEnabled = ref(false)
const toolDropdownRef = ref<HTMLElement | null>(null)
const mcpDropdownRef = ref<HTMLElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const currentSessionId = ref<string>('')  // 当前会话ID
const chatConversationRef = ref<HTMLElement | null>(null)  // 聊天容器引用
const isGenerating = ref(false)  // 是否正在生成回复

// 模型数据（来自应用中心"可见模型"）
const modelOptions = ref<LLMResponse[]>([])
const modelsLoading = ref(false)

// 本页对话消息（用户在上，AI在下）
const messages = ref<Array<{ role: 'user' | 'assistant'; content: string }>>([])

// 头像加载错误处理
const handleAvatarError = (event: Event) => {
  const target = event.target as HTMLImageElement
  if (target) {
    target.src = '/src/assets/user.svg'
  }
}

const modes = [
  {
    id: 'normal',
    label: '日常模式',
    icon: '💬'
  },
  {
    id: 'lingseek',
    label: '灵寻LingSeek',
    icon: '✨'
  }
]

// 从接口加载模型
const fetchModels = async () => {
  modelsLoading.value = true
  try {
    const res = await getVisibleLLMsAPI()
    if (res.data && res.data.status_code === 200) {
      const grouped = res.data.data || {}
      const list: LLMResponse[] = []
      Object.values(grouped).forEach((arr: any) => {
        if (Array.isArray(arr)) list.push(...arr)
      })
      // 仅保留 LLM 类型
      modelOptions.value = list.filter(m => (m.llm_type || '').toUpperCase() === 'LLM')
      // 默认选择第一个
      if (!selectedModelId.value && modelOptions.value.length > 0) {
        selectedModelId.value = modelOptions.value[0].llm_id
        selectedModel.value = modelOptions.value[0].model
      }
    }
  } catch (e) {
    console.error('获取模型失败', e)
  } finally {
    modelsLoading.value = false
  }
}

// 获取可用插件
const fetchPlugins = async () => {
  try {
    const response = await getWorkspacePluginsAPI()
    if (response.data.status_code === 200) {
      plugins.value = response.data.data || []
      console.log('可用插件:', plugins.value)
    }
  } catch (error) {
    console.error('获取插件列表出错:', error)
  }
}

// 选择模式
const selectMode = (modeId: string) => {
  selectedMode.value = modeId
}

// 选择模型
const selectModel = (llmId: string) => {
  const model = modelOptions.value.find(m => m.llm_id === llmId)
  if (model) {
    selectedModelId.value = model.llm_id
    selectedModel.value = model.model
  }
  showModelSelector.value = false
}

// 切换工具选择
const toggleTool = (toolId: string) => {
  const index = selectedTools.value.indexOf(toolId)
  if (index > -1) {
    selectedTools.value.splice(index, 1)
  } else {
    selectedTools.value.push(toolId)
  }
}

// 切换联网搜索
const toggleWebSearch = () => {
  webSearchEnabled.value = !webSearchEnabled.value
  showSearchSelector.value = false
}

// 点击空白处关闭工具/MCP下拉
const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as Node
  if (showToolSelector.value && toolDropdownRef.value && !toolDropdownRef.value.contains(target)) {
    showToolSelector.value = false
  }
  if (showMcpSelector.value && mcpDropdownRef.value && !mcpDropdownRef.value.contains(target)) {
    showMcpSelector.value = false
  }
}

// 触发文件选择
const triggerFileInput = () => {
  fileInputRef.value?.click()
}

// 处理文件选择
const onFileChange = (e: Event) => {
  const input = e.target as HTMLInputElement
  const files = input.files
  if (files && files.length > 0) {
    ElMessage.success(`已选择 ${files.length} 个文件`)
  }
  if (input) input.value = ''
}

// 切换 MCP 服务器选择
const toggleMcp = (serverId: string) => {
  const index = selectedMcpServers.value.indexOf(serverId)
  if (index > -1) {
    selectedMcpServers.value.splice(index, 1)
  } else {
    selectedMcpServers.value.push(serverId)
  }
}

// 生成UUID（模拟Python的uuid4().hex）
const generateSessionId = (): string => {
  // 使用crypto.randomUUID()生成UUID，然后移除横杠
  return crypto.randomUUID().replace(/-/g, '')
}

// 自动滚动到底部
const scrollToBottom = () => {
  if (chatConversationRef.value) {
    setTimeout(() => {
      if (chatConversationRef.value) {
        chatConversationRef.value.scrollTop = chatConversationRef.value.scrollHeight
      }
    }, 100)
  }
}

// 发送消息
const handleSend = async () => {
  if (!inputMessage.value.trim()) {
    ElMessage.warning('请输入消息内容')
    return
  }

  // 如果正在生成回复，不允许发送新消息
  if (isGenerating.value) {
    ElMessage.warning('请等待当前回复完成')
    return
  }
  
  const query = inputMessage.value.trim()
  
  // 根据模式跳转到不同的页面
  if (selectedMode.value === 'lingseek') {
    // 灵寻模式：直接跳转到任务流程图页面（三列布局）
    console.log('跳转到灵寻任务页面')
    console.log('query:', query)
    console.log('tools:', selectedTools.value)
    console.log('webSearch:', webSearchEnabled.value)
    
    // 立即清空输入框
    inputMessage.value = ''
    
    router.push({
      name: 'taskGraphPage',
      query: {
        query: query,
        tools: JSON.stringify(selectedTools.value),
        webSearch: webSearchEnabled.value.toString(),
        mcp_servers: JSON.stringify(selectedMcpServers.value)
      }
    })
  } else {
    // 日常模式：在本页进行对话（流式）
    console.log('=== 日常模式发送消息 ===')
    console.log('selectedModelId:', selectedModelId.value)
    console.log('query:', query)
    console.log('session_id:', currentSessionId.value)
    
    if (!selectedModelId.value) {
      ElMessage.warning('请先选择模型')
      return
    }

    // 如果还没有session_id，生成一个新的
    if (!currentSessionId.value) {
      currentSessionId.value = generateSessionId()
      console.log('生成新的 session_id:', currentSessionId.value)
    }

    // 立即清空输入框，提升用户体验
    inputMessage.value = ''
    
    // 设置正在生成状态（转圈）
    isGenerating.value = true

    // 将用户消息加入消息列表
    console.log('将用户消息加入 messages')
    messages.value.push({ role: 'user' as const, content: query })
    
    // 自动滚动到底部
    scrollToBottom()
    
    // 预置一条AI消息用于流式累加（先添加到数组，然后通过索引更新以触发响应式）
    const aiMsgIndex = messages.value.length
    messages.value.push({ role: 'assistant', content: '' })
    console.log('当前 messages 长度:', messages.value.length)

    try {
      const payload: WorkSpaceSimpleTask = {
        query,
        model_id: selectedModelId.value,
        plugins: selectedTools.value,
        mcp_servers: selectedMcpServers.value,
        session_id: currentSessionId.value  // 添加session_id参数
      }
      console.log('准备调用 workspaceSimpleChatStreamAPI，payload:', payload)
      await workspaceSimpleChatStreamAPI(
        payload,
        (chunk) => {
          console.log('收到 chunk，累加到 aiMsg:', chunk)
          // 通过索引更新以触发 Vue 的响应式
          messages.value[aiMsgIndex].content += chunk
          // 每次收到新内容时自动滚动到底部
          scrollToBottom()
        },
        (err) => {
          console.error('日常模式流式出错', err)
          ElMessage.error('对话失败，请稍后重试')
          isGenerating.value = false  // 出错时解除生成状态
        },
        () => {
          console.log('日常模式流式结束')
          isGenerating.value = false  // 完成时解除生成状态
        }
      )
    } catch (e) {
      console.error('日常模式对话异常', e)
      ElMessage.error('对话异常')
      isGenerating.value = false  // 异常时解除生成状态
    }
  }
}

// 键盘事件处理
const handleKeydown = (event: KeyboardEvent) => {
  // 直接回车发送，Shift+Enter 换行
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    // 如果正在生成，不响应回车
    if (!isGenerating.value) {
      handleSend()
    }
  }
}

// 加载会话历史
const loadSessionHistory = async (sessionId: string) => {
  try {
    // 导入 API
    const { getWorkspaceSessionsAPI } = await import('../../../apis/workspace')
    const response = await getWorkspaceSessionsAPI()
    
    if (response.data.status_code === 200) {
      const session = response.data.data.find((s: any) => s.session_id === sessionId)
      
      if (session && session.contexts && Array.isArray(session.contexts)) {
        // 将 contexts 转换为 messages 格式
        messages.value = session.contexts.map((ctx: any) => [
          { role: 'user' as const, content: ctx.query || '' },
          { role: 'assistant' as const, content: ctx.answer || '' }
        ]).flat().filter((msg: any) => msg.content) // 过滤掉空内容
        
        console.log('已加载会话历史，消息数量:', messages.value.length)
        
        // 加载历史后滚动到底部
        scrollToBottom()
      }
    }
  } catch (error) {
    console.error('加载会话历史失败:', error)
    ElMessage.error('加载会话历史失败')
  }
}

onMounted(async () => {
  fetchPlugins()
  fetchModels()
  
  // 检查是否有 session_id 参数，如果有则加载会话历史
  const sessionId = route.query.session_id as string
  if (sessionId) {
    console.log('加载已有会话:', sessionId)
    currentSessionId.value = sessionId  // 设置当前会话ID
    await loadSessionHistory(sessionId)
  } else {
    // 如果没有session_id，生成一个新的
    currentSessionId.value = generateSessionId()
    console.log('生成新会话ID:', currentSessionId.value)
  }
  
  // 懒加载 MCP 列表（用于选择）
  import('../../../apis/mcp-server').then(async ({ getMCPServersAPI }) => {
    try {
      const res = await getMCPServersAPI()
      if (res.data && res.data.status_code === 200 && Array.isArray(res.data.data)) {
        mcpServers.value = res.data.data
      }
    } catch (e) {
      console.error('加载 MCP 服务器失败', e)
    }
  })
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 监听路由参数变化
watch(
  () => route.query.session_id,
  async (newSessionId, oldSessionId) => {
    if (newSessionId && newSessionId !== oldSessionId) {
      console.log('检测到会话ID变化:', oldSessionId, '->', newSessionId)
      // 更新当前会话ID
      currentSessionId.value = newSessionId as string
      // 清空当前消息
      messages.value = []
      // 加载新会话的历史
      await loadSessionHistory(newSessionId as string)
    } else if (!newSessionId && oldSessionId) {
      // 如果从有session_id变为没有，生成新的session_id
      currentSessionId.value = generateSessionId()
      console.log('生成新会话ID:', currentSessionId.value)
      messages.value = []
    }
  }
)
</script>

<template>
  <div class="chat-page" :class="{ 'chat-active': messages.length > 0 }">
    <div class="chat-container">
      <!-- 欢迎区域（有对话时隐藏） -->
      <div v-if="messages.length === 0" class="welcome-section">
        <div class="avatar-wrapper">
          <img src="../../../assets/robot.svg" alt="智言" class="avatar" />
        </div>
        <h1 class="welcome-title">我是智言小助手，很高兴见到你！</h1>
        <p class="welcome-subtitle">
          欢迎体验智言灵寻LingSeek，一位懂得完成复杂任务的Agent助理~
        </p>
      </div>

      <!-- 模式选择（有对话时隐藏） -->
      <div v-if="messages.length === 0" class="mode-selector">
        <button
          v-for="mode in modes"
          :key="mode.id"
          :class="['mode-btn', { active: selectedMode === mode.id }]"
          @click="selectMode(mode.id)"
        >
          <span class="mode-icon">{{ mode.icon }}</span>
          <span class="mode-label">{{ mode.label }}</span>
        </button>
      </div>

      <!-- 对话历史（有对话时显示在上方） -->
      <div v-if="messages.length > 0" class="chat-conversation" ref="chatConversationRef">
        <div v-for="(msg, idx) in messages" :key="idx" class="message-group">
          <!-- User Message -->
          <div v-if="msg.role === 'user'" class="user-message">
            <div class="message-content">
              <span>{{ msg.content }}</span>
            </div>
            <img :src="userStore.userInfo?.avatar || '/src/assets/user.svg'" alt="User Avatar" class="avatar" @error="handleAvatarError" />
          </div>
          
          <!-- AI Message -->
          <div v-if="msg.role === 'assistant'" class="ai-message">
            <img src="/src/assets/robot.svg" alt="AI Avatar" class="avatar" />
            <div class="message-content">
              <!-- 加载转圈器 - 仅在内容为空且正在生成时显示 -->
              <div v-if="!msg.content && isGenerating && idx === messages.length - 1" class="loading-spinner-container">
                <div class="loading-spinner"></div>
                <span class="loading-text">AI正在思考中...</span>
              </div>
              <!-- 实际内容 - 有内容时显示 -->
              <MdPreview v-if="msg.content" :editorId="'workspace-ai-' + idx" :modelValue="msg.content" />
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域（固定在底部） -->
      <div class="input-section" :class="{ 'input-fixed': messages.length > 0 }">
        <div class="input-wrapper" :class="{ 'lingseek-glow': selectedMode === 'lingseek' }">
          <textarea
            v-model="inputMessage"
            placeholder="给智言发消息，让智言帮你完成任务~"
            class="message-input"
            rows="4"
            @keydown="handleKeydown"
          ></textarea>
          
          <!-- 底部控制栏 -->
          <div class="input-footer">
            <div class="footer-left">
              <!-- 模型选择（仅日常模式显示） -->
              <div v-if="selectedMode === 'normal'" class="selector-dropdown">
                <div 
                  :class="['selector-item', { open: showModelSelector }]"
                  @click="showModelSelector = !showModelSelector"
                >
                  <img src="../../../assets/model.svg" alt="模型" class="selector-icon-img" />
                  <span class="selector-text">{{ selectedModel || (modelsLoading ? '加载中...' : '选择模型') }}</span>
                  <span class="selector-arrow">▲</span>
                </div>
                
                <!-- 模型下拉菜单 -->
                <transition name="dropdown">
                  <div v-if="showModelSelector" class="dropdown-menu model-menu">
                    <div v-if="modelsLoading" class="dropdown-empty">
                      <span class="empty-icon">⏳</span>
                      <span class="empty-text">正在加载模型...</span>
                    </div>
                    <div v-else-if="modelOptions.length === 0" class="dropdown-empty">
                      <img src="../../../assets/model.svg" alt="模型" class="empty-icon-img" />
                      <span class="empty-text">暂无可用模型</span>
                    </div>
                    <div
                      v-for="m in modelOptions"
                      :key="m.llm_id"
                      :class="['dropdown-item', { selected: selectedModelId === m.llm_id }]"
                      @click="selectModel(m.llm_id)"
                    >
                      <div class="item-left">
                        <div class="item-icon-wrapper">
                          <img src="../../../assets/model.svg" alt="模型" class="item-icon-img" />
                        </div>
                        <div class="item-content">
                          <div class="item-text">{{ m.model }}</div>
                        </div>
                      </div>
                      <div v-if="selectedModelId === m.llm_id" class="item-check-wrapper">
                        <span class="item-check">✓</span>
                      </div>
                    </div>
                  </div>
                </transition>
              </div>

              <!-- 联网搜索（仅灵寻模式显示） -->
              <div v-if="selectedMode === 'lingseek'" class="selector-dropdown">
                <div 
                  :class="['selector-item', { active: webSearchEnabled }]"
                  @click="toggleWebSearch"
                >
                  <span class="selector-icon">🌐</span>
                  <span class="selector-text">联网搜索</span>
                  <span v-if="webSearchEnabled" class="selector-check">✓</span>
                </div>
              </div>
              
              <!-- 工具选择 -->
              <div class="selector-dropdown" ref="toolDropdownRef">
                <div 
                  class="selector-item"
                  @click="showToolSelector = !showToolSelector"
                >
                  <img src="../../../assets/plugin.svg" alt="工具" class="selector-icon-img" />
                  <span class="selector-text">
                    {{ selectedTools.length > 0 ? `已选 ${selectedTools.length} 个` : '选择工具' }}
                  </span>
                  <span class="selector-arrow">▲</span>
                </div>
                
                <!-- 工具下拉菜单 -->
                <transition name="dropdown">
                  <div v-if="showToolSelector" class="dropdown-menu tool-menu">
                    <!-- 标题 -->
                    <div class="dropdown-header">
                      <span class="header-title">选择工具</span>
                      <span class="header-count">{{ plugins.length }} 个可用</span>
                    </div>

                    <!-- 工具列表 -->
                    <div class="dropdown-list">
                      <div v-if="plugins.length === 0" class="dropdown-empty">
                        <img src="../../../assets/plugin.svg" alt="工具" class="empty-icon-img" />
                        <span class="empty-text">暂无可用工具</span>
                      </div>
                      <div
                        v-for="plugin in plugins"
                        :key="plugin.id || plugin.tool_id"
                        :class="['dropdown-item', { selected: selectedTools.includes(plugin.id || plugin.tool_id) }]"
                        @click="toggleTool(plugin.id || plugin.tool_id)"
                      >
                        <div class="item-left">
                          <div class="item-icon-wrapper">
                            <img 
                              v-if="plugin.logo_url" 
                              :src="plugin.logo_url" 
                              :alt="plugin.zh_name || plugin.name"
                              class="item-icon-img"
                            />
                            <img v-else src="../../../assets/plugin.svg" alt="工具" class="item-icon-img" />
                          </div>
                          <div class="item-content">
                            <div class="item-text">{{ plugin.zh_name || plugin.name || plugin.tool_name }}</div>
                            <div class="item-desc">{{ plugin.description || '暂无描述' }}</div>
                          </div>
                        </div>
                        <div 
                          v-if="selectedTools.includes(plugin.id || plugin.tool_id)" 
                          class="item-check-wrapper"
                        >
                          <span class="item-check">✓</span>
                        </div>
                      </div>
                    </div>

                    <!-- 底部操作栏 -->
                    <div v-if="selectedTools.length > 0" class="dropdown-footer">
                      <button 
                        class="clear-btn"
                        @click.stop="selectedTools = []"
                      >
                        <span>清空</span>
                      </button>
                      <div class="selected-info">
                        <span class="selected-count">已选 {{ selectedTools.length }} 个工具</span>
                      </div>
                    </div>
                  </div>
                </transition>
              </div>

              <!-- MCP 服务器选择（紧跟工具选择后） -->
              <div class="selector-dropdown" ref="mcpDropdownRef">
                <div 
                  class="selector-item"
                  @click="showMcpSelector = !showMcpSelector"
                >
                  <img src="../../../assets/mcp.svg" alt="MCP" class="selector-icon-img" />
                  <span class="selector-text">
                    {{ selectedMcpServers.length > 0 ? `已选 ${selectedMcpServers.length} 个MCP` : '选择MCP' }}
                  </span>
                  <span class="selector-arrow">▲</span>
                </div>
                
                <!-- MCP 下拉菜单 -->
                <transition name="dropdown">
                  <div v-if="showMcpSelector" class="dropdown-menu tool-menu">
                    <!-- 标题 -->
                    <div class="dropdown-header">
                      <span class="header-title">选择MCP服务器</span>
                      <span class="header-count">{{ mcpServers.length }} 个可用</span>
                    </div>

                    <!-- 列表 -->
                    <div class="dropdown-list">
                      <div v-if="mcpServers.length === 0" class="dropdown-empty">
                        <img src="../../../assets/mcp.svg" alt="MCP" class="empty-icon-img" />
                        <span class="empty-text">暂无可用MCP服务器</span>
                      </div>
                      <div
                        v-for="mcp in mcpServers"
                        :key="mcp.mcp_server_id"
                        :class="['dropdown-item', { selected: selectedMcpServers.includes(mcp.mcp_server_id) }]"
                        @click="toggleMcp(mcp.mcp_server_id)"
                      >
                        <div class="item-left">
                          <div class="item-icon-wrapper">
                            <img 
                              v-if="mcp.logo_url" 
                              :src="mcp.logo_url" 
                              :alt="mcp.server_name"
                              class="item-icon-img"
                            />
                            <img v-else src="../../../assets/mcp.svg" alt="MCP" class="item-icon-img" />
                          </div>
                          <div class="item-content">
                            <div class="item-text">{{ mcp.server_name }}</div>
                          </div>
                        </div>
                        <div 
                          v-if="selectedMcpServers.includes(mcp.mcp_server_id)" 
                          class="item-check-wrapper"
                        >
                          <span class="item-check">✓</span>
                        </div>
                      </div>
                    </div>

                    <!-- 底部操作栏 -->
                    <div v-if="selectedMcpServers.length > 0" class="dropdown-footer">
                      <button 
                        class="clear-btn"
                        @click.stop="selectedMcpServers = []"
                      >
                        <span>清空</span>
                      </button>
                      <div class="selected-info">
                        <span class="selected-count">已选 {{ selectedMcpServers.length }} 个MCP</span>
                      </div>
                    </div>
                  </div>
                </transition>
              </div>
            </div>
            
            <div class="footer-right">
              <!-- 附件按钮 -->
              <button class="icon-btn" title="上传附件" @click="triggerFileInput">
                <img src="../../../assets/upload.svg" alt="上传" class="upload-icon" />
              </button>
              <input
                type="file"
                ref="fileInputRef"
                class="hidden-file-input"
                multiple
                @change="onFileChange"
              />
              
              <!-- 发送按钮 -->
              <button class="send-btn" :class="{ 'btn-disabled': isGenerating }" :disabled="isGenerating" @click="handleSend">
                <span v-if="!isGenerating">➤</span>
                <span v-else class="loading-spinner"></span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.chat-page {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  background: linear-gradient(180deg, #fafbfc 0%, #ffffff 100%);
  padding: 0;
  overflow-y: auto;

  &.chat-active {
    padding: 0;
    overflow: hidden;
    background-color: #f7f8fa;
  }
}

.chat-container {
  max-width: 820px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px 40px;

  .chat-active & {
    max-width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    padding: 0;
  }
}

.welcome-section {
  text-align: center;
  margin-bottom: 40px;
  animation: fadeInUp 0.6s ease;

  .avatar-wrapper {
    margin-bottom: 20px;
    display: flex;
    justify-content: center;
    position: relative;

    .avatar {
      width: 120px;
      height: 120px;
      object-fit: contain;
      transition: all 0.3s ease;
      filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.08));

      &:hover {
        transform: scale(1.05);
        filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.12));
      }
    }
  }

  .welcome-title {
    font-size: 32px;
    font-weight: 700;
    background: linear-gradient(135deg, #1f2937 0%, #4b5563 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 12px 0;
    letter-spacing: -0.5px;
  }

  .welcome-subtitle {
    font-size: 15px;
    color: #6b7280;
    margin: 0;
    line-height: 1.7;
    max-width: 500px;
    margin: 0 auto;
  }
}

.mode-selector {
  display: flex;
  gap: 14px;
  margin-bottom: 36px;
  animation: fadeInUp 0.6s ease 0.1s both;

  .mode-btn {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 24px;
    border: 2px solid #e5e7eb;
    border-radius: 24px;
    background: white;
    color: #6b7280;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);

    .mode-icon {
      font-size: 18px;
      transition: transform 0.3s ease;
    }

    .mode-label {
      font-weight: 600;
    }

    &:hover {
      border-color: #667eea;
      background: #f8f9ff;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);

      .mode-icon {
        transform: scale(1.1);
      }
    }

    &.active {
      border-color: #667eea;
      background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
      color: #667eea;
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
      transform: translateY(-2px);

      .mode-icon {
        transform: scale(1.15);
      }
    }
  }
}

// 动画
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes rotate {
  from {
    transform: translate(-50%, -50%) rotate(0deg);
  }
  to {
    transform: translate(-50%, -50%) rotate(360deg);
  }
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0) translateY(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1.2) translateY(-8px);
    opacity: 1;
  }
}

// 灵寻模式输入框外发光“呼吸”动画（淡蓝色，颜色不变，仅强弱变化）
@keyframes lingseek-breath {
  0%, 100% {
    box-shadow:
      0 0 0 2px rgba(102, 126, 234, 0.12),
      0 0 24px 10px rgba(102, 126, 234, 0.14);
  }
  50% {
    box-shadow:
      0 0 0 3px rgba(102, 126, 234, 0.22),
      0 0 44px 18px rgba(102, 126, 234, 0.22);
  }
}

@keyframes lingseek-breath-strong {
  0%, 100% {
    box-shadow:
      0 0 0 3px rgba(102, 126, 234, 0.20),
      0 0 36px 14px rgba(102, 126, 234, 0.24);
  }
  50% {
    box-shadow:
      0 0 0 4px rgba(102, 126, 234, 0.30),
      0 0 60px 24px rgba(102, 126, 234, 0.30);
  }
}

// 移除彩虹动画（不再需要）

.input-section {
  width: 100%;
  max-width: 800px;
  animation: fadeInUp 0.6s ease 0.2s both;

  &.input-fixed {
    max-width: 100%;
    padding: 10px 20px 20px 20px;
    background: #f7f8fa;
    animation: none;

    .input-wrapper {
      max-width: 900px;
      margin: 0 auto;
    }
  }

  .input-wrapper {
    background: #ffffff;
    border: 2px solid #e5e7eb;
    border-radius: 20px;
    padding: 16px 20px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    position: relative;
    z-index: 1;

    &.lingseek-glow {
      border-color: rgba(102, 126, 234, 0.35);
      box-shadow:
        0 0 0 2px rgba(102, 126, 234, 0.12),
        0 0 16px 6px rgba(102, 126, 234, 0.14);
      animation: lingseek-breath 2.8s ease-in-out infinite;

      &:focus-within {
        border-color: rgba(102, 126, 234, 0.55);
        animation: lingseek-breath-strong 2.2s ease-in-out infinite;
        transform: translateY(-2px);
      }
    }

    &:focus-within {
      border-color: #667eea;
      box-shadow: 0 6px 24px rgba(102, 126, 234, 0.15);
      transform: translateY(-2px);
    }

    .message-input {
      width: 100%;
      border: none;
      background: transparent;
      font-size: 15px;
      line-height: 1.6;
      color: #1f2937;
      resize: none;
      outline: none;
      font-family: inherit;
      min-height: 45px;
      margin-bottom: 12px;

      &::placeholder {
        color: #9ca3af;
      }
    }

    .input-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .footer-left {
        display: flex;
        gap: 10px;

          .selector-dropdown {
          position: relative;

          .selector-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 14px;
            background: #f8f9fa;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            font-size: 13px;
            color: #4b5563;
            cursor: pointer;
            transition: all 0.2s ease;
            user-select: none;

            .selector-icon {
              font-size: 16px;
            }

            .selector-icon-img {
              width: 20px;
              height: 20px;
              object-fit: contain;
              display: inline-block;
            }

            .selector-text {
              font-weight: 500;
            }

            .selector-arrow {
              font-size: 10px;
              opacity: 0.5;
              transition: transform 0.2s ease;
            }

            &.open {
              .selector-arrow {
                transform: rotate(180deg);
              }
            }

            .selector-check {
              font-size: 14px;
              color: #667eea;
              font-weight: 600;
            }

            &:hover {
              border-color: #667eea;
              background: #f0f4ff;
              color: #667eea;
            }

            &.active {
              background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
              border-color: #667eea;
              color: #667eea;
              box-shadow: 0 2px 6px rgba(102, 126, 234, 0.15);
            }

            &:active {
              transform: scale(0.98);
            }
          }

          .dropdown-menu {
            position: absolute;
            bottom: calc(100% + 8px);
            left: 0;
            min-width: 200px;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            box-shadow: 0 -10px 30px rgba(0, 0, 0, 0.15);
            z-index: 1000;
            max-height: 320px;
            overflow: hidden;
            display: flex;
            flex-direction: column;

            &.tool-menu {
              min-width: 360px;
              max-height: 450px;
            }

            // 模型下拉尺寸与工具列表保持一致
            &.model-menu {
              min-width: 180px;
              max-height: 450px;

              .dropdown-item {
                .item-content {
                  .item-text {
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                  }
                }
              }
            }

            .dropdown-header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              padding: 12px 16px;
              background: linear-gradient(135deg, #f8f9fa 0%, #f0f2f5 100%);
              border-bottom: 1px solid #e5e7eb;

              .header-title {
                font-size: 14px;
                font-weight: 600;
                color: #1f2937;
              }

              .header-count {
                font-size: 12px;
                color: #6b7280;
                background: white;
                padding: 2px 8px;
                border-radius: 10px;
                border: 1px solid #e5e7eb;
              }
            }

            .dropdown-list {
              flex: 1;
              overflow-y: auto;
              padding: 8px;

              &::-webkit-scrollbar {
                width: 8px;
              }

              &::-webkit-scrollbar-track {
                background: transparent;
              }

              &::-webkit-scrollbar-thumb {
                background: #e0e0e0;
                border-radius: 4px;

                &:hover {
                  background: #bdbdbd;
                }
              }
            }

            .dropdown-empty {
              padding: 48px 20px;
              text-align: center;
              color: #9ca3af;
              display: flex;
              flex-direction: column;
              align-items: center;
              gap: 12px;

              .empty-icon {
                font-size: 48px;
                opacity: 0.3;
              }

              .empty-icon-img {
                width: 48px;
                height: 48px;
                opacity: 0.35;
                object-fit: contain;
              }

              .empty-text {
                font-size: 14px;
                color: #6b7280;
              }
            }

            .dropdown-item {
              display: flex;
              align-items: center;
              justify-content: space-between;
              gap: 12px;
              padding: 14px 12px;
              border-radius: 10px;
              cursor: pointer;
              transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
              margin-bottom: 4px;
              border: 2px solid transparent;
              background: #fafafa;

              .item-left {
                display: flex;
                align-items: center;
                gap: 12px;
                flex: 1;
                min-width: 0;
              }

              .item-icon-wrapper {
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
                border-radius: 10px;
                flex-shrink: 0;
                transition: all 0.3s ease;
                overflow: hidden;

                .item-icon-img {
                  width: 100%;
                  height: 100%;
                  object-fit: cover;
                }

                .item-icon {
                  font-size: 20px;
                }
              }

              .item-content {
                flex: 1;
                min-width: 0;

                .item-text {
                  font-size: 15px;
                  font-weight: 600;
                  color: #1f2937;
                  margin-bottom: 4px;
                  line-height: 1.3;
                }

                .item-desc {
                  font-size: 12px;
                  color: #6b7280;
                  overflow: hidden;
                  text-overflow: ellipsis;
                  display: -webkit-box;
                  -webkit-line-clamp: 2;
                  line-clamp: 2;
                  -webkit-box-orient: vertical;
                  line-height: 1.5;
                }
              }

              .item-check-wrapper {
                width: 28px;
                height: 28px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 50%;
                flex-shrink: 0;
                box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);

                .item-check {
                  font-size: 16px;
                  color: white;
                  font-weight: 700;
                }
              }

              &:hover {
                background: #f5f7fa;
                transform: translateX(2px);
                border-color: #e5e7eb;

                .item-icon-wrapper {
                  background: linear-gradient(135deg, #e5e7eb 0%, #d1d5db 100%);
                  transform: scale(1.05);
                }
              }

              &.selected {
                background: linear-gradient(135deg, #eff6ff 0%, #e0f2fe 100%);
                border-color: #667eea;
                box-shadow: 0 2px 8px rgba(102, 126, 234, 0.12);

                .item-icon-wrapper {
                  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
                  
                  .item-icon-img {
                    filter: brightness(1.2);
                  }

                  .item-icon {
                    filter: brightness(0) invert(1);
                  }
                }

                .item-text {
                  color: #667eea;
                }
              }

              &:active {
                transform: scale(0.98) translateX(2px);
              }
            }

            .dropdown-footer {
              display: flex;
              justify-content: space-between;
              align-items: center;
              padding: 12px 16px;
              border-top: 2px solid #f0f0f0;
              background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%);

              .clear-btn {
                padding: 8px 16px;
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                font-size: 13px;
                color: #6b7280;
                cursor: pointer;
                transition: all 0.25s ease;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 6px;

                &:hover {
                  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
                  border-color: #ef4444;
                  color: #dc2626;
                  transform: translateY(-1px);
                  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.2);
                }

                &:active {
                  transform: translateY(0);
                }
              }

              .selected-info {
                display: flex;
                align-items: center;
                gap: 8px;

                .selected-count {
                  font-size: 13px;
                  color: #667eea;
                  font-weight: 600;
                  padding: 4px 12px;
                  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                  border-radius: 12px;
                  border: 1px solid #667eea;
                }
              }
            }
          }
        }
      }

      .footer-right {
        display: flex;
        gap: 10px;
        align-items: center;

        .icon-btn {
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f8f9fa;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
          font-size: 18px;

          &:hover {
            border-color: #667eea;
            background: #f0f4ff;
            transform: translateY(-1px);
          }

          &:active {
            transform: translateY(0);
          }
        }

        .hidden-file-input {
          display: none;
        }

        .upload-icon {
          width: 18px;
          height: 18px;
          object-fit: contain;
          display: block;
        }

        .send-btn {
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
          border: none;
          border-radius: 8px;
          color: white;
          cursor: pointer;
          transition: all 0.2s ease;
          font-size: 16px;
          box-shadow: 0 2px 8px rgba(59, 130, 246, 0.25);

          &:hover:not(.btn-disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(59, 130, 246, 0.35);
          }

          &:active:not(.btn-disabled) {
            transform: translateY(0);
          }

          &.btn-disabled {
            background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);
            cursor: not-allowed;
            opacity: 0.6;
          }

          .loading-spinner {
            animation: spin 1s linear infinite;
          }
        }

        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
      }
    }
  }
}

.chat-conversation {
  flex: 1;
  padding: 0;
  overflow-y: auto;
  width: 100%;
  background-color: #f7f8fa;
  scroll-behavior: smooth;  // 平滑滚动
  
  .message-group {
    margin-bottom: 20px;
    padding: 0 20px;
    
    &:first-child {
      padding-top: 20px;
    }
  }

  .ai-message {
    display: flex;
    align-items: flex-start;
    justify-content: flex-start;

    .avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      margin-right: 15px;
      flex-shrink: 0;
      border: 1px solid #eee;
    }

    .message-content {
      background-color: #ffffff;
      border-radius: 18px;
      padding: 12px 18px;
      max-width: 70%;
      color: #333;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
      word-break: break-word;

      // 加载转圈器样式
      .loading-spinner-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 4px 0;
        color: #6b7280;
        font-size: 14px;

        .loading-spinner {
          width: 16px;
          height: 16px;
          border: 2px solid #d1d5db;
          border-top: 2px solid transparent;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        .loading-text {
          font-weight: 500;
          color: #9ca3af;
        }
      }
    }
  }

  .user-message {
    display: flex;
    justify-content: flex-end;
    align-items: flex-start;

    .avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      margin-left: 12px;
      flex-shrink: 0;
      border: 1px solid #eee;
    }

    .message-content {
      display: flex;
      align-items: center;
      background: linear-gradient(135deg, #6e8efb, #a777e3);
      color: white;
      border-radius: 18px;
      padding: 12px 18px;
      max-width: 70%;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
  }
}

// 下拉菜单动画（向上展开）
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

// Override MdPreview background
:deep(.md-editor-preview-wrapper) {
    background-color: transparent !important;
}

@media (max-width: 768px) {
  .chat-page {
    padding: 40px 16px 20px;
  }

  .welcome-section {
    margin-bottom: 32px;

    .avatar-wrapper {
      .avatar {
        width: 80px;
        height: 80px;
      }
    }

    .welcome-title {
      font-size: 26px;
    }

    .welcome-subtitle {
      font-size: 14px;
    }
  }

  .mode-selector {
    margin-bottom: 28px;
    
    .mode-btn {
      padding: 10px 18px;
      font-size: 13px;
    }
  }

  .input-section {
    .input-wrapper {
      padding: 18px;

      .input-footer {
        .footer-left {
          flex-wrap: wrap;
        }
      }
    }
  }
}
</style>

