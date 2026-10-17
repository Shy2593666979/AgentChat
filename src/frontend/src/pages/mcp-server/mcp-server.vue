<script setup lang="ts">
import CatalogHeader from '../../components/CatalogHeader.vue'
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import UiIcon from '../../components/UiIcon.vue';
import McpGlyph from '../../components/McpGlyph.vue';
import { responseError } from '../../utils/resource-visuals';
import { safeResourceUrl } from '../../utils/data-pages';
import { uploadFileAPI } from '../../apis/tool';
import { retryMCPMetadataAPI, getMCPServersAPI, createMCPServerAPI, updateMCPServerAPI, deleteMCPServerAPI, type MCPServer, type MCPServerTool } from '../../apis/mcp-server';
import { useUserStore } from '../../store/user';
interface Server extends MCPServer {
    description?: string;
}
const router = useRouter(), store = useUserStore();


const servers = ref<Server[]>([]), loading = ref(false), loadError = ref(''), search = ref(''), filter = ref('all'), brokenLogos = ref(new Set<string>());
const dialog = ref(false), editing = ref<Server>(), saving = ref(false), uploading = ref(false), formError = ref(''), mode = ref('form'), deleting = ref('');
const form = reactive({ name: '', url: '', type: 'sse', logo: '', json: '' }), connectionBaseline = ref('');
const details = ref<Server>();
const currentPage=ref(1),pageSize=6;
let refreshTimer: ReturnType<typeof setTimeout> | undefined;
let disposed = false, requestId = 0;
const owns = (server: Server) => server.user_id === '0' || server.user_id === store.userInfo?.id || store.userInfo?.id === '1';
const status = (server: Server) => ['pending','running'].includes(server.metadata_status || '') ? 'pending' : server.metadata_status === 'failed' ? 'failed' : 'added';
const statusLabel = (server: Server) => ({pending:'读取中',failed:'读取异常',added:'已添加'}[status(server)]);
function toolParams(server: Server): MCPServerTool[] { return Array.isArray(server.params) ? server.params : []; }
function toolNames(server: Server) { return [...new Set([...(Array.isArray(server.tools) ? server.tools : []), ...toolParams(server).map(tool => tool.name)])]; }
const filteredServers = computed(() => servers.value.filter(server => [server.server_name, server.description].join(' ').toLowerCase().includes(search.value.trim().toLowerCase()) && (filter.value === 'all' || status(server) === filter.value)));
const visibleServers=computed(()=>filteredServers.value.slice((currentPage.value-1)*pageSize,currentPage.value*pageSize));
watch([search,filter],()=>currentPage.value=1);
watch(()=>filteredServers.value.length,count=>currentPage.value=Math.max(1,Math.min(currentPage.value,Math.ceil(count/pageSize)||1)));
const protocol = (type: string) => ({ sse: 'SSE', streamable_http: 'HTTP', websocket: 'WebSocket' } as Record<string, string>)[type] || type?.toUpperCase() || 'MCP';
async function fetchServers() { const id = ++requestId; loading.value = true; loadError.value = ''; try {
    const response = await getMCPServersAPI();
    if (disposed || id !== requestId)
        return;
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '服务列表加载失败');
    servers.value = response.data.data || [];
    if (refreshTimer) clearTimeout(refreshTimer);
    if (servers.value.some(server => ['pending', 'running'].includes(server.metadata_status || '')))
        refreshTimer = setTimeout(fetchServers, 3000);
}
catch (error) {
    if (id === requestId && !disposed)
        loadError.value = responseError(error, '服务列表加载失败，请重试');
}
finally {
    if (id === requestId && !disposed)
        loading.value = false;
} }
function openEditor(server?: Server) {  editing.value = server; mode.value = 'form'; formError.value = ''; Object.assign(form, { name: server?.server_name || '', url: server?.url || '', type: server?.type || 'sse', logo: server?.logo_url || '', json: JSON.stringify(server?.imported_config || { mcpServers: { [server?.server_name || 'my-service']: { type: server?.type || 'sse', url: server?.url || 'https://example.com/mcp' } } }, null, 2) }); connectionBaseline.value = JSON.stringify({ url: form.url, type: form.type, json: form.json }); dialog.value = true; }
function imported() { const data = JSON.parse(form.json); if (!data || Array.isArray(data) || typeof data !== 'object' || !data.mcpServers || typeof data.mcpServers !== 'object' || Array.isArray(data.mcpServers) || Object.keys(data.mcpServers).length !== 1)
    throw new Error('请提供包含一个服务的 mcpServers 对象'); const [name, config] = Object.entries(data.mcpServers)[0] as [
    string,
    any
]; if (!name.trim() || !config || typeof config !== 'object' || Array.isArray(config))
    throw new Error('服务名称和连接配置不能为空'); if (config.headers && (typeof config.headers !== 'object' || Array.isArray(config.headers)))
    throw new Error('headers 必须是 JSON 对象'); return { data, name, config }; }
