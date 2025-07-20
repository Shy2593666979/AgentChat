<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { showDeleteConfirm } from '../../utils/dialog'
import { Plus, Edit, Delete, View, Search, Refresh, Tools } from '@element-plus/icons-vue'
import { 
  getAgentsAPI, 
  deleteAgentAPI, 
  searchAgentsAPI,
  type AgentResponse 
} from '../../apis/agent'
import { Agent } from '../../type'


const router = useRouter()
const agents = ref<Agent[]>([])
const loading = ref(false)
const searchLoading = ref(false)
const editingAgent = ref<Agent | null>(null)
const searchKeyword = ref('')


// 转换API响应为本地Agent类型
const convertToAgent = (apiAgent: any): Agent => ({
  agent_id: apiAgent.id || apiAgent.agent_id, // 兼容后端返回id字段
  name: apiAgent.name,
  description: apiAgent.description,
  logo_url: apiAgent.logo_url,
  tool_ids: apiAgent.tool_ids || [],
  llm_id: apiAgent.llm_id,
  mcp_ids: apiAgent.mcp_ids || [],
  system_prompt: apiAgent.system_prompt,
  knowledge_ids: apiAgent.knowledge_ids || [],
  use_embedding: apiAgent.use_embedding,
  created_time: apiAgent.create_time || apiAgent.created_time
})

