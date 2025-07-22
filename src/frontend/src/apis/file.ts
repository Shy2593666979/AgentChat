import { request } from "../utils/request"

// 文件上传接口
export function uploadFileAPI(data: FormData) {
  return request({
    url: '/api/v1/upload',
    method: 'POST',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
} 