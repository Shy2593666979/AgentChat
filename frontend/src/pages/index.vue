<script setup lang="ts">
import { onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import { useAgentCardStore } from "../store/agent_card"
import AgentCard from "../components/agentCard/index"
import { getAgentListAPI } from "../apis/history"
import { CardListType } from "../type"
import CreateAgent from "../components/dialog/create_agent/index"

const agentCardStore = useAgentCardStore()
const router = useRouter()
const userName = ref("666")
const itemName = ref("智言平台")
const cardList = ref<CardListType[]>([])
const createAgentRef = ref()

const godefault = () => {
  agentCardStore.clear()
  router.push("/")
}

const openDialog = (event:string,item?:CardListType) => {
  if(event === 'create'){
    createAgentRef.value.open(event)
  }else{
    createAgentRef.value.open(event,item)
  }
}

const updateList = async()=>{
  const list = await getAgentListAPI()
  cardList.value = list.data.data
}

onMounted(async () => {
  updateList()
})
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
        <div class="user-name">{{ userName }}</div>
      </div>
    </div>
    <div class="ai-main">
      <el-tabs type="border-card" class="demo-tabs" tab-position="left">
        <el-tab-pane>
          <template #label>
            <span class="custom-tabs-label">
              <el-icon>
                <img src="../assets/dialog.svg" width="20px" height="20px" />
              </el-icon>
              <span>会话</span>
            </span>
          </template>
          <router-view></router-view>
        </el-tab-pane>
        <el-scrollbar>
          <el-tab-pane>
            <template #label>
              <span class="custom-tabs-label">
                <el-icon>
                  <img src="../assets/robot.svg" width="20px" height="20px" />
                </el-icon>
                <span>构建</span>
              </span>
            </template>
            <div class="agent-card">
              <div class="create" @click="openDialog('create')">
                <div class="content">
                  <div class="top">
                    <img
                      src="../assets/add.svg"
                      alt=""
                      width="40px"
                      height="40px"
                    />
                    <span>新建助手</span>
                  </div>
                  <div class="middle">
                    通过描述角色和任务来创建你的助手<br />
                    助手可以调用多个技能和工具
                  </div>
                </div>
              </div>
              <div v-for="item in cardList">
                <AgentCard :key="item.id" :item="item" @delete="updateList" @click="openDialog('update',item)"></AgentCard>
              </div>
            </div>
          </el-tab-pane>
        </el-scrollbar>
        <CreateAgent ref="createAgentRef" @update="updateList"></CreateAgent>
      </el-tabs>

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
    .agent-card {
      padding: 20px;
      display: grid;
      grid-template-columns: 20% 20% 20% 20% 20%;
      .create {
        margin-top: 10px;
        margin-right: 10px;
        padding: 10px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 150px;
        background-color: #f9f9fc;
        border-radius: 10px;

        .content {
          margin: 5px 0px 0px 10px;

          .top {
            display: flex;
            font-size: 18px;
            align-items: center;
            font-weight: 600;
            margin-bottom: 15px;
            img {
              margin-right: 10px;
            }
          }

          .middle {
            font-size: 14px;
            font-weight: 300;
          }
        }
      }
      .create:hover {
        background-color: #f4f2f2;
        cursor: pointer;
      }
    }
    :deep(.el-tabs) {
      border: none;
      width: 100%;
    }
    :deep(.el-tabs__header) {
      border: none;
      width: 150px;
    }
    :deep(.el-tabs__nav-wrap) {
      width: 100%;
    }
    :deep(.el-tabs__nav) {
      width: 100%;
    }
    :deep(.el-tabs__item) {
      width: 100%;
      height: 50px;
      justify-content: start;
    }
    :deep(.is-active) {
      border: none;
      border-radius: 4px;
    }
    :deep(.el-icon) {
      margin: 0 15px 0 8px;
    }
    :deep(.el-tabs__content) {
      padding: 0px;
    }
  }
}
</style>
