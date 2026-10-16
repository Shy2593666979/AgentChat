<script setup lang="ts">
import { computed } from 'vue'
import UiIcon from './UiIcon.vue'
import { modelProviderBrand } from '../utils/model-provider-brand'
const props = defineProps<{ provider: string; model?: string; type?: string; modelMark?: boolean; baseUrl?: string }>()
const brand = computed(() => {
  const modelBrand = props.modelMark ? modelProviderBrand('', props.model, undefined, true) : ''
  if (modelBrand) return modelBrand
  // 火山等平台也可能托管其他模型，模型列仍保留其本身的品牌标识。
  if (props.modelMark && /gpt|openai|claude|anthropic|gemini|google|qwen|通义/i.test(props.model || '')) return ''
  return modelProviderBrand(props.provider, props.model, props.baseUrl, props.modelMark)
})
const region = computed(() => {
  if (props.modelMark && props.type === 'Embedding') return '330 714 48 48'
  const name = (props.modelMark ? props.model || props.provider : props.provider).toLowerCase()
  if (/gpt|openai/.test(name)) return '330 338 44 44'
  if (/claude|anthropic/.test(name)) return '330 413 44 44'
  if (/gemini|google/.test(name)) return '330 490 44 44'
  if (/deepseek/.test(name)) return '330 642 44 44'
  if (/qwen|通义/.test(name)) return '330 566 44 44'
  if (/阿里|aliyun|alibaba/.test(name)) return '655 566 40 36'
  return ''
})
</script>
<template><span class="provider-logo" aria-hidden="true"><img v-if="brand" :src="`/ui/providers/${brand}.svg`" alt=""><svg v-else-if="region" :viewBox="region"><image href="/ui/model-marks-reference.png" width="1770" height="889"/></svg><UiIcon v-else name="cube"/></span></template>
<style scoped>.provider-logo{display:grid;place-items:center;width:40px;height:40px;flex:none;border-radius:10px;overflow:hidden;background:#fff;color:#6b8fbd}.provider-logo img{display:block;width:88%;height:88%;object-fit:contain}.provider-logo svg{width:100%;height:100%;overflow:hidden}.provider-logo :deep(.p-icon){width:28px;height:28px}</style>
