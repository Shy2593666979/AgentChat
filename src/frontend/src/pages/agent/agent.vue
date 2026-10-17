<script setup lang="ts">
import CatalogHeader from '../../components/CatalogHeader.vue'
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAgentsAPI, deleteAgentAPI } from '../../apis/agent'
import { getVisibleLLMsAPI } from '../../apis/llm'
import { getVisibleToolsAPI } from '../../apis/tool'
import { getKnowledgeListAPI } from '../../apis/knowledge'
import { createConversationAPI } from '../../apis/history'
import { useHistoryChatStore } from '../../store/history_chat_msg'
import AgentCatalogCard from './AgentCatalogCard.vue'
import UiIcon from '../../components/UiIcon.vue'
import { modelDisplayName } from '../../utils/model-display'
import type { LLMResponse } from '../../apis/llm'
import { agentIdentity } from '../../utils/agent-identity'
import type { Agent } from '../../type'
import robotIcon from '../../assets/robot.svg'

const props = withDefaults(defineProps<{ assistantView?: boolean }>(), { assistantView: false })
const router = useRouter(), chatStore = useHistoryChatStore()
const modelDetails=ref<Record<string,LLMResponse>>({})

const agents = ref<Agent[]>([]), models = ref<Record<string, string>>({})
const toolNames = ref<Record<string, string>>({}), knowledgeNames = ref<Record<string, string>>({})
function capabilityLabel(ids: string[], names: Record<string, string>, fallback: string) { return names[ids[0]!] ? names[ids[0]!] + (ids.length > 1 ? ` +${ids.length - 1}` : '') : `${ids.length} 个${fallback}` }
function resourceCounts(agent:Agent){return [
  {key:'tools',icon:'grid',label:'工具',count:agent.tool_ids.length,title:agent.tool_ids.map(id=>toolNames.value[id]||id).join('、')},
  {key:'mcp',icon:'connect',label:'MCP',count:agent.mcp_ids.length,title:''},
  {key:'skill',icon:'layers',label:'Skill',count:agent.agent_skill_ids?.length||0,title:''},
  {key:'knowledge',icon:'database',label:'知识库',count:agent.knowledge_ids.length,title:agent.knowledge_ids.map(id=>knowledgeNames.value[id]||id).join('、')}
].filter(item=>item.count>0)}
const displayMode = ref('grid'), currentPage=ref(1)
const pageSize=6
const loading = ref(false), searchKeyword = ref(''), agentFilter = ref('all'), startingAgent = ref(''), catalogError = ref('')

const filteredAgents = computed(() => agents.value.filter(agent =>
  (agentFilter.value === 'all' || (agentFilter.value === 'mine' ? agent.is_custom !== false : agent.is_custom === false)) &&
  [agent.name, agent.description, models.value[agent.llm_id]].join(' ').toLowerCase().includes(searchKeyword.value.trim().toLowerCase())))
