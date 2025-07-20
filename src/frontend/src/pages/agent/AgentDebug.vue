<template>
  <div class="debug-page">
    <h2>智能体API调试页面</h2>
    
    <div class="debug-section">
      <h3>基本信息</h3>
      <p>当前URL: {{ currentUrl }}</p>
      <p>Token: {{ token ? '已设置' : '未设置' }}</p>
      <p>后端地址: {{ backendUrl }}</p>
    </div>
    
    <div class="debug-section">
      <h3>API测试</h3>
      <el-button @click="testAPI" :loading="testing">测试智能体API</el-button>
      <el-button @click="testNetwork">测试网络连接</el-button>
    </div>
    
    <div class="debug-section">
      <h3>调试输出</h3>
      <el-scrollbar height="400px">
        <pre class="debug-log">{{ debugLog }}</pre>
      </el-scrollbar>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { getAgentsAPI } from '../../apis/agent'

const testing = ref(false)
const debugLog = ref('准备开始调试...\n')
const token = ref(localStorage.getItem('token'))
const backendUrl = ref('通过代理: /api -> http://localhost:7860/')
const currentUrl = ref(window.location.href)

const addLog = (message: string) => {
  const timestamp = new Date().toLocaleTimeString()
  debugLog.value += `[${timestamp}] ${message}\n`
}

const testNetwork = async () => {
  addLog('开始测试网络连接...')
  
  try {
    const response = await fetch('/api/v1/agent', {
      method: 'GET',
      headers: {
        'Authorization': token.value ? `Bearer ${token.value}` : '',
        'Content-Type': 'application/json'
      }
    })
    
    addLog(`网络响应状态: ${response.status}`)
    addLog(`网络响应状态文本: ${response.statusText}`)
    
    const text = await response.text()
    addLog(`响应内容: ${text}`)
    
  } catch (error) {
    addLog(`网络测试失败: ${error}`)
  }
}

const testAPI = async () => {
  testing.value = true
  addLog('开始测试智能体API...')
  
  try {
    addLog('调用 getAgentsAPI()...')
    const response = await getAgentsAPI()
    
    addLog(`API调用成功!`)
    addLog(`响应对象: ${JSON.stringify(response, null, 2)}`)
    
    if (response.data) {
      addLog(`响应数据: ${JSON.stringify(response.data, null, 2)}`)
    }
    
  } catch (error: any) {
    addLog(`API调用失败: ${error}`)
    
    if (error.response) {
      addLog(`错误状态码: ${error.response.status}`)
      addLog(`错误响应: ${JSON.stringify(error.response.data, null, 2)}`)
    } else if (error.request) {
      addLog(`请求发送失败: ${error.request}`)
    } else {
      addLog(`其他错误: ${error.message}`)
    }
  } finally {
    testing.value = false
  }
}
</script>

<style lang="scss" scoped>
.debug-page {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
  
  .debug-section {
    margin-bottom: 30px;
    padding: 20px;
    border: 1px solid #e1e8ed;
    border-radius: 8px;
    background: white;
    
    h3 {
      margin-top: 0;
      color: #2c3e50;
    }
    
    .debug-log {
      background: #1e1e1e;
      color: #00ff00;
      padding: 15px;
      border-radius: 4px;
      font-family: 'Courier New', monospace;
      font-size: 12px;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
  }
}
</style> 