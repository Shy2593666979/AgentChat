<script setup lang="ts">
import { ref } from 'vue';
import card from '../../components/card/index';
const input = ref('')
</script>

<template>
    <div class="ai-dialog-main">
        <div class="aside">
            <el-scrollbar>
                <div class="create">
                    <div class="img">
                        <img src="../../assets/create_dialog.svg" alt="" width="30px" height="30px">
                    </div>
                    <div clasrews="text">新建会话</div>
                </div>
                <card></card>
            </el-scrollbar>
        </div>
        <div class="text">
            <el-input v-model="input" placeholder="请输入">
                <template #append>
                    <el-button></el-button>
                </template>
            </el-input>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.ai-dialog-main {
    .aside {
        width: 14%;
        height: 100%;
        border-right: 2px solid #f0f3f5;
        padding: 10px 10px 10px 0px;

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

:deep(.el-input__wrapper) {
    width: 685px;
    height: 60px;
}
</style>