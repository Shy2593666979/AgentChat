<script setup lang="ts">
import BrandLogo from './BrandLogo.vue'
defineProps<{ kind: number }>()
</script>
<template>
  <div class="s-case-art" :class="'s-art-' + kind" aria-hidden="true">
    <template v-if="kind === 0"><span class="s-art-dot s-dot-one"></span><span class="s-art-dot s-dot-two"></span><div class="s-art-robot"><BrandLogo compact /><i></i></div><div class="s-art-mini-doc"><span></span><span></span><span></span></div></template>
    <template v-else-if="kind === 1"><div class="s-art-search-sheet"></div><div class="s-art-search-pill"><span></span><i></i></div><div class="s-art-magnifier"></div><span class="s-art-dot s-dot-one"></span><span class="s-art-dot s-dot-two"></span></template>
    <template v-else-if="kind === 2"><div class="s-art-news"><header><span></span><b>AI</b></header><i></i><i></i><i></i><i></i></div></template>
    <template v-else><div class="s-art-mini-doc s-mini-left"><span></span><span></span><span></span></div><div class="s-art-donut"></div><div class="s-art-mini-doc s-mini-right"><span></span><span></span></div></template>
  </div>
</template>
