<script setup lang="ts">
withDefaults(defineProps<{ kind?: string; theme?: string }>(), { kind: 'custom', theme: 'blue' });
</script>
<template>
  <span class="tool-glyph" :class="theme" aria-hidden="true">
    <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="3.3" stroke-linecap="round" stroke-linejoin="round">
      <g v-if="kind==='globe'"><circle cx="24" cy="24" r="17"/><ellipse cx="24" cy="24" rx="7" ry="17"/><path d="M7 24h34"/></g>
      <g v-else-if="kind==='document'"><path d="M13 7h15l9 9v25H13a3 3 0 0 1-3-3V10a3 3 0 0 1 3-3Z"/><path d="M28 7v10h9M17 24h13M17 31h13"/></g>
      <g v-else-if="kind==='code'"><path d="m14 15-9 9 9 9m20-18 9 9-9 9M28 10l-8 28"/></g>
      <g v-else-if="kind==='database'"><ellipse cx="24" cy="12" rx="15" ry="6"/><path d="M9 12v24c0 3 7 6 15 6s15-3 15-6V12M9 24c0 3 7 6 15 6s15-3 15-6"/></g>
      <g v-else-if="kind==='image'"><rect x="7" y="7" width="34" height="34" rx="4"/><circle cx="17" cy="17" r="3" fill="currentColor" stroke="none"/><path d="m8 33 10-11 9 9 8-8 6 7"/></g>
      <g v-else-if="kind==='mail'"><rect x="6" y="10" width="36" height="28" rx="4"/><path d="m8 13 16 13 16-13"/></g>
      <g v-else-if="kind==='weather'"><circle cx="17" cy="17" r="7"/><path d="M17 4v2M4 17h2M7 7l2 2M27 7l-2 2"/><path d="M17 39h19a7 7 0 0 0 1-14 10 10 0 0 0-19-2 8 8 0 0 0-1 16Z" fill="var(--glyph-bg)"/></g>
      <g v-else-if="kind==='research'"><path d="M10 7h20l7 7v12M30 7v8h7M16 18h8M16 25h6M10 7v33h12"/><circle cx="31" cy="31" r="8"/><path d="m37 37 6 6"/></g>
      <g v-else-if="kind==='delivery'"><path d="m24 5 17 8v22l-17 8-17-8V13Z M7 13l17 8 17-8M24 21v22M15 9l18 8v9"/></g>
      <g v-else-if="kind==='book'"><path d="M24 11c-6-5-13-5-18-3v29c6-2 12-1 18 4 6-5 12-6 18-4V8c-5-2-12-2-18 3ZM24 11v30"/></g>
      <g v-else><rect x="7" y="7" width="13" height="13" rx="3"/><rect x="28" y="7" width="13" height="13" rx="3"/><rect x="7" y="28" width="13" height="13" rx="3"/><path d="M28 34h13M34 28v13"/></g>
    </svg>
  </span>
</template>
<style scoped>
.tool-glyph{--glyph-bg:#e8f2ff;display:grid;place-items:center;flex:none;width:94px;height:94px;border-radius:21px;color:#076bff;background:linear-gradient(135deg,#e9f4ff,#e1efff)}
.tool-glyph svg{width:58px;height:58px;filter:drop-shadow(0 2px 1px #fff9)}
.green{--glyph-bg:#e4fbee;color:#00b965;background:linear-gradient(135deg,#e6fbef,#def9e9)}
.purple{color:#7c22f6;background:linear-gradient(135deg,#f4edff,#eee6ff)}
.orange{color:#ff8108;background:linear-gradient(135deg,#fff4e7,#fff0dd)}
.rose{color:#fa3486;background:linear-gradient(135deg,#ffedf4,#ffe5ef)}
.violet{color:#7861f3;background:linear-gradient(135deg,#f2eeff,#eae6ff)}
.cyan{--glyph-bg:#e4faff;color:#11a8d9;background:linear-gradient(135deg,#e5faff,#dcf3ff)}
</style>
