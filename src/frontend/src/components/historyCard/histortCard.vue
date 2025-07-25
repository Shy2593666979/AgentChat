<script lang="ts" setup>
import { computed } from "vue"
import { HistoryListType } from "../../type"

const emits = defineEmits<{
    (event:'delete'):void
    (event:'select'):void
}>();

const props = defineProps<{
    item:HistoryListType
}>();

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

// 选择会话
const selectCard = () => {
  console.log('【historyCard】点击了会话卡片，item:', props.item)
  emits('select')
}
</script>

<template>
  <div class="history-card" @click="selectCard">
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
          <span
            class="delete-icon"
            @click="deleteCard"
          >×</span>
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
        opacity: 1; /* 修改为始终可见 */
        transition: opacity 0.2s ease;

        .delete-icon {
          color: #909399;
          font-size: 18px;
          font-weight: bold;
          cursor: pointer;
          width: 20px;
          height: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: transform 0.2s;
          
          &:hover {
            transform: scale(1.2);
          }
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
