<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { MdPreview } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';
import UiIcon from '../../components/UiIcon.vue';
import { postEventStream, copyChatText, downloadMarkdown } from '../../utils/chat-ui';
import { responseError } from '../../utils/resource-visuals';
import { marsPreview } from '../../utils/mars-preview';
import { consumeMarsEvent, createMarsTask, type MarsTask } from '../../utils/mars-task';

const route = useRoute(), router = useRouter();
const task = ref<MarsTask>(), busy = ref(false), processOpen = ref(window.innerWidth > 1000), reasoningOpen = ref(false);
const collapsedTools = ref(new Set<string>());
const output = ref<HTMLElement>(), follow = ref(true);
const report = ref<HTMLElement>();
let reportObserver: MutationObserver | undefined, userScrollUntil = 0;
const previewMode = route.query.preview === '1';
const isDemo = ref(previewMode);
let controller: AbortController | undefined, operation = 0, disposed = false, frame = 0, timer: ReturnType<typeof setInterval> | undefined;
const exampleNames: Record<number, string> = { 1: '自动构建智能体', 2: '深度搜索', 3: 'AI 日报', 4: '知识库问答' };
const stateLabel = computed(() => !task.value ? '准备就绪' : ({ working: '执行中', done: '已完成', stopped: '已停止', error: '执行异常' })[task.value.state]);
const stage = computed(() => task.value?.answer ? 2 : task.value?.tools.length ? 1 : 0);
const taskDate = computed(() => task.value ? new Date(task.value.time).toLocaleString('zh-CN', {year:'numeric',month:'long',day:'numeric',hour:'2-digit',minute:'2-digit'}) : '');
const resultTitle = computed(() => task.value?.answer.match(/^#\s+(.+)$/m)?.[1] || task.value?.query || '任务结果');
const resultContent = computed(() => (task.value?.answer || '').replace(/^#\s+.+\r?\n?/, ''));
const analysisSummary = computed(() => task.value?.reasoning.replace(/[#*`]/g, '').slice(0,160) || (busy.value && stage.value===0?'正在理解需求与选择执行能力…':'根据当前需求组织执行步骤。'));
function toggleTool(id: string) { const next = new Set(collapsedTools.value); if (next.has(id)) next.delete(id); else next.add(id); collapsedTools.value = next; }
function logsFor(id: string) { return task.value?.logs.filter(log => log.toolId === id) || []; }
const latestActivity = computed(() => task.value?.logs[task.value.logs.length-1]?.message || task.value?.tools.find(tool => tool.state === 'working')?.label || (stage.value === 2 ? '正在整理任务结果' : '正在理解需求，请稍候…'));
function completeStage(index: number) { return task.value?.state === 'done' ? index !== 1 || !!task.value.tools.length : index === 0 && stage.value > 0 || index === 1 && !!task.value?.tools.length && task.value.tools.every(tool => tool.state === 'done'); }
function scrollBottom(force = false) {
  if (force) follow.value = true;
  if (!follow.value) return;
  cancelAnimationFrame(frame);
  nextTick(() => { if (!disposed) frame = requestAnimationFrame(() => { if (output.value) output.value.scrollTop = output.value.scrollHeight; }); });
}
// Markdown 异步排版也会触发滚动事件，只在用户主动滚动时改变跟随状态。
function markUserScroll() { userScrollUntil = performance.now() + 1200; }
function onScroll() {
  if (output.value && performance.now() < userScrollUntil) follow.value = output.value.scrollHeight - output.value.scrollTop - output.value.clientHeight < 100;
}
function stop() {
  operation++; controller?.abort(); controller = undefined; clearInterval(timer); busy.value = false;
  if (task.value?.state === 'working') task.value.state = 'stopped';
}
async function run(query: string, example?: number) {
  if (busy.value || !query.trim()) return;
  const token = ++operation, started = performance.now();
  controller = new AbortController(); task.value = createMarsTask(query.trim(), example);
  const record = task.value;
  busy.value = true; isDemo.value = false; processOpen.value = window.innerWidth > 1000; reasoningOpen.value = false; collapsedTools.value = new Set(); scrollBottom(true);
  timer = setInterval(() => { record.elapsed = Math.floor((performance.now() - started) / 1000); }, 1000);
  try {
    await postEventStream(example ? '/api/v1/mars/example' : '/api/v1/mars/chat', example ? { example_id: example } : { user_input: query.trim() }, event => {
      if (disposed || token !== operation) return;
      consumeMarsEvent(record, event); scrollBottom();
    }, controller.signal);
    if (token === operation && !disposed && record.state === 'working') {
      record.state = record.answer.trim() && !record.tools.some(tool => tool.state === 'error') ? 'done' : 'error';
      if (record.state === 'error') record.error = record.answer.trim() ? '部分工具执行失败，已保留收到的结果，请检查执行过程。' : '响应已结束，但未收到结果，请重试';
    }
  } catch (error: any) {
    if (token === operation && !disposed && error.name !== 'AbortError') { record.state = 'error'; record.error = responseError(error, 'Mars 响应失败，请重试'); }
  } finally {
    if (token === operation && !disposed) { record.elapsed = Math.floor((performance.now() - started) / 1000); clearInterval(timer); busy.value = false; controller = undefined; scrollBottom(); }
  }
}
async function copy() { if (!task.value?.answer) return; try { await copyChatText(task.value.answer); ElMessage.success('内容已复制'); } catch { ElMessage.error('复制失败，请选中内容复制'); } }
function download() { if (task.value?.answer) downloadMarkdown(task.value.answer, task.value.query); }
async function leave() {
  if (!busy.value) return true;
  try { await ElMessageBox.confirm('任务仍在执行，离开将停止本次生成。', '离开 Mars', { confirmButtonText: '停止并离开', cancelButtonText: '继续执行', type: 'warning' }); return true; } catch { return false; }
}
onBeforeRouteLeave(leave);
function beforeUnload(event: BeforeUnloadEvent) { if (busy.value) { event.preventDefault(); event.returnValue = ''; } }
// 视觉验收示例不请求模型、不写入用户数据，正式任务继续使用后端流式接口。
function preview(kind = Number(route.query.tool) || 2) { if (busy.value) return; isDemo.value = true; collapsedTools.value = new Set(); task.value = marsPreview(kind); }
onMounted(() => {
  reportObserver = new MutationObserver(() => scrollBottom());
  if (report.value) reportObserver.observe(report.value, { childList: true, subtree: true, characterData: true });
  window.addEventListener('beforeunload', beforeUnload);
  if (previewMode) { preview(); return; }
  const message = typeof route.query.message === 'string' ? route.query.message : '', example = Number(route.query.example_id);
  if (message || exampleNames[example]) router.replace({ path: route.path, query: {} });
  if (exampleNames[example]) run('示例：' + exampleNames[example], example); else if (message.trim()) run(message);
});
onBeforeUnmount(() => { disposed = true; reportObserver?.disconnect(); stop(); cancelAnimationFrame(frame); window.removeEventListener('beforeunload', beforeUnload); });
</script>
<template>
  <div class="b5-page b5-mars mars-b">
    <header class="mars-heading"><div class="mars-brand"><h1>Mars Agent</h1><span>任务执行</span></div><button class="mars-back" @click="router.push('/homepage')"><UiIcon name="arrow-left"/>返回探索</button></header>
    <main class="mars-main" :class="{'has-task':task}">
      <div class="mars-left">
        <div ref="output" class="mars-output" @scroll="onScroll" @wheel.passive="markUserScroll" @pointerdown="markUserScroll" @keydown="markUserScroll"><div ref="report" class="mars-document">
          <section v-if="task" class="mars-report" :class="{'travel-report': /游玩|旅游|行程|泰山/.test(resultTitle)}">
            <header class="mars-result-heading"><UiIcon name="file"/><div class="mars-result-title"><h2>{{resultTitle}}</h2><div class="mars-result-meta"><span :class="['mars-badge',task.state]" role="status"><i v-if="busy" class="mars-spinner"/><UiIcon v-else :name="task.state==='done'?'check':task.state==='error'?'close':'stop'"/>{{task.state==='done'?'任务已完成':stateLabel}}</span><span><UiIcon name="clock"/>{{task.elapsed}} 秒</span><time>{{taskDate}}</time><span v-if="isDemo">视觉示例</span></div></div><div class="mars-report-actions"><button v-if="busy" class="mars-stop" @click="stop"><UiIcon name="stop"/>停止</button><button title="复制内容" aria-label="复制任务结果" :disabled="!task.answer" @click="copy"><UiIcon name="copy"/>复制内容</button><button title="下载 Markdown" aria-label="下载任务结果" :disabled="!task.answer" @click="download"><UiIcon name="download"/>下载 Markdown</button></div></header>
            <MdPreview v-if="task.answer" editorId="mars-result" :modelValue="resultContent"/>
            <div v-else class="mars-awaiting"><span class="mars-awaiting-icon"><UiIcon :name="task.state==='error'?'info':task.state==='stopped'?'stop':'spark'"/></span><h3>{{busy?'任务正在执行':task.state==='stopped'?'本次生成已停止':'暂未生成结果'}}</h3><p>{{busy?latestActivity:'可以重新执行此任务，或在下方输入新的需求。'}}</p><div v-if="busy" class="mars-loading-lines"><i/><i/><i/></div></div>
            <div v-if="task.error" class="mars-error" role="alert"><UiIcon name="info"/><span>{{task.error}}</span><button :disabled="busy" @click="run(task.query,task.example)"><UiIcon name="refresh"/>重试</button></div>
          </section>
          <section v-else class="mars-empty"><span class="mars-empty-mark"><UiIcon name="spark"/></span><small>从需求到结果</small><h2>让 Mars 帮你完成任务</h2><p>搜索资料、整理知识、生成日报，或构建你的专属智能体。</p><div class="mars-start-examples"><button v-for="(label,id) in exampleNames" :key="id" @click="run('示例：'+label,Number(id))"><UiIcon :name="Number(id)===1?'bot':Number(id)===2?'search':Number(id)===3?'file':'book'"/>{{label}}<UiIcon name="arrow"/></button></div></section>
        </div></div>
        <button v-if="!follow" class="mars-scroll-bottom" aria-label="回到最新内容" @click="scrollBottom(true)"><UiIcon name="arrow-down"/></button>
      </div>
      <aside v-if="task" class="mars-process-panel" aria-label="任务执行过程">
        <button class="mars-process-heading" :aria-expanded="processOpen" @click="processOpen=!processOpen"><UiIcon name="clock"/><strong>执行过程</strong><span :class="['mars-badge',task.state]"><UiIcon v-if="task.state==='done'" name="check"/>{{stateLabel}}</span><small class="mars-total-time"><UiIcon name="clock"/>{{task.elapsed}} 秒</small><UiIcon name="chevron-down" :class="{open:processOpen}"/></button>
        <div v-if="processOpen" class="mars-timeline">
          <section class="mars-phase" :class="{complete:completeStage(0),active:busy && stage===0}"><span class="mars-phase-dot"><UiIcon :name="completeStage(0)?'check':'spark'"/></span><button class="mars-phase-title" :aria-expanded="reasoningOpen" @click="reasoningOpen=!reasoningOpen"><strong>需求分析</strong><UiIcon name="chevron-down" :class="{open:reasoningOpen}"/></button><MdPreview v-if="reasoningOpen && task.reasoning" editorId="mars-reasoning" :modelValue="task.reasoning"/><p v-else>{{analysisSummary}}</p></section>
          <section class="mars-phase" :class="{complete:completeStage(1),active:busy && task.tools.some(tool=>tool.state==='working')}"><span class="mars-phase-dot"><UiIcon :name="completeStage(1)?'check':'tool'"/></span><h3>工具执行<small>{{task.tools.length?task.tools.length+' 个工具':''}}</small></h3><p v-if="!task.tools.length">{{busy?'按需求选择工具，无需工具时将直接生成结果。':'本次未调用工具。'}}</p>
            <article v-for="tool in task.tools" :key="tool.id" class="mars-tool-card"><button class="mars-tool-heading" :aria-expanded="!collapsedTools.has(tool.id)" @click="toggleTool(tool.id)"><span class="mars-mini-icon"><UiIcon :name="tool.icon"/></span><strong>{{tool.label}}</strong><span :class="['mars-tool-state',tool.state]"><i v-if="tool.state==='working' && busy" class="mars-spinner"/><UiIcon v-else :name="tool.state==='done'?'check':tool.state==='error'?'close':'stop'"/>{{tool.state==='done'?'已完成':tool.state==='error'?'失败':busy?'执行中':'已中断'}}</span><UiIcon name="chevron-down" :class="{open:!collapsedTools.has(tool.id)}"/></button><div v-if="!collapsedTools.has(tool.id)" class="mars-tool-details"><ul v-if="logsFor(tool.id).length" class="mars-log-list"><li v-for="(log,index) in logsFor(tool.id)" :key="index" :class="{error:log.status==='error'}"><UiIcon :name="log.status==='error'?'close':log.status==='complete'?'check':tool.icon"/><span>{{log.message}}</span></li></ul><p v-else>{{tool.state==='working' && busy?'等待工具返回…':tool.state==='error'?'工具未能完成执行。':'工具执行结束。'}}</p><small v-if="tool.elapsed!==undefined" class="mars-tool-time"><UiIcon name="clock"/>耗时 {{tool.elapsed}} 秒</small></div></article>
            <ul v-if="logsFor('').length" class="mars-log-list"><li v-for="(log,index) in logsFor('')" :key="index" :class="{error:log.status==='error'}"><UiIcon name="info"/><span>{{log.message}}</span></li></ul>
          </section>
          <section class="mars-phase" :class="{complete:task.state==='done',active:busy && !!task.answer}"><span class="mars-phase-dot"><UiIcon :name="task.state==='done'?'check':'file'"/></span><h3>生成结果</h3><p>{{busy?task.answer?'正在生成正文，内容实时显示在左侧。':'执行结果返回后，将在左侧生成内容。':task.state==='done'?'任务结果已生成，可查看、复制或下载。':task.state==='stopped'?'生成已停止，已保留收到的内容。':'执行出现异常，可查看已有结果或重试。'}}</p></section>
        </div>
      </aside>
    </main>
  </div>
</template>
<style scoped src="./mars-chat.css"></style>
