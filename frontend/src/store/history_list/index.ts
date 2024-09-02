import { defineStore } from 'pinia';
import { ref } from 'vue'
import { HistoryListType } from "../../type"
import { getDialogListAPI} from '../../apis/history';
import moment from 'moment';

export const useHistoryListStore = defineStore('history_list', () => {
  const historyList = ref<HistoryListType[]>([])
  async function getList() {
    const list = await getDialogListAPI()
    historyList.value = list.data.data
    historyList.value.map((item) => {
      {
        item.createTime = moment(item.createTime).format("YYYY-MM-DD HH:mm")
      }
    })
  }
  return { historyList, getList }
},
  {
    persist: true
  }
)
