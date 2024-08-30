<script setup lang="ts">
import { reactive, ref, onMounted } from "vue"
import CommonCard from "../../components/commonCard"
import { getAgentListAPI } from "../../apis/history"
import { CardListType } from '../../type'

const emits = defineEmits<{
  (event: "goChat", item: CardListType): void
}>()

const drawer = ref(false)
let cardList:CardListType[] = reactive([])
const currentId = ref()
const curentItem = ref<CardListType>()

onMounted(async () => {
  const list = await getAgentListAPI()
  cardList = list.data.data
  currentId.value = cardList[0].id
  curentItem.value = cardList[0]
})

const open = () => {
  drawer.value = true
}
const close = () => {
  drawer.value = false
}
const optionCard = (item: any) => {
  currentId.value = item.id
  curentItem.value = item
}
const cancel = () => {
  close()
}
const primary = () => {
  emits("goChat", curentItem.value as unknown as CardListType)
  close()
}

defineExpose({
  open,
  close,
})
</script>

<template>
  <div class="drawer">
    <el-drawer v-model="drawer" title="请选择一个应用" :with-header="true">
      <div class="card">
        <div
          v-for="item in cardList"
          :class="currentId === item.id ? 'active' : ''"
        >
          <CommonCard
            @click="optionCard(item)"
            :key="item.id"
            :title="item.name"
            :detail="item.description"
            :imgUrl="item.logo"
          ></CommonCard>
        </div>
      </div>
      <div class="button">
        <el-button @click="cancel">取消</el-button>
        <el-button type="primary" @click="primary">确定</el-button>
      </div>
    </el-drawer>
  </div>
</template>

<style lang="scss" scoped>
.drawer {
  .card {
    display: grid;
    grid-template-columns: 100%;
    gap: 10px;
  }
  .button {
    display: flex;
    margin-top: 15px;
    justify-content: center;
    :deep(.el-button) {
      padding: 20px 40px;
    }
  }
  .active {
    border: 1px solid blue;
    border-radius: 4px 4px 10px 4px;
  }
}
</style>
