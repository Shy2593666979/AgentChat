<script setup lang="ts">
import { onMounted, ref, watch } from "vue"
import { useRouter } from "vue-router"
import { useRoute } from "vue-router"
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, SwitchButton, Setting } from '@element-plus/icons-vue'
import { useAgentCardStore } from "../store/agent_card"
import { useUserStore } from "../store/user"
import { getAgentsAPI } from "../apis/agent"
import { logoutAPI, getUserInfoAPI } from "../apis/auth"
import { Agent } from "../type"

const agentCardStore = useAgentCardStore()
const userStore = useUserStore()
const route = useRoute()
const router = useRouter()
const itemName = ref("智言平台")
const current = ref(route.meta.current)
const cardList = ref<Agent[]>([])

// 初始化用户状态
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
  
  updateList()
})

const godefault = () => {
  agentCardStore.clear()
  router.push("/")
}
  
const updateList = async () => {
  try {
    const response = await getAgentsAPI()
    cardList.value = response.data.data
  } catch (error) {
    console.error('获取智能体列表失败:', error)
  }
}

const goCurrent = (item: string) => {
  const routes: Record<string, string> = {
    "homepage": "/homepage",
    "conversation": "/conversation",
    "agent": "/agent",
    "mcp-server": "/mcp-server",
    "knowledge": "/knowledge",
    "tool": "/tool",
    "model": "/model"
  }
  
  router.push(routes[item] || "/")
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

watch(
  route,
  (val) => {
    current.value = route.meta.current
  },
  {
    immediate: true
  }
)
</script>

<template>
  <div class="ai-body">
    <div class="ai-nav">
      <div class="left" @click="godefault">
        <div class="item-img">
          <img
            src="../../public/ai.svg"
            alt=""
            style="width: 32px; height: 32px"
          />
        </div>
        <div class="item-name" data-text="智言平台">{{ itemName }}</div>
      </div>
      <div class="right">
        <!-- 用户信息区域 -->
        <div class="user-info">
          <el-dropdown @command="handleUserCommand" trigger="click">
            <div class="user-avatar-wrapper">
              <div class="user-avatar">
                <img
                  :src="userStore.userInfo?.avatar || '/src/assets/user.svg'"
                  alt="用户头像"
                  style="width: 40px; height: 40px; border-radius: 50%"
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
    <div class="ai-main">
      <el-col :span="2">
        <div class="sidebar-content">
          <el-menu
            active-text-color="#6b9eff"
            background-color="#f4f5f8"
            class="el-menu-vertical-demo"
            :default-active="current"
            text-color="#909399"
          >
            <el-menu-item index="homepage" @click="goCurrent('homepage')">
              <template #title>
                <el-icon>
                  <img src="../assets/frontpage.svg" width="22px" height="22px" />
                </el-icon>
                <span>首页</span>
              </template>
            </el-menu-item>
            <el-menu-item index="conversation" @click="goCurrent('conversation')">
              <template #title>
                <el-icon>
                  <img src="../assets/dialog.svg" width="22px" height="22px" />
                </el-icon>
                <span>会话</span>
              </template>
            </el-menu-item>
            <el-menu-item index="agent" @click="goCurrent('agent')">
              <template #title>
                <el-icon>
                  <img src="../assets/robot.svg" width="22px" height="22px" />
                </el-icon>
                <span>智能体</span>
              </template>
            </el-menu-item>
            <el-menu-item index="mcp-server" @click="goCurrent('mcp-server')">
              <template #title>
                <el-icon>
                  <img src="../assets/mcp.svg" width="22px" height="22px" />
                </el-icon>
                <span>MCP</span>
              </template>
            </el-menu-item>
            <el-menu-item index="knowledge" @click="goCurrent('knowledge')">
              <template #title>
                <el-icon>
                  <img src="../assets/knowledge.svg" width="22px" height="22px" />
                </el-icon>
                <span>知识库</span>
              </template>
            </el-menu-item>
            <el-menu-item index="tool" @click="goCurrent('tool')">
              <template #title>
                <el-icon>
                  <img src="../assets/plugin.svg" width="22px" height="22px" />
                </el-icon>
                <span>工具</span>
              </template>
            </el-menu-item>
            <el-menu-item index="model" @click="goCurrent('model')">
              <template #title>
                <el-icon>
                  <img src="../assets/model.svg" width="22px" height="22px" />
                </el-icon>
                <span>模型</span>
              </template>
            </el-menu-item>
          </el-menu>
          
          <!-- 底部帮助链接 -->
          <div class="sidebar-footer">
            <div class="help-links">
              <a
                href="https://github.com/Shy2593666979/AgentChat"
                target="_blank"
                class="help-link"
                title="GitHub 仓库"
              >
                <img
                  src="../assets/github.png"
                  alt="GitHub"
                  class="help-icon"
                />
              </a>
              <a
                href="https://uawlh9wstr9.feishu.cn/docx/U3l4dvtC6oPrVwx61zIcrmD0nvf"
                target="_blank"
                class="help-link"
                title="帮助文档"
              >
                <img
                  src="../assets/help.png"
                  alt="帮助文档"
                  class="help-icon"
                />
              </a>
            </div>
          </div>
        </div>
      </el-col>
      <div class="content">
        <router-view></router-view>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.ai-body {
  overflow: hidden;
  
  .ai-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 64px;
    background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
    padding: 0 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    
    .left {
      display: flex;
      align-items: center;
      font-weight: 600;
      color: white;
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        opacity: 0.8;
      }
      
      .item-img {
        margin-right: 12px;
        
        img {
          /* 增加图标对比度和可见性 */
          filter: drop-shadow(0 0 3px rgba(0, 0, 0, 0.5)) brightness(1.2) contrast(1.2);
          transition: all 0.3s ease;
        }
      }
      
      .item-name {
        font-size: 22px;
        letter-spacing: 2px;
        background: linear-gradient(120deg, #f9f0ff, #fff, #e0f7fa, #fff6e5, #fff);
        background-size: 300% auto;
        background-clip: text;
        -webkit-background-clip: text;
        color: transparent;
        /* 移除阴影效果 */
        font-weight: 600;
        animation: shine-rainbow 6s ease-in-out infinite;
        /* 改为正常字体 */
        font-family: "Microsoft YaHei", "PingFang SC", "Helvetica Neue", sans-serif;
        position: relative;
        padding: 0 5px;
        
        &::before {
          content: attr(data-text);
          position: absolute;
          left: 0;
          top: 0;
          width: 100%;
          height: 100%;
          z-index: -1;
          background: none;
          /* 移除阴影效果 */
        }
      }
      
      @keyframes shine-rainbow {
        0% { background-position: 0% center; filter: hue-rotate(0deg); }
        50% { background-position: 100% center; filter: hue-rotate(10deg); }
        100% { background-position: 0% center; filter: hue-rotate(0deg); }
      }
    }

    .right {
      display: flex;
      align-items: center;
      
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
  
  .ai-main {
    display: flex;
    height: calc(100vh - 64px);
    background-color: #f5f7fa;
    
    :deep(.el-col-2) {
      display: flex;
      width: 180px;
      min-width: 180px;
    }
    
    .sidebar-content {
      display: flex;
      flex-direction: column;
      height: 100%;
      width: 100%;
      background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
      border-right: 1px solid #e2e8f0;
      padding: 24px 0;
      box-sizing: border-box;
      box-shadow: 2px 0 12px rgba(0, 0, 0, 0.08);
    }

    .sidebar-footer {
      margin-top: auto;
      padding: 0 24px 24px;
      display: flex;
      justify-content: center;
      align-items: center;

      .help-links {
        display: flex;
        gap: 16px;

        .help-link {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 48px;
          height: 48px;
          border: 2px solid rgba(59, 130, 246, 0.2);
          border-radius: 16px;
          padding: 10px;
          transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
          background: rgba(255, 255, 255, 0.8);
          backdrop-filter: blur(20px);

          &:hover {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(147, 51, 234, 0.15) 100%);
            border-color: rgba(59, 130, 246, 0.5);
            transform: translateY(-3px) scale(1.1);
            box-shadow: 0 12px 24px rgba(59, 130, 246, 0.25);
          }

          .help-icon {
            width: 26px;
            height: 26px;
            transition: all 0.4s ease;
            filter: saturate(0.8);
          }
          
          &:hover .help-icon {
            filter: saturate(1.3) hue-rotate(10deg);
            transform: scale(1.1);
          }
        }
      }
    }

    .content {
      flex: 1;
      overflow-y: auto;
      background-color: #ffffff;
      border-radius: 20px 0 0 0;
      margin-left: 4px;
      box-shadow: -4px 0 16px rgba(0, 0, 0, 0.05);
    }
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

// 菜单样式优化
:deep(.el-menu-vertical-demo) {
  border-right: none;
  background: transparent;
  font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
  
  .el-menu-item {
    border-radius: 16px;
    margin: 8px 16px;
    padding: 0 20px;
    height: 56px;
    line-height: 56px;
    font-size: 16px;
    font-weight: 600;
    letter-spacing: 0.5px;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    color: #475569;
    
    &:hover {
      background: rgba(99, 102, 241, 0.05);
      color: #6366f1;
      transform: translateX(2px);
      
      .el-icon img {
        transform: scale(1.05);
      }
    }
    
    &.is-active {
      background: #ffffff;
      color: #6366f1;
      box-shadow: 0 2px 8px rgba(99, 102, 241, 0.1);
      border: 1px solid rgba(99, 102, 241, 0.1);
      
      .el-icon {
        img {
          filter: none;
          opacity: 1 !important;
        }
      }
      
      span {
        font-weight: 600;
        color: #6366f1 !important;
      }
    }
    
    .el-icon {
      margin-right: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      
      img {
        width: 28px;
        height: 28px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      }
    }
    
    span {
      position: relative;
      z-index: 1;
      transition: all 0.4s ease;
      font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
    }
  }
}
</style>
