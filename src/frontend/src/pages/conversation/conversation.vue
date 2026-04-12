<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { useRouter } from "vue-router"
import { ElMessage, ElMessageBox } from "element-plus"
import { getAgentsAPI } from "../../apis/agent"
import { createDialogAPI, getDialogListAPI, deleteDialogAPI } from "../../apis/history"
import type { AgentResponse, ApiResponse } from "../../apis/agent"
import type { HistoryListType, DialogCreateType } from "../../type"
import histortCard from '../../components/historyCard/histortCard.vue'
import { useHistoryChatStore } from "../../store/history_chat_msg"

const router = useRouter()
const historyChatStore = useHistoryChatStore()
const searchKeyword = ref('')
const selectedDialog = ref('')
const showCreateDialog = ref(false)
const selectedAgent = ref('')
const agentSearchKeyword = ref('')

// 真实数据
const dialogs = ref<HistoryListType[]>([])
const agents = ref<AgentResponse[]>([])
const loading = ref(false)
const agentsLoading = ref(false)

// 过滤后的会话数据
const filteredDialogs = computed(() => {
  if (!searchKeyword.value) return dialogs.value
  return dialogs.value.filter(dialog => 
    dialog.name.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
    dialog.agent.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
})

// 过滤后的智能体数据
const filteredAgents = computed(() => {
  if (!agentSearchKeyword.value) return agents.value
  return agents.value.filter(agent => 
    agent.name.toLowerCase().includes(agentSearchKeyword.value.toLowerCase()) ||
    agent.description.toLowerCase().includes(agentSearchKeyword.value.toLowerCase())
  )
})

// 格式化时间
const formatTime = (timeStr: string) => {
  try {
    if (!timeStr) return '未知时间'
    
    // 处理不同的时间格式
    let date: Date
    if (typeof timeStr === 'string') {
      // 如果是ISO格式字符串
      if (timeStr.includes('T') || timeStr.includes('Z')) {
        date = new Date(timeStr)
      } else {
        // 尝试解析其他格式
        date = new Date(timeStr)
      }
    } else {
      date = new Date(timeStr)
    }
    
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      console.warn('无效的时间格式:', timeStr)
      return '未知时间'
    }
    
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
    
    if (diffInHours < 1) return '刚刚'
    if (diffInHours < 24) return `${Math.floor(diffInHours)}小时前`
    if (diffInHours < 24 * 7) return `${Math.floor(diffInHours / 24)}天前`
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  } catch (error) {
    console.error('时间格式化错误:', error, '时间字符串:', timeStr)
    return '未知时间'
  }
}

// 获取智能体列表
const fetchAgents = async () => {
  try {
    agentsLoading.value = true
    const response = await getAgentsAPI()
    if (response.data.status_code === 200) {
      agents.value = response.data.data
      console.log('智能体列表获取成功:', agents.value)
      console.log('智能体ID详情:', agents.value.map(a => ({
        name: a.name,
        agent_id: a.agent_id,
        id: (a as any).id,
        agent_id_type: typeof a.agent_id,
        id_type: typeof (a as any).id
      })))
    } else {
      ElMessage.error(`获取智能体列表失败: ${response.data.status_message}`)
    }
  } catch (error) {
    console.error('获取智能体列表出错:', error)
    ElMessage.error('获取智能体列表失败，请检查网络连接')
  } finally {
    agentsLoading.value = false
  }
}

