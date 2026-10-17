<script setup lang="ts">
// Outline geometry adapted from Lucide; attribution: icons/LICENSE-Lucide.txt.
defineProps<{ name: string }>()
</script>
<template>
  <svg class="p-icon s-sidebar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <template v-if="name === 'connect'">
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </template>
    <template v-else-if="name === 'chat'">
      <path d="M3.1 16.4a9.5 9.5 0 1 1 4.7 4.1L2.5 22l1.3-4.3a2 2 0 0 0-.7-1.3Z" />
      <circle cx="8" cy="12" r=".7" fill="currentColor" stroke="none" />
      <circle cx="12" cy="12" r=".7" fill="currentColor" stroke="none" />
      <circle cx="16" cy="12" r=".7" fill="currentColor" stroke="none" />
    </template>
    <template v-else-if="name === 'grid'">
      <rect x="2" y="2" width="8" height="8" rx="2.7" />
      <rect x="14" y="2" width="8" height="8" rx="2.7" />
      <rect x="2" y="14" width="8" height="8" rx="2.7" />
      <rect x="14" y="14" width="8" height="8" rx="2.7" />
    </template>
    <template v-else-if="name === 'bot'">
      <rect x="3.5" y="7" width="17" height="14" rx="4" />
      <path d="M12 7V4" />
      <circle cx="12" cy="2.5" r="1.2" fill="currentColor" stroke="none" />
      <circle cx="8.5" cy="12.5" r=".85" fill="currentColor" stroke="none" />
      <circle cx="15.5" cy="12.5" r=".85" fill="currentColor" stroke="none" />
      <path d="M9 17h6" />
    </template>
    <template v-else-if="name === 'search'">
      <circle cx="10.8" cy="10.8" r="7.8" /><path d="m16.4 16.4 4.6 4.6" />
    </template>
    <template v-else-if="name === 'cube'">
      <path d="m12 2.5 8.8 5v9L12 21.5l-8.8-5v-9Z" /><path d="m3.5 7.5 8.5 5 8.5-5M12 12.5v9" />
    </template>
    <template v-else-if="name === 'book'">
      <path d="M12 5C9 2 5 2 2 3v17c4-1 7-1 10 2 3-3 6-3 10-2V3c-3-1-7-1-10 2Zm0 0v13" />
    </template>
    <template v-else-if="name === 'chart'">
      <path d="M4.5 20v-7M11.8 20V8M19.1 20V3" stroke-width="2.6" />
    </template>
    <template v-else-if="name === 'layers'">
      <path d="m12 2.8 10 5.1L12 13 2 7.9Zm-10 10L12 18l10-5.2M2 17.6l10 5.1 10-5.1" />
    </template>
    <template v-else-if="name === 'home'">
      <path d="m2 10 10-8 10 8" /><path d="M5 9v12h5v-7h4v7h5V9" />
    </template>
  </svg>
</template>
