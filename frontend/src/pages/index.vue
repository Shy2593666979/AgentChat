<script setup lang="ts">
import { onMounted, ref, watch } from "vue"
import { useRouter } from "vue-router"
import { useRoute } from "vue-router"
import { useAgentCardStore } from "../store/agent_card"
import { getAgentListAPI } from "../apis/history"
import { CardListType } from "../type"

const agentCardStore = useAgentCardStore()
const route = useRoute()
const router = useRouter()
const itemName = ref("智言平台")
const current = ref(route.meta.current)
const cardList = ref<CardListType[]>([])
const godefault = () => {
  agentCardStore.clear()
  router.push("/")
}
  
const updateList = async () => {
  const list = await getAgentListAPI()
  cardList.value = list.data.data
}

onMounted(async () => {
  updateList()
})

const goCurrent = (item: string) => {
  if (item === "conversation") {
    router.push("/")
  } else if (item === "construct") {
    router.push("/construct")
  } else {
    router.push("/configuration")
  }
}

watch(
  route,
  (val) => {
    current.value = route.meta.current
  },
  {
    immediate: true,
  }
)
</script>

<template>
  <div class="ai-body">
    <div class="ai-nav">
      <div class="left" @click="godefault">
        <div class="item-img">
          <img
            src="../../public/ai.svg"
            alt=""
            style="width: 30px; height: 30px"
          />
        </div>
        <div class="item-name">{{ itemName }}</div>
      </div>
      <div class="right">
        <div class="user-img">
          <img
            src="../assets/user.svg"
            alt=""
            style="width: 30px; height: 30px"
          />
        </div>
      </div>
    </div>
    <div class="ai-main">
      <el-col :span="2">
        <el-menu
          active-text-color="#6b9eff"
          background-color="#f4f5f8"
          class="el-menu-vertical-demo"
          :default-active="current"
          text-color="#909399"
        >
          <el-menu-item index="conversation" @click="goCurrent('conversation')">
            <template #title>
              <el-icon>
                <img src="../assets/dialog.svg" width="22px" height="22px" />
              </el-icon>
              <span>会话</span>
            </template>
          </el-menu-item>
          <el-menu-item index="construct" @click="goCurrent('construct')">
            <template #title>
              <el-icon>
                <img src="../assets/robot.svg" width="22px" height="22px" />
              </el-icon>
              <span>构建</span>
            </template>
          </el-menu-item>
          <el-menu-item
            index="configuration"
            @click="goCurrent('configuration')"
          >
            <template #title>
              <el-icon>
                <img src="../assets/set.svg" width="22px" height="22px" />
              </el-icon>
              <span>配置</span>
            </template>
          </el-menu-item>
        </el-menu>
        <div class="custom-tabs-label">
          <div class="absolute right-16 bottom-16 flex">
            <div class="help flex">
              <a
                href="https://github.com/Shy2593666979/AgentChat"
                target="_blank"
              >
                <img
                  src="../assets/github.png"
                  class="block h-40 w-40 border p-10 rounded-8 mx-8 hover:bg-gray-800 hover:text-white hover:cursor-pointer"
                  style="width: 35px; height: 35px; margin-right: 20px"
                  alt="GitHub Icon"
                />
              </a>
              <a
                href="https://uawlh9wstr9.feishu.cn/docx/U3l4dvtC6oPrVwx61zIcrmD0nvf"
                target="_blank"
              >
                <img
                  src="../assets/help.png"
                  class="block h-40 w-40 border p-10 rounded-8 hover:bg-blue-600 hover:text-white hover:cursor-pointer"
                  alt="Book Open Icon"
                  style="width: 35px; height: 35px"
                />
              </a>
            </div>
          </div>
        </div>
      </el-col>
      <div class="content">
        <router-view></router-view>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.ai-body {
  overflow: hidden;
  .ai-nav {
    display: flex;
    justify-content: space-between;
    height: 60px;
    background-color: #f4f5f8;
    padding: 0 20px;
    .left {
      display: flex;
      align-items: center;
      font-weight: 600;
      cursor: pointer;
      .item-img {
        margin-top: 5px;
        margin-right: 10px;
      }
    }

    .right {
      display: flex;
      align-items: center;
      .user-img {
        margin-right: 10px;
      }
    }
  }
  .ai-main {
    display: flex;
    height: calc(100vh - 60px);
    background-color: #f5f7fa;
    .custom-tabs-label {
      margin: 20px auto;
    }
    .content {
      background-color: #fff;
      width: calc(100vw - 120px);
    }
    :deep(.el-col-2) {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      max-width: 120px;
    }
    :deep(.el-menu) {
      border: none;
    }
    :deep(.el-menu-item) {
      font-size: 16px;
    }
    :deep(.el-menu):hover {
      background-color: #fff;
    }
    :deep(.is-active) {
      background-color: #fff;
    }
  }
}
</style>
