<script setup lang="ts">
import CatalogHeader from '../../components/CatalogHeader.vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { ElConfigProvider } from 'element-plus'
import UiIcon from '../../components/UiIcon.vue'
import FolderGlyph from '../../components/FolderGlyph.vue'
import { getKnowledgeListAPI, createKnowledgeAPI, updateKnowledgeAPI, deleteKnowledgeAPI, type KnowledgeResponse } from '../../apis/knowledge'
import { formatDataDate, readableBytes, storedSizeBytes } from '../../utils/data-pages'
const router = useRouter()

const category = ref('all')
const knowledges = ref<KnowledgeResponse[]>([]), loading = ref(false), loadError = ref('')
const search = ref(''), sort = ref('updated'), view = ref('grid'), page = ref(1), pageSize = ref(12)
const dialogOpen = ref(false), saving = ref(false), saveError = ref(''), editingId = ref(''), formRef = ref<FormInstance>()
const form = reactive({ name:'', description:'' })
const filteredKnowledges = computed(() => knowledges.value.filter(item => (category.value === 'all' || (category.value === 'populated' ? item.count > 0 : !item.count)) && [item.name,item.description].join(' ').toLowerCase().includes(search.value.trim().toLowerCase())).sort((a,b) => sort.value === 'name' ? a.name.localeCompare(b.name,'zh-CN') : sort.value === 'count' ? (b.count || 0) - (a.count || 0) : (Date.parse(b.update_time || b.create_time) || 0) - (Date.parse(a.update_time || a.create_time) || 0)))
const visibleKnowledges = computed(() => filteredKnowledges.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value))
const totalDocuments = computed(() => knowledges.value.reduce((sum,item) => sum + (item.count || 0),0))
const totalSize = computed(() => readableBytes(knowledges.value.reduce((sum,item) => sum + storedSizeBytes(item.file_size),0)))
const newest = computed(() => [...knowledges.value].sort((a,b) => (Date.parse(b.update_time || b.create_time) || 0) - (Date.parse(a.update_time || a.create_time) || 0))[0])
function shortDay(value:string) {
  const date = formatDataDate(value,false)
  if (date === '—') return date
  const today = formatDataDate(new Date().toISOString(),false)
  const yesterday = new Date(); yesterday.setDate(yesterday.getDate()-1)
  return date === today ? '今天' : date === formatDataDate(yesterday.toISOString(),false) ? '昨天' : date.slice(5)
}
function updatedLabel(item:KnowledgeResponse) {
  const value=item.update_time || item.create_time
  const day=shortDay(value)
  return day === '今天' || day === '昨天' ? `${day} ${formatDataDate(value).slice(-5)} 更新` : `${formatDataDate(value,false)} 更新`
}
function folderTheme(item:KnowledgeResponse) {
  if (/制度/.test(item.name)) return 'green'
  if (/技术/.test(item.name)) return 'purple'
  if (/客服|客户/.test(item.name)) return 'orange'
  if (/行业/.test(item.name)) return 'cyan'
  if (/团队/.test(item.name)) return 'rose'
  return 'blue'
}
watch([search,sort,pageSize,category],() => { page.value=1 })
let listRequest = 0
async function fetchKnowledges() {
  const id = ++listRequest

  loading.value = true; loadError.value = ''
  try {
    const response = await getKnowledgeListAPI()
    if (id !== listRequest) return
    if (response.data.status_code !== 200) throw new Error(response.data.status_message || '知识库加载失败')
    knowledges.value = response.data.data || []
    page.value = Math.min(page.value, Math.max(1, Math.ceil(filteredKnowledges.value.length / pageSize.value)))
  } catch(error:any) { if (id === listRequest) loadError.value = error.message || '知识库加载失败，请重试' }
  finally { if (id === listRequest) loading.value = false }
}
function openEditor(item?:KnowledgeResponse) {
  editingId.value=item?.id || ''; form.name=item?.name || ''; form.description=item?.description || ''; saveError.value=''; dialogOpen.value=true
  formRef.value?.clearValidate()
}
const rules:FormRules={ name:[{required:true,message:'请输入知识库名称',trigger:'blur'},{min:2,max:10,message:'名称长度为 2—10 个字符',trigger:'blur'}],description:[{validator:(_rule,value,callback) => { const text=value.trim(); callback(text && (text.length<10 || text.length>200) ? new Error('描述长度为 10—200 个字符') : undefined) },trigger:'blur'}] }
async function saveKnowledge() {
  if (saving.value) return
  saving.value=true; saveError.value=''
  try {
    if (!await formRef.value?.validate().catch(() => false)) return
    const data={knowledge_name:form.name.trim(),knowledge_desc:form.description.trim() || null}
    const response=editingId.value ? await updateKnowledgeAPI({knowledge_id:editingId.value,...data}) : await createKnowledgeAPI(data)
    if(response.data.status_code !== 200) throw new Error(response.data.status_message || '保存失败')
    ElMessage.success(editingId.value ? '知识库已更新' : '知识库已创建'); dialogOpen.value=false; await fetchKnowledges()
  } catch(error:any) { saveError.value=typeof error.response?.data?.detail==='string' ? error.response.data.detail : error.message || '保存失败，请重试' }
  finally {saving.value=false}
}
async function removeKnowledge(item:KnowledgeResponse) {

  try {
    await ElMessageBox.confirm(`确定删除知识库“${item.name}”？相关资料将无法继续使用。`,'删除知识库',{type:'warning',confirmButtonText:'删除',cancelButtonText:'取消'})
    const response=await deleteKnowledgeAPI({knowledge_id:item.id})
    if(response.data.status_code!==200) throw new Error(response.data.status_message || '删除失败')
    ElMessage.success('知识库已删除'); await fetchKnowledges()
  } catch(error:any) {if(error!=='cancel' && error!=='close') ElMessage.error(error.message || '删除失败')}
}
function openFiles(item:KnowledgeResponse) { router.push({name:'knowledge-file',params:{knowledgeId:item.id},query:{name:item.name}}) }

