<script setup lang="ts">
import CatalogHeader from '../../components/CatalogHeader.vue'
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter, onBeforeRouteLeave, onBeforeRouteUpdate } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import * as monaco from 'monaco-editor';
import UiIcon from '../../components/UiIcon.vue';
import { skillTags } from '../../utils/skill-tags';
import FolderGlyph from '../../components/FolderGlyph.vue';
import SkillGlyph from '../../components/SkillGlyph.vue';
import { resourceVisual, responseError } from '../../utils/resource-visuals';
import { formatDataDate } from '../../utils/data-pages';
import { getAgentSkillsAPI, createAgentSkillAPI, updateAgentSkillAPI, deleteAgentSkillAPI, updateAgentSkillFileAPI, addAgentSkillFileAPI, uploadAgentSkillFileAPI, deleteAgentSkillFileAPI, type AgentSkill, type AgentSkillFile, type AgentSkillFolder } from '../../apis/agent-skill';
const route = useRoute(), router = useRouter();

const highlighted = ref('');
const listRoute = { path: '/agent-skill' };
function openSkill(skill: AgentSkill) { highlighted.value=skill.id; router.push({path:'/agent-skill',query:{skill:skill.id}}) }
const skills = ref<AgentSkill[]>([]), loading = ref(false), loadError = ref(''), search = ref(''), source = ref('all'), sort = ref('updated');
const current = ref<AgentSkill>(), selected = ref<AgentSkillFile>(), editorHost = ref<HTMLElement>(), content = ref(''), baseline = ref(''), fullscreen = ref(false), collapsed = ref(new Set<string>());
const creating = ref(false), createDialog = ref(false), createError = ref(''), saving = ref(false), saveError = ref(''), deleting = ref('');
const editingSkill = ref<AgentSkill>();
async function openSkillInfo(skill?: AgentSkill) { if (skill && !await discardChanges()) return; editingSkill.value = skill; createForm.name = skill?.name || ''; createForm.description = skill?.description || ''; createError.value = ''; createDialog.value = true; }
const createForm = reactive({ name: '', description: '' });
const addDialog = ref(false), adding = ref(false), addError = ref(''), upload = ref<File>(), addForm = reactive({ path: '', name: '' });
let editor: monaco.editor.IStandaloneCodeEditor | undefined, disposed = false, requestId = 0;
const skillId = computed(() => typeof route.query.skill === 'string' ? route.query.skill : '');
const detailMode = computed(() => !!skillId.value), dirty = computed(() => content.value !== baseline.value);
const currentDescription = computed(() => current.value?.description || '');
const visual = (skill: AgentSkill) => resourceVisual(skill.name, true);
function flatFiles(items: Array<AgentSkillFile | AgentSkillFolder>): AgentSkillFile[] { return items.flatMap(item => item.type === 'file' ? [item] : flatFiles(item.folder || [])); }
const visibleSkills = computed(() => skills.value.filter(skill => [skill.name, skill.description, ...skillTags(skill.name)].join(' ').toLowerCase().includes(search.value.trim().toLowerCase()) && (source.value === 'all' || (source.value === 'builtin') === (skill.user_id === '0'))).sort((a, b) => sort.value === 'name' ? a.name.localeCompare(b.name, 'zh-CN') : (Date.parse(b.update_time || b.create_time) || 0) - (Date.parse(a.update_time || a.create_time) || 0)));
const folders = computed(() => current.value?.folder?.folder.filter((item): item is AgentSkillFolder => item.type === 'folder' && ['scripts', 'reference'].includes(item.name)) || []);
const tree = computed(() => { const rows: Array<{
    item: AgentSkillFile | AgentSkillFolder;
    depth: number;
    parent: string;
}> = []; function walk(items: Array<AgentSkillFile | AgentSkillFolder>, depth: number, parent: string) { for (const item of items) {
    rows.push({ item, depth, parent });
    if (item.type === 'folder' && !collapsed.value.has(item.path))
        walk(item.folder || [], depth + 1, item.path);
} } if (current.value?.folder && !collapsed.value.has(current.value.folder.path))
    walk(current.value.folder.folder || [], 1, current.value.folder.path); return rows; });
