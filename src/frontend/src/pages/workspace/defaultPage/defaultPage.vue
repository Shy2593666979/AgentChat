<script setup lang="ts">
import { modelDisplayName } from "../../../utils/model-display";
import { ref, computed, onMounted, onBeforeUnmount, watch, inject, type Ref } from 'vue'
import UiIcon from '../../../components/UiIcon.vue'
import UserAvatar from '../../../components/UserAvatar.vue'
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
const workspaceSessions = inject<Ref<any[]>>('workspaceSessions', ref([]))
const openWorkspaceSession = inject<(id: string) => void>('openWorkspaceSession', () => {})
const deleteWorkspaceSession = inject<(id: string, event: Event) => void>('deleteWorkspaceSession', () => {})
const showAllSessions = ref(false)
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
        selectedModel.value = modelDisplayName(modelOptions.value[0])
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
    selectedModel.value = modelDisplayName(model)
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
  <div class="chat-page converted-workspace-chat" :class="{ 'chat-active': messages.length > 0 }">
    <div class="chat-container"><svg style="position:absolute;width:0;height:0;overflow:hidden" class="svg-library" xmlns="http://www.w3.org/2000/svg"><defs>
<symbol id="i-home" viewBox="0 0 24 24"><path d="M2 10.3 12 2l10 8.3v1.2h-3V22h-5v-7h-4v7H5V11.5H2Z" fill="currentColor" stroke="currentColor" stroke-width="1.2"/><path d="M10 22v-7h4v7" stroke="#e5f1ff" stroke-width="1.7"/></symbol>
<symbol id="i-search" viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="7.5"/><path d="m16 16 5 5"/></symbol>
<symbol id="i-chat" viewBox="0 0 24 24"><path d="M21.5 11.5a9.5 9.5 0 0 1-9.5 9.5 10 10 0 0 1-4.5-1L2 21l1.4-5A9.5 9.5 0 1 1 21.5 11.5Z"/><circle cx="7.5" cy="11" r=".6" fill="currentColor"/><circle cx="12" cy="11" r=".6" fill="currentColor"/><circle cx="16.5" cy="11" r=".6" fill="currentColor"/></symbol>
<symbol id="i-robot" viewBox="0 0 24 24"><path d="M12 3v3M9 3h3"/><rect x="2.5" y="6.5" width="19" height="16" rx="5"/><path d="M8 12v1M16 12v1M9 18h6"/></symbol>
<symbol id="i-link" viewBox="0 0 24 24"><path d="m9.5 15 5-5M7 9l-3 3a5 5 0 0 0 7 7l3-3M10 8l3-3a5 5 0 0 1 7 7l-3 3"/></symbol>
<symbol id="i-cube" viewBox="0 0 24 24"><path d="m12 2 9 5v12l-9 5-9-5V7Zm0 10L3 7m9 5 9-5m-9 5v12" transform="translate(0 -1)"/></symbol>
<symbol id="i-book" viewBox="0 0 24 24"><path d="M12 5C9 2 5 2 2 3v17c4-1.5 7-1 10 1 3-2 6-2.5 10-1V3c-3-1-7-1-10 2Zm0 0v16"/></symbol>
<symbol id="i-chart" viewBox="0 0 24 24"><path d="M4 20v-9M12 20V3M20 20V8" stroke-width="2.6"/></symbol>
<symbol id="i-grid" viewBox="0 0 24 24"><rect x="2.5" y="2.5" width="7.5" height="7.5" rx="3.5"/><rect x="14" y="2.5" width="7.5" height="7.5" rx="3.5"/><rect x="2.5" y="14" width="7.5" height="7.5" rx="3.5"/><rect x="14" y="14" width="7.5" height="7.5" rx="3.5"/></symbol>
<symbol id="i-layers" viewBox="0 0 24 24"><path d="m12 2 10 6-10 6L2 8Zm-10 11 10 6 10-6M2 18l10 6 10-6" transform="translate(0 -1)"/></symbol>
<symbol id="i-chevron" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></symbol>
<symbol id="i-right" viewBox="0 0 24 24"><path d="m9 4 7 8-7 8"/></symbol>
<symbol id="i-collapse" viewBox="0 0 24 24"><path d="m11 5-7 7 7 7m7-14-7 7 7 7"/></symbol>
<symbol id="i-bell" viewBox="0 0 24 24"><path d="M4 18h16c-2-3-2-5-2-8a6 6 0 0 0-12 0c0 3 0 5-2 8ZM10 21a2 2 0 0 0 4 0M12 2v1"/></symbol>
<symbol id="i-paperclip" viewBox="0 0 24 24"><path d="m8 14 7-7a3 3 0 0 1 4 4l-8 8a5 5 0 0 1-7-7l9-9a3.5 3.5 0 0 1 5 5L9 17a2 2 0 0 1-3-3l7-7"/></symbol>
<symbol id="i-globe" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9.5"/><ellipse cx="12" cy="12" rx="4.5" ry="9.5"/><path d="M3 8h18M3 16h18"/></symbol>
<symbol id="i-send" viewBox="0 0 24 24"><path d="M21.5 3 15 21l-4-8-8-4ZM11 13l6-6"/></symbol>
<symbol id="i-check" viewBox="0 0 24 24"><path d="m5 12 5 5 9-10"/></symbol>
<symbol id="i-more" viewBox="0 0 24 24"><circle cx="5" cy="12" r="1.5" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none"/><circle cx="19" cy="12" r="1.5" fill="currentColor" stroke="none"/></symbol>
<symbol id="i-close" viewBox="0 0 24 24"><path d="m6 6 12 12M6 18 18 6"/></symbol>
<symbol id="f-research" viewBox="0 0 64 64"><circle cx="27" cy="27" r="17" fill="#04cc7b"/><circle cx="27" cy="27" r="10.5" fill="#fff"/><path d="m39 39 15 15" stroke="#02c775" stroke-width="7"/><path d="M16 21a13 13 0 0 1 22-4" stroke="#97f7c9" stroke-width="2" fill="none"/></symbol>
<symbol id="f-document" viewBox="0 0 64 64"><path d="M13 8h25l13 13v31a4 4 0 0 1-4 4H13a4 4 0 0 1-4-4V12a4 4 0 0 1 4-4Z" fill="currentColor"/><path d="M38 8v13h13" fill="#b98aff"/><path d="M18 22h13M18 30h20M18 38h12" stroke="white" stroke-width="2.8" stroke-linecap="round"/><path d="m34 48 15-16a3 3 0 0 1 4 0l4 4a3 3 0 0 1 0 4L41 55l-9 2Z" fill="currentColor" stroke="#f4edff" stroke-width="3"/><path d="m48 34 7 7" stroke="white" stroke-width="2"/></symbol>
<symbol id="f-chart" viewBox="0 0 64 64"><rect x="9" y="33" width="9" height="23" rx="3" fill="currentColor"/><rect x="25" y="20" width="9" height="36" rx="3" fill="currentColor"/><rect x="41" y="7" width="9" height="49" rx="3" fill="currentColor"/><path d="M11 36v16M27 23v29M43 10v42" stroke="#ffc36b" stroke-width="1.5" stroke-linecap="round"/></symbol>
<symbol id="f-file" viewBox="0 0 32 32"><path d="M8 3h11l7 7v16a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V6a3 3 0 0 1 3-3Z" fill="currentColor"/><path d="M19 3v7h7" fill="#fff" opacity=".35"/><path d="M10 13h6m-6 5h11m-11 5h8" stroke="white" stroke-width="1.5" stroke-linecap="round"/><path d="M7 6v18" stroke="white" opacity=".25"/></symbol>
<symbol id="f-folder" viewBox="0 0 32 32"><path d="M3 8a3 3 0 0 1 3-3h7l3 4h10a3 3 0 0 1 3 3v14a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3Z" fill="currentColor"/><path d="M6 13h20" stroke="white" stroke-width="2"/><path d="M5 10V7h8" fill="none" stroke="#fff" opacity=".5"/></symbol>
<symbol id="f-calendar" viewBox="0 0 32 32"><rect x="4" y="6" width="24" height="23" rx="3" fill="currentColor"/><path d="M10 3v7M22 3v7" stroke="currentColor" stroke-width="3" stroke-linecap="round"/><path d="M7 14h18v12H7Z" fill="white"/><rect x="16" y="17" width="6" height="6" rx="1.5" fill="currentColor"/></symbol>
</defs></svg>
      <!-- 欢迎区域（有对话时隐藏） -->
      <header v-if="messages.length===0" class="welcome-section workspace-header"><h1>工作台</h1><p>描述目标，开始执行任务。</p></header>

      <!-- 模式选择（有对话时隐藏） -->
      <!-- 对话历史（有对话时显示在上方） -->
      <div v-if="messages.length > 0" class="chat-conversation" ref="chatConversationRef">
        <div v-for="(msg, idx) in messages" :key="idx" class="message-group">
          <!-- User Message -->
          <div v-if="msg.role === 'user'" class="user-message">
            <div class="message-content">
              <span>{{ msg.content }}</span>
            </div>
            <UserAvatar class="avatar" :username="userStore.userInfo?.username" :src="userStore.userInfo?.avatar"/>
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
            placeholder="描述你的任务，例如：调研 AI 陪伴产品，整理一份研究简报。"
            class="message-input"
            rows="4"
            @keydown="handleKeydown"
          ></textarea>

          <!-- 底部控制栏 -->
          <div class="input-footer">
            <div class="footer-left">
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
                          <div class="item-text">{{ modelDisplayName(m) }}</div>
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
                              :alt="plugin.display_name"
                              class="item-icon-img"
                            />
                            <img v-else src="../../../assets/plugin.svg" alt="工具" class="item-icon-img" />
                          </div>
                          <div class="item-content">
                            <div class="item-text">{{ plugin.display_name }}</div>
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

      <div v-if="messages.length === 0" class="p-workspace-landing">



