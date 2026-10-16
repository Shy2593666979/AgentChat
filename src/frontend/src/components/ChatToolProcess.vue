<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import UiIcon from './UiIcon.vue';
import { chatToolEventState, type ChatToolEvent } from '../utils/chat-tool-events';
const props=defineProps<{events:ChatToolEvent[];active:boolean}>();
const clock=ref(Date.now());
const timings=new Map<ChatToolEvent,{start:number;end?:number}>();
let ticker:ReturnType<typeof setInterval>|undefined;
const running=computed(()=>props.active&&props.events.some(event=>event.status==='START'));
const complete=computed(()=>props.events.length>0&&props.events.every(event=>chatToolEventState(event)==='END'));
const title=computed(()=>running.value?'正在执行工具':props.active?'正在生成回答':complete.value?'工具执行完成':'工具执行记录');
const state=(event:ChatToolEvent)=>event.status==='START'&&!props.active?'UNKNOWN':chatToolEventState(event);
const label=(event:ChatToolEvent)=>({START:'执行中',END:'已完成',ERROR:'执行异常',STOPPED:'已停止',WAITING:'等待执行'} as Record<string,string>)[state(event)]||'状态未记录';
const name=(event:ChatToolEvent)=>event.event_type.replace(/^.*?执行(?:可用)?(?:插件工具|工具|MCP|服务)?\s*[:：]\s*/, '')||event.event_type;
const icon=(event:ChatToolEvent)=>/搜索|search/i.test(event.event_type)?'search':/网页|读取|browser|fetch/i.test(event.event_type)?'browser':/文件|文档|pdf|doc/i.test(event.event_type)?'file':'tool';
const elapsed=(event:ChatToolEvent)=>{const timing=timings.get(event);return timing?Math.max(0,Math.floor(((timing.end??clock.value)-timing.start)/1000)):undefined;};
watch(()=>[props.active,props.events.map(event=>event.status).join('|')],()=>{
    clock.value=Date.now();
    for(const event of props.events){
        if(props.active&&event.status==='START'&&!timings.has(event))timings.set(event,{start:clock.value});
        const timing=timings.get(event);
        if(timing&&!timing.end&&(event.status!=='START'||!props.active))timing.end=clock.value;
    }
    if(running.value&&!ticker)ticker=setInterval(()=>clock.value=Date.now(),500);
    if(!running.value&&ticker){clearInterval(ticker);ticker=undefined;}
},{immediate:true});
onBeforeUnmount(()=>{if(ticker)clearInterval(ticker);});
</script>
<template><section v-if="events.length" class="chat-tool-process" aria-label="工具执行过程"><header class="tool-process-heading"><span class="tool-live-dot" :class="{active:running}"/><strong>{{title}}</strong><small>{{events.length}} 个调用</small></header><div class="tool-process-list"><article v-for="(event,index) in events" :key="index" class="tool-process-item" :class="state(event)"><button class="tool-process-summary" :aria-expanded="event.show" @click="event.show=!event.show"><span class="tool-process-icon"><UiIcon :name="icon(event)"/></span><span class="tool-process-copy"><strong>{{name(event)}}</strong><small>{{state(event)==='START'?'正在等待工具返回结果…':state(event)==='END'?'结果已返回，可展开查看':state(event)==='ERROR'?'本次调用未能完成，可展开查看原因':label(event)}}</small></span><span class="tool-process-state"><i v-if="state(event)==='START'" class="tool-spinner"/><UiIcon v-else-if="state(event)==='END'" name="check"/>{{label(event)}}<small v-if="elapsed(event)!==undefined">{{elapsed(event)}}s</small></span><UiIcon class="tool-process-chevron" :class="{open:event.show}" name="chevron-down"/></button><div v-if="event.show" class="tool-process-detail"><span>{{state(event)==='START'?'执行信息':state(event)==='ERROR'?'异常信息':'工具返回内容'}}</span><pre>{{event.message||'暂无详细信息'}}</pre></div></article></div></section></template>
<style scoped>
.chat-tool-process{margin-bottom:18px}.tool-process-heading{display:flex;align-items:center;gap:8px;margin-bottom:12px}.tool-process-heading strong{font-size:13px;font-weight:550;color:#586b87}.tool-process-heading>small{margin-left:auto;font-size:11px;color:#a0adc0}.tool-live-dot{width:6px;height:6px;background:#93a7c3;border-radius:50%;flex:none}.tool-live-dot.active{background:#3785ff;box-shadow:0 0 0 4px #eef5ff;animation:tool-pulse 1.6s ease-in-out infinite}.tool-process-list{display:grid;gap:8px}.tool-process-item{border:1px solid #e5ecf7;background:#f9fbfe;border-radius:10px;overflow:hidden}.tool-process-item.START{background:#f4f9ff;border-color:#c9dffc}.tool-process-item.END{background:#fbfdfc;border-color:#e2eee8}.tool-process-item.ERROR{background:#fffcf7;border-color:#f0e6d6}.tool-process-summary{display:flex;align-items:center;gap:10px;width:100%;padding:12px;text-align:left;border:0;background:transparent;cursor:pointer;min-width:0}.tool-process-icon{width:31px;height:31px;display:grid;place-items:center;border-radius:9px;color:#5e83bb;background:#eaf2ff;flex:none}.tool-process-icon .p-icon{width:17px;height:17px}.tool-process-copy{flex:1;min-width:0}.tool-process-copy strong{display:block;font-size:13px;font-weight:550;color:#465b79;overflow-wrap:anywhere}.tool-process-copy small{display:block;font-size:11px;line-height:1.6;color:#91a0b6;margin-top:3px}.tool-process-state{display:flex;align-items:center;gap:5px;font-size:11px;color:#96a4b8;flex:none;white-space:nowrap}.tool-process-state>.p-icon{width:14px;height:14px}.START .tool-process-state{color:#347ff0}.END .tool-process-state{color:#15a477}.ERROR .tool-process-state{color:#ba8b45}.tool-process-state small{margin-left:4px;font-size:10px;color:#a0aec1;font-variant-numeric:tabular-nums}.tool-spinner{width:12px;height:12px;border:2px solid #d5e6ff;border-top-color:#438afb;border-radius:50%;box-sizing:border-box;animation:tool-spin .85s linear infinite}.tool-process-chevron{width:12px;height:12px;flex:none;color:#9babc2;transition:transform .2s}.tool-process-chevron.open{transform:rotate(180deg)}.tool-process-detail{padding:12px 14px;border-top:1px solid #e5edf8}.tool-process-detail>span{font-size:11px;color:#91a0b8}.tool-process-detail pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:240px;overflow:auto;font:inherit;font-size:12px;line-height:1.8;color:#7387a4;margin:8px 0 0}@keyframes tool-spin{to{transform:rotate(360deg)}}@keyframes tool-pulse{50%{opacity:.4}}@media(max-width:700px){.tool-process-summary{padding:10px 8px;gap:7px}.tool-process-icon{width:26px;height:26px}.tool-process-state{font-size:10px}.tool-process-state small,.tool-process-chevron{display:none}.tool-process-copy small{font-size:10px}.tool-process-copy strong{font-size:12px}}@media(prefers-reduced-motion:reduce){.tool-live-dot.active{animation:none}}
</style>
