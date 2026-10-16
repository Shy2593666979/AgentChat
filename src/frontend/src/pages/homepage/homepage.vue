<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import UiIcon from '../../components/UiIcon.vue'

const router = useRouter()
const message = ref(''), navigating = ref(false)
const isMac = computed(() => /Mac|iPhone|iPad/.test(navigator.platform))
const examples = [
  { id: 1, kind: 'build', title: '自动构建智能体', category: '自动模式', description: '使用多个工具相互配合完成自动构建智能体的任务。', action: '开始构建', icon: 'bot', art: '295 751 328 171' },
  { id: 2, kind: 'search', title: '深度搜索', category: '搜索模式', description: '连接外部互联网资源，扩展系统能力和数据源。', action: '开始搜索', icon: 'search', art: '641 751 315 171' },
  { id: 3, kind: 'news', title: 'AI 日报', category: '生成模式', description: '对最近的 AI 新闻进行整理总结，可生成下载链接。', action: '生成日报', icon: 'file', art: '975 751 323 171' },
  { id: 4, kind: 'knowledge', title: '知识库问答', category: '知识库模式', description: '基于已有知识库进行精准问答和信息检索。', action: '查询知识', icon: 'book', art: '1316 751 324 171' }
]
async function openMars(query: Record<string, string>) {
  if (navigating.value) return
  navigating.value = true
  try { await router.push({ path: '/mars', query }) }
  finally { navigating.value = false }
}
function sendMessage() { if (message.value.trim()) return openMars({ message: message.value.trim() }) }
function handleKeydown(event: KeyboardEvent) {
  if (!event.isComposing && (event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault()
    sendMessage()
  }
}
</script>
<template>
  <div class="mars-explore">
    <header class="explore-hero">
      <svg class="hero-art hero-art-left" viewBox="266 0 390 282" aria-hidden="true"><image href="/ui/explore-reference.png" width="1668" height="943"/></svg>
      <svg class="hero-art hero-art-right" viewBox="1218 0 450 282" aria-hidden="true"><image href="/ui/explore-reference.png" width="1668" height="943"/></svg>
      <div class="hero-copy">
        <h1><svg class="mars-mark" viewBox="0 0 82 82" aria-hidden="true"><defs><linearGradient id="explore-mark" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#00c5ee"/><stop offset="1" stop-color="#1447ff"/></linearGradient></defs><path d="M41 6C35 27 29 33 8 41c21 7 27 13 33 35 7-22 13-28 34-35C54 33 48 27 41 6Z" fill="none" stroke="url(#explore-mark)" stroke-width="7" stroke-linejoin="round"/><path d="m19 65 3-2" stroke="#c9e549" stroke-width="3" stroke-linecap="round"/></svg><span>Mars Agent</span></h1>
        <h2>让 AI 成为你的超级生产力伙伴</h2>
        <p>整合知识、工具与智能体，完成从思考到执行的全流程任务。</p>
      </div>
    </header>
    <main class="explore-content">
      <form class="explore-composer" :aria-busy="navigating" @submit.prevent="sendMessage">
        <textarea v-model="message" placeholder="Mars Agent会完成你的任务并输出结果。" aria-label="描述你的任务" @keydown="handleKeydown"/>
        <div class="composer-footer"><span>{{ isMac ? '⌘' : 'Ctrl' }} + ↵ 发送</span><button type="submit" :disabled="!message.trim() || navigating" :aria-label="navigating ? '正在进入任务会话' : '发送任务'"><UiIcon name="send"/></button></div>
      </form>
      <section class="explore-cases" aria-labelledby="cases-heading">
        <div class="cases-heading"><h2 id="cases-heading">优秀案例</h2><p>从这些示例开始，体验 Mars Agent 的任务能力。</p></div>
        <div class="case-grid">
          <button v-for="example in examples" :key="example.id" type="button" class="case-card" :class="example.kind" :disabled="navigating" :aria-label="`${example.action}：${example.title}`" @click="openMars({ example_id: String(example.id) })">
            <div class="case-heading"><span class="case-icon"><UiIcon :name="example.icon"/></span><div><h3>{{ example.title }}</h3><span class="case-category">{{ example.category }}</span></div></div>
            <p class="case-description">{{ example.description }}</p>
            <span class="case-action">{{ example.action }}<UiIcon name="arrow"/></span>
            <svg class="case-art" :viewBox="example.art" preserveAspectRatio="xMidYMax slice" aria-hidden="true"><image href="/ui/explore-reference.png" width="1668" height="943"/></svg>
          </button>
        </div>
      </section>
    </main>
  </div>
</template>
<style scoped src="./explore.css"></style>
