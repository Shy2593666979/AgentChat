import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface UserInfo {
  id: string
  username: string
  nickname?: string
  avatar?: string
  description?: string
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>('')
  const userInfo = ref<UserInfo | null>(null)
  const isLoggedIn = ref(false)

  // 初始化用户状态（从localStorage读取）
  const initUserState = () => {
    const storedToken = localStorage.getItem('token')
    const storedUserInfo = localStorage.getItem('userInfo')
    
    if (storedToken) {
      token.value = storedToken
      isLoggedIn.value = true
    }
    
    if (storedUserInfo) {
      try {
        userInfo.value = JSON.parse(storedUserInfo)
      } catch (error) {
        console.error('解析用户信息失败:', error)
      }
    }
  }

  // 设置用户信息
  const setUserInfo = (newToken: string, newUserInfo: UserInfo) => {
    token.value = newToken
    userInfo.value = newUserInfo
    isLoggedIn.value = true
    
    // 存储到localStorage
    localStorage.setItem('token', newToken)
    localStorage.setItem('userInfo', JSON.stringify(newUserInfo))
  }

  // 更新用户信息（不更新token）
  const updateUserInfo = (updatedInfo: Partial<UserInfo>) => {
    if (userInfo.value) {
      userInfo.value = { ...userInfo.value, ...updatedInfo }
      localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
    }
  }

  // 清除用户信息
  const clearUserInfo = () => {
    token.value = ''
    userInfo.value = null
    isLoggedIn.value = false
    
    // 清除localStorage
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  // 登出
  const logout = () => {
    clearUserInfo()
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    initUserState,
    setUserInfo,
    updateUserInfo,
    clearUserInfo,
    logout
  }
}, {
  persist: true // 启用持久化
}) 