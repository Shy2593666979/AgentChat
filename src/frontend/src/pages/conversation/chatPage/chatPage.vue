<script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed } from "vue"
import { useRoute } from 'vue-router'
import { MdPreview } from "md-editor-v3"
import "md-editor-v3/lib/style.css"
import { sendMessage, type Chat } from "../../../apis/chat"
import { useHistoryChatStore } from "../../../store/history_chat_msg"
import { useUserStore } from "../../../store/user"
import { ElScrollbar, ElInput, ElButton, ElMessage, ElUpload, ElIcon } from "element-plus"
import { UploadFilled, Promotion, Loading, VideoPause, Check, Close } from '@element-plus/icons-vue'

// Import static assets
import defaultUserAvatar from '../../../assets/user.svg';
import defaultRobotAvatar from '../../../assets/robot.svg';

interface EventStatus {
  id: string
  event_type: string
  message: string
  status: 'START' | 'END' | 'ERROR'
  timestamp: number
  loading: boolean
  success: boolean
  error: boolean
}

const searchInput = ref("")
const sendQuestion = ref(true)
const historyChatStore = useHistoryChatStore()
const userStore = useUserStore()
const scrollbar = ref<InstanceType<typeof ElScrollbar>>()
const route = useRoute()
const abortCtrl = ref<AbortController | null>(null)
const isCancelled = ref(false)

// 事件状态管理
const eventStatusMap = ref<Map<string, EventStatus>>(new Map())
const eventDisplayOrder = ref<string[]>([])

// Get user avatar from store or use default
const userAvatar = computed(() => userStore.userInfo?.avatar || defaultUserAvatar)
// Get AI avatar from store or use default
const aiAvatar = computed(() => historyChatStore.logo || defaultRobotAvatar)

// 计算显示的事件列表
const displayEventList = computed(() => {
  return eventDisplayOrder.value.map(id => eventStatusMap.value.get(id)).filter(Boolean) as EventStatus[]
})

const handleUploadSuccess = (response: any, file: any, fileList: any) => {
  ElMessage.success(`文件 ${file.name} 上传成功!`)
  console.log(response)
}

const handleUploadError = (error: any, file: any, fileList: any) => {
  ElMessage.error(`文件 ${file.name} 上传失败.`)
  console.error(error)
}

// Function to scroll to the bottom of the chat
function scrollBottom() {
  nextTick(() => {
    scrollbar.value?.wrapRef?.scrollTo(0, scrollbar.value?.wrapRef.scrollHeight)
  })
}

// 清空事件状态
const clearEventStatus = () => {
  eventStatusMap.value.clear()
  eventDisplayOrder.value = []
}

// 处理事件状态更新
const handleEventStatus = (parsedData: any) => {
  const { data } = parsedData
  const { event_type, status, message } = data
  const eventId = event_type
  
  if (status === 'START') {
    const newEvent: EventStatus = {
      id: eventId,
      event_type: event_type,
      message: message || event_type,
      status: 'START',
      timestamp: Date.now(),
      loading: true,
      success: false,
      error: false
    }
    
    eventStatusMap.value.set(eventId, newEvent)
    
    // 如果是新的事件类型，添加到显示顺序中
    if (!eventDisplayOrder.value.includes(eventId)) {
      eventDisplayOrder.value.push(eventId)
    }
  } else if (status === 'END') {
    const existingEvent = eventStatusMap.value.get(eventId)
    if (existingEvent) {
      existingEvent.status = 'END'
      existingEvent.loading = false
      existingEvent.success = true
      existingEvent.error = false
      if (message) {
        existingEvent.message = message
      }
    }
  } else if (status === 'ERROR') {
    const existingEvent = eventStatusMap.value.get(eventId)
    if (existingEvent) {
      existingEvent.status = 'ERROR'
      existingEvent.loading = false
      existingEvent.success = false
      existingEvent.error = true
      if (message) {
        existingEvent.message = message
      }
    }
  }
  
  scrollBottom()
}

