// 封装跟历史对话记录的接口函数
import { request } from "../utils/request"
import { DialogCreateType,AgentCreateType,AgentUpdateType ,MsgLikeType} from '../type'
// 主要创建对话窗口的信息
export function createDialogAPI(data:DialogCreateType) {
  return request({
    url: '/dialog',
    method: 'POST',
    data
  })
}
// 主要获得对话列表的功能
export function getDialogListAPI() {
  return request({
    url: '/dialog/list',
    method: 'GET',
  })
}
// 用户可自定义创建Agent，需要将所需的参数返回给后端保存到数据库当中
export function createAgentAPI(data:AgentCreateType) {
  return request({
    url: '/agent',
    method: 'POST',
    data
  })
}
// 获取Agents 的列表信息
export function getAgentListAPI() {
  return request({
    url: '/agent',
    method: 'GET',
  })
}

// 删除Agent
  export function deleteAgentAPI(id:string) {
    return request({
      url: '/agent',
      method: 'DELETE', 
      data:id,
    })
  }
  // 修改Agent 的信息
  export function updateAgentAPI(data: AgentUpdateType) {
    return request({
      url: '/agent',
      method: 'PUT',
      data
    })
  }
  // 根据用户输入的Agent名字进行去数据库模糊查询
  export function searchAgentAPI(name:string) {
    return request({
      url: '/agent/search',
      method: 'POST',
      data:name
    })
  }
  // 将用户每条存入的信息
  export function getHistoryMsgAPI(dialogId:string) {
    return request({
      url: '/history',
      method: 'GET',
      data:dialogId
    })
  }
// 点赞-拉踩用户点击点赞功能，需要前端将userInput和agentOutput 返回给后端进行存入数据库
export function MsgLikeCreateAPI(data: MsgLikeType) {
  return request({
    url: '/message/like',
    method: 'POST',
    data
  })
}
// 用户点击拉踩功能，需要前端将userInput和agentOutput 返回给后端进行存入数据库
export function MsgDisLikeAPI(data: MsgLikeType) {
  return request({
    url: '/message/down',
    method: 'POST',
    data
  })
}
