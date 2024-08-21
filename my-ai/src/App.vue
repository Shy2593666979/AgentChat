<script setup lang="ts">
import { ref } from 'vue';
import card from './components/card/card.vue';
const input = ref('')
</script>

<template>
  <div class="ai-dialog-body">
    <div class="ai-dialog-nav">
      <div class="user">
        <div class="user-content">
          <div class="user-img">
            <img src="../src/assets/user.svg" alt="" style="width: 30px;height: 30px;">
          </div>
          <div class="user-name">666</div>
        </div>
      </div>
    </div>
    <div class="ai-dialog-main">
      <div class="aside">
        <el-scrollbar>
          <div class="create">
            <div class="img">
              <img src="../src/assets/create_dialog.svg" alt="" width="30px" height="30px">
            </div>
            <div clasrews="text">新建会话</div>
          </div>
          <card></card>
        </el-scrollbar>
      </div>
      <div class="text">
        <el-input v-model="input" placeholder="请输入">
          <template #append>
            <el-button ></el-button>
          </template>
        </el-input>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.ai-dialog-body {
  .ai-dialog-nav {
    display: flex;
    justify-content: end;
    height: 50px;
    background-color: #f4f5f8;

    .user {
      display: flex;
      align-items: center;
      margin-right: 30px;

      .user-content {
        display: flex;
        align-items: center;

        .user-img {
          margin-right: 10px;
        }
      }
    }
  }

  .ai-dialog-main {
    display: flex;
    height: calc(100vh - 50px);

    .aside {
      width: 15%;
      height: 100%;
      border-right: 2px solid #f0f3f5;
      padding: 10px;

      .create {
        display: flex;
        height: 50px;
        justify-content: center;
        align-items: center;

        .img {
          margin-right: 20px;
        }

        .text {
          font-weight: 500;
          margin-bottom: 8px;
        }
      }
    }
  }
}

:deep(.el-input__wrapper) {
  width: 685px;
  height: 60px;
}
</style>
