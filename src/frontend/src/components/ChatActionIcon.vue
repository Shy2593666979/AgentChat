<script setup lang="ts">
import RefreshIcon from "./RefreshIcon.vue";
defineProps<{name:'copy'|'retry'|'like'|'dislike'}>();
</script>
<template><RefreshIcon v-if="name==='retry'" class="chat-action-icon" style="width:18px;height:18px" stroke-width="1.6"/><svg v-else class="chat-action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><template v-if="name==='copy'"><rect x="8.5" y="8.5" width="11.5" height="12" rx="3"/><path d="M15.5 5.5A2 2 0 0 0 13.5 3.5H6a2.5 2.5 0 0 0-2.5 2.5v7.5a2 2 0 0 0 2 2"/></template><g v-else :transform="name==='dislike'?'rotate(180 12 12)':undefined"><path d="M7.5 10.5h-2a2 2 0 0 0-2 2V18a2 2 0 0 0 2 2h2V10.5Z M7.5 11l3.6-4.8a3 3 0 0 0 .6-1.8v-.5a1.4 1.4 0 0 1 2.7-.5 7 7 0 0 1 .1 5.6h3.7a2 2 0 0 1 2 2.4l-1.2 6a2.7 2.7 0 0 1-2.7 2.1H7.5"/></g></svg></template>
<style scoped>.chat-action-icon{width:18px;height:18px;display:block;flex:none}</style>
