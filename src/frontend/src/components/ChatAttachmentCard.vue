<script setup lang="ts">
import { computed } from 'vue';
import type { ChatAttachment } from '../type';
import DocumentBadge from './DocumentBadge.vue';
import UiIcon from './UiIcon.vue';
import { readableBytes, safeResourceUrl } from '../utils/data-pages';
const props = defineProps<{ file: ChatAttachment; uploading?: boolean; removable?: boolean; disabled?: boolean }>();
defineEmits<{ remove: [] }>();
const url = computed(() => props.uploading ? '' : safeResourceUrl(props.file.url));
const type = computed(() => props.file.name.includes('.') ? props.file.name.split('.').pop()?.toUpperCase().slice(0,12) : '文件');
</script>
<template><article class="chat-file-card" :aria-busy="uploading"><span class="chat-file-icon"><DocumentBadge :filename="file.name"/></span><div class="chat-file-copy"><a v-if="url" :href="url" target="_blank" rel="noopener noreferrer" :title="file.name">{{file.name}}</a><strong v-else :title="file.name">{{file.name}}</strong><small>{{type}}<template v-if="file.size!==undefined"> · {{readableBytes(file.size)}}</template><span v-if="uploading" class="chat-file-status" role="status"> · 上传中…</span></small></div><button v-if="removable" type="button" :disabled="disabled||uploading" aria-label="移除附件" title="移除附件" @click="$emit('remove')"><UiIcon name="close"/></button><a v-else-if="url" class="chat-file-open" :href="url" target="_blank" rel="noopener noreferrer" aria-label="打开附件" title="打开附件"><UiIcon name="external"/></a></article></template>
<style scoped>
.chat-file-card{display:flex;align-items:center;gap:12px;width:310px;max-width:100%;min-width:0;padding:12px 14px;border:1px solid #dce7f7;border-radius:12px;background:#f9fbff;box-sizing:border-box;white-space:normal;font-family:var(--ac-font)}
.chat-file-icon{display:grid;place-items:center;width:42px;height:44px;flex:none;background:white;border-radius:8px}.chat-file-copy{flex:1;min-width:0}.chat-file-copy>a,.chat-file-copy>strong{display:block;color:#334766;text-decoration:none;font-size:14px;font-weight:550;line-height:1.5;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.chat-file-copy>a:hover{color:#246bff}.chat-file-copy small{display:block;margin-top:4px;color:#8a9bb4;font-size:12px;line-height:1.5}.chat-file-status{color:#377adb}.chat-file-card>button,.chat-file-open{display:grid;place-items:center;flex:none;width:26px;height:26px;padding:5px;background:transparent;border:0;border-radius:6px;color:#8394ae;cursor:pointer;box-sizing:border-box}.chat-file-card>button:hover,.chat-file-open:hover{color:#246bff;background:#eaf2ff}.chat-file-card>button:disabled{opacity:.4;cursor:not-allowed}.p-icon{width:16px;height:16px}
</style>
