import { request } from "../utils/request"

// 获取这俩默认的    /api/default/parameter           /api/default/code
export function defaultParameterAPI() {
  return request({
    url: ' /api/default/parameter',
    method: 'GET',
  })
}

export function defaultCodeAPI() {
  return request({
    url: '/api/default/code',
    method: 'GET',
  })
}
