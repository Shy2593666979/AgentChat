<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ filename: string }>()
const extension = computed(() => props.filename.split('.').pop()?.toLowerCase() || '')
const kind = computed(() => /^(doc|docx)$/.test(extension.value) ? 'word' : /^(xls|xlsx|csv)$/.test(extension.value) ? 'excel' : /^(ppt|pptx)$/.test(extension.value) ? 'slides' : extension.value === 'pdf' ? 'pdf' : 'text')
const label = computed(() => ({ word:'W', excel:'X', slides:'P', pdf:'PDF', text: extension.value === 'md' ? 'M' : 'T' })[kind.value])
</script>
<template><span class="document-badge" :class="kind" aria-hidden="true"><span class="fold"/><svg v-if="kind==='pdf'" class="pdf-mark" viewBox="0 0 30 34" fill="none" aria-hidden="true"><path d="M16 5c-5 7 2 17 8 19 4 2 4-3 0-3-7-1-17 2-20 6-3 4 1 5 4 1 5-7 10-18 8-23Z" stroke="white" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg><span v-else>{{ label }}</span></span></template>
<style scoped>.document-badge{position:relative;display:grid;place-items:center;width:31px;height:36px;flex:none;border-radius:4px;background:linear-gradient(135deg,#8e9aaf,#6b7b95);color:#fff;font:650 22px/1 'AgentChat Inter',sans-serif;box-shadow:0 2px 5px #42638713;overflow:hidden}.fold{position:absolute;top:0;right:0;width:8px;height:8px;background:#ffffff66;clip-path:polygon(0 0,100% 100%,0 100%)}.word{background:linear-gradient(135deg,#5f93ff,#2464f6)}.excel{background:linear-gradient(135deg,#24d58d,#00ad66)}.slides{background:linear-gradient(135deg,#ffbe54,#fb8a13)}.pdf{background:linear-gradient(135deg,#ff7775,#ff262d);font-size:12px}.pdf-mark{width:27px;height:31px}</style>
