import { fetchEventSource } from '@microsoft/fetch-event-source'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

// 生成灵寻的指导提示（流式）
export const generateLingSeekGuidePromptAPI = async (
  data: {
    query: string
    tools?: string[]
    web_search?: boolean
    mcp_servers?: string[]
  },
  onMessage: (data: any) => void,
  onError?: (error: any) => void,
  onClose?: () => void
) => {
  const token = localStorage.getItem('token')
  
  console.log('=== generateLingSeekGuidePromptAPI 调用 ===')
  console.log('参数:', data)
  console.log('Token:', token ? `${token.substring(0, 20)}...` : '无')
  console.log('请求 URL:', `${BASE_URL}/api/v1/workspace/lingseek/guide_prompt`)
  
  const ctrl = new AbortController()
  
  try {
    await fetchEventSource(`${BASE_URL}/api/v1/workspace/lingseek/guide_prompt`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data),
      signal: ctrl.signal,
      openWhenHidden: true,
      onmessage(event) {
        console.log('📨 收到原始消息:', event.data)
        if (event.data) {
          try {
            // 后端返回的是 JSON 格式: { "event": "...", "data": { "chunk": "..." } }
            const parsedData = JSON.parse(event.data)
            console.log('📦 解析后的数据:', parsedData)
            
            if (parsedData.data && parsedData.data.chunk) {
              const chunk = parsedData.data.chunk
              console.log('📝 提取的 chunk:', chunk)
              onMessage(chunk)
            }
          } catch (error) {
            console.error('❌ JSON 解析失败:', error, '原始数据:', event.data)
            // 如果解析失败，尝试直接使用原始数据
            onMessage(event.data)
          }
        }
      },
      onerror(err) {
        console.error('Stream 错误:', err)
        onError?.(err)
        // 不要 throw，而是中断连接
        ctrl.abort()
      },
      onclose() {
        console.log('Stream 关闭')
        onClose?.()
      }
    })
  } catch (error) {
    console.error('fetchEventSource 异常:', error)
    if (error.name !== 'AbortError') {
      onError?.(error)
    }
  }
}

