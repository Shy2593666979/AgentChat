<script setup lang="ts">
import AgentCard from "../../components/agentCard/index"
import { onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import { Agent } from "../../type"
import { getAgentsAPI } from "../../apis/agent"


const router = useRouter()
const cardList = ref<Agent[]>([])


const openDialog = (event: string, item?: Agent) => {
  if (event === "create") {
    // 创建智能体时跳转到编辑页面
    createAgent()
  } else {
    // 编辑智能体时跳转到编辑页面
    editAgent(item!)
  }
}

// 创建智能体 - 跳转到编辑页面
const createAgent = () => {
  router.push('/agent/editor')
}

// 编辑智能体 - 跳转到编辑页面
const editAgent = (agent: Agent) => {
  router.push({
    path: '/agent/editor',
    query: { id: agent.agent_id }
  })
}

const updateList = async () => {
  try {
    const response = await getAgentsAPI()
    cardList.value = response.data.data
  } catch (error) {
    console.error('获取智能体列表失败:', error)
  }
}

onMounted(async () => {
  updateList()
})

</script>

<template>
  <div class="agent-card">
    <div class="create" @click="openDialog('create')">
      <div class="content">
        <div class="top">
          <img src="../../assets/plugin.svg" alt="" width="40px" height="40px" />
          <span>新建助手</span>
        </div>
        <div class="middle">
          通过描述角色和任务来创建你的助手<br />
          助手可以调用多个技能和工具
        </div>
      </div>
    </div>
    <div v-for="item in cardList" :key="item.agent_id">
      <AgentCard
        :item="item"
        @delete="updateList"
        @edit="editAgent"
        @click="openDialog('update', item)"
      ></AgentCard>
    </div>

  </div>
</template>

<style lang="scss" scoped>
.agent-card {
  padding: 32px;
  min-height: calc(100vh - 150px);
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  
  .create {
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    height: 160px;
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    border-radius: 20px;
    border: 2px solid transparent;
    box-shadow: 0 8px 32px rgba(59, 130, 246, 0.2);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    position: relative;
    overflow: hidden;
    
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
      backdrop-filter: blur(20px);
    }
    
    &::after {
      content: '';
      position: absolute;
      top: -2px;
      left: -2px;
      right: -2px;
      bottom: -2px;
      background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 50%, #8b5cf6 100%);
      border-radius: 22px;
      z-index: -1;
      opacity: 0;
      transition: opacity 0.3s ease;
    }

          .content {
        padding: 16px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        height: 100%;
        position: relative;
        z-index: 1;

        .top {
          display: flex;
          align-items: center;
          margin-bottom: 12px;
          
          img {
            width: 40px;
            height: 40px;
            margin-right: 12px;
            filter: brightness(0) invert(1) drop-shadow(0 2px 8px rgba(255, 255, 255, 0.3));
            transition: all 0.3s ease;
          }
          
          span {
            font-size: 18px;
            font-weight: 600;
            color: white;
            font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
          }
        }

        .middle {
          font-size: 14px;
          font-weight: 400;
          line-height: 1.5;
          color: rgba(255, 255, 255, 0.9);
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
          font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
        }
      }
    
    &:hover {
      transform: translateY(-8px) scale(1.02);
      box-shadow: 0 20px 60px rgba(59, 130, 246, 0.4);
      
      &::after {
        opacity: 1;
      }
      
      .content {
        .top img {
          transform: scale(1.1) rotate(5deg);
          filter: brightness(0) invert(1) drop-shadow(0 4px 12px rgba(255, 255, 255, 0.5));
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .agent-card {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
    padding: 24px;
  }
}

@media (max-width: 768px) {
  .agent-card {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 16px;
    
    .create {
      height: 180px;
      
      .content {
        padding: 24px;
        
        .top {
          span {
            font-size: 20px;
          }
          
          img {
            width: 40px;
            height: 40px;
          }
        }
        
        .middle {
          font-size: 14px;
        }
      }
    }
  }
}
</style>
