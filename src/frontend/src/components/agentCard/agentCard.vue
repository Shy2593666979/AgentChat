<script lang="ts" setup>
import { onMounted } from "vue"
import { ElMessage } from 'element-plus'
import { Agent } from "../../type"
import { deleteAgentAPI } from '../../apis/agent'
import { showDeleteConfirm } from '../../utils/dialog'

const props = defineProps<{
  item: Agent
}>()

const emits = defineEmits<{
  (event:'delete'):void
  (event:'edit', agent: Agent):void
}>()

onMounted(() => {
  document.addEventListener('DOMContentLoaded', function() {
  var content = document.getElementById('middle');
  var clampText = function(text: string , maxLines: number) {
    var lines = text.split('\n'); // 按换行符分割文本
    if (lines.length > maxLines) {
      var clampedText = lines.slice(0, maxLines).join('\n') + '...'; // 获取前几行文本并添加省略号
      if (content) content.textContent = clampedText; // 设置文本内容
    } else {
      if (content) content.textContent = text; // 如果文本行数不超过指定行数，则不添加省略号
    }
  };
  clampText(props.item.description, 3); // 截断为3行
});
})

const deleteAgent = async() => {
  try {
    await showDeleteConfirm(`确定要删除智能体 "${props.item.name}" 吗？`)
    
    const response = await deleteAgentAPI({ agent_id: props.item.agent_id })
    if (response.data?.status_code === 200) {
      ElMessage.success('删除成功')
      emits('delete')
    } else {
      ElMessage.error('删除失败')
    }
  } catch (error) {
    // 用户取消删除，不需要处理
    console.log('用户取消删除')
  }
}

const editAgent = () => {
  emits('edit', props.item)
}



</script>

<template>
  <div class="agentCard">
    <div class="content">
      <div class="top">
        <img :src="props.item.logo_url" alt="" width="40px" height="40px" />
        <span>{{ props.item.name }}</span>
      </div>
      <div class="middle" id="middle">
        {{ props.item.description }}
      </div>
      
      <div class="agent-stats">
        <div class="stat-item" :title="`工具数量: ${props.item.tool_ids?.length || 0}`">
          <div class="stat-icon">🔧</div>
          <span class="stat-label">工具</span>
          <span class="stat-value">{{ props.item.tool_ids?.length || 0 }}</span>
        </div>
        <div class="stat-item" :title="`知识库数量: ${props.item.knowledge_ids?.length || 0}`">
          <div class="stat-icon">📚</div>
          <span class="stat-label">知识库</span>
          <span class="stat-value">{{ props.item.knowledge_ids?.length || 0 }}</span>
        </div>
        <div class="stat-item" :title="`MCP数量: ${props.item.mcp_ids?.length || 0}`">
          <div class="stat-icon">🤖</div>
          <span class="stat-label">MCP</span>
          <span class="stat-value">{{ props.item.mcp_ids?.length || 0 }}</span>
        </div>
      </div>
      
      <div class="bottom">
        <div class="edit" @click.stop="editAgent">
          <img src="../../assets/set.svg" width="24px" />
        </div>
        <div class="delete" @click.stop="deleteAgent">
          <img src="../../assets/delete.svg" width="28px" />
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.agentCard {
  margin: 8px 8px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  height: 160px;
  background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 20px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #06b6d4 100%);
    border-radius: 20px 20px 0 0;
  }

      .content {
      padding: 14px;
      display: flex;
      flex-direction: column;
      height: 100%;

      .top {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        
        img {
          width: 36px;
          height: 36px;
          border-radius: 10px;
          margin-right: 10px;
          border: 2px solid rgba(59, 130, 246, 0.1);
          object-fit: cover;
          transition: all 0.3s ease;
        }
        
        span {
          font-size: 15px;
          font-weight: 600;
          color: #1e293b;
          font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
          line-height: 1.3;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          flex: 1;
        }
      }

          .middle {
        display: -webkit-box;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
        overflow: hidden;
        font-size: 12px;
        font-weight: 400;
        line-height: 1.4;
        color: #64748b;
        margin-bottom: 10px;
        flex: 1;
        font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
            }
      
      .agent-stats {
        display: flex;
        gap: 4px;
        margin-bottom: 8px;
        
        .stat-item {
          display: flex;
          align-items: center;
          gap: 3px;
          padding: 2px 4px;
          background: rgba(59, 130, 246, 0.08);
          border-radius: 8px;
          border: 1px solid rgba(59, 130, 246, 0.15);
          transition: all 0.3s ease;
          cursor: default;
          
          &:hover {
            background: rgba(59, 130, 246, 0.12);
            border-color: rgba(59, 130, 246, 0.25);
            transform: translateY(-1px);
          }
          
          .stat-icon {
            font-size: 12px;
            line-height: 1;
          }
          
          .stat-label {
            font-size: 9px;
            font-weight: 500;
            color: #64748b;
            white-space: nowrap;
          }
          
          .stat-value {
            font-size: 10px;
            font-weight: 600;
            color: #3b82f6;
            background: rgba(59, 130, 246, 0.1);
            padding: 1px 4px;
            border-radius: 4px;
            min-width: 16px;
            text-align: center;
            line-height: 1;
          }
        }
      }
      
      .bottom {
      display: flex;
      justify-content: flex-end;
      align-items: center;
      gap: 12px;
      margin-top: auto;
      
             .edit, .delete {
         display: flex;
         align-items: center;
         justify-content: center;
         width: 28px;
         height: 28px;
         border-radius: 8px;
         cursor: pointer;
         transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
         opacity: 0;
         transform: translateY(8px);
         
         img {
           width: 16px;
           height: 16px;
           transition: all 0.3s ease;
         }
       }
      
      .edit {
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        
        &:hover {
          background: rgba(59, 130, 246, 0.2);
          border-color: rgba(59, 130, 246, 0.4);
          transform: translateY(-2px);
          box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
          
          img {
            filter: saturate(1.5);
            transform: scale(1.1);
          }
        }
      }
      
      .delete {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.2);
        
        &:hover {
          background: rgba(239, 68, 68, 0.2);
          border-color: rgba(239, 68, 68, 0.4);
          transform: translateY(-2px);
          box-shadow: 0 8px 20px rgba(239, 68, 68, 0.3);
          
          img {
            filter: saturate(1.5);
            transform: scale(1.1);
          }
        }
      }
    }
  }
  
  &:hover {
    background: linear-gradient(145deg, #ffffff 0%, #f1f5f9 100%);
    border-color: rgba(59, 130, 246, 0.3);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    transform: translateY(-8px) scale(1.02);
    
    .content {
      .top {
        img {
          border-color: rgba(59, 130, 246, 0.3);
          transform: scale(1.05);
        }
        
        span {
          color: #3b82f6;
        }
      }
      
      .bottom {
        .edit, .delete {
          opacity: 1;
          transform: translateY(0);
        }
      }
    }
  }
}
</style>
