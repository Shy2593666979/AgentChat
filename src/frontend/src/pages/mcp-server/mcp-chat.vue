<template>
  <div class="mcp-chat-container">
    <!-- 历史会话抽屉（覆盖层） -->
    <transition name="drawer">
      <div v-if="sidebarOpen" class="sidebar-overlay" @click.self="sidebarOpen = false">
        <div class="sidebar">
          <div class="sidebar-header">
            <div class="sidebar-title">对话历史</div>
            <el-button :icon="Close" circle size="small" @click="sidebarOpen = false" />
          </div>
          <div class="task-list" v-loading="loadingTasks">
            <div v-if="!loadingTasks && tasks.length === 0" class="empty-tasks">
              暂无对话
            </div>
            <div
              v-for="task in tasks"
              :key="task.id"
              :class="['task-item', { active: task.id === currentTaskId }]"
              @click="selectTask(task.id); sidebarOpen = false"
            >
              <div class="task-item-header">
                <div class="task-item-title">{{ task.messages?.length || 0 }} 条消息</div>
                <div class="task-item-time">{{ formatTime(task.created_time) }}</div>
              </div>
              <div class="task-item-preview">
                {{ getLastMessage(task) }}
              </div>
              <div class="task-item-actions">
                <el-button
                  class="task-delete-btn"
                  size="small"
                  type="danger"
                  :icon="Delete"
                  @click.stop="deleteTask(task.id)"
                  circle
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 主聊天区域 -->
    <div class="main-content">
      <!-- 顶部操作栏 -->
      <div class="chat-toolbar">
        <div class="toolbar-left"></div>
        <div class="toolbar-right">
          <el-button @click="sidebarOpen = true" size="default" round style="font-weight: 600;">
            <span style="margin-right: 4px;">📋</span>历史会话
          </el-button>
          <el-button type="primary" :icon="Plus" @click="createNewTask" size="default" round
            style="background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); border: none; font-weight: 600;">
            新建对话
          </el-button>
        </div>
      </div>

      <div class="chat-messages" ref="chatMessagesRef">
        <div v-if="!currentTaskId" class="empty-state">
          <div class="empty-state-icon">📋</div>
          <div class="empty-state-text">开始新的任务</div>
          <div class="empty-state-hint">选择或创建一个任务开始聊天</div>
        </div>
        
        <template v-else>
          <div v-for="(msg, index) in displayMessages" :key="`msg-${index}-${renderKey}`">
            <!-- 用户消息 -->
            <div class="message-group user">
              <div class="message-content-wrapper">
                <div class="message-content">{{ msg.query }}</div>
              </div>
              <div class="message-avatar">
                <el-avatar :size="36" :src="userAvatar" />
              </div>
            </div>
            
            <!-- AI 回复 -->
            <div class="message-group assistant">
              <div class="message-avatar">
                <el-avatar :size="36" src="/src/assets/robot.svg" />
              </div>
              <div class="message-content-wrapper">
                <div class="message-content markdown-body">
                  <!-- 如果是最后一条消息且正在流式输出，且没有内容，显示加载图标 -->
                  <div v-if="isStreaming && index === displayMessages.length - 1 && !msg.content.length" class="loading-spinner">
                    <el-icon class="is-loading" :size="20"><Loading /></el-icon>
                  </div>
                  <template v-for="(block, bi) in buildBlocks(msg.content)" :key="bi">
                    <!-- 文本块 -->
                    <div v-if="block.type === 'text'" class="text-container" v-html="renderMarkdown(block.data)"></div>
                    <!-- 事件块 -->
                    <div v-else-if="block.type === 'event'" :class="['event-item', block.ev.is_error ? 'ERROR' : (block.ev.status || 'END')]">
                      <div class="event-header" @click="toggleEvent(`${index}-${bi}`)">
                        <span class="event-icon"></span>
                        <span class="event-title">{{ block.ev.title || '事件' }}</span>
                        <span class="event-status">{{ block.ev.is_error ? '失败' : block.ev.status === 'START' ? '进行中' : '已完成' }}</span>
                      </div>
                      <div v-if="block.ev.content && expandedEvents.has(`${index}-${bi}`)" class="event-message">{{ block.ev.content }}</div>
                    </div>
                    <!-- Interrupt 块 -->
                    <div v-else-if="block.type === 'interrupt'" :class="['interrupt-container', { 'processed': block.data.status !== false }]">
                      <div class="interrupt-description" v-html="renderMarkdown(block.data.action_requests?.[0]?.description || '')"></div>
                      <!-- 未处理：显示操作按钮 -->
                      <template v-if="block.data.status === false">
                        <div class="interrupt-buttons">
                          <el-button
                            v-if="block.data.allowed_decisions?.includes('approve')"
                            type="success"
                            @click="handleApprove"
                            :disabled="isStreaming"
                          >确认创建</el-button>
                          <el-button
                            v-if="block.data.allowed_decisions?.includes('reject')"
                            type="danger"
                            @click="showRejectInput = true"
                            :disabled="isStreaming"
                          >取消并修改</el-button>
                        </div>
                        <!-- 修改意见输入框 -->
                        <div v-if="showRejectInput" class="interrupt-feedback">
                          <el-input
                            v-model="rejectFeedback"
                            type="textarea"
                            :rows="3"
                            placeholder="请输入修改意见（留空则直接取消）"
                            class="interrupt-feedback-input"
                          />
                          <div class="interrupt-feedback-buttons">
                            <el-button @click="showRejectInput = false; rejectFeedback = ''">取消</el-button>
                            <el-button type="primary" @click="handleReject" :disabled="isStreaming">提交</el-button>
                          </div>
                        </div>
                      </template>
                      <!-- 已处理 -->
                      <div v-else class="processed-hint">（已处理）</div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <div class="chat-input-wrapper">
        <div class="chat-input-container">
          <div class="input-with-btn">
            <el-input
              v-model="messageInput"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 8 }"
              placeholder="输入消息... (Enter 发送，Shift+Enter 换行)"
              @keydown="handleKeyDown"
              :disabled="isStreaming"
              class="chat-input"
            />
            <el-button
              type="primary"
              :icon="Promotion"
              @click="sendMessage"
              :disabled="!messageInput.trim() || isStreaming"
              class="send-btn"
              circle
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>


