import { request } from "../utils/request"

// 主要获取配置的默认内容
export function getConfigAPI() {
  return request({
    url: '/api/config',
    method: 'GET',
  })
}

// 修改配置的默认内容
export function updateConfigAPI(data:FormData) {
  return request({
    url: '/api/config',
    method: 'POST',
    data
  })
}