function applyImport() { try {
    const { name, config } = imported();
    form.name = name;
    form.url = config.url || '';
    form.type = config.type || 'sse';
    mode.value = 'form';
    formError.value = '';
}
catch (error) {
    formError.value = responseError(error, 'JSON 格式无效');
} }
async function saveServer() { if (saving.value || uploading.value)
    return; formError.value = ''; try {
    let name = form.name.trim(), url = form.url.trim(), type = form.type, config: any;
    if (mode.value === 'json') {
        const parsed = imported();
        name = name || parsed.name;
        url = parsed.config.url;
        type = parsed.config.type;
        config = parsed.data;
    }
    else {
        if (!name)
            throw new Error('请输入服务名称');
        const parsed = imported();
        config = { ...parsed.data, mcpServers: { [name]: { ...parsed.config, url, type } } };
    }
    if (!name)
        throw new Error('请输入服务名称');
    if (!['sse', 'streamable_http', 'websocket'].includes(type))
        throw new Error('请选择支持的传输类型');
    let parsedUrl: URL;
    try {
        parsedUrl = new URL(url);
    }
    catch {
        throw new Error('请输入有效的服务地址');
    }
    if (!(type === 'websocket' ? ['ws:', 'wss:'] : ['http:', 'https:']).includes(parsedUrl.protocol))
        throw new Error(type === 'websocket' ? 'WebSocket 地址应以 ws:// 或 wss:// 开头' : '服务地址应以 http:// 或 https:// 开头');
    const changed = JSON.stringify({ url: form.url, type: form.type, json: form.json }) !== connectionBaseline.value;
    config = { ...config, mcpServers: { [name]: Object.values(config.mcpServers)[0] } };
    saving.value = true;
    const response = editing.value ? await updateMCPServerAPI({ server_id: editing.value.mcp_server_id, name, logo_url: form.logo, imported_config: changed || mode.value === 'json' ? config : undefined }) : await createMCPServerAPI({ server_name: name, logo_url: form.logo, imported_config: config });
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '保存失败');
    dialog.value = false;
    ElMessage.success(response.data.data?.metadata_status === 'pending' ? '服务已保存，正在后台生成工具信息与描述' : 'MCP 服务已保存');
    await fetchServers();
}
catch (error) {
    formError.value = responseError(error, '保存服务失败');
}
finally {
    saving.value = false;
} }
async function uploadLogo(event: Event) { const input = event.target as HTMLInputElement, file = input.files?.[0]; input.value = ''; if (!file)
    return; if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 2 * 1024 * 1024) {
    ElMessage.warning('请选择 2MB 以内的 JPG、PNG 或 WebP 图片');
    return;
} uploading.value = true; try {
    const response = await uploadFileAPI(file);
    if (response.data.status_code !== 200 || typeof response.data.data !== 'string')
        throw new Error(response.data.status_message || '上传失败');
    form.logo = response.data.data;
}
catch (error) {
    formError.value = responseError(error, '头像上传失败');
}
finally {
    uploading.value = false;
} }
async function removeServer(server: Server) { if (deleting.value || !owns(server))
    return; try {
    await ElMessageBox.confirm(`确定删除 MCP 服务“${server.server_name}”？`, '删除服务', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' });
    deleting.value = server.mcp_server_id;
    const response = await deleteMCPServerAPI(server.mcp_server_id);
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '删除失败');
    ElMessage.success('服务已删除');
    await fetchServers();
}
catch (error) {
    if (error !== 'cancel' && error !== 'close')
        ElMessage.error(responseError(error, '删除失败'));
}
finally {
    deleting.value = '';
} }
function failLogo(id: string) { brokenLogos.value = new Set([...brokenLogos.value, id]); }
async function retryMetadata(server: Server) {
    try {
        const response = await retryMCPMetadataAPI(server.mcp_server_id);
        if (response.data.status_code !== 200) throw new Error(response.data.status_message);
        ElMessage.success('已开始重新生成');
        await fetchServers();
    } catch (error) { ElMessage.error(responseError(error, '重试失败')); }
}
onMounted(fetchServers);
onBeforeUnmount(() => { if (refreshTimer) clearTimeout(refreshTimer); disposed = true; requestId++; });
</script>
<template><div class="b3-page b4-page b4-mcp catalog-page"><CatalogHeader title="MCP" subtitle="连接外部工具与数据服务" description="统一管理 MCP 服务与工具，为智能体扩展能力"><template #actions><button class="primary-button" @click="openEditor()"><UiIcon name="plus"/>添加服务</button><button class="primary-button mcp-custom-entry" @click="router.push('/mcp-server/chat')"><svg class="p-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m10 13 4-4M8 16l-1.5 1.5a4 4 0 0 1-5.7-5.7L6 7.6a4 4 0 0 1 5.7 0M16 8l1.5-1.5a4 4 0 0 1 5.7 5.7L19 16.4a4 4 0 0 1-5.7 0" transform="translate(1 0) scale(.9)"/></svg>自定义 MCP</button></template></CatalogHeader><div class="resource-toolbar"><label class="search-field"><UiIcon name="search"/><input v-model="search" type="search" placeholder="搜索服务名称或描述…" aria-label="搜索 MCP 服务"></label><div class="filter-controls"><el-select v-model="filter" aria-label="服务状态" class="catalog-select"><el-option value="all" label="全部状态"/><el-option value="added" label="已添加"/><el-option value="pending" label="读取中"/><el-option value="failed" label="读取异常"/></el-select></div></div><div v-if="loadError" class="error-banner" role="alert"><span>{{loadError}}</span><button @click="fetchServers">重新加载</button></div><section class="resource-grid mcp-grid" v-loading="loading"><article v-for="server in visibleServers" :key="server.mcp_server_id" class="resource-card mcp-card"><div class="mcp-card-header"><span class="mcp-art"><img v-if="server.logo_url&&!/\/icons\//i.test(server.logo_url)&&!brokenLogos.has(server.mcp_server_id)" :src="safeResourceUrl(server.logo_url)" alt="" @error="failLogo(server.mcp_server_id)"><McpGlyph v-else :name="server.server_name"/></span><div class="mcp-title"><h2 :title="server.server_name">{{server.server_name}}</h2></div><div class="mcp-badges"><span class="mcp-protocol">{{protocol(server.type)}}</span><span class="mcp-config-status" :class="status(server)" title="服务元数据状态"><i/>{{statusLabel(server)}}</span></div><el-dropdown v-if="owns(server)" trigger="click"><button class="more-button" :aria-label="`${server.server_name}的更多操作`"><UiIcon name="more"/></button><template #dropdown><el-dropdown-menu><el-dropdown-item @click="openEditor(server)"><UiIcon name="edit"/><span>编辑服务</span></el-dropdown-item><el-dropdown-item :disabled="!!deleting" @click="removeServer(server)" class="dropdown-danger-action"><UiIcon name="trash"/><span>删除服务</span></el-dropdown-item></el-dropdown-menu></template></el-dropdown></div><p class="mcp-description" :title="server.description">{{server.description||`${server.user_id==='0'?'内置服务':'自定义服务'} · ${toolNames(server).length} 个工具`}}</p><p v-if="server.metadata_status==='pending'||server.metadata_status==='running'" class="mcp-dialog-help" role="status">正在后台生成工具信息与描述…</p><p v-else-if="server.metadata_status==='failed'" class="mcp-dialog-help" role="status">{{server.metadata_error}}<el-button v-if="owns(server)&&server.user_id!=='0'" text @click="retryMetadata(server)">重新生成</el-button></p><div class="mcp-tags"><span v-for="tool in toolNames(server).slice(0,3)" :key="tool" :title="tool">{{tool}}</span><span v-if="!toolNames(server).length">暂无工具</span><small v-if="toolNames(server).length>3">+{{toolNames(server).length-3}}</small></div><footer class="resource-footer mcp-footer"><button @click="details=server"><svg class="p-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="6" rx="2"/><rect x="3" y="15" width="18" height="6" rx="2"/><path d="M7 6h.01M7 18h.01M15 6h3M15 18h3M7 9v6m10-6v6"/></svg>查看工具<span class="tool-count">{{toolNames(server).length}}</span></button><button title="编辑 MCP 服务" @click="openEditor(server)"><UiIcon name="gear"/>配置</button></footer></article><div v-if="!loading&&!visibleServers.length" class="resource-empty">{{loadError?'MCP 数据暂时无法读取':search||filter!=='all'?'没有匹配的服务':'暂无 MCP 服务，添加服务开始使用'}}</div></section><div v-if="!loading&&!loadError&&filteredServers.length" class="mcp-pagination"><span>共 {{filteredServers.length}} 个服务</span><el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="filteredServers.length" layout="prev, pager, next" background/></div>
<el-dialog v-model="dialog" :title="editing?'编辑 MCP 服务':'添加 MCP 服务'" width="600px" class="b4-dialog" append-to-body :close-on-click-modal="false" :close-on-press-escape="!saving&&!uploading" :show-close="!saving&&!uploading"><el-form label-position="top" :disabled="saving"><div class="mcp-mode"><button type="button" :class="{active:mode==='form'}" @click="mode='form'">连接信息</button><button type="button" :class="{active:mode==='json'}" @click="mode='json'">导入 JSON</button></div><el-form-item label="服务名称" required><el-input v-model="form.name" maxlength="50" show-word-limit placeholder="请输入 MCP 服务名称"/></el-form-item><template v-if="mode==='form'"><el-form-item label="服务 URL" required><el-input v-model="form.url" placeholder="https://example.com/mcp"/></el-form-item><el-form-item label="传输类型" required><el-select v-model="form.type" style="width:100%"><el-option value="sse" label="SSE"/><el-option value="streamable_http" label="Streamable HTTP"/><el-option value="websocket" label="WebSocket"/></el-select></el-form-item></template><template v-else><el-form-item label="mcpServers JSON" required><el-input v-model="form.json" type="textarea" class="code-input" :rows="10" spellcheck="false"/></el-form-item><el-button :disabled="saving" @click="applyImport">填入连接信息</el-button></template><div class="mcp-logo-field"><label>服务头像</label><img v-if="form.logo" :src="form.logo" alt="服务头像"><label class="mcp-logo-upload">{{uploading?'上传中…':'上传图片'}}<input type="file" accept="image/png,image/jpeg,image/webp" :disabled="uploading||saving" @change="uploadLogo"></label></div><p class="mcp-dialog-help">保存时会读取服务提供的工具，请确保地址可访问。需要 headers 的服务可通过 JSON 导入。</p><p v-if="formError" class="dialog-error" role="alert">{{formError}}</p></el-form><template #footer><el-button :disabled="saving||uploading" @click="dialog=false">取消</el-button><el-button type="primary" :loading="saving" :disabled="uploading" @click="saveServer">保存</el-button></template></el-dialog>
<el-dialog :model-value="!!details" :title="`${details?.server_name||'MCP'} · 工具`" width="760px" class="b4-dialog" append-to-body @close="details=undefined"><div v-if="details" class="mcp-tool-list"><el-collapse><el-collapse-item v-for="name in toolNames(details)" :key="name" :title="name" :name="name"><p>{{toolParams(details).find(tool=>tool.name===name)?.description||'暂无工具描述'}}</p><h4 v-if="toolParams(details).find(tool=>tool.name===name)?.input_schema">输入参数</h4><pre v-if="toolParams(details).find(tool=>tool.name===name)?.input_schema">{{JSON.stringify(toolParams(details).find(tool=>tool.name===name)?.input_schema,null,2)}}</pre></el-collapse-item></el-collapse><p v-if="!toolNames(details).length" class="mcp-dialog-help">此服务暂无工具信息。</p></div><template #footer><el-button @click="details=undefined">关闭</el-button></template></el-dialog>

</div></template>
<style scoped src="./mcp-catalog.css"></style>
