<script setup lang="ts">
import SidebarIcon from './SidebarIcon.vue'
import RefreshIcon from './RefreshIcon.vue'
defineProps<{ name: string }>()
const sharedNames = ['home', 'search', 'chat', 'bot', 'connect', 'cube', 'book', 'chart', 'grid', 'layers']
const paths: Record<string, string> = {
  shield: 'M12 3 4 6v6c0 5 8 9 8 9s8-4 8-9V6Z M8.5 12l2.5 2.5 4.5-5',
  'chevron-down': 'm6 9 6 6 6-6',
  'chevrons-left': 'm11 5-7 7 7 7 M20 5l-7 7 7 7',
  'chevrons-right': 'm4 5 7 7-7 7 M13 5l7 7-7 7',
  download: 'M12 3v12 m-5-5 5 5 5-5 M3 16v5h18v-5',
  stop: 'M6 6h12v12H6Z',
  play: 'm7 3 14 9-14 9Z',
  'thumb-up': 'M14 10V3c-2-1-3 0-3 2l-3 6v10h12l2-11Z M3 11h5v10H3Z',
  'thumb-down': 'M10 14v7c2 1 3 0 3-2l3-6V3H4l-2 11Z M16 3h5v10h-5Z',
  workflow: 'M12 3v6 M5 12v6 M19 12v6 M5 12h14 M12 9v3 M9 1h6v4H9Z M2 18h6v5H2Z M16 18h6v5h-6Z',
  code: 'm8 6-6 6 6 6 M16 6l6 6-6 6 M14 3l-4 18',
  mail: 'M3 5h18v14H3Z M3 6l9 7 9-7',
  image: 'M3 3h18v18H3Z M3 17l6-6 5 5 3-3 4 4 M8 7h.01',
  browser: 'M3 4h18v16H3Z M3 9h18 M6 6h.01 M9 6h.01',
  eye: 'M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z',
  copy: 'M8 8h13v13H8Z M16 8V3H3v13h5',
  save: 'M3 3h15l3 3v15H3Z M7 3v6h10V3 M7 21v-8h10v8',
  gear: 'm9 3 1-1h4l1 1 .5 2 2 1 2-.5 2 3-.5 2-1.5 1v2l1.5 1 .5 2-2 3-2-.5-2 1-.5 2-1 1h-4l-1-1-.5-2-2-1-2 .5-2-3 .5-2 1.5-1v-2L3 10l-.5-2 2-3 2 .5 2-1Z M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z',
  'plus-circle': 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z M12 8v8 M8 12h8',
  external: 'M14 3h7v7 M21 3l-10 10 M10 3H3v18h18v-7',
  edit: 'm15 3 6 6-12 12H3v-6Z M12 6l6 6',
  'square-pen': 'M11 4H5a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h13a2 2 0 0 0 2-2v-6 M17 3l4 4-10 10-5 1 1-5Z M15 5l4 4',
  trash: 'M3 6h18 M9 6V3h6v3 M5 6l1 15h12l1-15 M10 10v7 M14 10v7',
  info: 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z M12 11v6 M12 7h.01',
  list: 'M8 5h13 M8 12h13 M8 19h13 M3 5h.01 M3 12h.01 M3 19h.01',
  'arrow-left': 'M20 12H4 m6-6-6 6 6 6',
  'arrow-right': 'M4 12h16 m-6-6 6 6-6 6',
  upload: 'M12 16V3 m-5 5 5-5 5 5 M3 16v5h18v-5',
  refresh: 'M20 8a9 9 0 0 0-15-3L2 8 M2 3v5h5 M4 16a9 9 0 0 0 15 3l3-3 M22 21v-5h-5',
  'arrow-down': 'M12 3v18 m-6-6 6 6 6-6',
  'arrow-up': 'M12 21V3 m-6 6 6-6 6 6',
  database: 'M20 6c0 2-3.6 4-8 4S4 8 4 6s3.6-4 8-4 8 2 8 4Z M4 6v12c0 2 3.6 4 8 4s8-2 8-4V6 M4 12c0 2 3.6 4 8 4s8-2 8-4',
  paperclip: 'm8 12 6-6a3 3 0 0 1 4 4l-8 8a5 5 0 0 1-7-7l8-8a2 2 0 0 1 3 3l-8 8',
  globe: 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z M3 12h18 M12 3c5 5 5 13 0 18-5-5-5-13 0-18Z',
  send: 'm3 10 18-7-7 18-3-8-8-3Z M11 13l10-10',
  close: 'm6 6 12 12M18 6 6 18',
  check: 'M20 6 9 17l-5-5',
  clock: 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z M12 7v5l3 2',
  more: 'M4 12h.01M12 12h.01M20 12h.01',
  camera: 'M9 4h6l2 3h4v13H3V7h4Z M16 13a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z',
  expand: 'M8 3H3v5M16 3h5v5M21 16v5h-5M8 21H3v-5 M3 3l6 6m12-6-6 6m6 12-6-6M3 21l6-6',
  'chevron-right': 'm9 5 7 7-7 7',
  user: 'M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z M4 21v-2a8 6 0 0 1 16 0v2Z',
  home: 'm3 11 9-8 9 8 M5 10v11h5v-7h4v7h5V10',
  bell: 'M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9 M10 21h4',
  cube: 'm12 2 9 5v10l-9 5-9-5V7Z M3 7l9 5 9-5 M12 12v10',
  crown: 'm3 7 4 4 5-8 5 8 4-4-3 13H6Z M6 16h12',
  settings: 'M4 7h16 M4 17h16 M9 4v6 M15 14v6',
  grid: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
  spark: 'm12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z',
  chat: 'M21 11.5a8.5 8.5 0 0 1-8.5 8.5H5l-3 2V11.5a8.5 8.5 0 1 1 19 0Z M7 10h9 M7 14h5',
  bot: 'M8 7h8a4 4 0 0 1 4 4v5a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4v-5a4 4 0 0 1 4-4Z M12 3v4 M1 12v4 M23 12v4 M9 16h6 M8 12h1 M15 12h1',
  book: 'M12 5C8 2 3 3 3 3v16s5-1 9 2c4-3 9-2 9-2V3s-5-1-9 2Z M12 5v16',
  tool: 'M14 6a5 5 0 0 1 6-3l-3 3 1 3 3-3a5 5 0 0 1-6 6l-9 9-3-3 9-9a5 5 0 0 1 2-3Z',
  connect: 'M8 8 6 6a3 3 0 0 1 4-4l3 3 M16 16l2 2a3 3 0 0 1-4 4l-3-3 M7 17 17 7 M3 13l8 8 M13 3l8 8',
  layers: 'm12 3 10 6-10 6L2 9Z M3 14l9 5 9-5 M3 18l9 5 9-5',
  chart: 'M4 3v18h17 M8 15V9 M13 15V5 M18 15v-4',
  search: 'M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z m-1 6 5 5',
  file: 'M14 2H5v20h14V7Z M14 2v6h5 M8 13h8 M8 17h6',
  arrow: 'M5 12h14 m-5-5 5 5-5 5',
  plus: 'M12 5v14 M5 12h14'
}
</script>
<template>
  <RefreshIcon v-if="['refresh','retry','reload'].includes(name)"/>
  <SidebarIcon v-else-if="sharedNames.includes(name)" :name="name" />
  <svg v-else class="p-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path :d="paths[name] || paths.spark" /></svg>
</template>
