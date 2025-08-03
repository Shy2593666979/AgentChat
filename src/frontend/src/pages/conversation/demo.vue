<script setup lang="ts">
import { ref, computed } from "vue"
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from "element-plus"
import { Plus, Search, Delete, Star, Close } from '@element-plus/icons-vue'

const router = useRouter()

// 模拟数据
const mockAgents = ref([
  {
    agent_id: '1',
    name: '智能助手',
    description: '通用智能助手，可以回答各种问题',
    logo_url: 'https://via.placeholder.com/40x40/3b82f6/ffffff?text=AI'
  },
  {
    agent_id: '2',
    name: '代码专家',
    description: '专业的编程助手，支持多种编程语言',
    logo_url: 'https://via.placeholder.com/40x40/10b981/ffffff?text=Code'
  },
  {
    agent_id: '3',
    name: '翻译助手',
    description: '多语言翻译服务，支持多种语言互译',
    logo_url: 'https://via.placeholder.com/40x40/f59e0b/ffffff?text=翻译'
  }
])

const mockDialogs = ref([
  {
    dialogId: '1',
    name: '关于Vue.js的讨论',
    agent: '代码专家',
    createTime: '2024-01-15T10:30:00Z',
    logo: 'https://via.placeholder.com/40x40/10b981/ffffff?text=Code'
  },
  {
    dialogId: '2',
    name: '英语翻译帮助',
    agent: '翻译助手',
    createTime: '2024-01-14T15:20:00Z',
    logo: 'https://via.placeholder.com/40x40/f59e0b/ffffff?text=翻译'
  },
  {
    dialogId: '3',
    name: '日常问题咨询',
    agent: '智能助手',
    createTime: '2024-01-13T09:15:00Z',
    logo: 'https://via.placeholder.com/40x40/3b82f6/ffffff?text=AI'
  }
])

const searchKeyword = ref('')
const selectedDialog = ref('')
const showCreateDialog = ref(false)
const selectedAgent = ref('')

