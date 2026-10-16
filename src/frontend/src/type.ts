export  interface ConversationCreateType {
    name: string,
    agent_id: string,
    agent_type: string,
}
// searchType
export  interface searchType {
  name:string,
}

// 保持向后兼容的旧版智能体类型
export  interface AgentCreateType {
    name:string,
    description:string,
    parameter:string,
    code:string,
    logo:any
}

export  interface AgentUpdateType {
    name:string,
    description:string,
    parameter:string,
    code:string,
    logoFile:any
}

export  interface MsgLikeType {
    userInput:string,
    agentOutput:string,
}

// 兼容旧版本的CardListType，映射到Agent
export interface CardListType {
  code: string
  createTime: string
  description: string
  id: string
  isCustom: boolean
  logo: string
  name: string
  parameter: string
  type: string
}

export interface HistoryListType {
  agent: string
  conversationId: string
  name: string
  createTime: string
  logo:string
}

export interface ChatAttachment {
  url: string
  name: string
  size?: number
  mime?: string
}

export interface MessageType {
  agent?: { id: string; name: string; logo_url: string }
  attachments?: ChatAttachment[]
  content: string
  type?: string // 新增：支持消息类型
}

export interface ChatMessage {
  personMessage: MessageType
  aiMessage: MessageType
  eventInfo?: Array<{
    toolCallId?: string
    event_type: string
    show: boolean
    status: string
    message: string
  }>
}

// 知识库类型定义
export interface KnowledgeListType {
    id: string
    name: string
    description: string | null
    user_id: string | null
    create_time: string
    update_time: string
    count: number // 文件数量
    file_size: string // 文件总大小（已格式化）
}

// 知识库文件状态枚举
export enum KnowledgeFileStatus {
    FAIL = "❌失败",
    PROCESS = "🚀进行", 
    SUCCESS = "✅完成"
}

// 知识库文件类型定义
export interface KnowledgeFileType {
    id: string
    file_name: string
    knowledge_id: string
    status: KnowledgeFileStatus
    user_id: string
    oss_url: string
    file_size: number
    create_time: string
    update_time: string
}

// 新增智能体相关类型定义
export interface Agent {
  agent_id: string
  name: string
  description: string
  logo_url: string
  tool_ids: string[]
  llm_id: string
  mcp_ids: string[]
  system_prompt: string
  knowledge_ids: string[]
  agent_skill_ids?: string[]
  enable_memory: boolean
  created_time?: string
  updated_time?: string
  user_id?: string
  is_custom?: boolean
}

export interface AgentFormData {
  name: string
  description: string
  logo_url: string
  tool_ids: string[]
  llm_id: string
  mcp_ids: string[]
  system_prompt: string
  knowledge_ids: string[]
  agent_skill_ids: string[]
  enable_memory: boolean
}

export interface ToolOption {
  id: string
  name: string
  description: string
  logo_url?: string
  en_name?: string
  zh_name?: string
}

export interface LLMOption {
  id: string
  name: string
  model: string
  provider?: string
  api_key?: string
  base_url?: string
}

export interface MCPOption {
  id: string
  name: string
  description: string
  url?: string
  type?: string
  tools?: string[]
}

export interface KnowledgeOption {
  id: string
  name: string
  description: string | null
  user_id: string | null
  create_time?: string
  update_time?: string
  file_count?: number
}
