<script setup lang="ts">
defineProps<{ title: string; description: string; section?: string; icon?: string; count?: number }>()
</script>

<template>
  <div class="ac-page-intro">
    <div v-if="icon" class="ac-page-symbol"><img :src="icon" alt="" /></div>
    <div class="ac-page-intro-copy">
      <div class="ac-eyebrow">{{ section || 'YOUR WORK, A LITTLE CLEARER.' }}</div>
      <div class="ac-heading-line">
        <h2>{{ title }}</h2>
        <span v-if="count !== undefined" class="ac-count">{{ count }}</span>
      </div>
      <p>{{ description }}</p>
    </div>
  </div>
</template>
