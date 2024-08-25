<script lang="ts" setup>
import { ref } from 'vue';

const title = ref('预置_宏观研究员助手')
const detail = ref('你好！请问有什么可以帮您的吗')
const time = ref('20:45')
</script>

<template>
<div class="historyCard">
   <div class="top">
    <img src="../../../public/ai.svg" alt="" width="25px" height="25px">
    <span>{{ title }}</span>
   </div>
   <div class="middle">
    {{detail}}
   </div>
   <div class="bottom">
      {{ time }}
   </div>
</div>

</template>

<style lang="scss" scoped>
.historyCard{
    background-color: #f9f9fc;
    border-radius: 4px;
    padding: 10px;
    .top{
        display: flex;
        font-size: 15px;
        align-items: center;
        font-weight: 600;
        margin-bottom: 15px;
        img{
            margin-right: 10px;
        }
    }
    .middle{
        font-size: 14px;
        font-family: 'Courier New', Courier, monospace;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space:nowrap;
        font-weight: 500;
    }
    .bottom{
        margin-top: 15px;
        font-size: 13px;
        font-weight: 300;
    }
}
</style>