<script setup lang="ts">
defineProps<{ name: string }>()
</script>
<template>
  <svg class="overview-glyph" viewBox="0 0 32 32" aria-hidden="true">
    <g v-if="name === 'chat'">
      <path d="M16 3C8.3 3 3 8.1 3 14.7c0 3.5 1.5 6.4 4.3 8.5L5 29l7-3.5c1.3.3 2.7.5 4 .5 7.7 0 13-4.8 13-11.3S23.7 3 16 3Z" fill="currentColor"/>
      <circle v-for="x in [10,16,22]" :key="x" :cx="x" cy="15" r="1.7" fill="white"/>
    </g>
    <g v-else-if="name === 'bot'">
      <path d="M16 8V3" stroke="currentColor" stroke-width="2.5"/><circle cx="16" cy="3" r="2.5" fill="currentColor"/>
      <rect x="5" y="8" width="22" height="21" rx="7" fill="currentColor"/>
      <path d="M3 15v6m26-6v6" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
      <rect x="10" y="14" width="12" height="8" rx="4" fill="white"/>
      <path d="M13 16v3m6-3v3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    </g>
    <g v-else-if="name === 'book'">
      <rect x="6" y="4" width="19" height="24" rx="3" fill="currentColor"/>
      <path d="M10 10h11M10 15h11M10 20h7" stroke="white" stroke-width="2" stroke-linecap="round"/>
      <path d="M3 9v17a4 4 0 0 0 4 4h15" fill="none" stroke="currentColor" stroke-width="2"/>
    </g>
    <g v-else>
      <path d="m16 2 12 5v9c0 7-7 12-12 15C11 28 4 23 4 16V7Z" fill="currentColor"/>
      <path d="m10 16 4 4 8-9" fill="none" stroke="white" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round"/>
    </g>
  </svg>
</template>
<style scoped>.overview-glyph{display:block;width:33px;height:33px;flex:none}</style>
