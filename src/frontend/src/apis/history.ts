// 封装跟历史对话记录的接口函数
import { request } from "../utils/request"
import { ConversationCreateType, MsgLikeType } from '../type'

// 主要创建对话窗口的信息  json 格式
export function createConversationAPI(data: ConversationCreateType) {
  return request({
    url: '/api/v1/conversation',
    method: 'POST',
    data: {
      name: data.name,
      agent_id: data.agent_id,
      agent_type: data.agent_type
    }
  })
}

// 主要删除对话窗口的信息  json 格式
export function deleteConversationAPI(conversationId:string) {
  return request({
    url: '/api/v1/conversation',
    method: 'DELETE',
    data: {
      conversation_id: conversationId
    }
  })
}

// 在原会话中切换智能体，不创建新的会话。
export function switchConversationAgentAPI(conversationId: string, agentId: string) {
  return request({ url: '/api/v1/conversation', method: 'PUT', data: { conversation_id: conversationId, agent_id: agentId } })
}

// 主要获得对话列表的功能
export function getConversationListAPI() {
  return request({
    url: '/api/v1/conversation/list',
    method: 'GET',
  })
}

// 获取历史消息记录 - 根据对话ID
export function getHistoryMsgAPI(conversationId: string) {
  return request({
    url: '/api/v1/history',
    method: 'GET',
    params: {
      conversation_id: conversationId
    }
  })
}

// 点赞-拉踩用户点击点赞功能，需要前端将userInput和agentOutput 返回给后端进行存入数据库  json格式
export function MsgLikeCreateAPI(data: MsgLikeType) {
  return request({
    url: '/api/v1/message/like',
    method: 'POST',
    data: { user_input: data.userInput, agent_output: data.agentOutput }
  })
}

// 用户点击拉踩功能，需要前端将userInput和agentOutput 返回给后端进行存入数据库   json格式
export function MsgDisLikeAPI(data: MsgLikeType) {
  return request({
    url: '/api/v1/message/down',
    method: 'POST',
    data: { user_input: data.userInput, agent_output: data.agentOutput }
  })
}
