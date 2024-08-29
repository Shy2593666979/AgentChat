<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter()
const userName = ref('666')
const itemName = ref('智言平台')

const godefault = ()=>{
  router.push('/')
}

</script>

<template>

  <div class="ai-body">
    <div class="ai-nav">
      <div class="left" @click="godefault">
        <div class="item-img">
          <img src="../../public/ai.svg" alt="" style="width: 30px;height: 30px;">
        </div>
        <div class="item-name" >{{ itemName }}</div>
      </div>
      <div class="right">
        <div class="user-img">
          <img src="../assets/user.svg" alt="" style="width: 30px;height: 30px;">
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
                <img src="../assets/dialog.svg" width="20px" height="20px">
              </el-icon>
              <span>会话</span>
            </span>
          </template>
          <router-view></router-view>
        </el-tab-pane>
        <el-tab-pane>
          <template #label>
            <span class="custom-tabs-label">
              <el-icon>
                <img src="../assets/robot.svg" width="20px" height="20px">
              </el-icon>
              <span>构建</span>
            </span>
          </template>
          构建
        </el-tab-pane>
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
    :deep(.el-tabs){
      border: none;
      width: 100%;
    }
     :deep(.el-tabs__header){
      border: none;
      width: 150px;
     }
     :deep(.el-tabs__nav-wrap){
      width: 100%;
     }
     :deep(.el-tabs__nav){
      width:100%;
     }
     :deep(.el-tabs__item){
      width:100%;
      height: 50px;
      justify-content: start;
     }
     :deep(.is-active){
      border: none;
      border-radius: 4px;
     }
     :deep(.el-icon){
      margin: 0 15px 0 8px ;
     }
     :deep(.el-tabs__content){
      padding: 0px;
     }
  }
}
</style>