// 获取对话列表
const fetchDialogs = async () => {
  try {
    loading.value = true
    const response = await getDialogListAPI()
    if (response.data.status_code === 200) {
      // 处理返回的数据，确保字段名称正确
      console.log('原始对话数据:', response.data.data)
      dialogs.value = response.data.data.map((dialog: any) => {
        const processedDialog = {
          dialogId: dialog.dialog_id,
          name: dialog.name,
          agent: dialog.name, // 使用智能体名称作为显示
          createTime: dialog.create_time || dialog.update_time || new Date().toISOString(),
          logo: dialog.logo_url || 'https://via.placeholder.com/40x40/3b82f6/ffffff?text=AI'
        }
        console.log('处理后的对话数据:', processedDialog)
        return processedDialog
      })
      console.log('对话列表获取成功:', dialogs.value)
      
      // 如果会话列表不为空且当前路由是默认页面，立即自动打开第一个会话
      if (dialogs.value.length > 0 && router.currentRoute.value.name === 'defaultPage') {
        const firstDialog = dialogs.value[0]
        console.log('立即自动打开第一个会话:', firstDialog.dialogId, firstDialog.name)
        
        // 设置选中的会话
        selectedDialog.value = firstDialog.dialogId
        
        // 设置聊天store的状态
        historyChatStore.dialogId = firstDialog.dialogId
        historyChatStore.name = firstDialog.name
        historyChatStore.logo = firstDialog.logo
        
        // 立即跳转到聊天页面
        router.push({
          path: '/conversation/chatPage',
          query: {
            dialog_id: firstDialog.dialogId
          }
        })
      }
    } else {
      ElMessage.error(`获取对话列表失败: ${response.data.status_message}`)
    }
  } catch (error) {
    console.error('获取对话列表出错:', error)
    ElMessage.error('获取对话列表失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  console.log('会话页面已加载')
  // 如果当前是会话主页面，先获取对话列表检查是否需要跳转
  if (router.currentRoute.value.path === '/conversation') {
    await fetchDialogs()
    // 如果没有自动跳转（说明没有会话），再获取智能体列表
    if (router.currentRoute.value.name === 'defaultPage') {
      await fetchAgents()
    }
  } else {
    // 如果是其他子页面，正常加载
    await Promise.all([fetchAgents(), fetchDialogs()])
  }
  // ElMessage.success('页面加载成功')
})

// 创建新会话
const createDialog = async () => {
  if (!selectedAgent.value) {
    ElMessage.warning('请选择一个智能体')
    return
  }
  
  // 支持多种ID字段查找
  const agent = agents.value.find(a => {
    const agentIdMatch = a.agent_id === selectedAgent.value || String(a.agent_id) === String(selectedAgent.value)
    const idMatch = (a as any).id === selectedAgent.value || String((a as any).id) === String(selectedAgent.value)
    return agentIdMatch || idMatch
  })
  
  if (agent) {
    try {
      const dialogData: DialogCreateType = {
        name: `与${agent.name}的对话`,
        agent_id: (agent as any).id || agent.agent_id, // 优先使用 id 字段
        agent_type: "Agent" // 默认为普通Agent类型
      }
      
      console.log('创建会话数据:', dialogData)
      console.log('发送到后端的数据:', {
        name: dialogData.name,
        agent_id: dialogData.agent_id,
        agent_type: dialogData.agent_type
      })
      const response = await createDialogAPI(dialogData)
      if (response.data.status_code === 200) {
        ElMessage.success('会话创建成功')
        
        // 获取新创建的会话ID
        const dialogId = response.data.data.dialog_id
        console.log('获取到的 dialogId:', dialogId)
        console.log('完整的 response.data.data:', response.data.data)
        
        // 重新获取对话列表
        await fetchDialogs()
        showCreateDialog.value = false
        selectedAgent.value = ''
        agentSearchKeyword.value = ''
        
        // 跳转到新创建的会话页面
        if (dialogId) {
          console.log('准备跳转到会话页面，dialogId:', dialogId)
          
          // 更新选中的会话状态
          selectedDialog.value = dialogId
          
          // 设置聊天store的状态
          historyChatStore.dialogId = dialogId
          historyChatStore.name = dialogData.name
          historyChatStore.logo = agent.logo_url || 'https://via.placeholder.com/40x40/3b82f6/ffffff?text=AI'
          
          router.push({
            path: '/conversation/chatPage',
            query: {
              dialog_id: dialogId
            }
          })
        } else {
          console.error('dialogId 为空，无法跳转')
        }
      } else {
        ElMessage.error(`创建会话失败: ${response.data.status_message}`)
      }
    } catch (error) {
      console.error('创建会话出错:', error)
      ElMessage.error('创建会话失败，请检查网络连接')
    }
  } else {
    ElMessage.error('未找到选中的智能体')
  }
}

// 删除会话
const deleteDialog = async (dialogId: string) => {
  console.log('删除会话被调用，dialogId:', dialogId)
  try {
    const response = await deleteDialogAPI(dialogId)
    if (response.data.status_code === 200) {
      ElMessage({
        message: '会话删除成功',
        type: 'success',
        duration: 3000,
        showClose: false
      })
      // 重新获取对话列表
      await fetchDialogs()
      if (selectedDialog.value === dialogId) {
        selectedDialog.value = ''
      }
    } else {
      ElMessage.error(`删除会话失败: ${response.data.status_message}`)
    }
  } catch (error) {
    console.error('删除会话出错:', error)
    ElMessage.error('删除会话失败，请检查网络连接')
  }
}

// 选择会话
const selectDialog = (dialogId: string) => {
  const dialog = dialogs.value.find(d => d.dialogId === dialogId)
  if (!dialog) {
    console.error('未找到会话:', dialogId)
    return
  }
  
  console.log('选择会话:', dialogId, dialog.name)
  selectedDialog.value = dialogId
  
  // 设置聊天store的状态
  historyChatStore.dialogId = dialogId
  historyChatStore.name = dialog.name
  historyChatStore.logo = dialog.logo
  
  // 跳转到聊天页面
  router.push({
    path: '/conversation/chatPage',
    query: {
      dialog_id: dialogId
    }
  })
}

// 打开创建对话框
const openCreateDialog = async () => {
  showCreateDialog.value = true
  selectedAgent.value = ''
  agentSearchKeyword.value = ''
  
  // 如果智能体列表为空，重新获取
  if (agents.value.length === 0) {
    await fetchAgents()
  }
  
  // ElMessage.info('正在打开创建会话对话框...')
}

// 选择智能体
const selectAgent = (agentId: string) => {
  console.log('选择智能体:', agentId)
  console.log('当前智能体列表:', agents.value.map(a => ({ 
    agent_id: a.agent_id, 
    id: (a as any).id, 
    name: a.name 
  })))
  
  // 支持多种ID字段
  const agent = agents.value.find(a => {
    const agentIdMatch = a.agent_id === agentId || String(a.agent_id) === String(agentId)
    const idMatch = (a as any).id === agentId || String((a as any).id) === String(agentId)
    return agentIdMatch || idMatch
  })
  
  if (agent) {
    // 优先使用 id 字段作为选中值
    selectedAgent.value = (agent as any).id || agent.agent_id
    console.log('选中智能体:', agent.name, 'ID:', selectedAgent.value)
  } else {
    console.error('未找到智能体:', agentId)
  }
}

// 关闭创建对话框
const closeCreateDialog = () => {
  showCreateDialog.value = false
  selectedAgent.value = ''
  agentSearchKeyword.value = ''
}
</script>

<template>
  <div class="conversation-main">
    <!-- 左侧边栏 -->
    <div class="sidebar">
      <!-- 新建会话按钮 -->
      <div class="create-section">
        <button 
          @click="openCreateDialog"
          class="create-btn-native"
        >
          <div class="btn-content">
            <span class="icon">+</span>
            <span>新建会话</span>
          </div>
        </button>
      </div>

      

      <!-- 会话列表标题 -->
      <div class="list-header">
        <span class="title">会话列表</span>
        <span class="count">({{ filteredDialogs.length }})</span>
      </div>

      <!-- 会话列表 -->
      <div class="dialog-list">
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <div class="loading-icon">⏳</div>
          <div class="loading-text">正在加载会话列表...</div>
        </div>
        <!-- 空状态 -->
        <div v-else-if="filteredDialogs.length === 0" class="empty-state">
          <div class="empty-icon">💬</div>
          <div class="empty-text">
            {{ searchKeyword ? '没有找到相关会话' : '暂无会话记录' }}
          </div>
          <div v-if="!searchKeyword" class="empty-hint">
            点击上方按钮开始新的对话
          </div>
        </div>
        <!-- 用 histortCard 渲染会话卡片 -->
        <histortCard
          v-for="dialog in filteredDialogs" 
          :key="dialog.dialogId"
          :item="dialog"
          :class="{ active: selectedDialog === dialog.dialogId }"
          @select="selectDialog(dialog.dialogId)"
          @delete="deleteDialog(dialog.dialogId)"
        />
      </div>
    </div>

    <!-- 右侧内容区域，改为路由驱动 -->
    <div class="content">
      <router-view />
    </div>

    <!-- 创建会话对话框 -->
    <div v-if="showCreateDialog" class="create-dialog-overlay" @click="closeCreateDialog">
      <div class="create-dialog" @click.stop>
        <div class="dialog-body">
          <!-- 智能体搜索框 -->
          <div class="search-section">
            <div class="search-wrapper">
              <svg class="search-icon" width="18" height="18" viewBox="0 0 18 18" fill="none">
                <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2"/>
                <path d="M12.5 12.5L16 16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <input
                v-model="agentSearchKeyword"
                placeholder="搜索智能体名称或描述..."
                class="search-input"
              />
              <div v-if="agentSearchKeyword" class="clear-btn" @click="agentSearchKeyword = ''">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="7" fill="currentColor" opacity="0.1"/>
                  <path d="M10 6L6 10M6 6L10 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
              </div>
            </div>
          </div>

          <!-- 智能体列表 -->
          <div class="agents-section">
            <div class="section-header">
              <div class="header-left">
                <svg class="section-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <rect x="3" y="3" width="14" height="14" rx="3" stroke="currentColor" stroke-width="2"/>
                  <circle cx="7" cy="8" r="1.5" fill="currentColor"/>
                  <circle cx="13" cy="8" r="1.5" fill="currentColor"/>
                  <path d="M7 12C7 12 8 13.5 10 13.5C12 13.5 13 12 13 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
                <span class="title">可用智能体</span>
                <span class="count">{{ filteredAgents.length }}</span>
              </div>
            </div>

            <!-- 加载状态 -->
            <div v-if="agentsLoading" class="loading-state">
              <div class="loading-spinner">
                <svg class="spinner" width="40" height="40" viewBox="0 0 40 40">
                  <circle cx="20" cy="20" r="16" stroke="currentColor" stroke-width="4" fill="none" opacity="0.2"/>
                  <circle cx="20" cy="20" r="16" stroke="currentColor" stroke-width="4" fill="none" stroke-dasharray="80" stroke-dashoffset="60"/>
                </svg>
              </div>
              <div class="loading-text">正在加载智能体列表...</div>
            </div>

            <!-- 空状态 -->
            <div v-else-if="filteredAgents.length === 0" class="empty-state">
              <div class="empty-illustration">
                <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
                  <circle cx="40" cy="40" r="35" fill="#f3f4f6"/>
                  <rect x="25" y="25" width="30" height="30" rx="6" stroke="#9ca3af" stroke-width="2"/>
                  <circle cx="33" cy="35" r="2" fill="#9ca3af"/>
                  <circle cx="47" cy="35" r="2" fill="#9ca3af"/>
                  <path d="M32 45C32 45 35 48 40 48C45 48 48 45 48 45" stroke="#9ca3af" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="empty-text">
                {{ agentSearchKeyword ? '没有找到相关智能体' : '暂无可用智能体' }}
              </div>
              <div v-if="!agentSearchKeyword" class="empty-hint">
                请联系管理员添加智能体
              </div>
            </div>

            <div v-else class="agents-grid">
              <div
                v-for="agent in filteredAgents"
                :key="(agent as any).id || agent.agent_id"
                :class="['agent-card', selectedAgent === ((agent as any).id || agent.agent_id) ? 'active' : '']"
                @click="selectAgent((agent as any).id || agent.agent_id)"
              >
                <div class="card-inner">
                  <div class="agent-avatar">
                    <img :src="agent.logo_url" alt="" />
                    <div v-if="selectedAgent === ((agent as any).id || agent.agent_id)" class="avatar-badge">
                      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <circle cx="10" cy="10" r="10" fill="white"/>
                        <path d="M6 10L9 13L14 8" stroke="#667eea" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </div>
                  </div>
                  <div class="agent-info">
                    <div class="agent-name">{{ agent.name }}</div>
                    <div class="agent-description">{{ agent.description }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="dialog-footer">
          <div class="footer-info">
            <svg class="info-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
              <path d="M8 7V11M8 5V5.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            <span v-if="selectedAgent">
              已选择: {{ agents.find(a => (a.agent_id === selectedAgent || (a as any).id === selectedAgent))?.name || '未知' }}
            </span>
            <span v-else>请选择一个智能体</span>
          </div>
          <div class="footer-actions">
            <button @click="closeCreateDialog" class="btn-cancel">
              <span>取消</span>
            </button>
            <button 
              @click="createDialog"
              :disabled="!selectedAgent"
              class="btn-confirm"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 3V13M3 8H13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <span>创建会话</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.conversation-main {
  display: flex;
  height: calc(100vh - 60px);
  background-color: #ffffff;

  .sidebar {
    height: 100%;
    width: 280px;
    background-color: #ffffff;
    border-right: 1px solid #e9ecef;
    display: flex;
    flex-direction: column;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);

    .create-section {
      padding: 20px 16px 16px;
      border-bottom: 1px solid #f0f0f0;

      .create-btn-native {
        width: 100%;
        height: 48px;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
        background: linear-gradient(135deg, #74c0fc 0%, #4b9fe2 100%);
        color: white;
        border: none;
        cursor: pointer;
        font-size: 14px;

        &:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(116, 192, 252, 0.4);
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
            font-size: 18px;
            font-weight: bold;
          }
        }
      }
    }

    .search-section {
      padding: 16px;
      border-bottom: 1px solid #f0f0f0;

      .search-input-wrapper {
        position: relative;
        display: flex;
        align-items: center;

        .search-icon {
          position: absolute;
          left: 12px;
          color: #9ca3af;
          font-size: 14px;
          z-index: 1;
        }

        .search-input {
          width: 100%;
          padding: 8px 12px 8px 36px;
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          font-size: 14px;
          background: #f9fafb;
          transition: all 0.2s ease;

          &:focus {
            outline: none;
            border-color: #667eea;
            background: white;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
          }

          &::placeholder {
            color: #9ca3af;
          }
        }
      }
    }

    .list-header {
      padding: 16px 16px 8px;
      display: flex;
      align-items: center;
      gap: 4px;

      .title {
        font-size: 14px;
        font-weight: 600;
        color: #1f2937;
      }

      .count {
        font-size: 12px;
        color: #6b7280;
      }
    }

    .dialog-list {
      flex: 1;
      padding: 0 8px;
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

      .dialog-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        min-height: 80px;
        position: relative;

        &:hover {
          border-color: #3b82f6;
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
          transform: translateY(-2px);
        }

        &.active {
          border-color: #3b82f6;
          background-color: #eff6ff;
        }

        .avatar {
          position: absolute;
          top: 16px;
          left: 16px;
          width: 40px;
          height: 40px;
          border-radius: 8px;
          overflow: hidden;

          img {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }
        }

        .title {
          position: absolute;
          top: 16px;
          left: 68px;
          right: 60px;
          font-size: 14px;
          font-weight: 600;
          color: #1f2937;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .delete-btn {
          position: absolute;
          top: 16px;
          right: 16px;
          width: 32px;
          height: 32px;
          padding: 4px;
          background: rgba(255, 255, 255, 0.9);
          border: 1px solid #e5e7eb;
          cursor: pointer;
          border-radius: 4px;
          transition: all 0.2s ease;
          font-size: 14px;
          opacity: 0;
          z-index: 9999;
          display: flex;
          align-items: center;
          justify-content: center;
          user-select: none;
          pointer-events: auto;
          outline: none;

          &:hover {
            background: #fee2e2;
            color: #dc2626;
            border-color: #dc2626;
            opacity: 1;
          }

          &:active {
            transform: scale(0.95);
          }
        }

        &:hover .delete-btn {
          opacity: 1 !important;
          background: #fee2e2 !important;
          color: #dc2626 !important;
          border-color: #dc2626 !important;
        }

        .time {
          position: absolute;
          bottom: 8px;
          right: 16px;
          font-size: 11px;
          color: #9ca3af;
        }
      }
    }
  }

  .content {
    flex: 1;
    background-color: #ffffff;
    border-radius: 0;
    margin: 0;
    box-shadow: none;
    border-left: 1px solid #e9ecef;
    overflow: hidden;

    .welcome-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      color: #6b7280;
      height: 100%;

      .welcome-icon {
        margin-bottom: 24px;

        .icon {
          font-size: 48px;
          color: #3b82f6;
        }
      }

      h2 {
        font-size: 1.5rem;
        margin: 0 0 12px 0;
        color: #1f2937;
      }

      p {
        font-size: 1rem;
        margin: 0;
      }
    }

    .chat-content {
      flex: 1;
      display: flex;
      flex-direction: column;

      .chat-header {
        padding: 20px;
        border-bottom: 1px solid #e5e7eb;
        background: #f9fafb;

        h3 {
          margin: 0;
          color: #1f2937;
        }
      }

      .chat-messages {
        flex: 1;
        padding: 20px;

        .message {
          padding: 12px 16px;
          border-radius: 8px;
          margin-bottom: 12px;

          &.system {
            background: #f3f4f6;
            color: #6b7280;
          }
        }
      }
    }
  }
}

