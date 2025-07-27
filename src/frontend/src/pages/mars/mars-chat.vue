<template>
  <div class="mars-output-page">
    <!-- AI输出展示区域 -->
    <div class="mars-output-container" ref="outputContainer">
      <!-- 加载状态 -->
      <div v-if="isLoading && !aiContent" class="mars-loading-state">
        <div class="mars-chat-message">
          <div class="mars-ai-avatar">
            <img src="../../assets/robot.svg" alt="AI Assistant" class="avatar-img" />
          </div>
          <div class="mars-loading-text">Mars Agent 正在处理您的请求...</div>
        </div>
      </div>

      <!-- AI回复内容 -->
      <div v-if="aiContent" class="mars-content">
        <div class="mars-chat-message">
          <div class="mars-ai-avatar">
            <img src="../../assets/robot.svg" alt="AI Assistant" class="avatar-img" />
          </div>
          <div class="mars-response">
            <MdPreview 
              editorId="mars-output" 
              :modelValue="aiContent"
              :showCodeRowNumber="true"
            />
          </div>
        </div>
        
        <!-- 生成状态指示器 -->
        <div v-if="isLoading" class="mars-generating">
          <div class="mars-generating-indicator">
            <span class="mars-generating-dot"></span>
            正在生成中...
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
      <div v-if="!aiContent && !isLoading && !hasError" class="mars-empty-state">
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
import { ref, nextTick, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import { ElMessage } from 'element-plus'
import { MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'

// 响应式数据
const route = useRoute()
const router = useRouter()
const aiContent = ref('')
const isLoading = ref(false)
const hasError = ref(false)
const errorMessage = ref('')
const abortController = ref<AbortController | null>(null)
const outputContainer = ref<HTMLElement>()

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (outputContainer.value) {
      outputContainer.value.scrollTop = outputContainer.value.scrollHeight
    }
  })
}

// 返回首页
const backToHome = () => {
  router.push('/')
}

// 重试 - 返回首页
const retryFromHome = () => {
  router.push('/')
}

// 发送消息
const sendMessage = async (userMessage: string) => {
  if (!userMessage.trim() || isLoading.value) return
  
  // 重置状态
  aiContent.value = ''
  hasError.value = false
  errorMessage.value = ''
  isLoading.value = true
  abortController.value = new AbortController()

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
          
          // 尝试解析JSON
          try {
            const jsonString = rawData.replace(/'/g, '"')
            const parsedData = JSON.parse(jsonString)
            
            const chunkData = parsedData.data || ''
            console.log(`类型: ${parsedData.type}, 内容: "${chunkData}"`)
            
            // 直接追加到AI内容中
            if (chunkData !== undefined && chunkData !== null) {
              aiContent.value += chunkData
              console.log('添加内容:', `"${chunkData}"`, '当前总长度:', aiContent.value.length)
              scrollToBottom()
            }
          } catch (parseError) {
            console.error('JSON解析失败:', parseError)
            // 如果解析失败，直接添加原始数据
            aiContent.value += rawData
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
      },
      onerror(err) {
        console.error('Mars聊天连接错误:', err)
        isLoading.value = false
        abortController.value = null
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

// 页面加载时的初始化
onMounted(() => {
  // 检查是否有来自首页的消息
  const messageFromHome = route.query.message
  if (messageFromHome && typeof messageFromHome === 'string') {
    // 清除URL中的message参数，保持URL简洁
    router.replace({
      path: '/mars',
      query: {}  // 清空所有query参数
    })
    
    // 自动发送消息
    nextTick(() => {
      sendMessage(messageFromHome)
    })
  }
})
</script>

<style lang="scss" scoped>
.mars-output-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  display: flex;
  flex-direction: column;
  padding: 0;
}

.mars-output-container {
  flex: 1;
  width: 100%;
  background: white;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

// 加载状态样式
.mars-loading-state {
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
    
    .mars-loading-text {
      font-size: 18px;
      color: #666;
      margin-bottom: 24px;
      font-weight: 500;
    }
  }
}



// AI内容展示样式
.mars-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  
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
  
  .mars-generating {
    margin-top: 24px;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 12px;
    border-left: 4px solid #722ed1;
    
    .mars-generating-indicator {
      display: flex;
      align-items: center;
      gap: 8px;
      color: #666;
      font-size: 14px;
      
      .mars-generating-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #722ed1;
        animation: pulse 1.5s ease-in-out infinite;
      }
    }
  }
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

// 滚动条样式
.mars-content {
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;
    
    &:hover {
      background: #a8a8a8;
    }
  }
}

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
  
  .mars-loading-state,
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
}
</style> 