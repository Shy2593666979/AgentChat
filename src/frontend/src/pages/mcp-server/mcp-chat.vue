<script setup lang="ts">
import UserAvatar from "../../components/UserAvatar.vue";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';

import BrandLogo from '../../components/BrandLogo.vue';
import ProviderModelPicker from '../../components/ProviderModelPicker.vue';
import {getVisibleLLMsAPI,type LLMResponse} from '../../apis/llm';
import ChatActionIcon from '../../components/ChatActionIcon.vue';
import McpToolEvent from '../../components/McpToolEvent.vue';
import McpApprovalCard from '../../components/McpApprovalCard.vue';
import {latestMcpPending} from '../../utils/mcp-review';

import { MdPreview } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';
import UiIcon from '../../components/UiIcon.vue';
import SessionRail from '../../components/SessionRail.vue';
import { getTaskListAPI, createTaskAPI, deleteTaskAPI, type MCPTask, type MCPMessage, type MCPContent } from '../../apis/mcp-chat';
import { useUserStore } from '../../store/user';
import { postEventStream, isSendKey, copyChatText } from '../../utils/chat-ui';
import { fitComposer } from '../../utils/chat-ui';
import { safeResourceUrl } from '../../utils/data-pages';
import { responseError } from '../../utils/resource-visuals';


const models=ref<LLMResponse[]>([]),selectedModel=ref(''),modelsLoading=ref(false),modelError=ref('');
const pendingModelId=computed(()=>tasks.value.find(task=>task.id===currentId.value)?.messages?.at(-1)?.model_id||'');
const user = useUserStore(), tasks = ref<MCPTask[]>([]), currentId = ref(''), messages = ref<MCPMessage[]>([]), draft = ref(''), loading = ref(false), creating = ref(false), busy = ref(false), deleting = ref(false), loadError = ref(''), streamError = ref(''), sidebarOpen = ref(false), output = ref<HTMLElement>(), follow = ref(true), expanded = ref(new Set<string>()), rejectOpen = ref(false), feedback = ref(''), brokenAvatars = ref(new Set<string>());
const streamingQuery = ref(''), streamingContent = ref<MCPContent[]>([]), replaying = ref(false);
let controller: AbortController | undefined, operation = 0, listRequest = 0, disposed = false, frame = 0;
const displayMessages = computed(() => streamingQuery.value ? [...(replaying.value ? messages.value.slice(0, -1) : messages.value), { query: streamingQuery.value, content: streamingContent.value }] : messages.value);
const railRecords = computed(() => [...tasks.value].sort((a, b) => (Date.parse(b.updated_time || b.created_time) || 0) - (Date.parse(a.updated_time || a.created_time) || 0)).map(task => ({ id: task.id, title: task.messages?.[0]?.query?.slice(0, 35) || '新会话', preview: task.messages?.[task.messages.length - 1]?.query || '等待开始对话', time: task.updated_time || task.created_time })));
const pending = computed(() => latestMcpPending(displayMessages.value.at(-1)?.content || []));
function blocks(content: MCPContent[]) { const result: any[] = [], events = new Map<string, number>(); for (const item of content || []) {
    if (item.type === 'text') {
        const last = result.at(-1);
        if (last?.type === 'text')
            last.text += String(item.data || '');
        else
            result.push({ type: 'text', text: String(item.data || '') });
    }
    else if (item.type === 'event') {
        const event = item.data || {}, title = event.title || '工具调用', key = event.tool_call_id || title;
        if (events.has(key) && (event.status!=='START'||result[events.get(key)!].event.status==='START'))
            result[events.get(key)!].event = event;
        else {
            events.set(key, result.length);
            result.push({ type: 'event', event });
        }
    }
    else if (item.type === 'interrupt')
        result.push({ type: 'interrupt', data: item.data || {} });
} return result; }
function toggle(key: string) { const next = new Set(expanded.value); next.has(key) ? next.delete(key) : next.add(key); expanded.value = next; }
const validAvatar = (url: string) => !!safeResourceUrl(url) && !brokenAvatars.value.has(url);
const avatar = computed(() => user.userInfo?.avatar || '');
function scrollBottom(force = false) { if (force)
    follow.value = true; if (!follow.value)
    return; cancelAnimationFrame(frame); nextTick(() => { if (!disposed)
    frame = requestAnimationFrame(() => { if (output.value)
        output.value.scrollTop = output.value.scrollHeight; }); }); }
