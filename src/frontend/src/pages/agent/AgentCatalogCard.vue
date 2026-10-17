<script setup lang="ts">
import { computed } from 'vue'
import { agentIdentity } from '../../utils/agent-identity'
import AgentIdentity from '../../components/AgentIdentity.vue'
import UiIcon from '../../components/UiIcon.vue'
import SidebarIcon from '../../components/SidebarIcon.vue'
import ProviderLogo from '../../components/ProviderLogo.vue'
import type { Agent } from '../../type'
import type { LLMResponse } from '../../apis/llm'
const props = defineProps<{
  agent: Agent
  modelName: string
  model?: LLMResponse
  resources: { key: string; icon: string; label: string; count: number; title: string }[]
  starting: boolean
  disabled: boolean
}>()
defineEmits<{ chat: []; edit: []; remove: [] }>()
const category = computed(() => ({bot:'对话',mail:'邮件',writing:'写作',book:'文档',weather:'天气',search:'搜索',code:'代码',chart:'数据',calendar:'日程',image:'图像',package:'物流'} as Record<string,string>)[agentIdentity(props.agent).icon] || '助手')
const tone = computed(() => ({weather:'orange',search:'cyan',code:'purple',chart:'orange',calendar:'cyan',image:'pink',package:'cyan'} as Record<string,string>)[agentIdentity(props.agent).icon] || 'blue')
</script>
<template>
  <article class="agent-card" :class="`tone-${tone}`">
    <div class="card-heading">
      <AgentIdentity :agent="agent" variant="catalog"/>
      <div class="card-copy"><h3 :title="agent.name">{{ agent.name }}</h3><p class="card-description" :title="agent.description">{{ agent.description || '为你的工作提供帮助，开始对话试试。' }}</p><span class="category-tag">{{ category }}</span></div>
      <el-dropdown trigger="click" class="card-menu">
        <button class="icon-button" :aria-label="`${agent.name}的更多操作`"><UiIcon name="more"/></button>
        <template #dropdown><el-dropdown-menu><el-dropdown-item @click="$emit('edit')"><UiIcon name="edit"/><span>编辑智能体</span></el-dropdown-item><el-dropdown-item @click="$emit('remove')" class="dropdown-danger-action"><UiIcon name="trash"/><span>删除智能体</span></el-dropdown-item></el-dropdown-menu></template>
      </el-dropdown>
    </div>
    <div class="card-model" :title="modelName">
      <ProviderLogo v-if="model" :provider="model.provider" :base-url="model.base_url"/><UiIcon v-else name="cube"/>
      <span class="agent-card-model-name">{{ modelName }}</span>
      <div v-if="resources.length" class="card-resources">
        <span v-for="resource in resources" :key="resource.key" class="resource-count" :title="`${resource.label}：${resource.count}${resource.title ? ' · '+resource.title : ''}`" :aria-label="`${resource.label}：${resource.count}`">
          <UiIcon v-if="resource.icon === 'database'" name="database"/><SidebarIcon v-else :name="resource.icon"/><span>{{ resource.count }}</span>
        </span>
      </div>
    </div>
    <div class="card-footer">
      <button class="chat-button" :disabled="disabled" @click="$emit('chat')"><UiIcon name="chat"/><span>{{ starting ? '创建中…' : '开始对话' }}</span></button>
      <button class="edit-button" :aria-label="`编辑${agent.name}`" title="编辑智能体" @click="$emit('edit')"><UiIcon name="edit"/></button>
    </div>
  </article>
