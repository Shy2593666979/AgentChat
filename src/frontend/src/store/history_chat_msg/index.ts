import { defineStore } from 'pinia';
import { ref } from 'vue'
import { ChatMessage } from '../../type';
import { getHistoryMsgAPI } from '../../apis/history';
import { ElMessage } from 'element-plus';

export const useHistoryChatStore = defineStore('history_chat_msg', () => {
  const chatArr = ref<ChatMessage[]>([])
  const dialogId = ref('')
  const name = ref('')
  const logo = ref('')
  const loading = ref(false)
  const error = ref('')

  /**
   * 获取历史聊天记录
   * @param id 对话ID
   */
  async function HistoryChat(id: string) {
    console.log('【HistoryChat】开始获取历史消息，dialog_id:', id)
    chatArr.value = [] // 清空现有消息
    loading.value = true
    error.value = ''
    
    try {
      const response = await getHistoryMsgAPI(id)
      console.log('【HistoryChat】历史消息API返回:', response.data)
      
      if (response.data.status_code === 200 && Array.isArray(response.data.data)) {
        const messages = response.data.data
        
        // 设置会话信息
        if (messages.length > 0 && messages[0].dialog_name) {
          name.value = messages[0].dialog_name || '新对话'
          logo.value = messages[0].logo_url || 'https://via.placeholder.com/40x40/3b82f6/ffffff?text=AI'
        }
        
        // 处理消息对
        for (let i = 0; i < messages.length; i += 2) {
          if (i + 1 >= messages.length) {
            // 如果只剩最后一条消息，单独处理
            const lastMsg = messages[i]
            const chatMsg: ChatMessage = {
              personMessage: { content: '' },
              aiMessage: { content: '' }
            }
            
            if (lastMsg.role === 'user') {
              chatMsg.personMessage.content = lastMsg.content
            } else if (lastMsg.role === 'assistant') {
              chatMsg.aiMessage.content = lastMsg.content
            }
            
            chatArr.value.push(chatMsg)
            continue
          }
          
          // 正常处理一对消息
          const userMsg = messages[i].role === 'user' ? messages[i] : messages[i+1]
          const aiMsg = messages[i].role === 'assistant' ? messages[i] : messages[i+1]
          
          const chatMsg: ChatMessage = {
            personMessage: { content: userMsg.role === 'user' ? userMsg.content : '' },
            aiMessage: { content: aiMsg.role === 'assistant' ? aiMsg.content : '' }
          }
          
          chatArr.value.push(chatMsg)
        }
        
        console.log('【HistoryChat】处理后的消息数组:', chatArr.value)
      } else {
        console.error('【HistoryChat】API返回错误:', response.data)
        error.value = '获取历史消息失败'
        ElMessage.error('获取历史消息失败')
      }
    } catch (err) {
      console.error('【HistoryChat】获取历史消息出错:', err)
      error.value = '获取历史消息出错'
      ElMessage.error('获取历史消息出错，请重试')
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 清空聊天记录
   */
  function clear() {
    chatArr.value = []
    error.value = ''
  }
  
  return { 
    chatArr, 
    HistoryChat,
    clear,
    dialogId,
    name,
    logo,
    loading,
    error
  }
},
{
  persist: true
})


