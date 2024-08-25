<script setup lang="ts">
import HistortCard from '../../components/historyCard/index';
import Drawer from '../../components/drawer';
import { ref } from 'vue';
import DefaultPage from './defaultPage/defaultPage.vue';
import ChatPage from './chatPage/index'

const drawerRef = ref()
const defaultPage = ref(true)
const chatTitle = ref('')

const open =()=>{
    drawerRef.value.open()
}

const chat = (title:string)=>{
    defaultPage.value = false
    chatTitle.value = title
}

</script>

<template>
    <div class="ai-conversation-main">
        <div class="aside">
            <el-scrollbar>
                <div class="create">
                    <el-button @click="open">
                        <div class="img">
                            <img src="../../assets/create_dialog.svg" alt="" width="30px" height="30px">
                        </div>
                        <div clasrews="text">新建会话</div>
                    </el-button>
                </div>
                <HistortCard></HistortCard>
            </el-scrollbar>
        </div>
        <div class="content" v-if="defaultPage">
           <DefaultPage></DefaultPage>
        </div>
        <div class="content" v-else>
           <ChatPage :chatTitle="chatTitle"></ChatPage>
        </div>
        <Drawer ref="drawerRef" @goChat="chat"></Drawer>
    </div>
</template>

<style lang="scss" scoped>
.ai-conversation-main {
    display: flex;
    height: calc(100vh - 60px);

    .aside {
        width: 180px;
        height: 100%;
        border-right: 2px solid #f0f3f5;
        padding: 10px 10px 10px 0px;

        .create {
            display: flex;
            height: 50px;
            justify-content: center;
            align-items: center;
            :deep(.el-button){
                border:none
            }
            :deep(.el-button):hover{
               background-color: #fff;
            }
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
</style>