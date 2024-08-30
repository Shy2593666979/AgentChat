import { onMounted } from 'vue';
<script lang="ts" setup>
import { onMounted} from 'vue';
const props = defineProps<{
  title: string
  detail: string
  type?: string
  imgUrl: string
}>()
onMounted(()=>{

   
})
</script>

<template>
  <div class="historyCard">
    <div class="content">
      <div class="top">
        <img :src="props.imgUrl" alt="" width="40px" height="40px" />
        <span>{{ props.title }}</span>
      </div>
      <div class="middle">
        {{ props.detail }}
      </div>
    </div>

  </div>
</template>

<style lang="scss" scoped>
.historyCard {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 150px;
  background-color: #f9f9fc;
  border-radius: 10px;
  padding: 5px 10px;
  margin-right: 15px;
  margin-top: 15px;
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
      font-size: 16px;
      font-weight: 500;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  .bottom {
    display: flex;
    justify-content: end;
    font-size: 13px;
    font-weight: 300;
    color: #f9f9fc;

    .agent {
      padding: 10px;
      background-color: #024de3;
      border-radius: 0 0 10px 0;
    }

    .skill {
      padding: 10px;
      background-color: black;
      border-radius: 0 0 10px 0;
    }
  }
}
</style>
