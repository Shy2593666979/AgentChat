<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
const route = useRoute()
const labels: Record<string, string> = {
  homepage: 'Mars Agent', conversation: '智能会话', chatPage: '智能会话', defaultPage: '智能会话',
  construct: '我的助手', configuration: '系统配置', agent: '智能体', 'agent-editor': '智能体画布',
  'mcp-server': 'MCP 服务', 'mcp-chat': 'MCP 对话', knowledge: '知识库', 'knowledge-file': '文件管理',
  tool: '工具', 'agent-skill': 'Agent Skill', model: '模型', 'model-editor': '模型配置',
  profile: '个人资料', mars: 'Mars 任务', dashboard: '数据看板', workspaceDefaultPage: '工作台', workspacePage: '任务记录'
}
const label = computed(() => labels[String(route.name)] || '工作空间')
</script>

<template>
  <div class="ac-shell-context"><span>个人空间</span><i>/</i><strong>{{ label }}</strong></div>
</template>
