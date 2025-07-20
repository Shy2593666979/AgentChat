import { request } from '../utils/request'

export interface CreateMCPServerRequest {
  server_name: string
  url: string
  type: string
  config?: any | string
}

export interface MCPServerTool {
  name: string
  description: string
  input_schema: {
    type: string
    title: string
    required?: string[]
    properties?: any
    description?: string
  }
}

export interface MCPServerConfig {
  key: string
  label: string
  value: string
}

export interface MCPServer {
  mcp_server_id: string
  server_name: string
  url: string
  type: string
  config?: MCPServerConfig[] | any
  config_enabled: boolean
  tools: string[]
  params: MCPServerTool[]
  logo_url: string
  user_id: string
  user_name: string
  create_time: string
  update_time: string
}

export interface MCPServerResponse {
  status_code: number
  status_message: string
  data: MCPServer[] | null
}

export interface MCPServerSingleResponse {
  status_code: number
  status_message: string
  data: null
}

// 创建MCP服务器
export const createMCPServerAPI = (data: CreateMCPServerRequest) => {
  return request<MCPServerSingleResponse>({
    url: '/api/v1/mcp_server',
    method: 'POST',
    data
  })
}

// 获取MCP服务器列表
export const getMCPServersAPI = () => {
  return request<MCPServerResponse>({
    url: '/api/v1/mcp_server',
    method: 'GET'
  })
}

// 删除MCP服务器
export const deleteMCPServerAPI = (server_id: string) => {
  return request<MCPServerSingleResponse>({
    url: '/api/v1/mcp_server',
    method: 'DELETE',
    data: { server_id }
  })
} 