<script setup lang="ts">
import {computed,ref} from 'vue';
const mode=ref('continuous'),page=ref('chat');
const pages=[
 {id:'chat',name:'聊天',url:'/conversation/chatPage?conversation_id=6280137c844d48a6951c984cb7bb43f1'},
 {id:'mcp',name:'MCP 对话',url:'/mcp-server/chat?example=hitl'},
 {id:'task',name:'任务执行',url:'/workspace/taskGraph?example=1'},
 {id:'mars',name:'Mars',url:'/mars'},
 {id:'knowledge',name:'知识库',url:'/knowledge?example=1'},
 {id:'tool',name:'工具',url:'/tool'},
 {id:'model',name:'模型',url:'/model'},
 {id:'agent',name:'智能体',url:'/agent'}
];
const frameUrl=computed(()=>{const url=new URL(pages.find(item=>item.id===page.value)!.url,location.origin);if(mode.value==='continuous')url.searchParams.set('layout_preview','continuous');return url.pathname+url.search;});
</script>
<template><main class="layout-review"><header><div><strong>列间距预览</strong><span>只比较布局，侧边栏样式保持原样</span></div><el-select class="catalog-select" v-model="page" aria-label="选择预览页面"><el-option v-for="item in pages" :key="item.id" :value="item.id" :label="item.name"/></el-select><div class="layout-modes"><button :class="{active:mode==='original'}" @click="mode='original'">原有间距</button><button :class="{active:mode==='continuous'}" @click="mode='continuous'">连续布局</button></div><a :href="frameUrl" target="_blank" rel="noopener">单独打开 ↗</a></header><iframe :key="page+'-'+mode" :src="frameUrl" :name="mode==='continuous'?'agentchat-continuous-preview':'agentchat-original-preview'" title="页面布局预览"/></main></template>
<style scoped>.layout-review{height:100dvh;display:flex;flex-direction:column;background:#f8fbff;font-family:'AgentChat Sans SC','Microsoft YaHei',sans-serif}.layout-review>header{min-height:64px;padding:10px 20px;box-sizing:border-box;display:flex;align-items:center;gap:18px;border-bottom:1px solid #dfe8f6;background:#fff;flex:none}.layout-review header>div:first-child{display:flex;align-items:center;gap:14px;flex:1;min-width:0}.layout-review strong{font-size:15px;color:#293f63;white-space:nowrap}.layout-review header span{font-size:12px;color:#93a1b8}.layout-review select{border:1px solid #dce7f7;border-radius:9px;height:36px;padding:0 10px;font:inherit;font-size:12px;color:#577296;background:#fbfdff}.layout-modes{display:flex;border:1px solid #e0e9f7;border-radius:9px;padding:3px;gap:3px}.layout-modes button{padding:6px 12px;border:0;background:transparent;border-radius:6px;font:inherit;font-size:12px;color:#8296b4;cursor:pointer;white-space:nowrap}.layout-modes .active{background:#eaf3ff;color:#256ddd}.layout-review a{font-size:12px;color:#7293be;white-space:nowrap;text-decoration:none}.layout-review iframe{display:block;width:100%;flex:1;min-height:0;border:0;background:white}@media(max-width:850px){.layout-review header span{display:none}.layout-review>header{flex-wrap:wrap;gap:8px;padding:10px 12px}.layout-review header>div:first-child{flex:1}.layout-review a{display:none}.layout-modes button{padding-inline:9px}}
</style>
