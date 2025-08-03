<template>
  <div class="mars-output-page">
    <!-- 离开页面提醒弹窗 -->
    <div v-if="showLeaveModal" class="leave-modal-overlay" @click="handleOverlayClick">
      <div class="leave-modal">
        <div class="leave-modal-header">
          <h3>离开页面提醒</h3>
        </div>
        <div class="leave-modal-body">
          <p>🔔 Mars Agent 不会保存您的聊天记录</p>
          <p>离开此页面后，当前对话内容将无法找回。</p>
          <p>确定要离开吗？</p>
        </div>
        <div class="leave-modal-footer">
          <button class="modal-btn cancel-btn" @click="cancelLeave">取消</button>
          <button class="modal-btn confirm-btn" @click="confirmLeave">确定离开</button>
        </div>
      </div>
    </div>
    
    <!-- AI输出展示区域 -->
    <div class="mars-output-container" ref="outputContainer">
      <!-- 加载状态 -->
      <div v-if="isLoading && !aiContent" class="mars-content">
        <div class="mars-chat-message">
          <div class="mars-ai-avatar">
            <img src="../../assets/robot.svg" alt="AI Assistant" class="avatar-img" />
          </div>
          <div class="mars-loading-dialog">
            <span class="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </span>
          </div>
        </div>
      </div>

      <!-- AI回复内容 -->
      <div v-if="chatSegments.length > 0" class="mars-content">
        <div class="mars-chat-message">
          <div class="mars-ai-avatar">
            <img src="../../assets/robot.svg" alt="AI Assistant" class="avatar-img" />
          </div>
          <div class="mars-response">
            <div v-for="(segment, index) in chatSegments" :key="index">
              <div v-if="segment.type === 'reasoning_chunk'" class="thinking-segment">
                <div class="thinking-header" @click="toggleCollapse(segment)">
                  深度思考
                  <span class="collapse-icon">{{ segment.isCollapsed ? '&#x25B6;' : '&#x25BC;' }}</span>
                </div>
                <div v-show="!segment.isCollapsed" class="thinking-content">
            <MdPreview 
                    :editorId="`mars-output-${index}`"
                    :modelValue="segment.content"
              :showCodeRowNumber="true"
            />
          </div>
        </div>
              <div v-else class="answer-segment">
                <MdPreview
                  :editorId="`mars-output-${index}`"
                  :modelValue="segment.content"
                  :showCodeRowNumber="true"
                />
              </div>
            </div>
            <span v-if="isLoading && showTypingIndicator" class="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </span>
          </div>
        </div>
      </div>

      <!-- 错误状态 -->
      <div v-if="hasError" class="mars-error-state">
        <div class="mars-chat-message">
          <div class="mars-ai-avatar">
            <img src="../../assets/robot.svg" alt="AI Assistant" class="avatar-img" />
          </div>
          <div class="mars-error-text">{{ errorMessage }}</div>
        </div>
        <button class="mars-retry-btn" @click="retryFromHome">
          返回首页重试
        </button>
      </div>

      <!-- 空状态（如果没有从首页传入消息） -->
      <div v-if="chatSegments.length === 0 && !isLoading && !hasError" class="mars-empty-state">
        <div class="mars-chat-message">
          <div class="mars-ai-avatar">
            <img src="../../assets/robot.svg" alt="AI Assistant" class="avatar-img" />
          </div>
          <div class="mars-empty-text">请从首页输入您的问题开始对话</div>
        </div>
        <button class="mars-back-btn" @click="backToHome">
          返回首页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import { ElMessage } from 'element-plus'
import { MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'

// 响应式数据
const route = useRoute()
const router = useRouter()
const chatSegments = ref<{ type: string; content: string, isCollapsed?: boolean }[]>([])
const isLoading = ref(false)
const hasError = ref(false)
const errorMessage = ref('')
const abortController = ref<AbortController | null>(null)
const outputContainer = ref<HTMLElement>()
const showTypingIndicator = ref(false)
const typingTimer = ref<NodeJS.Timeout | null>(null)

// 离开页面提醒相关
const showLeaveModal = ref(false)
let pendingNavigation: (() => void) | null = null

const aiContent = computed(() => chatSegments.value.map(s => s.content).join(''))

// 检查是否有聊天内容
const hasContent = computed(() => {
  return chatSegments.value.length > 0 && aiContent.value.trim().length > 0
})

// 滚动到底部 - 使用更可靠的方法
const scrollToBottom = () => {
  console.log('执行滚动到底部')
  // 使用多个延迟时间来确保滚动生效
  const scrollWithDelay = (delay: number) => {
    setTimeout(() => {
      if (outputContainer.value) {
        console.log(`尝试滚动 (${delay}ms):`, outputContainer.value.scrollHeight)
        outputContainer.value.scrollTop = outputContainer.value.scrollHeight
      }
    }, delay)
  }
  
  // 立即滚动一次
  if (outputContainer.value) {
    outputContainer.value.scrollTop = outputContainer.value.scrollHeight
  }
  
  // 然后在不同的延迟时间再次尝试滚动，确保DOM已更新
  scrollWithDelay(50)
  scrollWithDelay(100)
  scrollWithDelay(200)
  scrollWithDelay(500)
}



// 处理离开页面的逻辑
const handleLeave = (next: () => void) => {
  if (hasContent.value) {
    pendingNavigation = next
    showLeaveModal.value = true
  } else {
    next()
  }
}

// 取消离开
const cancelLeave = () => {
  showLeaveModal.value = false
  pendingNavigation = null
}

// 确认离开
const confirmLeave = () => {
  showLeaveModal.value = false
  if (pendingNavigation) {
    pendingNavigation()
    pendingNavigation = null
  }
}

// 点击遮罩层关闭弹窗
const handleOverlayClick = (event: Event) => {
  if (event.target === event.currentTarget) {
    cancelLeave()
  }
}

// 返回首页
const backToHome = () => {
  handleLeave(() => {
    router.push('/')
  })
}

// 重试 - 返回首页
const retryFromHome = () => {
  handleLeave(() => {
    router.push('/')
  })
}

const toggleCollapse = (segment: { isCollapsed?: boolean }) => {
  segment.isCollapsed = !segment.isCollapsed
}



// 发送消息
const sendMessage = async (userMessage: string) => {
  if (!userMessage.trim() || isLoading.value) return
  
  // 重置状态
  chatSegments.value = []
  hasError.value = false
  errorMessage.value = ''
  isLoading.value = true
  showTypingIndicator.value = false
  if (typingTimer.value) clearTimeout(typingTimer.value)
  abortController.value = new AbortController()

  // 设置初始计时器
  startTypingTimer()

  try {
    await fetchEventSource('/api/v1/mars/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
      },
      body: JSON.stringify({
        user_input: userMessage,
      }),
      signal: abortController.value.signal,
      openWhenHidden: true,
      async onopen(response) {
        if (response.status !== 200) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
      },
      onmessage(msg) {
        if (typingTimer.value) clearTimeout(typingTimer.value)
        showTypingIndicator.value = false
        try {
          console.log('=== Mars消息处理开始 ===')
          console.log('原始消息数据长度:', msg.data.length)
          console.log('原始消息数据:', msg.data.substring(0, 200) + (msg.data.length > 200 ? '...' : ''))
          
          // 处理SSE格式的数据，去掉 "data: " 前缀
          let rawData = msg.data.trim()
          
          if (!rawData) return
          
          // 去掉 "data: " 前缀（如果存在）
          if (rawData.startsWith('data: ')) {
            rawData = rawData.substring(6).trim()
          }
          
          console.log('去掉前缀后的数据:', rawData)
          
          let parsedData
          let parseSuccess = false
          
          // 方法1: 尝试直接替换单引号为双引号并解析JSON
          try {
            const jsonString = rawData.replace(/'/g, '"')
            parsedData = JSON.parse(jsonString)
            console.log(`方法1成功 - 类型: ${parsedData.type}, 内容: "${parsedData.data || ''}"`)
            parseSuccess = true
          } catch (parseError1) {
            console.error('方法1 JSON解析失败:', parseError1)
            
            // 方法2: 尝试使用eval解析
            try {
              // @ts-ignore
              const evalData = eval('(' + rawData + ')')
              parsedData = evalData
              if (!parsedData.data) {
                throw new Error('Eval解析后无法获取data字段')
              }
              console.log(`方法2成功 - 使用eval解析:`, parsedData.data)
              parseSuccess = true
            } catch (evalError) {
              console.error('方法2 Eval解析失败:', evalError)
              
              // 方法3: 尝试修复JSON格式后再解析
              try {
                // 尝试处理嵌套引号问题
                const fixedJson = rawData
                  .replace(/'/g, '"')                   // 替换所有单引号为双引号
                  .replace(/"\s*([^"]*?)\s*":/g, '"$1":') // 修复键名格式
                  .replace(/:\s*"([^"]*?)"/g, ':"$1"')    // 修复值格式
                
                parsedData = JSON.parse(fixedJson)
                if (!parsedData.data) {
                  throw new Error('修复JSON后无法获取data字段')
                }
                console.log(`方法3成功 - 修复后JSON解析:`, parsedData.data)
                parseSuccess = true
              } catch (parseError3) {
                console.error('方法3 修复JSON解析失败:', parseError3)
              }
            }
          }

          if (parseSuccess && parsedData) {
            const type = parsedData.type || 'answer'
            const chunkData = parsedData.data || ''

            if (chunkData !== undefined && chunkData !== null) {
              if (chatSegments.value.length > 0 && chatSegments.value[chatSegments.value.length - 1].type === type) {
                chatSegments.value[chatSegments.value.length - 1].content += chunkData
              } else {
                const newSegment: { type: string, content: string, isCollapsed?: boolean } = { type: type, content: chunkData }
                if (type === 'reasoning_chunk') {
                  newSegment.isCollapsed = false;
                }
                chatSegments.value.push(newSegment)
              }
              console.log('添加内容:', `"${chunkData}"`, '当前总长度:', aiContent.value.length)
                scrollToBottom()
              
              // 重新启动计时器，以便在下一次数据延迟时显示...
              if (isLoading.value) {
                startTypingTimer()
              }
            }
          } else {
            // 所有方法都失败，直接添加原始数据
            console.log('所有解析方法都失败，直接添加原始数据')
            if (chatSegments.value.length > 0 && chatSegments.value[chatSegments.value.length - 1].type === 'raw') {
              chatSegments.value[chatSegments.value.length - 1].content += rawData
            } else {
              chatSegments.value.push({ type: 'raw', content: rawData })
            }
            scrollToBottom()
          }
        } catch (error) {
          console.error('处理Mars消息时出错:', error)
          hasError.value = true
          errorMessage.value = '处理响应时出现错误'
        }
      },
      onclose() {
        isLoading.value = false
        abortController.value = null
        if (typingTimer.value) clearTimeout(typingTimer.value)
        showTypingIndicator.value = false
      },
      onerror(err) {
        console.error('Mars聊天连接错误:', err)
        isLoading.value = false
        abortController.value = null
        if (typingTimer.value) clearTimeout(typingTimer.value)
        showTypingIndicator.value = false
        ElMessage.error('连接错误，请重试')
        throw err
      }
    })
  } catch (error) {
    console.error('Mars聊天失败:', error)
    isLoading.value = false
    abortController.value = null
    hasError.value = true
    errorMessage.value = '发送消息失败，请重试'
    ElMessage.error('发送消息失败，请重试')
  }
}

