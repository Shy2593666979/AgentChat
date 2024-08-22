<script lang="ts" setup>
import { ref } from 'vue';

const title = ref('预置_宏观研究员助手')
const detail = ref('你好！请问有什么可以帮您的吗')
const time = ref('20:45')
</script>

<template>
<div class="card">
   <div class="top">
    <img src="../../assets/AI.svg" alt="" width="40px" height="40px">
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
.card{
    background-color: #edeff6;
    height: 100px;
    border-radius: 4px;
    padding: 20px;
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