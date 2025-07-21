import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  server: {
    host: '0.0.0.0',
    port: 8090,
    // 是否开启 https
    https: false,
      // 设置反向代理，跨域
      proxy: {
        '/api': {
          target: 'http://localhost:7860/',
          changeOrigin: true,
      }
    },
  },
  plugins: [vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver()],
    }),
  ],
  
})