// 监听AI内容变化，自动滚动
watch(aiContent, () => {
  console.log('AI内容变化，触发滚动')
  scrollToBottom()
}, { flush: 'post' })

// 监听加载状态变化，自动滚动
watch(isLoading, (newVal) => {
  if (newVal) {
    console.log('开始加载，触发滚动')
    scrollToBottom()
  } else {
    // 当加载结束时，滚动到底部
    console.log('加载结束，触发滚动')
    scrollToBottom()
  }
}, { flush: 'post' })

// 创建DOM变化观察器，监听内容变化并滚动
const createContentObserver = () => {
  if (!outputContainer.value) return null
  
  const observer = new MutationObserver((_mutations) => {
    console.log('检测到DOM变化，触发滚动')
    scrollToBottom()
  })
  
  observer.observe(outputContainer.value, {
    childList: true,
    subtree: true,
    characterData: true
  })
  
  return observer
}

// 发送示例请求
const sendExampleRequest = async (exampleId: number) => {
  if (isLoading.value) return
  
  // 重置状态
  chatSegments.value = []
  hasError.value = false
  errorMessage.value = ''
  isLoading.value = true
  showTypingIndicator.value = false
  if (typingTimer.value) clearTimeout(typingTimer.value)
  abortController.value = new AbortController()

  // 设置初始计时器
  startTypingTimer()

  try {
    await fetchEventSource('/api/v1/mars/example', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
      },
      body: JSON.stringify({
        example_id: exampleId
      }),
      signal: abortController.value.signal,
      openWhenHidden: true,
      async onopen(response) {
        if (response.status !== 200) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
      },
      onmessage: msg => {
        if (typingTimer.value) clearTimeout(typingTimer.value)
        showTypingIndicator.value = false
        try {
          console.log('=== Mars示例消息处理开始 ===')
          console.log('原始消息数据长度:', msg.data.length)
          console.log('原始消息数据:', msg.data.substring(0, 200) + (msg.data.length > 200 ? '...' : ''))
          
          // 处理SSE格式的数据，去掉 "data: " 前缀
          let rawData = msg.data.trim()
          
          if (!rawData) return
          
          // 去掉 "data: " 前缀（如果存在）
          if (rawData.startsWith('data: ')) {
            rawData = rawData.substring(6).trim()
          }
          
          console.log('去掉前缀后的数据:', rawData)
          
          let parsedData
          let parseSuccess = false

          // 方法1: 尝试直接替换单引号为双引号并解析JSON
          try {
            const jsonString = rawData.replace(/'/g, '"')
            parsedData = JSON.parse(jsonString)
            console.log(`方法1成功 - 类型: ${parsedData.type}, 内容: "${parsedData.data || ''}"`)
            parseSuccess = true
          } catch (parseError1) {
            console.error('方法1 JSON解析失败:', parseError1)
            
            // 方法2: 尝试使用eval解析
            try {
              // @ts-ignore
              const evalData = eval('(' + rawData + ')')
              parsedData = evalData
              if (!parsedData.data) {
                throw new Error('Eval解析后无法获取data字段')
              }
              console.log(`方法2成功 - 使用eval解析:`, parsedData.data)
              parseSuccess = true
            } catch (evalError) {
              console.error('方法2 Eval解析失败:', evalError)
              
              // 方法3: 尝试修复JSON格式后再解析
              try {
                // 尝试处理嵌套引号问题
                const fixedJson = rawData
                  .replace(/'/g, '"')                   // 替换所有单引号为双引号
                  .replace(/"\s*([^"]*?)\s*":/g, '"$1":') // 修复键名格式
                  .replace(/:\s*"([^"]*?)"/g, ':"$1"')    // 修复值格式
                
                parsedData = JSON.parse(fixedJson)
                if (!parsedData.data) {
                  throw new Error('修复JSON后无法获取data字段')
                }
                console.log(`方法3成功 - 修复后JSON解析:`, parsedData.data)
                parseSuccess = true
              } catch (parseError3) {
                console.error('方法3 修复JSON解析失败:', parseError3)
              }
            }
          }

          if (parseSuccess && parsedData) {
            const type = parsedData.type || 'answer'
            const chunkData = parsedData.data || ''

            if (chunkData !== undefined && chunkData !== null) {
              if (chatSegments.value.length > 0 && chatSegments.value[chatSegments.value.length - 1].type === type) {
                chatSegments.value[chatSegments.value.length - 1].content += chunkData
              } else {
                const newSegment: { type: string, content: string, isCollapsed?: boolean } = { type: type, content: chunkData }
                if (type === 'reasoning_chunk') {
                  newSegment.isCollapsed = false;
                }
                chatSegments.value.push(newSegment)
              }
              console.log('添加内容:', `"${chunkData}"`, '当前总长度:', aiContent.value.length)
                scrollToBottom()
              
              // 重新启动计时器，以便在下一次数据延迟时显示...
              if (isLoading.value) {
                startTypingTimer()
              }
            }
          } else {
            // 所有方法都失败，直接添加原始数据
            console.log('所有解析方法都失败，直接添加原始数据')
            if (chatSegments.value.length > 0 && chatSegments.value[chatSegments.value.length - 1].type === 'raw') {
              chatSegments.value[chatSegments.value.length - 1].content += rawData
            } else {
              chatSegments.value.push({ type: 'raw', content: rawData })
            }
            scrollToBottom()
          }
        } catch (error) {
          console.error('处理Mars示例消息时出错:', error)
          hasError.value = true
          errorMessage.value = '处理响应时出现错误'
        }
      },
      onclose() {
        isLoading.value = false
        abortController.value = null
        if (typingTimer.value) clearTimeout(typingTimer.value)
        showTypingIndicator.value = false
      },
      onerror(err) {
        console.error('Mars示例连接错误:', err)
        isLoading.value = false
        abortController.value = null
        if (typingTimer.value) clearTimeout(typingTimer.value)
        showTypingIndicator.value = false
        ElMessage.error('连接错误，请重试')
        throw err
      }
    })
  } catch (error) {
    console.error('Mars示例请求失败:', error)
    isLoading.value = false
    abortController.value = null
    hasError.value = true
    errorMessage.value = '示例请求失败，请重试'
    ElMessage.error('示例请求失败，请重试')
  }
}

