<script setup lang="ts">
import { computed, inject, ref, type Ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import UiIcon from '../../components/UiIcon.vue'
import CapabilityIcon from '../../components/CapabilityIcon.vue'

const router = useRouter()
const sessions = inject<Ref<any[]>>('workspaceSessions', ref([]))
const sessionsLoading = inject<Ref<boolean>>('workspaceSessionsLoading', ref(false))
const sessionsError = inject<Ref<string>>('workspaceSessionsError', ref(''))
const refreshSessions = inject<() => Promise<void>>('refreshWorkspaceSessions', async () => {})
const openSession = inject<(id: string) => void>('openWorkspaceSession', () => {})
const deleteSession = inject<(id: string, event: Event) => Promise<void>>('deleteWorkspaceSession', async () => {})
const query = ref(''), search = ref(''), statusFilter = ref('all'), webSearch = ref(false)
const fileInput = ref<HTMLInputElement>(), filesReading = ref(false), navigating = ref(false)
const attachments = ref<Array<{ id: string; name: string; text: string }>>([])
const scenarios = [
  { kind: 'research', title: '深度调研', description: '帮你进行专业的深度研究，从海量信息中提炼关键洞察与结论', prompt: '请帮我调研一个产品并整理方案', search: true },
  { kind: 'writing', title: '内容创作', description: '辅助你进行各类内容创作，包括文章、报告、邮件等', prompt: '请帮我撰写一份结构清晰的产品方案', search: false },
  { kind: 'analytics', title: '数据分析', description: '帮你分析和解读数据，生成图表、洞察和分析报告', prompt: '请分析以下数据，并整理主要发现与建议', search: false }
]
function recordStatus(session: any) {
  const latest = Array.isArray(session.contexts) ? session.contexts[session.contexts.length - 1] : null
  if (typeof latest?.answer === 'string' && latest.answer.trim()) return { id: 'result', label: '已有结果', icon: 'check' }
  if (latest?.guide_prompt) return { id: 'plan', label: '已有规划', icon: 'file' }
  return { id: 'pending', label: '暂无结果', icon: 'clock' }
}
const displayedSessions = computed(() => sessions.value.filter(session =>
  session.title.toLowerCase().includes(search.value.trim().toLowerCase()) &&
  (statusFilter.value === 'all' || recordStatus(session).id === statusFilter.value)))
function formatDate(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(date)
}
function applyScenario(scenario: typeof scenarios[number]) { query.value = scenario.prompt; webSearch.value = scenario.search }
async function readAttachments(event: Event) {
  const input = event.target as HTMLInputElement
  filesReading.value = true
  try {
    for (const file of Array.from(input.files || [])) {
      if (!/\.(txt|md|csv|json)$/i.test(file.name)) { ElMessage.warning('请选择 TXT、Markdown、CSV 或 JSON 文件'); continue }
      if (file.size > 2 * 1024 * 1024) { ElMessage.warning(`${file.name} 超过 2MB`); continue }
      const text = await file.text()
      if (attachments.value.length >= 5 || attachments.value.reduce((n, item) => n + item.text.length, 0) + text.length > 16000) {
        ElMessage.warning('最多添加 5 个文件，附件正文合计不超过 16000 字符'); continue
      }
      attachments.value.push({ id: crypto.randomUUID(), name: file.name, text })
    }
  } catch { ElMessage.error('读取文件失败，请重试') }
  finally { input.value = ''; filesReading.value = false }
}
async function startTask() {
  if (!query.value.trim() || filesReading.value || navigating.value) return
  navigating.value = true
  const attachmentText = attachments.value.map(item => `\n\n附件：${item.name}\n${item.text}`).join('')
  try { await router.push({ name: 'taskGraphPage', query: { query: query.value.trim() + attachmentText, webSearch: String(webSearch.value) } }) }
  finally { navigating.value = false }
}
async function removeSession(session: any, event: Event) {
  try {
    await ElMessageBox.confirm(`确定删除“${session.title}”及其任务记录？`, '删除任务', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
    await deleteSession(session.sessionId, event)
  } catch { /* Dismissing the confirmation leaves the record unchanged. */ }
}
</script>
<template>
  <div class="workspace-home">
    <header class="page-heading"><h1>工作台</h1><p>描述目标，开始执行任务。</p></header>
    <form class="task-composer surface" :aria-busy="navigating" @submit.prevent="startTask">
      <textarea v-model="query" aria-label="任务目标" placeholder="请帮我调研一个产品并整理方案" @keydown.ctrl.enter.prevent="startTask" @keydown.meta.enter.prevent="startTask"/>
      <div v-if="attachments.length" class="attachments"><span v-for="item in attachments" :key="item.id"><UiIcon name="file"/>{{ item.name }}<button type="button" :aria-label="`移除附件 ${item.name}`" @click="attachments = attachments.filter(file => file.id !== item.id)"><UiIcon name="close"/></button></span></div>
      <div class="composer-actions">
        <div class="composer-options">
          <input ref="fileInput" type="file" accept=".txt,.md,.csv,.json" multiple hidden @change="readAttachments">
          <button class="option-button" type="button" :disabled="filesReading" title="支持 TXT、Markdown、CSV、JSON，单文件不超过 2MB" @click="fileInput?.click()"><UiIcon name="paperclip"/>{{ filesReading ? '读取中…' : '添加附件' }}</button>
          <button class="option-button" :class="{ selected: webSearch }" type="button" :aria-pressed="webSearch" @click="webSearch = !webSearch"><UiIcon name="globe"/>联网搜索</button>
          <router-link class="option-button" to="/knowledge" title="管理知识库"><UiIcon name="book"/>知识库</router-link>
        </div>
        <button class="primary-button" type="submit" :disabled="!query.trim() || filesReading || navigating"><UiIcon name="send"/>{{ navigating ? '正在进入…' : '开始执行' }}</button>
      </div>
    </form>
    <section class="scenario-grid" aria-label="任务场景">
      <button v-for="scenario in scenarios" :key="scenario.kind" class="scenario-card surface" @click="applyScenario(scenario)"><CapabilityIcon :kind="scenario.kind"/><span class="scenario-copy"><strong>{{ scenario.title }}</strong><span>{{ scenario.description }}</span></span><UiIcon class="scenario-arrow" name="chevron-right"/></button>
    </section>
    <section class="recent-tasks surface" aria-labelledby="recent-heading">
      <div class="recent-heading"><h2 id="recent-heading">最近任务</h2><div class="table-filters"><label class="search-field"><UiIcon name="search"/><input v-model="search" type="search" placeholder="搜索任务名称…" aria-label="搜索任务名称"></label><el-select v-model="statusFilter" aria-label="任务状态" class="catalog-select"><el-option value="all" label="全部状态"/><el-option value="result" label="已有结果"/><el-option value="plan" label="已有规划"/><el-option value="pending" label="暂无结果"/></el-select></div></div>
      <div v-if="sessionsError" class="error-state" role="alert"><p>{{ sessionsError }}</p><button class="option-button" :disabled="sessionsLoading" @click="refreshSessions">重新加载</button></div>
      <div v-else class="table-scroll" v-loading="sessionsLoading" :aria-busy="sessionsLoading">
        <table><thead><tr><th>任务名称</th><th>创建时间</th><th>状态</th><th>操作</th></tr></thead><tbody>
          <tr v-for="(session, index) in displayedSessions" :key="session.sessionId"><td><button class="task-name" @click="openSession(session.sessionId)"><span class="task-file" :class="`color-${index % 3}`"><UiIcon name="file"/></span><span :title="session.title">{{ session.title }}</span></button></td><td class="task-date">{{ formatDate(session.createTime) }}</td><td><span class="status-badge" :class="recordStatus(session).id"><UiIcon :name="recordStatus(session).icon"/>{{ recordStatus(session).label }}</span></td><td><div class="row-actions"><button class="view-button" @click="openSession(session.sessionId)">查看</button><el-dropdown trigger="click"><button class="more-button" :aria-label="`${session.title}的更多操作`"><UiIcon name="more"/></button><template #dropdown><el-dropdown-menu><el-dropdown-item @click="openSession(session.sessionId)">打开任务</el-dropdown-item><el-dropdown-item @click="removeSession(session, $event)" class="dropdown-danger-action"><UiIcon name="trash"/><span>删除任务</span></el-dropdown-item></el-dropdown-menu></template></el-dropdown></div></td></tr>
        </tbody></table>
        <div v-if="!sessionsLoading && !displayedSessions.length" class="empty-state"><UiIcon name="file"/><h3>{{ search || statusFilter !== 'all' ? '没有匹配的任务' : '还没有任务记录' }}</h3><p>{{ search || statusFilter !== 'all' ? '试试其他关键词或状态' : '写下目标，从上方开始你的第一个任务' }}</p></div>
      </div>
    </section>
  </div>
</template>
<style scoped src="./workspace-home.css"></style>