// Function to handle sending a message
const personQuestion = async () => {
  if (!historyChatStore.dialogId) {
    ElMessage.error('未获取到会话 ID，请先选择或创建会话')
    return
  }
  if (searchInput.value.trim() && sendQuestion.value) {
    sendQuestion.value = false
    isCancelled.value = false
    const currentInput = searchInput.value
    searchInput.value = ""

    // 清空之前的事件状态
    clearEventStatus()

    historyChatStore.chatArr.push({
      personMessage: { content: currentInput },
      aiMessage: { content: "" },
    })
    scrollBottom()

    const data: Chat = {
      dialogId: historyChatStore.dialogId,
      userInput: currentInput,
    }

    try {
      abortCtrl.value = sendMessage(
        data,
        (msg: any) => {
          if (isCancelled.value) {
            historyChatStore.chatArr[historyChatStore.chatArr.length - 1].aiMessage.content = '已取消本次对话！'
            clearEventStatus()
            return
          }
          try {
            const parsedData = JSON.parse(msg.data)
            console.log("---------------------------")
            console.log(parsedData.data)
            // 处理不同类型的消息
            if (parsedData.type === 'response_chunk') {
              historyChatStore.chatArr[historyChatStore.chatArr.length - 1].aiMessage.content += parsedData.data.chunk
              scrollBottom()
            } else if (parsedData.type === 'Run MCP Agent') {
              // 只处理当前对话最后一项
              const lastChat = historyChatStore.chatArr[historyChatStore.chatArr.length - 1]
              if (lastChat) {
                // 只保留一条 eventInfo
                lastChat.eventInfo = {
                  show: true,
                  status: parsedData.data.status,
                  message: parsedData.data.message
                }
              }
              scrollBottom()
            } else if (parsedData.type === 'knowledge') {
              historyChatStore.chatArr.push({
                personMessage: { content: '' },
                aiMessage: { content: '[知识库检索结果]\n' + (parsedData.data.message || ''), type: 'knowledge' }
              })
              scrollBottom()
            } else if (parsedData.type === 'error') {
              historyChatStore.chatArr.push({
                personMessage: { content: '' },
                aiMessage: { content: '[错误]\n' + (parsedData.data.message || ''), type: 'error' }
              })
              scrollBottom()
            } else if (parsedData.type === 'heartbeat') {
              // 心跳包可忽略
            } else {
              // 其他类型作为普通消息展示
              historyChatStore.chatArr.push({
                personMessage: { content: '' },
                aiMessage: { content: '[系统消息]\n' + JSON.stringify(parsedData.data), type: 'system' }
              })
              scrollBottom()
            }
          } catch (error) {
            console.error('解析消息失败:', error)
          }
        },
        () => {
          sendQuestion.value = true
          abortCtrl.value = null
          // 对话结束后，延迟3秒清空事件状态
          setTimeout(() => {
            clearEventStatus()
          }, 3000)
        }
      )
    } catch (error) {
      ElMessage.error('发送消息失败，请重试')
      sendQuestion.value = true
      abortCtrl.value = null
      clearEventStatus()
    }
  }
}

const stopGeneration = () => {
  if (abortCtrl.value) {
    console.log('[stopGeneration] 用户点击暂停, abort 请求')
    isCancelled.value = true
    abortCtrl.value.abort()
    const lastMessage = historyChatStore.chatArr[historyChatStore.chatArr.length - 1]
    if (lastMessage) {
      lastMessage.aiMessage.content = '已取消本次AI生成！'
      sendQuestion.value = true
      abortCtrl.value = null
      clearEventStatus()
      ElMessage.info('已取消本次AI生成！')
    }
  }
}

// Load history on mount
onMounted(() => {
  const dialog_id = route.query.dialog_id
  if (dialog_id) {
    historyChatStore.dialogId = dialog_id as string
    historyChatStore.HistoryChat(dialog_id as string).then(() => {
        scrollBottom()
    })
  }
})

// Watch for route changes to load new chat history
watch(
  () => route.query.dialog_id,
  (newVal, oldVal) => {
    if (newVal && newVal !== oldVal) {
      historyChatStore.dialogId = newVal as string
      historyChatStore.HistoryChat(newVal as string).then(() => {
        scrollBottom()
      })
      // 切换对话时清空事件状态
      clearEventStatus()
    }
  }
)

// Watch for new messages to scroll down
watch(
  () => historyChatStore.chatArr,
  () => {
    scrollBottom()
  },
  { deep: true }
)
</script>