// 添加启动计时器的辅助函数
const startTypingTimer = () => {
  if (typingTimer.value) clearTimeout(typingTimer.value)
  typingTimer.value = setTimeout(() => {
    if (isLoading.value) {
      showTypingIndicator.value = true
      scrollToBottom()
    }
  }, 1000) // 1秒延迟
}

// 组件内路由守卫
onBeforeRouteLeave((_to, _from, next) => {
  if (hasContent.value) {
    handleLeave(() => {
      next()
    })
  } else {
    next()
  }
})

// 页面加载时的初始化
onMounted(() => {
  // 创建内容观察器
  createContentObserver()
  
  // 添加浏览器前进后退监听
  const handleBeforeUnload = (event: BeforeUnloadEvent) => {
    if (hasContent.value) {
      event.preventDefault()
      event.returnValue = 'Mars Agent 不会保存您的聊天记录，离开后将无法找回。确定要离开吗？'
      return event.returnValue
    }
  }
  
  window.addEventListener('beforeunload', handleBeforeUnload)
  
  // 检查URL参数
  const messageFromHome = route.query.message
  const exampleId = route.query.example_id
  
  // 清除URL中的参数，保持URL简洁
  router.replace({
    path: route.path,
    query: {}  // 清空所有query参数
  })
  
  // 根据参数类型执行不同的操作
  nextTick(() => {
    // 优先处理示例ID
    if (exampleId && typeof exampleId === 'string') {
      const id = parseInt(exampleId)
      if (!isNaN(id)) {
        sendExampleRequest(id)
      }
    } 
    // 如果没有示例ID但有消息，则发送消息
    else if (messageFromHome && typeof messageFromHome === 'string') {
      sendMessage(messageFromHome)
    }
  })
  
  // 清理函数
  onBeforeUnmount(() => {
    window.removeEventListener('beforeunload', handleBeforeUnload)
  })
})
</script>

