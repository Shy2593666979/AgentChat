<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, provide, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import UiIcon from '../../components/UiIcon.vue';
import { agentIdentity } from '../../utils/agent-identity';
import CapabilityIcon from '../../components/CapabilityIcon.vue';
import { getAgentsAPI, type AgentResponse } from '../../apis/agent';
import { createConversationAPI, getConversationListAPI, deleteConversationAPI, switchConversationAgentAPI } from '../../apis/history';

import { useHistoryChatStore } from '../../store/history_chat_msg';
import { historyGroup, historyTime } from '../../utils/chat-ui';
import { useScrollingScrollbar } from '../../utils/scrolling-scrollbar';

import { responseError } from '../../utils/resource-visuals';
interface Conversation {
    id: string;
    name: string;
    agentId: string;
    logo: string;
    time: string;
    titlePending: boolean;
}
const route = useRoute(), router = useRouter(), store = useHistoryChatStore();
const { scrolling, showScrollbar } = useScrollingScrollbar();
const conversations = ref<Conversation[]>([]), agents = ref<AgentResponse[]>([]), loading = ref(false), agentsLoading = ref(false), loadError = ref(''), agentError = ref('');
const search = ref(''), agentSearch = ref(''), selectedAgent = ref(''), picker = ref(false), creating = ref(false), createError = ref(''), deleting = ref(''), pendingMessage = ref(''), sidebarOpen = ref(false), brokenLogos = ref(new Set<string>());
const attachment = ref<{
    url: string;
    name: string;
    size?: number;
    mime?: string;
}>();
const agentId = (agent: AgentResponse) => String((agent as any).id || agent.agent_id);
const currentConversation = computed(() => conversations.value.find(conversation => conversation.id === route.query.conversation_id));
const activeAgent = computed(() => agents.value.find(agent => agentId(agent) === currentConversation.value?.agentId));
const pickedAgent = computed(() => agents.value.find(agent => agentId(agent) === selectedAgent.value));
const visibleAgents = computed(() => agents.value.filter(agent => [agent.name, agent.description].join(' ').toLowerCase().includes(agentSearch.value.trim().toLowerCase())));
const groups = computed(() => { const visible = conversations.value.filter(conversation => conversation.name.toLowerCase().includes(search.value.trim().toLowerCase())).sort((a, b) => (Date.parse(b.time) || 0) - (Date.parse(a.time) || 0)); return ['今天', '昨天', '过去 7 天', '更早'].map(label => ({ label, items: visible.filter(conversation => historyGroup(conversation.time) === label) })).filter(group => group.items.length); });
let disposed = false, listRequest = 0, agentRequest = 0;
let titlePoll: ReturnType<typeof setTimeout> | undefined;
async function fetchConversations(showLoading = true) { const id = ++listRequest; if (showLoading) loading.value = true; loadError.value = ''; try {
    const response = await getConversationListAPI();
    if (disposed || id !== listRequest)
        return;
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '会话记录加载失败');
    conversations.value = (response.data.data || []).map((conversation: any) => ({ id: conversation.conversation_id, name: conversation.name || '新会话', agentId: String(conversation.agent_id || ''), logo: conversation.logo_url || '', time: conversation.update_time || conversation.create_time || '', titlePending: conversation.title_pending === true }));
    clearTimeout(titlePoll);
    if (conversations.value.some(conversation => conversation.titlePending)) titlePoll = setTimeout(() => fetchConversations(false), 2000);
}
catch (error) {
    if (id === listRequest && !disposed)
        loadError.value = responseError(error, '会话记录加载失败');
}
finally {
    if (id === listRequest && !disposed)
        loading.value = false;
} }
async function fetchAgents() { const id = ++agentRequest; agentsLoading.value = true; agentError.value = ''; try {
    const response = await getAgentsAPI();
    if (disposed || id !== agentRequest)
        return;
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '智能体加载失败');
    agents.value = (response.data.data || []).map(agent => ({ ...agent, logo_url: agentIdentity(agent).url }));
}
catch (error) {
    if (!disposed && id === agentRequest)
        agentError.value = responseError(error, '智能体加载失败');
}
finally {
    if (!disposed && id === agentRequest)
        agentsLoading.value = false;
} }
async function requestConversation(message = '', forcePicker = false) { if (creating.value)
    return; pendingMessage.value = message; if (forcePicker || !pickedAgent.value) {
    createError.value = '';
    picker.value = true;
    if (!agents.value.length)
        await fetchAgents();
}
else
    await createConversation(); }