const displayedAgents=computed(()=>filteredAgents.value.slice((currentPage.value-1)*pageSize,currentPage.value*pageSize))
watch([searchKeyword,agentFilter],()=>currentPage.value=1)
watch(()=>filteredAgents.value.length,count=>currentPage.value=Math.max(1,Math.min(currentPage.value,Math.ceil(count/pageSize)||1)))
async function fetchAgents() {
  if (loading.value) return
  loading.value = true
  catalogError.value = ''
  try {
    const response = await getAgentsAPI()
    if (response.data.status_code !== 200) throw new Error(response.data.status_message || '获取智能体失败')
    agents.value = (response.data.data || []).map((agent: any) => ({ ...agent, agent_id: agent.id || agent.agent_id,
      tool_ids: agent.tool_ids || [], knowledge_ids: agent.knowledge_ids || [], mcp_ids: agent.mcp_ids || [], agent_skill_ids: agent.agent_skill_ids || [] }))
  } catch (error: any) { catalogError.value = error.message || '获取智能体失败，请重试' }
  finally { loading.value = false }
}
const createAgent = () => router.push({ path: '/agent/editor', query: props.assistantView ? { from: 'explore' } : {} })
const editAgent = (agent: Agent) => router.push({ path: '/agent/editor', query: { id: agent.agent_id, ...(props.assistantView ? { from: 'explore' } : {}) } })
async function removeAgent(agent: Agent) {
  try {
    await ElMessageBox.confirm('确定删除智能体“' + agent.name + '”？', '确认删除', { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' })
    const response = await deleteAgentAPI({ agent_id: agent.agent_id })
    if (response.data.status_code !== 200) throw new Error(response.data.status_message || '删除失败')
    ElMessage.success('删除成功')
    await fetchAgents()
  } catch (error: any) { if (error !== 'cancel' && error !== 'close') ElMessage.error(error.message || '删除失败') }
}
async function startChat(agent: Agent) {
  if (startingAgent.value) return
  startingAgent.value = agent.agent_id
  try {
    const name = '与' + agent.name + '的对话'
    const response = await createConversationAPI({ name, agent_id: agent.agent_id, agent_type: 'Agent' })
    if (response.data.status_code !== 200 || !response.data.data?.conversation_id) throw new Error(response.data.status_message || '创建会话失败')
    chatStore.conversationId = response.data.data.conversation_id
    chatStore.name = name
    chatStore.logo = agentIdentity(agent).url || robotIcon
    await router.push({ path: '/conversation/chatPage', query: { conversation_id: response.data.data.conversation_id } })
  } catch (error: any) { ElMessage.error(error.message || '创建会话失败') }
  finally { startingAgent.value = '' }
}

onMounted(async () => {
  await Promise.all([fetchAgents(), getVisibleLLMsAPI().then(response => {
    if (response.data.status_code === 200) {const list=(Array.isArray(response.data.data) ? response.data.data : Object.values(response.data.data || {}).flat()) as LLMResponse[];models.value=Object.fromEntries(list.map(model=>[model.llm_id,modelDisplayName(model)]));modelDetails.value=Object.fromEntries(list.map(model=>[model.llm_id,model]));}
  }).catch(() => {}), getVisibleToolsAPI().then(r => { if (r.data.status_code === 200) toolNames.value = Object.fromEntries((r.data.data || []).map(t => [t.tool_id, t.display_name || t.name])) }).catch(() => {}), getKnowledgeListAPI().then(r => { if (r.data.status_code === 200) knowledgeNames.value = Object.fromEntries((r.data.data || []).map(k => [k.id, k.name])) }).catch(() => {})])
})
</script>
<template><div class="b2-catalog catalog-page" :class="{ 'assistant-view': assistantView }"><svg class="svg-library" xmlns="http://www.w3.org/2000/svg"><defs>
<linearGradient id="robotBlue" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#277bff"/><stop offset="1" stop-color="#0054ff"/></linearGradient>
<symbol id="robot" viewBox="0 0 68 76"><path d="M34 18V7" stroke="#1266ff" stroke-width="3.5"/><circle cx="34" cy="6" r="5" fill="#216aff"/><rect x="1" y="33" width="8" height="20" rx="4" fill="#599aff"/><rect x="59" y="33" width="8" height="20" rx="4" fill="#599aff"/><rect x="6" y="17" width="56" height="55" rx="18" fill="url(#robotBlue)"/><path d="M14 26c2-3 6-5 12-5" fill="none" stroke="#77baff" stroke-width="2" stroke-linecap="round" opacity=".65"/><rect x="18" y="32" width="33" height="26" rx="11" fill="#fff"/><rect x="24" y="41" width="5" height="9" rx="2.5" fill="#2677ff"/><rect x="40" y="41" width="5" height="9" rx="2.5" fill="#2677ff"/><path d="M32 49q2 3 5 0" fill="none" stroke="#7eacff" stroke-width="1.5" stroke-linecap="round"/><circle cx="48" cy="30" r="2.7" fill="#abd9ff"/><path d="M21 66h23" stroke="#004aff" stroke-width="2" stroke-linecap="round" opacity=".25"/></symbol>
<symbol id="brandRobot" viewBox="0 0 40 40"><rect x="6" y="9" width="28" height="25" rx="11" fill="white"/><rect x="12" y="18" width="4" height="8" rx="2" fill="#2977ff"/><rect x="25" y="18" width="4" height="8" rx="2" fill="#2977ff"/><path d="M18 26q2 2 4 0" fill="none" stroke="#97baff" stroke-width="1.4"/><circle cx="32" cy="8" r="3.3" fill="#d3e8ff"/></symbol>
<symbol id="home" viewBox="0 0 24 24"><path d="m2 11 10-9 10 9M5 9v12h5v-7h4v7h5V9"/></symbol>
<symbol id="search" viewBox="0 0 24 24"><circle cx="10.3" cy="10.3" r="7.6"/><path d="m16 16 5.5 5.5"/></symbol>
<symbol id="chat" viewBox="0 0 24 24"><path d="M21 11.4a9.2 9.2 0 0 1-9.3 9.1c-1.6 0-3.2-.4-4.5-1.1L2 21l1.6-5A9.2 9.2 0 1 1 21 11.4Z"/><circle cx="7.3" cy="11.4" r=".8" fill="currentColor" stroke="none"/><circle cx="11.5" cy="11.4" r=".8" fill="currentColor" stroke="none"/><circle cx="15.7" cy="11.4" r=".8" fill="currentColor" stroke="none"/></symbol>
<symbol id="link" viewBox="0 0 24 24"><path d="m9 15 6-6M7.5 16.5l-1 1a4.5 4.5 0 0 1-6.3-6.4l5-5a4.5 4.5 0 0 1 6.4 0M16.5 7.5l1-1a4.5 4.5 0 0 1 6.3 6.4l-5 5a4.5 4.5 0 0 1-6.4 0" transform="translate(1 0) scale(.91)"/></symbol>
<symbol id="cube" viewBox="0 0 24 24"><path d="m12 1.5 9.5 5.2v10.5L12 22.5 2.5 17.2V6.7Z M2.5 6.7 12 12l9.5-5.3M12 12v10.5"/></symbol>
<symbol id="book" viewBox="0 0 24 24"><path d="M12 5C9 2 5 2 2 3v17c4-1 7-1 10 2 3-3 6-3 10-2V3c-3-1-7-1-10 2Zm0 0v11"/></symbol>
<symbol id="chart" viewBox="0 0 24 24"><path d="M4 21V12M12 21V3M20 21V7" stroke-width="2.8"/></symbol>
<symbol id="grid" viewBox="0 0 24 24"><rect x="2" y="2" width="8" height="8" rx="3"/><rect x="14" y="2" width="8" height="8" rx="3"/><rect x="2" y="14" width="8" height="8" rx="3"/><rect x="14" y="14" width="8" height="8" rx="3"/></symbol>
<symbol id="layers" viewBox="0 0 24 24"><path d="m12 1.5 10 5.7L12 13 2 7.2Zm-10 11L12 18l10-5.5M2 18l10 5.5L22 18"/></symbol>
<symbol id="chevron" viewBox="0 0 24 24"><path d="m5 9 7 7 7-7"/></symbol>
<symbol id="plus" viewBox="0 0 24 24"><path d="M12 3v18M3 12h18"/></symbol>
<symbol id="edit" viewBox="0 0 24 24"><path d="m4 16 12-12a2.5 2.5 0 0 1 3.5 0l.5.5a2.5 2.5 0 0 1 0 3.5L8 20l-5 1ZM14.5 5.5l4 4"/></symbol>
<symbol id="more" viewBox="0 0 24 24"><circle cx="4" cy="12" r="1.5" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none"/><circle cx="20" cy="12" r="1.5" fill="currentColor" stroke="none"/></symbol>
<symbol id="brain" viewBox="0 0 24 24"><path d="M11 4.5c-2-3-5-.8-4.6 1.4-3-.2-4.5 3-3 5-2.5 2-.8 5 1.2 5.5-.4 3.2 3.3 5.4 6.4 2.7Zm2 0c2-3 5-.8 4.6 1.4 3-.2 4.5 3 3 5 2.5 2 .8 5-1.2 5.5.4 3.2-3.3 5.4-6.4 2.7ZM7 6l1 3-2 2m5 1H8l-1 3m10-9-1 3 2 2m-5 1h3l1 3M8 19v-2m8 2v-2"/></symbol>
<symbol id="enterprise" viewBox="0 0 24 24"><path d="M3 21V4h14v17M17 9h4v12M1 21h22M7 7v3m6-3v3M7 13v3m6-3v3M9 21v-3h3v3"/></symbol>
<symbol id="calendar" viewBox="0 0 24 24"><rect x="5" y="5" width="16" height="16" rx="1.5"/><path d="M5 10h16M9 3v4m8-4v4M2 17V2h15M9 13h3v4H9"/></symbol>
<symbol id="mail" viewBox="0 0 24 24"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m3 6 9 7 9-7M16 1l2 2 2-2"/></symbol>
<symbol id="close" viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18"/></symbol>
<symbol id="menu" viewBox="0 0 24 24"><path d="M3 6h18M3 12h18M3 18h18"/></symbol>
<linearGradient id="greenIcon" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#00dd83"/><stop offset="1" stop-color="#00be68"/></linearGradient><linearGradient id="purpleIcon" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#a276ff"/><stop offset="1" stop-color="#6f31f5"/></linearGradient><linearGradient id="orangeIcon" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#ffb42f"/><stop offset="1" stop-color="#ff920b"/></linearGradient>
<symbol id="avatar-research" viewBox="0 0 64 64"><circle cx="27" cy="27" r="16" fill="none" stroke="#00c978" stroke-width="6"/><path d="m39 39 13 13" stroke="#00c978" stroke-width="7" stroke-linecap="round"/><path d="M16 25a12 12 0 0 1 13-10" stroke="#84efbd" stroke-width="2" fill="none" stroke-linecap="round"/></symbol>
<symbol id="avatar-writing" viewBox="0 0 64 64"><path d="M15 9h25l10 12v32a3 3 0 0 1-3 3H15a4 4 0 0 1-4-4V13a4 4 0 0 1 4-4" fill="url(#purpleIcon)"/><path d="M39 9v12h11" fill="#c5aaff"/><path d="M19 24h17M19 32h22M19 40h12" stroke="white" stroke-width="3" stroke-linecap="round"/><path d="m33 50 18-18 9 8-18 18-12 3Z" fill="#8950ff" stroke="#efe8ff" stroke-width="2.5"/><path d="m48 35 9 8" stroke="#efe8ff" stroke-width="2"/></symbol>
<symbol id="avatar-analytics" viewBox="0 0 64 64"><rect x="10" y="33" width="9" height="23" rx="3" fill="url(#orangeIcon)"/><rect x="26" y="21" width="9" height="35" rx="3" fill="url(#orangeIcon)"/><rect x="42" y="8" width="9" height="48" rx="3" fill="url(#orangeIcon)"/><path d="M45 12v39" stroke="#ffc968" stroke-width="1.5" stroke-linecap="round"/></symbol>
<symbol id="avatar-coding" viewBox="0 0 64 64"><path d="m19 21-12 12 12 11M45 21l12 12-12 11M36 13 27 52" stroke="#0863ff" fill="none" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><path d="m35 14-8 35" stroke="#79b3ff" stroke-width="2" stroke-linecap="round"/></symbol>
<symbol id="avatar-enterprise" viewBox="0 0 64 64"><path d="M9 13h14l6 6h23a4 4 0 0 1 4 4v29a4 4 0 0 1-4 4H13a5 5 0 0 1-5-5V17a4 4 0 0 1 1-4Z" fill="url(#greenIcon)"/><path d="M15 27h35" stroke="#eefff8" stroke-width="3" stroke-linecap="round"/><path d="M11 18v31" stroke="#56ebad" stroke-width="2" stroke-linecap="round" opacity=".6"/></symbol>
<symbol id="avatar-daily" viewBox="0 0 64 64"><rect x="9" y="14" width="44" height="44" rx="7" fill="url(#purpleIcon)"/><rect x="14" y="29" width="34" height="23" rx="3" fill="#f2eaff"/><path d="M21 12v10M41 12v10" stroke="#7d3eff" stroke-width="6" stroke-linecap="round"/><path d="M35 40c2-4 7-4 6 1s-4 8-7 6-1-4 1-7" fill="#925bff"/><path d="M13 19h36" stroke="#c2a0ff" stroke-width="1.5" opacity=".5"/></symbol>
</defs></svg><CatalogHeader :title="assistantView ? '我的助手' : '智能体'" :subtitle="assistantView ? '把重复的工作交给 AI' : '构建你的专属 AI 助手'" description="通过自然语言、知识和工具，创建能够执行特定任务的智能体"><template #actions><button class="create-button" @click="createAgent"><UiIcon name="plus-circle"/>{{ assistantView ? '新建助手' : '创建智能体' }}</button></template></CatalogHeader>
    <section class="workspace" :aria-label="assistantView ? '助手列表' : '智能体列表'">
      <div class="toolbar">
        <label class="search-wrap"><svg class="icon" aria-hidden="true"><use href="#search"/></svg><input v-model="searchKeyword" type="search" :aria-label="assistantView ? '搜索助手' : '搜索智能体'" :placeholder="assistantView ? '搜索助手名称、描述…' : '搜索智能体名称、描述或模型…'"></label>
        <template v-if="assistantView"><button class="create-button" @click="createAgent"><svg class="icon" aria-hidden="true"><use href="#plus"/></svg>新建助手</button><el-select v-model="agentFilter" class="catalog-select assistant-filter" aria-label="助手分类"><el-option value="all" label="全部助手"/><el-option value="mine" label="我的助手"/><el-option value="builtin" label="内置助手"/></el-select></template>
        <div v-else class="tabs" role="group" aria-label="智能体分类"><button v-for="filter in [{ id: 'all', label: '全部' }, { id: 'mine', label: '我的' }, { id: 'builtin', label: '内置' }]" :key="filter.id" class="tab" :class="{ active: agentFilter === filter.id }" :aria-pressed="agentFilter === filter.id" @click="agentFilter = filter.id">{{ filter.label }}</button></div>
        <div class="view-switch" role="group" aria-label="列表布局"><button aria-label="卡片视图" :aria-pressed="displayMode === 'grid'" :class="{ active: displayMode === 'grid' }" @click="displayMode = 'grid'"><UiIcon name="grid"/></button><button aria-label="列表视图" :aria-pressed="displayMode === 'list'" :class="{ active: displayMode === 'list' }" @click="displayMode = 'list'"><UiIcon name="list"/></button></div>
      </div>
      <div v-if="catalogError" class="catalog-error" role="alert"><p>{{ catalogError }}</p><button :disabled="loading" @click="fetchAgents">重新加载</button></div>
      <div class="cards" :class="{ 'list-mode': displayMode === 'list' }" v-loading="loading" :aria-busy="loading">
        <button v-if="assistantView" class="new-card" @click="createAgent"><span class="plus-circle"><svg class="icon" aria-hidden="true"><use href="#plus"/></svg></span><strong>新建助手</strong><p>基于你的需求，快速创建专属 AI 助手，提升工作效率</p></button>
        <AgentCatalogCard v-for="agent in displayedAgents" :key="agent.agent_id" :agent="agent"
          :model-name="models[agent.llm_id] || (agent.llm_id ? '模型未加载' : '模型未配置')"
          :model="modelDetails[agent.llm_id]" :resources="resourceCounts(agent)"
          :starting="startingAgent === agent.agent_id" :disabled="!!startingAgent"
          @chat="startChat(agent)" @edit="editAgent(agent)" @remove="removeAgent(agent)" />
        <div v-if="!loading && !catalogError && !displayedAgents.length" class="empty-state"><h3>{{ searchKeyword || agentFilter !== 'all' ? '没有找到匹配的智能体' : '暂无智能体' }}</h3><p>{{ searchKeyword || agentFilter !== 'all' ? '试试其他关键词或分类' : '创建你的第一个智能体，开始智能对话' }}</p><button v-if="!assistantView" class="create-button" @click="createAgent">创建智能体</button></div>
      </div>
      <div v-if="!loading&&!catalogError&&filteredAgents.length" class="agent-pagination"><span class="agent-total">共 {{filteredAgents.length}} 个智能体</span><el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="filteredAgents.length" layout="prev, pager, next" background/></div>
    </section>
  </div>
</template>
<style scoped src="./agent-catalog-a.css"></style>
