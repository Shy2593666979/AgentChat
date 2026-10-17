<script setup lang="ts">
import { useRoute } from 'vue-router'
import WorkspaceHome from './WorkspaceHome.vue'
import WorkspaceChat from './defaultPage/defaultPage.vue'
const route = useRoute()
</script>
<template><WorkspaceChat v-if="route.query.session_id || route.query.chat" /><WorkspaceHome v-else /></template>