<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete, Promotion, Close, List, Loading } from '@element-plus/icons-vue'
import { marked } from 'marked'
import {
  getTaskListAPI,
  createTaskAPI,
  deleteTaskAPI,
  sendMessageAPI,
  hitlApproveAPI,
  hitlRejectAPI,
  type MCPTask,
  type MCPMessage,
  type MCPContent
} from '../../apis/mcp-chat'
import { useUserStore } from '../../store/user'

const userStore = useUserStore()
const userAvatar = computed(() => userStore.userInfo?.avatar || '/src/assets/user.svg')

const tasks = ref<MCPTask[]>([])
const currentTaskId = ref<string | null>(null)
const currentMessages = ref<MCPMessage[]>([])
const streamingContent = ref<MCPContent[]>([])
const streamingQuery = ref<string>('')
const messageInput = ref('')
const isStreaming = ref(false)
const loadingTasks = ref(false)
const chatMessagesRef = ref<HTMLElement>()
const renderKey = ref(0) // 用于强制重新渲染
const showRejectInput = ref(false)
const rejectFeedback = ref('')
const expandedEvents = ref(new Set<string>())
const sidebarOpen = ref(false)

const toggleEvent = (key: string) => {
  if (expandedEvents.value.has(key)) {
    expandedEvents.value.delete(key)
  } else {
    expandedEvents.value.add(key)
  }
  expandedEvents.value = new Set(expandedEvents.value) // 触发响应式更新
}

// 计算属性：合并历史消息和流式消息
const displayMessages = computed(() => {
  if (isStreaming.value && streamingQuery.value) {
    return [...currentMessages.value, {
      query: streamingQuery.value,
      content: streamingContent.value
    }]
  }
  return currentMessages.value
})

