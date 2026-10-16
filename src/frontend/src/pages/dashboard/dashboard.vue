<script setup lang="ts">
import CatalogHeader from '../../components/CatalogHeader.vue'
import SidebarIcon from '../../components/SidebarIcon.vue'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { formatDataDate } from '../../utils/data-pages'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts/core'
import type { ECharts as Chart } from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { getUsageStatsAPI, getUsageCountAPI, getUsageModelsAPI, getUsageAgentsAPI, type UsageDataByDate, type UsageCountByDate, type TokenUsageData } from '../../apis/usage-stats'
import { getConversationListAPI } from '../../apis/history'
import { getWorkspaceSessionsAPI } from '../../apis/workspace'
echarts.use([LineChart, BarChart, GridComponent, TooltipComponent, CanvasRenderer])
const router = useRouter()
const days = ref(1)
const loading = ref(false)
const filters = ref({ model: '', agent: '' })
const models = ref<string[]>([]), agents = ref<string[]>([])
const countData = ref<UsageCountByDate>({}), tokenData = ref<UsageDataByDate>({})
const countsLoaded = ref(false), tokensLoaded = ref(false)
const distributionMetric = ref('tokens')
const showAllActivities = ref(false)
interface Activity { id: string; time: string; kind: string; title: string; source: string; status: string; route: string; tokenUsage?: TokenUsageData }
const activities = ref<Activity[]>([])
const activityError = ref(false)
const trendRef = ref<HTMLElement>(), distributionRef = ref<HTMLElement>()
let trendChart: Chart | undefined, distributionChart: Chart | undefined, observer: ResizeObserver | undefined
let requestId = 0, activityRequestId = 0, disposed = false
const usageError = ref(false)
const today = () => new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Shanghai' }).format(new Date())
const shiftDay = (date: string, offset: number) => new Date(Date.parse(date + 'T00:00:00Z') + offset * 86400000).toISOString().slice(0, 10)
const inRange = (date: string, previous = false) => { const end = shiftDay(today(), previous ? -days.value : 0); return date.slice(0, 10) >= shiftDay(end, 1 - days.value) && date.slice(0, 10) <= end }
const currentCounts = computed(() => Object.entries(countData.value).filter(([date]) => inRange(date)))
const currentTokens = computed(() => Object.entries(tokenData.value).filter(([date]) => inRange(date)))
const callsFor = (previous = false) => Object.entries(countData.value).filter(([date]) => inRange(date, previous)).reduce((sum, [, day]) => sum + Object.values(day.model || {}).reduce((s, v) => s + Number(v || 0), 0), 0)
const tokensFor = (previous = false) => Object.entries(tokenData.value).filter(([date]) => inRange(date, previous)).reduce((sum, [, day]) => sum + Object.values(day.model || {}).reduce((s, v) => s + Number(v.total_tokens ?? ((v.input_tokens || 0) + (v.output_tokens || 0))), 0), 0)
const activeFor = (previous = false) => new Set(Object.entries(countData.value).filter(([date]) => inRange(date, previous)).flatMap(([, day]) => Object.entries(day.agent || {}).filter(([name, n]) => n > 0 && !/^未指定/.test(name)).map(([name]) => name))).size
const formatNumber = (value: number) => new Intl.NumberFormat('en-US').format(value)
const compare = (value: number, prior: number, absolute = false) => {
  if (!prior) return value ? '新增使用' : '暂无变化'
  const difference = absolute ? value - prior : Math.round((value - prior) / prior * 100)
  return (difference > 0 ? '+' : '') + difference + (absolute ? '' : '%')
}
const comparisonLabel = computed(() => days.value === 1 ? '较昨日' : '较前' + days.value + '天')
const metrics = computed(() => [
  { label: '模型调用', value: countsLoaded.value ? formatNumber(callsFor()) : '—', icon: 'i-chat-fill', theme: 'blue', change: countsLoaded.value ? compare(callsFor(), callsFor(true)) : '暂无数据', direction: Math.sign(callsFor() - callsFor(true)), hint: '统计所选时间内会话产生的模型调用次数' },
  { label: '活跃智能体', value: countsLoaded.value ? formatNumber(activeFor()) : '—', icon: 'i-bot-fill', theme: 'blue', change: countsLoaded.value ? compare(activeFor(), activeFor(true), true) : '暂无数据', direction: Math.sign(activeFor() - activeFor(true)), hint: '所选时间内实际产生调用的智能体数量' },
  { label: '工具调用', value: '—', icon: 'i-link', theme: 'blue', change: '暂无统计', direction: 0, hint: '当前服务尚未提供工具调用统计' },
  { label: 'Token用量', value: tokensLoaded.value ? formatNumber(tokensFor()) : '—', icon: 'i-layers', theme: 'blue', change: tokensLoaded.value ? compare(tokensFor(), tokensFor(true)) : '暂无数据', direction: Math.sign(tokensFor() - tokensFor(true)), hint: '输入与输出 Token 的总和' }
])
const visibleActivities = computed(() => activities.value.filter(row => inRange(row.time)).slice(0, showAllActivities.value ? undefined : 5))
const distribution = computed(() => {
  const values = new Map<string, number>()
  if (distributionMetric.value === 'tokens') for (const [, day] of currentTokens.value) for (const [name, v] of Object.entries(day.model || {})) values.set(name, (values.get(name) || 0) + Number(v.total_tokens ?? ((v.input_tokens || 0) + (v.output_tokens || 0))))
  else for (const [, day] of currentCounts.value) for (const [name, v] of Object.entries(day.model || {})) values.set(name, (values.get(name) || 0) + Number(v || 0))
  return [...values.entries()].sort((a, b) => b[1] - a[1])
})
const hasTrend = computed(() => currentCounts.value.some(([, day]) => Object.values(day.model || {}).some(n => n > 0)))
const hasDistribution = computed(() => distribution.value.some(([, value]) => value > 0))
const chartFont = 'AgentChat Inter, AgentChat Sans SC, sans-serif'
function renderCharts() {
  if (!trendChart || !distributionChart) return
  const dateKeys = Array.from({ length: days.value }, (_, i) => shiftDay(today(), i + 1 - days.value))
  const countMap = new Map(currentCounts.value.map(([date, day]) => [date, Object.values(day.model || {}).reduce((a, b) => a + Number(b || 0), 0)]))
  const axisLabel = { color: '#7e8dae', fontSize: 12, fontFamily: chartFont }
  const splitLine = { lineStyle: { color: '#e8eef9', type: 'dashed' as const } }
  const tooltip = { trigger: 'axis' as const, backgroundColor: '#fff', borderColor: '#edf1f8', padding: [10, 12], textStyle: { color: '#425780', fontSize: 13, fontFamily: chartFont }, extraCssText: 'border-radius:10px;box-shadow:0 5px 22px #1d3f7614;' }
  trendChart.setOption({ animation: false, textStyle: { fontFamily: chartFont }, tooltip, grid: { left: 43, right: 12, top: 16, bottom: 29 }, xAxis: { type: 'category', boundaryGap: false, data: dateKeys.map(date => date.slice(5).replace('-', '/')), axisTick: { show: false }, axisLine: { lineStyle: { color: '#dce5f5' } }, axisLabel, splitLine: { show: true, ...splitLine } }, yAxis: { type: 'value', minInterval: 1, axisLabel, splitLine }, series: [{ name: '模型调用', type: 'line', smooth: true, symbol: 'circle', symbolSize: 6, data: dateKeys.map(date => countMap.get(date) || 0), itemStyle: { color: '#fff', borderColor: '#1768ff', borderWidth: 2 }, lineStyle: { color: '#1768ff', width: 2.2 }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#256cff32' }, { offset: 1, color: '#256cff06' }]) } }] }, true)
  distributionChart.setOption({ animation: false, textStyle: { fontFamily: chartFont }, tooltip: { ...tooltip, axisPointer: { type: 'shadow' } }, grid: { left: 44, right: 4, top: 16, bottom: 29 }, xAxis: { type: 'category', data: distribution.value.map(([name]) => name), axisTick: { show: false }, axisLine: { lineStyle: { color: '#dce5f5' } }, axisLabel: { ...axisLabel, interval: 0, width: 83, overflow: 'truncate' } }, yAxis: { type: 'value', axisLabel: { ...axisLabel, formatter: (n: number) => n >= 1000 ? n / 1000 + 'K' : n }, splitLine }, series: [{ name: distributionMetric.value === 'tokens' ? 'Token用量' : '调用次数', type: 'bar', data: distribution.value.map(([, value]) => value), barMaxWidth: 40, itemStyle: { borderRadius: [5, 5, 0, 0], color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#4e86ff' }, { offset: 1, color: '#c0dcff' }]) }, label: { show: true, position: 'top', color: '#28477a', fontSize: 12, formatter: (p: any) => formatNumber(Number(p.value)) } }] }, true)
}
async function fetchUsage() {
  const id = ++requestId
  loading.value = true
  const params = { delta_days: days.value * 2, model: filters.value.model || undefined, agent: filters.value.agent || undefined }
  const results = await Promise.allSettled([getUsageCountAPI(params), getUsageStatsAPI(params)])
  if (id !== requestId) return
  let failed = false
  const [counts, tokens] = results
  if (counts.status === 'fulfilled' && counts.value.data.status_code === 200) { countData.value = counts.value.data.data || {}; countsLoaded.value = true } else { countsLoaded.value = false; countData.value = {}; failed = true }
  if (tokens.status === 'fulfilled' && tokens.value.data.status_code === 200) { tokenData.value = tokens.value.data.data || {}; tokensLoaded.value = true } else { tokensLoaded.value = false; tokenData.value = {}; failed = true }
  renderCharts()
  loading.value = false
  usageError.value = failed
  if (failed) ElMessage.error('部分统计数据暂时无法读取')
}
async function fetchActivities() {
  const id = ++activityRequestId
  const results = await Promise.allSettled([getConversationListAPI(), getWorkspaceSessionsAPI()])
  if (disposed || id !== activityRequestId) return
  const rows: Activity[] = []
  const [conversations, sessions] = results
  if (conversations.status === 'fulfilled' && conversations.value.data.status_code === 200 && Array.isArray(conversations.value.data.data)) for (const row of conversations.value.data.data) rows.push({ id: row.conversation_id, time: row.update_time || row.create_time || '', kind: '会话', title: row.name || '未命名会话', source: row.agent_name || '—', status: '已创建', route: '/conversation/chatPage?conversation_id=' + encodeURIComponent(row.conversation_id), tokenUsage: row.usage_available ? { input_tokens: Number(row.input_tokens || 0), output_tokens: Number(row.output_tokens || 0), total_tokens: Number(row.total_tokens || 0) } : undefined })
  if (sessions.status === 'fulfilled' && sessions.value.data.status_code === 200 && Array.isArray(sessions.value.data.data)) for (const row of sessions.value.data.data) rows.push({ id: row.session_id, time: row.update_time || row.create_time || '', kind: '智能体', title: row.title || '工作台任务', source: row.agent === 'simple' ? '日常对话' : '灵寻 LingSeek', status: Array.isArray(row.contexts) && row.contexts.some((c: any) => c.answer) ? '已有结果' : '已创建', route: (row.agent === 'simple' ? '/workspace?session_id=' : '/workspace/taskGraph?session_id=') + encodeURIComponent(row.session_id) })
  activities.value = rows.sort((a, b) => b.time.localeCompare(a.time))
  activityError.value = results.some(result => result.status === 'rejected' || result.value.data.status_code !== 200)
}
function setPeriod(value: number) { days.value = value; showAllActivities.value = false; fetchUsage() }
function exportData() {
  const escape = (v: unknown) => { let text = String(v ?? ''); if (/^[=+@-]/.test(text)) text = "'" + text; return '"' + text.replace(/"/g, '""') + '"' }
  const rows: unknown[][] = [['统计周期', days.value === 1 ? '今天' : '近' + days.value + '天'], ['模型筛选', filters.value.model || '全部'], ['智能体筛选', filters.value.agent || '全部'], ['指标', '数值'], ...metrics.value.map(m => [m.label, m.value]), [], ['模型', distributionMetric.value === 'tokens' ? 'Token用量' : '调用次数'], ...distribution.value, [], ['时间', '类型', '内容', '来源', '状态'], ...activities.value.filter(row => inRange(row.time)).map(row => [row.time, row.kind, row.title, row.source, row.status])]
  const url = URL.createObjectURL(new Blob(['\ufeff' + rows.map(row => row.map(escape).join(',')).join('\r\n')], { type: 'text/csv;charset=utf-8;' }))
  const link = document.createElement('a'); link.href = url; link.download = 'AI使用看板-' + today() + '.csv'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000)
}
onMounted(async () => {
  await nextTick()
  if (disposed) return
  if (trendRef.value && distributionRef.value) {
    trendChart = echarts.init(trendRef.value); distributionChart = echarts.init(distributionRef.value)
    observer = new ResizeObserver(() => { trendChart?.resize(); distributionChart?.resize() })
    observer.observe(trendRef.value); observer.observe(distributionRef.value)
  }
  renderCharts()
  document.fonts.ready.then(() => { if (!disposed) { renderCharts(); trendChart?.resize(); distributionChart?.resize() } })
  await Promise.allSettled([fetchUsage(), fetchActivities(), getUsageModelsAPI().then(r => { if (!disposed && r.data.status_code === 200) models.value = r.data.data || [] }), getUsageAgentsAPI().then(r => { if (!disposed && r.data.status_code === 200) agents.value = r.data.data || [] })])
})
onBeforeUnmount(() => { disposed = true; activityRequestId++; requestId++; observer?.disconnect(); trendChart?.dispose(); distributionChart?.dispose() })
</script>
<template>
  <div class="reference-dashboard catalog-page" v-loading="loading">
    <svg style="position:absolute;width:0;height:0;overflow:hidden" class="defs" xmlns="http://www.w3.org/2000/svg"><defs>
<symbol id="i-home" viewBox="0 0 24 24"><path d="M3 10 12 2l9 8v11h-6v-7H9v7H3z" fill="currentColor" stroke="none"/><path d="m1 11 11-9 11 9"/></symbol>
<symbol id="i-search" viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="7.5"/><path d="m16 16 6 6"/></symbol>
<symbol id="i-chat" viewBox="0 0 24 24"><path d="M21 11.5c0 5-4.1 8.5-9 8.5-1.5 0-3-.3-4.3-.9L3 21l1.5-4.5A8.5 8.5 0 0 1 3 11.5C3 6.8 7 3 12 3s9 3.8 9 8.5Z"/><circle cx="8" cy="11.5" r=".8" fill="currentColor" stroke="none"/><circle cx="12" cy="11.5" r=".8" fill="currentColor" stroke="none"/><circle cx="16" cy="11.5" r=".8" fill="currentColor" stroke="none"/></symbol>
<symbol id="i-chat-fill" viewBox="0 0 32 32"><path d="M30 14.8C30 7.7 24 3 16 3S2 7.7 2 14.8c0 4 1.7 7.1 4.4 9.3L4 29l6.1-2.6c1.8.6 3.8.9 5.9.9s4.1-.3 5.9-.9c4.9-1.7 8.1-5.8 8.1-11.6Z" fill="currentColor" stroke="none"/><g fill="white" stroke="none"><circle cx="9.5" cy="15" r="1.8"/><circle cx="16" cy="15" r="1.8"/><circle cx="22.5" cy="15" r="1.8"/></g></symbol>
<symbol id="i-bot" viewBox="0 0 24 24"><path d="M12 5V2"/><circle cx="12" cy="2" r=".8" fill="currentColor"/><rect x="3" y="6" width="18" height="16" rx="4"/><path d="M1 11v5m22-5v5m-15 1c2 1.5 6 1.5 8 0"/><circle cx="8" cy="12" r="1" fill="currentColor" stroke="none"/><circle cx="16" cy="12" r="1" fill="currentColor" stroke="none"/></symbol>
<symbol id="i-bot-fill" viewBox="0 0 36 36"><path d="M15.3 7V5a3 3 0 0 1 6 0v3" stroke="currentColor" stroke-width="3.5"/><rect x="5" y="10" width="26" height="23" rx="7" fill="currentColor" stroke="none"/><rect x="1" y="17" width="6" height="11" rx="3" fill="currentColor" stroke="none"/><rect x="29" y="17" width="6" height="11" rx="3" fill="currentColor" stroke="none"/><path d="M12 11h12l-1-3H13z" fill="currentColor" stroke="none"/><g fill="white" stroke="none"><circle cx="12.5" cy="20" r="2.3"/><circle cx="23.5" cy="20" r="2.3"/><rect x="14" y="26" width="8" height="2.3" rx="1.1"/></g></symbol>
<symbol id="i-link" viewBox="0 0 24 24"><path d="m10 7 3-3a5 5 0 0 1 7 7l-3 3M14 17l-3 3a5 5 0 0 1-7-7l3-3m1 6 8-8"/></symbol>
<symbol id="i-cube" viewBox="0 0 24 24"><path d="m12 2 9 5v10l-9 5-9-5V7zM3 7l9 5 9-5M12 12v10"/></symbol>
<symbol id="i-book" viewBox="0 0 24 24"><path d="M12 5v17M12 5C9 2 5 2 2 4v16c3-2 7-2 10 2 3-4 7-4 10-2V4c-3-2-7-2-10 1Z"/></symbol>
<symbol id="i-chart" viewBox="0 0 24 24"><rect x="3" y="11" width="3" height="11" rx="1" fill="currentColor" stroke="none"/><rect x="10.5" y="3" width="3" height="19" rx="1" fill="currentColor" stroke="none"/><rect x="18" y="7" width="3" height="15" rx="1" fill="currentColor" stroke="none"/></symbol>
<symbol id="i-apps" viewBox="0 0 24 24"><rect x="2" y="2" width="8" height="8" rx="3"/><rect x="14" y="2" width="8" height="8" rx="3"/><rect x="2" y="14" width="8" height="8" rx="3"/><rect x="14" y="14" width="8" height="8" rx="3"/></symbol>
<symbol id="i-layers" viewBox="0 0 24 24"><path d="m12 2 10 5-10 5L2 7zM2 12l10 5 10-5M2 17l10 5 10-5"/></symbol>
<symbol id="i-layers-fill" viewBox="0 0 24 24"><path d="m12 1 11 6-11 6L1 7zM1 10l11 6 11-6v3l-11 6L1 13zM1 16l11 6 11-6v3l-11 6L1 19z" fill="currentColor" stroke="none"/></symbol>
<symbol id="i-down" viewBox="0 0 24 24"><path d="m5 9 7 7 7-7"/></symbol>
<symbol id="i-up" viewBox="0 0 24 24"><path d="M12 20V4m-6 6 6-6 6 6"/></symbol>
<symbol id="i-right" viewBox="0 0 24 24"><path d="M4 12h16m-6-6 6 6-6 6"/></symbol>
<symbol id="i-collapse" viewBox="0 0 24 24"><path d="m13 4-8 8 8 8m7-16-8 8 8 8"/></symbol>
<symbol id="i-download" viewBox="0 0 24 24"><path d="M12 2v13m-5-5 5 5 5-5M3 16v5h18v-5"/></symbol>
<symbol id="i-bell" viewBox="0 0 24 24"><path d="M5 10a7 7 0 0 1 14 0v5l2 4H3l2-4zm5 12h4"/></symbol>
<symbol id="i-close" viewBox="0 0 24 24"><path d="m6 6 12 12M6 18 18 6"/></symbol>
</defs></svg>
    <CatalogHeader title="数据看板" subtitle="了解你的 AI 使用与效率" description="查看调用趋势、模型用量与最近活动，掌握平台使用情况"><template #actions><div class="dashboard-actions"><div class="period-switch" aria-label="统计时间范围"><button v-for="period in [{days:1,label:'今天'},{days:7,label:'近7天'},{days:30,label:'近30天'}]" :key="period.days" :class="{active:days===period.days}" :aria-pressed="days===period.days" @click="setPeriod(period.days)">{{period.label}}</button></div><button class="export-button" @click="exportData"><svg class="icon"><use href="#i-download"/></svg>导出</button></div></template></CatalogHeader>
    <div v-if="usageError" class="dashboard-error" role="alert"><span>部分统计数据未能加载</span><button @click="fetchUsage">重新加载</button></div>
    <section class="metric-grid" aria-label="使用概览">
      <article v-for="metric in metrics" :key="metric.label" class="metric-card" :class="metric.theme" :title="metric.hint"><div class="metric-icon"><SidebarIcon v-if="metric.label === '活跃智能体'" name="bot" class="icon"/><svg v-else class="icon"><use :href="'#'+metric.icon"/></svg></div><div class="metric-copy"><h2>{{metric.label}}</h2><strong>{{metric.value}}</strong><p class="metric-comparison"><span v-if="metric.label!=='工具调用'">{{comparisonLabel}}</span><b :class="{negative:metric.direction<0}">{{metric.change}}</b><svg v-if="metric.direction" class="icon" :class="{down:metric.direction<0}"><use href="#i-up"/></svg></p></div><SidebarIcon v-if="metric.label === '活跃智能体'" name="bot" class="metric-watermark icon"/><svg v-else class="metric-watermark icon" aria-hidden="true"><use :href="'#'+(metric.icon==='i-layers'?'i-layers-fill':metric.icon)"/></svg></article>
    </section>
    <section class="chart-grid" aria-label="使用图表">
      <article class="chart-panel"><header class="panel-heading"><h2>调用活跃趋势 <small>按日统计</small></h2><el-popover placement="bottom-end" :width="285" trigger="click"><template #reference><button class="chart-select" :class="{filtered:filters.agent||filters.model}">模型调用<svg class="icon"><use href="#i-down"/></svg></button></template><div class="chart-filters"><label>智能体<el-select v-model="filters.agent" clearable placeholder="全部智能体" @change="fetchUsage"><el-option v-for="agent in agents" :key="agent" :value="agent" :label="agent"/></el-select></label><label>模型<el-select v-model="filters.model" clearable placeholder="全部模型" @change="fetchUsage"><el-option v-for="model in models" :key="model" :value="model" :label="model"/></el-select></label></div></el-popover></header><div ref="trendRef" class="chart-canvas"/><div v-if="!hasTrend&&!loading" class="chart-empty">{{countsLoaded ? '所选时间暂无调用记录' : '调用数据暂时无法读取'}}</div></article>
      <article class="chart-panel"><header class="panel-heading"><h2>模型使用分布</h2><label class="chart-select"><el-select v-model="distributionMetric" aria-label="模型分布统计指标" @change="renderCharts" class="catalog-select"><el-option value="tokens" label="Token 用量"/><el-option value="calls" label="调用次数"/></el-select><svg class="icon"><use href="#i-down"/></svg></label></header><div ref="distributionRef" class="chart-canvas"/><div v-if="!hasDistribution&&!loading" class="chart-empty">{{(distributionMetric==='tokens' ? tokensLoaded : countsLoaded) ? '所选时间暂无模型使用记录' : '模型数据暂时无法读取'}}</div></article>
    </section>
    <section class="activity-panel"><header class="panel-heading"><h2>最近活动</h2><button class="view-all" @click="showAllActivities=!showAllActivities">{{showAllActivities?'收起':'查看全部'}}<svg class="icon"><use href="#i-right"/></svg></button></header><div v-if="activityError" class="activity-error" role="alert">部分活动记录未能加载<button @click="fetchActivities">重试</button></div><div class="activity-table-scroll"><table><thead><tr><th>时间</th><th>类型</th><th>内容</th><th>活动来源</th><th title="会话累计的供应方用量，包含对话、标题、摘要与子智能体调用">Token 用量</th><th>状态</th><th>操作</th></tr></thead><tbody><tr v-for="row in visibleActivities" :key="row.kind+row.id"><td>{{formatDataDate(row.time)}}</td><td><span class="activity-kind" :class="{purple:row.kind==='智能体'}"><svg class="icon"><use :href="row.kind==='会话'?'#i-chat':'#i-bot-fill'"/></svg>{{row.kind}}</span></td><td><span class="activity-title" :title="row.title">{{row.title}}</span></td><td>{{row.source}}</td><td :class="{unavailable:!row.tokenUsage}" :title="row.tokenUsage ? `会话累计：输入 ${formatNumber(row.tokenUsage.input_tokens)}，输出 ${formatNumber(row.tokenUsage.output_tokens)}` : row.kind==='会话'?'尚未记录供应方返回的用量':'该活动尚无会话用量统计'">{{row.tokenUsage?formatNumber(row.tokenUsage.total_tokens):'—'}}</td><td><span class="status-pill" :class="{created:row.status==='已创建'}">{{row.status}}</span></td><td><button class="detail-button" @click="router.push(row.route)">查看详情<svg class="icon"><use href="#i-right"/></svg></button></td></tr><tr v-if="!visibleActivities.length"><td colspan="7" class="activity-empty">{{activityError?'暂时无法读取活动记录':'所选时间暂无活动记录'}}</td></tr></tbody></table></div></section>
  </div>
</template>
<style scoped src="./dashboard.css"></style>