const editable = computed(() => !!selected.value && current.value?.folder?.folder.some(item => item.path === selected.value?.path || (item.type === 'folder' && ['scripts', 'reference'].includes(item.name) && item.folder?.some(file => file.path === selected.value?.path))));
const language = computed(() => ({ md: 'markdown', py: 'python', js: 'javascript', ts: 'typescript', json: 'json', yml: 'yaml', yaml: 'yaml', html: 'html', css: 'css', sh: 'shell', txt: 'plaintext' } as Record<string, string>)[selected.value?.name.split('.').pop()?.toLowerCase() || ''] || 'plaintext');
function destroyEditor() { const model = editor?.getModel(); editor?.dispose(); model?.dispose(); editor = undefined; }
async function mountEditor() { destroyEditor(); await nextTick(); if (disposed || !editorHost.value || !selected.value)
    return;
    monaco.editor.defineTheme('agentchat-skill', {base:'vs',inherit:true,rules:[{token:'',foreground:'273551'},{token:'keyword',foreground:'0864FF',fontStyle:'bold'},{token:'comment',foreground:'8C9BB4'},{token:'string',foreground:'009B75'},{token:'number',foreground:'1767FF'}],colors:{'editor.foreground':'#273551','editor.background':'#FFFFFF','editorLineNumber.foreground':'#98A6BF','editorLineNumber.activeForeground':'#6E83A9','editor.lineHighlightBackground':'#FFFFFF','editor.lineHighlightBorder':'#FFFFFF','editor.selectionBackground':'#E4EFFF'}});
    editor = monaco.editor.create(editorHost.value, { value: content.value, language: language.value, theme: 'agentchat-skill', lineDecorationsWidth: 28, wordWrap: 'on', readOnly: !editable.value, minimap: { enabled: false }, automaticLayout: true, fontSize: 16, lineHeight: 22, fontFamily: "Consolas, 'AgentChat Sans SC', 'Microsoft YaHei', monospace", scrollBeyondLastLine: false, padding: { top: 12, bottom: 16 }, tabSize: 2 }); editor.onDidChangeModelContent(() => { content.value = editor?.getValue() || ''; }); editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => saveFile()); }
function activate(skill?: AgentSkill) { current.value = skill; selected.value = undefined; content.value = ''; baseline.value = ''; collapsed.value = new Set(); saveError.value = ''; fullscreen.value = false; destroyEditor(); if (skill) {

    const files = flatFiles(skill.folder?.folder || []);
    const file = files.find(file => file.name === 'SKILL.md') || files[0];
    if (file)
        setFile(file);
} }
function setFile(file: AgentSkillFile) { selected.value = file; content.value = file.content || ''; baseline.value = content.value; saveError.value = ''; mountEditor(); }
async function discardChanges() { if (saving.value || adding.value)
    return false; if (!dirty.value)
    return true; try {
    await ElMessageBox.confirm('当前文件有未保存的修改，是否放弃？', '未保存的修改', { type: 'warning', confirmButtonText: '放弃修改', cancelButtonText: '继续编辑' });
    return true;
}
catch {
    return false;
} }
async function chooseFile(file: AgentSkillFile) { if (selected.value?.path === file.path)
    return; if (await discardChanges())
    setFile(file); }