<style lang="scss" scoped>
// 离开页面提醒弹窗样式
.leave-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.leave-modal {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 420px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.leave-modal-header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e9ecef;
  
  h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #333;
  }
}

.leave-modal-body {
  padding: 20px 24px;
  
  p {
    margin: 0 0 12px 0;
    line-height: 1.6;
    color: #555;
    
    &:first-child {
      font-weight: 600;
      color: #4a90e2;
    }
    
    &:last-child {
      margin-bottom: 0;
      font-weight: 500;
      color: #333;
    }
  }
}

.leave-modal-footer {
  padding: 16px 24px 20px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  border-top: 1px solid #e9ecef;
}

.modal-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 80px;
  
  &.cancel-btn {
    background: #f8f9fa;
    color: #666;
    border: 1px solid #e9ecef;
    
    &:hover {
      background: #e9ecef;
      color: #333;
    }
  }
  
  &.confirm-btn {
    background: #4a90e2;
    color: white;
    
    &:hover {
      background: #357abd;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
    }
  }
}

.mars-output-page {
  height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden; /* 防止整个页面出现滚动条 */
}

.mars-output-container {
  flex: 1;
  width: 100%;
  background: white;
  overflow-y: auto; /* 只在内容超出时显示垂直滚动条 */
  overflow-x: hidden; /* 隐藏水平滚动条 */
  display: flex;
  flex-direction: column;
  
  /* 隐藏右侧滚动条但保留滚动功能 */
  &::-webkit-scrollbar {
    width: 0;
    display: none;
  }
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
}