// 过滤后的数据
const filteredDialogs = computed(() => {
  if (!searchKeyword.value) return mockDialogs.value
  return mockDialogs.value.filter(dialog => 
    dialog.name.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
    dialog.agent.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
})

const filteredAgents = computed(() => {
  if (!searchKeyword.value) return mockAgents.value
  return mockAgents.value.filter(agent => 
    agent.name.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
    agent.description.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
})

// 格式化时间
const formatTime = (timeStr: string) => {
  const date = new Date(timeStr)
  const now = new Date()
  const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
  
  if (diffInHours < 1) return '刚刚'
  if (diffInHours < 24) return `${Math.floor(diffInHours)}小时前`
  if (diffInHours < 24 * 7) return `${Math.floor(diffInHours / 24)}天前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

// 创建新会话
const createDialog = () => {
  if (!selectedAgent.value) {
    ElMessage.warning('请选择一个智能体')
    return
  }
  
  const agent = mockAgents.value.find(a => a.agent_id === selectedAgent.value)
  if (agent) {
    const newDialog = {
      dialogId: Date.now().toString(),
      name: `与${agent.name}的对话`,
      agent: agent.name,
      createTime: new Date().toISOString(),
      logo: agent.logo_url
    }
    mockDialogs.value.unshift(newDialog)
    selectedDialog.value = newDialog.dialogId
    showCreateDialog.value = false
    selectedAgent.value = ''
    ElMessage.success('会话创建成功')
    
    // 跳转到新创建的会话页面
    router.push({
      path: '/conversation/chatPage',
      query: {
        dialog_id: newDialog.dialogId
      }
    })
  }
}

// 删除会话
const deleteDialog = async (dialogId: string) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个会话吗？删除后无法恢复。',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    const index = mockDialogs.value.findIndex(d => d.dialogId === dialogId)
    if (index > -1) {
      mockDialogs.value.splice(index, 1)
      if (selectedDialog.value === dialogId) {
        selectedDialog.value = ''
      }
      ElMessage.success('会话删除成功')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 选择会话
const selectDialog = (dialogId: string) => {
  selectedDialog.value = dialogId
  // ElMessage.info('进入会话')
}

// 清除搜索
const clearSearch = () => {
  searchKeyword.value = ''
}
</script>

<template>
  <div class="demo-page">
    <div class="demo-header">
      <h1>会话管理系统演示</h1>
      <p>这是一个完整的会话管理系统演示，展示了所有核心功能</p>
    </div>

    <div class="demo-container">
      <!-- 左侧边栏 -->
      <div class="sidebar">
        <!-- 新建会话按钮 -->
        <div class="create-section">
          <el-button 
            type="primary" 
            @click="showCreateDialog = true"
            class="create-btn"
            :icon="Plus"
          >
            <div class="btn-content">
              <el-icon><Plus /></el-icon>
              <span>新建会话</span>
            </div>
          </el-button>
        </div>

        <!-- 搜索框 -->
        <div class="search-section">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索会话..."
            :prefix-icon="Search"
            :suffix-icon="searchKeyword ? Close : ''"
            @click-suffix="clearSearch"
            clearable
            size="small"
          />
        </div>

        <!-- 会话列表标题 -->
        <div class="list-header">
          <span class="title">会话列表</span>
          <span class="count">({{ filteredDialogs.length }})</span>
        </div>

        <!-- 会话列表 -->
        <div class="dialog-list">
          <div v-if="filteredDialogs.length === 0" class="empty-state">
            <div class="empty-icon">💬</div>
            <div class="empty-text">
              {{ searchKeyword ? '没有找到相关会话' : '暂无会话记录' }}
            </div>
            <div v-if="!searchKeyword" class="empty-hint">
              点击上方按钮开始新的对话
            </div>
          </div>
          
          <div 
            v-for="dialog in filteredDialogs" 
            :key="dialog.dialogId"
            class="dialog-card"
            :class="{ active: selectedDialog === dialog.dialogId }"
            @click="selectDialog(dialog.dialogId)"
          >
            <div class="card-main">
              <div class="card-left">
                <div class="avatar">
                  <img :src="dialog.logo" alt="" />
                </div>
                <div class="content">
                  <div class="title" :title="dialog.name">
                    {{ dialog.name }}
                  </div>
                  <div class="subtitle">
                    {{ dialog.agent }}
                  </div>
                </div>
              </div>
              <div class="card-right">
                <div class="time">{{ formatTime(dialog.createTime) }}</div>
                <div class="actions">
                  <el-tooltip content="删除会话" placement="top">
                    <el-button
                      type="danger"
                      :icon="Delete"
                      size="small"
                      circle
                      @click.stop="deleteDialog(dialog.dialogId)"
                      class="delete-btn"
                    />
                  </el-tooltip>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧内容区域 -->
      <div class="content">
        <div v-if="!selectedDialog" class="welcome-content">
          <div class="welcome-icon">
            <el-icon size="48" color="#3b82f6">
              <Star />
            </el-icon>
          </div>
          <h2>欢迎使用会话管理系统</h2>
          <p>从左侧选择一个会话开始对话，或创建新的会话</p>
        </div>
        <div v-else class="chat-content">
          <div class="chat-header">
            <h3>正在与 {{ mockDialogs.find(d => d.dialogId === selectedDialog)?.agent }} 对话</h3>
          </div>
          <div class="chat-messages">
            <div class="message system">
              <p>这是一个演示页面，实际的聊天功能需要连接到后端服务。</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建会话对话框 -->
    <el-dialog 
      v-model="showCreateDialog" 
      title="选择智能体创建会话" 
      width="500px"
    >
      <div class="dialog-content">
        <div class="search-section">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索智能体..."
            :prefix-icon="Search"
            clearable
            size="large"
          />
        </div>

        <div class="agents-section">
          <div class="section-header">
            <span class="title">可用智能体</span>
            <span class="count">({{ filteredAgents.length }})</span>
          </div>

          <div v-if="filteredAgents.length === 0" class="empty-state">
            <div class="empty-icon">🤖</div>
            <div class="empty-text">没有找到相关智能体</div>
          </div>

          <div v-else class="agents-grid">
            <div
              v-for="agent in filteredAgents"
              :key="agent.agent_id"
              :class="['agent-card', selectedAgent === agent.agent_id ? 'active' : '']"
              @click="selectedAgent = agent.agent_id"
            >
              <div class="agent-avatar">
                <img :src="agent.logo_url" alt="" />
              </div>
              <div class="agent-info">
                <div class="agent-name">{{ agent.name }}</div>
                <div class="agent-description">{{ agent.description }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="createDialog"
            :disabled="!selectedAgent"
          >
            创建会话
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.demo-page {
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;

  .demo-header {
    text-align: center;
    color: white;
    margin-bottom: 20px;

    h1 {
      font-size: 2rem;
      margin: 0 0 8px 0;
      text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    p {
      font-size: 1rem;
      margin: 0;
      opacity: 0.9;
    }
  }

  .demo-container {
    display: flex;
    height: calc(100vh - 120px);
    background: rgba(255, 255, 255, 0.95);
    border-radius: 16px;
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    overflow: hidden;

    .sidebar {
      width: 300px;
      background: #f8f9fa;
      border-right: 1px solid #e9ecef;
      display: flex;
      flex-direction: column;

      .create-section {
        padding: 20px 16px 16px;

        .create-btn {
          width: 100%;
          height: 48px;
          border-radius: 8px;

          .btn-content {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
          }
        }
      }

      .search-section {
        padding: 16px;
        border-bottom: 1px solid #f0f0f0;
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

          &:hover {
            border-color: #3b82f6;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
            transform: translateY(-2px);
          }

          &.active {
            border-color: #3b82f6;
            background-color: #eff6ff;
          }

          .card-main {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;

            .card-left {
              display: flex;
              align-items: center;
              gap: 12px;
              flex: 1;

              .avatar {
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

              .content {
                flex: 1;

                .title {
                  font-size: 14px;
                  font-weight: 600;
                  color: #1f2937;
                  margin-bottom: 4px;
                  overflow: hidden;
                  text-overflow: ellipsis;
                  white-space: nowrap;
                }

                .subtitle {
                  font-size: 12px;
                  color: #6b7280;
                }
              }
            }

            .card-right {
              display: flex;
              flex-direction: column;
              align-items: flex-end;
              gap: 8px;

              .time {
                font-size: 11px;
                color: #9ca3af;
              }

              .actions {
                opacity: 0;
                transition: opacity 0.2s ease;

                .delete-btn {
                  width: 24px;
                  height: 24px;
                  padding: 0;
                }
              }
            }
          }

          &:hover .actions {
            opacity: 1;
          }
        }
      }
    }

    .content {
      flex: 1;
      display: flex;
      flex-direction: column;

      .welcome-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        color: #6b7280;

        .welcome-icon {
          margin-bottom: 24px;
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
      }
    }

    .agents-grid {
      display: grid;
      gap: 12px;

      .agent-card {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px;
        border: 2px solid transparent;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;

        &:hover {
          background: #f9fafb;
        }

        &.active {
          border-color: #3b82f6;
          background: #eff6ff;
        }

        .agent-avatar {
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

        .agent-info {
          flex: 1;

          .agent-name {
            font-size: 14px;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 4px;
          }

          .agent-description {
            font-size: 12px;
            color: #6b7280;
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
  .demo-page {
    padding: 10px;

    .demo-container {
      flex-direction: column;

      .sidebar {
        width: 100%;
        height: 300px;
      }

      .content {
        flex: 1;
      }
    }
  }
}
</style> 