// 格式化时间
const formatTime = (dateStr: string) => {
  if (!dateStr) return '刚刚'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  if (diff < 604800000) return Math.floor(diff / 86400000) + '天前'
  
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

// 获取最后一条消息
const getLastMessage = (task: MCPTask) => {
  if (!task.messages || task.messages.length === 0) return '新对话'
  return task.messages[task.messages.length - 1].query || '新对话'
}

// 加载任务列表
const loadTaskList = async () => {
  loadingTasks.value = true
  try {
    const response = await getTaskListAPI()
    if (response.data.status_code === 200) {
      tasks.value = response.data.data || []
    } else {
      ElMessage.error(response.data.status_message || '加载任务列表失败')
    }
  } catch (error) {
    console.error('加载任务列表失败:', error)
    ElMessage.error('加载任务列表失败')
  } finally {
    loadingTasks.value = false
  }
}


// 创建新任务
const createNewTask = async () => {
  try {
    const response = await createTaskAPI()
    if (response.data.status_code === 200 && response.data.data) {
      currentTaskId.value = response.data.data.id
      currentMessages.value = []
      await loadTaskList()
      ElMessage.success('创建新对话成功')
    } else {
      ElMessage.error(response.data.status_message || '创建对话失败')
    }
  } catch (error) {
    console.error('创建任务失败:', error)
    ElMessage.error('创建对话失败')
  }
}

// 选择任务
const selectTask = async (taskId: string) => {
  currentTaskId.value = taskId
  const task = tasks.value.find(t => t.id === taskId)
  if (task) {
    currentMessages.value = task.messages || []
    await nextTick()
    scrollToBottom()
  }
}

// 删除任务
const deleteTask = async (taskId: string) => {
  try {
    const response = await deleteTaskAPI(taskId)
    if (response.data.status_code === 200) {
      if (taskId === currentTaskId.value) {
        currentTaskId.value = null
        currentMessages.value = []
      }
      await loadTaskList()
      ElMessage.success('删除成功')
    } else {
      ElMessage.error(response.data.status_message || '删除失败')
    }
  } catch (error) {
    console.error('删除任务失败:', error)
    ElMessage.error('删除失败')
  }
}

// 将 content 数组构建为渲染块列表
const buildBlocks = (content: MCPContent[]) => {
  if (!content || content.length === 0) return []
  const blocks: any[] = []
  const eventMap = new Map()
  content.forEach(item => {
    if (item.type === 'text') {
      const last = blocks[blocks.length - 1]
      if (last && last.type === 'text') {
        last.data += item.data
      } else {
        blocks.push({ type: 'text', data: item.data })
      }
    } else if (item.type === 'event') {
      const ev = item.data
      const title = ev.title || '事件'
      const existingIdx = eventMap.get(title)
      if (existingIdx !== undefined) {
        blocks[existingIdx].ev = ev
      } else {
        eventMap.set(title, blocks.length)
        blocks.push({ type: 'event', ev })
      }
    } else if (item.type === 'interrupt') {
      blocks.push({ type: 'interrupt', data: item.data })
    }
  })
  return blocks
}

// 渲染 markdown
const renderMarkdown = (text: string) => {
  if (!text) return ''
  return marked.parse(text) as string
}

const escapeHtml = (text: string) => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

// 处理流式响应的通用函数
const processStream = async (response: Response) => {
  const reader = response.body?.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  if (!reader) throw new Error('无法获取响应流')
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const dataContent = line.substring(6).trim()
        if (dataContent === 'DONE') continue
        try {
          const data = JSON.parse(dataContent)
          if (data.type === 'text') {
            streamingContent.value.push({ type: 'text', data: data.content })
            renderKey.value++
          } else if (data.type === 'event') {
            streamingContent.value.push({ type: 'event', data: data.event || data })
            renderKey.value++
          } else if (data.type === 'interrupt') {
            streamingContent.value.push({ type: 'interrupt', data: data.event || data })
            renderKey.value++
          }
          await nextTick()
          scrollToBottom()
        } catch (e) {
          // ignore parse errors
        }
      }
    }
  }
}

