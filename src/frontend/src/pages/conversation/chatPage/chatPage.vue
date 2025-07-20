<script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed } from "vue"
import { useRoute } from 'vue-router'
import { MdPreview } from "md-editor-v3"
import "md-editor-v3/lib/style.css"
import { sendMessage, type Chat } from "../../../apis/chat"
import { useHistoryChatStore } from "../../../store/history_chat_msg"
import { useUserStore } from "../../../store/user" // Import user store
import { ElScrollbar, ElInput, ElButton, ElMessage, ElUpload, ElIcon } from "element-plus"
import { UploadFilled, Promotion, Loading, VideoPause } from '@element-plus/icons-vue'


// Import static assets
import defaultUserAvatar from '../../../assets/user.svg';
import defaultRobotAvatar from '../../../assets/robot.svg';

const searchInput = ref("")
const sendQuestion = ref(true)
const historyChatStore = useHistoryChatStore()
const userStore = useUserStore() // Use user store
const scrollbar = ref<InstanceType<typeof ElScrollbar>>()
const route = useRoute()
const abortCtrl = ref<AbortController | null>(null)
const isCancelled = ref(false)

// Get user avatar from store or use default
const userAvatar = computed(() => userStore.userInfo?.avatar || defaultUserAvatar)
// Get AI avatar from store or use default
const aiAvatar = computed(() => historyChatStore.logo || defaultRobotAvatar)

const handleUploadSuccess = (response: any, file: any, fileList: any) => {
  ElMessage.success(`文件 ${file.name} 上传成功!`)
  // You can handle the response from the server here
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
            // 强制只显示“已取消本次对话！”
            historyChatStore.chatArr[historyChatStore.chatArr.length - 1].aiMessage.content = '已取消本次对话！'
            return
          }
          try {
            const parsedData = JSON.parse(msg.data)
            if (parsedData.chunk) {
              historyChatStore.chatArr[historyChatStore.chatArr.length - 1].aiMessage.content += parsedData.chunk
              scrollBottom()
            }
          } catch (error) {
            console.error('解析消息失败:', error)
          }
        },
        () => {
          sendQuestion.value = true
          abortCtrl.value = null
        }
      )
    } catch (error) {
      ElMessage.error('发送消息失败，请重试')
      sendQuestion.value = true
      abortCtrl.value = null
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
        <div v-for="(item, index) in historyChatStore.chatArr" :key="index" class="message-group">
          <!-- User Message -->
          <div v-if="item.personMessage.content" class="user-message">
            <div class="message-content">
              <span>{{ item.personMessage.content }}</span>
            </div>
            <img :src="userAvatar" alt="User Avatar" class="avatar" />
          </div>
          
          <!-- AI Message -->
          <div v-if="item.aiMessage.content || (!sendQuestion && index === historyChatStore.chatArr.length - 1)" class="ai-message">
            <img :src="aiAvatar" alt="AI Avatar" class="avatar" />
            <div class="message-content">
              <!-- Loading Indicator -->
              <div v-if="!item.aiMessage.content && !sendQuestion" class="loading-spinner">
                  <el-icon class="is-loading" :size="20"><Loading /></el-icon>
              </div>
              <MdPreview v-else :editorId="'ai-' + index" :modelValue="item.aiMessage.content" />
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
  background-color: #f7f8fa; // Lighter gray background
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
      background-color: #ffffff; // White bubbles for AI
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
      background: linear-gradient(135deg, #6e8efb, #a777e3); // Gradient for user bubbles
      color: white;
      border-radius: 18px;
      padding: 12px 18px;
      max-width: 70%;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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

.input-area {
  display: flex;
  align-items: flex-end; /* Align items to the bottom */
  padding: 15px 20px;
  border-top: 1px solid #e0e0e0;
  background-color: #ffffff;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.05);

  .action-btn {
    margin-right: 10px;
    background-color: #f0f2f5;
    border: none;
    width: 48px; /* Increased size */
    height: 48px; /* Increased size */
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
      padding: 12px 18px; /* Adjust padding for textarea */
      &:focus {
        border-color: #6e8efb;
      }
    }
  }

  .send-btn {
    margin-left: 10px;
    background-color: #6e8efb;
    border: none;
    width: 48px; /* Increased size */
    height: 48px; /* Increased size */
    font-size: 24px;
    &:hover {
      background-color: #5a78e6;
    }
    &.pause-mode {
      background-color: #f56c6c; // Red color when in pause mode
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
