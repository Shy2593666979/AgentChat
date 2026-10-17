<script setup lang="ts">
import { getCurrentInstance } from 'vue';
import ResourceGlyph from './ResourceGlyph.vue';
withDefaults(defineProps<{kind?:string;theme?:string}>(),{kind:'document',theme:'blue'});
const gradient='skill-envelope-'+getCurrentInstance()?.uid;
</script>
<template>
 <span v-if="kind==='mail'" class="resource-glyph skill-envelope" aria-hidden="true"><svg viewBox="0 0 64 64" fill="none"><defs><linearGradient :id="gradient" x1="8" y1="10" x2="57" y2="56" gradientUnits="userSpaceOnUse"><stop stop-color="#ff9b9b"/><stop offset=".45" stop-color="#fc6976"/><stop offset="1" stop-color="#ef3c61"/></linearGradient></defs><rect x="6" y="12" width="52" height="41" rx="6" :fill="`url(#${gradient})`"/><path d="m8 16 24 18 24-18" stroke="white" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/><path d="m7 50 15-14m35 14-15-14" stroke="white" stroke-opacity=".13" stroke-width="2"/></svg></span>
 <ResourceGlyph v-else :kind="kind" :theme="theme"/>
</template>
<style scoped>.skill-envelope{display:grid;place-items:center;flex:none;width:94px;height:94px;border-radius:21px;background:radial-gradient(circle at 30% 20%,#fff4f6,#ffedf0);color:#fa5b79}.skill-envelope svg{width:64px;height:64px;filter:drop-shadow(0 4px 5px #ff85962a)}</style>