function toggleFolder(path: string) { const next = new Set(collapsed.value); next.has(path) ? next.delete(path) : next.add(path); collapsed.value = next; }
async function fetchSkills() { const id = ++requestId;

    loading.value = true; loadError.value = ''; try {
    const response = await getAgentSkillsAPI();
    if (disposed || id !== requestId)
        return;
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || 'Skill 列表加载失败');
    skills.value = response.data.data || [];
    if (skillId.value && current.value?.id !== skillId.value)
        activate(skills.value.find(skill => skill.id === skillId.value));
}
catch (error) {
    if (id === requestId && !disposed)
        loadError.value = responseError(error, 'Skill 列表加载失败，请重试');
}
finally {
    if (id === requestId && !disposed)
        loading.value = false;
} }
async function createSkill() { if (creating.value)
    return; createError.value = ''; const name = createForm.name.trim(), description = createForm.description.trim(); if (name.length < 2 || name.length > 50) {
    createError.value = '名称长度为 2—50 个字符';
    return;
} if (!description || description.length > 500) {
    createError.value = '请填写 500 字符以内的 Skill 描述';
    return;
} creating.value = true; try {


    const response = editingSkill.value ? await updateAgentSkillAPI({ agent_skill_id: editingSkill.value.id, name, description }) : await createAgentSkillAPI({ name, description });
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '创建失败');
    if (editingSkill.value && response.data.data) updateCurrent(response.data.data, selected.value?.path);
    createDialog.value = false;
    createForm.name = '';
    createForm.description = '';
    ElMessage.success(editingSkill.value ? 'Skill 已保存' : 'Skill 已创建');
    await fetchSkills();
    if (response.data.data?.id)
        router.push({ path: '/agent-skill', query: { skill: response.data.data.id } });
}
catch (error) {
    createError.value = responseError(error, 'Skill 创建失败');
}
finally {
    creating.value = false;
} }
async function deleteSkill(skill: AgentSkill) { if (deleting.value)
    return; try {
    await ElMessageBox.confirm(`确定删除 Skill“${skill.name}”及其文件？`, '删除 Skill', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' });
    deleting.value = skill.id;

    const response = await deleteAgentSkillAPI({ agent_skill_id: skill.id });
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '删除失败');
    ElMessage.success('Skill 已删除');
    await fetchSkills();
}
catch (error) {
    if (error !== 'cancel' && error !== 'close')
        ElMessage.error(responseError(error, '删除失败'));
}
finally {
    deleting.value = '';
} }
function updateCurrent(skill: AgentSkill, preferred?: string) { const index = skills.value.findIndex(item => item.id === skill.id); if (index >= 0)
    skills.value[index] = skill; current.value = skill; const file = flatFiles(skill.folder?.folder || []).find(file => file.path === (preferred || selected.value?.path)); if (file)
    setFile(file);
else {
    selected.value = undefined;
    content.value = '';
    baseline.value = '';
    destroyEditor();
} }
async function saveFile() { if (!current.value || !selected.value || !editable.value || saving.value || !dirty.value)
    return; saving.value = true; editor?.updateOptions({ readOnly: true }); saveError.value = ''; const skill = current.value, file = selected.value, value = content.value; try {

    const response = await updateAgentSkillFileAPI({ agent_skill_id: skill.id, path: file.path, content: value });
    if (response.data.status_code !== 200 || !response.data.data)
        throw new Error(response.data.status_message || '保存失败');
    if (!disposed && current.value?.id === skill.id) {
        updateCurrent(response.data.data, file.path);
        ElMessage.success('文件已保存');
    }
}
catch (error) {
    saveError.value = responseError(error, '文件保存失败');
}
finally {
    saving.value = false;
    editor?.updateOptions({ readOnly: !editable.value });
} }
async function openAdd(path?: string) { if (!await discardChanges())
    return; if (dirty.value && selected.value)
    setFile(selected.value); addForm.path = path || folders.value[0]?.path || ''; addForm.name = ''; upload.value = undefined; addError.value = ''; addDialog.value = true; }
function pickUpload(event: Event) { const input = event.target as HTMLInputElement; upload.value = input.files?.[0]; input.value = ''; if (upload.value)
    addForm.name = upload.value.name; }