// HITL Approve
const handleApprove = async () => {
  if (isStreaming.value || !currentTaskId.value) return
  isStreaming.value = true
  try {
    const response = await hitlApproveAPI(currentTaskId.value)
    // 把当前 interrupt 标记为已处理
    const lastInterrupt = [...streamingContent.value].reverse().find(c => c.type === 'interrupt')
    if (lastInterrupt) lastInterrupt.data.status = true
    // 把 streaming 内容追加到当前消息的 content 里（找最后一条消息）
    const task = tasks.value.find(t => t.id === currentTaskId.value)
    const lastMsg = task?.messages?.[task.messages.length - 1]
    if (lastMsg) {
      // 更新 interrupt status
      const interruptItem = [...lastMsg.content].reverse().find(c => c.type === 'interrupt')
      if (interruptItem) interruptItem.data.status = true
      streamingQuery.value = lastMsg.query
      streamingContent.value = [...lastMsg.content]
    }
    renderKey.value++
    await processStream(response)
    await loadTaskList()
    const updatedTask = tasks.value.find(t => t.id === currentTaskId.value)
    if (updatedTask) currentMessages.value = updatedTask.messages || []
  } catch (error) {
    console.error('Approve 失败:', error)
    ElMessage.error('操作失败')
  } finally {
    isStreaming.value = false
    streamingQuery.value = ''
    streamingContent.value = []
    await nextTick()
    scrollToBottom()
  }
}

// HITL Reject
const handleReject = async () => {
  if (isStreaming.value || !currentTaskId.value) return
  isStreaming.value = true
  showRejectInput.value = false
  const feedback = rejectFeedback.value
  rejectFeedback.value = ''
  try {
    const response = await hitlRejectAPI(currentTaskId.value, feedback)
    const task = tasks.value.find(t => t.id === currentTaskId.value)
    const lastMsg = task?.messages?.[task.messages.length - 1]
    if (lastMsg) {
      const interruptItem = [...lastMsg.content].reverse().find(c => c.type === 'interrupt')
      if (interruptItem) interruptItem.data.status = true
      streamingQuery.value = lastMsg.query
      streamingContent.value = [...lastMsg.content]
    }
    renderKey.value++
    await processStream(response)
    await loadTaskList()
    const updatedTask = tasks.value.find(t => t.id === currentTaskId.value)
    if (updatedTask) currentMessages.value = updatedTask.messages || []
  } catch (error) {
    console.error('Reject 失败:', error)
    ElMessage.error('操作失败')
  } finally {
    isStreaming.value = false
    streamingQuery.value = ''
    streamingContent.value = []
    await nextTick()
    scrollToBottom()
  }
}


// 发送消息
const sendMessage = async () => {
  const query = messageInput.value.trim()
  if (!query || isStreaming.value) return
  
  // 如果没有当前任务，自动创建
  if (!currentTaskId.value) {
    try {
      const response = await createTaskAPI()
      if (response.data.status_code === 200 && response.data.data) {
        currentTaskId.value = response.data.data.id
        await loadTaskList()
      } else {
        ElMessage.error('创建对话失败')
        return
      }
    } catch (error) {
      console.error('创建任务失败:', error)
      ElMessage.error('创建对话失败')
      return
    }
  }
  
  const userQuery = query
  messageInput.value = ''
  isStreaming.value = true
  
  // 初始化流式状态
  streamingQuery.value = userQuery
  streamingContent.value = []
  renderKey.value = 0
  
  await nextTick()
  scrollToBottom()
  
  try {
    const response = await sendMessageAPI(userQuery, currentTaskId.value)
    await processStream(response)
    
    // 流式完成后，重新加载任务列表
    await loadTaskList()
    
    // 重新选择当前任务以刷新消息
    const task = tasks.value.find(t => t.id === currentTaskId.value)
    if (task) {
      currentMessages.value = task.messages || []
    }
    
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败')
  } finally {
    // 清空流式状态
    isStreaming.value = false
    streamingQuery.value = ''
    streamingContent.value = []
    await nextTick()
    scrollToBottom()
  }
}

// 处理键盘事件
const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

// 滚动到底部
const scrollToBottom = () => {
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
  }
}

onMounted(() => {
  loadTaskList()
})
</script>


<style lang="scss" scoped>
.mcp-chat-container {
  display: flex;
  height: 100%;
  background: #f7f8fa;
  overflow: hidden;
}

// 抽屉覆盖层
.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 100;
  display: flex;
}

