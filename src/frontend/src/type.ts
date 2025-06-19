export  interface DialogCreateType {
    agent:string,
}
// searchType
export  interface searchType {
  name:string,
}
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
  dialogId: string
  name: string
  createTime: string
  logo:string
}

export interface MessageType {
  content: string
}
export interface ChatMessage {
  personMessage: MessageType
  aiMessage: MessageType
}
export interface KnowledgeListType{
    id: string,
    name: string,
    description: string,
    userId: string,
    updateTime: string
}