.typing-dots {
  display: inline-flex;
  gap: 4px;
  vertical-align: middle;
}

.typing-dots span {
  width: 8px;
  height: 8px;
  background-color: #666;
  border-radius: 50%;
  animation: typing-blink 1.4s infinite both;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing-blink {
  0% {
    opacity: 0.2;
  }
  20% {
    opacity: 1;
  }
  100% {
    opacity: 0.2;
  }
}

.thinking-segment {
  background-color: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  margin-bottom: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1), 0 2px 6px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

.thinking-header {
  padding: 12px 16px;
  font-weight: 600;
  color: #333;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e0e0e0;
}

.collapse-icon {
  font-size: 14px;
  transition: transform 0.3s ease;
}

.thinking-content {
  padding: 16px;
  border-top: none;
}

.thinking-content :deep(.md-editor-preview) p,
.thinking-content :deep(.md-editor-preview) li,
.thinking-content :deep(.md-editor-preview) ul,
.thinking-content :deep(.md-editor-preview) ol,
.thinking-content :deep(.md-editor-preview) h1,
.thinking-content :deep(.md-editor-preview) h2,
.thinking-content :deep(.md-editor-preview) h3,
.thinking-content :deep(.md-editor-preview) h4,
.thinking-content :deep(.md-editor-preview) h5,
.thinking-content :deep(.md-editor-preview) h6 {
  color: #495057 !important;
}

.answer-segment {
  /* No specific styles needed unless for spacing/debugging */
  margin-bottom: 10px;
}

// 加载对话框样式
.mars-loading-dialog {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 16px 20px;
  border: 1px solid #e9ecef;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 120px;
}



// AI内容展示样式
.mars-content {
  padding: 20px;
  width: 100%;
  
  .mars-chat-message {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    
    .mars-ai-avatar {
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      
      .avatar-img {
        width: 40px;
        height: 40px;
      }
    }
    
    .mars-response {
      flex: 1;
      line-height: 1.8;
      min-width: 0;
    }
  }
  
  /*
  .mars-generating {
    margin-top: 16px;
    padding: 12px 16px;
    background: #f8f9fa;
    border-radius: 12px;
    border: 1px solid #e9ecef;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    
    .mars-generating-indicator {
      display: flex;
      align-items: center;
      justify-content: center;
      
      .mars-generating-spinner {
        width: 20px;
        height: 20px;
        border: 2px solid #e9ecef;
        border-top: 2px solid #666;
        border-radius: 50%;
        animation: spin 1s linear infinite;
      }
    }
  }
  */
}

// 错误状态样式
.mars-error-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 40px;
  text-align: center;
  
  .mars-chat-message {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .mars-ai-avatar {
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      
      .avatar-img {
        width: 40px;
        height: 40px;
      }
    }
    
    .mars-error-text {
      font-size: 16px;
      color: #ff4d4f;
      margin-bottom: 32px;
      font-weight: 500;
    }
  }
  
  .mars-retry-btn {
    background: #722ed1;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
    
    &:hover {
      background: #531dab;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(114, 46, 209, 0.3);
    }
  }
}

