<script lang="ts" setup>
import {onMounted } from "vue"
import { HistoryListType } from "../../type"

const emits = defineEmits<{
    (event:'delete'):void
}>();

const props = defineProps<{
    item:HistoryListType
}>();


onMounted(()=>{

  
})

const deletCard = () =>{
    emits('delete')
}
</script>

<template>
  <div class="historyCard">
    <div class="top">
      <img :src=props.item.logo  alt="" width="25px" height="25px" />
      <div>{{ props.item.name }}</div>
    </div>

    <div class="bottom">
      <div>{{ props.item.createTime }}</div>
      <div class="delete" @click.stop="deletCard">
        <img src='../../assets/delete.svg' width="25px">
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.historyCard {
  background-color: #f7f7f9;
  border-radius: 4px;
  padding: 10px;
  .top {
    display: flex;
    font-size: 15px;
    align-items: center;
    font-weight: 600;
    margin-bottom: 15px;
    img {
      margin-right: 10px;
    }
    div {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
  .middle {
    font-size: 14px;
    font-weight: 500;
  }
  .bottom {
    margin-top: 15px;
    font-size: 13px;
    font-weight: 300;
    height: 25px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    .delete{
      display: none;
    }
  }
}
.historyCard:hover{
  background-color: white;
  .delete{
    display: flex;
  }
}
</style>