.sidebar {
  width: 280px;
  height: 100%;
  background: #fff;
  display: flex;
  flex-direction: column;
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.12);

  .sidebar-header {
    padding: 16px;
    border-bottom: 1px solid var(--el-border-color);
    display: flex;
    align-items: center;
    justify-content: space-between;

    .sidebar-title {
      font-size: 15px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }

  .task-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px;

    .empty-tasks {
      text-align: center;
      padding: 20px;
      color: var(--el-text-color-secondary);
      font-size: 14px;
    }

    .task-item {
      padding: 12px;
      margin-bottom: 4px;
      background: transparent;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.2s;
      border: 1px solid transparent;
      position: relative;

      &:hover {
        background: var(--el-fill-color-light);

        .task-item-actions {
          opacity: 1;
        }
      }

      &.active {
        background: var(--el-fill-color);
        border-color: var(--el-color-primary);
      }

      .task-item-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;

        .task-item-title {
          font-size: 14px;
          font-weight: 500;
          color: var(--el-text-color-primary);
        }

        .task-item-time {
          font-size: 11px;
          color: var(--el-text-color-secondary);
        }
      }

      .task-item-preview {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        margin-bottom: 8px;
      }

      .task-item-actions {
        display: flex;
        justify-content: flex-end;
        opacity: 0;
        transition: opacity 0.2s;
      }
    }
  }
}

// 抽屉动画
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.25s ease;
  .sidebar {
    transition: transform 0.25s ease;
  }
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
  .sidebar {
    transform: translateX(-100%);
  }
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f7f8fa;
  position: relative;

  .chat-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    background: transparent;
    border-bottom: none;

    .toolbar-left {
      display: flex;
      align-items: center;
      gap: 10px;

      .toolbar-icon {
        width: 28px;
        height: 28px;
      }

      .toolbar-title {
        font-size: 20px;
        font-weight: 600;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
    }

    .toolbar-right {
      display: flex;
      gap: 12px;
    }
  }
  
  .chat-messages {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 24px 24px 120px;
    
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: var(--el-text-color-secondary);
      
      .empty-state-icon {
        font-size: 64px;
        margin-bottom: 16px;
        opacity: 0.5;
      }
      
      .empty-state-text {
        font-size: 18px;
        margin-bottom: 8px;
        font-weight: 500;
      }
      
      .empty-state-hint {
        font-size: 14px;
        opacity: 0.7;
      }
    }
    
    .message-group {
      margin-bottom: 24px;
      display: flex;
      gap: 12px;
      min-width: 0;
      width: 100%;
      
      &.user {
        justify-content: flex-end;
        
        .message-avatar {
          order: 2;
        }
      }
      
      &.assistant {
        justify-content: flex-start;
      }
      
      .message-avatar {
        flex-shrink: 0;
      }
      
      .message-content-wrapper {
        max-width: 65%;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      
      .message-content {
        padding: 12px 16px;
        border-radius: 16px;
        line-height: 1.5;
        font-size: 15px;
        word-wrap: break-word;
        overflow-wrap: break-word;
        word-break: break-word;
        overflow: hidden;
      }
      
      &.user .message-content {
        background: var(--el-color-primary);
        color: white;
        border-bottom-right-radius: 4px;
      }
      
      &.assistant .message-content {
        background: var(--el-fill-color-light);
        color: var(--el-text-color-primary);
        border-bottom-left-radius: 4px;
      }
    }
  }

  .loading-spinner {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 28px;
    color: #6e8efb;
  }
  
  .chat-input-wrapper {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 16px 24px 24px;
    background: transparent;
    border-top: none;
    
    .chat-input-container {
      width: 66.67%;
      margin: 0 auto;

      .input-with-btn {
        position: relative;

        .chat-input {
          :deep(.el-textarea__inner) {
            padding: 14px 56px 14px 16px;
            border-radius: 12px;
            font-size: 15px;
            line-height: 1.6;
            resize: none;
            border: 1px solid var(--el-border-color);
            background: var(--el-fill-color-blank);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            transition: border-color 0.2s, box-shadow 0.2s;

            &:focus {
              border-color: var(--el-color-primary);
              box-shadow: 0 2px 12px rgba(64, 158, 255, 0.15);
            }

            &::placeholder {
              color: var(--el-text-color-placeholder);
            }
          }
        }

        .send-btn {
          position: absolute;
          right: 8px;
          top: 50%;
          transform: translateY(-50%);
          width: 36px;
          height: 36px;
          box-shadow: 0 2px 6px rgba(64, 158, 255, 0.3);
          transition: transform 0.15s, box-shadow 0.15s;

          &:not(:disabled):hover {
            transform: translateY(-50%) scale(1.08);
            box-shadow: 0 4px 10px rgba(64, 158, 255, 0.4);
          }
        }
      }
    }
  }
}

