<script setup lang="ts">
withDefaults(defineProps<{ compact?: boolean; sidebar?: boolean }>(), { compact: false, sidebar: false })
</script>
<template>
  <div class="brand-logo" :class="{ 'brand-logo--compact': compact }" aria-label="agentchat">
    <span class="brand-logo__mark" aria-hidden="true"><img src="/ui/brand/zhiyan-robot.png" alt="" width="1280" height="1280" decoding="async" /></span>
    <div v-if="!compact" class="brand-logo__type">
      <span class="brand-logo__name">agen<span class="brand-logo__letter-t">t</span>cha<span class="brand-logo__letter-t">t</span></span>
    </div>
  </div>
</template>
<style scoped>
.brand-logo { --brand-wordmark-font: 'AgentChat Brand','AgentChat Inter',sans-serif; --brand-wordmark-weight: 550; --brand-wordmark-spacing: -.2px; --brand-wordmark-color: #403f68; display: inline-flex; align-items: center; gap: 10px; color: var(--brand-wordmark-color); }
.brand-logo__mark { position: relative; display: block; width: 36px; height: 36px; flex-shrink: 0; border-radius: 50%; overflow: hidden; }
.brand-logo__mark img { position: absolute; top: -6%; left: -6%; display: block; width: 112%; height: 112%; max-width: none; object-fit: contain; }
.brand-logo__type { display: flex; flex-direction: column; gap: 3px; text-align: left; }
.brand-logo__name { font-family: var(--brand-wordmark-font); font-size: 22px; font-weight: var(--brand-wordmark-weight); line-height: 1.2; letter-spacing: var(--brand-wordmark-spacing); color: var(--brand-wordmark-color); white-space: nowrap; font-synthesis: none; font-feature-settings: 'cv11' 1; }
/* 使用带弧形收笔的 t，保留字标底部向右延伸的小尾巴。 */
.brand-logo__letter-t { font-family: 'AgentChat Inter', sans-serif; font-feature-settings: normal; }
@media (max-width: 700px) { .brand-logo__mark { width: 31px; height: 31px; } .brand-logo__name { font-size: 19px; } }
</style>
