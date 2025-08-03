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

// MCP用户配置相关接口
export interface MCPUserConfigCreateRequest {
  mcp_server_id: string
  config: any
}

export interface MCPUserConfigUpdateRequest {
  server_id: string
  config: any
}

export interface MCPUserConfig {
  config_id: string
  mcp_server_id: string
  user_id: string
  config: any
  create_time: string
  update_time: string
}

export interface MCPUserConfigResponse {
  status_code: number
  status_message: string
  data: MCPUserConfig | null
}

// 获取用户配置
export const getMCPUserConfigAPI = (server_id: string) => {
  return request<MCPUserConfigResponse>({
    url: `/api/v1/mcp_user_config?server_id=${server_id}`,
    method: 'GET'
  })
}

// 创建用户配置
export const createMCPUserConfigAPI = (data: MCPUserConfigCreateRequest) => {
  return request<MCPUserConfigResponse>({
    url: '/api/v1/mcp_user_config/create',
    method: 'POST',
    data
  })
}

// 更新用户配置
export const updateMCPUserConfigAPI = (data: MCPUserConfigUpdateRequest) => {
  return request<MCPServerSingleResponse>({
    url: '/api/v1/mcp_user_config/update',
    method: 'PUT',
    data
  })
}

// 删除用户配置
export const deleteMCPUserConfigAPI = (config_id: string) => {
  return request<MCPServerSingleResponse>({
    url: '/api/v1/mcp_user_config/delete',
    method: 'DELETE',
    data: { config_id }
  })
}