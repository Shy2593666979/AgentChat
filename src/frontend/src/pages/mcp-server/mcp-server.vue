<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Connection, VideoPlay, Edit, Delete, View, Tools } from '@element-plus/icons-vue'
import { 
  createMCPServerAPI, 
  getMCPServersAPI, 
  deleteMCPServerAPI, 
  updateMCPUserConfigAPI,
  type MCPServer, 
  type CreateMCPServerRequest, 
  type MCPServerTool,
  type MCPUserConfigUpdateRequest
} from '../../apis/mcp-server'

const servers = ref<MCPServer[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const toolsDialogVisible = ref(false)
const configDialogVisible = ref(false)
const formLoading = ref(false)
const editingServer = ref<MCPServer | null>(null)
const configuringServer = ref<MCPServer | null>(null)
const selectedServerTools = ref<MCPServerTool[]>([])
const selectedServerName = ref('')

// 表单数据
const formData = ref<CreateMCPServerRequest>({
  server_name: '',
  url: '',
  type: 'sse',
  config: '{}'
})

// 用户配置相关数据
const userConfigData = ref<string>('{}') // 仅保留配置数据，编辑时不预加载

// 表单验证
const formErrors = ref<Record<string, string>>({})

const validateForm = () => {
  formErrors.value = {}
  
  if (!formData.value.server_name) {
    formErrors.value.server_name = '请输入服务器名称'
  } else if (formData.value.server_name.length < 2 || formData.value.server_name.length > 50) {
    formErrors.value.server_name = '服务器名称长度在 2 到 50 个字符'
  }
  
  if (!formData.value.url) {
    formErrors.value.url = '请输入服务器地址'
  } else {
    const urlPattern = /^https?:\/\/.+/
    if (!urlPattern.test(formData.value.url)) {
      formErrors.value.url = '请输入正确的URL格式'
    }
  }
  
  if (!formData.value.type) {
    formErrors.value.type = '请选择连接类型'
  }
  
  return Object.keys(formErrors.value).length === 0
}

const fetchServers = async () => {
  loading.value = true
  try {
    const response = await getMCPServersAPI()
    
    if (response?.data?.status_code === 200) {
      const serverList = response.data.data || []
      // 排序：官方服务器（user_id = 0）在前，其他服务器在后
      servers.value = serverList.sort((a: MCPServer, b: MCPServer) => {
        const aIsOfficial = String(a.user_id) === '0'
        const bIsOfficial = String(b.user_id) === '0'
        
        // 如果一个是官方，一个不是，官方的排在前面
        if (aIsOfficial && !bIsOfficial) return -1
        if (!aIsOfficial && bIsOfficial) return 1
        
        // 如果都是官方或都不是官方，按创建时间排序（新的在前）
        return new Date(b.create_time).getTime() - new Date(a.create_time).getTime()
      })
    } else {
      ElMessage.error(response?.data?.status_message || '获取MCP服务器列表失败')
      servers.value = []
    }
  } catch (error) {
    console.error('获取MCP服务器列表失败:', error)
    ElMessage.error('网络错误：无法获取MCP服务器列表')
    servers.value = []
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  editingServer.value = null
  dialogVisible.value = true
  formErrors.value = {}
  // 阻止背景滚动
  document.body.style.overflow = 'hidden'
  // 重置表单
  formData.value = {
    server_name: '',
    url: '',
    type: 'sse',
    config: '{}'
  }
}

const handleEdit = (server: MCPServer) => {
  // 检查是否为官方服务器
  if (String(server.user_id) === '0') {
    ElMessage.warning(`${server.server_name} MCP Server 为官方所有，不能编辑`)
    return
  }
  
  editingServer.value = server
  dialogVisible.value = true
  formErrors.value = {}
  // 阻止背景滚动
  document.body.style.overflow = 'hidden'
  
  // 填充服务器基本信息到表单（编辑时只编辑基本信息，不包含配置）
  formData.value = {
    server_name: server.server_name,
    url: server.url,
    type: server.type,
    config: '{}' // 编辑时不涉及配置
  }
}

const closeDialog = () => {
  dialogVisible.value = false
  editingServer.value = null
  formErrors.value = {}
  userConfigData.value = '[]'
  // 恢复背景滚动
  document.body.style.overflow = 'auto'
}

// 移除加载用户配置的函数，编辑时直接使用服务器信息

const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }
  
  formLoading.value = true
  try {
    if (editingServer.value) {
      // 编辑模式：更新服务器基本信息（不包含配置）
      ElMessage.info('编辑功能暂未实现，请联系管理员')
      closeDialog()
      return
    } else {
      // 创建模式：创建服务器
      // 处理配置字段
      let configData = {}
      if (formData.value.config && typeof formData.value.config === 'string') {
        try {
          configData = JSON.parse(formData.value.config)
        } catch (error) {
          formErrors.value.config = '配置信息格式不正确，请输入有效的JSON格式'
          return
        }
      } else {
        configData = formData.value.config || {}
      }
      
      const submitData = {
        ...formData.value,
        config: configData
      }
      
      const response = await createMCPServerAPI(submitData)
      if (response.data.status_code === 200) {
        ElMessage.success('创建MCP服务器成功')
        closeDialog()
        await fetchServers()
      } else {
        ElMessage.error(response.data.status_message || '创建失败')
      }
    }
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  } finally {
    formLoading.value = false
  }
}

