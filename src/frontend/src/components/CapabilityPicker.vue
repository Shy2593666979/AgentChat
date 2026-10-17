<script setup lang="ts">
import { computed, ref } from 'vue'
import UiIcon from './UiIcon.vue'
const props = defineProps<{ modelValue: string[]; label: string; icon: string; options: Array<{ id: string; name: string }>; loading?: boolean; error?: string; managePath: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string[]]; retry: [] }>()
const search = ref('')
const visibleOptions = computed(() => props.options.filter(item => String(item.name || item.id).toLowerCase().includes(search.value.trim().toLowerCase())))
const selectedOptions = computed(() => props.modelValue.map(id => props.options.find(option => option.id === id) || { id, name: `未找到的资源（${id}）` }))
function remove(id: string) { emit('update:modelValue', props.modelValue.filter(value => value !== id)) }
</script>
<template>
  <div class="capability-group">
    <div class="capability-row"><h3><UiIcon :name="icon"/>{{ label }}</h3><el-popover placement="bottom-end" :width="320" trigger="click"><div class="resource-picker" v-loading="loading"><el-input v-model="search" :placeholder="`搜索${label}`" clearable :aria-label="`搜索${label}`"/><div class="resource-options"><el-checkbox-group :model-value="modelValue" @update:model-value="emit('update:modelValue', $event as string[])"><el-checkbox v-for="item in visibleOptions" :key="item.id" :label="item.id"><span class="dropdown-option-row"><UiIcon :name="icon"/><span>{{item.name}}</span></span></el-checkbox></el-checkbox-group><p v-if="!loading && !visibleOptions.length" class="picker-empty">{{ search ? '没有匹配的资源' : '暂无可用资源' }}</p></div><router-link class="manage-link" :to="managePath">管理{{ label }} →</router-link></div><template #reference><button class="add-button" type="button"><UiIcon name="plus"/>选择{{ label }}</button></template></el-popover></div>
    <div v-if="selectedOptions.length" class="resource-chips"><span v-for="item in selectedOptions" :key="item.id" class="resource-chip" :title="item.name"><UiIcon :name="icon"/><span>{{ item.name }}</span><button type="button" :aria-label="`移除${item.name}`" @click="remove(item.id)"><UiIcon name="close"/></button></span></div>
    <p v-else class="unselected">{{ loading ? '正在加载…' : `尚未选择${label}` }}</p>
    <p v-if="error" class="resource-error" role="alert">{{ error }}<button type="button" :disabled="loading" @click="emit('retry')">重试</button></p>
  </div>
</template>
<style scoped>
.capability-group{margin-top:18px}.capability-row{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:8px}.capability-row h3{display:flex;gap:11px;align-items:center;font-size:16px;font-weight:550;margin:0;color:#17264b}.capability-row h3 :deep(.p-icon){width:23px;height:23px}.add-button{display:flex;align-items:center;gap:6px;border:1px solid #d1e1ff;background:#f5f9ff;border-radius:9px;color:#1767ff;font:inherit;font-size:14px;padding:6px 10px;cursor:pointer;white-space:nowrap}.add-button:hover{background:#eaf3ff}.add-button :deep(.p-icon){width:16px;height:16px}.resource-chips{display:flex;gap:8px;flex-wrap:wrap}.resource-chip{display:inline-flex;align-items:center;gap:8px;max-width:100%;padding:5px 10px;border:1px solid #e5edf8;border-radius:18px;background:#f5f8fd;color:#536584;font-size:13px;line-height:1.5}.resource-chip>span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.resource-chip :deep(.p-icon){width:17px;height:17px;flex:none;color:#1767ff}.resource-chip button{display:grid;place-items:center;border:0;background:transparent;cursor:pointer;padding:2px}.resource-chip button :deep(.p-icon){width:12px;height:12px;color:#8291ad}.unselected{margin:0;font-size:13px;line-height:1.8;color:#8a98b3}.resource-options{max-height:250px;overflow:auto;margin:12px 0}.resource-options :deep(.el-checkbox-group){display:flex;flex-direction:column}.resource-options :deep(.el-checkbox){margin-right:0;height:auto;min-height:38px}.resource-options :deep(.el-checkbox__label){white-space:normal;overflow-wrap:anywhere}.picker-empty{padding:14px;text-align:center;color:#8a98b3}.manage-link{font-size:13px;color:#246bff;text-decoration:none}.add-button:focus-visible,.resource-chip button:focus-visible{outline:2px solid #82b1ff;outline-offset:3px}
</style>
<style scoped>
.resource-error{margin-top:8px;display:flex;align-items:center;gap:10px;color:#b34a53;font-size:13px;line-height:1.6}.resource-error button{font:inherit;border:0;background:transparent;padding:2px 5px;color:#1266ff;cursor:pointer}.resource-error button:disabled{opacity:.5}
</style>
