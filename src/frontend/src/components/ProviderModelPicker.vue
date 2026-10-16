<script setup lang="ts">
import { modelProviderDisplayName } from '../utils/model-provider-brand'
import { modelDisplayName } from "../utils/model-display";
import { computed, nextTick, ref, watch } from 'vue'
import ProviderLogo from './ProviderLogo.vue'
import UiIcon from './UiIcon.vue'
import type { LLMResponse } from '../apis/llm'
const props = withDefaults(defineProps<{ modelValue: string; models: LLMResponse[]; disabled?: boolean; loading?: boolean; legacyDefault?: boolean }>(), { disabled: false, loading: false, legacyDefault: false })
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
const popover = ref<{ popperRef?: { popperInstanceRef?: { update: () => Promise<unknown> } } }>()
const open = ref(false), activeProvider = ref(''), modelPanel = ref<HTMLElement>(), triggerButton = ref<HTMLButtonElement>()
const current = computed(() => props.models.find(model => model.llm_id === props.modelValue))
const groups = computed(() => {
  const result = new Map<string, { provider: string; baseUrl: string; models: LLMResponse[] }>()
  for (const model of props.models) {
    const provider = modelProviderDisplayName(model.provider) || '自定义服务'
    if (!result.has(provider)) result.set(provider, { provider, baseUrl: model.base_url, models: [] })
    result.get(provider)!.models.push(model)
  }
  return [...result.values()]
})
const activeGroup = computed(() => groups.value.find(group => group.provider === activeProvider.value))
const label = computed(() => props.loading ? '正在加载模型…' : (current.value ? modelDisplayName(current.value) : '') || (props.legacyDefault ? '默认配置模型（旧会话）' : props.modelValue ? '原模型已不可用' : '选择模型'))
watch(open, () => { activeProvider.value = '' })
// 二级面板改变宽度后重新定位，确保靠近屏幕边缘时也完整可见。
watch(activeProvider, async () => { await nextTick(); await popover.value?.popperRef?.popperInstanceRef?.update() }, { flush: 'post' })
watch(() => props.disabled || props.loading, value => { if (value) open.value = false })
function selectModel(id: string) { if (props.disabled || props.loading) return; emit('update:modelValue', id); open.value = false; nextTick(() => triggerButton.value?.focus()) }
function focusSibling(event: KeyboardEvent, step: number) {
  const button = event.currentTarget as HTMLElement
  const items = [...(button.parentElement?.querySelectorAll<HTMLButtonElement>('button') || [])]
  items[(items.indexOf(button as HTMLButtonElement) + step + items.length) % items.length]?.focus()
}
async function openWithKeyboard() { if (props.disabled || props.loading) return; open.value = true; await nextTick(); document.getElementById('mcp-provider-0')?.focus() }
async function focusModels(provider: string) { activeProvider.value = provider; await nextTick(); modelPanel.value?.querySelector<HTMLButtonElement>('button')?.focus() }
function backToProviders() { document.getElementById('mcp-provider-' + groups.value.findIndex(group => group.provider === activeProvider.value))?.focus() }
</script>
<template>
  <el-popover ref="popover" v-model:visible="open" trigger="click" placement="top-end" :width="activeGroup ? 470 : 190" :disabled="disabled || loading" popper-class="provider-model-menu" :show-arrow="false" :persistent="false">
    <template #reference><button ref="triggerButton" type="button" class="provider-model-picker" @keydown.down.prevent="openWithKeyboard" @keydown.esc.stop.prevent="open = false" :disabled="disabled || loading" aria-label="选择 MCP 模型" aria-haspopup="menu" :aria-expanded="open" :title="label"><ProviderLogo v-if="current" :provider="current.provider" :base-url="current.base_url"/><UiIcon v-else name="cube"/><span>{{ label }}</span><UiIcon name="chevron-down"/></button></template>
    <div class="provider-model-panels" @keydown.esc.stop.prevent="open = false">
      <div class="provider-panel" role="menu" aria-label="模型厂商">
        <button v-for="(group, index) in groups" :id="'mcp-provider-' + index" :key="group.provider" type="button" role="menuitem" aria-haspopup="menu" :aria-expanded="activeProvider === group.provider" :class="{ active: activeProvider === group.provider }" @mouseenter="activeProvider = group.provider" @focus="activeProvider = group.provider" @click="activeProvider = group.provider" @keydown.right.prevent="focusModels(group.provider)" @keydown.down.prevent="focusSibling($event, 1)" @keydown.up.prevent="focusSibling($event, -1)"><ProviderLogo :provider="group.provider" :base-url="group.baseUrl"/><span>{{ group.provider }}</span><UiIcon name="chevron-right"/></button>
        <p v-if="!groups.length" class="picker-empty">暂无可用的对话模型</p>
      </div>
      <div v-if="activeGroup" ref="modelPanel" class="models-panel" role="menu" :aria-label="activeGroup.provider + '模型'">
        <button v-for="model in activeGroup.models" :key="model.llm_id" type="button" role="menuitemradio" :aria-checked="model.llm_id === modelValue" :class="{ selected: model.llm_id === modelValue }" :title="model.model" @click="selectModel(model.llm_id)" @keydown.left.prevent="backToProviders" @keydown.down.prevent="focusSibling($event, 1)" @keydown.up.prevent="focusSibling($event, -1)"><ProviderLogo class="dropdown-option-logo" :provider="model.provider" :base-url="model.base_url"/><span>{{ modelDisplayName(model) }}</span><small>{{ model.user_id === '0' ? '内置' : '我的' }}</small><UiIcon v-if="model.llm_id === modelValue" name="check"/></button>
      </div>
    </div>
  </el-popover>
