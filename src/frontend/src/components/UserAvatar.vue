<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { userAvatarUrl, userInitial } from '../utils/user-avatar';
const props = defineProps<{ username?: string; src?: string }>();
const failed = ref(false);
const url = computed(() => userAvatarUrl(props.src));
watch(url, () => { failed.value = false; });
</script>
<template><span class="user-initial-avatar" role="img" :aria-label="`${username || '用户'}的头像`"><img v-if="url && !failed" :src="url" alt="" @error="failed = true"><span v-else>{{ userInitial(username) }}</span></span></template>
<style scoped>
.user-initial-avatar{display:grid;place-items:center;width:100%;height:100%;border-radius:50%;overflow:hidden;background:linear-gradient(145deg,#edf5ff,#dfebff);color:#246bff;box-shadow:inset 0 0 0 1px #d8e6fc;font-family:var(--ac-font);font-weight:650;line-height:1;container-type:inline-size;flex:none}
.user-initial-avatar>span{font-size:18px;font-size:48cqw;line-height:1;user-select:none}
.user-initial-avatar img{display:block;width:100%;height:100%;object-fit:cover}
</style>
