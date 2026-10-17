<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import SidebarAccount from './SidebarAccount.vue'
import BrandLogo from './BrandLogo.vue'
import UiIcon from './SidebarIcon.vue'
const route = useRoute()
const collapsed = ref(localStorage.getItem('agentchat.sidebarCollapsed') === 'true')
watch(collapsed, value => { document.body.dataset.sidebarCollapsed = String(value); localStorage.setItem('agentchat.sidebarCollapsed', String(value)) }, { immediate: true })
const groups = [
  { title: 'AI 能力', items: [
    { path: '/homepage', label: '探索', icon: 'search' },
    { path: '/conversation', label: '会话', icon: 'chat' },
    { path: '/agent', label: '智能体', icon: 'bot' },
    { path: '/mcp-server', label: 'MCP', icon: 'connect' },
    { path: '/model', label: '模型', icon: 'cube' }
  ] },
  { title: '知识与数据', items: [
    { path: '/knowledge', label: '知识库', icon: 'book' },
    { path: '/dashboard', label: '数据看板', icon: 'chart' }
  ] },
  { title: '效率工具', items: [
    { path: '/tool', label: '工具', icon: 'grid' },
    { path: '/agent-skill', label: 'Skill', icon: 'layers' }
  ] }
]
const active = (path: string) => route.path === path || route.path.startsWith(path + '/')
</script>
<template>
  <aside class="p-sidebar" :class="{ 's-sidebar-collapsed': collapsed }">
    <router-link class="p-sidebar-brand" to="/workspace"><BrandLogo sidebar /></router-link>
    <router-link class="p-nav-item s-workspace-nav" :class="{ active: active('/workspace') }" to="/workspace" title="工作台"><UiIcon name="home" /><span>工作台</span></router-link>
    <nav class="p-navigation" aria-label="主导航">
      <div v-for="group in groups" :key="group.title">
        <div class="p-nav-section">{{ group.title }}</div>
        <div v-for="item in group.items" :key="item.path" class="s-nav-row">
          <router-link :to="item.path" class="p-nav-item" :class="{ active: active(item.path) }" :title="item.label"><UiIcon :name="item.icon" /><span>{{ item.label }}</span></router-link>
        </div>
      </div>
    </nav>
    <div class="p-sidebar-footer">
      <SidebarAccount :collapsed="collapsed" @toggle="collapsed=!collapsed"/>
    </div>
  </aside>
</template>
