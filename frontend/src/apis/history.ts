// 封装跟历史对话记录的接口函数
import { request } from "../utils/request"
import { DialogCreateType, AgentCreateType, AgentUpdateType, MsgLikeType } from '../type'
// 主要创建对话窗口的信息  json 格式
export function createDialogAPI(data: DialogCreateType) {
  return request({
    url: '/api/dialog',
    method: 'POST',
    data:JSON.stringify({'agent':data.agent})
  })
}

// 主要删除对话窗口的信息  json 格式
export function deleteDialogAPI(dialogId:string) {
  return request({
    url: '/api/dialog',
    method: 'DELETE',
    data:JSON.stringify({'dialogId':dialogId})
  })
}

// 主要获得对话列表的功能 xxx
export function getDialogListAPI() {
  return request({
    url: '/api/dialog/list',
    method: 'GET',
  })
}
// 用户可自定义创建Agent，需要将所需的参数返回给后端保存到数据库当中  xxx
export function createAgentAPI(data:FormData) {
  return request({
    url: '/api/agent',
    method: 'POST',
    data
  })
}
// 获取Agents 的列表信息
export function getAgentListAPI() {
  return request({
    url: '/api/agent',
    method: 'GET',
  })
}

// 删除Agent  xxx
export function deleteAgentAPI(id: FormData) {
  return request({
    url: '/api/agent',
    method: 'DELETE',
    data: id,
  })
}
// 修改Agent 的信息 xxx
export function updateAgentAPI(data: FormData) {
  return request({
    url: '/api/agent',
    method: 'PUT',
    data
  })
}
// 根据用户输入的Agent名字进行去数据库模糊查询 xxx
export function searchAgentAPI(data: FormData) {
  return request({
    url: '/api/agent/search',
    method: 'POST',
    data
  })
}
// 将用户每条存入的信息  json格式
export function getHistoryMsgAPI(dialogId: string) {
  return request({
    url: '/api/history',
    method: 'POST',
    data: JSON.stringify({ "dialogId": dialogId })
  })
}
// 点赞-拉踩用户点击点赞功能，需要前端将userInput和agentOutput 返回给后端进行存入数据库  json格式
export function MsgLikeCreateAPI(data: MsgLikeType) {
  return request({
    url: '/api/message/like',
    method: 'POST',
    data
  })
}
// 用户点击拉踩功能，需要前端将userInput和agentOutput 返回给后端进行存入数据库   json格式
export function MsgDisLikeAPI(data: MsgLikeType) {
  return request({
    url: '/api/message/down',
    method: 'POST',
    data
  })
}
