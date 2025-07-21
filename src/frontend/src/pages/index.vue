<script setup lang="ts">
import { onMounted, ref, watch } from "vue"
import { useRouter } from "vue-router"
import { useRoute } from "vue-router"
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, SwitchButton, Setting } from '@element-plus/icons-vue'
import { useAgentCardStore } from "../store/agent_card"
import { useUserStore } from "../store/user"
import { getAgentsAPI } from "../apis/agent"
import { logoutAPI } from "../apis/auth"
import { Agent } from "../type"

const agentCardStore = useAgentCardStore()
const userStore = useUserStore()
const route = useRoute()
const router = useRouter()
const itemName = ref("智言平台")
const current = ref(route.meta.current)
const cardList = ref<Agent[]>([])

// 初始化用户状态
onMounted(() => {
  userStore.initUserState()
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
    "conversation": "/",
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
        <div class="item-name">{{ itemName }}</div>
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
                  style="width: 36px; height: 36px; border-radius: 50%"
                  @error="handleAvatarError"
                />
              </div>
              <div class="user-details" v-if="userStore.isLoggedIn">
                <div class="user-name">{{ userStore.userInfo?.nickname || userStore.userInfo?.username || '用户' }}</div>
                <div class="user-status">在线</div>
              </div>
              <div class="user-details" v-else>
                <div class="user-name">访客模式</div>
                <div class="user-status">未登录</div>
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
                  src="../assets/knowledge.svg"
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
          filter: brightness(0) invert(1);
        }
      }
      
      .item-name {
        font-size: 20px;
        letter-spacing: 1px;
      }
    }

    .right {
      display: flex;
      align-items: center;
      
      .user-info {
        .user-avatar-wrapper {
          display: flex;
          align-items: center;
          padding: 8px 12px;
          border-radius: 25px;
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(10px);
          cursor: pointer;
          transition: all 0.3s ease;
          
          &:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-1px);
          }
          
          .user-avatar {
            margin-right: 12px;
            
            img {
              border: 2px solid rgba(255, 255, 255, 0.3);
              object-fit: cover;
            }
          }
          
          .user-details {
            .user-name {
              color: white;
              font-size: 14px;
              font-weight: 500;
              line-height: 1.2;
              margin-bottom: 2px;
            }
            
            .user-status {
              color: rgba(255, 255, 255, 0.8);
              font-size: 12px;
              line-height: 1;
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
      background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%);
      color: #3b82f6;
      transform: translateX(6px) scale(1.02);
      box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15);
      
      .el-icon img {
        filter: saturate(1.5) hue-rotate(10deg);
        transform: scale(1.1);
      }
      
      span {
        text-shadow: 0 1px 3px rgba(59, 130, 246, 0.2);
      }
    }
    
    &.is-active {
      background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
      color: white;
      transform: translateX(8px) scale(1.03);
      box-shadow: 0 12px 32px rgba(59, 130, 246, 0.4);
      
      .el-icon {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        padding: 2px;
        
        img {
          filter: brightness(0) invert(1) contrast(2) drop-shadow(0 0 6px rgba(255, 255, 255, 0.8));
          transform: scale(1.15);
          opacity: 1 !important;
        }
      }
      
      span {
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        color: white !important;
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