async function addFile() { if (adding.value || !current.value)
    return; addError.value = ''; const name = addForm.name.trim(); if (!addForm.path || !name || /[\\/]/.test(name) || ['.', '..'].includes(name)) {
    addError.value = '请选择目录，并输入不含路径分隔符的文件名';
    return;
} const folder = folders.value.find(item => item.path === addForm.path); if (folder?.folder.some(item => item.name === name)) {
    addError.value = '此目录已存在同名文件';
    return;
} if (upload.value && upload.value.size > 2 * 1024 * 1024) {
    addError.value = '文本文件不能超过 2MB';
    return;
} adding.value = true; try {

    let response;
    if (upload.value) {
        try {
            new TextDecoder('utf-8', { fatal: true }).decode(await upload.value.arrayBuffer());
        }
        catch {
            throw new Error('请上传 UTF-8 编码的文本文件');
        }
        const data = new FormData();
        data.append('agent_skill_id', current.value.id);
        data.append('path', addForm.path);
        data.append('file', upload.value, name);
        response = await uploadAgentSkillFileAPI(data);
    }
    else
        response = await addAgentSkillFileAPI({ agent_skill_id: current.value.id, path: addForm.path, name });
    if (response.data.status_code !== 200 || !response.data.data)
        throw new Error(response.data.status_message || '添加失败');
    updateCurrent(response.data.data, addForm.path.replace(/\/$/, '') + '/' + name);
    addDialog.value = false;
    collapsed.value.delete(addForm.path);
    ElMessage.success('文件已添加');
}
catch (error) {
    addError.value = responseError(error, '添加文件失败');
}
finally {
    adding.value = false;
} }
async function deleteFile(file: AgentSkillFile, parent: string) { if (deleting.value || !current.value || !await discardChanges())
    return; try {
    await ElMessageBox.confirm(`确定删除文件“${file.name}”？`, '删除文件', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' });
    deleting.value = file.path;

    const response = await deleteAgentSkillFileAPI({ agent_skill_id: current.value.id, path: parent, name: file.name });
    if (response.data.status_code !== 200 || !response.data.data)
        throw new Error(response.data.status_message || '删除失败');
    updateCurrent(response.data.data);
    ElMessage.success('文件已删除');
}
catch (error) {
    if (error !== 'cancel' && error !== 'close')
        ElMessage.error(responseError(error, '删除失败'));
}
finally {
    deleting.value = '';
} }
watch(skillId, id => { if (!id)
    activate();
else if (skills.value.length)
    activate(skills.value.find(skill => skill.id === id)); });

onBeforeRouteLeave(discardChanges);
onBeforeRouteUpdate((to, from) => to.query.skill !== from.query.skill ? discardChanges() : true);
function beforeUnload(event: BeforeUnloadEvent) { if (dirty.value) {
    event.preventDefault();
    event.returnValue = '';
} }
onMounted(() => { fetchSkills(); window.addEventListener('beforeunload', beforeUnload); });
onBeforeUnmount(() => { disposed = true; requestId++; destroyEditor(); window.removeEventListener('beforeunload', beforeUnload); });
</script>
<template>
<div class="b3-page b4-page b4-skills" :class="{'skill-detail-page':detailMode,'catalog-page':!detailMode}">
<template v-if="!detailMode"><CatalogHeader title="Skill" subtitle="将工作方法沉淀为可复用技能" description="管理技能说明、脚本和参考资料，构建可复用的工作流程"><template #actions><button class="primary-button" @click="openSkillInfo()"><UiIcon name="plus-circle"/>创建 Skill</button></template></CatalogHeader><div class="resource-toolbar"><label class="search-field"><UiIcon name="search"/><input v-model="search" type="search" placeholder="搜索 Skill 名称、描述或标签…" aria-label="搜索 Skill"></label><el-popover trigger="click" placement="bottom-end" :width="260"><template #reference><el-button class="skill-filter" :class="{filtered:source!=='all'||sort!=='updated'}"><UiIcon name="settings"/>筛选</el-button></template><div class="skill-filter-form"><label>来源<el-select v-model="source" class="catalog-select"><el-option value="all" label="全部 Skill"/><el-option value="builtin" label="内置技能"/><el-option value="custom" label="自定义技能"/></el-select></label><label>排序<el-select v-model="sort" class="catalog-select"><el-option value="updated" label="最近更新"/><el-option value="name" label="名称排序"/></el-select></label><el-button @click="source='all';sort='updated'">重置筛选</el-button></div></el-popover></div></template>
<div v-if="loadError" class="error-banner" role="alert"><span>{{loadError}}</span><button @click="fetchSkills">重新加载</button></div>
<section v-if="!detailMode" class="resource-grid skill-grid" v-loading="loading"><article v-for="skill in visibleSkills" :key="skill.id" class="resource-card skill-card" :class="{selected:highlighted===skill.id}"><span v-if="highlighted===skill.id" class="skill-selected" aria-label="当前选择的技能"><UiIcon name="check"/></span><div class="resource-main"><SkillGlyph :kind="visual(skill).kind" :theme="visual(skill).theme"/><div class="resource-copy"><h2 :title="skill.name">{{skill.name}}</h2><p :title="skill.description">{{skill.description||'暂未填写描述'}}</p><div class="skill-tags"><span v-for="tag in skillTags(skill.name)" :key="tag">{{tag}}</span></div></div><el-dropdown class="resource-more" trigger="click"><button class="more-button" :aria-label="`${skill.name}的更多操作`"><UiIcon name="more"/></button><template #dropdown><el-dropdown-menu><el-dropdown-item @click="openSkillInfo(skill)"><UiIcon name="edit"/><span>编辑信息</span></el-dropdown-item><el-dropdown-item :disabled="!!deleting" @click="deleteSkill(skill)" class="dropdown-danger-action"><UiIcon name="trash"/><span>删除 Skill</span></el-dropdown-item></el-dropdown-menu></template></el-dropdown></div><div class="skill-meta"><span><UiIcon name="file"/>{{flatFiles(skill.folder?.folder||[]).length}} 个文件</span><span :title="formatDataDate(skill.update_time||skill.create_time)"><UiIcon name="clock"/>{{formatDataDate(skill.update_time||skill.create_time,false)}} 更新</span></div><button class="skill-open" @click="openSkill(skill)"><UiIcon :name="skill.user_id==='0'?'eye':'paperclip'"/>{{skill.user_id==='0'?'查看详情':'查看与编辑'}}</button></article><div v-if="!loading&&!visibleSkills.length" class="resource-empty">{{loadError?'Skill 数据暂时无法读取':search||source!=='all'?'没有匹配的 Skill':'还没有 Skill，创建一个来沉淀工作方法'}}</div></section>
<template v-else-if="current"><header class="skill-detail-heading"><h1>{{current.name}}</h1><p>{{currentDescription}}</p><div class="skill-detail-actions"><el-button class="skill-return-button" @click="router.push(listRoute)"><UiIcon name="arrow-left"/>返回 Skill</el-button><el-button :disabled="saving" @click="openSkillInfo(current)"><UiIcon name="edit"/>编辑信息</el-button><button  class="primary-button" :disabled="!folders.length||saving" :title="!folders.length?'暂无可添加文件的目录':''" @click="openAdd()"><UiIcon name="plus-circle"/>添加文件</button><el-button  :loading="saving" :disabled="!dirty||!editable" @click="saveFile"><UiIcon name="save"/>保存</el-button></div></header><section class="skill-summary"><SkillGlyph :kind="visual(current).kind" :theme="visual(current).theme"/><div><h2>{{current.name}}<span>Skill</span></h2><p>{{currentDescription}}</p><div class="skill-tags"><span v-for="tag in skillTags(current.name,true)" :key="tag">{{tag}}</span></div></div></section><p v-if="saveError" class="error-banner" role="alert">{{saveError}}</p><section class="skill-editor" :class="{fullscreen}"><aside class="skill-tree"><header><h2>文件</h2><button  class="tree-add" :disabled="!folders.length||saving" aria-label="添加文件" @click="openAdd()"><UiIcon name="plus"/></button></header><button class="tree-folder root-folder" @click="toggleFolder(current.folder.path)"><UiIcon name="chevron-right" :class="{expanded:!collapsed.has(current.folder.path)}"/><FolderGlyph class="tree-folder-icon"/><strong>{{current.folder.name||current.name}}</strong></button><div v-for="row in tree" :key="row.item.path" class="tree-row" :class="{selected:selected?.path===row.item.path}" :style="{paddingLeft:`${row.depth*18+36}px`}"><button class="tree-item" :title="row.item.name" @click="row.item.type==='file'?chooseFile(row.item):toggleFolder(row.item.path)"><UiIcon v-if="row.item.type==='folder'" name="chevron-right" :class="{expanded:!collapsed.has(row.item.path)}"/><UiIcon v-if="row.item.type==='file'" name="file"/><FolderGlyph v-else class="tree-folder-icon"/><span>{{row.item.name}}</span></button><button v-if="row.item.type==='folder'&&folders.some(folder=>folder.path===row.item.path)" class="tree-action" aria-label="在此目录添加文件" :disabled="saving" @click="openAdd(row.item.path)"><UiIcon name="plus"/></button><button v-if="row.item.type==='file'&&folders.some(folder=>folder.path===row.parent)" class="tree-action danger" :aria-label="`删除${row.item.name}`" :disabled="!!deleting||saving" @click="deleteFile(row.item,row.parent)"><UiIcon name="trash"/></button></div></aside><div class="skill-code"><header><span class="file-tab"><UiIcon name="file"/>{{selected?.name||'未选择文件'}}</span><button :aria-label="fullscreen?'退出放大编辑器':'放大编辑器'" @click="fullscreen=!fullscreen"><UiIcon :name="fullscreen?'close':'expand'"/></button></header><div v-if="selected" ref="editorHost" class="skill-monaco" aria-label="Skill 文件编辑器"/><div v-else class="skill-editor-empty">选择一个文件查看内容</div><footer class="editor-status"><span :class="{unsaved:dirty}"><UiIcon :name="dirty?'clock':'check'"/>{{saving?'保存中…':dirty?'有未保存的修改':'已保存'}}<span v-if="!dirty">· {{formatDataDate(current.update_time||current.create_time)}}</span></span><span>UTF-8 <i/>{{language==='markdown'?'Markdown':language}}</span></footer></div></section></template>
<div v-else-if="detailMode" class="resource-empty" v-loading="loading">{{loading?'加载 Skill…':loadError?'Skill 数据暂时无法读取':'未找到此 Skill'}}<el-button v-if="!loading" @click="router.push('/agent-skill')">返回 Skill 列表</el-button></div>
<el-dialog v-model="createDialog" :title="editingSkill ? '编辑 Skill' : '创建 Skill'" width="520px" class="b4-dialog" append-to-body :close-on-click-modal="false" :close-on-press-escape="!creating" :show-close="!creating"><el-form label-position="top" :disabled="creating"><el-form-item label="Skill 名称" required><el-input v-model="createForm.name" maxlength="50" show-word-limit placeholder="请输入 Skill 名称"/></el-form-item><el-form-item label="Skill 描述" required><el-input v-model="createForm.description" maxlength="500" show-word-limit type="textarea" :rows="4" placeholder="描述功能、场景和使用方式"/></el-form-item><p class="skill-create-help">创建后可在文件编辑器中编写 SKILL.md，并添加脚本和参考资料。</p><p v-if="createError" class="dialog-error" role="alert">{{createError}}</p></el-form><template #footer><el-button :disabled="creating" @click="createDialog=false">取消</el-button><el-button type="primary" :loading="creating" @click="createSkill">{{ editingSkill ? '保存' : '创建' }}</el-button></template></el-dialog>
<el-dialog v-model="addDialog" title="添加文件" width="520px" class="b4-dialog" append-to-body :close-on-click-modal="false" :close-on-press-escape="!adding" :show-close="!adding"><el-form label-position="top" :disabled="adding"><el-form-item label="目录" required><el-select v-model="addForm.path" style="width:100%"><el-option v-for="folder in folders" :key="folder.path" :label="folder.name" :value="folder.path"><span class="dropdown-option-row"><FolderGlyph class="dropdown-option-logo"/><span>{{folder.name}}</span></span></el-option></el-select></el-form-item><el-form-item label="文件名" required><el-input v-model="addForm.name" placeholder="例如 prompts.md 或 analyze.py"/></el-form-item><label class="skill-upload">{{upload?'已选择：'+upload.name:'选择 UTF-8 文本文件上传（可选，最大 2MB）'}}<input type="file" :disabled="adding" @change="pickUpload"></label><button v-if="upload" type="button" class="clear-upload" :disabled="adding" @click="upload=undefined">清除上传文件</button><p v-if="addError" class="dialog-error" role="alert">{{addError}}</p></el-form><template #footer><el-button :disabled="adding" @click="addDialog=false">取消</el-button><el-button type="primary" :loading="adding" @click="addFile">添加</el-button></template></el-dialog>
</div></template>
<style scoped src="./skill-catalog.css"></style>