// 根据用户反馈重新生成指导提示（流式）
export const regenerateLingSeekGuidePromptAPI = async (
  data: {
    query: string
    guide_prompt: string
    feedback: string
    web_search?: boolean
    plugins?: string[]
    mcp_servers?: string[]
  },
  onMessage: (data: any) => void,
  onError?: (error: any) => void,
  onClose?: () => void
) => {
  const token = localStorage.getItem('token')
  
  console.log('开始调用 guide_prompt/feedback 接口，参数:', data)
  
  const ctrl = new AbortController()
  
  try {
    await fetchEventSource(`${BASE_URL}/api/v1/workspace/lingseek/guide_prompt/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data),
      signal: ctrl.signal,
      openWhenHidden: true,
      onmessage(event) {
        console.log('📨 收到原始消息:', event.data)
        if (event.data) {
          try {
            // 后端返回的是 JSON 格式: { "event": "...", "data": { "chunk": "..." } }
            const parsedData = JSON.parse(event.data)
            console.log('📦 解析后的数据:', parsedData)
            
            if (parsedData.data && parsedData.data.chunk) {
              const chunk = parsedData.data.chunk
              console.log('📝 提取的 chunk:', chunk)
              onMessage(chunk)
            }
          } catch (error) {
            console.error('❌ JSON 解析失败:', error, '原始数据:', event.data)
            // 如果解析失败，尝试直接使用原始数据
            onMessage(event.data)
          }
        }
      },
      onerror(err) {
        console.error('Stream 错误:', err)
        onError?.(err)
        ctrl.abort()
      },
      onclose() {
        console.log('Stream 关闭')
        onClose?.()
      }
    })
  } catch (error) {
    console.error('fetchEventSource 异常:', error)
    if (error.name !== 'AbortError') {
      onError?.(error)
    }
  }
}

// 生成灵寻任务列表（流式）
export const generateLingSeekTasksAPI = async (
  data: {
    guide_prompt: string
  },
  onMessage: (data: any) => void,
  onError?: (error: any) => void,
  onClose?: () => void
) => {
  const token = localStorage.getItem('token')
  
  console.log('开始调用 task 接口，参数:', data)
  
  const ctrl = new AbortController()
  
  try {
    await fetchEventSource(`${BASE_URL}/api/v1/workspace/lingseek/task`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data),
      signal: ctrl.signal,
      openWhenHidden: true,
      onmessage(event) {
        console.log('📨 收到原始消息:', event.data)
        if (event.data) {
          try {
            // 后端返回的是 JSON 格式: { "event": "...", "data": { "chunk": "..." } }
            const parsedData = JSON.parse(event.data)
            console.log('📦 解析后的数据:', parsedData)
            
            if (parsedData.data && parsedData.data.chunk) {
              const chunk = parsedData.data.chunk
              console.log('📝 提取的 chunk:', chunk)
              onMessage(chunk)
            }
          } catch (error) {
            console.error('❌ JSON 解析失败:', error, '原始数据:', event.data)
            // 如果解析失败，尝试直接使用原始数据
            onMessage(event.data)
          }
        }
      },
      onerror(err) {
        console.error('Stream 错误:', err)
        onError?.(err)
        ctrl.abort()
      },
      onclose() {
        console.log('Stream 关闭')
        onClose?.()
      }
    })
  } catch (error) {
    console.error('fetchEventSource 异常:', error)
    if (error.name !== 'AbortError') {
      onError?.(error)
    }
  }
}

// 开始执行灵寻任务（流式）
export const startLingSeekTaskAPI = async (
  data: {
    query: string
    guide_prompt: string
    web_search?: boolean
    plugins?: string[]
    mcp_servers?: string[]
  },
  onMessage: (data: any) => void,
  onTaskGraph?: (graph: any) => void,  // 处理任务图数据
  onStepResult?: (stepData: { title: string; message: string }) => void,  // 处理步骤结果
  onTaskResult?: (message: string) => void,  // 新增：处理任务最终结果
  onError?: (error: any) => void,
  onClose?: () => void
) => {
  const token = localStorage.getItem('token')
  
  console.log('开始调用 task_start 接口，参数:', data)
  
  const ctrl = new AbortController()
  
  try {
    await fetchEventSource(`${BASE_URL}/api/v1/workspace/lingseek/task_start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data),
      signal: ctrl.signal,
      openWhenHidden: true,
      onmessage(event) {
        console.log('📨 收到原始消息:', event.data)
        if (event.data) {
          try {
            // 后端返回的是 JSON 格式: { "event": "...", "data": {...} }
            const parsedData = JSON.parse(event.data)
            console.log('📦 解析后的数据:', parsedData)
            
            // 处理不同类型的事件
            if (parsedData.event === 'generate_tasks' && parsedData.data?.graph) {
              // 处理任务图数据
              console.log('📊 收到任务图数据:', parsedData.data.graph)
              onTaskGraph?.(parsedData.data.graph)
            } else if (parsedData.event === 'step_result' && parsedData.data?.title && parsedData.data?.message) {
              // 处理步骤执行结果
              console.log('✅ 收到步骤结果:', parsedData.data)
              onStepResult?.({ title: parsedData.data.title, message: parsedData.data.message })
            } else if (parsedData.event === 'task_result' && parsedData.data?.message) {
              // 处理任务最终结果（流式）
              console.log('📄 收到任务结果数据块:', parsedData.data.message)
              onTaskResult?.(parsedData.data.message)
            } else if (parsedData.data?.chunk) {
              // 处理文本块数据
              const chunk = parsedData.data.chunk
              console.log('📝 提取的 chunk:', chunk)
              onMessage(chunk)
            } else {
              // 其他类型的数据，直接传递
              onMessage(parsedData)
            }
          } catch (error) {
            console.error('❌ JSON 解析失败:', error, '原始数据:', event.data)
            // 如果解析失败，尝试直接使用原始数据
            onMessage(event.data)
          }
        }
      },
      onerror(err) {
        console.error('Stream 错误:', err)
        onError?.(err)
        ctrl.abort()
      },
      onclose() {
        console.log('Stream 关闭')
        onClose?.()
      }
    })
  } catch (error) {
    console.error('fetchEventSource 异常:', error)
    if (error.name !== 'AbortError') {
      onError?.(error)
    }
  }
}

