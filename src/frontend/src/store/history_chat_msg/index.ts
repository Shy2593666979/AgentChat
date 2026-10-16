import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { ChatMessage } from '../../type';
import { getHistoryMsgAPI } from '../../apis/history';
import { normalizeHistory } from '../../utils/chat-ui';
import { responseError } from '../../utils/resource-visuals';
export const useHistoryChatStore = defineStore('history_chat_msg', () => {
    const chatArr = ref<ChatMessage[]>([]), conversationId = ref(''), name = ref(''), logo = ref(''), loading = ref(false), error = ref('');
    let requestId = 0;
    async function HistoryChat(id: string) { const request = ++requestId; conversationId.value = id; chatArr.value = []; loading.value = true; error.value = ''; try {
        const response = await getHistoryMsgAPI(id);
        if (request !== requestId || conversationId.value !== id)
            return false;
        if (response.data.status_code !== 200 || !Array.isArray(response.data.data))
            throw new Error(response.data.status_message || '历史消息加载失败');
        chatArr.value = normalizeHistory(response.data.data);
        return true;
    }
    catch (err) {
        if (request === requestId)
            error.value = responseError(err, '历史消息加载失败，请重试');
        return false;
    }
    finally {
        if (request === requestId)
            loading.value = false;
    } }
    function clear() { requestId++; chatArr.value = []; error.value = ''; loading.value = false; }
    return { chatArr, conversationId, name, logo, loading, error, HistoryChat, clear };
}, { persist: true });