function onScroll() { if (output.value)
    follow.value = output.value.scrollHeight - output.value.scrollTop - output.value.clientHeight < 100; }
function commitStream() { if (streamingQuery.value) {
    const row = { query: streamingQuery.value, content: [...streamingContent.value], model_id: replaying.value?pendingModelId.value:selectedModel.value };
    if (replaying.value)
        messages.value = [...messages.value.slice(0, -1), row];
    else
        messages.value = [...messages.value, row];
} streamingQuery.value = ''; streamingContent.value = []; replaying.value = false; }
function stop() {  operation++; controller?.abort(); controller = undefined; for (const content of streamingContent.value)
    if (content.type === 'event' && content.data?.status === 'START')
        content.data.status = 'RECEIVE_STOPPED'; if (busy.value)
    commitStream(); busy.value = false; creating.value = false; streamError.value = '已停止接收，保留已收到的内容。'; rejectOpen.value = false; }
async function loadModels(){modelsLoading.value=true;modelError.value='';try{const response=await getVisibleLLMsAPI();if(response.data.status_code!==200)throw new Error(response.data.status_message||'模型加载失败');const data=response.data.data||{};if(disposed)return;models.value=(Array.isArray(data)?data:Object.values(data).flat()).filter(model=>model.llm_type==='LLM');if(!selectedModel.value&&(!pending.value))selectedModel.value=models.value[0]?.llm_id||'';}catch(error){if(!disposed)modelError.value=responseError(error,'模型加载失败');}finally{if(!disposed)modelsLoading.value=false;}}
function restoreModel(task?:MCPTask){const saved=[...(task?.messages||[])].reverse().find(message=>message.model_id)?.model_id;if(saved)selectedModel.value=saved;else if(latestMcpPending(task?.messages?.at(-1)?.content||[]))selectedModel.value='';else if(!selectedModel.value)selectedModel.value=models.value[0]?.llm_id||'';}
async function loadTasks() {  const id = ++listRequest; loading.value = true; loadError.value = ''; try {
    const response = await getTaskListAPI();
    if (disposed || id !== listRequest)
        return;
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '会话记录加载失败');
    tasks.value = response.data.data || [];
    return true;
}
catch (error) {
    if (!disposed && id === listRequest)
        loadError.value = responseError(error, '会话记录加载失败');
    return false;
}
finally {
    if (!disposed && id === listRequest)
        loading.value = false;
} }
async function createTask() {  if (creating.value)
    return; if (busy.value)
    stop(); creating.value = true; try {
    const response = await createTaskAPI();
    if (disposed)
        return;
    if (response.data.status_code !== 200 || !response.data.data?.id)
        throw new Error(response.data.status_message || '创建会话失败');
    currentId.value = response.data.data.id;
    messages.value = [];
    draft.value = '';
    streamError.value = '';
    expanded.value = new Set();
    sidebarOpen.value = false;
    await loadTasks();
}
catch (error) {
    if (!disposed)
        ElMessage.error(responseError(error, '创建会话失败'));
}
finally {
    creating.value = false;
} }
function selectTask(id: string) { if (creating.value)
    return; if (busy.value)
    stop(); const task = tasks.value.find(task => task.id === id); if (!task)
    return; restoreModel(task);currentId.value = id; messages.value = task.messages || []; draft.value = ''; streamError.value = ''; rejectOpen.value = false; feedback.value = ''; expanded.value = new Set(); scrollBottom(true); }
