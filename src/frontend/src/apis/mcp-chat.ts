import { request } from "../utils/request"

// MCP 对话相关接口类型定义
export interface MCPTask {
  id: string
  messages: MCPMessage[]
  created_time: string
  updated_time: string
}

export interface MCPMessage {
  query: string
  content: MCPContent[]
}

export interface MCPContent {
  type: 'text' | 'event' | 'interrupt'
  data: any
}

export interface ApiResponse<T> {
  status_code: number
  status_message: string
  data: T
}

// 获取任务列表
export function getTaskListAPI() {
  return request<ApiResponse<MCPTask[]>>({
    url: '/api/v1/mcp/register/task/list',
    method: 'GET'
  })
}

// 创建新任务
export function createTaskAPI() {
  return request<ApiResponse<MCPTask>>({
    url: '/api/v1/mcp/register/task/create',
    method: 'POST'
  })
}

// 删除任务
export function deleteTaskAPI(taskId: string) {
  return request<ApiResponse<any>>({
    url: '/api/v1/mcp/register/task/delete',
    method: 'POST',
    data: { task_id: taskId }
  })
}

// 发送消息（流式响应，需要特殊处理）
export function sendMessageAPI(query: string, taskId: string) {
  const token = localStorage.getItem('token')
  return fetch('/api/v1/mcp/register/completion', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    },
    body: JSON.stringify({
      query,
      task_id: taskId
    })
  })
}

// HITL Approve
export function hitlApproveAPI(taskId: string) {
  const token = localStorage.getItem('token')
  return fetch('/api/v1/mcp/register/completion/hitl/approve', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    },
    body: JSON.stringify({
      task_id: taskId
    })
  })
}

// HITL Reject
export function hitlRejectAPI(taskId: string, feedback: string) {
  const token = localStorage.getItem('token')
  return fetch('/api/v1/mcp/register/completion/hitl/reject', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    },
    body: JSON.stringify({
      task_id: taskId,
      feedback
    })
  })
}
