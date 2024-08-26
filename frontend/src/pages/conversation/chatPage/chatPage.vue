<script setup lang="ts">
import { nextTick, ref, onMounted } from 'vue';
import { ElScrollbar } from 'element-plus';
import { MdPreview } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';
import { CardListType } from '../../../type'
import { sendMessage } from '../../../apis/chat'

const props = defineProps<{
    item : CardListType
}>();

const scrollbar = ref<InstanceType<typeof ElScrollbar>>();
const searchInput = ref('')
const id = 'preview-only';


const chatArr = ref([
    {
        type: 'person',
        content: '你好，大模型！'
    },
    {
        type: 'ai',
        content: '你好,如果问题仍然存在，你可能需要检查 Element Plus 的文档或源码，以了解 <el-scrollbar> 组件的具体实现和可能存在的限制。同时，也可以检查控制台是否有任何错误或警告，这可能会提供更多关于问题的线索。'
    },
    {
        type: 'person',
        content: '你好，大模型！'
    },
    {
        type: 'ai',
        content: '你好'
    },
])

const personQuestion = () => {
    if (searchInput.value) {
        chatArr.value.push({
            type: 'person',
            content: searchInput.value
        })
        // 在下次DOM更新循环结束后执行滚动到底部的操作
        nextTick(() => {
            // 确保scrollbar对象存在
            if (scrollbar.value) {
                const wrapEl = scrollbar.value.wrapRef; // 获取滚动容器元素
                (wrapEl as HTMLDivElement).scrollTop = (wrapEl as HTMLDivElement).scrollHeight; // 直接设置scrollTop滚动到底部
            }
        })
        searchInput.value = ''
    }
}

onMounted(async()=>{
  const data = {
    dialogId: props.item.id,
    agent:props.item.name,
    userInput:'你好',
  }
  await sendMessage(data)
})
</script>

<template>
    <div class="chat">
        <div class="chat-title">{{ props.item.name }}</div>

        <div class="chat-conversation">
            <el-scrollbar ref="scrollbar">
                <div v-for="item in chatArr">
                    <div v-if="item.type === 'person'" class="person">
                        <div class="content">
                            <MdPreview :editorId="id" :modelValue=item.content />
                        </div>
                        <div class="img">
                            <img src="../../../assets/user.svg" width="30px" height="30px">
                        </div>
                    </div>
                    <div v-else class="ai">
                        <div class="img">
                            <img src="../../../../public/ai.svg" width="30px" height="30px">
                        </div>
                        <div class="content">
                            <MdPreview :editorId="id" :modelValue=item.content />
                        </div>
                    </div>
                </div>
            </el-scrollbar>
        </div>
        <div class="search">
            <div class="mt-4">
                <el-input v-model="searchInput" placeholder="请输入想要搜索的问题">
                    <template #append>
                        <div @click="personQuestion" class="send">
                            <img src="../../../assets//send.svg" width="30px" height="30px">
                        </div>
                    </template>
                </el-input>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.chat {
    padding: 20px;
    height: 100%;

    .chat-title {
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 10px;
    }

    .chat-conversation {
        height: 75%;
        width: 100%;
        font-size: 16px;
       
        .person {
            display: flex;
            justify-content: end;
            align-items: center;
            margin-bottom: 10px;
            .content {
                margin-right: 5px;
                background-color: pink;
                border-radius: 15px 15px 0 15px;
                max-width: 50%;
            }
        }

        .ai {
            display: flex;
            justify-content: first;
            align-items: center;
            margin-bottom: 10px;
            .img {
                margin-right: 5px;
            }

            .content {
                max-width: 50%;
                background-color: #f4f5f8;
                border-radius: 15px 15px 15px 0;
            }
        }

        .content {
            padding: 0 10px ;
        }
    }

    .search {
        margin: 15px auto;
        width: 600px;
        .send{
            display: flex;
            align-items: center;
        }
    }

    :deep(.el-input__wrapper) {
        width: 685px;
        height: 40px;
    }
}
</style>