async function createConversation() { if (creating.value || !pickedAgent.value)
    return; creating.value = true; createError.value = ''; const agent = pickedAgent.value; try {
    const response = await createConversationAPI({ name: '新会话', agent_id: agentId(agent), agent_type: 'Agent' });
    if (response.data.status_code !== 200 || !response.data.data?.conversation_id)
        throw new Error(response.data.status_message || '创建会话失败');
    picker.value = false;
    await fetchConversations();
    sidebarOpen.value = false;
    await router.push({ path: '/conversation/chatPage', query: { conversation_id: response.data.data.conversation_id, initial_message: pendingMessage.value || undefined } });
    pendingMessage.value = '';
}
catch (error) {
    createError.value = responseError(error, '创建会话失败');
}
finally {
    creating.value = false;
} }
async function removeConversation(conversation: Conversation) { if (deleting.value)
    return; try {
    await ElMessageBox.confirm(`确定删除会话“${conversation.name}”及其记录？`, '删除会话', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' });
    deleting.value = conversation.id;
    const response = await deleteConversationAPI(conversation.id);
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '删除失败');
    if (route.query.conversation_id === conversation.id)
        await router.push('/conversation');
    await fetchConversations();
    ElMessage.success('会话已删除');
}
catch (error) {
    if (error !== 'cancel' && error !== 'close')
        ElMessage.error(responseError(error, '删除会话失败'));
}
finally {
    deleting.value = '';
} }
function selectConversation(conversation: Conversation) { attachment.value = undefined; sidebarOpen.value = false; router.push({ path: '/conversation/chatPage', query: { conversation_id: conversation.id } }); }
function newConversation() { attachment.value = undefined; selectedAgent.value = ''; pendingMessage.value = ''; sidebarOpen.value = false; router.push('/conversation'); }
function failLogo(id: string) { brokenLogos.value = new Set([...brokenLogos.value, id]); }
provide('requestConversation', requestConversation);
provide('conversationAgents', agents);
provide('conversationAgentsLoading', agentsLoading);
provide('conversationAgentError', agentError);
provide('refreshConversationAgents', fetchAgents);
provide('selectedConversationAgent', selectedAgent);
provide('conversationCreating', creating);
provide('conversationCreateError', createError);
provide('conversationAttachment', attachment);
provide('activeConversationAgent', activeAgent);
provide('activeConversation', currentConversation);
provide('refreshConversations', fetchConversations);
provide('chooseConversationAgent', () => requestConversation('', true));
provide('switchConversationAgent', async (id: string) => {
    const conversationId = String(route.query.conversation_id || '');
    if (!conversationId || creating.value) return false;
    try {
        const response = await switchConversationAgentAPI(conversationId, id);
        if (response.data.status_code !== 200) throw new Error(response.data.status_message || '切换失败');
        if (disposed || route.query.conversation_id !== conversationId) return false;
        listRequest++;
        conversations.value = conversations.value.map(conversation => conversation.id === conversationId ? { ...conversation, agentId: id } : conversation);
        selectedAgent.value = id;
        void fetchConversations(false);
        return true;
    } catch (error) {
        if (!disposed && route.query.conversation_id === conversationId) ElMessage.error(responseError(error, '智能体切换失败'));
        return false;
    }
});
watch(currentConversation, conversation => { if (conversation) {
    store.name = conversation.name;
    store.logo = activeAgent.value?.logo_url || conversation.logo;
} }, { immediate: true });
onMounted(() => { fetchConversations(); fetchAgents(); });
onBeforeUnmount(() => { disposed = true; listRequest++; agentRequest++; clearTimeout(titlePoll); });
</script>
<template><div class="b5-page b5-conversation" :class="{ 'has-chat': route.path === '/conversation/chatPage' }"><button class="mobile-history" aria-label="打开会话记录" @click="sidebarOpen=true"><UiIcon name="list"/></button><div v-if="sidebarOpen" class="conversation-scrim" @click="sidebarOpen=false"/><aside class="conversation-history" :class="{open:sidebarOpen}"><header><button class="new-conversation" @click="newConversation"><UiIcon name="plus"/>新建会话</button><button class="close-history" aria-label="关闭会话记录" @click="sidebarOpen=false"><UiIcon name="close"/></button></header><label class="history-search"><UiIcon name="search"/><input v-model="search" type="search" placeholder="搜索会话…" aria-label="搜索会话"></label><div v-if="loadError" class="history-error" role="alert">{{loadError}}<button @click="fetchConversations()">重试</button></div><div class="conversation-list scrollbar-on-scroll" :class="{ 'is-scrolling': scrolling }" v-loading="loading" @scroll.passive="showScrollbar"><section v-for="group in groups" :key="group.label"><h2>{{group.label}}</h2><article v-for="conversation in group.items" :key="conversation.id" class="conversation-entry" :class="{selected:route.query.conversation_id===conversation.id}"><button class="entry-select" :title="conversation.name" @click="selectConversation(conversation)"><span class="entry-avatar"><UiIcon name="chat"/></span><span class="entry-copy"><strong>{{conversation.name}}</strong><small>{{historyTime(conversation.time)}}</small></span></button><el-dropdown trigger="click"><button class="entry-more" :aria-label="`${conversation.name}的更多操作`"><UiIcon name="more"/></button><template #dropdown><el-dropdown-menu><el-dropdown-item :disabled="!!deleting" @click="removeConversation(conversation)" class="dropdown-danger-action"><UiIcon name="trash"/><span>删除会话</span></el-dropdown-item></el-dropdown-menu></template></el-dropdown></article></section><p v-if="!loading&&!groups.length" class="history-empty">{{loadError?'会话记录暂时无法读取':search?'没有匹配的会话':'暂无会话，开始一段新对话'}}</p></div></aside><main class="conversation-view"><router-view/></main><el-dialog v-model="picker" title="选择智能体" width="680px" class="b4-dialog b5-agent-picker" append-to-body :close-on-click-modal="false" :show-close="!creating" :close-on-press-escape="!creating"><el-input v-model="agentSearch" placeholder="搜索名称或描述" clearable :disabled="creating"/><div v-if="agentError" class="dialog-error" role="alert">{{agentError}}<el-button @click="fetchAgents">重试</el-button></div><div class="picker-agents" v-loading="agentsLoading"><button v-for="agent in visibleAgents" :key="agentId(agent)" :class="{selected:selectedAgent===agentId(agent)}" :disabled="creating" :aria-pressed="selectedAgent===agentId(agent)" @click="selectedAgent=agentId(agent)"><span class="picker-avatar"><img v-if="agent.logo_url&&!brokenLogos.has(agentId(agent))" :src="agent.logo_url" alt="" @error="failLogo(agentId(agent))"><CapabilityIcon v-else kind="coding" robot/></span><span><strong>{{agent.name}}</strong><small>{{agent.description||'暂未填写描述'}}</small></span><UiIcon v-if="selectedAgent===agentId(agent)" name="check"/></button><p v-if="!agentsLoading&&!visibleAgents.length">{{agentSearch?'没有匹配的智能体':'暂无智能体，先创建一个智能体'}}</p></div><p v-if="createError" class="dialog-error" role="alert">{{createError}}</p><template #footer><el-button :disabled="creating" @click="picker=false">取消</el-button><el-button type="primary" :loading="creating" :disabled="!pickedAgent" @click="createConversation">开始会话</el-button></template></el-dialog></div></template>
<style scoped src="./conversation.css"></style>

<style scoped src="../../styles/scrolling-scrollbar.css"></style>
