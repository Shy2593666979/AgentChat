import { request } from '../utils/request'

// Agent Skill 类型定义
export interface AgentSkillFile {
  name: string
  path: string
  type: 'file'
  content: string
}

export interface AgentSkillFolder {
  name: string
  path: string
  type: 'folder'
  folder: (AgentSkillFile | AgentSkillFolder)[]
}

export interface AgentSkill {
  id: string
  name: string
  description: string
  user_id: string
  folder: AgentSkillFolder
  create_time: string
  update_time: string
}

export interface ApiResponse<T> {
  status_code: number
  status_message: string
  data: T
}

// 创建 Agent Skill 请求
export interface CreateAgentSkillRequest {
  name: string
  description: string
}

// 删除 Agent Skill 请求
export interface DeleteAgentSkillRequest {
  agent_skill_id: string
}

// 更新文件请求
export interface UpdateAgentSkillFileRequest {
  agent_skill_id: string
  path: string
  content: string
}

// 添加文件请求
export interface AddAgentSkillFileRequest {
  agent_skill_id: string
  path: string
  name: string
}

// 删除文件请求
export interface DeleteAgentSkillFileRequest {
  agent_skill_id: string
  path: string
  name: string
}

// 获取用户所有 Agent Skills
export function getAgentSkillsAPI() {
  return request<ApiResponse<AgentSkill[]>>({
    url: '/api/v1/agent_skill/all',
    method: 'GET'
  })
}

// 创建 Agent Skill
export function createAgentSkillAPI(data: CreateAgentSkillRequest) {
  return request<ApiResponse<AgentSkill>>({
    url: '/api/v1/agent_skill/create',
    method: 'POST',
    data
  })
}

// 删除 Agent Skill
export function deleteAgentSkillAPI(data: DeleteAgentSkillRequest) {
  return request<ApiResponse<null>>({
    url: '/api/v1/agent_skill/delete',
    method: 'POST',
    data
  })
}

// 更新 Agent Skill 文件
export function updateAgentSkillFileAPI(data: UpdateAgentSkillFileRequest) {
  return request<ApiResponse<AgentSkill>>({
    url: '/api/v1/agent_skill/file/update',
    method: 'POST',
    data
  })
}

// 添加 Agent Skill 文件
export function addAgentSkillFileAPI(data: AddAgentSkillFileRequest) {
  return request<ApiResponse<AgentSkill>>({
    url: '/api/v1/agent_skill/file/add',
    method: 'POST',
    data
  })
}

// 上传 Agent Skill 文件
export function uploadAgentSkillFileAPI(formData: FormData) {
  return request<ApiResponse<AgentSkill>>({
    url: '/api/v1/agent_skill/file/upload',
    method: 'POST',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 删除 Agent Skill 文件
export function deleteAgentSkillFileAPI(data: DeleteAgentSkillFileRequest) {
  return request<ApiResponse<AgentSkill>>({
    url: '/api/v1/agent_skill/file/delete',
    method: 'POST',
    data
  })
}