// 空状态样式
.mars-empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 40px;
  text-align: center;
  
  .mars-chat-message {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .mars-ai-avatar {
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      
      .avatar-img {
        width: 40px;
        height: 40px;
      }
    }
    
    .mars-empty-text {
      font-size: 16px;
      color: #999;
      margin-bottom: 32px;
    }
  }
  
  .mars-back-btn {
    background: #722ed1;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
    
    &:hover {
      background: #531dab;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(114, 46, 209, 0.3);
    }
  }
}

// 移除滚动条样式，使用上面定义的隐藏滚动条

.mars-response-content {
  // Markdown预览组件的样式调整
  :deep(.md-editor-preview) {
    background: transparent;
    padding: 0;
    width: 100%;
    max-width: 100%;
    
    // 确保代码块有合适的样式并充分利用宽度
    pre {
      background: #f6f8fa;
      border-radius: 6px;
      padding: 16px;
      margin: 8px 0;
      border: 1px solid #e1e4e8;
      width: 100%;
      box-sizing: border-box;
      overflow-x: auto;
    }
    
    // 段落间距
    p {
      margin: 8px 0;
      line-height: 1.6;
      width: 100%;
    }
    
    // 列表样式
    ul, ol {
      margin: 8px 0;
      padding-left: 24px;
      width: 100%;
    }
    
    // 标题样式
    h1, h2, h3, h4, h5, h6 {
      margin: 16px 0 8px 0;
      font-weight: 600;
      width: 100%;
    }
    
    // 表格样式 - 充分利用宽度
    table {
      border-collapse: collapse;
      margin: 8px 0;
      width: 100%;
      max-width: 100%;
      
      th, td {
        border: 1px solid #e1e4e8;
        padding: 8px 12px;
        text-align: left;
        word-wrap: break-word;
      }
      
      th {
        background: #f6f8fa;
        font-weight: 600;
      }
    }
    
    // 引用块样式
    blockquote {
      border-left: 4px solid #722ed1;
      padding-left: 16px;
      margin: 8px 0;
      color: #666;
      font-style: italic;
      width: 100%;
      box-sizing: border-box;
    }
    
    // 行内代码样式
    code {
      background: #f6f8fa;
      padding: 2px 4px;
      border-radius: 3px;
      font-size: 0.9em;
      color: #d73a49;
    }
    
    // 确保所有内容元素都充分利用宽度
    div, section, article {
      width: 100%;
      max-width: 100%;
    }
  }
}



@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

// 删除输入相关样式，现在只是输出页面

@media (max-width: 768px) {
  .mars-output-page {
    padding: 0;
  }
  
  .mars-content {
    padding: 16px;
    
    .mars-chat-message {
      gap: 10px;
      
      .mars-ai-avatar {
        width: 36px;
        height: 36px;
        padding: 5px;
        
        .avatar-img {
          width: 26px;
          height: 26px;
        }
      }
    }
  }
  
  .mars-error-state,
  .mars-empty-state {
    padding: 40px 20px;
    
         .mars-chat-message {
       .mars-ai-avatar {
         width: 36px;
         height: 36px;
         
         .avatar-img {
           width: 36px;
           height: 36px;
         }
       }
     }
  }
  
    .mars-content {
    .mars-chat-message {
      .mars-loading-dialog {
        padding: 12px 16px;
        min-width: 100px;
        
        .mars-loading-spinner {
          width: 16px;
          height: 16px;
          border-top: 2px solid #666;
        }
      }
    }
    
    /*
    .mars-generating {
      padding: 10px 12px;
      
      .mars-generating-indicator {
        .mars-generating-spinner {
          width: 16px;
          height: 16px;
        }
      }
    }
    */
  }
}
</style> 