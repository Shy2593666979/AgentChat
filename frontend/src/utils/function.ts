import { nextTick, ref } from "vue"
import { ElScrollbar } from "element-plus"
import { ChatMessage } from "../type"

const scrollbar = ref<InstanceType<typeof ElScrollbar>>()

export function getHistoryChat(list: any, chatArr: ChatMessage[]) {
  for (let i = 0; i < list.data.data.length; i += 2) {
    const chatMsg = ref<ChatMessage>({
      personMessage: { content: '' },
      aiMessage: { content: '' }
    })
    if (list.data.data[i].role === 'user') {
      chatMsg.value.personMessage.content = list.data.data[i].content
    }
    if (list.data.data[i + 1].role === 'user') {
      chatMsg.value.personMessage.content = list.data.data[i + 1].content
    }
    if (list.data.data[i].role === 'assistant') {
      chatMsg.value.aiMessage.content = list.data.data[i].content
    }
    if (list.data.data[i + 1].role === 'assistant') {
      chatMsg.value.aiMessage.content = list.data.data[i + 1].content
    }
    chatArr.push(chatMsg.value)
    scrollBottom()
  }
}

export function scrollBottom() {
  // 在下次DOM更新循环结束后执行滚动到底部的操作
  nextTick(() => {
    // 确保scrollbar对象存在
    if (scrollbar.value) {
      const wrapEl = scrollbar.value.wrapRef // 获取滚动容器元素
        ; (wrapEl as HTMLDivElement).scrollTop = (
          wrapEl as HTMLDivElement
        ).scrollHeight // 直接设置scrollTop滚动到底部
    }
  })
}