<template>
  <div class="chat-container">
    <div class="chat-conversation">
      <el-scrollbar ref="scrollbar">
        <!-- 事件进度指示器区域 -->
        <div v-if="displayEventList.length > 0" class="event-progress-container">
          <div class="event-progress-header">
            <div class="progress-icon">🤖</div>
            <div class="progress-title">AI 处理进度</div>
          </div>
          
          <div class="event-list">
            <div 
              v-for="(event, index) in displayEventList" 
              :key="event.id"
              class="event-item"
              :class="{
                'event-loading': event.loading,
                'event-success': event.success,
                'event-error': event.error
              }"
            >
              <!-- 连接线 -->
              <div 
                v-if="index < displayEventList.length - 1" 
                class="connection-line"
                :class="{
                  'line-active': event.success || event.error,
                  'line-success': event.success,
                  'line-error': event.error
                }"
              ></div>
              
              <!-- 状态图标 -->
              <div class="status-indicator">
                <div class="indicator-circle" :class="{
                  'circle-loading': event.loading,
                  'circle-success': event.success,
                  'circle-error': event.error
                }">
                  <el-icon v-if="event.loading" class="status-icon rotating">
                    <Loading />
                  </el-icon>
                  <el-icon v-else-if="event.success" class="status-icon">
                    <Check />
                  </el-icon>
                  <el-icon v-else-if="event.error" class="status-icon">
                    <Close />
                  </el-icon>
                </div>
              </div>
              
              <!-- 事件信息 -->
              <div class="event-info">
                <div class="event-title" :class="{
                  'title-loading': event.loading,
                  'title-success': event.success,
                  'title-error': event.error
                }">
                  {{ event.event_type }}
                </div>
                <div class="event-message" :class="{
                  'message-loading': event.loading,
                  'message-success': event.success,
                  'message-error': event.error
                }">
                  {{ event.message }}
                </div>
              </div>
              
              <!-- 动画进度条 -->
              <div v-if="event.loading" class="progress-bar">
                <div class="progress-fill"></div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 聊天消息区 -->
        <div v-for="(item, index) in historyChatStore.chatArr" :key="index" class="message-group">
          <!-- User Message -->
          <div v-if="item.personMessage.content" class="user-message">
            <div class="message-content">
              <span>{{ item.personMessage.content }}</span>
            </div>
            <img :src="userAvatar" alt="User Avatar" class="avatar" />
          </div>
          
          <!-- AI Message -->
          <div v-if="item.aiMessage.content || (!sendQuestion && index === historyChatStore.chatArr.length - 1)" class="ai-message" :class="item.aiMessage.type ? 'ai-message-' + item.aiMessage.type : ''">
            <img :src="aiAvatar" alt="AI Avatar" class="avatar" />
            <div class="message-content">
              <!-- 事件进度信息，每个type一行，可折叠 -->
              <div v-if="item.eventInfo && item.eventInfo.length" class="event-info-list">
                <div v-for="(ev, evIdx) in item.eventInfo" :key="ev.event_type" class="event-info-row" :class="ev.status">
                  <div class="event-info-header" @click="ev.show = !ev.show">
                    <el-icon v-if="ev.status === 'START'" class="rotating"><Loading /></el-icon>
                    <el-icon v-else-if="ev.status === 'END'" style="color: #67c23a"><Check /></el-icon>
                    <el-icon v-else-if="ev.status === 'ERROR'" style="color: #f56c6c"><Close /></el-icon>
                    <span class="event-info-title">{{ ev.event_type }}</span>
                    <span class="event-info-status">
                      {{ ev.status === 'START' ? '进行中' : ev.status === 'END' ? '已完成' : '失败' }}
                    </span>
                    <span class="event-info-toggle">{{ ev.show ? '收起' : '展开' }}</span>
                  </div>
                  <div v-if="ev.show" class="event-info-message">
                    {{ ev.message }}
                  </div>
                </div>
              </div>
              <!-- Loading Indicator -->
              <div v-if="!item.aiMessage.content && !sendQuestion" class="loading-spinner">
                  <el-icon class="is-loading" :size="20"><Loading /></el-icon>
              </div>
              <template v-else>
                <div v-if="item.aiMessage.type === 'knowledge'" style="color: #409eff;">
                  <MdPreview :editorId="'ai-knowledge-' + index" :modelValue="item.aiMessage.content" />
                </div>
                <div v-else-if="item.aiMessage.type === 'event'" style="color: #67c23a;">
                  <MdPreview :editorId="'ai-event-' + index" :modelValue="item.aiMessage.content" />
                </div>
                <div v-else-if="item.aiMessage.type === 'error'" style="color: #f56c6c;">
                  <MdPreview :editorId="'ai-error-' + index" :modelValue="item.aiMessage.content" />
                </div>
                <div v-else-if="item.aiMessage.type === 'system'" style="color: #e6a23c;">
                  <MdPreview :editorId="'ai-system-' + index" :modelValue="item.aiMessage.content" />
                </div>
                <MdPreview v-else :editorId="'ai-' + index" :modelValue="item.aiMessage.content" />
              </template>
            </div>
          </div>
          <!-- 事件进度信息，可折叠 -->
          <div v-if="item.eventInfo" class="event-info-row" :class="item.eventInfo.status">
            <div class="event-info-header" @click="item.eventInfo.show = !item.eventInfo.show">
              <el-icon v-if="item.eventInfo.status === 'START'" class="rotating"><Loading /></el-icon>
              <el-icon v-else-if="item.eventInfo.status === 'END'"><Check /></el-icon>
              <el-icon v-else-if="item.eventInfo.status === 'ERROR'"><Close /></el-icon>
              <span class="event-info-title">
                {{ item.eventInfo.status === 'START' ? '进行中' : item.eventInfo.status === 'END' ? '已完成' : '失败' }}
              </span>
              <span class="event-info-toggle">{{ item.eventInfo.show ? '收起' : '展开' }}</span>
            </div>
            <div v-if="item.eventInfo.show" class="event-info-message">
              {{ item.eventInfo.message }}
            </div>
          </div>
        </div>
      </el-scrollbar>
    </div>

    <div class="input-area">
      <el-upload
        action="https://your-upload-api-endpoint"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :show-file-list="false"
      >
        <el-button circle class="action-btn">
          <el-icon><UploadFilled /></el-icon>
        </el-button>
      </el-upload>
      <el-input
        v-model="searchInput"
        type="textarea"
        :autosize="{ minRows: 1, maxRows: 4 }"
        placeholder="请输入您的问题..."
        @keydown.enter.exact.prevent="personQuestion"
        class="message-input"
      />
      <el-button
        @click="sendQuestion ? personQuestion() : stopGeneration()"
        type="primary"
        circle
        class="send-btn"
        :class="{ 'pause-mode': !sendQuestion }"
        :disabled="sendQuestion ? !searchInput.trim() : false"
      >
        <el-icon v-if="sendQuestion"><Promotion /></el-icon>
        <el-icon v-else><VideoPause /></el-icon>
      </el-button>
    </div>
    <div class="footer-text">内容由AI生成, 仅供参考!</div>
  </div>
