<script setup lang="ts">
import { computed } from 'vue'
import ToolGlyph from './ToolGlyph.vue'
import ResourceGlyph from './ResourceGlyph.vue'
const props = defineProps<{ icon: string; color: string; name?: string }>()
const spriteIndex = computed(() => ({bot:0,mail:1,writing:2,book:2,weather:3,search:4,code:5} as Record<string,number>)[props.icon])
const hue = {blue:220,purple:265,green:155,cyan:190,orange:35,pink:355} as Record<string,number>
const spriteStyle = computed(() => {
  const index = spriteIndex.value ?? 0
  const original = ['blue','pink','purple','orange','green','purple'][index]!
  return {
    backgroundPosition: `${[21.099744,49.744246,78.196931][index % 3]}% ${index < 3 ? 33.253874 : 71.275328}%`,
    filter: props.color !== original ? `hue-rotate(${(hue[props.color] || 220) - hue[original]!}deg)` : undefined,
  }
})
const theme = computed(() => props.color === 'pink' ? 'rose' : props.color)
</script>
<template>
  <span v-if="spriteIndex !== undefined" class="catalog-glyph catalog-glyph--sprite" :style="spriteStyle" aria-hidden="true"/>
  <span v-else class="catalog-glyph" aria-hidden="true">
    <ResourceGlyph v-if="['chart','calendar'].includes(icon)" :kind="icon === 'chart' ? 'analytics' : 'clock'" :theme="theme"/>
    <ToolGlyph v-else :kind="icon === 'package' ? 'delivery' : icon" :theme="theme"/>
  </span>
</template>
<style scoped>
/* 直接读取用户确认图中的六个 104px 图标区域；保留原始像素，不重新绘制。 */
.catalog-glyph{display:block;width:100%;height:100%;border-radius:inherit}
.catalog-glyph--sprite{background-image:url('/ui/agent-icons/catalog-a-reference.png');background-size:1603.846154% 906.730769%;background-repeat:no-repeat}
.catalog-glyph :deep(.resource-glyph),.catalog-glyph :deep(.tool-glyph){width:100%;height:100%;border-radius:inherit}.catalog-glyph :deep(svg){width:65%;height:65%}
</style>
