import { request } from "../utils/request"

// 统一响应模型
export interface UnifiedResponse<T = any> {
  status_code: number
  status_message: string
  data?: T
}

// 知识库响应类型
export interface KnowledgeResponse {
  id: string
  name: string
  description: string | null
  user_id: string | null
  create_time: string
  update_time: string
  count: number // 文件数量
  file_size: string // 文件总大小（已格式化）
}

// 知识库创建请求
export interface KnowledgeCreateRequest {
  knowledge_name: string
  knowledge_desc?: string
}

// 知识库更新请求
export interface KnowledgeUpdateRequest {
  knowledge_id: string
  knowledge_name?: string
  knowledge_desc?: string
}

// 知识库删除请求
export interface KnowledgeDeleteRequest {
  knowledge_id: string
}

// 知识库检索请求
export interface KnowledgeRetrievalRequest {
  query: string
  knowledge_id: string | string[]
  top_k?: number
}

// 查询知识库列表
export function getKnowledgeListAPI() {
  return request<UnifiedResponse<KnowledgeResponse[]>>({
    url: '/api/v1/knowledge/select',
    method: 'GET'
  })
}

// 创建知识库
export function createKnowledgeAPI(data: KnowledgeCreateRequest) {
  return request<UnifiedResponse<null>>({
    url: '/api/v1/knowledge/create',
    method: 'POST',
    data
  })
}

// 更新知识库
export function updateKnowledgeAPI(data: KnowledgeUpdateRequest) {
  return request<UnifiedResponse<null>>({
    url: '/api/v1/knowledge/update',
    method: 'PUT',
    data
  })
}

// 删除知识库
export function deleteKnowledgeAPI(data: KnowledgeDeleteRequest) {
  return request<UnifiedResponse<null>>({
    url: '/api/v1/knowledge/delete',
    method: 'DELETE',
    data
  })
}

// 知识库检索
export function knowledgeRetrievalAPI(data: KnowledgeRetrievalRequest) {
  return request<UnifiedResponse<string>>({
    url: '/api/v1/knowledge/retrieval',
    method: 'POST',
    data
  })
} 