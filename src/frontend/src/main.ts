import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router';
import { createPinia } from 'pinia'
import persistState from 'pinia-plugin-persistedstate';

// Element Plus CSS
import 'element-plus/dist/index.css'
import './styles/fonts.css'
import './styles/refinement.css'
import './styles/redesign.css'
import './styles/prototype.css'
import './styles/screenshot.css'
import './styles/converted-dialogs.css'
import './styles/data-pages.css'
import './styles/management-pages.css'
import './styles/conversation-pages.css'
import './styles/sidebar.css'
import './styles/continuous-layout.css'
import './styles/catalog-layout.css'
import './styles/dropdowns.css'
import './utils/monaco-workers'

const app = createApp(App)
document.body.dataset.design = 'screenshot'
// 正式页面默认连续分栏；对比页的旧版 iframe 仍可用于查看原有间距。
document.body.dataset.columnLayout = window.name === 'agentchat-original-preview' ? 'original' : 'continuous'
const pinia = createPinia();
pinia.use(persistState);

app.use(router);
app.use(pinia);
app.mount('#app')