// 获取智能体列表
const fetchAgents = async () => {
  loading.value = true
  try {
    console.log('开始调用智能体API...')
    console.log('请求URL: /api/v1/agent')
    console.log('Token:', localStorage.getItem('token'))
    
    const response = await getAgentsAPI()
    console.log('API响应:', response)
    console.log('响应数据:', response.data)
    
    // 兼容不同的后端响应格式
    const responseCode = response.data.status_code || response.data.status_code
    const responseMessage = response.data.status_message || response.data.status_message
    const responseData = response.data.data
    
    if (responseCode === 200 || response.data.status_code === 200) {
      console.log('API调用成功，智能体数据:', responseData)
      if (responseData && Array.isArray(responseData)) {
        agents.value = responseData.map(convertToAgent)
        console.log('转换后的智能体列表:', agents.value)
      } else {
        console.warn('响应数据格式异常:', responseData)
        agents.value = []
      }
    } else {
      console.error('API返回错误:', responseMessage)
      ElMessage.error(responseMessage || '获取智能体列表失败')
    }
  } catch (error) {
    console.error('获取智能体列表失败 - 详细错误:', error)
    console.error('错误类型:', typeof error)
    console.error('错误信息:', error.message)
    console.error('错误响应:', error.response)
    
    if (error.response) {
      console.error('响应状态码:', error.response.status)
      console.error('响应数据:', error.response.data)
      ElMessage.error(`请求失败: ${error.response.status} - ${error.response.data?.message || '未知错误'}`)
    } else if (error.request) {
      console.error('请求对象:', error.request)
      ElMessage.error('网络错误：无法连接到服务器')
    } else {
      ElMessage.error('获取智能体列表失败：' + error.message)
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
    if (response.data.status_code === 200) {
      // 搜索结果转换为Agent格式
      agents.value = response.data.data.map(item => ({
        agent_id: item.agent_id,
        name: item.name,
        description: item.description,
        logo_url: item.logo_url,
        tool_ids: [],
        llm_id: '',
        mcp_ids: [],
        system_prompt: '',
        knowledge_ids: [],
        use_embedding: false
      }))
    } else {
      ElMessage.error(response.data.status_message || '搜索失败')
    }
  } catch (error) {
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
  router.push('/agent/editor')
}

// 编辑智能体
const editAgent = (agent: Agent) => {
  router.push({
    path: '/agent/editor',
    query: { id: agent.agent_id }
  })
}



// 处理智能体更新
const handleAgentUpdate = () => {
  fetchAgents()
}

// 删除智能体
const deleteAgent = async (agent: Agent) => {
  try {
    await showDeleteConfirm(`确定要删除智能体 "${agent.name}" 吗？`)
    
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
  // TODO: 实现智能体详情查看功能
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
      <div class="header-title">
        <div class="title-icon">
          <img src="/src/assets/robot1.svg" alt="智能体" width="40" height="40" />
        </div>
        <h2>智能体管理</h2>
      </div>
      <div class="header-actions">
        <div class="search-box">
          <div class="search-input-wrapper">
            <el-input
              v-model="searchKeyword"
              placeholder="🔍 搜索智能体名称..."
              @keyup.enter="searchAgents"
              @clear="clearSearch"
              clearable
              size="large"
              style="width: 320px"
            />
            <el-button 
              type="primary" 
              :icon="Search" 
              @click="searchAgents"
              :loading="searchLoading"
              size="large"
              style="margin-left: 12px; border-radius: 12px;"
            >
              搜索
            </el-button>
          </div>
        </div>
        <div class="action-buttons">
          <el-button 
            :icon="Refresh" 
            @click="refreshAgents"
            :loading="loading"
            title="刷新列表"
            size="large"
            circle
            style="border-radius: 12px;"
          />
          <el-button 
            type="primary" 
            :icon="Plus" 
            @click="createAgent"
            size="large"
            style="border-radius: 12px; background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); border: none;"
          >
            🤖 创建智能体
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
              :icon="Tools" 
              @click="editAgent(agent)"
              title="高级编辑"
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


  </div>
</template>

<style lang="scss" scoped>
.agent-page {
  padding: 32px;
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    padding: 32px 40px;
    border-radius: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(226, 232, 240, 0.6);
    
    .header-title {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .title-icon {
        width: 56px;
        height: 56px;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
        
        img {
          filter: brightness(0) invert(1);
        }
      }
      
      h2 {
        margin: 0;
        font-size: 28px;
        font-weight: 700;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
      }
    }
    
    .header-actions {
      display: flex;
      align-items: center;
      gap: 32px;
      
      .search-box {
        .search-input-wrapper {
          display: flex;
          align-items: center;
          background: rgba(255, 255, 255, 0.8);
          padding: 8px;
          border-radius: 16px;
          border: 1px solid rgba(59, 130, 246, 0.2);
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
          
          :deep(.el-input) {
            .el-input__wrapper {
              background: transparent;
              border: none;
              box-shadow: none;
              border-radius: 12px;
              
              .el-input__inner {
                font-size: 15px;
                font-weight: 500;
                color: #1e293b;
                
                &::placeholder {
                  color: #64748b;
                  font-weight: 400;
                }
              }
            }
          }
        }
      }
      
      .action-buttons {
        display: flex;
        gap: 16px;
        
        :deep(.el-button) {
          font-weight: 600;
          font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          
          &:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
          }
        }
      }
    }
  }
  
  .agent-list {
    height: calc(100vh - 140px);
    overflow-y: auto;
    
    .agent-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 16px;
      
      .agent-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 20px;
        padding: 16px;
        height: 160px;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(226, 232, 240, 0.8);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
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
          width: 48px;
          height: 48px;
          border-radius: 12px;
          overflow: hidden;
          margin-bottom: 12px;
          border: 2px solid #f0f0f0;
          
          img {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }
        }
        
        .agent-info {
          .agent-name {
            font-size: 16px;
            font-weight: 600;
            color: #2c3e50;
            margin: 0 0 6px 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          
          .agent-description {
            color: #64748b;
            font-size: 12px;
            line-height: 1.4;
            margin: 0 0 10px 0;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            min-height: 32px;
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
@media (min-width: 1400px) {
  .agent-list .agent-grid {
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  }
}

@media (min-width: 1200px) and (max-width: 1399px) {
  .agent-list .agent-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}

@media (min-width: 1000px) and (max-width: 1199px) {
  .agent-list .agent-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (min-width: 768px) and (max-width: 999px) {
  .agent-list .agent-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
  }
}

@media (max-width: 767px) {
  .agent-page {
    padding: 16px;
    
    .page-header {
      flex-direction: column;
      gap: 16px;
      align-items: stretch;
      padding: 24px;
      
      .header-title {
        .title-icon {
          width: 48px;
          height: 48px;
          
          img {
            width: 32px;
            height: 32px;
          }
        }
        
        h2 {
          font-size: 24px;
        }
      }
      
      .header-actions {
        flex-direction: column;
        gap: 16px;
        
        .search-box {
          .search-input-wrapper {
            flex-direction: column;
            gap: 12px;
            padding: 12px;
            
            .el-input {
              width: 100% !important;
            }
          }
        }
        
        .action-buttons {
          justify-content: center;
        }
      }
    }
    
    .agent-list .agent-grid {
      grid-template-columns: 1fr;
      gap: 16px;
    }
  }
}


</style> 