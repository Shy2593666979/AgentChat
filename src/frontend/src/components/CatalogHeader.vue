<script setup lang="ts">
defineProps<{ title: string; subtitle: string; description: string }>()
</script>
<template>
  <header class="catalog-header">
    <div class="catalog-header-copy">
      <h1 class="catalog-title">{{ title }}</h1>
      <h2 class="catalog-subtitle">{{ subtitle }}</h2>
      <p class="catalog-description">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="catalog-header-actions"><slot name="actions" /></div>
  </header>
</template>
