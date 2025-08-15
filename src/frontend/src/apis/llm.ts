import { request } from "../utils/request"

// 大模型相关接口类型定义
export interface LLMResponse {
  llm_id: string
  model: string
  provider: string
  llm_type: string
  base_url: string
  api_key: string
  user_id: string
  update_time: string
  create_time: string
}

export interface CreateLLMRequest {
  model: string
  api_key: string
  base_url: string
  provider: string
  llm_type: string
}

export interface UpdateLLMRequest {
  llm_id: string
  model?: string
  api_key?: string
  base_url?: string
  provider?: string
  llm_type?: string
}

export interface ApiResponse<T> {
  status_code: number
  status_message: string
  data: T
}

// 获取所有大模型
export function getAllLLMsAPI() {
  return request<ApiResponse<Record<string, LLMResponse[]>>>({
    url: '/api/v1/llm/all',
    method: 'GET'
  })
}

// 获取个人大模型
export function getPersonalLLMsAPI() {
  return request<ApiResponse<Record<string, LLMResponse[]>>>({
    url: '/api/v1/llm/personal',
    method: 'POST'
  })
}

// 获取可见大模型
export function getVisibleLLMsAPI() {
  return request<ApiResponse<Record<string, LLMResponse[]>>>({
    url: '/api/v1/llm/visible',
    method: 'POST'
  })
}


// 获取智能体可用模型
export function getAgentModelsAPI() {
  return request<ApiResponse<LLMResponse[]>>({
    url: '/api/v1/agent/models',
    method: 'GET'
  })
}

// 获取大模型类型
export function getLLMSchemaAPI() {
  return request<ApiResponse<string[]>>({
    url: '/api/v1/llm/schema',
    method: 'GET'
  })
}

// 创建大模型
export function createLLMAPI(data: CreateLLMRequest) {
  return request<ApiResponse<null>>({
    url: '/api/v1/llm/create',
    method: 'POST',
    data
  })
}

// 更新大模型
export function updateLLMAPI(data: UpdateLLMRequest) {
  return request<ApiResponse<null>>({
    url: '/api/v1/llm/update',
    method: 'PUT',
    data
  })
}

// 删除大模型
export function deleteLLMAPI(data: { llm_id: string }) {
  return request<ApiResponse<null>>({
    url: '/api/v1/llm/delete',
    method: 'DELETE',
    data
  })
} 