async function removeTask(id: string) { if (deleting.value || creating.value)
    return; try {
    await ElMessageBox.confirm('确定删除此 MCP 会话及其记录？', '删除会话', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' });
    if (id === currentId.value && busy.value)
        stop();
    deleting.value = true;
    const response = await deleteTaskAPI(id);
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '删除失败');
    if (id === currentId.value) {
        currentId.value = '';
        messages.value = [];
        draft.value = '';
        streamError.value = '';
    }
    await loadTasks();
    ElMessage.success('会话已删除');
}
catch (error) {
    if (error !== 'cancel' && error !== 'close')
        ElMessage.error(responseError(error, '删除会话失败'));
}
finally {
    deleting.value = false;
} }
async function run(decision?: 'approve' | 'reject') { if(decision&&(!pending.value||!pending.value.allowed_decisions?.includes(decision)))return;  if (busy.value || creating.value || (!decision && (!draft.value.trim() || pending.value)))
    return; if(!decision&&!selectedModel.value){streamError.value='请先选择对话模型';return;}busy.value = true; streamError.value = ''; const token = ++operation, query = draft.value.trim(), pendingAction = pending.value; controller = new AbortController(); try {
    if (!currentId.value) {
        creating.value = true;
        const response = await createTaskAPI();
        if (disposed || token !== operation)
            return;
        if (response.data.status_code !== 200 || !response.data.data?.id)
            throw new Error(response.data.status_message || '创建会话失败');
        currentId.value = response.data.data.id;
        creating.value = false;
    }
    const taskId = currentId.value;
    if (decision) {
        if (!pendingAction)
            throw new Error('未找到待确认操作');
        replaying.value = true;
        const last = messages.value.at(-1);
        streamingQuery.value = last?.query || '';
        streamingContent.value = [...(last?.content || [])];
        rejectOpen.value = false;
    }
    else {
        streamingQuery.value = query;
        streamingContent.value = [];
        replaying.value = false;
        draft.value = '';
    }
    scrollBottom(true);
    const path = decision ? `/api/v1/mcp/register/completion/hitl/${decision}` : '/api/v1/mcp/register/completion';
    const modelId=decision?pendingModelId.value:selectedModel.value;
    const body = decision ? { task_id: taskId, ...(pendingAction?.interrupt_id ? { interrupt_id: pendingAction.interrupt_id } : {}), ...(modelId?{model_id:modelId}:{}), ...(decision === 'reject' ? { feedback: feedback.value } : {}) } : { query, task_id: taskId, model_id:modelId };
    await postEventStream(path, body, event => { if (disposed || token !== operation)
        return; if (decision && pendingAction && ['text','event','interrupt'].includes(event.type))
        pendingAction.status = true; if (event.type === 'text')
        streamingContent.value.push({ type: 'text', data: event.content || '' });
    else if (event.type === 'event')
        streamingContent.value.push({ type: 'event', data: event.event || event });
    else if (event.type === 'interrupt')
        streamingContent.value.push({ type: 'interrupt', data: event.event || event }); scrollBottom(); }, controller.signal);
    if (disposed || token !== operation)
        return;
    if (decision && pendingAction)
        pendingAction.status = true;
    commitStream();
    feedback.value = '';
    const refreshed = await loadTasks();
    if (disposed || token !== operation)
        return;
    const fresh = tasks.value.find(task => task.id === taskId);
    if (refreshed && fresh && fresh.messages?.length >= messages.value.length)
        messages.value = fresh.messages;
}
catch (error: any) {
    if (token === operation && !disposed && error.name !== 'AbortError') {
        commitStream();
        streamError.value = responseError(error, 'MCP 响应失败，请重试');
    }
}
finally {
    if (token === operation && !disposed) {
        busy.value = false;
        creating.value = false;
        controller = undefined;
        scrollBottom();
    }
} }


function requestRevision(value:string){feedback.value=value;run('reject');}


function keydown(event: KeyboardEvent) { if (isSendKey(event)) {
    event.preventDefault();
    run();
} }
async function copy(content: MCPContent[]) { const value = content.filter(item => item.type === 'text').map(item => String(item.data || '')).join(''); try {
    await copyChatText(value);
    ElMessage.success('回答已复制');
}
catch {
    ElMessage.error('复制失败，请选中内容复制');
} }
const eventState = (event: any) => event.is_error || event.status === 'ERROR' ? '失败' : event.status === 'RECEIVE_STOPPED' ? '接收已停止' : event.status === 'START' ? '进行中' : event.status === 'END' ? '已完成' : '状态未记录';
onMounted(()=>{loadTasks();loadModels();});
onBeforeUnmount(() => { disposed = true; operation++; listRequest++; controller?.abort(); cancelAnimationFrame(frame); });
const composerInput=ref<HTMLTextAreaElement>();
watch(draft,()=>nextTick(()=>fitComposer(composerInput.value)));
</script>
<template>
<div class="b5-page b5-mcp-chat">
<button class="mobile-rail-button" aria-label="打开 MCP 会话记录" @click="sidebarOpen=true"><UiIcon name="list"/></button>
<SessionRail v-model:open="sidebarOpen" title="MCP 会话" variant="conversation" create-label="新建会话" :records="railRecords" :selected="currentId" :loading="loading" :error="loadError" :creating="creating" :deleting="deleting" :allow-delete="true" @select="selectTask" @create="createTask" @remove="removeTask" @retry="loadTasks"><template #footer><router-link class="mcp-rail-link" to="/mcp-server"><UiIcon name="arrow-left"/>返回 MCP 服务</router-link></template></SessionRail>
<main class="mcp-chat-main b5-chat">

