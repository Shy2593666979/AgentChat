<script setup lang="ts">
import { Search, Plus, Star } from "@element-plus/icons-vue"
import CommonCard from "../../../components/commonCard"
import { ref, onMounted, computed } from "vue"
import { createDialogAPI } from "../../../apis/history"
import { getAgentsAPI, searchAgentsAPI } from "../../../apis/agent"
import { Agent } from "../../../type"
import { useHistoryChatStore } from "../../../store/history_chat_msg"
import { useHistoryListStore } from "../../../store/history_list/index"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"

const router = useRouter()
const historyListStore = useHistoryListStore()
const historyChatStore = useHistoryChatStore()
const searchInput = ref("")
const CardList = ref<Agent[]>([])
const loading = ref(false)

// 过滤后的智能体列表
const filteredAgents = computed(() => {
  if (!searchInput.value) {
    return CardList.value
  }
  return CardList.value.filter(agent => 
    agent.name.toLowerCase().includes(searchInput.value.toLowerCase()) ||
    agent.description.toLowerCase().includes(searchInput.value.toLowerCase())
  )
})

onMounted(async () => {
  await loadAgents()
})

const loadAgents = async () => {
  try {
    loading.value = true
    const response = await getAgentsAPI()
    CardList.value = response.data.data
  } catch (error) {
    console.error('获取智能体列表失败:', error)
    ElMessage.error('获取智能体列表失败')
  } finally {
    loading.value = false
  }
}

const gochat = async (item: Agent) => {
  try {
    historyChatStore.name = item.name
    historyChatStore.logo = item.logo_url
    const list = await createDialogAPI({ agent: item.name })
    historyChatStore.dialogId = list.data.data.dialogId
    historyChatStore.clear()
    await historyListStore.getList()
    router.push("/conversation/chatPage")
    ElMessage.success('会话创建成功')
  } catch (error) {
    ElMessage.error('创建会话失败')
  }
}

