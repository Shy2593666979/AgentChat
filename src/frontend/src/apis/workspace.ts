import { request } from '../utils/request'

// 获取工作区插件列表
export const getWorkspacePluginsAPI = async () => {
  return request({
    url: '/api/v1/workspace/plugins',
    method: 'get'
  })
}

// 获取工作区会话列表
export const getWorkspaceSessionsAPI = async () => {
  return request({
    url: '/api/v1/workspace/session',
    method: 'get'
  })
}

// 创建工作区会话
export const createWorkspaceSessionAPI = async (data: { title?: string, contexts?: any }) => {
  return request({
    url: '/api/v1/workspace/session',
    method: 'post',
    data
  })
}

// 获取工作区会话信息
export const getWorkspaceSessionInfoAPI = async (sessionId: string) => {
  return request({
    url: `/api/v1/workspace/session/${sessionId}`,
    method: 'post'
  })
}

// 删除工作区会话  
export const deleteWorkspaceSessionAPI = async (sessionId: string) => {
  return request({
    url: `/api/v1/workspace/session`,
    method: 'delete',
    params: {
      session_id: sessionId
    }
  })
}

// 工作区日常对话接口
export interface WorkSpaceSimpleTask {
  query: string
  model_id: string
  plugins: string[]
  mcp_servers: string[]
}

export const workspaceSimpleChatAPI = async (data: WorkSpaceSimpleTask) => {
  return request({
    url: '/api/v1/workspace/simple/chat',
    method: 'post',
    data,
    responseType: 'stream'
  })
}
