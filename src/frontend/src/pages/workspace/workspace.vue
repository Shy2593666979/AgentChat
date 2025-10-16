<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, SwitchButton, Setting } from '@element-plus/icons-vue'
import { useUserStore } from '../../store/user'
import { logoutAPI, getUserInfoAPI } from '../../apis/auth'
import { 
  getWorkspaceSessionsAPI, 
  deleteWorkspaceSessionAPI 
} from '../../apis/workspace'

const router = useRouter()
const userStore = useUserStore()
const selectedSession = ref('')
const sessions = ref<any[]>([])
const loading = ref(false)

// 格式化时间
const formatTime = (timeStr: string) => {
  try {
    if (!timeStr) return '未知时间'
    
    const date = new Date(timeStr)
    if (isNaN(date.getTime())) {
      return '未知时间'
    }
    
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
    
    if (diffInHours < 1) return '刚刚'
    if (diffInHours < 24) return `${Math.floor(diffInHours)}小时前`
    if (diffInHours < 24 * 7) return `${Math.floor(diffInHours / 24)}天前`
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  } catch (error) {
    return '未知时间'
  }
}

// 获取会话列表
const fetchSessions = async () => {
  try {
    loading.value = true
    const response = await getWorkspaceSessionsAPI()
    if (response.data.status_code === 200) {
      sessions.value = response.data.data.map((session: any) => ({
        sessionId: session.session_id || session.id,
        title: session.title || '未命名会话',
        createTime: session.create_time || session.created_at || new Date().toISOString()
      }))
      console.log('工作区会话列表:', sessions.value)
    } else {
      ElMessage.error('获取会话列表失败')
    }
  } catch (error) {
    console.error('获取会话列表出错:', error)
    ElMessage.error('获取会话列表失败')
  } finally {
    loading.value = false
  }
}

// 删除会话
const deleteSession = async (sessionId: string, event: Event) => {
  event.stopPropagation()
  
  try {
    const response = await deleteWorkspaceSessionAPI(sessionId)
    if (response.data.status_code === 200) {
      ElMessage.success('会话删除成功')
      await fetchSessions()
      
      if (selectedSession.value === sessionId) {
        selectedSession.value = ''
        router.push('/workspace')
      }
    } else {
      ElMessage.error('删除会话失败')
    }
  } catch (error) {
    console.error('删除会话出错:', error)
    ElMessage.error('删除会话失败')
  }
}

// 选择会话 - 直接跳转到三列布局页面
const selectSession = (sessionId: string) => {
  selectedSession.value = sessionId
  router.push({
    name: 'taskGraphPage',
    query: {
      session_id: sessionId
    }
  })
}

// 用户下拉菜单命令处理
const handleUserCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/configuration')
      break
    case 'logout':
      await handleLogout()
      break
  }
}

// 退出登录
const handleLogout = async () => {
  try {
    await logoutAPI()
  } catch (error) {
    console.error('调用登出接口失败:', error)
  }
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

// 头像加载错误处理
const handleAvatarError = (event: Event) => {
  const target = event.target as HTMLImageElement
  if (target) {
    target.src = '/src/assets/user.svg'
  }
}

// 跳转到应用中心
const goToHomepage = () => {
  router.push('/homepage')
}

onMounted(async () => {
  userStore.initUserState()
  
  // 如果已登录但没有头像，则尝试获取用户信息
  if (userStore.isLoggedIn && userStore.userInfo && !userStore.userInfo.avatar) {
    try {
      const response = await getUserInfoAPI(userStore.userInfo.id)
      if (response.data.status_code === 200 && response.data.data) {
        const userData = response.data.data
        userStore.updateUserInfo({
          avatar: userData.user_avatar || userData.avatar || '/src/assets/user.svg',
          description: userData.user_description || userData.description
        })
      }
    } catch (error) {
      console.error('初始化时获取用户信息失败:', error)
    }
  }
  
  await fetchSessions()
})
</script>

<template>
  <div class="workspace-container">
    <!-- 顶部导航栏 -->
    <div class="workspace-nav">
      <div class="nav-left">
        <div class="logo-section">
          <img src="../../assets/robot.svg" alt="Logo" class="logo" />
          <span class="brand-name">智言工作台</span>
        </div>
      </div>
      <div class="nav-right">
        <!-- 用户信息区域 -->
        <div class="user-info">
          <el-dropdown @command="handleUserCommand" trigger="click">
            <div class="user-avatar-wrapper">
              <div class="user-avatar">
                <img
                  :src="userStore.userInfo?.avatar || '/src/assets/user.svg'"
                  alt="用户头像"
                  @error="handleAvatarError"
                  referrerpolicy="no-referrer"
                />
              </div>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile" :icon="User">
                  个人资料
                </el-dropdown-item>
                <el-dropdown-item command="settings" :icon="Setting">
                  系统设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout" :icon="SwitchButton">
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    <!-- 工作区主内容 -->
    <div class="workspace-main">
    <!-- 左侧边栏 -->
    <div class="sidebar">
      <!-- 应用中心按钮 -->
      <div class="create-section">
        <button @click="goToHomepage" class="create-btn-native">
          <div class="btn-content">
            <span class="icon">🏠</span>
            <span>应用中心</span>
          </div>
        </button>
      </div>

      <!-- 会话列表 -->
      <div class="session-list">
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <div class="loading-icon">⏳</div>
          <div class="loading-text">正在加载会话列表...</div>
        </div>

        <!-- 空状态 -->
        <div v-else-if="sessions.length === 0" class="empty-state">
          <div class="empty-icon">💼</div>
          <div class="empty-text">暂无会话记录</div>
        </div>

        <!-- 会话卡片 -->
        <div
          v-for="session in sessions"
          :key="session.sessionId"
          :class="['session-card', { active: selectedSession === session.sessionId }]"
          @click="selectSession(session.sessionId)"
        >
          <div class="session-icon">📋</div>
          <div class="session-info">
            <div class="session-title">{{ session.title }}</div>
            <div class="session-time">{{ formatTime(session.createTime) }}</div>
          </div>
          <button
            class="delete-btn"
            @click="deleteSession(session.sessionId, $event)"
            title="删除会话"
          >
            ×
          </button>
        </div>
      </div>
    </div>

    <!-- 右侧内容区域 -->
    <div class="content">
      <router-view />
    </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.workspace-container {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f8f9fa;
}

.workspace-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 64px;
  background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  .nav-left {
    display: flex;
    align-items: center;

    .logo-section {
      display: flex;
      align-items: center;
      gap: 12px;

      .logo {
        width: 32px;
        height: 32px;
        filter: drop-shadow(0 0 3px rgba(0, 0, 0, 0.5)) brightness(1.2) contrast(1.2);
      }

      .brand-name {
        font-size: 20px;
        font-weight: 600;
        color: white;
        letter-spacing: 1px;
      }
    }
  }

  .nav-right {
    .user-info {
      .user-avatar-wrapper {
        display: flex;
        align-items: center;
        padding: 4px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        cursor: pointer;
        transition: all 0.3s ease;

        &:hover {
          background: rgba(255, 255, 255, 0.25);
          transform: translateY(-2px);
          box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
        }

        .user-avatar {
          img {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border: 2px solid rgba(255, 255, 255, 0.5);
            object-fit: cover;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;

            &:hover {
              border-color: rgba(255, 255, 255, 0.8);
              transform: scale(1.05);
            }
          }
        }
      }
    }
  }
}

