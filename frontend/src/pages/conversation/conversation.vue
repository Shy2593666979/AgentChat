<script setup lang="ts">
import HistortCard from "../../components/historyCard/index"
import Drawer from "../../components/drawer"
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import { CardListType, HistoryListType } from "../../type"
import { ElScrollbar } from "element-plus"
import { useHistoryListStore } from "../../store/history_list/index"
import { createDialogAPI, deleteDialogAPI } from "../../apis/history"
import { useHistoryChatStore } from "../../store/history_chat_msg"
import { useAgentCardStore } from "../../store/agent_card"


const agentCardStore = useAgentCardStore()
const router = useRouter()
const drawerRef = ref()
const historyListStore = useHistoryListStore()
const historyChatStore = useHistoryChatStore()


onMounted(async () => {
  historyListStore.getList()
})

const open = () => {
  drawerRef.value.open()
}

const chat = async (item: CardListType) => {
  historyChatStore.name = item.name
  historyChatStore.logo = item.logo
  const list = await createDialogAPI({ agent: (item as CardListType).name })
  historyChatStore.dialogId = list.data.data.dialogId
  agentCardStore.currentId = list.data.data.dialogId
  historyChatStore.clear()
  historyListStore.getList()
  router.push("/conversation/chatPage")
}

const goHisChat = async (item: HistoryListType) => {
  agentCardStore.currentId = item.dialogId
  historyChatStore.dialogId = item.dialogId
  historyChatStore.name = item.name
  historyChatStore.logo = item.logo
  historyChatStore.clear()
  historyChatStore.HistoryChat(historyChatStore.dialogId)
  router.push("/conversation/chatPage")
}


const deleteCard = async (item: HistoryListType) => {
  await deleteDialogAPI(item.dialogId)
  historyListStore.getList()
  router.push("/conversation/")
}
</script>

<template>
  <div class="ai-conversation-main">
    <div class="aside">
      <div class="create">
        <el-button @click="open">
          <div class="img">
            <img
              src="../../assets/create_dialog.svg"
              alt=""
              width="30px"
              height="30px"
            />
          </div>
          <div clasrews="text">新建会话</div>
        </el-button>
      </div>
      <el-scrollbar>
        <div class="history-card-list">
          <HistortCard
            v-for="item in historyListStore.historyList"
            class="card"
            :key="item.dialogId"
            :item="item"
            :class="agentCardStore.currentId === item.dialogId ? 'active' : ''"
            @click="goHisChat(item)"
            @delete="deleteCard(item)"
          ></HistortCard>
        </div>
      </el-scrollbar>
    </div>
    <div class="content">
      <router-view ></router-view>
    </div>
    <Drawer ref="drawerRef" @goChat="chat"></Drawer>
  </div>
</template>

<style lang="scss" scoped>
.ai-conversation-main {
  display: flex;
  height: calc(100vh - 60px);

  .aside {
    height: 100%;
    width: 150px;
    border-right: 2px solid #f0f3f5;
    padding: 0px 10px 10px 0px;
    margin-left: 10px;
    .create {
      display: flex;
      height: 50px;
      justify-content: center;
      align-items: center;
      :deep(.el-button) {
        border: none;
      }
      :deep(.el-button):hover {
        border: none;
        background-color: #fff;
      }
      .img {
        margin-right: 20px;
      }

      .text {
        font-weight: 500;
        margin-bottom: 8px;
      }
    }
    .history-card-list {
      .card {
        margin-bottom: 8px;
      }
    }
  }
  .content {
    width: calc(100vw - 282px);
  }
  .active {
    background-color: rgb(236, 236, 236);
  }
}
</style>