</template>
<style scoped>
.provider-model-picker{display:flex;align-items:center;gap:8px;width:235px;max-width:100%;min-height:43px;padding:8px 10px;border:1px solid #d8e6fb;border-radius:10px;background:#fbfdff;font:inherit;font-size:13px;color:#365579;cursor:pointer;box-sizing:border-box}.provider-model-picker>span:not(.provider-logo){flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:left}.provider-model-picker>.provider-logo{width:23px;height:23px;border-radius:6px;background:transparent}.provider-model-picker>.p-icon{width:16px;height:16px;flex:none;color:#91a2ba}.provider-model-picker:disabled{opacity:.6;cursor:not-allowed}.provider-model-picker:focus-visible{outline:2px solid #a7c7ff;outline-offset:2px}.provider-model-panels{display:flex;max-width:100%;min-width:0;gap:0;color:#385071}.provider-panel{width:174px;flex:none}.models-panel{flex:1;min-width:0;border-left:1px solid #edf2f9;padding-left:5px;margin-left:5px}.provider-panel,.models-panel{max-height:270px;overflow-y:auto;scrollbar-width:thin}.provider-panel>button,.models-panel>button{display:flex;align-items:center;gap:9px;width:100%;min-height:42px;border:0;border-radius:8px;background:transparent;padding:8px 10px;font:inherit;font-size:13px;color:#385071;text-align:left;cursor:pointer}.provider-panel>button>.provider-logo{width:25px;height:25px;border-radius:6px;background:transparent}.provider-panel>button>span:not(.provider-logo),.models-panel>button>span{min-width:0;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.provider-panel>button>.p-icon,.models-panel>button>.p-icon{width:16px;height:16px;flex:none;color:#93a7c1}.provider-panel>button.active,.provider-panel>button:hover,.models-panel>button:hover,.models-panel>button.selected{color:#176aff;background:#f0f6ff}.models-panel>button.selected>.p-icon{color:#176aff}.models-panel small{flex:none;color:#91a2ba;font-size:10px}.provider-panel button:focus-visible,.models-panel button:focus-visible{outline:2px solid #aac9ff;outline-offset:-2px}.picker-empty{font-size:12px;color:#92a0b6;padding:12px 8px;margin:0}:global(.provider-model-menu){border-radius:12px;border-color:#dfe9f7;box-shadow:0 8px 28px #183e7514;max-width:calc(100vw - 20px);padding:6px!important;box-sizing:border-box}
@media(max-width:700px){.provider-model-picker{width:160px;min-height:37px;padding:6px 9px}.provider-panel{width:120px}.provider-panel>button,.models-panel>button{gap:5px;padding:8px 6px}.provider-panel>button>.provider-logo{width:20px;height:20px}.models-panel small{display:none}}
/* 向左展开二级列表，保持厂商列的位置稳定。 */
.provider-model-panels{align-items:flex-end}.provider-panel{order:1;margin-left:auto}.models-panel{order:0;border-left:0;border-right:1px solid #edf2f9;padding-left:0;padding-right:5px;margin-left:0;margin-right:5px}
@media(max-width:700px){.provider-panel{width:174px}}
</style>
