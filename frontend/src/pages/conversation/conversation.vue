<script setup lang="ts">
import HistortCard from "../../components/historyCard/index"
import Drawer from "../../components/drawer"
import { ref, onMounted } from "vue"
import DefaultPage from "./defaultPage/defaultPage.vue"
import ChatPage from "./chatPage/index"
import moment from "moment"
import { getDialogListAPI } from "../../apis/history"
import { CardListType } from '../../type'

interface HistoryListType {
  agent: string
  dialogId: string
  name: string
  createTime: string
}

const drawerRef = ref()
const defaultPage = ref(true)
const chatItem = ref<CardListType>()
const historyList = ref<HistoryListType[]>([])

onMounted(async () => {
  const list = await getDialogListAPI()
  historyList.value = list.data.data
  historyList.value.map((item) => {
    {
      item.createTime = moment(item.createTime).format("YYYY-MM-DD HH:mm")
    }
  })
})

const open = () => {
  drawerRef.value.open()
}

const chat = (item: CardListType) => {
  defaultPage.value = false
  chatItem.value = item
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
            v-for="item in historyList"
            class="card"
            :key="item.dialogId"
            :title="item.name"
            :detail="item.agent"
            :time="item.createTime"
          ></HistortCard>
        </div>
      </el-scrollbar>
    </div>
    <div class="content" v-if="defaultPage">
      <DefaultPage></DefaultPage>
    </div>
    <div class="content" v-else>
      <ChatPage :item="chatItem as CardListType"></ChatPage>
    </div>
    <Drawer ref="drawerRef" @goChat="chat"></Drawer>
  </div>
</template>

<style lang="scss" scoped>
.ai-conversation-main {
  display: flex;
  height: calc(100vh - 60px);

  .aside {
    width: 180px;
    height: 100%;
    border-right: 2px solid #f0f3f5;
    padding: 10px 10px 10px 0px;

    .create {
      display: flex;
      height: 50px;
      justify-content: center;
      align-items: center;
      :deep(.el-button) {
        border: none;
      }
      :deep(.el-button):hover {
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
    width: calc(100vw - 330px);
  }
}
</style>