</template>

<style lang="scss" scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #f7f8fa;
}

.chat-conversation {
  flex: 1;
  padding: 20px;
  overflow-y: hidden;
  
  .message-group {
    margin-bottom: 20px;
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

/* 事件进度指示器样式 */
.event-progress-container {
  background: linear-gradient(135deg, #f8faff 0%, #f0f4ff 100%);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  border: 1px solid #e0e7ff;
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.08);
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #06b6d4);
    background-size: 200% 100%;
    animation: shimmer 3s ease-in-out infinite;
  }
}

.event-progress-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  
  .progress-icon {
    font-size: 24px;
    margin-right: 12px;
    animation: bounce 2s ease-in-out infinite;
  }
  
  .progress-title {
    font-size: 18px;
    font-weight: 700;
    color: #4338ca;
    letter-spacing: 0.5px;
  }
}

.event-list {
  position: relative;
}

.event-item {
  display: flex;
  align-items: center;
  padding: 16px 0;
  position: relative;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  
  &:hover {
    transform: translateX(4px);
  }
}

.connection-line {
  position: absolute;
  left: 24px;
  top: 56px;
  bottom: -16px;
  width: 2px;
  background: #e5e7eb;
  transition: all 0.6s ease;
  z-index: 1;
  
  &.line-active {
    background: linear-gradient(180deg, #10b981, #059669);
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.3);
  }
  
  &.line-error {
    background: linear-gradient(180deg, #ef4444, #dc2626);
    box-shadow: 0 0 8px rgba(239, 68, 68, 0.3);
  }
}

.status-indicator {
  margin-right: 20px;
  z-index: 2;
}

.indicator-circle {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  
  &.circle-loading {
    background: linear-gradient(135deg, #6366f1, #4f46e5);
    box-shadow: 
      0 8px 25px rgba(99, 102, 241, 0.25),
      0 0 0 0 rgba(99, 102, 241, 0.4);
    animation: pulse-loading 2s ease-in-out infinite;
  }
  
  &.circle-success {
    background: linear-gradient(135deg, #10b981, #059669);
    box-shadow: 
      0 8px 25px rgba(16, 185, 129, 0.25),
      0 0 20px rgba(16, 185, 129, 0.2);
    transform: scale(1.1);
  }
  
  &.circle-error {
    background: linear-gradient(135deg, #ef4444, #dc2626);
    box-shadow: 
      0 8px 25px rgba(239, 68, 68, 0.25),
      0 0 20px rgba(239, 68, 68, 0.2);
    transform: scale(1.1);
  }
}

.status-icon {
  font-size: 24px;
  color: white;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
  
  &.rotating {
    animation: spin 1.5s linear infinite;
  }
}

.event-info {
  flex: 1;
  min-width: 0;
}

.event-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 6px;
  transition: all 0.3s ease;
  
  &.title-loading {
    color: #4f46e5;
  }
  
  &.title-success {
    color: #059669;
  }
  
  &.title-error {
    color: #dc2626;
  }
}

.event-message {
  font-size: 14px;
  line-height: 1.5;
  transition: all 0.3s ease;
  
  &.message-loading {
    color: #6b7280;
  }
  
  &.message-success {
    color: #10b981;
    font-weight: 500;
  }
  
  &.message-error {
    color: #ef4444;
    font-weight: 500;
  }
}

.progress-bar {
  position: absolute;
  bottom: 8px;
  left: 68px;
  right: 20px;
  height: 3px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 2px;
  animation: progress-wave 2s ease-in-out infinite;
}

/* 动画定义 */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-6px); }
  60% { transform: translateY(-3px); }
}

