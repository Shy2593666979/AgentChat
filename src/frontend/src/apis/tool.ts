import { request } from "../utils/request"

// 工具相关接口类型定义
export interface ToolResponse {
  tool_id: string
  zh_name: string
  en_name: string
  user_id: string
  description: string
  logo_url: string
}

export interface ApiResponse<T> {
  status_code: number
  status_message: string
  data: T
}

// 获取所有工具
export function getAllToolsAPI() {
  return request<ApiResponse<ToolResponse[]>>({
    url: '/api/v1/tool/all',
    method: 'GET'
  })
}

// 获取个人工具
export function getOwnToolsAPI() {
  return request<ApiResponse<ToolResponse[]>>({
    url: '/api/v1/tool/own',
    method: 'POST'
  })
}

// 获取可见工具
export function getVisibleToolsAPI() {
  return request<ApiResponse<ToolResponse[]>>({
    url: '/api/v1/tool/visible',
    method: 'POST'
  })
}

// 创建工具
export function createToolAPI(data: {
  zh_name: string
  en_name: string
  description: string
  logo_url: string
}) {
  return request<ApiResponse<{ tool_id: string }>>({
    url: '/api/v1/tool/create',
    method: 'POST',
    data
  })
}

// 更新工具
export function updateToolAPI(data: {
  tool_id: string
  zh_name?: string
  en_name?: string
  description?: string
  logo_url?: string
}) {
  return request<ApiResponse<null>>({
    url: '/api/v1/tool/update',
    method: 'PUT',
    data
  })
}

// 删除工具
export function deleteToolAPI(data: { tool_id: string }) {
  return request<ApiResponse<null>>({
    url: '/api/v1/tool/delete',
    method: 'DELETE',
    data
  })
} 