onMounted(fetchKnowledges)
</script>
<template>
<div class="b3-page b3-knowledge catalog-page">
  <CatalogHeader title="知识库" subtitle="打造你的专属知识空间" description="让企业知识成为 AI 的可靠来源，统一管理文档与知识内容"><template #actions><button class="primary-button" @click="openEditor()"><UiIcon name="plus"/>创建知识库</button></template></CatalogHeader>
  <section class="stat-grid" aria-label="知识库概览"><article v-for="stat in [{label:'知识库',value:knowledges.length,icon:'book'},{label:'文档',value:totalDocuments,icon:'file'},{label:'文档体积',value:totalSize,icon:'database'},{label:'最近更新',value:newest ? shortDay(newest.update_time || newest.create_time) : '—',icon:'clock'}]" :key="stat.label" class="stat-card"><span class="stat-icon"><UiIcon :name="stat.icon"/></span><div class="stat-copy"><span class="stat-label">{{stat.label}}</span><strong class="stat-value">{{ loadError ? '—' : stat.value }}</strong></div><UiIcon class="stat-chevron" name="chevron-right"/></article></section>
  <div class="table-toolbar"><label class="search-field"><UiIcon name="search"/><input v-model="search" type="search" placeholder="搜索知识库名称、描述…" aria-label="搜索知识库"></label><div class="knowledge-controls"><el-select v-model="category" aria-label="知识库分类" class="catalog-select"><el-option value="all" label="全部知识库"/><el-option value="populated" label="有文档"/><el-option value="empty" label="暂无文档"/></el-select><label class="knowledge-sort"><el-select v-model="sort" aria-label="知识库排序" class="catalog-select"><el-option value="updated" label="最近更新"/><el-option value="count" label="文档数量"/><el-option value="name" label="名称排序"/></el-select></label><div class="view-switch" role="group" aria-label="知识库视图"><button :class="{active:view==='grid'}" :aria-pressed="view==='grid'" aria-label="网格视图" @click="view='grid'"><UiIcon name="grid"/></button><button :class="{active:view==='list'}" :aria-pressed="view==='list'" aria-label="列表视图" @click="view='list'"><UiIcon name="list"/></button></div></div></div>
  <div v-if="loadError" class="error-banner" role="alert"><span>{{loadError}}</span><button :disabled="loading" @click="fetchKnowledges">重新加载</button></div>
  <section class="knowledge-grid" :class="{'list-view':view==='list'}" v-loading="loading" :aria-busy="loading"><article v-for="item in visibleKnowledges" :key="item.id" class="knowledge-card"><el-dropdown class="knowledge-more" trigger="click"><button class="more-button" :aria-label="`${item.name}的更多操作`"><UiIcon name="more"/></button><template #dropdown><el-dropdown-menu><el-dropdown-item @click="openEditor(item)"><UiIcon name="edit"/><span>编辑知识库</span></el-dropdown-item><el-dropdown-item @click="removeKnowledge(item)" class="dropdown-danger-action"><UiIcon name="trash"/><span>删除知识库</span></el-dropdown-item></el-dropdown-menu></template></el-dropdown><router-link class="knowledge-card-body" :to="{name:'knowledge-file',params:{knowledgeId:item.id},query:{name:item.name}}" :aria-label="`打开知识库${item.name}`"><FolderGlyph :theme="folderTheme(item)"/><div class="knowledge-copy"><h2 :title="item.name">{{item.name}}</h2><p class="description" :title="item.description || ''">{{item.description || '暂未填写描述'}}</p></div></router-link><footer class="knowledge-card-footer"><span class="knowledge-enter">查看文档<UiIcon name="arrow"/></span><button class="text-button settings-button" :aria-label="`设置知识库${item.name}`" @click="openEditor(item)"><UiIcon name="edit"/>设置</button></footer></article><div v-if="!loading && !loadError && !filteredKnowledges.length" class="knowledge-empty"><UiIcon name="book"/><h2>{{search || category!=='all' ? '没有匹配的知识库' : '还没有知识库'}}</h2><p>{{search || category!=='all' ? '试试其他关键词或分类' : '创建知识库，开始积累你的资料'}}</p></div></section>
  <footer class="page-footer"><span>共 {{filteredKnowledges.length}} 条</span><ElConfigProvider :locale="zhCn"><el-pagination v-model:current-page="page" v-model:page-size="pageSize" :page-sizes="[6,12,24]" :total="filteredKnowledges.length" layout="prev,pager,next,sizes"/></ElConfigProvider></footer>
  <el-dialog v-model="dialogOpen" :title="editingId ? '编辑知识库' : '创建知识库'" width="500px" append-to-body :close-on-click-modal="!saving" :close-on-press-escape="!saving" :show-close="!saving" destroy-on-close><el-form ref="formRef" :model="form" :rules="rules" label-position="top" :disabled="saving"><el-form-item label="知识库名称" prop="name"><el-input v-model="form.name" placeholder="请输入知识库名称（2—10 个字符）" maxlength="10" show-word-limit/></el-form-item><el-form-item label="知识库描述（可选）" prop="description"><el-input v-model="form.description" type="textarea" :rows="4" maxlength="200" show-word-limit placeholder="描述知识库的内容、用途或使用场景（10—200 个字符）"/></el-form-item></el-form><p v-if="saveError" class="knowledge-save-error" role="alert">{{saveError}}</p><template #footer><el-button :disabled="saving" @click="dialogOpen=false">取消</el-button><el-button type="primary" :loading="saving" @click="saveKnowledge">{{editingId ? '保存' : '创建'}}</el-button></template></el-dialog>
</div>
</template>
<style scoped src="./knowledge-list.css"></style>
