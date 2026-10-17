<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter, onBeforeRouteLeave, onBeforeRouteUpdate } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { MdEditor, MdPreview } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';
import AppSidebar from '../../../components/AppSidebar.vue';
import TaskGlyph from '../../../components/TaskGlyph.vue';
import { taskResultExample, taskPlanningExample } from '../../../utils/task-result-example';
import UiIcon from '../../../components/UiIcon.vue';
import CapabilityPicker from '../../../components/CapabilityPicker.vue';
import { useUserStore } from '../../../store/user';
import { getWorkspaceSessionsAPI, getWorkspaceSessionInfoAPI, deleteWorkspaceSessionAPI } from '../../../apis/workspace';
import { getAllToolsAPI } from '../../../apis/tool';
import { getMCPServersAPI } from '../../../apis/mcp-server';
import { postEventStream, parseStringArray, copyChatText, downloadMarkdown, historyTime } from '../../../utils/chat-ui';
import { formatDataDate } from '../../../utils/data-pages';
import { responseError } from '../../../utils/resource-visuals';
const props = withDefaults(defineProps<{
    standalone?: boolean;
}>(), { standalone: true });
const supportedTools = new Set(['send_email', 'tavily_search', 'web_search', 'get_arxiv', 'get_weather', 'get_delivery_info', 'text_to_image', 'image_to_text', 'docx_to_pdf', 'pdf_to_docx', 'bocha_search', 'serply_search', 'youcom_search', 'youcom_research']);
const toolsFetched = ref(false);
interface Edge {
    start: string;
    end: string;
}
interface Step {
    title: string;
    result?: string;
    target?: string;
    status?: string;
}
interface Context {
    query: string;
    guide_prompt?: string;
    task_graph?: Edge[];
    task?: Step[];
    answer?: string;
}
interface NodeState {
    state: 'waiting' | 'working' | 'done' | 'submitted' | 'unknown';
    message: string;
}
const route = useRoute(), router = useRouter(), user = useUserStore();
const planningExample=computed(()=>route.query.example==='planning');
const example=computed(()=>planningExample.value||route.query.example==='1'||(props.standalone&&!route.query.session_id&&!route.query.query&&!route.query.guide_prompt));
const elapsed=ref('');
const exampleStep=(title:string)=>example.value?taskResultExample.steps.find(step=>step.title===title):undefined;
const query = ref(''), guide = ref(''), savedGuide = ref(''), result = ref(''), graph = ref<Edge[]>([]), states = ref(new Map<string, NodeState>()), phase = ref('planning'), history = ref(false), loading = ref(false), generating = ref(false), executing = ref(false), error = ref(''), historyError = ref(''), sessions = ref<any[]>([]), contexts = ref<Context[]>([]), contextIndex = ref(0), sessionTitle = ref(''), createdTime = ref(''), sessionLoaded = ref(false), guideMode = ref('edit'), webSearch = ref(false), plugins = ref<string[]>([]), mcpIds = ref<string[]>([]), attachments = ref<Array<{
    name: string;
    text: string;
}>>([]), feedbackDialog = ref(false), feedback = ref(''), selectedNode = ref(''), nodeDialog = ref(false), guideOutput = ref<HTMLElement>(), resultOutput = ref<HTMLElement>(), followGuide = ref(true), followResult = ref(true);
const tools = ref<Array<{
    id: string;
    name: string;
}>>([]), servers = ref<Array<{
    id: string;
    name: string;
}>>([]), toolsLoading = ref(false), serversLoading = ref(false), toolsError = ref(''), serversError = ref('');
let controller: AbortController | undefined, operation = 0, disposed = false, historyRequest = 0, resultFrame = 0, guideFrame = 0;
const busy = computed(() => generating.value || executing.value || loading.value), dirty = computed(() => !history.value && guide.value !== savedGuide.value);
const executionQuery = computed(() => query.value.trim() + attachments.value.map(item => `

[附件：${item.name}]
${item.text}`).join(''));
const taskTitle = computed(() => sessionTitle.value || query.value.split('\n')[0].slice(0, 35) || '任务规划');
const nodes = computed(() => [...new Set([...graph.value.flatMap(edge => [edge.start, edge.end]), ...states.value.keys()])].map(title => ({ title, ...(states.value.get(title) || { state: history.value ? 'unknown' : 'waiting', message: '' }), dependencies: graph.value.filter(edge => edge.end === title).map(edge => edge.start) })));
const nodeDetail = computed(() => nodes.value.find(node => node.title === selectedNode.value));
const guideSections = computed(() => { const matches = [...guide.value.matchAll(/^#{1,3}\s+(.+)$/gm)]; return matches.map((match, index) => ({ title: match[1].replace(/^\d+[.、．]\s*/,''), content: guide.value.slice((match.index || 0) + match[0].length, matches[index + 1]?.index ?? guide.value.length).trim() })); });
const stopped=ref(false);
const resultLabel = computed(() => executing.value ? '执行中' : stopped.value ? '接收已停止' : error.value ? '响应异常' : result.value ? nodes.value.length>0&&nodes.value.every(node=>node.state==='done') ? '已完成' : '已有结果' : graph.value.length ? '等待结果' : '待执行');
const executor=ref('灵寻智能体');
const avatar = computed(() => user.userInfo?.avatar || '');
function scrollResult(force = false) { if (force)
    followResult.value = true; if (!followResult.value)
    return; cancelAnimationFrame(resultFrame); nextTick(() => { if (!disposed)
    resultFrame = requestAnimationFrame(() => { if (resultOutput.value)
        resultOutput.value.scrollTop = resultOutput.value.scrollHeight; }); }); }
function scrollGuide(force = false) { if (force)
    followGuide.value = true; if (!followGuide.value)
    return; cancelAnimationFrame(guideFrame); nextTick(() => { if (!disposed)
    guideFrame = requestAnimationFrame(() => { if (guideOutput.value)
        guideOutput.value.scrollTop = guideOutput.value.scrollHeight; }); }); }
function trackScroll(element: HTMLElement | undefined, flag: 'guide' | 'result') { if (!element)
    return; const near = element.scrollHeight - element.scrollTop - element.clientHeight < 100; if (flag === 'guide')
    followGuide.value = near;
else
    followResult.value = near; }
function stop() { stopped.value=true;operation++; controller?.abort(); controller = undefined; generating.value = false; executing.value = false; for (const [title, state] of states.value)
    if (state.state === 'working')
        states.value.set(title, { state: 'unknown', message: state.message }); if (!history.value)
    error.value = '已停止接收，保留已收到的内容。'; }
async function fetchSessions() { if(planningExample.value){sessions.value=taskPlanningExample.sessions.map(item=>({...item}));return;} const id = ++historyRequest; historyError.value = ''; try {
    const response = await getWorkspaceSessionsAPI();
    if (disposed || id !== historyRequest)
        return;
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '任务记录加载失败');
    sessions.value = (response.data.data || []).filter((session: any) => session.agent !== 'simple').sort((a: any, b: any) => (Date.parse(b.update_time || b.create_time) || 0) - (Date.parse(a.update_time || a.create_time) || 0));
}
catch (err) {
    if (!disposed && id === historyRequest)
        historyError.value = responseError(err, '任务记录加载失败');
} }
async function loadTools() { toolsLoading.value = true; toolsError.value = ''; try {
    const response = await getAllToolsAPI();
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '工具加载失败');
    if (!disposed)
        tools.value = (response.data.data || []).filter(tool => tool.user_id === '0' && supportedTools.has(tool.name)).map(tool => ({ id: tool.tool_id, name: tool.display_name || tool.name }));
    toolsFetched.value = true;
}
catch (err) {
    if (!disposed)
        toolsError.value = responseError(err, '工具加载失败');
}
finally {
    if (!disposed)
        toolsLoading.value = false;
} }
async function loadServers() { serversLoading.value = true; serversError.value = ''; try {
    const response = await getMCPServersAPI();
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || 'MCP 加载失败');
    if (!disposed)
        servers.value = (response.data.data || []).map(server => ({ id: server.mcp_server_id, name: server.server_name }));
}
catch (err) {
    if (!disposed)
        serversError.value = responseError(err, 'MCP 加载失败');
}
finally {
    if (!disposed)
        serversLoading.value = false;
} }
function applyContext() { const context = contexts.value[contextIndex.value]; if (!context)
    return; query.value = context.query || ''; guide.value = context.guide_prompt || ''; savedGuide.value = guide.value; result.value = context.answer || ''; graph.value = Array.isArray(context.task_graph) ? context.task_graph.filter(edge => typeof edge.start === 'string' && typeof edge.end === 'string') : []; states.value = new Map(); for (const step of context.task || [])
    if (step.title)
        states.value.set(step.title, { state: step.result?.trim() ? 'done' : 'unknown', message: step.result || step.target || '' }); phase.value = result.value || graph.value.length ? 'result' : 'planning'; guideMode.value = 'preview'; error.value = ''; scrollResult(true); scrollGuide(true); }
async function initialize() { stopped.value=false;executor.value='灵寻智能体';operation++; controller?.abort(); controller = undefined; generating.value = false; executing.value = false; error.value = ''; sessionLoaded.value = false; query.value = ''; guide.value = ''; savedGuide.value = ''; result.value = ''; graph.value = []; states.value = new Map(); attachments.value = []; contexts.value = []; sessionTitle.value = ''; createdTime.value = ''; selectedNode.value = ''; nodeDialog.value = false; const token = operation, id = typeof route.query.session_id === 'string' ? route.query.session_id : ''; history.value = !!id; loading.value = !!id; phase.value = 'planning'; elapsed.value=''; if(planningExample.value){ query.value=taskPlanningExample.query; guide.value=taskPlanningExample.guide; savedGuide.value=guide.value;sessionTitle.value=taskPlanningExample.title;sessions.value=taskPlanningExample.sessions.map(item=>({...item}));guideMode.value='edit';return; } if(example.value){ const data=taskResultExample; history.value=true; sessionLoaded.value=true; loading.value=false; sessionTitle.value=data.title; createdTime.value=data.created; executor.value=data.executor; elapsed.value=data.duration; query.value=data.query; guide.value=data.guide; savedGuide.value=data.guide; result.value=data.report; graph.value=data.steps.slice(1).map((step,index)=>({start:data.steps[index].title,end:step.title})); states.value=new Map(data.steps.map(step=>[step.title,{state:'done',message:step.message}])); phase.value='result'; guideMode.value='preview'; return; } if (id) {
    try {
        const response = await getWorkspaceSessionInfoAPI(id);
        if (disposed || token !== operation)
            return;
        if (response.data.status_code !== 200 || !response.data.data)
            throw new Error(response.data.status_message || '任务记录加载失败');
        const data = response.data.data;
            executor.value=data.agent==='simple'?'日常对话':'灵寻智能体';
        sessionTitle.value = data.title || '';
        createdTime.value = data.create_time || '';
        contexts.value = Array.isArray(data.contexts) ? data.contexts : [];
        contextIndex.value = Math.max(0, contexts.value.length - 1);
        sessionLoaded.value = true;
        applyContext();
        if (!contexts.value.length)
            error.value = '此任务暂无可显示的上下文';
    }
    catch (err) {
        if (!disposed && token === operation)
            error.value = responseError(err, '任务记录加载失败');
    }
    finally {
        if (!disposed && token === operation)
            loading.value = false;
    }
}
else {
    query.value = typeof route.query.query === 'string' ? route.query.query : '';
    guide.value = typeof route.query.guide_prompt === 'string' ? route.query.guide_prompt : '';
    savedGuide.value = guide.value;
    plugins.value = parseStringArray(route.query.plugins || route.query.tools);
    mcpIds.value = parseStringArray(route.query.mcp_servers);
    webSearch.value = route.query.webSearch === 'true';
    guideMode.value = 'edit';
    if (query.value.trim() && !guide.value.trim())
        await generateGuide();
} }
async function generateGuide(regenerate = false) { if(planningExample.value){guide.value=taskPlanningExample.guide;savedGuide.value=guide.value;feedbackDialog.value=false;return;} if (busy.value || !executionQuery.value.trim())
    return; if (plugins.value.length && !toolsFetched.value)
    await loadTools(); if (plugins.value.some(id => !tools.value.some(tool => tool.id === id))) {
    error.value = '包含当前任务不支持的工具，请移除未找到的工具后重试';
    return;
} const previous = guide.value, token = ++operation; controller = new AbortController(); generating.value = true;stopped.value=false; error.value = ''; guide.value = ''; guideMode.value = 'preview'; const body = { query: executionQuery.value, plugins: plugins.value, mcp_servers: mcpIds.value, web_search: webSearch.value, ...(regenerate ? { guide_prompt: previous, feedback: feedback.value.trim() } : {}) }; feedbackDialog.value = false; try {
    await postEventStream(regenerate ? '/api/v1/workspace/lingseek/guide_prompt/feedback' : '/api/v1/workspace/lingseek/guide_prompt', body, event => { if (token !== operation || disposed)
        return; if (typeof event.data?.chunk === 'string')
        guide.value += event.data.chunk; scrollGuide(); }, controller.signal);
    if (token === operation && !disposed) {
        savedGuide.value = guide.value;
        guideMode.value = 'edit';
        if (!guide.value.trim())
            throw new Error('响应已结束，但未收到指导手册');
    }
}
catch (err: any) {
    if (token === operation && !disposed && err.name !== 'AbortError') {
        error.value = responseError(err, '指导手册生成失败');
        if (!guide.value)
            guide.value = previous;
    }
}
finally {
    if (token === operation && !disposed) {
        generating.value = false;
        controller = undefined;
    }
} }
async function startTask() { if(planningExample.value){savedGuide.value=guide.value;await router.push({path:route.path,query:{example:'1'}});return;} if (busy.value || history.value || !executionQuery.value.trim() || !guide.value.trim())
    return; if (plugins.value.length && !toolsFetched.value)
    await loadTools(); if (plugins.value.some(id => !tools.value.some(tool => tool.id === id))) {
    error.value = '包含当前任务不支持的工具，请移除未找到的工具后重试';
    return;
} const token = ++operation; controller = new AbortController(); executing.value = true;stopped.value=false; phase.value = 'result'; result.value = ''; graph.value = []; states.value = new Map(); error.value = ''; savedGuide.value = guide.value; guideMode.value = 'preview'; const body = { query: executionQuery.value, guide_prompt: guide.value, plugins: plugins.value, mcp_servers: mcpIds.value, web_search: webSearch.value }; try {
    await postEventStream('/api/v1/workspace/lingseek/task_start', body, event => { if (token !== operation || disposed)
        return; const data = event.data || {}; if (event.event === 'generate_tasks' && Array.isArray(data.graph)) {
        graph.value = data.graph.filter((edge: any) => typeof edge.start === 'string' && typeof edge.end === 'string');
        const targets = new Set(graph.value.map(edge => edge.end));
        for (const title of new Set(graph.value.flatMap(edge => [edge.start, edge.end])))
            if (!targets.has(title))
                states.value.set(title, { state: 'submitted', message: '任务需求已提交' });
    }
    else if (event.event === 'step_result' && typeof data.title === 'string') {
        states.value.set(data.title, { state: 'done', message: String(data.message || '') });
    }
    else if (event.event === 'step_start' && typeof data.title === 'string') {
        states.value.set(data.title, { state: 'working', message: String(data.message || '') });
    }
    else if (event.event === 'task_result' && typeof data.message === 'string') {
        result.value += data.message;
        scrollResult();
    }
    else if (typeof data.chunk === 'string') {
        result.value += data.chunk;
        scrollResult();
    } }, controller.signal);
    if (token === operation && !disposed) {
        if (!result.value.trim())
            error.value = '响应已结束，暂未收到最终结果';
        await fetchSessions();
    }
}
catch (err: any) {
    if (token === operation && !disposed && err.name !== 'AbortError')
        error.value = responseError(err, '任务执行失败');
}
finally {
    if (token === operation && !disposed) {
        executing.value = false;
        controller = undefined;
        scrollResult();
    }
} }
async function addAttachment(event: Event) { const input = event.target as HTMLInputElement, file = input.files?.[0]; input.value = ''; if (!file)
    return; if (!/\.(txt|md|csv|json)$/i.test(file.name) || file.size > 2 * 1024 * 1024 || attachments.value.length >= 5) {
    error.value = '支持 TXT、Markdown、CSV、JSON，单文件最大 2MB，最多 5 个附件';
    return;
} try {
    const text = new TextDecoder('utf-8', { fatal: true }).decode(await file.arrayBuffer());
    if (executionQuery.value.length + text.length + file.name.length + 10 > 16000)
        throw new Error('需求与附件正文合计不能超过 16000 字符');
    attachments.value.push({ name: file.name, text });
}
catch (err) {
    error.value = responseError(err, '请使用 UTF-8 编码的文本文件');
} }
function viewNode(title: string) { selectedNode.value = title; nodeDialog.value = true; }
async function copyResult() { try {
    await copyChatText(result.value);
    ElMessage.success('报告已复制');
}
catch {
    ElMessage.error('复制失败，请选中内容复制');
} }
function downloadResult() { downloadMarkdown(result.value, taskTitle.value); }
async function openSession(id: string) { if(planningExample.value){if(!await confirmLeave())return;const item=sessions.value.find(item=>item.session_id===id);if(item){sessionTitle.value=item.title;query.value=item.title;guide.value=taskPlanningExample.guide;savedGuide.value=guide.value;}return;} router.push({ path: props.standalone ? '/workspace/taskGraph' : '/workspace/workspacePage', query: { session_id: id } }); }
async function removeSessions(ids: string[]) {
if(busy.value||!ids.length)return;
try { await ElMessageBox.confirm(ids.length>1?'确定清空任务历史记录？删除后无法恢复。':'确定删除这条任务记录？删除后无法恢复。','删除任务记录',{confirmButtonText:'删除',cancelButtonText:'取消',type:'warning'}); } catch { return; }
try { for(const id of ids){ if(!planningExample.value){const response=await deleteWorkspaceSessionAPI(id);if(response.data.status_code!==200)throw new Error(response.data.status_message||'删除失败');} sessions.value=sessions.value.filter(item=>item.session_id!==id); } ElMessage.success('任务记录已删除'); } catch(err){ElMessage.error(responseError(err,'删除失败'));} }
function baseNewTask() { history.value = false; contexts.value = []; attachments.value = []; plugins.value = []; mcpIds.value = []; webSearch.value = false; result.value = ''; graph.value = []; states.value = new Map(); phase.value = 'planning'; guideMode.value = 'edit'; savedGuide.value = guide.value; router.replace({ path: props.standalone ? '/workspace/taskGraph' : '/workspace/workspacePage', query: { query: query.value, guide_prompt: guide.value } }); }
async function confirmLeave() { if (!generating.value && !executing.value && !dirty.value)
    return true; try {
    await ElMessageBox.confirm(generating.value || executing.value ? '正在生成内容，离开会停止接收本次响应。确定离开？' : '指导手册有未保存到任务的修改，是否放弃？', '离开任务', { type: 'warning', confirmButtonText: '离开', cancelButtonText: '继续查看' });
    return true;
}
catch {
    return false;
} }
onBeforeRouteLeave(confirmLeave);
onBeforeRouteUpdate((to, from) => to.fullPath !== from.fullPath ? confirmLeave() : true);
function beforeUnload(event: BeforeUnloadEvent) { if (generating.value || executing.value || dirty.value) {
    event.preventDefault();
    event.returnValue = '';
} }
watch(() => route.fullPath, initialize, { immediate: true });
onMounted(() => { user.initUserState(); fetchSessions(); loadTools(); loadServers(); window.addEventListener('beforeunload', beforeUnload); });
onBeforeUnmount(() => { disposed = true; operation++; historyRequest++; controller?.abort(); cancelAnimationFrame(resultFrame); cancelAnimationFrame(guideFrame); window.removeEventListener('beforeunload', beforeUnload); });
const stateLabel = (state: string) => ({ waiting: '等待结果', working: '执行中', done: '已完成', submitted: '已提交', unknown: '状态未记录' } as Record<string, string>)[state] || '状态未记录';
</script>
<template><div class="b5-page b5-task" :class="{'p-shell':standalone,'task-planning-view':phase==='planning','task-result-view':phase==='result','task-example-view':example}"><AppSidebar v-if="standalone"/><header class="task-topbar"><nav aria-label="面包屑"><router-link to="/workspace"><UiIcon name="arrow-left"/>返回工作台</router-link><span v-if="phase!=='result'">/</span><strong v-if="phase!=='result'" :title="taskTitle">{{taskTitle}}</strong></nav><span v-if="example" class="task-example-label">示例任务 · 用于样式预览</span></header><div class="task-workspace"><header class="task-page-heading"><div class="task-title-block"><TaskGlyph v-if="phase==='result'" class="task-heading-icon" kind="document" :size="76"/><div class="task-title-copy"><div class="task-title-line"><h1>{{phase==='result'?taskTitle:'任务规划'}}</h1><span v-if="phase==='result'" class="stream-status" :class="{working:executing,done:!!result&&!executing&&!error,error:!!error&&!stopped}"><UiIcon v-if="resultLabel==='已完成'" name="check"/>{{resultLabel}}</span></div><p v-if="phase==='planning'">确认执行方案，开始高效完成你的任务</p><p v-else class="task-metadata"><span v-if="createdTime">创建时间 {{formatDataDate(createdTime)}}</span><span v-if="elapsed">耗时 {{elapsed}}</span><span>执行者 {{executor}}</span><span v-if="history&&!example">历史任务</span></p></div></div><div class="task-heading-actions"><button v-if="busy&&(generating||executing)" class="chat-outline" @click="stop"><UiIcon name="stop"/>停止接收</button><button v-if="history&&sessionLoaded&&phase!=='result'" class="chat-outline" :disabled="busy" @click="baseNewTask"><UiIcon name="plus"/>基于此任务新建</button><button v-if="!history&&phase==='planning'" class="chat-primary" :disabled="busy||!guide.trim()||!executionQuery.trim()" @click="startTask"><UiIcon name="play"/>开始执行</button><router-link v-if="phase!=='result'" class="chat-outline task-back" to="/workspace"><UiIcon name="arrow-left"/>返回</router-link></div></header><div v-if="error" class="chat-error" :class="{stopped}" role="alert"><span>{{error}}</span><button v-if="history" :disabled="busy" @click="initialize">重新加载</button></div><div v-if="contexts.length>1" class="context-selector"><label>任务记录轮次<el-select v-model="contextIndex" @change="applyContext" class="catalog-select"><el-option v-for="(context,index) in contexts" :key="index" :value="index" :label="String(index+1)+' · '+String(context.query.slice(0,35))"/></el-select></label></div><div class="task-columns" :class="{planning:phase==='planning'}" v-loading="loading"><aside v-if="phase==='planning'" class="task-panel task-requirements"><h2>我的需求</h2><div class="requirement-input"><textarea maxlength="2000" v-model="query" :readonly="history" :disabled="generating" rows="6" placeholder="描述你想完成的任务…" aria-label="任务需求"/><div class="requirement-count">{{query.length}}/2000</div></div><div v-if="!history" class="requirement-actions"><label><UiIcon name="paperclip"/>添加文本附件<input type="file" accept=".txt,.md,.csv,.json" :disabled="busy" @change="addAttachment"></label><router-link to="/knowledge"><UiIcon name="book"/>管理知识库</router-link><button :disabled="busy" @click="query='调研一个产品的市场现状、竞争格局与用户需求，给出下一阶段的产品方案建议。'"><UiIcon name="file"/>示例需求</button><el-popover placement="bottom-start" :width="360" trigger="click"><template #reference><button class="task-resource-trigger" aria-label="执行资源设置"><UiIcon name="settings"/></button></template><fieldset v-if="!history" :disabled="busy" class="task-resource-settings"><label class="task-web-search"><input v-model="webSearch" type="checkbox">启用联网搜索</label><CapabilityPicker v-model="plugins" label="内置工具" icon="tool" :options="tools" :loading="toolsLoading" :error="toolsError" manage-path="/tool" @retry="loadTools"/><CapabilityPicker v-model="mcpIds" label="MCP 服务" icon="connect" :options="servers" :loading="serversLoading" :error="serversError" manage-path="/mcp-server" @retry="loadServers"/></fieldset></el-popover></div><div v-for="(attachment,index) in attachments" :key="index" class="attachment-chip"><UiIcon name="file"/><span :title="attachment.name">{{attachment.name}}</span><button :disabled="busy" aria-label="移除文本附件" @click="attachments.splice(index,1)"><UiIcon name="close"/></button></div><header class="task-history-heading"><h2>历史记录</h2><button :disabled="busy||!sessions.length" @click="removeSessions(sessions.map(item=>item.session_id))">清空</button></header><p v-if="historyError" class="task-history-error">{{historyError}}</p><div class="task-history-list"><div class="task-history-entry" v-for="session in sessions.slice(0,12)" :key="session.session_id"><button :class="{selected:route.query.session_id===session.session_id}" :disabled="busy" @click="openSession(session.session_id)"><TaskGlyph kind="document" :size="26" bare/><span><strong :title="session.title">{{session.title||'未命名任务'}}</strong><small>{{historyTime(session.update_time||session.create_time)}}</small></span></button><el-dropdown trigger="click"><button class="task-more" aria-label="历史任务操作">···</button><template #dropdown><el-dropdown-menu><el-dropdown-item @click="openSession(session.session_id)">查看任务</el-dropdown-item><el-dropdown-item @click="removeSessions([session.session_id])" class="dropdown-danger-action"><UiIcon name="trash"/><span>删除记录</span></el-dropdown-item></el-dropdown-menu></template></el-dropdown></div><p v-if="!sessions.length">{{historyError?'任务记录暂时无法读取':'暂无历史任务'}}</p></div></aside><section class="task-panel task-guide"><header class="task-panel-heading"><div><h2><TaskGlyph v-if="phase==='result'" kind="document"/>指导手册</h2><p v-if="phase==='result'">本任务根据以下步骤执行，{{resultLabel==='已完成'?'已全部完成。':'以下为执行步骤。'}}</p><p v-if="phase==='planning'">AI 已根据你的需求生成任务执行方案，你可以调整并完善</p></div><el-dropdown v-if="phase==='result'" trigger="click" class="task-panel-menu"><button class="task-more" aria-label="指导手册操作">···</button><template #dropdown><el-dropdown-menu><el-dropdown-item @click="copyChatText(guide)"><UiIcon name="copy"/><span>复制手册</span></el-dropdown-item><el-dropdown-item @click="downloadMarkdown(guide,taskTitle+'指导手册')"><UiIcon name="download"/><span>下载手册</span></el-dropdown-item><el-dropdown-item @click="baseNewTask">基于此任务新建</el-dropdown-item></el-dropdown-menu></template></el-dropdown><div v-if="phase==='planning'" class="guide-controls"><div class="guide-mode"><button :class="{active:guideMode==='edit'}" :disabled="history||generating" @click="guideMode='edit'">编辑</button><button :class="{active:guideMode==='preview'}" @click="guideMode='preview'">预览</button></div><button v-if="!history" class="chat-outline" :disabled="busy||!query.trim()" @click="guide.trim()?feedbackDialog=true:generateGuide()"><UiIcon name="refresh"/>{{guide.trim()?'重新生成':'生成手册'}}</button></div></header><div v-if="phase==='planning'&&guideMode==='edit'&&!history" class="task-guide-editor"><MdEditor v-model="guide" language="zh-CN" :preview="false" :toolbars="['title','bold','italic','codeRow','link','unorderedList','orderedList','task','quote','table','revoke','next']" :footers="[]" :disabled="generating"/></div><div v-else ref="guideOutput" class="task-guide-output" @scroll="trackScroll(guideOutput,'guide')"><template v-if="phase==='result'&&guideSections.length"><article v-for="(section,index) in guideSections" :key="index" class="guide-step"><span>{{index+1}}</span><div><h3>{{section.title}}</h3><MdPreview :editorId="`task-guide-step-${index}`" :modelValue="section.content"/></div><UiIcon v-if="resultLabel==='已完成'" class="guide-complete" name="check"/></article></template><MdPreview v-else-if="guide" editorId="task-guide-preview" :modelValue="guide"/><div v-else class="empty-chat"><UiIcon name="file"/><p>{{generating?'正在生成指导手册…':'填写需求后生成指导手册'}}</p></div></div><footer class="task-guide-footer"><span>{{generating?'指导手册生成中…':history?'历史手册':dirty?'手册已修改，执行时使用当前内容':'执行时使用当前手册'}}</span><button v-if="generating&&!followGuide" @click="scrollGuide(true)">回到最新内容</button><button v-if="phase==='result'&&!history&&!executing" @click="phase='planning'">返回规划</button></footer></section><section v-if="phase==='result'" class="task-panel task-flow"><header class="task-panel-heading"><div><h2><TaskGlyph kind="workflow"/>执行流程</h2><p>任务执行过程与关键节点</p></div><el-dropdown trigger="click" class="task-panel-menu"><button class="task-more" aria-label="执行流程操作">···</button><template #dropdown><el-dropdown-menu><el-dropdown-item @click="copyChatText(nodes.map(node=>node.title+'：'+node.message).join('\n'))">复制执行流程</el-dropdown-item><el-dropdown-item @click="nodes.length&&viewNode(nodes[0].title)">查看步骤详情</el-dropdown-item></el-dropdown-menu></template></el-dropdown></header><div class="task-flow-output"><div v-if="!nodes.length" class="empty-chat"><UiIcon name="workflow"/><p>{{executing?'正在生成任务流程…':'暂无任务流程'}}</p></div><article v-for="(node,index) in nodes" :key="node.title" class="flow-step" :class="node.state"><span class="flow-dot"/><button class="flow-step-card" @click="viewNode(node.title)"><header><TaskGlyph class="flow-number" :kind="exampleStep(node.title)?.icon||'document'" :size="49"/><strong>{{node.title}}</strong><span class="flow-state">{{stateLabel(node.state)}}</span></header><p v-if="node.message">{{node.message}}</p><p v-else>{{history?'未提供此步骤的执行记录':'等待服务返回步骤结果'}}</p><div v-if="exampleStep(node.title)" class="flow-evidence"><span v-for="(detail,index) in exampleStep(node.title)?.details" :key="detail"><TaskGlyph :kind="exampleStep(node.title)?.detailIcons[index]||'document'" :size="16" bare/>{{detail}}</span></div><p v-if="exampleStep(node.title)" class="flow-timing">2026–10–14 {{exampleStep(node.title)?.time}}<span>耗时 {{exampleStep(node.title)?.duration}}</span></p><div v-if="!example&&node.dependencies.length" class="flow-dependencies"><UiIcon name="connect"/><span :title="node.dependencies.join('、')">依赖：{{node.dependencies.join('、')}}</span></div><small v-if="!example">查看步骤详情<UiIcon name="chevron-right"/></small></button></article></div></section><section v-if="phase==='result'" class="task-panel task-result"><header class="task-panel-heading"><h2><TaskGlyph kind="document"/>执行结果</h2><div class="result-actions"><button class="chat-outline" :disabled="!result" @click="copyResult"><UiIcon name="copy"/>复制内容</button><button class="chat-primary" :disabled="!result" @click="downloadResult"><UiIcon name="download"/>下载报告</button></div></header><div ref="resultOutput" class="task-result-output" @scroll="trackScroll(resultOutput,'result')"><MdPreview v-if="result" editorId="task-final-result" :modelValue="result"/><div v-else class="empty-chat"><UiIcon name="file"/><h2>{{executing?'等待生成执行结果':'暂未收到执行结果'}}</h2><p>{{executing?'步骤响应会实时显示在中间的流程区。':'可查看已有步骤详情，或基于当前需求重新规划。'}}</p></div></div><button v-if="!followResult" class="near-bottom" @click="scrollResult(true)"><UiIcon name="arrow-down"/>最新结果</button></section></div></div><el-dialog v-model="feedbackDialog" title="重新生成指导手册" width="540px" class="b4-dialog" append-to-body :close-on-click-modal="false"><p class="task-feedback-help">描述需要调整的目标、步骤或输出形式。</p><el-input v-model="feedback" type="textarea" :rows="5" placeholder="例如：增加竞品对比，并明确输出表格…"/><template #footer><el-button @click="feedbackDialog=false">取消</el-button><el-button type="primary" :disabled="busy" @click="generateGuide(true)">重新生成</el-button></template></el-dialog><el-dialog v-model="nodeDialog" :title="nodeDetail?.title||'步骤详情'" width="720px" class="b4-dialog" append-to-body><p class="node-detail-status">{{stateLabel(nodeDetail?.state||'unknown')}}</p><MdPreview v-if="nodeDetail?.message" editorId="task-node-detail" :modelValue="nodeDetail.message"/><p v-else class="task-feedback-help">此步骤暂无详细响应。</p><template #footer><el-button @click="nodeDialog=false">关闭</el-button></template></el-dialog></div></template>
<style scoped src="./task-workspace.css"></style>
