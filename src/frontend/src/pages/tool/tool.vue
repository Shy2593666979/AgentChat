<script setup lang="ts">
import CatalogHeader from '../../components/CatalogHeader.vue'
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import UiIcon from '../../components/UiIcon.vue';
import ToolGlyph from '../../components/ToolGlyph.vue';
import { toolVisual } from '../../utils/tool-visuals';
import { responseError } from '../../utils/resource-visuals';
import { getAllToolsAPI, getOwnToolsAPI, createToolAPI, updateToolAPI, deleteToolAPI, type ToolResponse } from '../../apis/tool';
import { useUserStore } from '../../store/user';
const store = useUserStore();
const tools = ref<ToolResponse[]>([]), ownIds = ref(new Set<string>()), loading = ref(false), loadError = ref('');
const activeTab = ref('all'), search = ref(''), dialog = ref(false), saving = ref(false), formError = ref(''), deleting = ref('');
const editing = ref<ToolResponse>(), detail = ref<ToolResponse>();
const blankSchema = JSON.stringify({ openapi: '3.1.0', info: { title: 'My API', version: '1.0.0' }, servers: [{ url: 'https://api.example.com' }], paths: {} }, null, 2);
const form = reactive({ display_name: '', description: '', logo_url: '', schema: blankSchema, auth: '' as '' | 'bearer' | 'basic', token: '' });
const owns = (tool: ToolResponse) => tool.user_id !== '0' && (tool.user_id === store.userInfo?.id || ownIds.value.has(tool.tool_id));
const canManage = (tool: ToolResponse) => tool.user_id === '0' || owns(tool) || store.userInfo?.id === '1';
const builtinEditing = computed(() => !!editing.value && !editing.value.is_user_defined && !editing.value.openapi_schema);
const ownCount = computed(() => tools.value.filter(owns).length);
const visibleTools = computed(() => tools.value.filter(tool => (activeTab.value === 'all' || owns(tool)) && [tool.display_name, tool.name, tool.description].join(' ').toLowerCase().includes(search.value.trim().toLowerCase())));
const visual = (tool: ToolResponse) => toolVisual([tool.display_name, tool.name].join(' '));
const operations = computed(() => { try {
    const schema = JSON.parse(form.schema);
    return Object.entries(schema.paths || {}).flatMap(([path, methods]: [
        string,
        any
    ]) => Object.entries(methods || {}).filter(([method]) => ['get', 'post', 'put', 'patch', 'delete', 'head', 'options'].includes(method)).map(([method, data]: [
        string,
        any
    ]) => ({ path, method: method.toUpperCase(), name: data.summary || data.operationId || '' })));
}
catch {
    return [];
} });
async function fetchTools() { if (loading.value)
    return; loading.value = true; loadError.value = ''; try {
    const results = await Promise.allSettled([getAllToolsAPI(), getOwnToolsAPI()]);
    const all = results[0], own = results[1];
    if (all.status === 'rejected')
        throw all.reason;
    if (all.value.data.status_code !== 200)
        throw new Error(all.value.data.status_message || '工具列表加载失败');
    tools.value = all.value.data.data || [];
    if (own.status === 'fulfilled' && own.value.data.status_code === 200)
        ownIds.value = new Set((own.value.data.data || []).map(tool => tool.tool_id));
}
catch (error) {
    loadError.value = responseError(error, '工具列表加载失败，请重试');
}
finally {
    loading.value = false;
} }
function openEditor(tool?: ToolResponse, duplicate = false) {
    if (saving.value) return;
    editing.value = duplicate ? undefined : tool;
    formError.value = '';
    Object.assign(form, { display_name: duplicate ? `${tool?.display_name || ''} 副本` : tool?.display_name || '', description: tool?.description || '', logo_url: tool?.logo_url || '', schema: tool?.openapi_schema ? JSON.stringify(tool.openapi_schema, null, 2) : blankSchema, auth: duplicate ? '' : tool?.auth_config?.type || '', token: duplicate ? '' : tool?.auth_config?.token || '' });
    dialog.value = true;
}
async function saveTool() { if (saving.value)
    return; formError.value = ''; if (!form.display_name.trim()) {
    formError.value = '请输入工具名称';
    return;
} if (form.auth && !form.token.trim()) {
    formError.value = '请输入鉴权凭据';
    return;
} let schema: any; if (!builtinEditing.value) try {
    schema = JSON.parse(form.schema);
    if (!schema || Array.isArray(schema) || typeof schema !== 'object' || !schema.openapi || !schema.info || !schema.paths)
        throw new Error();
}
catch {
    formError.value = '请输入有效的 OpenAPI JSON，包含 openapi、info 和 paths';
    return;
} saving.value = true; try {
    const data = { display_name: form.display_name.trim(), description: form.description.trim(), logo_url: form.logo_url, openapi_schema: schema, auth_config: form.auth ? { type: form.auth, token: form.token.trim() } : null };
    const updateData = builtinEditing.value ? { display_name: data.display_name, description: data.description } : data;
    const response = editing.value ? await updateToolAPI({ tool_id: editing.value.tool_id, ...updateData }) : await createToolAPI(data);
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '保存失败');
    dialog.value = false;
    ElMessage.success('工具已保存');
    await fetchTools();
}
catch (error) {
    formError.value = responseError(error, '工具保存失败');
}
finally {
    saving.value = false;
} }
async function removeTool(tool: ToolResponse) { if (deleting.value || !canManage(tool))
    return; try {
    await ElMessageBox.confirm(`确定删除工具“${tool.display_name}”？`, '删除工具', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' });
    deleting.value = tool.tool_id;
    const response = await deleteToolAPI({ tool_id: tool.tool_id });
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '删除失败');
    ElMessage.success('工具已删除');
    await fetchTools();
}
catch (error) {
    if (error !== 'cancel' && error !== 'close')
        ElMessage.error(responseError(error, '删除失败'));
}
finally {
    deleting.value = '';
} }
onMounted(fetchTools);
</script>
<template><div class="b3-page b4-page b4-tools catalog-page"><CatalogHeader title="工具" subtitle="为智能体连接实际行动能力" description="连接搜索、文档处理与业务工具，让 AI 完成更多任务"><template #actions><button class="primary-button" @click="openEditor()"><UiIcon name="plus-circle"/>创建工具</button></template></CatalogHeader>
<div class="resource-toolbar"><label class="search-field"><UiIcon name="search"/><input v-model="search" type="search" placeholder="搜索工具名称、功能或描述…" aria-label="搜索工具"></label><div class="resource-tabs" role="group" aria-label="工具分类"><button v-for="tab in [{id:'all',label:'全部工具',count:tools.length},{id:'own',label:'我的工具',count:ownCount}]" :key="tab.id" :class="{active:activeTab===tab.id}" :aria-pressed="activeTab===tab.id" @click="activeTab=tab.id">{{tab.label}}<span>{{loadError&&!tools.length?'—':tab.count}}</span></button></div></div>
<div v-if="loadError" class="error-banner" role="alert"><span>{{loadError}}</span><button @click="fetchTools">重新加载</button></div>
<section class="resource-grid tools-grid" v-loading="loading" :aria-busy="loading"><article v-for="tool in visibleTools" :key="tool.tool_id" class="resource-card tool-card"><div class="resource-main"><div class="tool-art"><ToolGlyph :kind="visual(tool).kind" :theme="visual(tool).theme"/></div><div class="resource-copy"><div class="resource-title"><h2 :title="tool.display_name">{{tool.display_name||tool.name}}</h2><span class="resource-tag" :class="visual(tool).theme">{{visual(tool).tag}}</span></div><p :title="tool.description">{{tool.description||'暂未填写描述'}}</p></div><el-dropdown class="resource-more" trigger="click" popper-class="tool-actions-popover"><button class="more-button" :aria-label="`${tool.display_name}的更多操作`"><UiIcon name="more"/></button><template #dropdown><el-dropdown-menu><el-dropdown-item v-if="canManage(tool)" @click="openEditor(tool)"><UiIcon name="edit"/>编辑</el-dropdown-item><el-dropdown-item @click="openEditor(tool,true)"><UiIcon name="copy"/>复制</el-dropdown-item><el-dropdown-item v-if="canManage(tool)" class="tool-delete-action" :disabled="!!deleting" @click="removeTool(tool)"><UiIcon name="trash"/>删除</el-dropdown-item></el-dropdown-menu></template></el-dropdown></div><footer class="resource-footer"><button @click="detail=tool"><UiIcon name="eye"/>查看详情</button><button v-if="canManage(tool)" @click="openEditor(tool)"><UiIcon name="edit"/>编辑</button><button v-else title="复制为自己的工具后编辑" @click="openEditor(tool,true)"><UiIcon name="copy"/>复制</button></footer></article><div v-if="!loading&&!visibleTools.length" class="resource-empty">{{loadError?'工具数据暂时无法读取':search?'没有匹配的工具，试试其他关键词':activeTab==='own'?'还没有创建工具':'暂无可用工具'}}</div></section>
<el-dialog v-model="dialog" :title="editing?'编辑工具':'创建工具'" width="720px" class="b4-dialog" append-to-body :close-on-click-modal="false" :close-on-press-escape="!saving" :show-close="!saving"><el-form label-position="top" :disabled="saving"><div class="logo-field"><ToolGlyph :kind="toolVisual(form.display_name).kind" :theme="toolVisual(form.display_name).theme"/><div><strong>工具图标</strong><p>根据工具名称匹配功能图标</p></div></div><el-form-item label="工具名称" required><el-input v-model="form.display_name" maxlength="50" show-word-limit placeholder="请输入工具名称"/></el-form-item><el-form-item label="工具描述"><el-input v-model="form.description" type="textarea" :rows="3" maxlength="500" show-word-limit placeholder="说明功能、场景和输入输出"/></el-form-item><p v-if="builtinEditing" class="mcp-dialog-help">此工具使用内置实现，可修改名称和描述。</p><el-form-item v-if="!builtinEditing" label="OpenAPI JSON" required><el-input v-model="form.schema" class="code-input" type="textarea" :rows="10" spellcheck="false"/></el-form-item><div v-if="operations.length" class="operation-preview"><span v-for="(operation,index) in operations" :key="index"><b>{{operation.method}}</b>{{operation.path}}<small>{{operation.name}}</small></span></div><div v-if="!builtinEditing" class="auth-fields"><el-form-item label="鉴权方式"><el-select v-model="form.auth"><el-option value="" label="无需鉴权"/><el-option value="bearer" label="Bearer Token"/><el-option value="basic" label="Basic"/></el-select></el-form-item><el-form-item v-if="form.auth" :label="form.auth==='basic'?'Basic 凭据（Base64）':'Token'" required><el-input v-model="form.token" type="password" show-password autocomplete="off"/></el-form-item></div><p v-if="formError" class="dialog-error" role="alert">{{formError}}</p></el-form><template #footer><el-button :disabled="saving" @click="dialog=false">取消</el-button><el-button type="primary" :loading="saving" @click="saveTool">{{editing?'保存':'创建'}}</el-button></template></el-dialog>
<el-dialog :model-value="!!detail" :title="detail?.display_name||'工具详情'" width="640px" class="b4-dialog" append-to-body @close="detail=undefined"><div v-if="detail" class="tool-detail-heading"><ToolGlyph :kind="visual(detail).kind" :theme="visual(detail).theme"/><span class="tool-detail-tag" :class="visual(detail).theme">{{visual(detail).tag}}</span></div><p class="tool-description">{{detail?.description||'暂未填写描述'}}</p><dl class="tool-detail-meta"><dt>工具标识</dt><dd>{{detail?.name||'—'}}</dd><dt>来源</dt><dd>{{detail?.user_id==='0'?'内置工具':'自定义工具'}}</dd></dl><h3 v-if="detail?.openapi_schema">OpenAPI 配置</h3><pre v-if="detail?.openapi_schema" class="schema-preview">{{JSON.stringify(detail.openapi_schema,null,2)}}</pre><template #footer><el-button @click="detail=undefined">关闭</el-button></template></el-dialog>
</div></template>
<style scoped src="./tool-catalog.css"></style>