@keyframes pulse-loading {
  0% { box-shadow: 0 8px 25px rgba(99, 102, 241, 0.25), 0 0 0 0 rgba(99, 102, 241, 0.4); }
  70% { box-shadow: 0 8px 25px rgba(99, 102, 241, 0.25), 0 0 0 20px rgba(99, 102, 241, 0); }
  100% { box-shadow: 0 8px 25px rgba(99, 102, 241, 0.25), 0 0 0 0 rgba(99, 102, 241, 0); }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes progress-wave {
  0% { transform: translateX(-100%) scaleX(0.5); opacity: 0.7; }
  50% { transform: translateX(0%) scaleX(1); opacity: 1; }
  100% { transform: translateX(100%) scaleX(0.5); opacity: 0.7; }
}

.loading-spinner {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 28px;
  color: #6e8efb;
}

.input-area {
  display: flex;
  align-items: flex-end;
  padding: 15px 20px;
  border-top: 1px solid #e0e0e0;
  background-color: #ffffff;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.05);

  .action-btn {
    margin-right: 10px;
    background-color: #f0f2f5;
    border: none;
    width: 48px;
    height: 48px;
    font-size: 24px;
    &:hover {
      background-color: #e6e8eb;
    }
  }

  .message-input {
    flex-grow: 1;
    :deep(.el-textarea__inner) {
      border-radius: 20px;
      background-color: #f0f2f5;
      box-shadow: none;
      border: 1px solid transparent;
      padding: 12px 18px;
      &:focus {
        border-color: #6e8efb;
      }
    }
  }

  .send-btn {
    margin-left: 10px;
    background-color: #6e8efb;
    border: none;
    width: 48px;
    height: 48px;
    font-size: 24px;
    &:hover {
      background-color: #5a78e6;
    }
    &.pause-mode {
      background-color: #f56c6c;
      &:hover {
        background-color: #dd6161;
      }
    }
  }
}

.footer-text {
  text-align: center;
  font-size: 12px;
  color: #aaa;
  padding: 8px 0;
  background-color: #f7f8fa;
}

/* 事件进度信息样式 */
.event-info-row {
  margin-bottom: 8px;
  border-radius: 8px;
  padding: 8px 12px;
  background: #f8fafc;
  cursor: pointer;
  transition: background 0.3s;
  display: flex;
  flex-direction: column;
}
.event-info-row.START { border-left: 4px solid #409eff; }
.event-info-row.END { border-left: 4px solid #67c23a; background: #f0fff4; }
.event-info-row.ERROR { border-left: 4px solid #f56c6c; background: #fff0f0; }
.event-info-header { display: flex; align-items: center; }
.event-info-title { margin-left: 8px; font-weight: bold; }
.event-info-toggle { margin-left: auto; color: #aaa; font-size: 12px; }
.event-info-message { margin-top: 4px; color: #333; }
.rotating { animation: spin 1.2s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

// Override MdPreview background
:deep(.md-editor-preview-wrapper) {
    background-color: transparent !important;
}

:deep(.el-scrollbar__view) {
  padding: 10px;
}
</style>