import { request } from '../utils/request'

export interface LoginForm {
  username: string
  password: string
}

export interface RegisterForm {
  user_name: string
  user_email?: string
  user_password: string
}

export interface LoginResponse {
  success: boolean
  message?: string
  token?: string
  userInfo?: {
    id: string
    username: string
    nickname?: string
    avatar?: string
  }
}

export interface UserIconsResponse {
  status_code: number
  status_message: string
  data: string[]
}

export interface UpdateUserResponse {
  status_code: number
  status_message: string
  data: any
}

// 登录接口
export const loginAPI = (data: LoginForm) => {
  return request<LoginResponse>({
    url: '/api/v1/user/login',
    method: 'POST',
    data: {
      user_name: data.username,
      user_password: data.password
    }
  })
}

// 注册接口
export const registerAPI = (data: RegisterForm) => {
  return request({
    url: '/api/v1/user/register',
    method: 'POST',
    data
  })
}

// 登出接口
export const logoutAPI = () => {
  return request({
    url: '/api/v1/user/logout',
    method: 'POST'
  })
}

// 获取用户信息接口
export const getUserInfoAPI = (userId: string) => {
  return request({
    url: `/api/v1/user/info?user_id=${userId}`,
    method: 'GET'
  })
}

// 更新用户信息接口
export const updateUserInfoAPI = (userId: string, userAvatar?: string, userDescription?: string) => {
  return request<UpdateUserResponse>({
    url: '/api/v1/user/update',
    method: 'PUT',
    data: {
      user_id: userId,
      user_avatar: userAvatar,
      user_description: userDescription
    }
  })
}

// 获取用户头像选择接口
export const getUserIconsAPI = () => {
  return request<UserIconsResponse>({
    url: '/api/v1/user/icons',
    method: 'GET'
  })
}

// 检查token是否有效
export const checkTokenAPI = () => {
  return request({
    url: '/api/v1/auth/check',
    method: 'GET'
  })
} 