<script setup lang="ts">
import { ref, onMounted, nextTick, watch, watchEffect } from "vue"
import { MdPreview } from "md-editor-v3"
import "md-editor-v3/lib/style.css"
import { sendMessage } from "../../../apis/chat"
import { useHistoryChatStore } from "../../../store//history_chat_msg"
import { ElScrollbar } from "element-plus"

const searchInput = ref("")
const id = "preview-only"
const sendQuestion = ref(true)
const historyChatStore = useHistoryChatStore()
const scrollbar = ref<InstanceType<typeof ElScrollbar>>()

function scrollBottom() {
  // 在下次DOM更新循环结束后执行滚动到底部的操作
  nextTick(() => {
    // 确保scrollbar对象存在
    if (scrollbar.value) {
      const wrapEl = scrollbar.value.wrapRef // 获取滚动容器元素
      ;(wrapEl as HTMLDivElement).scrollTop =(wrapEl as HTMLDivElement).scrollHeight // 直接设置scrollTop滚动到底部
    }
  })
}

const personQuestion = () => {
  if (searchInput.value && sendQuestion) {
    sendQuestion.value = false
    historyChatStore.chatArr.push({
      personMessage: { content: searchInput.value },
      aiMessage: { content: "" },
    })
    scrollBottom()
    const data = ref({
      dialogId: historyChatStore.dialogId,
      userInput: searchInput.value,
    })

    sendMessage(
      data.value,
      (onmessage = (msg: any) => {
        historyChatStore.chatArr[
          historyChatStore.chatArr.length - 1
        ].aiMessage.content += JSON.parse(msg.data).content
        scrollBottom()
      }),
      (onclose = () => {
        sendQuestion.value = true
      })
    )
    scrollBottom()
    searchInput.value = ""
  }
}
onMounted(async () => {
  scrollBottom()
  watch(
    historyChatStore.chatArr,
    () => {
      scrollBottom()
    },
    { deep: true }
  )
})
watchEffect(() => {
  if (historyChatStore.chatArr.length >= 0) {
    scrollBottom()
  }
})


</script>

<template>
  <div class="chat">
    <div class="chat-title">
      {{ historyChatStore.name }}
    </div>

    <div class="chat-conversation">
      <el-scrollbar ref="scrollbar">
        <div v-for="item in historyChatStore.chatArr">
          <div v-if="item.personMessage.content" class="person">
            <div class="content">
              <MdPreview
                :editorId="id"
                :modelValue="item.personMessage.content"
              />
            </div>
            <div class="img">
              <img src="../../../assets/user.svg" width="30px" height="30px" />
            </div>
          </div>
          <div v-if="item.aiMessage.content !== undefined" class="ai">
            <div class="img">
              <img :src="historyChatStore.logo" width="30px" height="30px" />
            </div>
            <div v-if="!item.aiMessage.content">
              <img src="../../../assets/loading.gif" width="30px" />
            </div>
            <div class="content">
              <MdPreview :editorId="id" :modelValue="item.aiMessage.content" />
            </div>
          </div>
        </div>
      </el-scrollbar>
    </div>
    <div class="search">
      <div class="mt-4">
        <el-input
          v-model="searchInput"
          placeholder="请输入想要搜索的问题"
          @keydown.enter="personQuestion"
          v-if="sendQuestion"
        >
          <template #append>
            <div @click="personQuestion" class="send">
              <img src="../../../assets//send.svg" width="30px" height="30px" />
            </div>
          </template>
        </el-input>
        <el-input
          v-model="searchInput"
          placeholder="正在输出请稍等..."
          v-else
          disabled
        >
          <template #append>
            <div @click="personQuestion" class="send">
              <img src="../../../assets//send.svg" width="30px" height="30px" />
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
      padding: 0 10px;
    }
  }

  .search {
    margin: 15px auto;
    width: 600px;
    .send {
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
