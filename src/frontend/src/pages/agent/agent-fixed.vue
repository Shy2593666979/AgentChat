<script setup lang="ts">
import RefreshIcon from "../../components/RefreshIcon.vue";
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, View, Search, Refresh } from '@element-plus/icons-vue'
import {
  getAgentsAPI,
  deleteAgentAPI,
  searchAgentsAPI
} from '../../apis/agent'
import { Agent } from '../../type'
import AgentFormDialog from '../../components/dialog/create_agent/AgentFormDialog.vue'

const agents = ref<Agent[]>([])
const loading = ref(false)
const searchLoading = ref(false)
const editingAgent = ref<Agent | null>(null)
const searchKeyword = ref('')
const agentFormRef = ref()

// 转换后端数据为前端Agent类型（兼容实际后端响应）
const convertBackendToAgent = (backendAgent: any): Agent => ({
  agent_id: backendAgent.id, // 后端返回的是id字段
  name: backendAgent.name,
  description: backendAgent.description,
  logo_url: backendAgent.logo_url,
  tool_ids: backendAgent.tool_ids || [],
  llm_id: backendAgent.llm_id,
  mcp_ids: backendAgent.mcp_ids || [],
  system_prompt: backendAgent.system_prompt || '',
  knowledge_ids: backendAgent.knowledge_ids || [],
  enable_memory: backendAgent.enable_memory || false,
  created_time: backendAgent.create_time
})

// 获取智能体列表
const fetchAgents = async () => {
  loading.value = true
  try {
    console.log('开始调用智能体API...')
    const response = await getAgentsAPI()
    console.log('API响应:', response.data)

    // 处理后端实际返回的响应格式
    if (response.data.status_code === 200 && response.data.data) {
      console.log('API调用成功，智能体数据:', response.data.data)
      agents.value = response.data.data.map(convertBackendToAgent)
      console.log('转换后的智能体列表:', agents.value)
      ElMessage.success(`成功获取 ${agents.value.length} 个智能体`)
    } else {
      console.error('API返回错误:', response.data.status_message)
      ElMessage.error(response.data.status_message || '获取智能体列表失败')
    }
  } catch (error: any) {
    console.error('获取智能体列表失败:', error)
    if (error.response) {
      ElMessage.error(`请求失败: ${error.response.status}`)
    } else {
      ElMessage.error('网络错误：无法连接到服务器')
    }
  } finally {
    loading.value = false
  }
}

// 搜索智能体
const searchAgents = async () => {
  if (!searchKeyword.value.trim()) {
    await fetchAgents()
    return
  }

  searchLoading.value = true
  try {
    const response = await searchAgentsAPI({ name: searchKeyword.value.trim() })
    if (response.data.status_code === 200 && response.data.data) {
      agents.value = response.data.data.map((item: any) => ({
        agent_id: item.agent_id,
        name: item.name,
        description: item.description,
        logo_url: item.logo_url,
        tool_ids: [],
        llm_id: '',
        mcp_ids: [],
        system_prompt: '',
        knowledge_ids: [],
        enable_memory: false
      }))
    } else {
      ElMessage.error(response.data.status_message || '搜索失败')
    }
  } catch (error: any) {
    console.error('搜索智能体失败:', error)
    ElMessage.error('搜索智能体失败')
  } finally {
    searchLoading.value = false
  }
}

// 清空搜索
const clearSearch = () => {
  searchKeyword.value = ''
  fetchAgents()
}

// 创建智能体
const createAgent = () => {
  agentFormRef.value?.open('create')
}

// 编辑智能体
const editAgent = (agent: Agent) => {
  agentFormRef.value?.open('edit', agent)
}

// 删除智能体
const deleteAgent = async (agent: Agent) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除智能体 "${agent.name}" 吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        center: true,
        lockScroll: true,
        customClass: 'delete-confirm-dialog'
      }
    )

    const response = await deleteAgentAPI({ agent_id: agent.agent_id })
    if (response.data.status_code === 200) {
      ElMessage.success('删除成功')
      await fetchAgents()
    } else {
      ElMessage.error(response.data.status_message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除智能体失败:', error)
      ElMessage.error('删除智能体失败')
    }
  }
}

// 查看智能体详情
const viewAgent = (agent: Agent) => {
  ElMessage.info('智能体详情功能开发中...')
  console.log('查看智能体:', agent)
}

// 刷新列表
const refreshAgents = () => {
  if (searchKeyword.value.trim()) {
    searchAgents()
  } else {
    fetchAgents()
  }
}

// 处理智能体更新
const handleAgentUpdate = () => {
  fetchAgents()
}

// 处理图片加载错误
const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement
  if (target) {
    target.src = '/src/assets/robot.svg'
  }
}

onMounted(() => {
  fetchAgents()
})
</script>

