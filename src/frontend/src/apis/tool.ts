import { request } from "../utils/request"

// 工具相关接口类型定义
export interface ToolResponse {
  tool_id: string
  name: string  // 英文名称，大模型调用
  display_name: string  // 中文名称，显示给用户
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
    method: 'POST'
  })
}

// 获取个人工具
export function getOwnToolsAPI() {
  return request<ApiResponse<ToolResponse[]>>({
    url: '/api/v1/tool/user_defined',
    method: 'POST'
  })
}

// 获取可见工具
export function getVisibleToolsAPI() {
  return request<ApiResponse<ToolResponse[]>>({
    url: '/api/v1/tool/all',
    method: 'POST'
  })
}

// 创建工具
export function createToolAPI(data: {
  display_name: string  // 名称
  description: string
  logo_url: string
  auth_config?: any
  openapi_schema?: any
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
  display_name?: string
  description?: string
  logo_url?: string
  auth_config?: any
  openapi_schema?: any
}) {
  return request<ApiResponse<null>>({
    url: '/api/v1/tool/update',
    method: 'POST',
    data
  })
}

// 删除工具
export function deleteToolAPI(data: { tool_id: string }) {
  return request<ApiResponse<null>>({
    url: '/api/v1/tool/delete',
    method: 'POST',
    data
  })
}

// 获取默认工具头像
export function getDefaultToolLogoAPI() {
  return request<ApiResponse<{ logo_url: string }>>({
    url: '/api/v1/tool/default_logo',
    method: 'GET'
  })
}

// 上传文件
export function uploadFileAPI(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  
  return request<ApiResponse<string>>({
    url: '/api/v1/upload/upload',
    method: 'POST',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
