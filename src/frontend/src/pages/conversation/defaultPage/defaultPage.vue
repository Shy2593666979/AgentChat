<script setup lang="ts">
import AgentIdentity from "../../../components/AgentIdentity.vue";
import ChatAttachmentCard from "../../../components/ChatAttachmentCard.vue";
import type { ChatAttachment } from "../../../type";
import { computed, inject, nextTick, onBeforeUnmount, ref, watch, type Ref } from 'vue';
import UiIcon from '../../../components/UiIcon.vue';
import CapabilityIcon from '../../../components/CapabilityIcon.vue';
import ResourceGlyph from '../../../components/ResourceGlyph.vue';
import { uploadFileAPI } from '../../../apis/tool';
import type { AgentResponse } from '../../../apis/agent';
import { isSendKey } from '../../../utils/chat-ui';
import { fitComposer } from '../../../utils/chat-ui';
import { responseError } from '../../../utils/resource-visuals';

let disposed = false;
onBeforeUnmount(()=>disposed=true);
const pendingAttachment = ref<ChatAttachment>();
const draft = ref(''), uploading = ref(false), uploadError = ref('');
const requestConversation = inject<(message?: string, picker?: boolean) => Promise<void>>('requestConversation', async () => { });
const agents = inject<Ref<AgentResponse[]>>('conversationAgents', ref([])), agentsLoading = inject<Ref<boolean>>('conversationAgentsLoading', ref(false)), selectedAgent = inject<Ref<string>>('selectedConversationAgent', ref('')), creating = inject<Ref<boolean>>('conversationCreating', ref(false)), createError = inject<Ref<string>>('conversationCreateError', ref(''));
const attachment = inject<Ref<{
    url: string;
    name: string;
    size?: number;
    mime?: string;
} | undefined>>('conversationAttachment', ref());
const selected = computed(() => agents.value.find(agent => String((agent as any).id || agent.agent_id) === selectedAgent.value));

function submit() {
  if(!draft.value.trim()||uploading.value||creating.value)return;
  if(!selected.value){createError.value='请先从下拉列表选择智能体';return;}
  createError.value='';requestConversation(draft.value.trim());
}
function keydown(event: KeyboardEvent) { if (isSendKey(event)) {
    event.preventDefault();
    submit();
} }
async function upload(event: Event) { const input = event.target as HTMLInputElement, file = input.files?.[0]; input.value = ''; if (!file)
    return; if (file.size > 20 * 1024 * 1024) {
    uploadError.value = '附件不能超过 20MB';
    return;
} uploading.value = true; uploadError.value = ''; pendingAttachment.value={url:'',name:file.name,size:file.size,mime:file.type}; try {
    const response = await uploadFileAPI(file);
    if (disposed) return;
    if (response.data.status_code !== 200 || typeof response.data.data !== 'string')
        throw new Error(response.data.status_message || '附件上传失败');
    attachment.value = { url: response.data.data, name: file.name, size: file.size, mime: file.type };
}
catch (error) {
    uploadError.value = responseError(error, '附件上传失败');
}
finally {
    uploading.value = false; pendingAttachment.value=undefined;
} }
const suggestions = [{ title: '帮我整理一份报告', description: '快速生成结构清晰、内容完整的专业报告', kind: 'writing', theme: 'purple' }, { title: '分析一个问题', description: '从多角度分析问题原因，并提供可行的解决方案', kind: 'analytics', theme: 'orange' }, { title: '解释一段代码', description: '详细解释代码的功能、实现逻辑和关键细节', kind: 'coding', theme: 'green' }];
const composerInput=ref<HTMLTextAreaElement>();
watch(draft,()=>nextTick(()=>fitComposer(composerInput.value)));
</script>
<template><div class="b5-page conversation-welcome"><section class="welcome-content"><CapabilityIcon class="welcome-robot" kind="coding" robot/><h1>开始一段新的对话</h1><p>选择智能体，让 AI 帮你完成工作。</p><div class="welcome-suggestions"><button v-for="suggestion in suggestions" :key="suggestion.title" @click="draft=suggestion.title"><ResourceGlyph :kind="suggestion.kind==='writing'?'document':suggestion.kind" :theme="suggestion.theme"/><span><strong>{{suggestion.title}}</strong><small>{{suggestion.description}}</small></span><UiIcon name="chevron-right"/></button></div></section><form class="chat-composer welcome-composer" @submit.prevent="submit"><p v-if="createError||uploadError" class="chat-error" role="alert">{{createError||uploadError}}</p><div v-if="pendingAttachment||attachment" class="composer-attachments"><ChatAttachmentCard :file="(pendingAttachment||attachment)!" :uploading="uploading" removable :disabled="creating" @remove="attachment=undefined"/></div><textarea ref="composerInput" v-model="draft" rows="3" :disabled="creating" placeholder="输入你的问题，Enter 发送，Shift + Enter 换行…" aria-label="输入问题" @keydown="keydown"/><div class="composer-footer"><div class="composer-tools"><label class="upload-label" :class="{busy:uploading}" :title="uploading?'上传中…':'添加附件'"><UiIcon :name="uploading?'clock':'paperclip'"/><input type="file" :disabled="uploading||creating" @change="upload"></label><p v-if="uploading" class="composer-help" role="status">附件上传中…</p></div><div class="composer-send"><el-select v-model="selectedAgent" filterable placeholder="选择智能体" :loading="agentsLoading" :disabled="creating" class="welcome-agent-select" @change="createError=''"><template #prefix><AgentIdentity v-if="selected" class="dropdown-option-logo" :agent="selected"/><UiIcon v-else name="bot"/></template><el-option v-for="agent in agents" :key="String((agent as any).id||agent.agent_id)" :value="String((agent as any).id||agent.agent_id)" :label="agent.name"><span class="dropdown-option-row"><AgentIdentity class="dropdown-option-logo" :agent="agent"/><span>{{agent.name}}</span></span></el-option></el-select><button class="chat-primary" type="submit" :disabled="!draft.trim()||uploading||creating"><UiIcon :name="creating?'clock':'send'"/>{{creating?'创建中…':'发送'}}</button></div></div></form></div></template>
<style scoped src="./conversation-welcome.css"></style>
