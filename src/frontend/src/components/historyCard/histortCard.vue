<script lang="ts" setup>
import { computed } from "vue"
import { HistoryListType } from "../../type"
import { Delete } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const emits = defineEmits<{
    (event:'delete'):void
}>();

const props = defineProps<{
    item:HistoryListType
}>();

const router = useRouter()

// 格式化时间显示
const formattedTime = computed(() => {
  try {
    const date = new Date(props.item.createTime)
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
    
    if (diffInHours < 1) {
      return '刚刚'
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}小时前`
    } else if (diffInHours < 24 * 7) {
      return `${Math.floor(diffInHours / 24)}天前`
    } else {
      return date.toLocaleDateString('zh-CN', { 
        month: 'short', 
        day: 'numeric' 
      })
    }
  } catch (error) {
    return '未知时间'
  }
})

const deleteCard = (event: Event) => {
  event.stopPropagation()
  emits('delete')
}

// 跳转到聊天页面
const goToChat = () => {
  console.log('【historyCard】点击了会话卡片，item:', props.item)
  
  if (props.item.dialogId) {
    console.log('【historyCard】准备跳转到聊天页面，dialogId:', props.item.dialogId)
    router.push({ path: '/conversation/chatPage', query: { dialog_id: props.item.dialogId } })
  } else {
    console.error('【historyCard】会话卡片缺少 dialogId 字段，无法跳转')
    console.error('【historyCard】当前item的所有字段:', Object.keys(props.item))
  }
}
</script>

<template>
  <div class="history-card" @click="goToChat">
    <!-- 卡片主体 -->
    <div class="card-main">
      <!-- 左侧图标和标题 -->
      <div class="card-left">
        <div class="avatar">
          <img :src="props.item.logo || '/default-avatar.png'" alt="" />
        </div>
        <div class="content">
          <div class="title" :title="props.item.name">
            {{ props.item.name || '未命名会话' }}
          </div>
          <div class="subtitle">
            {{ props.item.agent || '智能助手' }}
          </div>
        </div>
      </div>

      <!-- 右侧操作区域 -->
      <div class="card-right">
        <div class="time">{{ formattedTime }}</div>
        <div class="actions">
          <el-button
            type="danger"
            :icon="Delete"
            size="small"
            circle
            @click="deleteCard"
            class="delete-btn"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.history-card {
  position: relative;
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 8px;

  &:hover {
    border-color: #3b82f6;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
    transform: translateY(-2px);

    .card-right .actions {
      opacity: 1;
    }
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
      min-width: 0;

      .avatar {
        flex-shrink: 0;
        width: 40px;
        height: 40px;
        border-radius: 8px;
        overflow: hidden;
        background-color: #f3f4f6;
        display: flex;
        align-items: center;
        justify-content: center;

        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      }

      .content {
        flex: 1;
        min-width: 0;

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
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
    }

    .card-right {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 8px;
      flex-shrink: 0;

      .time {
        font-size: 11px;
        color: #9ca3af;
        white-space: nowrap;
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
}

// 激活状态
.history-card.active {
  border-color: #3b82f6;
  background-color: #eff6ff;
  box-shadow: 0 0 0 1px #3b82f6;

  .card-left .content .title {
    color: #1d4ed8;
  }
}

// 响应式设计
@media (max-width: 480px) {
  .history-card {
    padding: 12px;

    .card-main {
      .card-left {
        gap: 8px;

        .avatar {
          width: 32px;
          height: 32px;
        }

        .content {
          .title {
            font-size: 13px;
          }

          .subtitle {
            font-size: 11px;
          }
        }
      }

      .card-right {
        .time {
          font-size: 10px;
        }
      }
    }
  }
}
</style>
