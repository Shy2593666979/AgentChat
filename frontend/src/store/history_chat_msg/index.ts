import { defineStore } from 'pinia';
import {   ref } from 'vue'
import { ChatMessage } from '../../type';
import { getHistoryMsgAPI } from '../../apis/history';

export const useHistoryChatStore = defineStore('history_chat_msg', () => {
  const chatArr = ref<ChatMessage[]>([])
  const dialogId = ref('')
  const name = ref('')
  const logo = ref('')
  function HistoryChat(id: string){
    chatArr.value = []
    async function getList(id: string) {
      const list = await getHistoryMsgAPI(JSON.parse(JSON.stringify(id as string)))
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
          chatArr.value.push(chatMsg.value)
        }
    }
    getList(id)
  }
  function clear() {
    chatArr.value = []
  }
  return { chatArr, HistoryChat ,clear,dialogId,name,logo}

},
  {
    persist: true
  }
)