<div class="mcp-chat-output chat-messages" ref="output" @scroll="onScroll">
<div v-if="!displayMessages.length" class="empty-chat"><UiIcon name="connect"/><h2>开始一段 MCP 对话</h2><p>描述你要接入的 MCP 服务，助手会检查配置。<br>需要注册或修改时，确认卡片会等待你的决定。</p></div>
<article v-for="(message,index) in displayMessages" :key="index" class="mcp-turn chat-turn">
<div v-if="message.query" class="mcp-user-message user-message"><p class="user-bubble">{{message.query}}</p><span class="message-avatar"><UserAvatar :username="user.userInfo?.username" :src="avatar"/></span></div>
<div v-if="message.content?.length || (busy && index === displayMessages.length - 1)" class="mcp-assistant-message assistant-message"><span class="message-avatar mcp-bot-avatar"><BrandLogo compact/></span><section class="mcp-answer assistant-bubble">
<div v-if="busy&&index===displayMessages.length-1&&!message.content?.length" class="mcp-working" role="status"><span class="mcp-waiting-dots"><i/><i/><i/></span>正在处理需求…</div>
<template v-for="(block,blockIndex) in blocks(message.content)" :key="blockIndex">
<MdPreview v-if="block.type==='text'" :editorId="'mcp-message-'+index+'-'+blockIndex" :modelValue="block.text"/>
<McpToolEvent v-else-if="block.type==='event'" :event="block.event" :active="busy&&index===displayMessages.length-1"/>
<McpApprovalCard v-else-if="block.type==='interrupt'" :data="block.data" :actionable="block.data===pending" :busy="busy" @approve="run('approve')" @reject="requestRevision"/>
</template>
<span v-if="busy&&index===displayMessages.length-1" class="mcp-stream-caret" aria-label="回答生成中"/>
<footer v-if="message.content?.some(item=>item.type==='text')&&!(busy&&index===displayMessages.length-1)" class="answer-actions"><button aria-label="复制回答" title="复制回答" @click="copy(message.content)"><ChatActionIcon name="copy"/></button></footer>
</section></div></article>
<p v-if="streamError" class="chat-error" role="alert">{{streamError}}</p>
</div>
<button v-if="!follow" class="near-bottom" @click="scrollBottom(true)"><UiIcon name="arrow-down"/>回到最新消息</button>
<form class="chat-composer mcp-composer conversation-composer welcome-composer" @submit.prevent="run()"><p v-if="modelError" class="mcp-model-error">{{modelError}}<button type="button" @click="loadModels">重试</button></p><textarea ref="composerInput" v-model="draft" rows="3" :disabled="creating||!!pending" :placeholder="pending?'请先处理上方的确认操作…':'输入你的问题，Shift + Enter 换行…'" aria-label="输入 MCP 消息" @keydown="keydown"/><div class="composer-footer"><p class="composer-help">{{pending?'操作已暂停，等待你的确认':'Enter 发送，Shift + Enter 换行'}}</p><div class="composer-send"><ProviderModelPicker v-model="selectedModel" :models="models" :loading="modelsLoading" :disabled="busy||creating||!!pending" :legacy-default="!!pending&&!pendingModelId"/><button v-if="busy" type="button" class="chat-primary" @click="stop"><UiIcon name="stop"/>停止</button><button v-else type="submit" class="chat-primary" :disabled="!draft.trim()||creating||!!pending||(!selectedModel)"><UiIcon name="send"/>发送</button></div></div></form>
</main></div></template>
<style scoped src="./mcp-chat.css"></style>
<style scoped src="../conversation/chatPage/chat.css"></style>

<style scoped src="../conversation/defaultPage/conversation-welcome.css"></style>
