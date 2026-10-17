<script setup lang="ts">
import CatalogHeader from '../../components/CatalogHeader.vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import UiIcon from '../../components/UiIcon.vue'
import { modelDisplayName } from '../../utils/model-display'
import { modelProviderDisplayName } from '../../utils/model-provider-brand'
import { useUserStore } from '../../store/user'
import ProviderLogo from '../../components/ProviderLogo.vue'
import { getVisibleLLMsAPI, deleteLLMAPI, type LLMResponse } from '../../apis/llm'
import { formatDataDate, safeResourceUrl } from '../../utils/data-pages'

const router = useRouter(), userStore=useUserStore()
const models = ref<LLMResponse[]>([]), loading = ref(false), loadError = ref(''), deleting = ref('')
const search = ref(''), filter = ref('all'), page = ref(1), pageSize = 10
const types = [{ id: 'all', label: '全部模型' }, { id: 'LLM', label: '对话模型' }, { id: 'Embedding', label: '向量模型' }, { id: 'Rerank', label: '重排模型' }]
const visibleTypes = computed(() => types.filter(type => type.id !== 'Rerank' || models.value.some(model => model.llm_type === 'Rerank')))
const filteredModels = computed(() => models.value.filter(model => (filter.value === 'all' || model.llm_type === filter.value) &&
  [model.model,model.show_model, model.provider, modelProviderDisplayName(model.provider)].join(' ').toLowerCase().includes(search.value.trim().toLowerCase())))
const displayedModels = computed(() => filteredModels.value.slice((page.value - 1) * pageSize, page.value * pageSize))
watch([search, filter], () => { page.value = 1 })
async function fetchModels() {
  if (loading.value) return
  loading.value = true; loadError.value = ''
  try {
    const response = await getVisibleLLMsAPI()
    if (response.data.status_code !== 200) throw new Error(response.data.status_message || '模型列表加载失败')
    const data = response.data.data || {}
    models.value = Array.isArray(data) ? data : Object.values(data).flat()
    page.value = Math.min(page.value, Math.max(1, Math.ceil(filteredModels.value.length / pageSize)))
  } catch (error: any) { loadError.value = error.message || '模型列表加载失败，请重试' }
  finally { loading.value = false }
}
function typeLabel(type: string) { return types.find(item => item.id === type)?.label || type }
function isOfficial(model: LLMResponse) { return model.user_id === '0' }
async function deleteModel(model: LLMResponse) {
  if (isOfficial(model) || deleting.value) return
  try {
    await ElMessageBox.confirm(`确定删除模型“${model.model}”？`, '删除模型', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
    deleting.value = model.llm_id
    const response = await deleteLLMAPI({ llm_id: model.llm_id })
    if (response.data.status_code !== 200) throw new Error(response.data.status_message || '删除失败')
    ElMessage.success('模型已删除'); await fetchModels()
  } catch (error: any) { if (error !== 'cancel' && error !== 'close') ElMessage.error(error.message || '删除失败') }
  finally { deleting.value = '' }
}
onMounted(fetchModels)
</script>
<template>
  <div class="b3-page b3-models catalog-page">
    <CatalogHeader title="模型" subtitle="管理你的 AI 模型服务" description="连接大语言模型与向量模型，统一管理模型服务与接口配置"><template #actions><button class="primary-button" @click="router.push('/model/editor')"><UiIcon name="plus-circle"/>添加模型</button></template></CatalogHeader>
    <section class="data-surface model-panel">
      <div class="table-toolbar"><div class="model-tabs" role="group" aria-label="模型分类"><button v-for="type in visibleTypes" :key="type.id" :class="{active:filter === type.id}" :aria-pressed="filter === type.id" @click="filter = type.id">{{ type.label }} ({{ type.id === 'all' ? models.length : models.filter(model => model.llm_type === type.id).length }})</button></div><div class="toolbar-right"><label class="search-field"><UiIcon name="search"/><input v-model="search" type="search" placeholder="搜索模型名称、服务提供方" aria-label="搜索模型"></label></div></div>
      <div v-if="loadError" class="error-banner" role="alert"><span>{{ loadError }}</span><button :disabled="loading" @click="fetchModels">重新加载</button></div>
      <div class="table-scroll" v-loading="loading" :aria-busy="loading"><table class="data-table model-table"><colgroup><col class="name-column"><col class="provider-column"><col class="type-column"><col class="url-column"><col class="time-column"><col class="actions-column"></colgroup><thead><tr><th>模型名称</th><th>服务提供方</th><th>类型</th><th>接口地址</th><th>更新时间</th><th>操作</th></tr></thead><tbody><tr v-for="model in displayedModels" :key="model.llm_id"><td><div class="model-name"><ProviderLogo :provider="model.provider" :base-url="model.base_url" :model="model.model" :type="model.llm_type" model-mark/><div><strong :title="model.model">{{modelDisplayName(model)}}</strong><small>{{model.model}}</small></div></div></td><td><span class="provider-name"><ProviderLogo :provider="model.provider" :base-url="model.base_url"/><span :title="modelProviderDisplayName(model.provider)">{{ modelProviderDisplayName(model.provider) }}</span></span></td><td><span class="model-type" :class="model.llm_type">{{ typeLabel(model.llm_type) }}</span></td><td><a v-if="safeResourceUrl(model.base_url)" class="model-url" :href="safeResourceUrl(model.base_url)" target="_blank" rel="noopener noreferrer" :title="model.base_url"><span>{{ model.base_url }}</span><UiIcon name="external"/></a><span v-else class="muted">{{ model.base_url || '—' }}</span></td><td class="date-cell">{{ formatDataDate(model.update_time || model.create_time) }}</td><td><div class="row-actions"><button class="text-button" :disabled="isOfficial(model)&&userStore.userInfo?.id!=='1'" :title="isOfficial(model) ? '编辑展示名称' : '编辑模型'" @click="router.push({path:'/model/editor',query:{id:model.llm_id}})"><UiIcon name="edit"/>编辑</button><button class="text-button danger" :disabled="isOfficial(model) || !!deleting" @click="deleteModel(model)"><UiIcon name="trash"/>{{ deleting === model.llm_id ? '删除中' : '删除' }}</button></div></td></tr><tr v-if="!loading && !displayedModels.length"><td colspan="6" class="table-empty">{{ loadError ? '模型数据暂时无法读取' : search || filter !== 'all' ? '没有匹配的模型，试试其他关键词或分类' : '暂无模型，添加模型后即可使用' }}</td></tr></tbody></table></div>
      <footer class="page-footer"><span>共 {{ filteredModels.length }} 条数据</span><el-pagination v-model:current-page="page" :page-size="pageSize" :total="filteredModels.length" layout="prev,pager,next"/></footer>
    </section>
  </div>
</template>
<style scoped src="./model-list.css"></style>