.workspace-main {
  display: flex;
  flex: 1;
  height: calc(100vh - 64px);
  background-color: #f8f9fa;

  .sidebar {
    height: 100%;
    width: 280px;
    background-color: #ffffff;
    border-right: 1px solid #e9ecef;
    display: flex;
    flex-direction: column;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);

    .create-section {
      padding: 20px 16px;

      .create-btn-native {
        width: 100%;
        height: 48px;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        border: none;
        cursor: pointer;
        font-size: 14px;

        &:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(116, 185, 255, 0.4);
        }

        &:active {
          transform: translateY(0);
        }

        .btn-content {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;

          .icon {
            font-size: 20px;
          }
        }
      }
    }

    .session-list {
      flex: 1;
      padding: 8px;
      overflow-y: auto;

      .loading-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 200px;
        color: #3b82f6;

        .loading-icon {
          font-size: 48px;
          margin-bottom: 16px;
          animation: spin 1s linear infinite;
        }

        .loading-text {
          font-size: 14px;
          color: #6b7280;
        }
      }

      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 200px;
        color: #9ca3af;

        .empty-icon {
          font-size: 48px;
          margin-bottom: 16px;
        }

        .empty-text {
          font-size: 14px;
          margin-bottom: 8px;
        }

        .empty-hint {
          font-size: 12px;
          color: #d1d5db;
        }
      }

      .session-card {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px;
        margin-bottom: 8px;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;

        &:hover {
          border-color: #667eea;
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
          transform: translateY(-2px);

          .delete-btn {
            opacity: 1;
          }
        }

        &.active {
          border-color: #667eea;
          background-color: #eff6ff;
        }

        .session-icon {
          font-size: 24px;
          flex-shrink: 0;
        }

        .session-info {
          flex: 1;
          min-width: 0;

          .session-title {
            font-size: 14px;
            font-weight: 600;
            color: #1f2937;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            margin-bottom: 4px;
          }

          .session-time {
            font-size: 11px;
            color: #9ca3af;
          }
        }

        .delete-btn {
          position: absolute;
          top: 8px;
          right: 8px;
          width: 24px;
          height: 24px;
          padding: 0;
          background: rgba(255, 255, 255, 0.9);
          border: 1px solid #e5e7eb;
          cursor: pointer;
          border-radius: 4px;
          transition: all 0.2s ease;
          font-size: 18px;
          opacity: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #6b7280;

          &:hover {
            background: #fee2e2;
            color: #dc2626;
            border-color: #dc2626;
          }

          &:active {
            transform: scale(0.95);
          }
        }
      }
    }
  }

  .content {
    flex: 1;
    background-color: #ffffff;
    border-radius: 8px;
    margin: 16px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    overflow: hidden;
  }
}

// 动画
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// 下拉菜单样式
:deep(.el-dropdown-menu) {
  border: none;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  overflow: hidden;
  
  .el-dropdown-menu__item {
    padding: 12px 16px;
    font-size: 14px;
    
    &:hover {
      background-color: #f5f7fa;
      color: #409eff;
    }
    
    .el-icon {
      margin-right: 8px;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .workspace-nav {
    .nav-left {
      .logo-section {
        .brand-name {
          display: none;
        }
      }
    }
  }

  .workspace-main {
    .sidebar {
      width: 240px;
    }

    .content {
      margin: 8px;
    }
  }
}

@media (max-width: 480px) {
  .workspace-nav {
    padding: 0 12px;
  }

  .workspace-main {
    flex-direction: column;

    .sidebar {
      width: 100%;
      height: auto;
      max-height: 300px;
    }

    .content {
      flex: 1;
      margin: 8px;
    }
  }
}
</style>

