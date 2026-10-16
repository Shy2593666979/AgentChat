<script setup lang="ts">
import {ref,watch} from 'vue';
import ChatToolProcess from './ChatToolProcess.vue';
import type {ChatToolEvent} from '../utils/chat-tool-events';
import {maskMcpParameters} from '../utils/mcp-review';
const props=defineProps<{event:any;active:boolean}>();
const tool=ref<ChatToolEvent>({event_type:'工具调用',status:'UNKNOWN',message:'',show:false});
watch(()=>props.event,event=>{
    tool.value.event_type=event.title||'工具调用';
    tool.value.status=event.is_error?'ERROR':event.status==='RECEIVE_STOPPED'?'STOPPED':event.status||'UNKNOWN';
    const value=maskMcpParameters(event.content||event.message||'');
    tool.value.message=typeof value==='string'?value:JSON.stringify(value,null,2);
},{immediate:true,deep:true});
</script>
<template><div class="mcp-tool-event"><ChatToolProcess :events="[tool]" :active="active"/></div></template>
<style scoped>.mcp-tool-event{margin:10px 0}.mcp-tool-event :deep(.tool-process-heading){display:none}.mcp-tool-event :deep(.chat-tool-process){margin-bottom:0}</style>