// 更新用户配置
const updateUserConfig = async () => {
  if (!editingServer.value) return
  
  try {
    // 解析用户配置JSON
    let parsedUserConfig = {}
    try {
      parsedUserConfig = JSON.parse(userConfigData.value.trim() || '[]')
    } catch (error) {
      ElMessage.error('用户配置JSON格式错误')
      return
    }

    // 直接调用更新接口（后端会自动判断是创建还是更新）
    const serverId = editingServer.value?.mcp_server_id || configuringServer.value?.mcp_server_id
    if (!serverId) {
      ElMessage.error('服务器ID不存在')
      return
    }
    
    const response = await updateMCPUserConfigAPI({
      server_id: serverId,
      config: parsedUserConfig
    })
    
    if (response.data.status_code === 200) {
      ElMessage.success('用户配置保存成功')
    } else {
      ElMessage.error(response.data.status_message || '保存失败')
      return
    }
    
    closeDialog()
    await fetchServers()
  } catch (error: any) {
    console.error('保存用户配置失败:', error)
    throw error
  }
}

const handleDelete = async (server: MCPServer) => {
  // 检查是否为官方服务器
  if (String(server.user_id) === '0') {
    ElMessage.warning(`${server.server_name} MCP Server 为官方所有，不能删除`)
    return
  }
  
  if (!confirm(`确定要删除MCP服务器 "${server.server_name}" 吗？`)) {
    return
  }
  
  try {
    const response = await deleteMCPServerAPI(server.mcp_server_id)
    if (response.data.status_code === 200) {
      ElMessage.success('删除成功')
      await fetchServers() // 刷新列表
    } else {
      ElMessage.error(response.data.status_message || '删除失败')
    }
  } catch (error) {
    console.error('删除MCP服务器失败:', error)
    ElMessage.error('删除失败')
  }
}

// 查看工具详情
const viewTools = (server: MCPServer) => {
  selectedServerTools.value = server.params || []
  selectedServerName.value = server.server_name
  toolsDialogVisible.value = true
  // 阻止背景滚动
  document.body.style.overflow = 'hidden'
}

const closeToolsDialog = () => {
  toolsDialogVisible.value = false
  // 恢复背景滚动
  document.body.style.overflow = 'auto'
}

// 处理个人配置
const handleConfig = (server: MCPServer) => {
  configuringServer.value = server
  configDialogVisible.value = true
  // 阻止背景滚动
  document.body.style.overflow = 'hidden'
  
  // 初始化用户配置数据，使用服务器的config字段作为基础
  userConfigData.value = typeof server.config === 'object' 
    ? JSON.stringify(server.config, null, 2) 
    : server.config || '[]'
}

const closeConfigDialog = () => {
  configDialogVisible.value = false
  configuringServer.value = null
  // 恢复背景滚动
  document.body.style.overflow = 'auto'
}

// 更新个人配置
const handleConfigSubmit = async () => {
  if (!configuringServer.value) return
  
  formLoading.value = true
  try {
    await updateUserConfig()
    ElMessage.success('个人配置更新成功')
    closeConfigDialog()
    await fetchServers()
  } catch (error) {
    console.error('配置更新失败:', error)
    ElMessage.error('配置更新失败')
  } finally {
    formLoading.value = false
  }
}

// 处理图片加载错误
const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement
  if (target) {
    target.src = '/src/assets/robot.svg'
  }
}

onMounted(async () => {
  try {
    await fetchServers()
  } catch (error) {
    console.error('MCP Server 页面初始化失败:', error)
    ElMessage.error('页面初始化失败，请刷新重试')
  }
})

onUnmounted(() => {
  // 页面卸载时恢复背景滚动，防止影响其他页面
  document.body.style.overflow = 'auto'
})
</script>

