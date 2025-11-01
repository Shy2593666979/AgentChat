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
        <div class="dialog-header">
          <h3>选择智能体创建会话</h3>
          <button @click="closeCreateDialog" class="close-btn">×</button>
        </div>
        
        <div class="dialog-body">
          <!-- 智能体搜索框 -->
          <div class="search-section">
            <input
              v-model="agentSearchKeyword"
              placeholder="搜索智能体..."
              class="search-input"
            />
          </div>

          <!-- 智能体列表 -->
          <div class="agents-section">
            <div class="section-header">
              <span class="title">可用智能体</span>
              <span class="count">({{ filteredAgents.length }})</span>
            </div>

            <!-- 加载状态 -->
            <div v-if="agentsLoading" class="loading-state">
              <div class="loading-icon">⏳</div>
              <div class="loading-text">正在加载智能体列表...</div>
            </div>

            <!-- 空状态 -->
            <div v-else-if="filteredAgents.length === 0" class="empty-state">
              <div class="empty-icon">🤖</div>
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
                <div class="agent-avatar">
                  <img :src="agent.logo_url" alt="" />
                </div>
                <div class="agent-info">
                  <div class="agent-name">{{ agent.name }}</div>
                  <div class="agent-description">{{ agent.description }}</div>
                </div>
                <div class="agent-status">
                  <div v-if="selectedAgent === ((agent as any).id || agent.agent_id)" class="selected-icon">
                    ★
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="dialog-footer">
          <div class="debug-info" style="font-size: 12px; color: #666; margin-bottom: 8px;">
            当前选中: {{ selectedAgent ? agents.find(a => (a.agent_id === selectedAgent || (a as any).id === selectedAgent))?.name || selectedAgent : '无' }}
          </div>
          <button @click="closeCreateDialog" class="btn-cancel">取消</button>
          <button 
            @click="createDialog"
            :disabled="!selectedAgent"
            class="btn-confirm"
          >
            创建会话
          </button>
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
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.3s ease;
}

.create-dialog {
  background: white;
  border-radius: 16px;
  width: 600px;
  max-width: 90vw;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideIn 0.3s ease;
  display: flex;
  flex-direction: column;

  .dialog-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 24px 24px 16px;
    border-bottom: 1px solid #f0f0f0;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);

    h3 {
      margin: 0;
      color: #1f2937;
      font-size: 18px;
      font-weight: 600;
    }

    .close-btn {
      background: none;
      border: none;
      font-size: 24px;
      cursor: pointer;
      color: #6b7280;
      padding: 0;
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      transition: all 0.2s ease;

      &:hover {
        background: #e5e7eb;
        color: #1f2937;
      }
    }
  }

  .dialog-body {
    flex: 1;
    padding: 20px 24px;
    overflow-y: auto;

    .search-section {
      margin-bottom: 20px;

      .search-input {
        width: 100%;
        padding: 12px 16px;
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        font-size: 14px;
        transition: all 0.2s ease;
        background: #f9fafb;

        &:focus {
          outline: none;
          border-color: #667eea;
          background: white;
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        &::placeholder {
          color: #9ca3af;
        }
      }
    }

    .agents-section {
      .section-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 16px;

        .title {
          font-size: 16px;
          font-weight: 600;
          color: #1f2937;
        }

        .count {
          font-size: 14px;
          color: #6b7280;
          background: #f3f4f6;
          padding: 2px 8px;
          border-radius: 12px;
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
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.2s ease;
          position: relative;
          background: #f9fafb;

          &:hover {
            background: #f3f4f6;
            border-color: #d1d5db;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          }

          &.active {
            border-color: #667eea;
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
          }

          .agent-avatar {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            overflow: hidden;
            flex-shrink: 0;
            border: 2px solid #e5e7eb;

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
              background: #667eea;
              color: white;
              border-radius: 50%;
              font-size: 12px;
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
    padding: 16px 24px;
    border-top: 1px solid #f0f0f0;
    background: #f9fafb;

    .btn-cancel {
      padding: 10px 20px;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      background: white;
      color: #6b7280;
      cursor: pointer;
      font-size: 14px;
      transition: all 0.2s ease;

      &:hover {
        background: #f3f4f6;
        border-color: #9ca3af;
      }
    }

    .btn-confirm {
      padding: 10px 20px;
      border: none;
      border-radius: 8px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      transition: all 0.2s ease;

      &:hover:not(:disabled) {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
      }

      &:disabled {
        background: #d1d5db;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
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
    transform: scale(0.9) translateY(-20px);
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
</style>