<template>
  <div class="agent-page">
    <div class="page-header">
      <h2>智能体管理</h2>
      <div class="header-actions">
        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索智能体..."
            :prefix-icon="Search"
            @keyup.enter="searchAgents"
            @clear="clearSearch"
            clearable
            style="width: 300px"
          />
          <el-button
            type="primary"
            :icon="Search"
            @click="searchAgents"
            :loading="searchLoading"
            style="margin-left: 10px"
          >
            搜索
          </el-button>
        </div>
        <div class="action-buttons">
          <el-button
            :icon="RefreshIcon"
            @click="refreshAgents"
            :loading="loading"
            title="刷新"
          />
          <el-button type="primary" :icon="Plus" @click="createAgent">
            创建智能体
          </el-button>
        </div>
      </div>
    </div>

    <div class="agent-list" v-loading="loading">
      <div class="agent-grid" v-if="agents.length > 0">
        <div
          v-for="agent in agents"
          :key="agent.agent_id"
          class="agent-card"
        >
          <div class="agent-avatar">
            <img
              :src="agent.logo_url || '/src/assets/robot.svg'"
              :alt="agent.name"
              @error="handleImageError"
            />
          </div>

          <div class="agent-info">
            <h3 class="agent-name" :title="agent.name">{{ agent.name }}</h3>
            <p class="agent-description" :title="agent.description">
              {{ agent.description }}
            </p>

            <div class="agent-meta">
              <span class="meta-item">
                <i class="meta-icon">🔧</i>
                工具: {{ agent.tool_ids?.length || 0 }}
              </span>
              <span class="meta-item">
                <i class="meta-icon">📚</i>
                知识库: {{ agent.knowledge_ids?.length || 0 }}
              </span>
              <span class="meta-item">
                <i class="meta-icon">🤖</i>
                MCP: {{ agent.mcp_ids?.length || 0 }}
              </span>
            </div>

            <div class="agent-status">
              <el-tag
                :type="agent.enable_memory ? 'success' : 'info'"
                size="small"
              >
                {{ agent.enable_memory ? '已启用向量化' : '未启用向量化' }}
              </el-tag>
            </div>
          </div>

          <div class="agent-actions">
            <el-button
              size="small"
              :icon="View"
              @click="viewAgent(agent)"
              title="查看详情"
              plain
            />
            <el-button
              size="small"
              type="primary"
              :icon="Edit"
              @click="editAgent(agent)"
              title="编辑"
              plain
            />
            <el-button
              size="small"
              type="danger"
              :icon="Delete"
              @click="deleteAgent(agent)"
              title="删除"
              plain
            />
          </div>
        </div>
      </div>

      <div v-else-if="!loading" class="empty-state">
        <img src="/src/assets/404.gif" alt="暂无数据" width="300" />
        <p v-if="searchKeyword">
          未找到包含 "{{ searchKeyword }}" 的智能体
        </p>
        <p v-else>
          暂无智能体，点击上方按钮创建第一个智能体吧！
        </p>
        <el-button
          v-if="searchKeyword"
          type="primary"
          @click="clearSearch"
          style="margin-top: 20px"
        >
          查看所有智能体
        </el-button>
      </div>
    </div>

    <!-- 创建/编辑智能体对话框 -->
    <AgentFormDialog ref="agentFormRef" @update="handleAgentUpdate" />
  </div>
</template>

<style lang="scss" scoped>
.agent-page {
  padding: 24px;
  height: 100vh;
  background-color: #f8f9fa;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    background: white;
    padding: 20px 24px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

    h2 {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
      color: #2c3e50;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 20px;

      .search-box {
        display: flex;
        align-items: center;
      }

      .action-buttons {
        display: flex;
        gap: 12px;
      }
    }
  }

  .agent-list {
    height: calc(100vh - 140px);
    overflow-y: auto;

    .agent-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
      gap: 24px;

      .agent-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        border: 1px solid #e1e8ed;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;

        &:hover {
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
          transform: translateY(-4px);

          .agent-actions {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .agent-avatar {
          width: 64px;
          height: 64px;
          border-radius: 16px;
          overflow: hidden;
          margin-bottom: 16px;
          border: 2px solid #f0f0f0;

          img {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }
        }

        .agent-info {
          .agent-name {
            font-size: 20px;
            font-weight: 600;
            color: #2c3e50;
            margin: 0 0 8px 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          .agent-description {
            color: #64748b;
            font-size: 14px;
            line-height: 1.6;
            margin: 0 0 16px 0;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            min-height: 40px;
          }

          .agent-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 12px;

            .meta-item {
              font-size: 12px;
              color: #64748b;
              display: flex;
              align-items: center;
              gap: 4px;
              background: #f8fafc;
              padding: 4px 8px;
              border-radius: 6px;

              .meta-icon {
                font-size: 14px;
              }
            }
          }

          .agent-status {
            margin-top: 12px;
          }
        }

        .agent-actions {
          position: absolute;
          top: 20px;
          right: 20px;
          display: flex;
          gap: 8px;
          opacity: 0;
          transform: translateY(-10px);
          transition: all 0.3s ease;

          .el-button {
            padding: 8px;
            border-radius: 8px;
          }
        }
      }
    }

    .empty-state {
      text-align: center;
      padding: 80px 20px;
      color: #64748b;
      background: white;
      border-radius: 16px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);

      p {
        margin-top: 24px;
        font-size: 16px;
        line-height: 1.5;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .agent-page {
    padding: 16px;

    .page-header {
      flex-direction: column;
      gap: 16px;
      align-items: stretch;

      .header-actions {
        flex-direction: column;
        gap: 12px;

        .search-box {
          flex-direction: column;
          gap: 8px;

          .el-input {
            width: 100% !important;
          }
        }
      }
    }

    .agent-list .agent-grid {
      grid-template-columns: 1fr;
    }
  }
}
</style>