</template>
<style scoped>
/* 第一张 A 方案：立体图标、单一分类标签、完整的模型资源栏。 */
.agent-card{--topic-ink:#176aff;--topic-tint:#eaf3ff;position:relative;display:flex;flex-direction:column;min-width:0;min-height:300px;padding:22px 20px 17px;box-sizing:border-box;border:1px solid #dfebfb;border-radius:18px;background:#fff;box-shadow:0 3px 14px #6494ca05;transition:border-color .15s,box-shadow .15s}
.agent-card:hover{border-color:#a8c9fb;box-shadow:0 7px 24px #3d7acb0d}
.card-heading{display:flex;align-items:flex-start;gap:22px;min-width:0;min-height:158px}
.card-heading :deep(.agent-identity){width:104px;height:104px;border-radius:21px;background:transparent}
.card-copy{flex:1;min-width:0}
.card-copy h3{margin:2px 20px 10px 0;color:#0a183e;font-size:22px;font-weight:700;line-height:1.45;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.card-description{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere;margin:0;color:#647498;font-size:18px;font-weight:400;line-height:1.55;min-height:56px}
.category-tag{display:inline-flex;align-items:center;min-height:28px;max-width:100%;margin-top:10px;padding:2px 13px;border-radius:20px;background:var(--topic-tint);color:var(--topic-ink);font-size:14px;line-height:24px}
.tone-purple{--topic-ink:#7650ef;--topic-tint:#f0ebff}.tone-green{--topic-ink:#00a575;--topic-tint:#e7faf1}.tone-orange{--topic-ink:#eb8b16;--topic-tint:#fff1df}.tone-pink{--topic-ink:#ef6370;--topic-tint:#fff0f2}.tone-cyan{--topic-ink:#029db8;--topic-tint:#e6f9fd}
.card-menu{position:absolute;top:20px;right:22px}
.icon-button{display:grid;place-items:center;width:25px;height:25px;padding:0;border:0;border-radius:7px;background:transparent;color:#647798;cursor:pointer}.icon-button:hover{background:#edf5ff;color:#1767ff}.icon-button :deep(.p-icon){width:22px;height:22px;stroke-width:3}
.card-model{display:flex;align-items:center;gap:8px;min-width:0;margin-top:auto;padding:12px 0 15px;border-top:1px solid #e8eef9;color:#4a618a;font-size:16px;line-height:24px}
.agent-card-model-name{font:400 16px/24px 'AgentChat Inter','AgentChat Sans SC',sans-serif;letter-spacing:0;color:inherit;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.card-model :deep(.provider-logo),.card-model> :deep(.p-icon){width:22px;height:22px;flex:none;border-radius:4px;background:transparent}
.card-resources{display:flex;align-items:center;flex:none;gap:12px;margin-left:2px;padding-left:12px;border-left:1px solid #e0eaf9}
.resource-count{display:inline-flex;align-items:center;gap:6px;white-space:nowrap;color:#5e7298;font-size:16px;font-weight:400;line-height:24px;font-variant-numeric:tabular-nums}.resource-count :deep(.p-icon){width:19px;height:19px;color:#5e7298}
.card-footer{display:flex;align-items:center;gap:12px}
.chat-button,.edit-button{display:flex;align-items:center;justify-content:center;gap:9px;height:48px;border:1px solid transparent;border-radius:10px;color:#0860ff;font:600 18px/1.5 var(--ac-font);cursor:pointer}
.chat-button{flex:1;min-width:0;padding:0 12px;background:linear-gradient(110deg,#eaf3ff,#e7f1ff)}.edit-button{flex:none;width:48px;padding:0;background:#fff;border-color:#dce7f8;color:#273d72}
.card-footer :deep(.p-icon){width:21px;height:21px}.chat-button:hover{background:#deecff}.edit-button:hover{background:#f3f8ff;border-color:#b3d1ff}.chat-button:disabled{opacity:.5;cursor:not-allowed}
button:focus-visible{outline:2px solid #94bdff;outline-offset:3px}
@media(max-width:700px){.agent-card{padding:19px 17px 16px}.card-heading{gap:15px;min-height:142px}.card-heading :deep(.agent-identity){width:70px;height:70px;border-radius:16px}.card-copy h3{font-size:18px;margin-top:0}.card-description{font-size:14px;min-height:46px}.category-tag{font-size:12px;min-height:24px;margin-top:9px}.card-menu{top:16px;right:11px}.card-model{flex-wrap:wrap;gap:7px}.agent-card-model-name{min-width:calc(100% - 30px)}.card-resources{margin-left:0;border-left:0;padding-left:0}.card-footer{gap:9px}.chat-button,.edit-button{font-size:15px;height:43px}.edit-button{width:43px}}
@media(prefers-reduced-motion:reduce){.agent-card{transition:none}}
</style>
