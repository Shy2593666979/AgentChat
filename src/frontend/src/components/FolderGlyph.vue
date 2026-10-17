<script setup lang="ts">
import { getCurrentInstance } from 'vue'
withDefaults(defineProps<{ theme?: string }>(), { theme:'blue' })
const id = `folder-${getCurrentInstance()?.uid}`
</script>
<template><span class="folder-glyph" :class="theme" aria-hidden="true"><svg viewBox="0 0 48 48"><defs><linearGradient :id="id" x1="0" y1="0" x2="1" y2="1"><stop stop-color="currentColor" stop-opacity=".75"/><stop offset="1" stop-color="currentColor"/></linearGradient></defs><path d="M7 8h13l6 6h15a4 4 0 0 1 4 4v22a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V12a4 4 0 0 1 4-4Z" :fill="`url(#${id})`"/><path d="M8 20h32" stroke="white" stroke-width="2.5" stroke-linecap="round"/><path d="M5 13v24" stroke="white" stroke-opacity=".22" stroke-width="2" stroke-linecap="round"/></svg></span></template>
<style scoped>.folder-glyph{display:grid;place-items:center;width:58px;height:58px;flex:none;border-radius:14px;background:#e6f0ff;color:#1367ff}.folder-glyph svg{width:40px;height:40px}.green{color:#00c880;background:#e6fbf1}.purple{color:#8746ff;background:#f1eaff}.orange{color:#ff991c;background:#fff3e2}.cyan{color:#00b6ed;background:#e4f6ff}.rose{color:#f43e88;background:#fff0f6}</style>
