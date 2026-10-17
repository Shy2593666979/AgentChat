<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import * as monaco from 'monaco-editor';
import UiIcon from '../../components/UiIcon.vue';
import { getConfigAPI, updateConfigAPI } from '../../apis/configuration';
import { responseError } from '../../utils/resource-visuals';
const editorHost = ref<HTMLElement>(), baseline = ref(''), content = ref(''), loading = ref(false), saving = ref(false), loaded = ref(false), loadError = ref(''), saveError = ref('');
const language = ref('yaml'), dirty = computed(() => content.value !== baseline.value), languageLabel = computed(() => language.value === 'json' ? 'JSON' : 'YAML / 配置文本');
let editor: monaco.editor.IStandaloneCodeEditor | undefined, disposed = false, requestId = 0;
function destroyEditor() { const model = editor?.getModel(); editor?.dispose(); model?.dispose(); editor = undefined; }
async function loadConfig() { if (loading.value || saving.value)
    return; const id = ++requestId; loading.value = true; loadError.value = ''; saveError.value = ''; try {
    const response = await getConfigAPI();
    if (disposed || id !== requestId)
        return;
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '配置读取失败');
    const value = response.data.data;
    if (value == null || !['string', 'object'].includes(typeof value))
        throw new Error('未读取到有效的配置内容');
    baseline.value = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
    content.value = baseline.value;
    language.value = /^[\s]*[\[{]/.test(content.value) ? 'json' : 'yaml';
    loaded.value = true;
    await nextTick();
    if (disposed || !editorHost.value)
        return;
    destroyEditor();
    editor = monaco.editor.create(editorHost.value, { value: content.value, language: language.value, theme: 'vs', fontSize: 16, lineHeight: 26, fontFamily: 'Consolas, monospace', minimap: { enabled: false }, automaticLayout: true, scrollBeyondLastLine: false, padding: { top: 18, bottom: 18 }, tabSize: 2 });
    editor.onDidChangeModelContent(() => { content.value = editor?.getValue() || ''; });
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => saveConfig());
}
catch (error) {
    if (!disposed && id === requestId) {
        loaded.value = false;
        loadError.value = (error as any)?.response?.status === 404
            ? '当前服务未开放在线配置，请在后端配置文件中修改并重启服务。'
            : responseError(error, '配置读取失败，请重试');
    }
}
finally {
    if (!disposed && id === requestId)
        loading.value = false;
} }
async function saveConfig() { if (!editor || saving.value || loading.value || !loaded.value || !dirty.value)
    return; saveError.value = ''; const value = editor.getValue(); if (!value.trim()) {
    saveError.value = '配置内容不能为空';
    return;
} if (language.value === 'json') {
    try {
        JSON.parse(value);
    }
    catch (error) {
        saveError.value = responseError(error, 'JSON 格式错误');
        return;
    }
} saving.value = true; editor.updateOptions({ readOnly: true }); try {
    const data = new FormData();
    data.append('data', value);
    const response = await updateConfigAPI(data);
    if (response.data.status_code !== 200)
        throw new Error(response.data.status_message || '配置保存失败');
    baseline.value = value;
    ElMessage.success('配置已保存');
}
catch (error) {
    saveError.value = responseError(error, '配置保存失败');
}
finally {
    saving.value = false;
    editor?.updateOptions({ readOnly: false });
} }
function resetConfig() { if (saving.value)
    return; editor?.setValue(baseline.value); content.value = baseline.value; saveError.value = ''; }
async function copyConfig() { if (!loaded.value)
    return; try {
    await navigator.clipboard.writeText(content.value);
    ElMessage.success('配置已复制');
}
catch {
    ElMessage.error('复制失败，请在编辑器内选中并复制');
} }
onBeforeRouteLeave(async () => { if (saving.value)
    return false; if (!dirty.value)
    return true; try {
    await ElMessageBox.confirm('配置有未保存的修改，是否放弃？', '未保存的配置', { confirmButtonText: '放弃修改', cancelButtonText: '继续编辑' });
    return true;
}
catch {
    return false;
} });
function beforeUnload(event: BeforeUnloadEvent) { if (dirty.value) {
    event.preventDefault();
    event.returnValue = '';
} }
onMounted(() => { loadConfig(); window.addEventListener('beforeunload', beforeUnload); });
onBeforeUnmount(() => { disposed = true; requestId++; destroyEditor(); window.removeEventListener('beforeunload', beforeUnload); });
</script>
<template><div class="b3-page b4-page b4-configuration"><header class="data-heading"><div class="heading-copy"><h1>系统配置</h1><p>查看和编辑当前配置，确认后保存更改。</p></div></header><div v-if="loadError" class="error-banner" role="alert"><span>{{loadError}}</span><button :disabled="loading" @click="loadConfig">重新加载</button></div><div class="configuration-columns"><section class="data-surface configuration-panel" v-loading="loading"><header><h2>配置文件</h2><span class="configuration-format">{{loaded?languageLabel:'配置文本'}}</span></header><div class="configuration-editor"><div ref="editorHost" class="configuration-monaco" aria-label="系统配置编辑器"/><button v-if="loaded" class="copy-config" aria-label="复制配置" @click="copyConfig"><UiIcon name="copy"/></button><div v-if="!loaded&&!loading" class="config-unavailable"><UiIcon name="file"/><p>配置内容暂时无法读取</p><button @click="loadConfig">重新加载</button></div></div><footer class="configuration-status"><span>{{loading?'读取中…':!loaded?'未加载配置':saving?'保存中…':dirty?'有未保存的修改':'当前内容已保存'}}</span><span v-if="loaded">UTF-8 · {{language==='json'?'JSON':'YAML'}}</span></footer></section><aside class="data-surface configuration-notes"><h2><UiIcon name="info"/>注意事项</h2><div v-for="(note,index) in [{title:'配置格式',copy:'保持原有配置格式和字段结构。JSON 内容会在保存前检查语法，其他格式由服务处理。'},{title:'参数说明',copy:'根据实际需要修改配置项。确认参数含义与取值后再修改，保留其他配置内容。'},{title:'保存与恢复',copy:'点击确定提交修改；取消可恢复到最近一次读取或保存的内容。实际生效时间取决于服务的配置加载方式。'}]" :key="note.title" class="configuration-note"><span>{{index+1}}</span><div><h3>{{note.title}}</h3><p>{{note.copy}}</p></div></div></aside></div><p v-if="saveError" class="configuration-error" role="alert">{{saveError}}</p><footer v-if="loaded" class="configuration-actions"><el-button :disabled="saving||!dirty" @click="resetConfig">取消</el-button><el-button type="primary" :loading="saving" :disabled="loading||!loaded||!dirty" @click="saveConfig">确定</el-button></footer></div></template>
<style scoped src="./configuration.css"></style>