// 事件样式
:deep(.event-item) {
  margin: 0 0 4px 0;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  border-left: 3px solid;
  
  &.START {
    background: rgba(37, 99, 235, 0.08);
    border-left-color: #2563eb;
  }
  
  &.END {
    background: rgba(34, 197, 94, 0.08);
    border-left-color: #22c55e;
  }
  
  &.ERROR {
    background: rgba(239, 68, 68, 0.08);
    border-left-color: #ef4444;
  }
  
  .event-header {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    user-select: none;
  }
  
  .event-icon {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  
  &.START .event-icon {
    background: #2563eb;
    animation: pulse 1.5s ease-in-out infinite;
  }
  
  &.END .event-icon {
    background: #22c55e;
  }
  
  &.ERROR .event-icon {
    background: #ef4444;
  }
  
  .event-title {
    font-weight: 600;
    flex: 1;
  }
  
  &.START .event-title {
    color: #2563eb;
  }
  
  &.END .event-title {
    color: #22c55e;
  }
  
  &.ERROR .event-title {
    color: #ef4444;
  }
  
  .event-status {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: 500;
  }
  
  &.START .event-status {
    background: rgba(37, 99, 235, 0.15);
    color: #2563eb;
  }
  
  &.END .event-status {
    background: rgba(34, 197, 94, 0.15);
    color: #22c55e;
  }
  
  &.ERROR .event-status {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
  }
  
  .event-message {
    margin-top: 8px;
    padding: 8px;
    background: rgba(255, 255, 255, 0.5);
    border-radius: 6px;
    font-size: 12px;
    line-height: 1.5;
  }
}

.interrupt-buttons {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 12px;
}

.interrupt-feedback {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(37, 99, 235, 0.3);
  
  .interrupt-feedback-input {
    margin-bottom: 10px;
  }
  
  .interrupt-feedback-buttons {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
  }
}

.processed-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 8px;
}

// Interrupt 样式
:deep(.interrupt-container) {
  margin: 8px 0;
  padding: 16px;
  background: rgba(37, 99, 235, 0.08);
  border: 1px solid rgba(37, 99, 235, 0.3);
  border-radius: 12px;
  
  &.processed {
    opacity: 0.6;
  }
  
  .interrupt-description {
    font-size: 14px;
    line-height: 1.5;
    margin-bottom: 12px;
    
    p { margin: 0 0 8px 0; &:last-child { margin-bottom: 0; } }
    code { background: rgba(128, 128, 128, 0.2); padding: 2px 5px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 13px; }
    pre { background: rgba(0, 0, 0, 0.3); padding: 12px; border-radius: 8px; overflow-x: auto; margin: 8px 0; code { background: none; padding: 0; } }
  }
}

// Markdown 样式
:deep(.markdown-body) {
  p {
    margin: 0 0 4px 0;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  h1, h2, h3, h4 {
    margin: 12px 0 6px 0;
    font-weight: 600;
  }
  
  ul, ol {
    padding-left: 20px;
    margin: 6px 0;
  }
  
  li {
    margin: 3px 0;
  }
  
  code {
    background: rgba(128, 128, 128, 0.2);
    padding: 2px 5px;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
  }
  
  pre {
    background: rgba(0, 0, 0, 0.3);
    padding: 12px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 8px 0;
    
    code {
      background: none;
      padding: 0;
    }
  }
  
  blockquote {
    border-left: 3px solid var(--el-border-color);
    padding-left: 12px;
    margin: 8px 0;
    color: var(--el-text-color-secondary);
  }
  
  table {
    border-collapse: collapse;
    width: 100%;
    margin: 8px 0;
    
    th, td {
      border: 1px solid var(--el-border-color);
      padding: 6px 10px;
      text-align: center;
    }
    
    th {
      font-weight: 600;
    }
  }
  
  a {
    color: var(--el-color-primary);
    text-decoration: underline;
  }
  
  hr {
    border: none;
    border-top: 1px solid var(--el-border-color);
    margin: 10px 0;
  }
}
</style>

