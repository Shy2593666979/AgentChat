<script setup lang="ts">
import { ref } from 'vue';
import HistortCard from '../../components/historyCard/index';
import CommonCard from '../../components/commonCard';


const searchInput = ref('')
import { Search } from '@element-plus/icons-vue'
</script>

<template>
    <div class="ai-conversation-main">
        <div class="aside">
            <el-scrollbar>
                <div class="create">
                    <div class="img">
                        <img src="../../assets/create_dialog.svg" alt="" width="30px" height="30px">
                    </div>
                    <div clasrews="text">新建会话</div>
                </div>
                <HistortCard></HistortCard>
            </el-scrollbar>
        </div>
        <div class="content">
            <div class="title">
                <div class="title-img">
                    <img src="../../assets/robot.svg" style="width: 80px;height: 80px;">
                </div>
                <div class="title-text">
                    <span style="color: blue;">智言</span>平台
                </div>
            </div>
            <div class="search">
                <div class="mt-4">
                    <el-input v-model="searchInput"  style="max-width: 600px" placeholder="请搜索功能" class="input-with-select">
                        <template #prepend>
                            <el-button :icon="Search" />
                        </template>
                    </el-input>
                </div>
            </div>
            <el-scrollbar>
             <div class="item-card" >
                <div v-for="item in 9">
                    <CommonCard></CommonCard>
                </div>
             </div>
           </el-scrollbar>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.ai-conversation-main {
    display: flex;
    height: calc(100vh - 60px);

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

    .content {
        display: flex;
        flex-direction: column;
        margin: 0 auto;
        width: 80%;
        .title {
            display: flex;
            margin: 10px auto;
            font-size: 35px;
            font-weight: 600;
            align-items: center;
            font-family: 'Times New Roman', Times, serif;

            .title-img {
                margin-right: 20px;
            }
        }
        .search{
            margin: 10px auto;
        }
        .item-card {
            display: grid;
            grid-template-columns: 33% 33% 33%;
            gap: 5px;
            box-sizing: border-box;
            margin-top: 10px;
        }
    }
}

:deep(.el-input__wrapper) {
    width: 685px;
    height: 40px;
}
</style>