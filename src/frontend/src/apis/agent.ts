import { request } from "../utils/request"

// 智能体相关接口类型定义
export interface AgentCreateRequest {
  name: string
  description: string
  logo_url: string
  tool_ids: string[]
  llm_id: string
  mcp_ids: string[]
  system_prompt: string
  knowledge_ids: string[]
  enable_memory: boolean
}

export interface AgentUpdateRequest {
  agent_id: string
  name?: string
  description?: string
  logo_url?: string
  tool_ids?: string[]
  llm_id?: string
  mcp_ids?: string[]
  system_prompt?: string
  knowledge_ids?: string[]
  enable_memory?: boolean
}

export interface AgentResponse {
  agent_id: string
  name: string
  description: string
  logo_url: string
  tool_ids: string[]
  llm_id: string
  mcp_ids: string[]
  system_prompt: string
  knowledge_ids: string[]
  enable_memory: boolean
}

export interface ApiResponse<T> {
  status_code: number
  status_message: string
  data: T
}

// 创建智能体
export function createAgentAPI(data: AgentCreateRequest) {
  return request<ApiResponse<null>>({
    url: '/api/v1/agent',
    method: 'POST',
    data
  })
}

// 获取智能体列表
export function getAgentsAPI() {
  return request<ApiResponse<AgentResponse[]>>({
    url: '/api/v1/agent',
    method: 'GET'
  })
}

// 根据ID获取智能体详情
export function getAgentByIdAPI(agentId: string) {
  console.log('🔍 getAgentByIdAPI - 查找智能体ID:', agentId, '类型:', typeof agentId)
  return getAgentsAPI().then(response => {
    console.log('📦 getAgentsAPI 响应:', response.data)
    if (response.data.status_code === 200) {
      console.log('📋 所有智能体列表:', response.data.data.map(a => ({ 
        agent_id: a.agent_id, 
        id: (a as any).id, 
        name: a.name, 
        agent_id_type: typeof a.agent_id,
        id_type: typeof (a as any).id
      })))
      const agent = response.data.data.find(a => {
        // 支持多种ID字段名和类型比较
        const agentIdMatch = a.agent_id === agentId || String(a.agent_id) === String(agentId)
        const idMatch = (a as any).id === agentId || String((a as any).id) === String(agentId)
        const isMatch = agentIdMatch || idMatch
        console.log(`🔎 比较智能体 "${a.name}": agent_id=${a.agent_id} (${typeof a.agent_id}), id=${(a as any).id} (${typeof (a as any).id}), 目标=${agentId} (${typeof agentId}), 匹配=${isMatch}`)
        return isMatch
      })
      if (agent) {
        console.log('✅ 找到智能体:', agent)
        return {
          data: {
            status_code: 200,
            status_message: 'SUCCESS',
            data: agent
          }
        } as { data: ApiResponse<AgentResponse> }
      } else {
        console.log('❌ 未找到智能体，ID:', agentId)
        return {
          data: {
            status_code: 404,
            status_message: '智能体不存在',
            data: null
          }
        } as { data: ApiResponse<null> }
      }
    }
    return {
      data: {
        status_code: response.data.status_code,
        status_message: response.data.status_message,
        data: null
      }
    } as { data: ApiResponse<null> }
  })
}

// 删除智能体
export function deleteAgentAPI(data: { agent_id: string }) {
  return request<ApiResponse<null>>({
    url: '/api/v1/agent',
    method: 'DELETE',
    data
  })
}

// 更新智能体
export function updateAgentAPI(data: AgentUpdateRequest) {
  return request<ApiResponse<null>>({
    url: '/api/v1/agent',
    method: 'PUT',
    data
  })
}

// 搜索智能体
export function searchAgentsAPI(data: { name: string }) {
  return request<ApiResponse<Array<{
    agent_id: string
    name: string
    description: string
    logo_url: string
  }>>>({
    url: '/api/v1/agent/search',
    method: 'POST',
    data
  })
}

// 获取默认参数（保留原有接口）
export function defaultParameterAPI() {
  return request({
    url: '/api/default/parameter',
    method: 'GET',
  })
}

// 获取默认代码（保留原有接口）
export function defaultCodeAPI() {
  return request({
    url: '/api/default/code',
    method: 'GET',
  })
}
