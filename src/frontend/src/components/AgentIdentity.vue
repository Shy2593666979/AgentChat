<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { agentIdentity, identityUrl, parseIdentity, catalogAgentColor } from '../utils/agent-identity'
import AgentCatalogGlyph from './AgentCatalogGlyph.vue'
const props = defineProps<{ agent: { name?: string; description?: string; logo_url?: string; knowledge_ids?: string[] }; variant?: 'catalog' }>()
const identity = computed(() => agentIdentity(props.agent))
const failed = ref(false)
watch(() => identity.value.url, () => { failed.value = false })
</script>
<template><span class="agent-identity" :class="`tone-${identity.color}`"><AgentCatalogGlyph v-if="variant === 'catalog' && (failed || parseIdentity(identity.url))" :icon="identity.icon" :color="catalogAgentColor(agent)" :name="agent.name"/><img v-else :src="failed ? identityUrl(identity.icon, identity.color) : identity.url" alt="" @error="failed = true" /></span></template>
<style scoped>
.agent-identity{display:block;flex:none;width:56px;height:56px;border-radius:14px;overflow:hidden;background:#edf4ff}.agent-identity img{display:block;width:100%;height:100%;object-fit:cover}
</style>
