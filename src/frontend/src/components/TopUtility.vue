<script setup lang="ts">
import { ElPopover } from 'element-plus'
import UiIcon from './UiIcon.vue'
withDefaults(defineProps<{placement?:'bottom-end'|'top-start'}>(),{placement:'bottom-end'})
</script>
<template>
  <div class="s-top-utility"><el-popover :placement="placement" :width="260" trigger="click"><div class="s-platform-tip"><strong>欢迎使用agentchat</strong><p>从工作台开始任务，或从左侧导航管理智能体、知识库与工具。</p></div><template #reference><button class="s-notification-button" aria-label="平台提示"><UiIcon name="bell" /></button></template></el-popover></div>
</template>