const searchAgent = async () => {
  if (searchInput.value) {
    try {
      loading.value = true
      const response = await searchAgentsAPI({ name: searchInput.value })
      CardList.value = response.data.data.map(item => ({
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
    } catch (error) {
      console.error('搜索智能体失败:', error)
      ElMessage.error('搜索失败')
    } finally {
      loading.value = false
    }
  } else {
    await loadAgents()
  }
}

const clearSearch = () => {
  searchInput.value = ''
  loadAgents()
}
</script>

<template>
  <div class="default-page">
    <!-- 头部区域 -->
    <div class="header-section">
      <div class="welcome-content">
        <div class="welcome-icon">
          <el-icon size="48" color="#3b82f6">
            <Star />
          </el-icon>
        </div>
        <div class="welcome-text">
          <h1 class="title">
            欢迎使用 <span class="highlight">智言</span> 平台
          </h1>
          <p class="subtitle">
            选择您需要的智能体，开始智能对话之旅
          </p>
        </div>
      </div>
    </div>

    <!-- 搜索区域 -->
    <div class="search-section">
      <div class="search-container">
        <el-input
          v-model="searchInput"
          placeholder="搜索智能体功能..."
          class="search-input"
          size="large"
          @keydown.enter="searchAgent"
          clearable
          @clear="clearSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
          <template #append>
            <el-button 
              type="primary" 
              @click="searchAgent"
              :loading="loading"
            >
              搜索
            </el-button>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 智能体列表区域 -->
    <div class="agents-section">
      <div class="section-header">
        <div class="header-left">
          <h2 class="section-title">可用智能体</h2>
          <span class="agent-count">({{ filteredAgents.length }})</span>
        </div>
        <div class="header-right">
          <el-button 
            type="primary" 
            :icon="Plus"
            @click="loadAgents"
            :loading="loading"
          >
            刷新列表
          </el-button>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="6" animated />
      </div>

      <!-- 空状态 -->
      <div v-else-if="filteredAgents.length === 0" class="empty-state">
        <div class="empty-icon">🤖</div>
        <div class="empty-title">
          {{ searchInput ? '没有找到相关智能体' : '暂无可用智能体' }}
        </div>
        <div class="empty-description">
          {{ searchInput ? '请尝试其他关键词' : '请联系管理员添加智能体' }}
        </div>
        <el-button 
          v-if="searchInput" 
          type="primary" 
          @click="clearSearch"
        >
          清除搜索
        </el-button>
      </div>

      <!-- 智能体网格 -->
      <div v-else class="agents-grid">
        <div 
          v-for="item in filteredAgents" 
          :key="item.agent_id"
          class="agent-item"
        >
          <CommonCard
            class="agent-card"
            :title="item.name"
            :detail="item.description"
            :imgUrl="item.logo_url"
            @click="gochat(item)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.default-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;

  .header-section {
    text-align: center;
    margin-bottom: 40px;

    .welcome-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 20px;

      .welcome-icon {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 50%;
        padding: 20px;
        backdrop-filter: blur(10px);
      }

      .welcome-text {
        .title {
          font-size: 2.5rem;
          font-weight: 700;
          color: white;
          margin: 0 0 12px 0;
          text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

          .highlight {
            color: #fbbf24;
            text-shadow: 0 2px 4px rgba(251, 191, 36, 0.3);
          }
        }

        .subtitle {
          font-size: 1.1rem;
          color: rgba(255, 255, 255, 0.9);
          margin: 0;
          font-weight: 400;
        }
      }
    }
  }

  .search-section {
    margin-bottom: 40px;

    .search-container {
      max-width: 600px;
      margin: 0 auto;

      .search-input {
        :deep(.el-input__wrapper) {
          border-radius: 12px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(10px);
          
          &:hover {
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
          }
          
          &.is-focus {
            box-shadow: 0 0 0 2px #3b82f6;
          }
        }

        :deep(.el-input-group__append) {
          .el-button {
            border-radius: 0 12px 12px 0;
            border: none;
            background: #3b82f6;
            
            &:hover {
              background: #2563eb;
            }
          }
        }
      }
    }
  }

  .agents-section {
    flex: 1;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 20px;
    padding: 32px;
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);

    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;

      .header-left {
        display: flex;
        align-items: center;
        gap: 8px;

        .section-title {
          font-size: 1.5rem;
          font-weight: 600;
          color: #1f2937;
          margin: 0;
        }

        .agent-count {
          font-size: 0.9rem;
          color: #6b7280;
          background: #f3f4f6;
          padding: 4px 8px;
          border-radius: 12px;
        }
      }
    }

    .loading-state {
      padding: 40px 0;
    }

    .empty-state {
      text-align: center;
      padding: 60px 20px;
      color: #6b7280;

      .empty-icon {
        font-size: 4rem;
        margin-bottom: 16px;
      }

      .empty-title {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 8px;
        color: #374151;
      }

      .empty-description {
        font-size: 0.9rem;
        margin-bottom: 24px;
      }
    }

    .agents-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 24px;

      .agent-item {
        .agent-card {
          transition: all 0.3s ease;
          border-radius: 16px;
          overflow: hidden;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);

          &:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
          }
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .default-page {
    padding: 16px;

    .header-section {
      .welcome-content {
        .welcome-text {
          .title {
            font-size: 2rem;
          }

          .subtitle {
            font-size: 1rem;
          }
        }
      }
    }

    .agents-section {
      padding: 20px;

      .section-header {
        flex-direction: column;
        gap: 16px;
        align-items: flex-start;
      }

      .agents-grid {
        grid-template-columns: 1fr;
        gap: 16px;
      }
    }
  }
}

@media (max-width: 480px) {
  .default-page {
    .header-section {
      .welcome-content {
        .welcome-text {
          .title {
            font-size: 1.5rem;
          }
        }
      }
    }
  }
}
</style>
