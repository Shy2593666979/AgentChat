import { request } from "../utils/request"

// 用量统计请求参数
export interface UsageStatsRequest {
  agent?: string
  model?: string
  delta_days?: number
}

// Token使用量数据结构
export interface TokenUsageData {
  input_tokens: number
  output_tokens: number
  total_tokens: number
}

export interface UsageDataByDate {
  [date: string]: {
    agent: {
      [agentName: string]: TokenUsageData
    }
    model: {
      [modelName: string]: TokenUsageData
    }
  }
}

// 调用次数数据结构
export interface UsageCountByDate {
  [date: string]: {
    agent: {
      [agentName: string]: number
    }
    model: {
      [modelName: string]: number
    }
  }
}

// API响应结构
export interface ApiResponse<T> {
  status_code: number
  status_message: string
  data: T
}

// 获取Token使用量统计
export function getUsageStatsAPI(data: UsageStatsRequest) {
  return request<ApiResponse<UsageDataByDate>>({
    url: '/api/v1/usage',
    method: 'POST',
    data
  })
}

// 获取调用次数统计
export function getUsageCountAPI(data: UsageStatsRequest) {
  return request<ApiResponse<UsageCountByDate>>({
    url: '/api/v1/usage_count',
    method: 'POST',
    data
  })
}

// 获取模型列表
export function getUsageModelsAPI() {
  return request<ApiResponse<string[]>>({
    url: '/api/v1/usage/models_list',
    method: 'GET'
  })
}

// 获取智能体列表
export function getUsageAgentsAPI() {
  return request<ApiResponse<string[]>>({
    url: '/api/v1/usage/agents_list',
    method: 'GET'
  })
}


