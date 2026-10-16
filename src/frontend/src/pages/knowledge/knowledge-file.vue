<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type UploadProps, type UploadInstance } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { ElConfigProvider } from 'element-plus'
import UiIcon from '../../components/UiIcon.vue'
import FolderGlyph from '../../components/FolderGlyph.vue'
import DocumentBadge from '../../components/DocumentBadge.vue'
import { getKnowledgeFileListAPI, deleteKnowledgeFileAPI, createKnowledgeFileAPI, type KnowledgeFileResponse } from '../../apis/knowledge-file'

import { getKnowledgeListAPI, type KnowledgeResponse } from '../../apis/knowledge'
import { fileState, formatDataDate, readableBytes, safeResourceUrl } from '../../utils/data-pages'

interface DocumentRow extends KnowledgeFileResponse { chunk_count?:number; chunks_count?:number }
interface UploadRow { uid:number; knowledgeId:string; name:string; percent:number; state:'uploading'|'parsing'|'success'|'error'|'pending'; url?:string; message?:string }
const route=useRoute(), router=useRouter()

const returnRoute = { path: '/knowledge' }


const knowledgeId=computed(() => String(route.params.knowledgeId || ''))
const metadata=ref<KnowledgeResponse>()
const knowledgeName=computed(() => metadata.value?.name || String(route.query.name || '知识库文档'))
const files=ref<DocumentRow[]>([]), loading=ref(false), loadError=ref(''), deleting=ref(false)
const search=ref(''), filter=ref('all'), page=ref(1), pageSize=ref(10), sort=ref('time'), order=ref('desc')
const selectedIds=ref(new Set<string>())
const uploadDialog=ref(false), uploadRef=ref<UploadInstance>(), uploads=reactive<UploadRow[]>([])
const uploading=computed(() => uploads.some(item => ['uploading','parsing'].includes(item.state)))
const filteredFiles=computed(() => files.value.filter(file => file.file_name.toLowerCase().includes(search.value.trim().toLowerCase()) && (filter.value==='all' || fileState(file.status).id===filter.value)).sort((a,b) => {
  const value=sort.value==='name' ? a.file_name.localeCompare(b.file_name,'zh-CN') : sort.value==='size' ? a.file_size-b.file_size : (Date.parse(a.create_time)||0)-(Date.parse(b.create_time)||0)
  return order.value==='desc' ? -value : value
}))
const displayedFiles=computed(() => filteredFiles.value.slice((page.value-1)*pageSize.value,page.value*pageSize.value))
const allSelected=computed(() => displayedFiles.value.length>0 && displayedFiles.value.every(file => selectedIds.value.has(file.id)))
const someSelected=computed(() => displayedFiles.value.some(file => selectedIds.value.has(file.id)))
const processingCount=computed(() => files.value.filter(file => fileState(file.status).id==='process').length)
const completedCount=computed(() => files.value.filter(file => fileState(file.status).id==='success').length)
let disposed=false, requestId=0, pollTimer:ReturnType<typeof setTimeout> | undefined
const uploadHeaders=computed(() => ({ Authorization:'Bearer '+(localStorage.getItem('token') || '') }))
function toggleSelected(id:string) { const next=new Set(selectedIds.value); next.has(id) ? next.delete(id) : next.add(id); selectedIds.value=next }
function toggleAll() { const next=new Set(selectedIds.value); for(const file of displayedFiles.value) allSelected.value ? next.delete(file.id) : next.add(file.id); selectedIds.value=next }
function setSort(value:string) { order.value=sort.value===value && order.value==='desc' ? 'asc' : 'desc'; sort.value=value; page.value=1 }
function chunkCount(file:DocumentRow) { const value=file.chunk_count ?? file.chunks_count; return typeof value==='number' && Number.isFinite(value) ? value : '—' }
function schedulePoll() { clearTimeout(pollTimer); if (!disposed && processingCount.value) pollTimer=setTimeout(() => fetchFiles(false),15000) }
async function fetchFiles(showLoading=true) {

  const id=++requestId, requestedKnowledge=knowledgeId.value
  if (showLoading) loading.value=true
  try {
    const response=await getKnowledgeFileListAPI(requestedKnowledge)
    if (disposed || id!==requestId) return
    if (response.data.status_code!==200) throw new Error(response.data.status_message || '文档列表加载失败')
    files.value=response.data.data || []; loadError.value=''
    selectedIds.value=new Set([...selectedIds.value].filter(id => files.value.some(file => file.id===id)))
    page.value=Math.min(page.value,Math.max(1,Math.ceil(filteredFiles.value.length/pageSize.value)))
    for(const item of uploads) {
      const file=files.value.find(file => item.url && file.oss_url===item.url)
      if (!file) continue
      const state=fileState(file.status).id
      if(state==='success') { item.state='success'; item.message=undefined }
      if(state==='fail') { item.state='error'; item.message='文档解析失败' }
    }
  } catch(error:any) { if(!disposed && id===requestId) loadError.value=error.message || '文档列表加载失败，请重试' }
  finally { if(!disposed && id===requestId) { loading.value=false; schedulePoll() } }
}
async function removeFiles(ids:string[]) {
  if(!ids.length || deleting.value) return
  try {
    const name=ids.length===1 ? `“${files.value.find(file => file.id===ids[0])?.file_name || '此文档'}”` : `选中的 ${ids.length} 个文档`
    await ElMessageBox.confirm(`确定删除${name}？`,'删除文档',{type:'warning',confirmButtonText:'删除',cancelButtonText:'取消'})
    deleting.value=true
    const results=await Promise.allSettled(ids.map(async id => { const response=await deleteKnowledgeFileAPI({knowledge_file_id:id}); if(response.data.status_code!==200) throw new Error(response.data.status_message || '删除失败') }))
    const failed=ids.filter((_id,index) => results[index].status==='rejected')
    selectedIds.value=new Set(failed)
    if(failed.length) ElMessage.error(`${failed.length} 个文档删除失败，请重试`)
    else ElMessage.success('文档已删除')
    await fetchFiles()
  } catch(error:any) { if(error!=='cancel' && error!=='close') ElMessage.error(error.message || '删除失败') }
  finally { deleting.value=false }
}
const beforeUpload:UploadProps['beforeUpload']=(file) => {

  if(!/\.(pdf|doc|docx|txt|md|xls|xlsx|ppt|pptx|jpg|jpeg|png|gif)$/i.test(file.name)) { ElMessage.warning('请选择 PDF、Office、文本或图片文件'); return false }
  if(file.size>100*1024*1024) { ElMessage.warning('单个文件不能超过 100MB'); return false }
  uploads.push({uid:file.uid,knowledgeId:knowledgeId.value,name:file.name,percent:0,state:'uploading'}); return true
}
const onProgress:UploadProps['onProgress']=(event,file) => { const item=uploads.find(item => item.uid===file.uid); if(item) item.percent=Math.min(100,Math.round(event.percent || 0)) }
const onUploadError:UploadProps['onError']=(_error,file) => { const item=uploads.find(item => item.uid===file.uid); if(item) {item.state='error';item.message='上传失败，请重新选择文件'} }
const onUploadSuccess:UploadProps['onSuccess']=async (response,file) => {
  const item=uploads.find(item => item.uid===file.uid)
  if(!item || disposed) return
  try {
    if(response.status_code!==200 || typeof response.data!=='string') throw new Error(response.status_message || '上传失败')
    item.url=response.data; item.percent=100; item.state='parsing'
    const result=await createKnowledgeFileAPI({knowledge_id:item.knowledgeId,file_url:response.data})
    if(disposed) return
    if(result.data.status_code!==200) throw new Error(result.data.status_message || '解析请求失败')
    item.state='success'; ElMessage.success(`${item.name}已上传并解析`)
  } catch(error:any) {
    if(disposed) return
    item.state=error.code==='ECONNABORTED' ? 'pending' : 'error'
    item.message=error.code==='ECONNABORTED' ? '解析状态待确认，请稍后刷新' : error.message || '解析请求失败'
  } finally { if(!disposed) await fetchFiles(false) }
}
watch([search,filter,pageSize],() => {page.value=1})
watch(knowledgeId, async id => {
  requestId++
  uploadRef.value?.abort(undefined); uploads.splice(0); uploadDialog.value=false
  clearTimeout(pollTimer); files.value=[]; selectedIds.value=new Set(); page.value=1; metadata.value=undefined
  if(!id) { await router.push(returnRoute); return }

  await Promise.allSettled([fetchFiles(),getKnowledgeListAPI().then(response => {if(knowledgeId.value===id && response.data.status_code===200) metadata.value=response.data.data?.find(item => item.id===id)})])
},{immediate:true})
onBeforeUnmount(() => {disposed=true;requestId++;clearTimeout(pollTimer);uploadRef.value?.abort(undefined)})
</script>
<template>
  <div class="b3-page b3-files">
    <header class="data-heading"><div class="heading-title"><FolderGlyph/><div class="heading-copy"><h1 :title="knowledgeName">{{knowledgeName}}</h1><p>{{metadata?.description || '管理知识库中的文档，查看上传与解析状态。'}}</p></div></div><div class="files-actions"><el-button @click="router.push(returnRoute)"><UiIcon name="arrow-left"/>返回知识库</el-button><button class="primary-button" @click="uploadDialog=true"><UiIcon name="upload"/>{{uploading ? '查看上传进度' : '上传文档'}}</button></div></header>
    <section class="stat-grid file-stats" aria-label="文档概览"><article v-for="stat in [{label:'文档',value:files.length,icon:'file'},{label:'处理中',value:processingCount,icon:'clock'},{label:'已完成',value:completedCount,icon:'check'}]" :key="stat.label" class="stat-card"><span class="stat-icon" :class="{'completed-icon':stat.icon==='check'}"><UiIcon :name="stat.icon"/></span><div class="stat-copy"><span class="stat-label">{{stat.label}}</span><strong class="stat-value">{{loadError && !files.length ? '—' : stat.value}}</strong></div></article></section>
    <div class="table-toolbar"><label class="search-field"><UiIcon name="search"/><input v-model="search" type="search" placeholder="搜索文档名称、关键词" aria-label="搜索文档"></label><el-select v-model="filter" class="catalog-select status-filter-select" aria-label="文档状态"><el-option value="all" label="全部状态"/><el-option value="success" label="处理完成"/><el-option value="process" label="处理中"/><el-option value="fail" label="处理失败"/><el-option value="unknown" label="其他状态"/></el-select><button class="refresh-files" :disabled="loading" aria-label="刷新文档" @click="fetchFiles()"><UiIcon name="refresh"/></button></div>
    <div v-if="loadError" class="error-banner" role="alert"><span>{{loadError}}</span><button :disabled="loading" @click="fetchFiles()">重新加载</button></div>
    <section class="data-surface file-table-panel"><div class="table-scroll" v-loading="loading" :aria-busy="loading"><table class="data-table files-table"><colgroup><col class="select-column"><col class="filename-column"><col class="size-column"><col class="chunks-column"><col class="status-column"><col class="upload-column"><col class="file-actions-column"></colgroup><thead><tr><th><input type="checkbox" :checked="allSelected" :indeterminate="someSelected && !allSelected" :disabled="!displayedFiles.length" aria-label="选择此页全部文档" @change="toggleAll"></th><th><button class="sort-heading" @click="setSort('name')">文件名<UiIcon v-if="sort==='name'" :name="order==='desc' ? 'arrow-down' : 'arrow-up'"/></button></th><th><button class="sort-heading" @click="setSort('size')">大小<UiIcon v-if="sort==='size'" :name="order==='desc' ? 'arrow-down' : 'arrow-up'"/></button></th><th>切分数量</th><th>状态</th><th><button class="sort-heading" @click="setSort('time')">上传时间<UiIcon :name="order==='desc' ? 'arrow-down' : 'arrow-up'" v-if="sort==='time'"/></button></th><th>操作</th></tr></thead><tbody><tr v-for="file in displayedFiles" :key="file.id"><td><input type="checkbox" :checked="selectedIds.has(file.id)" :aria-label="`选择${file.file_name}`" @change="toggleSelected(file.id)"></td><td><div class="document-name"><DocumentBadge :filename="file.file_name"/><span :title="file.file_name">{{file.file_name}}</span></div></td><td>{{readableBytes(file.file_size)}}</td><td><span :title="chunkCount(file)==='—' ? '暂无切分统计' : ''">{{chunkCount(file)}}</span></td><td><span class="file-status" :class="fileState(file.status).id"><span class="status-symbol"><UiIcon :name="fileState(file.status).icon"/></span>{{fileState(file.status).label}}</span></td><td class="file-date">{{formatDataDate(file.create_time)}}</td><td><el-dropdown trigger="click"><button class="more-button" :aria-label="`${file.file_name}的更多操作`" :disabled="deleting"><UiIcon name="more"/></button><template #dropdown><el-dropdown-menu><el-dropdown-item v-if="safeResourceUrl(file.oss_url)"><a :href="safeResourceUrl(file.oss_url)" target="_blank" rel="noopener noreferrer">打开原文件</a></el-dropdown-item><el-dropdown-item :disabled="deleting" @click="removeFiles([file.id])" class="dropdown-danger-action"><UiIcon name="trash"/><span>删除文档</span></el-dropdown-item></el-dropdown-menu></template></el-dropdown></td></tr><tr v-if="!loading && !displayedFiles.length"><td colspan="7" class="table-empty">{{loadError ? '文档数据暂时无法读取' : search || filter!=='all' ? '没有匹配的文档，试试其他关键词或状态' : '暂无文档，上传文件开始构建知识库'}}</td></tr></tbody></table></div><footer class="page-footer"><div class="selection-summary"><span>已选择 {{selectedIds.size}} 项，共 {{filteredFiles.length}} 项</span><button v-if="selectedIds.size" class="text-button danger" :disabled="deleting" @click="removeFiles([...selectedIds])"><UiIcon name="trash"/>{{deleting ? '删除中…' : '删除选中'}}</button></div><ElConfigProvider :locale="zhCn"><el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="filteredFiles.length" :page-sizes="[10,20,50]" layout="sizes,prev,pager,next"/></ElConfigProvider></footer></section>
    <el-dialog v-model="uploadDialog" title="上传文档" width="560px" append-to-body :close-on-click-modal="false"><el-upload ref="uploadRef" action="/api/v1/upload" :headers="uploadHeaders" :before-upload="beforeUpload" :on-progress="onProgress" :on-success="onUploadSuccess" :on-error="onUploadError" :show-file-list="false" accept=".pdf,.doc,.docx,.txt,.md,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.gif" multiple drag><div class="upload-drop"><UiIcon name="upload"/><strong>点击或拖拽文件到此处上传</strong><span>支持 PDF、Office、文本、图片等格式<br>单个文件不超过 100MB</span></div></el-upload><div class="upload-queue"><div v-for="item in uploads" :key="item.uid" class="upload-item"><DocumentBadge :filename="item.name"/><div class="upload-copy"><strong :title="item.name">{{item.name}}</strong><span :class="item.state">{{item.state==='uploading' ? `上传中 ${item.percent}%` : item.state==='parsing' ? '上传完成，正在解析…' : item.state==='success' ? '解析完成' : item.message}}</span><el-progress v-if="item.state==='uploading'" :percentage="item.percent" :show-text="false" :stroke-width="5"/></div></div></div><template #footer><el-button @click="uploadDialog=false">{{uploading ? '后台继续处理' : '完成'}}</el-button><el-button v-if="uploads.some(item=>item.state==='pending')" type="primary" :loading="loading" @click="fetchFiles(false)">刷新状态</el-button></template></el-dialog>

  </div>
</template>
<style scoped src="./knowledge-files.css"></style>