.dialog-content {
  .search-section {
    margin-bottom: 20px;
  }

  .agents-section {
    .section-header {
      display: flex;
      align-items: center;
      gap: 4px;
      margin-bottom: 16px;

      .title {
        font-size: 16px;
        font-weight: 600;
        color: #1f2937;
      }

      .count {
        font-size: 14px;
        color: #6b7280;
      }
    }

    .empty-state {
      text-align: center;
      padding: 40px 20px;
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

    .agents-grid {
      display: grid;
      gap: 12px;
      max-height: 400px;
      overflow-y: auto;

      .agent-card {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px;
        border: 2px solid transparent;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        position: relative;

        &:hover {
          background: #f9fafb;
          border-color: #d1d5db;
        }

        &.active {
          border-color: #3b82f6;
          background: #eff6ff;
        }

        .agent-avatar {
          width: 48px;
          height: 48px;
          border-radius: 8px;
          overflow: hidden;
          flex-shrink: 0;

          img {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }
        }

        .agent-info {
          flex: 1;

          .agent-name {
            font-size: 16px;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 4px;
          }

          .agent-description {
            font-size: 14px;
            color: #6b7280;
            line-height: 1.4;
          }
        }

        .agent-status {
          flex-shrink: 0;

          .selected-icon {
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #eff6ff;
            border-radius: 50%;
          }
        }
      }
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

// 响应式设计
@media (max-width: 768px) {
  .conversation-main {
    .sidebar {
      width: 240px;
    }
    
    .content {
      margin: 0;
    }
  }
}

@media (max-width: 480px) {
  .conversation-main {
    flex-direction: column;
    
    .sidebar {
      width: 100%;
      height: auto;
      max-height: 300px;
    }
    
    .content {
      flex: 1;
      margin: 0;
    }
  }
}

// 调试样式 - 确保对话框显示
:deep(.el-dialog) {
  z-index: 9999 !important;
  position: fixed !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) !important;
  background: white !important;
  border-radius: 8px !important;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2) !important;
}

:deep(.el-overlay) {
  z-index: 9998 !important;
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  background: rgba(0, 0, 0, 0.5) !important;
}

// 原生对话框样式
.create-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.create-dialog {
  background: white;
  border-radius: 24px;
  width: 85vw;
  max-width: 1200px;
  height: 75vh;
  max-height: 675px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(59, 130, 246, 0.3), 0 0 0 1px rgba(59, 130, 246, 0.1);
  animation: slideIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  display: flex;
  flex-direction: column;

  .dialog-body {
    flex: 1;
    padding: 40px;
    overflow-y: auto;
    background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
    border-radius: 24px 24px 0 0;

    &::-webkit-scrollbar {
      width: 10px;
    }

    &::-webkit-scrollbar-track {
      background: rgba(59, 130, 246, 0.05);
      border-radius: 5px;
    }

    &::-webkit-scrollbar-thumb {
      background: linear-gradient(180deg, #60a5fa 0%, #3b82f6 100%);
      border-radius: 5px;

      &:hover {
        background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
      }
    }

    .search-section {
      margin-bottom: 28px;

      .search-wrapper {
        position: relative;
        display: flex;
        align-items: center;

        .search-icon {
          position: absolute;
          left: 18px;
          color: #3b82f6;
          pointer-events: none;
          z-index: 1;
        }

        .search-input {
          width: 100%;
          padding: 16px 56px 16px 52px;
          border: 2px solid #93c5fd;
          border-radius: 14px;
          font-size: 15px;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
          background: white;
          color: #1e40af;
          font-weight: 500;

          &:focus {
            outline: none;
            border-color: #3b82f6;
            background: white;
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.15);
          }

          &::placeholder {
            color: #93c5fd;
            font-weight: 400;
          }
        }

        .clear-btn {
          position: absolute;
          right: 14px;
          color: #60a5fa;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s ease;
          padding: 6px;
          border-radius: 8px;

          &:hover {
            color: #3b82f6;
            background: #dbeafe;
          }
        }
      }
    }

    .agents-section {
      .section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;

        .header-left {
          display: flex;
          align-items: center;
          gap: 12px;

          .section-icon {
            color: #3b82f6;
          }

          .title {
            font-size: 18px;
            font-weight: 700;
            color: #1e40af;
            letter-spacing: -0.01em;
          }

          .count {
            font-size: 14px;
            color: #3b82f6;
            background: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: 600;
            border: 2px solid #93c5fd;
          }
        }
      }

      .loading-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 80px 20px;

        .loading-spinner {
          margin-bottom: 24px;

          .spinner {
            color: #3b82f6;
            animation: spin 1s linear infinite;
          }
        }

        .loading-text {
          font-size: 15px;
          color: #1e40af;
          font-weight: 600;
        }
      }

      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 80px 20px;

        .empty-illustration {
          margin-bottom: 24px;
          animation: float 3s ease-in-out infinite;
        }

        .empty-text {
          font-size: 16px;
          color: #1e40af;
          margin-bottom: 10px;
          font-weight: 600;
        }

        .empty-hint {
          font-size: 14px;
          color: #60a5fa;
        }
      }

      .agents-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 20px;
        max-height: 450px;
        overflow-y: auto;
        padding: 6px;

        &::-webkit-scrollbar {
          width: 8px;
        }

        &::-webkit-scrollbar-track {
          background: rgba(59, 130, 246, 0.05);
          border-radius: 4px;
        }

        &::-webkit-scrollbar-thumb {
          background: linear-gradient(180deg, #60a5fa 0%, #3b82f6 100%);
          border-radius: 4px;

          &:hover {
            background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
          }
        }

        .agent-card {
          border: 3px solid #93c5fd;
          border-radius: 20px;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
          background: white;
          overflow: hidden;
          aspect-ratio: 1;
          display: flex;
          flex-direction: column;

          &::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(37, 99, 235, 0.05) 100%);
            opacity: 0;
            transition: opacity 0.3s ease;
          }

          &:hover {
            border-color: #60a5fa;
            transform: translateY(-6px) scale(1.02);
            box-shadow: 0 16px 32px rgba(59, 130, 246, 0.25);

            &::before {
              opacity: 1;
            }
          }

          &.active {
            border-color: #3b82f6;
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
            box-shadow: 0 16px 40px rgba(59, 130, 246, 0.4);
            transform: translateY(-6px) scale(1.02);

            &::before {
              opacity: 1;
            }

            .agent-avatar {
              border-color: #3b82f6;
              box-shadow: 0 8px 20px rgba(59, 130, 246, 0.5);
            }

            .agent-name {
              color: #1e40af;
            }
          }

          .card-inner {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 24px 18px;
            height: 100%;
            text-align: center;
            position: relative;
            z-index: 1;
          }

          .agent-avatar {
            width: 80px;
            height: 80px;
            border-radius: 20px;
            overflow: hidden;
            flex-shrink: 0;
            border: 3px solid #93c5fd;
            transition: all 0.3s ease;
            position: relative;
            margin-bottom: 14px;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);

            img {
              width: 100%;
              height: 100%;
              object-fit: cover;
            }

            .avatar-badge {
              position: absolute;
              bottom: -8px;
              right: -8px;
              width: 32px;
              height: 32px;
              background: white;
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
              box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
              border: 3px solid #3b82f6;
              animation: scaleIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            }
          }

          .agent-info {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            width: 100%;

            .agent-name {
              font-size: 16px;
              font-weight: 700;
              color: #1e3a8a;
              margin-bottom: 8px;
              letter-spacing: -0.01em;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
              line-height: 1.3;
              text-align: center;
            }

            .agent-description {
              font-size: 13px;
              color: #3b82f6;
              line-height: 1.5;
              display: -webkit-box;
              -webkit-line-clamp: 2;
              -webkit-box-orient: vertical;
              overflow: hidden;
              font-weight: 500;
              text-align: left;
            }
          }
        }
      }
    }
  }

  .dialog-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    padding: 24px 40px;
    border-top: 2px solid #93c5fd;
    background: linear-gradient(180deg, white 0%, #f0f9ff 100%);

    .footer-info {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 14px;
      color: #1e40af;
      flex: 1;

      .info-icon {
        color: #3b82f6;
        flex-shrink: 0;
      }

      span {
        font-weight: 600;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }

    .footer-actions {
      display: flex;
      gap: 14px;
    }

    .btn-cancel {
      padding: 13px 28px;
      border: 2px solid #93c5fd;
      border-radius: 12px;
      background: white;
      color: #3b82f6;
      cursor: pointer;
      font-size: 15px;
      font-weight: 600;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      display: flex;
      align-items: center;
      gap: 8px;

      &:hover {
        background: #eff6ff;
        border-color: #60a5fa;
        color: #2563eb;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
      }

      &:active {
        transform: translateY(0);
      }
    }

    .btn-confirm {
      padding: 13px 28px;
      border: none;
      border-radius: 12px;
      background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
      color: white;
      cursor: pointer;
      font-size: 15px;
      font-weight: 600;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      display: flex;
      align-items: center;
      gap: 10px;
      box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);

      svg {
        transition: transform 0.2s ease;
      }

      &:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.5);
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);

        svg {
          transform: rotate(90deg);
        }
      }

      &:active:not(:disabled) {
        transform: translateY(0);
      }

      &:disabled {
        background: linear-gradient(135deg, #cbd5e1 0%, #94a3b8 100%);
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
        opacity: 0.6;
      }
    }
  }
}

// 动画
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}
</style>
