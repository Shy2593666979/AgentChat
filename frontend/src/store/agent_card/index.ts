import { defineStore } from 'pinia';
import { ref } from 'vue'

export const useAgentCardStore = defineStore('agent_card', () => {
  const currentId = ref('')
  const clear = ()=>{
    currentId.value = ''
  }
  return { currentId,clear}
},
  {
    persist: true
  }
)
