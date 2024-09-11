<script setup lang="ts">
import { Search } from "@element-plus/icons-vue"
import CommonCard from "../../../components/commonCard"
import { ref, onMounted } from "vue"
import {
  createDialogAPI,
  getAgentListAPI,
  searchAgentAPI,
} from "../../../apis/history"
import { CardListType } from "../../../type"
import { useHistoryChatStore } from "../../../store/history_chat_msg"
import { useHistoryListStore } from "../../../store/history_list/index"
import { useRouter } from "vue-router"

const router = useRouter()
const historyListStore = useHistoryListStore()
const historyChatStore = useHistoryChatStore()
const searchInput = ref("")
const CardList = ref<CardListType[]>([
  {
    id: "",
    name: "",
    description: "",
    logo: "",
    code: "",
    createTime: "",
    isCustom: false,
    parameter: "",
    type: "",
  },
])

onMounted(async () => {
  const list = await getAgentListAPI()
  CardList.value = list.data.data
})

const gochat = async (item: CardListType) => {
  historyChatStore.name = item.name
  historyChatStore.logo = item.logo
  const list = await createDialogAPI({ agent: (item as CardListType).name })
  historyChatStore.dialogId = list.data.data.dialogId
  historyChatStore.clear()
  historyListStore.getList()
  router.push("/conversation/chatPage")
}

const searchAgent = async () => {
  if (searchInput.value) {
    const formData = new FormData()
    formData.append("name", searchInput.value)
    const list = await searchAgentAPI(formData)
    CardList.value = list.data.data
  } else {
    const list = await getAgentListAPI()
    CardList.value = list.data.data
  }
}
</script>

<template>
  <div class="default-page">
    <div class="title">
      <div class="title-img">
        <img
          src="../../../assets/robot.svg"
          style="width: 80px; height: 80px"
        />
      </div>
      <div class="title-text"><span style="color: blue">智言</span>平台</div>
    </div>
    <div class="search">
      <div class="mt-4">
        <el-input
          v-model="searchInput"
          style="max-width: 600px"
          placeholder="请搜索功能"
          class="input-with-select"
          @keydown.enter="searchAgent"
        >
          <template #prepend>
            <el-button :icon="Search" @click="searchAgent" />
          </template>
        </el-input>
      </div>
    </div>
    <el-scrollbar>
      <div
        class="item-card"
        v-if="Array.isArray(CardList) && CardList.length > 0"
      >
        <div v-for="item in CardList">
          <CommonCard
            class="card"
            :key="item.id"
            :title="item.name"
            :detail="item.description"
            :imgUrl="item.logo"
            @click="gochat(item)"
          ></CommonCard>
        </div>
      </div>
      <div v-else>
        <div class="item-img">
          <img src="../../../assets/404.gif" width="600px" />
        </div>
      </div>
    </el-scrollbar>
  </div>
</template>

<style lang="scss" scoped>
.default-page {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  .title {
    display: flex;
    margin: 10px auto;
    font-size: 35px;
    font-weight: 600;
    align-items: center;
    font-family: "Microsoft YaHei";
    justify-content: center;
    .title-img {
      margin-right: 20px;
    }
  }

  .search {
    display: flex;
    margin: 0px auto;
  }
  .item-card {
    width: 80%;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 33% 33% 33%;
    margin-top: 10px;
    .card:hover {
      background-color: #ecebeb;
    }
  }
  .item-img {
    margin: 0 auto;
    width: 600px;
  }

  :deep(.el-input__wrapper) {
    width: 685px;
    height: 40px;
  }
}
</style>
