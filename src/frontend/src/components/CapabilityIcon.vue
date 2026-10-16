<script setup lang="ts">
import { getCurrentInstance } from 'vue'
withDefaults(defineProps<{ kind?: string; robot?: boolean }>(), { kind: 'research', robot: false })
const gradientId = `capability-${getCurrentInstance()?.uid}`
</script>
<template>
  <span class="capability-icon" :class="kind" aria-hidden="true">
    <svg viewBox="0 0 64 64" fill="none">
      <defs><linearGradient :id="gradientId" x1="0" y1="0" x2="1" y2="1"><stop stop-color="currentColor"/><stop offset="1" stop-color="currentColor" stop-opacity=".65"/></linearGradient></defs>
      <g v-if="robot">
        <path d="M32 15V7" stroke="currentColor" stroke-width="4" stroke-linecap="round"/><circle cx="32" cy="6" r="4" fill="currentColor"/>
        <rect x="8" y="15" width="48" height="40" rx="15" :fill="`url(#${gradientId})`"/>
        <rect x="3" y="28" width="6" height="17" rx="3" fill="currentColor" opacity=".55"/><rect x="55" y="28" width="6" height="17" rx="3" fill="currentColor" opacity=".55"/>
        <rect x="16" y="25" width="32" height="20" rx="10" fill="white"/><path d="M24 31v7m16-7v7" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
        <path d="M17 22c2-3 5-4 9-4" stroke="white" stroke-opacity=".35" stroke-width="2" stroke-linecap="round"/><circle cx="48" cy="22" r="2.5" fill="white" opacity=".9"/>
      </g>
      <g v-else-if="kind === 'research'"><circle cx="27" cy="27" r="16" stroke="currentColor" stroke-width="6"/><path d="m39 39 14 14" stroke="currentColor" stroke-width="7" stroke-linecap="round"/><path d="M16 25a12 12 0 0 1 13-10" stroke="white" stroke-opacity=".6" stroke-width="2" stroke-linecap="round"/></g>
      <g v-else-if="kind === 'writing'"><path d="M15 9h25l10 12v31a4 4 0 0 1-4 4H15a4 4 0 0 1-4-4V13a4 4 0 0 1 4-4Z" :fill="`url(#${gradientId})`"/><path d="M39 9v12h11" fill="white" fill-opacity=".5"/><path d="M19 24h17M19 32h22M19 40h12" stroke="white" stroke-width="3" stroke-linecap="round"/><path d="m33 50 18-18 9 8-18 18-12 3Z" fill="currentColor" stroke="#f3ecff" stroke-width="2.5"/></g>
      <g v-else-if="kind === 'analytics'"><rect x="10" y="33" width="9" height="23" rx="3" :fill="`url(#${gradientId})`"/><rect x="26" y="21" width="9" height="35" rx="3" :fill="`url(#${gradientId})`"/><rect x="42" y="8" width="9" height="48" rx="3" :fill="`url(#${gradientId})`"/></g>
      <g v-else-if="kind === 'coding'"><path d="m19 21-12 12 12 11M45 21l12 12-12 11M36 13 27 52" stroke="currentColor" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></g>
      <g v-else-if="kind === 'enterprise'"><path d="M9 13h14l6 6h23a4 4 0 0 1 4 4v29a4 4 0 0 1-4 4H13a5 5 0 0 1-5-5V17a4 4 0 0 1 1-4Z" :fill="`url(#${gradientId})`"/><path d="M15 27h35" stroke="white" stroke-width="3" stroke-linecap="round"/></g>
      <g v-else><rect x="9" y="14" width="44" height="44" rx="7" :fill="`url(#${gradientId})`"/><rect x="14" y="29" width="34" height="23" rx="3" fill="#f2eaff"/><path d="M21 12v10M41 12v10" stroke="currentColor" stroke-width="6" stroke-linecap="round"/><circle cx="35" cy="41" r="5" fill="currentColor"/></g>
    </svg>
  </span>
</template>
<style scoped>
.capability-icon{display:grid;place-items:center;flex:none;width:64px;height:64px;border-radius:15px;color:#0863ff;background:linear-gradient(135deg,#dceeff,#cde3ff)}
.capability-icon svg{width:44px;height:44px;filter:drop-shadow(0 3px 2px #ffffff88)}
.research,.enterprise{color:#00c978;background:linear-gradient(135deg,#e6fff1,#dcfceb)}
.writing,.daily{color:#8744ff;background:linear-gradient(135deg,#f0eaff,#e9e0ff)}
.analytics{color:#ff9b16;background:linear-gradient(135deg,#fff1df,#ffe9cd)}
.coding{color:#0870ff;background:linear-gradient(135deg,#dcefff,#cde4ff)}
</style>