<section class="quick-grid" aria-label="快捷任务">
<button class="quick-card" @click="selectedMode='lingseek';inputMessage='请帮我围绕这个主题进行深度研究，整理资料、关键洞察和结论。'"><span class="feature-icon green"><svg><use href="#f-research"/></svg></span><span class="quick-copy"><h2>深度调研</h2><p>帮你进行专业的深度研究，<br>从海量信息中提炼关键洞察与结论</p></span><svg class="icon quick-arrow"><use href="#i-right"/></svg></button>
<button class="quick-card" @click="selectedMode='lingseek';inputMessage='请帮我创作一份结构清晰、内容完整的文章或报告。'"><span class="feature-icon purple"><svg><use href="#f-document"/></svg></span><span class="quick-copy"><h2>内容创作</h2><p>辅助你进行各类内容创作，<br>包括文章、报告、邮件等</p></span><svg class="icon quick-arrow"><use href="#i-right"/></svg></button>
<button class="quick-card" @click="selectedMode='lingseek';inputMessage='请帮我分析这份数据，解释关键变化并给出可执行的建议。'"><span class="feature-icon orange"><svg><use href="#f-chart"/></svg></span><span class="quick-copy"><h2>数据分析</h2><p>帮你分析和解读数据，<br>生成图表、洞察和分析报告</p></span><svg class="icon quick-arrow"><use href="#i-right"/></svg></button>
</section>
        <div class="p-section-heading"><h2>最近任务</h2><button class="p-btn" @click="showAllSessions = !showAllSessions">{{ showAllSessions ? '收起记录' : '全部任务' }}</button></div>
        <div class="p-recent-table"><table><thead><tr><th>会话</th><th>模式</th><th>记录</th><th>最近更新</th><th>操作</th></tr></thead><tbody><tr v-for="session in (showAllSessions ? workspaceSessions : workspaceSessions.slice(0, 4))" :key="session.sessionId"><td><div class="p-table-name"><UiIcon class="p-tile" name="chat" /><span>{{ session.title }}<small>个人工作空间</small></span></div></td><td><span class="p-tag">{{ session.agent === 'simple' ? '日常模式' : '灵寻 LingSeek' }}</span></td><td>{{ session.contexts?.length || 0 }} 条</td><td>{{ new Date(session.createTime).toLocaleDateString('zh-CN') }}</td><td><div class="p-row-actions"><button class="p-btn" @click="openWorkspaceSession(session.sessionId)">→ 继续</button><button class="p-delete" title="删除会话" @click="deleteWorkspaceSession(session.sessionId, $event)">×</button></div></td></tr><tr v-if="!workspaceSessions.length"><td colspan="5" class="p-empty-inline">还没有任务记录，从上方输入框开始新的想法。</td></tr></tbody></table></div>

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


