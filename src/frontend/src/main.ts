import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router';
import { createPinia } from 'pinia'
import persistState from 'pinia-plugin-persistedstate';


const app = createApp(App)
const pinia = createPinia();
pinia.use(persistState);

app.use(router);
app.use(pinia);
app.mount('#app')
