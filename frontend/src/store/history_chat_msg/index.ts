import { defineStore } from 'pinia';
import { ref } from 'vue'
import { ChatMessage } from '../../type';
import { getHistoryMsgAPI } from '../../apis/history';
import { getHistoryChat } from '../../utils/function'


export const useHistoryChatStore = defineStore('history_chat_msg', () => {
  const chatArr = ref<ChatMessage[]>([])
  const dialogId = ref('')
  const name = ref('')
  const logo = ref('')
  async function HistoryChat(id: string) {
    chatArr.value = []
    const list = await getHistoryMsgAPI(JSON.parse(JSON.stringify(id as string)))
    getHistoryChat(list, chatArr.value)
  }
  async function clear() {
    chatArr.value = []
  }
  return { chatArr, HistoryChat ,clear,dialogId,name,logo}

},
  {
    persist: true
  }
)


