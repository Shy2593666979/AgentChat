<script setup lang="ts">
import AgentCard from "../../components/agentCard/index"
import { onMounted, ref } from "vue"
import { CardListType } from "../../type"
import { getAgentListAPI } from "../../apis/history"
import  CreateAgent  from '../../components/dialog/create_agent/index'

const cardList = ref<CardListType[]>([])
const createAgentRef = ref()

const openDialog = (event: string, item?: CardListType) => {
  if (event === "create") {
    createAgentRef.value.open(event)
  } else {
    createAgentRef.value.open(event, item)
  }
}

const updateList = async () => {
  const list = await getAgentListAPI()
  cardList.value = list.data.data
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
          <img src="../../assets/add.svg" alt="" width="40px" height="40px" />
          <span>新建助手</span>
        </div>
        <div class="middle">
          通过描述角色和任务来创建你的助手<br />
          助手可以调用多个技能和工具
        </div>
      </div>
    </div>
    <div v-for="item in cardList">
      <AgentCard
        :key="item.id"
        :item="item"
        @delete="updateList"
        @click="openDialog('update', item)"
      ></AgentCard>
    </div>
    <CreateAgent ref="createAgentRef" @update="updateList"></CreateAgent>
  </div>
</template>

<style lang="scss" scoped>
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
</style>
