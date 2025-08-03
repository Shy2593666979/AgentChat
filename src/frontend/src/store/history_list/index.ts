import { defineStore } from 'pinia';
import { ref } from 'vue'
import { HistoryListType } from "../../type"
import { getDialogListAPI} from '../../apis/history';

export const useHistoryListStore = defineStore('history_list', () => {
  const historyList = ref<HistoryListType[]>([])
  
  async function getList() {
    try {
      const list = await getDialogListAPI()
      historyList.value = list.data.data || []
      
      // 使用原生JavaScript格式化时间
      historyList.value.forEach((item) => {
        if (item.createTime) {
          try {
            const date = new Date(item.createTime)
            item.createTime = date.toLocaleString('zh-CN', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
            })
          } catch (error) {
            console.error('时间格式化失败:', error)
            item.createTime = '未知时间'
          }
        }
      })
    } catch (error) {
      console.error('获取会话列表失败:', error)
      historyList.value = []
    }
  }
  
  return { historyList, getList }
},
  {
    persist: true
  }
)