<style scoped>

.converted-workspace-chat{--ink:#0b1749;--muted:#69789f;--blue:#1467ff;--line:#e8f1fe;--sidebar:264px}*{box-sizing:border-box}.converted-workspace-chat{margin:0;color:var(--ink);font-family:Inter,"Noto Sans SC",sans-serif;background:#f8fcff;font-size:16px}button,input,textarea,select{font:inherit}button{cursor:pointer}button,a,input,textarea{outline:none}button:focus-visible,a:focus-visible{outline:3px solid #93bcff;outline-offset:3px}svg{display:block;flex-shrink:0}.icon{width:26px;height:26px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}button{color:inherit}a{color:inherit;text-decoration:none}.svg-library{position:absolute;width:0;height:0;overflow:hidden}.sidebar{position:fixed;z-index:5;inset:0 auto 0 0;width:var(--sidebar);padding:19px 16px 22px;background:linear-gradient(110deg,#f8fcff 0%,#f6fbff 100%);border-right:1px solid #e5f0ff;box-shadow:4px 0 18px #c4e2ff2b;display:flex;flex-direction:column;transition:width .2s}.brand{display:flex;align-items:center;gap:14px;padding:0 13px;margin-bottom:24px;white-space:nowrap}.brand-logo{height:45px;width:45px;display:grid;place-items:center;color:white;background:linear-gradient(140deg,#1a70ff,#0759f7);box-shadow:0 4px 10px #207aff24,inset 0 0 6px #80aaff;border-radius:11px;position:relative}.brand-logo:after{content:"";width:6px;height:6px;border-radius:50%;background:#b7d9ff;position:absolute;right:8px;top:9px}.brand-logo svg{width:31px;height:31px}.brand-name{font-size:24px;font-weight:700;letter-spacing:1px}.navigation{display:flex;flex-direction:column;gap:1px}.nav-item{display:flex;align-items:center;width:100%;height:54px;gap:22px;padding:0 23px;border:0;border-radius:14px;background:transparent;font-size:20px;text-align:left;white-space:nowrap}.nav-item .icon{width:28px;height:28px}.nav-item:hover{background:#ecf5ff}.nav-item.active{color:#0864ff;background:#e5f1ff;font-weight:500}.nav-item .nav-chevron{margin-left:auto;width:18px;height:18px}.nav-label{color:#69789b;font-size:16px;margin:22px 13px 4px}.nav-label.second{margin-top:24px}.nav-label.third{margin-top:29px;margin-bottom:10px}.collapse-button{display:flex;align-items:center;gap:22px;margin-top:auto;border:0;background:none;padding:12px 22px;color:#53628b;font-size:18px;white-space:nowrap}.collapse-button .icon{width:23px;height:23px}.mcp-submenu{display:none;padding:0 0 5px 73px;color:var(--muted);font-size:14px}.mcp-submenu.open{display:block}.mcp-submenu button{border:0;background:none;padding:8px 0;color:inherit}.main{margin-left:var(--sidebar);min-height:100vh;position:relative;padding:0 27px 20px 26px;background:radial-gradient(ellipse at 46% -20%,#d7ecffbb 0,transparent 53%),linear-gradient(180deg,#f2f9ff 0,#fbfdff 55%,#f9fcff 100%);transition:margin-left .2s}.header-art{position:absolute;top:0;right:0;width:740px;height:163px;pointer-events:none;opacity:.68;overflow:hidden}.header-art svg{width:100%;height:100%}.workspace-header{height:124px;position:relative;display:flex;justify-content:space-between;align-items:flex-start;padding:34px 9px 0}.workspace-header h1{font-size:30px;line-height:43px;margin:0;font-weight:700;letter-spacing:.3px}.workspace-header p{font-size:18px;line-height:27px;color:#52618d;margin:3px 0 0}.account{display:flex;align-items:center;gap:29px;margin-top:-14px}.bell{width:30px;height:42px;background:transparent;border:0;display:grid;place-items:center}.bell .icon{width:25px;height:25px}.profile{display:flex;gap:10px;align-items:center;border:0;background:transparent;padding:0;font-size:17px;position:relative}.avatar{width:41px;height:41px;border-radius:50%;background:#d3e9ff;display:grid;place-items:center;overflow:hidden}.avatar svg{width:36px;height:36px}.profile .icon{width:17px;height:17px}.panel{border:1px solid var(--line);background:#ffffffed;border-radius:17px;box-shadow:0 4px 13px #adcfff12}.input-wrapper{padding:20px;height:206px;position:relative}.input-textarea{display:block;width:100%;height:107px;resize:none;background:#ffffff80;border:1px solid #d8e4f7;border-radius:12px;color:var(--ink);padding:17px 20px;font-size:20px;line-height:29px;box-shadow:inset 0 0 1px #bad0ee}.input-textarea::placeholder{color:#67779f;opacity:1}.input-textarea:focus{border-color:#7eafff;box-shadow:0 0 0 2px #eff5ff}.composer-actions{display:flex;align-items:center;justify-content:space-between;margin-top:11px;gap:12px}.tool-buttons{display:flex;align-items:center;gap:11px}.outline-button{display:flex;align-items:center;justify-content:center;gap:11px;height:45px;border:1px solid #d8e4f7;background:#fff;border-radius:12px;padding:0 18px;font-size:17px;white-space:nowrap;box-shadow:0 1px 2px #c8daf90a}.outline-button .icon{width:23px;height:23px}.outline-button:hover,.outline-button.selected{background:#edf5ff;border-color:#a7c7ff;color:#1263f2}.execute{display:flex;align-items:center;justify-content:center;gap:12px;width:174px;height:49px;border:1px solid #1a6bff;border-radius:12px;background:linear-gradient(115deg,#0860ff,#176fff);color:white;font-size:18px;font-weight:500;box-shadow:inset 0 0 7px #5890ff}.execute .icon{width:26px;height:26px}.execute:hover{background:#0759ec}.quick-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:18px}.quick-card{height:139px;display:flex;align-items:flex-start;text-align:left;padding:22px 24px;border:1px solid var(--line);background:#ffffffed;border-radius:17px;box-shadow:0 4px 13px #adcfff12;gap:22px;position:relative;transition:transform .15s,border-color .15s}.quick-card:hover{border-color:#b7d5ff;transform:translateY(-2px)}.feature-icon{width:80px;height:80px;flex-shrink:0;border-radius:17px;display:grid;place-items:center}.feature-icon.green{background:linear-gradient(135deg,#e5fff1,#e5fbed);color:#00c97a}.feature-icon.purple{background:linear-gradient(135deg,#f1ebff,#eee8ff);color:#8b45ff}.feature-icon.orange{background:linear-gradient(135deg,#fff0dd,#ffedd8);color:#ff990b}.feature-icon svg{width:52px;height:52px}.quick-copy{min-width:0;align-self:flex-start;padding-top:3px}.quick-copy h2{font-size:20px;font-weight:700;line-height:29px;margin:0 0 7px}.quick-copy p{font-size:16px;line-height:24px;color:#647399;margin:0;white-space:nowrap;letter-spacing:-.2px}.quick-arrow{position:absolute;right:26px;top:36px;color:#7283aa;width:17px;height:21px;stroke-width:1.6}.recent{margin-top:18px;padding:19px 24px 21px;min-height:418px}.recent-header{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:10px}.recent h2{font-size:24px;line-height:34px;margin:0;font-weight:700}.filters{display:flex;align-items:center;gap:11px}.search-box{width:317px;height:45px;display:flex;align-items:center;gap:11px;border:1px solid #d8e4f7;border-radius:12px;padding:0 15px;background:#fff}.search-box .icon{width:24px;height:24px}.search-box input{border:0;background:transparent;width:100%;min-width:0;font-size:16px;color:var(--ink)}.search-box input::placeholder{color:#7280a4;opacity:1}.status-select{position:relative;width:153px;height:45px}.status-select select{appearance:none;width:100%;height:100%;background:#fff;border:1px solid #d8e4f7;border-radius:12px;padding:0 35px 0 17px;color:var(--ink);font-size:17px;cursor:pointer}.status-select .icon{position:absolute;right:16px;top:15px;width:17px;height:17px;pointer-events:none}.task-table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:16px}.task-table col:nth-child(1){width:37.4%}.task-table col:nth-child(2){width:25%}.task-table col:nth-child(3){width:21.2%}.task-table col:nth-child(4){width:16.4%}.task-table thead{height:46px;background:#f2f7fc}.task-table th{text-align:left;font-weight:500;color:#50618c;padding:10px 0}.task-table th:first-child{border-radius:10px 0 0 10px;padding-left:21px}.task-table th:last-child{border-radius:0 10px 10px 0}.task-table td{height:55px;border-bottom:1px solid #e5edf9;padding:0}.task-table td:first-child{padding-left:20px}.task-name{display:flex;align-items:center;gap:23px;font-size:17px;font-weight:500;white-space:nowrap}.task-icon{height:40px;width:40px;border-radius:11px;display:grid;place-items:center;flex-shrink:0}.task-icon svg{width:26px;height:26px}.task-icon.blue{background:linear-gradient(135deg,#e5f1ff,#e2efff);color:#076bff}.task-icon.purple{background:#f0eaff;color:#8e45ff}.task-icon.orange{background:#ffeed8;color:#ff9400}.task-icon.green{background:#e2fff0;color:#00c97b}.date{color:#7181a8;font-size:16px;white-space:nowrap}.status-pill{display:inline-flex;align-items:center;gap:12px;background:#e5fff1;color:#00bc72;border-radius:30px;padding:7px 16px;font-size:16px;line-height:22px;white-space:nowrap}.status-pill .check{width:18px;height:18px;background:#04c77b;border-radius:50%;color:#fff;display:grid;place-items:center}.status-pill .check svg{width:13px;height:13px;stroke-width:2.3}.status-pill.running{background:#eaf3ff;color:#1767df}.status-pill.running .check{background:#317aec}.row-actions{display:flex;align-items:center;gap:33px}.view-button{background:#eaf4ff;color:#0767ff;border:0;border-radius:12px;height:37px;width:101px;font-size:16px;font-weight:500}.view-button:hover{background:#daebff}.more-button{width:36px;height:35px;display:grid;place-items:center;background:transparent;border:0}.more-button .icon{width:22px;height:22px}.empty{padding:45px;text-align:center;color:var(--muted);display:none}.popover{position:fixed;z-index:15;background:white;border:1px solid #dce9fa;border-radius:12px;box-shadow:0 8px 35px #203e7020;padding:9px;min-width:160px}.popover button{display:block;width:100%;padding:10px 13px;background:none;border:0;border-radius:7px;text-align:left;font-size:15px}.popover button:hover{background:#eff6ff}.popover p{font-size:14px;padding:8px;margin:0;color:var(--muted)}.toast{position:fixed;bottom:28px;left:calc(50% + 100px);transform:translate(-50%,15px);padding:13px 22px;background:#fff;color:#1b396b;border:1px solid #dce9fb;box-shadow:0 6px 25px #264c7522;border-radius:12px;z-index:30;opacity:0;pointer-events:none;transition:.2s}.toast.show{opacity:1;transform:translate(-50%,0)}.modal-backdrop{position:fixed;inset:0;background:#16335344;backdrop-filter:blur(3px);display:none;align-items:center;justify-content:center;z-index:25;padding:20px}.modal-backdrop.open{display:flex}.modal{width:min(540px,100%);border-radius:18px;background:#fff;padding:28px;box-shadow:0 15px 60px #203d7522}.modal-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}.modal-top h2{margin:0;font-size:23px}.close-button{border:0;background:#f1f6fd;width:32px;height:32px;border-radius:8px;display:grid;place-items:center}.close-button .icon{width:19px;height:19px}.modal p{color:var(--muted);line-height:1.8}.modal .detail-line{display:flex;gap:20px;margin:14px 0;font-size:16px}.modal .detail-line>span:first-child{color:var(--muted);width:70px}.knowledge-option{display:flex;align-items:center;gap:12px;padding:13px;background:#f5f9ff;margin:10px 0;border-radius:10px}.modal-footer{display:flex;justify-content:flex-end;margin-top:24px}.modal-footer .execute{height:42px;width:100px;font-size:16px}.attached-name{font-size:13px;color:#1870f3;margin-left:8px;max-width:130px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.sidebar-collapsed{--sidebar:86px}.sidebar-collapsed .sidebar{padding-left:12px;padding-right:12px}.sidebar-collapsed .brand{padding:0 8px}.sidebar-collapsed .brand-name,.sidebar-collapsed .nav-text,.sidebar-collapsed .nav-label,.sidebar-collapsed .nav-chevron,.sidebar-collapsed .collapse-button span{display:none}.sidebar-collapsed .nav-item{padding:0;justify-content:center}.sidebar-collapsed .navigation{gap:7px}.sidebar-collapsed .nav-item:nth-of-type(2),.sidebar-collapsed .nav-item:nth-of-type(7),.sidebar-collapsed .nav-item:nth-of-type(9){margin-top:16px}.sidebar-collapsed .collapse-button{justify-content:center;padding:12px}.sidebar-collapsed .collapse-button svg{transform:rotate(180deg)}
@media(min-width:1700px){.main{padding-right:32px}.quick-copy p{font-size:17px}}
@media(max-width:1400px){.converted-workspace-chat{--sidebar:236px}.sidebar{padding-left:13px;padding-right:13px}.nav-item{padding-left:21px;gap:18px}.brand{padding-left:9px;gap:12px}.brand-name{font-size:23px}.main{padding-left:22px;padding-right:22px}.quick-card{padding:20px;gap:16px}.feature-icon{width:65px;height:65px}.quick-copy h2{font-size:19px}.quick-copy p{font-size:14px;line-height:22px}.quick-arrow{right:16px}.recent{padding-left:20px;padding-right:20px}.task-name{gap:14px;font-size:15px}.date{font-size:14px}.row-actions{gap:12px}.view-button{width:80px}.search-box{width:275px}}
@media(max-width:1100px){.converted-workspace-chat{--sidebar:200px}.brand-name{font-size:20px}.brand{gap:10px;padding-left:3px}.brand-logo{width:40px;height:40px}.nav-item{padding:0 16px;gap:14px;font-size:18px}.main{padding-left:18px;padding-right:18px}.quick-card{gap:12px;padding:18px 14px}.feature-icon{width:53px;height:60px}.feature-icon svg{width:42px;height:42px}.quick-copy h2{font-size:17px}.quick-copy p{font-size:12px}.quick-arrow{right:10px;width:13px}.recent{padding:18px 15px}.task-name{font-size:14px;gap:10px}.task-table td:first-child{padding-left:10px}.task-table th:first-child{padding-left:10px}.task-icon{width:32px;height:34px}.status-pill{font-size:13px;gap:6px;padding:6px 10px}.date{font-size:12px}.view-button{width:60px;font-size:14px}.row-actions{gap:4px}.search-box{width:225px}.status-select{width:132px}.task-table col:nth-child(1){width:37%}.task-table col:nth-child(2){width:25%}.task-table col:nth-child(3){width:21%}.task-table col:nth-child(4){width:17%}}
@media(max-width:760px){.converted-workspace-chat{--sidebar:72px}.sidebar{padding:17px 9px 18px}.brand{padding:0 6px;margin-bottom:24px}.brand-logo{width:40px;height:40px;border-radius:10px}.brand-name,.nav-text,.nav-label,.nav-chevron,.collapse-button span{display:none}.nav-item{padding:0;justify-content:center;height:49px;border-radius:11px}.nav-item .icon{width:25px;height:25px}.navigation{gap:5px}.nav-item:nth-of-type(2),.nav-item:nth-of-type(7),.nav-item:nth-of-type(9){margin-top:15px}.collapse-button{padding:10px;justify-content:center}.main{padding:0 14px 20px}.workspace-header{height:118px;padding:26px 0 0}.workspace-header h1{font-size:26px;line-height:37px}.workspace-header p{font-size:13px;line-height:22px;max-width:180px;margin-top:5px}.account{gap:9px;margin-top:-9px}.profile{gap:4px}.profile .user-name,.profile>.icon{display:none}.avatar{width:33px;height:33px}.avatar svg{width:30px;height:30px}.bell .icon{width:21px;height:21px}.header-art{width:380px;opacity:.4}.input-wrapper{height:auto;padding:12px;border-radius:14px}.input-textarea{height:125px;font-size:16px;padding:13px;line-height:26px}.composer-actions{flex-wrap:wrap;gap:12px;margin-top:12px}.tool-buttons{gap:6px;width:100%;justify-content:space-between}.outline-button{height:37px;flex:1;min-width:0;gap:4px;padding:0 5px;font-size:11px;border-radius:9px}.outline-button .icon{width:17px;height:17px}.execute{width:100%;height:42px;font-size:16px;border-radius:9px}.execute .icon{width:22px;height:22px}.quick-grid{grid-template-columns:1fr;gap:10px;margin-top:14px}.quick-card{height:auto;min-height:106px;min-width:0;width:100%;align-items:center;padding:14px 16px;gap:12px;border-radius:14px}.feature-icon{width:60px;height:60px;border-radius:13px}.feature-icon svg{width:43px;height:43px}.quick-copy h2{font-size:17px;line-height:24px;margin-bottom:4px}.quick-copy p{font-size:12px;line-height:19px;white-space:normal}.quick-copy p br{display:none}.quick-copy{padding-right:5px;align-self:center}.quick-arrow{right:15px;top:28px;width:16px}.recent{margin-top:14px;padding:15px 12px;min-height:0;border-radius:14px}.recent-header{display:block;margin-bottom:13px}.recent h2{font-size:20px;margin-bottom:12px}.filters{gap:7px}.search-box{width:auto;flex:1;height:38px;padding:0 9px;gap:6px;min-width:0;border-radius:9px}.search-box .icon{width:18px;height:18px}.search-box input{font-size:12px}.status-select{width:93px;height:38px;flex-shrink:0}.status-select select{padding:0 23px 0 8px;font-size:12px;border-radius:9px}.status-select .icon{width:13px;height:13px;right:8px;top:13px}.task-table thead{display:none}.task-table,.task-table t.converted-workspace-chat{display:block}.task-table tr{position:relative;display:flex;flex-wrap:wrap;padding:12px 0;gap:7px;border-bottom:1px solid #e5edf9}.task-table td{display:block;height:auto;border:0}.task-table td:first-child{padding:0;width:calc(100% - 47px);order:1}.task-name{gap:9px;font-size:13px;white-space:normal;line-height:22px}.task-icon{width:31px;height:32px;border-radius:8px}.task-icon svg{width:22px;height:22px}.task-table td:nth-child(2){order:3;padding-left:40px;font-size:9px;line-height:22px;width:calc(100% - 92px)}.task-table td:nth-child(3){order:4;width:85px;display:flex;justify-content:flex-end}.status-pill{padding:3px 6px;font-size:10px;gap:4px;line-height:16px}.status-pill .check{width:13px;height:13px}.status-pill .check svg{width:10px;height:10px}.task-table td:last-child{order:2;width:40px;margin-left:auto}.row-actions{gap:0}.view-button{font-size:11px;width:40px;height:29px;border-radius:7px}.more-button{display:none}.toast{left:50%;width:max-content;max-width:85%;font-size:13px;text-align:center}.mcp-submenu.open{display:none}.sidebar-collapsed{--sidebar:0px}.sidebar-collapsed .sidebar{transform:translateX(-100%)}.sidebar-collapsed .main{margin-left:0}.sidebar-collapsed .workspace-header h1{cursor:pointer}.attached-name{display:none}.modal{padding:21px}.modal-top h2{font-size:20px}}
.converted-workspace-chat.chat-page{background:linear-gradient(180deg,#edf6ff,white 400px);font-family:var(--ac-font);height:100%;min-height:0;align-items:stretch}.converted-workspace-chat .chat-container{max-width:100%;width:100%;padding:26px 32px 40px;min-height:100%;margin:0;background:transparent}.workspace-header{display:block;text-align:left;padding:0;margin:0 0 24px;min-height:70px}.workspace-header h1{font-size:30px;color:#1f3555;margin:0 0 8px}.workspace-header p{font-size:15px;color:#879bb8;margin:0}.input-wrapper{border:1px solid #dfe9f9;border-radius:17px;background:white;box-shadow:0 10px 24px #457ab50b;padding:20px}.input-wrapper.lingseek-glow{border:1px solid #c8dcff;box-shadow:0 8px 24px #3777d910}.input-wrapper:before,.input-wrapper:after{display:none}.input-textarea{font-family:var(--ac-font);font-size:16px;color:#5a759c;background:white;line-height:1.8;min-height:105px}.bottom-actions{border-top:1px solid #eef3fb;margin-top:14px;padding-top:13px}.mode-btn,.function-btn{border:1px solid #dfe8f8;background:#f8fbff;color:#5575a0;border-radius:10px}.mode-btn.active{background:#eaf2ff;border-color:#c9ddff;color:#246bff}.send-btn{background:#246bff!important;border:0;border-radius:12px;padding:11px 22px;color:white}.p-workspace-landing{margin-top:20px}.quick-grid{margin:20px 0 24px;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.quick-card{background:white;border:1px solid #e0eafa;border-radius:16px;display:flex;text-align:left;padding:22px 20px;gap:16px;min-height:130px;align-items:center}.feature-icon{width:64px;height:64px;border-radius:15px;display:grid;place-items:center;flex-shrink:0;background:#e8f9ef}.feature-icon svg{width:44px;height:44px}.feature-icon.purple{background:#f0eaff}.feature-icon.orange{background:#fff0dd}.quick-copy h2{font-size:17px;margin:0 0 8px;color:#2a4264}.quick-copy p{font-size:13px;color:#879dbb;line-height:1.7;margin:0}.quick-arrow{width:18px;height:18px;color:#8ca1c0;margin-left:auto}.p-section-heading{display:flex;justify-content:space-between;align-items:center;border:1px solid #e1eafa;border-bottom:0;border-radius:16px 16px 0 0;background:white;padding:20px 22px;margin-bottom:0}.p-section-heading h2{font-size:20px;color:#233b5d;margin:0}.p-recent-table{border:1px solid #e1eafa;border-top:0;border-radius:0 0 16px 16px;background:white;overflow:auto;padding:0 22px 20px}.p-recent-table table{min-width:650px}.p-recent-table th{background:#f3f8ff;color:#6981a4;font-size:13px;padding:13px 16px}.p-recent-table td{font-size:14px;padding:16px;color:#506c93;border-bottom:1px solid #edf2fa}.p-recent-table .p-tile{width:36px;height:36px}.p-table-name small{font-size:11px;color:#97abc5}.p-tag{background:#edf4ff;color:#6088c4;border:1px solid #dde9fb;border-radius:20px;padding:4px 10px;font-size:11px}.chat-active .chat-container{height:100%;padding-bottom:18px;min-height:0}.chat-active .chat-conversation{flex:1;min-height:0;padding-top:15px}.user-message .message-content{background:#e7f1ff;color:#38557b;border-radius:14px}.ai-message .message-content{background:white;border:1px solid #e1eafa;border-radius:14px;padding:18px;max-width:calc(100% - 50px)}.selector-dropdown{border:1px solid #dde8fa;border-radius:13px;box-shadow:0 10px 30px #203d6320;background:white}.ai-message :deep(.md-editor){font-family:var(--ac-font);background:transparent;color:#3c567b}@media(max-width:1100px){.quick-grid{grid-template-columns:1fr}.quick-card{min-height:105px;padding:18px}.quick-copy p br{display:none}.quick-copy h2{font-size:16px}}@media(max-width:700px){.converted-workspace-chat .chat-container{padding:22px 16px}.workspace-header h1{font-size:26px}.workspace-header p{font-size:13px}.input-wrapper{padding:14px}.input-textarea{font-size:14px}.feature-icon{width:48px;height:48px}.feature-icon svg{width:34px;height:34px}.quick-card{gap:12px}.quick-copy h2{font-size:15px}.quick-copy p{font-size:12px}.p-section-heading{padding:18px 16px}.p-section-heading h2{font-size:18px}.p-recent-table{padding-inline:16px}.bottom-actions{flex-wrap:wrap;gap:8px}}
</style>

<style scoped>
/* Details checked against the generated page reference. */
.converted-workspace-chat .input-section{width:100%;max-width:none;align-self:stretch}.converted-workspace-chat .workspace-header{height:auto;min-height:70px}.converted-workspace-chat .input-wrapper{width:100%;padding:16px 20px}.converted-workspace-chat .input-textarea{min-height:88px}.converted-workspace-chat .chat-container{gap:20px}.converted-workspace-chat .workspace-header{margin-bottom:0}.converted-workspace-chat .input-section{padding:0}
</style>
