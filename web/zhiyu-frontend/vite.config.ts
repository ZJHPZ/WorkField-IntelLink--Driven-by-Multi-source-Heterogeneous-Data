import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, 'src'),
    },
  },
  server: {
    port: 3001,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        ws: true,
      },
      // 讯飞虚拟人 vms-web-sdk-2.0.0:服务不支持跨域,必须经代理。
      // SDK 内部以 /vmss 为前缀请求,转发时剥掉前缀直达 vms 服务。
      '/vmss': {
        target: 'http://vms.cn-huadong-1.xf-yun.com',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/vmss/, ''),
      },
    },
  },
})