<template>
  <div class="mcp-server-page">
    <div class="page-header">
      <h2>MCP Server管理</h2>
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        添加服务器
      </el-button>
    </div>

    <div class="server-list">
      <el-table :data="servers || []" style="width: 100%" :table-layout="'fixed'">
        <!-- 头像列 -->
        <el-table-column label="头像" width="80" align="center">
          <template #default="{ row }">
            <div class="server-avatar">
              <img 
                :src="row.logo_url || '/src/assets/robot.svg'" 
                :alt="row.server_name"
                @error="handleImageError"
              />
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="server_name" label="服务器名称" width="150" align="center">
          <template #default="{ row }">
            <div class="server-name" :class="{ 'official-server': String(row.user_id) === '0' }">
              <span class="name">{{ row.server_name }}</span>
              <el-tag v-if="String(row.user_id) === '0'" type="warning" size="small" class="official-tag">
                官方
              </el-tag>
            </div>
          </template>
        </el-table-column>
        
        <!-- 创建用户列 -->
        <el-table-column label="创建用户" width="110" align="center">
          <template #default="{ row }">
            <div class="user-info">
              <el-tag size="small" type="info">{{ row.user_name }}</el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="type" label="连接类型" width="130" align="center">
          <template #default="{ row }">
            <el-tag :type="row.type === 'sse' ? 'primary' : 'success'">
              {{ row.type.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        
        <!-- 可用工具数量列 -->
        <el-table-column label="可用工具" width="170" align="center">
          <template #default="{ row }">
            <div class="tools-count">
              <el-button 
                type="primary" 
                :icon="Tools"
                size="small"
                @click="viewTools(row)"
                :disabled="!row.params || row.params.length === 0"
                round
              >
                {{ row.params?.length || 0 }} 个工具
              </el-button>
            </div>
          </template>
        </el-table-column>
        
        <!-- 配置状态列 -->
        <el-table-column label="配置状态" width="130" align="center">
          <template #default="{ row }">
            <div class="config-status">
              <el-tag 
                :type="row.config_enabled ? 'warning' : 'success'" 
                size="small"
                :class="{ 'clickable-tag': row.config_enabled }"
                @click="row.config_enabled ? handleConfig(row) : null"
                :title="row.config_enabled ? '点击配置个人参数' : '配置已完成'"
              >
                {{ row.config_enabled ? '需配置' : '已就绪' }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="创建时间" width="210" align="center" fixed="right">
          <template #default="{ row }">
            <div class="create-time">
              <span>{{ new Date(row.create_time).toLocaleString() }}</span>
            </div>
          </template>
        </el-table-column>
        
        <!-- 编辑列 -->
        <el-table-column label="编辑" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-if="String(row.user_id) !== '0'"
              size="small" 
              type="primary"
              :icon="Edit"
              @click="handleEdit(row)"
              title="编辑"
              round
            >
              编辑
            </el-button>
            <el-button 
              v-else
              size="small" 
              type="info"
              :icon="Edit"
              disabled
              :title="`${row.server_name} MCP Server 为官方所有，不能编辑`"
              round
            >
              编辑
            </el-button>
          </template>
        </el-table-column>
        
        <!-- 删除列 -->
        <el-table-column label="删除" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-if="String(row.user_id) !== '0'"
              size="small" 
              type="danger" 
              :icon="Delete"
              @click="handleDelete(row)"
              title="删除"
              round
            >
              删除
            </el-button>
            <el-button 
              v-else
              size="small" 
              type="info" 
              :icon="Delete"
              disabled
              :title="`${row.server_name} MCP Server 为官方所有，不能删除`"
              round
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="servers.length === 0 && !loading" class="empty-state">
        <img src="/src/assets/404.gif" alt="暂无数据" width="300" />
        <p>暂无MCP服务器，点击上方按钮添加第一个服务器吧！</p>
      </div>
    </div>

    <!-- 纯HTML创建/编辑弹窗 -->
    <Teleport to="body">
      <div v-if="dialogVisible" class="modal-overlay" @click.self="closeDialog">
        <div class="modal-dialog">
          <div class="modal-header">
            <h3>{{ editingServer ? '编辑MCP服务器' : '创建MCP服务器' }}</h3>
            <button class="close-btn" @click="closeDialog">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
          
          <div class="modal-body">
            <!-- 服务器配置向导 -->
            <div class="config-wizard">
              <div class="wizard-header">
                <div class="wizard-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L2 7V17L12 22L22 17V7L12 2Z" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M12 12L2 7L12 2L22 7L12 12Z" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <div class="wizard-text">
                  <h4>{{ editingServer ? '更新服务器配置' : '配置新的MCP服务器' }}</h4>
                  <p>{{ editingServer ? '修改现有服务器的连接参数和配置' : '填写以下信息来添加新的MCP服务器' }}</p>
                </div>
              </div>

              <form @submit.prevent="handleSubmit" class="mcp-form">
                <!-- 服务器信息 -->
                <div class="form-section">
                  <div class="section-title">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 2L2 7V17L12 22L22 17V7L12 2Z" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span v-if="editingServer">服务器信息 (只读)</span>
                    <span v-else>基础信息</span>
                  </div>
                  
                  <div class="form-grid">
                    <div class="form-group">
                      <label for="server_name">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M12 2L2 7V17L12 22L22 17V7L12 2Z" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        服务器名称
                      </label>
                      <input 
                        id="server_name"
                        v-model="formData.server_name" 
                        type="text"
                        placeholder="例如：Weather API Server"
                        :class="{ 'error': formErrors.server_name }"
                        :readonly="!!editingServer"
                        :disabled="!!editingServer"
                      />
                      <span v-if="formErrors.server_name" class="error-text">{{ formErrors.server_name }}</span>
                    </div>
                    
                    <div class="form-group">
                      <label for="type">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M12 20h9l-3-9H8l-3 9h9z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <path d="M12 20v-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        连接类型
                      </label>
                      <select 
                        id="type"
                        v-model="formData.type"
                        :class="{ 'error': formErrors.type }"
                        :disabled="!!editingServer"
                      >
                        <option value="sse">SSE (Server-Sent Events)</option>
                        <option value="websocket">WebSocket</option>
                      </select>
                      <span v-if="formErrors.type" class="error-text">{{ formErrors.type }}</span>
                    </div>
                  </div>
                  
                  <div class="form-group">
                    <label for="url">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M9 19c-5 0-5-5.5-7-5.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M21 9a9 9 0 0 1-9 9c-4.5 0-4.5-4-6-4h-.5a2.5 2.5 0 0 1 0-5H9a9 9 0 0 1 12 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      服务器地址
                    </label>
                    <input 
                      id="url"
                      v-model="formData.url" 
                      type="url"
                      placeholder="http://localhost:3001/sse"
                      :class="{ 'error': formErrors.url }"
                      :readonly="!!editingServer"
                      :disabled="!!editingServer"
                    />
                    <span v-if="formErrors.url" class="error-text">{{ formErrors.url }}</span>
                    <div class="input-help" v-if="!editingServer">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="10" stroke="#909399" stroke-width="2"/>
                        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" stroke="#909399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M12 17h.01" stroke="#909399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      <span>请确保服务器地址可以正常访问，支持HTTP和HTTPS协议</span>
                    </div>
                    <div class="input-help" v-else>
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="10" stroke="#f56c6c" stroke-width="2"/>
                        <path d="M12 8v4" stroke="#f56c6c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M12 16h.01" stroke="#f56c6c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      <span>服务器基础信息不可修改，如需更改请联系管理员</span>
                    </div>
                  </div>
                </div>



                <!-- 基础配置（仅创建时显示） -->
                <div class="form-section" v-if="!editingServer">
                  <div class="section-title">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="3" stroke="#409eff" stroke-width="2"/>
                      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span>服务器配置 (可选)</span>
                  </div>
                  
                  <div class="form-group">
                    <label for="config">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <polyline points="10,9 9,9 8,9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      服务器默认配置
                    </label>
                    <div class="textarea-wrapper">
                      <textarea 
                        id="config"
                        v-model="formData.config" 
                        rows="8"
                        placeholder='请输入JSON格式的配置信息，例如：

{
  "api_key": "default_api_key",
  "timeout": 30000,
  "headers": {
    "User-Agent": "MCP-Client/1.0"
  }
}'
                        :class="{ 'error': formErrors.config }"
                      ></textarea>
                      <div class="json-indicator">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M16 3l4 4-4 4" stroke="#909399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <path d="M8 21l-4-4 4-4" stroke="#909399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <path d="M15 14l-6-6" stroke="#909399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        JSON
                      </div>
                    </div>
                    <span v-if="formErrors.config" class="error-text">{{ formErrors.config }}</span>
                    <div class="input-help">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="10" stroke="#67c23a" stroke-width="2"/>
                        <polyline points="16,12 12,8 8,12" stroke="#67c23a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <line x1="12" y1="16" x2="12" y2="8" stroke="#67c23a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      <span>服务器默认配置，所有用户共享。用户可以通过个人配置进行覆盖</span>
                    </div>
                  </div>
                </div>
              </form>
            </div>
          </div>
          
          <div class="modal-footer">
            <button type="button" @click="closeDialog" class="btn btn-cancel">
              取消
            </button>
            <button 
              type="button" 
              @click="handleSubmit"
              :disabled="formLoading"
              class="btn btn-primary"
            >
              <span v-if="formLoading" class="loading-spinner"></span>
              {{ editingServer ? '保存修改' : '添加服务器' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 纯HTML工具详情弹窗 -->
    <Teleport to="body">
      <div v-if="toolsDialogVisible" class="modal-overlay" @click.self="closeToolsDialog">
        <div class="modal-dialog tools-dialog">
          <div class="modal-header">
            <h3>{{ selectedServerName }} - 可用工具</h3>
            <button class="close-btn" @click="closeToolsDialog">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
          
          <div class="modal-body tools-content">
            <div v-if="selectedServerTools.length === 0" class="no-tools">
              <div class="empty-icon">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.77 3.77z" stroke="#c0c4cc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="empty-text">
                <h3>暂无可用工具</h3>
                <p>该服务器尚未提供任何工具，或者服务器连接异常</p>
              </div>
            </div>
            <div v-else class="tools-overview">
              <!-- 工具统计 -->
              <div class="tools-stats">
                <div class="stat-card">
                  <div class="stat-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.77 3.77z" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <div class="stat-info">
                    <span class="stat-number">{{ selectedServerTools.length }}</span>
                    <span class="stat-label">可用工具</span>
                  </div>
                </div>
              </div>

              <!-- 工具列表 -->
              <div class="tools-list">
                <div 
                  v-for="(tool, index) in selectedServerTools" 
                  :key="index"
                  class="tool-card"
                >
                  <div class="tool-header">
                    <div class="tool-info">
                      <div class="tool-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.77 3.77z" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                      </div>
                      <div class="tool-text">
                        <h4 class="tool-name">{{ tool.name }}</h4>
                        <span class="tool-tag">Function</span>
                      </div>
                    </div>
                  </div>
                  
                  <div class="tool-description">
                    <p>{{ tool.description || '暂无描述' }}</p>
                  </div>
                  
                  <div class="tool-schema" v-if="tool.input_schema">
                    <div class="schema-header">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <polyline points="16 18 22 12 16 6" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <polyline points="8 6 2 12 8 18" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      <span>参数结构</span>
                    </div>
                    
                    <div class="schema-content">
                      <div class="schema-meta">
                        <div class="meta-item" v-if="tool.input_schema.type">
                          <span class="meta-label">类型:</span>
                          <span class="meta-value type">{{ tool.input_schema.type }}</span>
                        </div>
                        <div class="meta-item" v-if="tool.input_schema.title">
                          <span class="meta-label">标题:</span>
                          <span class="meta-value">{{ tool.input_schema.title }}</span>
                        </div>
                      </div>
                      
                      <div v-if="tool.input_schema.required?.length" class="required-section">
                        <div class="section-title">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="#f56c6c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M9 12l2 2 4-4" stroke="#f56c6c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          </svg>
                          <span>必填参数</span>
                        </div>
                        <div class="required-params">
                          <span 
                            v-for="param in tool.input_schema.required" 
                            :key="param"
                            class="required-param"
                          >
                            {{ param }}
                          </span>
                        </div>
                      </div>
                      
                      <div v-if="tool.input_schema.properties" class="properties-section">
                        <div class="section-title">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" stroke="#67c23a" stroke-width="2"/>
                            <circle cx="8.5" cy="8.5" r="1.5" stroke="#67c23a" stroke-width="2"/>
                            <path d="M21 15l-5-5L5 21l5-5z" stroke="#67c23a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          </svg>
                          <span>参数详情</span>
                        </div>
                        <div class="properties-grid">
                          <div 
                            v-for="(prop, propName) in tool.input_schema.properties" 
                            :key="propName"
                            class="property-card"
                          >
                            <div class="property-header">
                              <span class="property-name">{{ propName }}</span>
                              <span class="property-type">{{ prop.type }}</span>
                            </div>
                            <div class="property-body">
                              <p v-if="prop.description" class="property-desc">{{ prop.description }}</p>
                              <div v-if="prop.default !== undefined" class="property-default">
                                <span class="default-label">默认值:</span>
                                <code class="default-value">{{ prop.default }}</code>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="modal-footer">
            <button type="button" @click="closeToolsDialog" class="btn btn-primary">关闭</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 个人配置弹窗 -->
    <Teleport to="body">
      <div v-if="configDialogVisible" class="modal-overlay" @click.self="closeConfigDialog">
        <div class="modal-dialog config-dialog">
          <div class="modal-header">
            <h3>{{ configuringServer?.server_name }} - 个人配置</h3>
            <button class="close-btn" @click="closeConfigDialog">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
          
          <div class="modal-body">
            <div class="config-info">
              <div class="info-card">
                <div class="info-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="#409eff" stroke-width="2"/>
                    <path d="M9 12l2 2 4-4" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <div class="info-text">
                  <h4>个人配置说明</h4>
                  <p>配置您的个人参数，这些设置仅对您的账户有效，不会影响其他用户。</p>
                </div>
              </div>
            </div>
            
            <form @submit.prevent="handleConfigSubmit">
              <div class="form-section">
                <div class="section-title">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="8.5" cy="7" r="4" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M20 8v6M23 11h-6" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  <span>个人配置参数</span>
                </div>
                
                <div class="form-group">
                  <label for="userConfig">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    配置参数 (JSON数组格式)
                  </label>
                  <div class="textarea-wrapper">
                    <textarea 
                      id="userConfig"
                      v-model="userConfigData" 
                      rows="12"
                      placeholder='请输入JSON数组格式的配置信息，例如：

[
  {
    "key": "api_key",
    "label": "API密钥",
    "value": "your_api_key_here"
  },
  {
    "key": "timeout",
    "label": "超时时间(毫秒)",
    "value": "30000"
  }
]'
                    ></textarea>
                    <div class="json-indicator">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M16 3l4 4-4 4" stroke="#e67e22" stroke-width="2"/>
                        <path d="M8 21l-4-4 4-4" stroke="#e67e22" stroke-width="2"/>
                      </svg>
                      <span>JSON Array</span>
                    </div>
                  </div>
                  <div class="input-help">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" stroke="#67c23a" stroke-width="2"/>
                      <path d="M9 12l2 2 4-4" stroke="#67c23a" stroke-width="2"/>
                    </svg>
                    <span>配置仅对您的账户生效，支持覆盖服务器默认配置</span>
                  </div>
                </div>
              </div>
            </form>
          </div>
          
          <div class="modal-footer">
            <button type="button" @click="closeConfigDialog" class="btn btn-cancel">
              取消
            </button>
            <button 
              type="button" 
              @click="handleConfigSubmit"
              :disabled="formLoading"
              class="btn btn-primary"
            >
              <span v-if="formLoading" class="loading-spinner"></span>
              保存配置
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style lang="scss">
// 弹窗样式 - 移除scoped，因为使用了Teleport
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99999 !important;
  backdrop-filter: blur(4px);
  pointer-events: auto;
  overflow: hidden;
}

.modal-dialog {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  
  &.tools-dialog {
    max-width: 800px;
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #ebeef5;
  background: #fff;
  
  h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #303133;
  }
  
  .close-btn {
    width: 28px;
    height: 28px;
    border: none;
    background: none;
    color: #909399;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    transition: all 0.2s ease;
    
    &:hover {
      background: #f5f7fa;
      color: #606266;
    }
  }
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
  background: #fafafa;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  background: #fff;
}

// 表单样式
// 配置向导样式
.config-wizard {
  .wizard-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
    background: linear-gradient(135deg, #f8fbff 0%, #f0f7ff 100%);
    border: 1px solid #e1ecf4;
    border-radius: 12px;
    margin-bottom: 24px;
    
    .wizard-icon {
      flex-shrink: 0;
      width: 48px;
      height: 48px;
      background: white;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
    }
    
    .wizard-text {
      h4 {
        margin: 0 0 6px 0;
        font-size: 18px;
        font-weight: 600;
        color: #303133;
      }
      
      p {
        margin: 0;
        font-size: 14px;
        color: #606266;
        line-height: 1.5;
      }
    }
  }
}

.mcp-form {
  .form-section {
    background: white;
    border: 1px solid #ebeef5;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    
    .section-title {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 20px;
      padding-bottom: 12px;
      border-bottom: 1px solid #f0f2f5;
      font-weight: 600;
      color: #303133;
      font-size: 16px;
      
// 移除不需要的状态样式
    }
  }
  
  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    
    @media (max-width: 768px) {
      grid-template-columns: 1fr;
    }
  }
  
  .form-group {
    margin-bottom: 24px;
    
    label {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 12px;
      font-size: 14px;
      
      &[for$="_name"]::after,
      &[for$="_url"]::after,
      &[for$="_type"]::after {
        content: " *";
        color: #f56c6c;
        margin-left: 4px;
      }
      
      svg {
        opacity: 0.7;
      }
    }
    
    input, select, textarea {
      width: 100%;
      padding: 12px 16px;
      border: 1px solid #dcdfe6;
      border-radius: 6px;
      font-size: 14px;
      transition: all 0.2s ease;
      background: white;
      box-sizing: border-box;
      font-family: inherit;
      
      &:focus {
        outline: none;
        border-color: #409eff;
        box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
      }
      
      &:hover {
        border-color: #c0c4cc;
      }
      
      &.error {
        border-color: #f56c6c;
        background-color: #fef0f0;
      }
      
      &::placeholder {
        color: #c0c4cc;
        font-size: 13px;
      }
      
      &:disabled,
      &[readonly] {
        background-color: #f5f7fa;
        border-color: #e4e7ed;
        color: #c0c4cc;
        cursor: not-allowed;
        
        &::placeholder {
          color: #c0c4cc;
        }
      }
    }
    
    textarea {
      resize: vertical;
      min-height: 100px;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      line-height: 1.6;
      font-size: 13px;
    }
    
    select {
      cursor: pointer;
      appearance: none;
      background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6,9 12,15 18,9'%3e%3c/polyline%3e%3c/svg%3e");
      background-repeat: no-repeat;
      background-position: right 12px center;
      background-size: 16px;
      padding-right: 40px;
    }
    
    .error-text {
      display: block;
      color: #f56c6c;
      font-size: 12px;
      margin-top: 6px;
      font-weight: 500;
    }
    
    .input-help {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      font-size: 12px;
      color: #909399;
      margin-top: 8px;
      line-height: 1.5;
      padding: 8px 12px;
      background: #f8f9fa;
      border-radius: 6px;
      border-left: 3px solid #67c23a;
      
      svg {
        flex-shrink: 0;
        margin-top: 2px;
      }
    }
    
    .textarea-wrapper {
      position: relative;
      
      .json-indicator {
        position: absolute;
        top: 12px;
        right: 12px;
        display: flex;
        align-items: center;
        gap: 4px;
        background: rgba(255, 255, 255, 0.9);
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 11px;
        color: #909399;
        font-weight: 500;
        border: 1px solid #e4e7ed;
        backdrop-filter: blur(4px);
      }
    }
  }
}

// 按钮样式
.btn {
  padding: 10px 20px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 78px;
  line-height: 1;
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  &.btn-cancel {
    background: #fff;
    border-color: #dcdfe6;
    color: #606266;
    
    &:hover:not(:disabled) {
      color: #409eff;
      border-color: #c6e2ff;
      background-color: #ecf5ff;
    }
  }
  
  &.btn-primary {
    background: #409eff;
    border-color: #409eff;
    color: #fff;
    
    &:hover:not(:disabled) {
      background: #66b1ff;
      border-color: #66b1ff;
    }
    
    &:active:not(:disabled) {
      background: #3a8ee6;
      border-color: #3a8ee6;
    }
  }
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
  margin-right: 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

// 页面样式已移至底部scoped样式中，避免重复

// 工具详情样式
.tools-content {
  background: #f8f9fa;
  
  .no-tools {
    text-align: center;
    padding: 80px 40px;
    
    .empty-icon {
      margin-bottom: 20px;
      opacity: 0.6;
    }
    
    .empty-text {
      h3 {
        margin: 0 0 8px 0;
        font-size: 18px;
        font-weight: 600;
        color: #909399;
      }
      
      p {
        color: #c0c4cc;
        font-size: 14px;
        margin: 0;
        line-height: 1.5;
      }
    }
  }
  
  .tools-overview {
    .tools-stats {
      margin-bottom: 24px;
      
      .stat-card {
        background: white;
        border: 1px solid #ebeef5;
        border-radius: 12px;
        padding: 20px;
        display: flex;
        align-items: center;
        gap: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        
        .stat-icon {
          width: 48px;
          height: 48px;
          background: #f0f7ff;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .stat-info {
          display: flex;
          flex-direction: column;
          gap: 4px;
          
          .stat-number {
            font-size: 24px;
            font-weight: 700;
            color: #409eff;
            line-height: 1;
          }
          
          .stat-label {
            font-size: 14px;
            color: #606266;
            font-weight: 500;
          }
        }
      }
    }
    
    .tools-list {
      .tool-card {
        background: white;
        border: 1px solid #ebeef5;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        transition: all 0.2s ease;
        
        &:hover {
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
          transform: translateY(-2px);
        }
        
        .tool-header {
          margin-bottom: 16px;
          
          .tool-info {
            display: flex;
            align-items: center;
            gap: 12px;
            
            .tool-icon {
              width: 40px;
              height: 40px;
              background: #f0f7ff;
              border-radius: 10px;
              display: flex;
              align-items: center;
              justify-content: center;
              flex-shrink: 0;
            }
            
            .tool-text {
              .tool-name {
                margin: 0 0 4px 0;
                font-size: 18px;
                font-weight: 600;
                color: #303133;
              }
              
              .tool-tag {
                background: #ecf5ff;
                color: #409eff;
                border: 1px solid #b3d8ff;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
                display: inline-block;
              }
            }
          }
        }
        
        .tool-description {
          color: #606266;
          line-height: 1.6;
          margin-bottom: 20px;
          font-size: 14px;
          
          p {
            margin: 0;
          }
        }
        
        .tool-schema {
          background: #f8f9fa;
          border: 1px solid #ebeef5;
          border-radius: 8px;
          padding: 20px;
          
          .schema-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid #e4e7ed;
            font-weight: 600;
            color: #303133;
            font-size: 14px;
          }
          
          .schema-content {
            .schema-meta {
              margin-bottom: 16px;
              
              .meta-item {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
                
                .meta-label {
                  font-weight: 500;
                  color: #606266;
                  min-width: 60px;
                }
                
                .meta-value {
                  color: #303133;
                  
                  &.type {
                    background: #f0f2f5;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 500;
                  }
                }
              }
            }
            
            .required-section {
              margin-bottom: 16px;
              
              .section-title {
                display: flex;
                align-items: center;
                gap: 6px;
                margin-bottom: 12px;
                font-weight: 600;
                color: #f56c6c;
                font-size: 14px;
              }
              
              .required-params {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                
                .required-param {
                  background: #fef0f0;
                  color: #f56c6c;
                  border: 1px solid #fbc4c4;
                  padding: 4px 8px;
                  border-radius: 4px;
                  font-size: 12px;
                  font-weight: 500;
                }
              }
            }
            
            .properties-section {
              .section-title {
                display: flex;
                align-items: center;
                gap: 6px;
                margin-bottom: 12px;
                font-weight: 600;
                color: #67c23a;
                font-size: 14px;
              }
              
              .properties-grid {
                display: grid;
                gap: 12px;
                
                .property-card {
                  background: white;
                  border: 1px solid #ebeef5;
                  border-radius: 6px;
                  padding: 16px;
                  
                  .property-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 8px;
                    
                    .property-name {
                      font-weight: 600;
                      color: #303133;
                      font-size: 14px;
                    }
                    
                    .property-type {
                      background: #ecf5ff;
                      color: #409eff;
                      padding: 2px 8px;
                      border-radius: 4px;
                      font-size: 12px;
                      font-weight: 500;
                    }
                  }
                  
                  .property-body {
                    .property-desc {
                      color: #606266;
                      font-size: 13px;
                      line-height: 1.5;
                      margin: 0 0 8px 0;
                    }
                    
                    .property-default {
                      display: flex;
                      align-items: center;
                      gap: 6px;
                      
                      .default-label {
                        font-size: 12px;
                        color: #909399;
                      }
                      
                      .default-value {
                        background: #f4f4f5;
                        color: #303133;
                        padding: 2px 6px;
                        border-radius: 3px;
                        font-size: 12px;
                        font-family: 'Monaco', 'Menlo', monospace;
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}

.mcp-server-page {
  padding: 24px;
  min-height: calc(100vh - 60px);
  background-color: transparent;
  position: relative;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 28px;
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    padding: 24px 32px;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.2);
    
    h2 {
      margin: 0;
      font-size: 28px;
      font-weight: 700;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      letter-spacing: -0.02em;
      position: relative;
      
      &::after {
        content: '';
        position: absolute;
        bottom: -4px;
        left: 0;
        width: 60px;
        height: 3px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 2px;
      }
    }
    
    .el-button {
      font-weight: 600;
      letter-spacing: 0.025em;
      border-radius: 12px;
      padding: 12px 24px;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(64, 158, 255, 0.3);
      }
    }
  }
  
  .server-list {
    min-height: 400px;
    background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.2);
    overflow: auto;
    
    :deep(.el-table) {
      border-radius: 16px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
      
      .el-table__header {
        th {
          background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
          color: #374151;
          font-weight: 700;
          font-size: 13px;
          padding: 18px 12px;
          border-bottom: 2px solid #e2e8f0;
          letter-spacing: 0.025em;
          text-transform: uppercase;
          
          .cell {
            color: #4b5563;
            font-weight: 700;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
          }
        }
      }
      
      .el-table__body {
        tr {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          
          &:hover {
            background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
          }
          
          td {
            padding: 20px 12px;
            border-bottom: 1px solid #f1f5f9;
            font-size: 14px;
            font-weight: 500;
            color: #374151;
            
            .cell {
              font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
              line-height: 1.5;
            }
          }
        }
      }
    }
    
    .server-avatar {
      width: 40px;
      height: 40px;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid #e1e8ed;
      margin: 0 auto;
      
      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }
    
    .server-name {
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      
      .name {
        font-weight: 600;
        color: #1f2937;
        font-size: 15px;
        display: block;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        letter-spacing: -0.01em;
      }
      
      &.official-server {
        opacity: 0.8;
        
        .name {
          color: #6b7280;
          font-weight: 500;
        }
      }
      
      .official-tag {
        margin-top: 2px;
        font-weight: 600;
        font-size: 11px;
        letter-spacing: 0.025em;
      }
    }
    
    .config-status {
      display: flex;
      justify-content: center;
      align-items: center;
      
      .el-tag {
        font-weight: 600;
        letter-spacing: 0.025em;
        border-radius: 8px;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      }
      
      .clickable-tag {
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        font-weight: 700;
        
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 20px rgba(245, 158, 11, 0.4);
          background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
          border-color: #d97706;
          color: white;
        }
        
        &:active {
          transform: translateY(0);
        }
        
        &::after {
          content: '⚙️';
          margin-left: 6px;
          font-size: 11px;
        }
      }
    }
    
    .user-info {
      display: flex;
      justify-content: center;
      
      .el-tag {
        font-size: 12px;
        padding: 6px 12px;
        font-weight: 600;
        letter-spacing: 0.025em;
        border-radius: 8px;
      }
    }
    
    .tools-count {
      .el-button {
        font-size: 12px;
        padding: 8px 14px;
        font-weight: 600;
        letter-spacing: 0.025em;
        border-radius: 8px;
        transition: all 0.3s ease;
        
        &:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(64, 158, 255, 0.25);
        }
      }
    }
    
    .create-time {
      font-size: 13px;
      color: #6b7280;
      font-weight: 500;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    :deep(.el-table__fixed-right) {
      box-shadow: -2px 0 8px rgba(0, 0, 0, 0.06);
    }
    
    :deep(.el-table__body) {
      .el-button {
        &.el-button--small {
          padding: 10px 18px;
          font-size: 13px;
          font-weight: 600;
          letter-spacing: 0.025em;
          min-width: 70px;
          border-radius: 10px;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
          
          &:hover {
            transform: translateY(-2px);
          }
          
          &.el-button--primary {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            border: none;
            
            &:hover {
              background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
              box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
            }
          }
          
          &.el-button--danger {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            border: none;
            
            &:hover {
              background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
              box-shadow: 0 8px 25px rgba(239, 68, 68, 0.4);
            }
          }
          
          &.el-button--info {
            background: #e5e7eb;
            color: #9ca3af;
            border: none;
            cursor: not-allowed;
            
            &:hover {
              transform: none;
              background: #e5e7eb;
            }
          }
        }
      }
    }
    
        .empty-state {
      text-align: center;
      padding: 80px 20px;

      p {
        margin-top: 24px;
        font-size: 16px;
        color: #6b7280;
        font-weight: 500;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        letter-spacing: -0.01em;
      }
    }

    // Element UI 按钮样式覆盖
    :deep(.el-button) {
      font-size: 12px;
      padding: 8px 15px;
      border-radius: 6px;
      height: auto;
      line-height: 1.2;
      
      &.el-button--small {
        min-width: 60px;
        
        &.el-button--primary {
          background-color: #409eff;
          border-color: #409eff;
        }
        
        &.el-button--danger {
          background-color: #f56c6c;
          border-color: #f56c6c;
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .mcp-server-page {
    padding: 16px;
    
    .page-header {
      flex-direction: column;
      gap: 16px;
      align-items: stretch;
    }
  }
  
  // 配置对话框样式
  .config-dialog {
    max-width: 600px;
    
    .config-info {
      margin-bottom: 24px;
      
      .info-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 1px solid #bae6fd;
        border-radius: 12px;
        padding: 16px;
        display: flex;
        align-items: flex-start;
        gap: 12px;
        
        .info-icon {
          flex-shrink: 0;
          width: 40px;
          height: 40px;
          background: rgba(64, 158, 255, 0.1);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .info-text {
          flex: 1;
          
          h4 {
            margin: 0 0 6px 0;
            font-size: 16px;
            font-weight: 600;
            color: #1e293b;
          }
          
          p {
            margin: 0;
            font-size: 14px;
            color: #64748b;
            line-height: 1.6;
          }
        }
      }
    }
    
    .form-section .form-group textarea {
      min-height: 240px;
    }
    
    .json-indicator {
      span {
        color: #e67e22;
        font-weight: 500;
      }
    }
  }
}
</style>

<!-- 页面本身的样式使用scoped -->
<style lang="scss" scoped>
// 页面样式已移至底部scoped样式中，避免重复
</style>