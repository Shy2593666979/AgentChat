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

// 使用与ChatMessage接口中定义的eventInfo类型一致的接口
interface EventInfo {
  event_type: string
  show: boolean
  status: string
  message: string
}

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
// 标记是否有正在进行的事件
const hasActiveEvents = ref(false)

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

// 检查是否有活跃事件
const checkActiveEvents = (chatItem: any) => {
  if (!chatItem.eventInfo || chatItem.eventInfo.length === 0) {
    return false
  }
  return chatItem.eventInfo.some((event: EventInfo) => event.status === 'START')
}

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
  
  // 确保事件有title字段，如果没有则使用event_type或默认值
  const eventId = data.title || data.event_type || "event"
  const { status, message } = data
  
  // 获取最后一条AI消息
  const lastChat = historyChatStore.chatArr[historyChatStore.chatArr.length - 1]
  
  // 初始化eventInfo数组（如果不存在）
  if (!lastChat.eventInfo) {
    lastChat.eventInfo = []
  }
  
  // 查找是否已有相同事件类型的事件
  const existingEventIndex = lastChat.eventInfo.findIndex(
    (event) => event.event_type === eventId
  )
  
  if (status === 'START') {
    // 如果是新事件，添加到事件列表
    if (existingEventIndex === -1) {
      lastChat.eventInfo.push({
        event_type: eventId,
        message: message || "处理中...",
        status: status,
        show: false // 默认折叠
      })
    } else {
      // 更新已有事件
      lastChat.eventInfo[existingEventIndex].status = status
      lastChat.eventInfo[existingEventIndex].message = message || "处理中..."
    }
    // 设置有活跃事件
    hasActiveEvents.value = true
  } else if (status === 'END' || status === 'ERROR') {
    // 更新已有事件状态
    if (existingEventIndex !== -1) {
      lastChat.eventInfo[existingEventIndex].status = status
      if (message) {
        lastChat.eventInfo[existingEventIndex].message = message
      }
    } else {
      // 如果没有找到对应的事件，创建一个新事件
      lastChat.eventInfo.push({
        event_type: eventId,
        message: message || (status === 'END' ? "已完成" : "处理出错"),
        status: status,
        show: false // 默认折叠
      })
    }
    
    // 检查是否还有其他活跃事件
    hasActiveEvents.value = checkActiveEvents(lastChat)
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
    hasActiveEvents.value = false
    const currentInput = searchInput.value
    searchInput.value = ""

    historyChatStore.chatArr.push({
      personMessage: { content: currentInput },
      aiMessage: { content: "" },
      eventInfo: [] // 初始化事件信息数组
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
            } else if (parsedData.type === 'event') {
              // 处理事件消息
              handleEventStatus(parsedData)
            } else if (parsedData.type === 'knowledge') {
              historyChatStore.chatArr.push({
                personMessage: { content: '' },
                aiMessage: { content: '[知识库检索结果]\n' + (parsedData.data.message || ''), type: 'knowledge' },
                eventInfo: []
              })
              scrollBottom()
            } else if (parsedData.type === 'error') {
              historyChatStore.chatArr.push({
                personMessage: { content: '' },
                aiMessage: { content: '[错误]\n' + (parsedData.data.message || ''), type: 'error' },
                eventInfo: []
              })
              scrollBottom()
            } else if (parsedData.type === 'heartbeat') {
              // 心跳包可忽略
            } else {
              // 其他类型作为普通消息展示
              historyChatStore.chatArr.push({
                personMessage: { content: '' },
                aiMessage: { content: '[系统消息]\n' + JSON.stringify(parsedData.data), type: 'system' },
                eventInfo: []
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
          hasActiveEvents.value = false
        }
      )
    } catch (error) {
      ElMessage.error('发送消息失败，请重试')
      sendQuestion.value = true
      abortCtrl.value = null
      hasActiveEvents.value = false
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
      hasActiveEvents.value = false
      ElMessage.info('已取消本次AI生成！')
    }
  }
}

// 切换事件信息的展开/折叠状态
const toggleEventInfo = (event: EventInfo) => {
  event.show = !event.show
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
              <!-- 事件进度信息，每个事件一行，可折叠 -->
              <div v-if="item.eventInfo && item.eventInfo.length" class="event-info-list">
                <div v-for="(event, evIdx) in item.eventInfo" :key="evIdx" class="event-info-row" :class="event.status">
                  <div class="event-info-header" @click="toggleEventInfo(event)">
                    <el-icon v-if="event.status === 'START'" class="rotating"><Loading /></el-icon>
                    <el-icon v-else-if="event.status === 'END'" class="success-icon"><Check /></el-icon>
                    <el-icon v-else-if="event.status === 'ERROR'" class="error-icon"><Close /></el-icon>
                    <span class="event-info-title">{{ event.event_type }}</span>
                    <span class="event-info-status">
                      {{ event.status === 'START' ? '进行中' : event.status === 'END' ? '已完成' : '失败' }}
                    </span>
                    <span class="event-info-toggle">{{ event.show ? '收起' : '展开' }}</span>
                  </div>
                  <div v-if="event.show" class="event-info-message">
                    {{ event.message }}
                  </div>
                </div>
              </div>
              
              <!-- Loading Indicator - 只在没有活跃事件时显示 -->
              <div v-if="!item.aiMessage.content && !sendQuestion && index === historyChatStore.chatArr.length - 1 && !hasActiveEvents" class="loading-spinner">
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
        </div>
      </el-scrollbar>
    </div>

    <div class="input-area">
      <el-upload
        action="/api/v1/upload"
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

/* 事件进度信息样式 */
.event-info-list {
  margin-bottom: 12px;
}

.event-info-row {
  margin-bottom: 8px;
  border-radius: 8px;
  padding: 8px 12px;
  background: #f8fafc;
  cursor: pointer;
  transition: background 0.3s ease;
  display: flex;
  flex-direction: column;
  
  &.START { 
    border-left: 4px solid #409eff; 
    background: #f0f7ff;
  }
  
  &.END { 
    border-left: 4px solid #67c23a; 
    background: #f0fff4;
  }
  
  &.ERROR { 
    border-left: 4px solid #f56c6c; 
    background: #fff0f0;
  }
  
  &:hover {
    transform: translateX(2px);
  }
}

.event-info-header { 
  display: flex; 
  align-items: center; 
}

.event-info-title { 
  margin-left: 8px; 
  font-weight: 600;
  color: #333;
}

.event-info-status {
  margin-left: 8px;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 10px;
  background: #eee;
  
  .START & {
    background: #e6f1ff;
    color: #409eff;
  }
  
  .END & {
    background: #e7f9eb;
    color: #67c23a;
  }
  
  .ERROR & {
    background: #ffeded;
    color: #f56c6c;
  }
}

.event-info-toggle { 
  margin-left: auto; 
  color: #aaa; 
  font-size: 12px;
  
  &:hover {
    color: #666;
  }
}

.event-info-message { 
  margin-top: 8px; 
  color: #333;
  padding: 8px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.5;
}

.rotating { 
  animation: spin 1.2s linear infinite;
  color: #409eff;
}

.success-icon {
  color: #67c23a;
}

.error-icon {
  color: #f56c6c;
}

@keyframes spin { 
  from { transform: rotate(0deg); } 
  to { transform: rotate(360deg); } 
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

// Override MdPreview background
:deep(.md-editor-preview-wrapper) {
    background-color: transparent !important;
}

:deep(.el-scrollbar__view) {
  padding: 10px;
}
</style>