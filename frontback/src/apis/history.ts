// 封装跟历史对话记录的接口函数
import { request } from "../utils/request"
import { dialogCreateType } from '../type'
// 主要创建对话窗口的信息
export function getDialogCreateAPI(data:dialogCreateType) {
  return request({
    url: '/dialog',
    method: 'POST',
    data
  })
}