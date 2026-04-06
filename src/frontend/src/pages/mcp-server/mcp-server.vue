<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, reactive } from 'vue'
import { ElMessage, ElMessageBox, UploadProps } from 'element-plus'
import { Plus, Connection, VideoPlay, Edit, Delete, View, Tools } from '@element-plus/icons-vue'
import * as monaco from 'monaco-editor'
import mcpIcon from '../../assets/mcp.svg'
import { 
  createMCPServerAPI, 
  getMCPServersAPI, 
  deleteMCPServerAPI, 
  updateMCPServerAPI,
  updateMCPUserConfigAPI,
  getDefaultMCPLogoAPI,
  type MCPServer, 
  type CreateMCPServerRequest, 
  type UpdateMCPServerRequest,
  type MCPServerTool,
  type MCPUserConfigUpdateRequest
} from '../../apis/mcp-server'

const servers = ref<MCPServer[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const toolsDialogVisible = ref(false)
const configDialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const formLoading = ref(false)
const editingServer = ref<MCPServer | null>(null)
const configuringServer = ref<MCPServer | null>(null)
const deletingServer = ref<MCPServer | null>(null)
const selectedServerTools = ref<MCPServerTool[]>([])
const selectedServerName = ref('')
const expandedToolIndex = ref<number | null>(null) // 当前展开的工具索引
let jsonEditor: monaco.editor.IStandaloneCodeEditor | null = null

// 配置状态
const configStatus = reactive({
  valid: true,
  message: '',
})

// 示例配置JSON
const exampleConfig = `{
  "mcpServers": {
    "amap-maps": {
      "type": "sse",
      "url": "Your_URL",
      "headers": {
        "Authorization": "Bearer Your_Token"
      }
    }
  }
}`

// 表单数据
const formData = ref<CreateMCPServerRequest>({
  server_name: '',
  logo_url: '',
  imported_config: {}
})

// 用于表单输入的字符串版本
const configString = ref('')

// Logo 上传相关
const uploadingLogo = ref(false)

const handleLogoUploadSuccess: UploadProps['onSuccess'] = (response: any) => {
  // 后端通常返回 { data: 'http://xxx/xxx.png', ... } 或直接是字符串
  const imageUrl = typeof response === 'string' ? response : response?.data
  if (imageUrl) {
    formData.value.logo_url = imageUrl
    ElMessage.success('Logo 上传成功')
  } else {
    ElMessage.error('上传失败，未获取到图片链接')
  }
  uploadingLogo.value = false
}

const handleLogoUploadError: UploadProps['onError'] = (err: any) => {
  console.error('Logo 上传失败:', err)
  ElMessage.error('Logo 上传失败，请重试')
  uploadingLogo.value = false
}

const beforeLogoUpload: UploadProps['beforeUpload'] = (file: File) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件作为 Logo')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB')
    return false
  }
  uploadingLogo.value = true
  return true
}

// 用户配置相关数据
const userConfigData = ref<string>('{}') // 仅保留配置数据，编辑时不预加载

// 表单验证
const formErrors = ref<Record<string, string>>({})

const validateForm = () => {
  formErrors.value = {}
  
  // 服务器名称为可选字段，仅在用户填写时做长度校验
  if (formData.value.server_name && formData.value.server_name.trim() !== '') {
    if (formData.value.server_name.length < 2 || formData.value.server_name.length > 50) {
      formErrors.value.server_name = '服务器名称长度在 2 到 50 个字符'
    }
  }
  
  // Logo为可选字段，不需要验证
  
  // 服务器配置验证：必须是有效的JSON格式才能提交
  if (configString.value && configString.value.trim() !== '') {
    // 验证JSON格式
    try {
      const parsed = JSON.parse(configString.value.trim())
      // 验证通过
    } catch (error) {
      formErrors.value.imported_config = '配置信息格式不正确，请输入有效的JSON格式'
    }
  } else if (!editingServer.value) {
    // 仅创建模式下配置为必填
    formErrors.value.imported_config = '请输入服务器配置'
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

const handleCreate = async () => {
  editingServer.value = null
  dialogVisible.value = true
  formErrors.value = {}
  // 阻止背景滚动
  document.body.style.overflow = 'hidden'
  // 重置表单
  formData.value = {
    server_name: '',
    logo_url: '',
    imported_config: {}
  }
  configString.value = ''
  
  // 获取默认logo
  try {
    const response = await getDefaultMCPLogoAPI()
    if (response.data.status_code === 200) {
      formData.value.logo_url = response.data.data.logo_url
    }
  } catch (error) {
    console.error('获取默认logo失败:', error)
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
  
  // 填充服务器信息到表单，包括配置
  formData.value = {
    server_name: server.server_name,
    logo_url: server.logo_url || '',
    imported_config: {}
  }
  
  // 直接使用服务器的imported_config
  if (server.imported_config) {
    configString.value = JSON.stringify(server.imported_config, null, 2)
  } else {
    // 如果没有imported_config，使用url和type重构（兼容旧数据）
    const importedConfig = {
      mcpServers: {
        [server.server_name]: {
          type: server.type,
          url: server.url
        }
      }
    }
    configString.value = JSON.stringify(importedConfig, null, 2)
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
      // 编辑模式：更新服务器信息（包括配置）
      // 处理配置字段：解析JSON
      let configData = undefined
      if (configString.value && configString.value.trim() !== '') {
        try {
          const parsed = JSON.parse(configString.value.trim())
          configData = parsed
        } catch (error) {
          formErrors.value.imported_config = '配置信息格式不正确，请输入有效的JSON格式'
          formLoading.value = false
          return
        }
      }
      
      const updateData: UpdateMCPServerRequest = {
        server_id: editingServer.value.mcp_server_id,
        name: formData.value.server_name,
        logo_url: formData.value.logo_url,
        imported_config: configData
      }
      
      const response = await updateMCPServerAPI(updateData)
      if (response.data.status_code === 200) {
        ElMessage.success('更新MCP服务器成功')
        closeDialog()
        await fetchServers()
      } else {
        ElMessage.error(response.data.status_message || '更新失败')
      }
    } else {
      // 创建模式：创建服务器
      // 处理配置字段：解析JSON，如果用户清空了，使用空对象 {}
      let configData = {}
      if (configString.value && configString.value.trim() !== '') {
        try {
          const parsed = JSON.parse(configString.value.trim())
          configData = parsed
        } catch (error) {
          formErrors.value.imported_config = '配置信息格式不正确，请输入有效的JSON格式'
          formLoading.value = false
          return
        }
      } else {
        // 如果为空或未填写，使用空对象
        configData = {}
      }
      
      const submitData = {
        server_name: formData.value.server_name,
        logo_url: formData.value.logo_url,
        imported_config: configData
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
    // 获取编辑器的最新内容
    const jsonContent = jsonEditor ? jsonEditor.getValue() : userConfigData.value
    
    // 解析用户配置JSON
    let parsedUserConfig = {}
    try {
      parsedUserConfig = JSON.parse(jsonContent.trim() || '[]')
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
    
    closeConfigDialog()
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
  
  // 显示自定义删除确认对话框
  deletingServer.value = server
  deleteDialogVisible.value = true
  // 阻止背景滚动
  document.body.style.overflow = 'hidden'
}

const closeDeleteDialog = () => {
  deleteDialogVisible.value = false
  deletingServer.value = null
  // 恢复背景滚动
  document.body.style.overflow = 'auto'
}

const confirmDelete = async () => {
  if (!deletingServer.value) return
  
  formLoading.value = true
  try {
    const response = await deleteMCPServerAPI(deletingServer.value.mcp_server_id)
    if (response.data.status_code === 200) {
      ElMessage.success('删除成功')
      closeDeleteDialog()
      await fetchServers() // 刷新列表
    } else {
      ElMessage.error(response.data.status_message || '删除失败')
    }
  } catch (error) {
    console.error('删除MCP服务器失败:', error)
    ElMessage.error('删除失败')
  } finally {
    formLoading.value = false
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
  expandedToolIndex.value = null // 重置展开状态
  // 恢复背景滚动
  document.body.style.overflow = 'auto'
}

// 切换工具详情展开/收起
const toggleToolDetail = (index: number) => {
  if (expandedToolIndex.value === index) {
    expandedToolIndex.value = null
  } else {
    expandedToolIndex.value = index
  }
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
    
  // 初始化JSON编辑器
  nextTick(() => {
    initJsonEditor()
  })
}

// 初始化Monaco编辑器
const initJsonEditor = () => {
  const editorContainer = document.getElementById('jsonEditor')
  if (editorContainer && !jsonEditor) {
    // 注册JSON语言
    monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
      validate: true,
      schemas: [{
        uri: 'http://myserver/mcp-config-schema.json',
        fileMatch: ['*'],
        schema: {
          type: 'array',
          items: {
            type: 'object',
            required: ['key', 'label', 'value'],
            properties: {
              key: {
                type: 'string',
                description: '配置项的唯一标识符'
              },
              label: {
                type: 'string',
                description: '配置项的显示名称'
              },
              value: {
                description: '配置项的值'
              }
            }
          }
        }
      }]
    })
    
    // 创建编辑器
    jsonEditor = monaco.editor.create(editorContainer, {
      value: userConfigData.value,
      language: 'json',
      theme: 'vs',
      automaticLayout: true,
      minimap: { enabled: false },
      lineNumbers: 'on',
      roundedSelection: true,
      scrollBeyondLastLine: false,
      fontSize: 14,
      tabSize: 2,
      renderLineHighlight: 'all',
      scrollbar: {
        vertical: 'auto',
        horizontal: 'auto',
      }
    })
    
    // 添加编辑器验证
    jsonEditor.onDidChangeModelContent(() => {
      validateJsonConfig()
    })
    
    // 初始验证
    validateJsonConfig()
  }
}

// 验证JSON配置
const validateJsonConfig = () => {
  if (!jsonEditor) return
  
  const content = jsonEditor.getValue()
  configStatus.valid = true
  configStatus.message = ''
  
  try {
    const parsed = JSON.parse(content)
    if (!Array.isArray(parsed)) {
      configStatus.valid = false
      configStatus.message = '配置必须是JSON数组格式'
      return
    }
    
    // 验证每个项目结构
    for (let i = 0; i < parsed.length; i++) {
      const item = parsed[i]
      if (!item.key || !item.label || item.value === undefined) {
        configStatus.valid = false
        configStatus.message = `第${i+1}项缺少必要字段，请确保包含key、label和value`
        return
      }
    }
  } catch (e) {
    configStatus.valid = false
    configStatus.message = '无效的JSON格式'
  }
}

const closeConfigDialog = () => {
  configDialogVisible.value = false
  configuringServer.value = null
  
  // 销毁编辑器
  if (jsonEditor) {
    jsonEditor.dispose()
    jsonEditor = null
  }
  
  // 恢复背景滚动
  document.body.style.overflow = 'auto'
}

// 更新个人配置
const handleConfigSubmit = async () => {
  if (!configuringServer.value) {
    ElMessage.error('服务器信息缺失，请重试')
    return
  }
  
  // 检查JSON是否有效
  if (!configStatus.valid) {
    ElMessage.error(configStatus.message || 'JSON格式无效')
    return
  }
  
  formLoading.value = true
  try {
    // 获取编辑器的最新内容
    const jsonContent = jsonEditor ? jsonEditor.getValue() : userConfigData.value
    
    // 解析用户配置JSON
    let parsedUserConfig = {}
    try {
      parsedUserConfig = JSON.parse(jsonContent.trim() || '[]')
    } catch (error) {
      ElMessage.error('用户配置JSON格式错误: ' + (error as Error).message)
      formLoading.value = false
      return
    }

    // 准备请求参数
    const requestData: MCPUserConfigUpdateRequest = {
      server_id: configuringServer.value.mcp_server_id,
      config: parsedUserConfig
    }

    console.log('准备发送配置更新请求:', requestData)
    
    // 调用API更新配置
    const response = await updateMCPUserConfigAPI(requestData)
    console.log('配置更新响应:', response)
    
    if (response.data.status_code === 200) {
      ElMessage.success('个人配置更新成功')
      closeConfigDialog()
      await fetchServers()
    } else {
      ElMessage.error(response.data.status_message || '保存失败')
    }
  } catch (error) {
    console.error('配置更新失败:', error)
    ElMessage.error('配置更新失败: ' + (error as Error).message)
  } finally {
    formLoading.value = false
  }
}

// 插入示例配置
const insertExampleConfig = () => {
  if (!jsonEditor) return
  
  const exampleConfig = [
    {
      "key": "api_key",
      "label": "API密钥",
      "value": "your_api_key_here"
    },
    {
      "key": "timeout",
      "label": "超时时间(毫秒)",
      "value": 30000
    },
    {
      "key": "model",
      "label": "模型名称",
      "value": "gpt-4"
    }
  ]
  
  jsonEditor.setValue(JSON.stringify(exampleConfig, null, 2))
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
  
  // 销毁编辑器
  if (jsonEditor) {
    jsonEditor.dispose()
    jsonEditor = null
  }
})

// 保存用户配置
const saveUserConfig = async () => {
  if (!configuringServer.value || !jsonEditor) return
  
  try {
    // 更新用户配置
    const configContent = jsonEditor.getValue()
    
    // 验证JSON格式
    if (!configStatus.valid) {
      ElMessage.error('配置格式错误，无法保存')
      return
    }
    
    // 准备请求数据
    const requestData: MCPUserConfigUpdateRequest = {
      mcp_server_id: configuringServer.value.mcp_server_id,
      user_config: configContent
    }
    
    // 发送请求
    // console.log('准备发送配置更新请求:', requestData)
    const response = await updateMCPUserConfigAPI(requestData)
    // console.log('配置更新响应:', response)
    
    if (response.data.status_code === 200) {
      ElMessage.success('配置保存成功')
      configDialogVisible.value = false
      await fetchServers() // 刷新列表
    } else {
      ElMessage.error(response.data.status_message || '保存配置失败')
    }
  } catch (error) {
    console.error('保存MCP用户配置失败:', error)
    ElMessage.error('保存失败')
  }
}
</script>

<template>
  <div class="mcp-server-page">
    <div class="page-header">
      <div class="header-title">
        <img :src="mcpIcon" alt="MCP" class="title-icon" />
        <h2>MCP Server管理</h2>
      </div>
      <div class="header-actions">
        <el-button type="success" @click="$router.push('/mcp-server/chat')">
          对话生成 MCP
        </el-button>
        <el-button type="primary" :icon="Plus" @click="handleCreate">
          添加服务器
        </el-button>
      </div>
    </div>

    <div class="server-list">
      <el-table v-if="servers.length > 0" :data="servers || []" style="width: 100%">
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
        
        <el-table-column prop="server_name" label="服务器名称" min-width="150" align="center">
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
        
        <el-table-column prop="type" label="连接类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="row.type === 'sse' ? 'primary' : 'success'">
              {{ row.type.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        
        <!-- 可用工具数量列 -->
        <el-table-column label="可用工具" width="140" align="center">
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
        <el-table-column label="配置状态" width="110" align="center">
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
        
        <el-table-column label="创建时间" min-width="180" align="center">
          <template #default="{ row }">
            <div class="create-time">
              <span>{{ new Date(row.create_time).toLocaleString() }}</span>
            </div>
          </template>
        </el-table-column>
        
        <!-- 操作列 -->
        <el-table-column label="操作" width="180" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button 
                v-if="String(row.user_id) !== '0'"
                size="small" 
                type="primary"
                :icon="Edit"
                @click="handleEdit(row)"
                title="编辑"
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
              >
                编辑
              </el-button>
              
              <el-button 
                v-if="String(row.user_id) !== '0'"
                size="small" 
                type="danger" 
                :icon="Delete"
                @click="handleDelete(row)"
                title="删除"
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
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="servers.length === 0 && !loading" class="empty-state">
        <div class="empty-icon">
          <i class="empty-icon-symbol">📡</i>
        </div>
        <h3>暂无MCP服务</h3>
        <p>添加MCP服务器以增强智能体的能力</p>
        <el-button type="primary" @click="handleCreate()" class="create-btn">
          添加服务器
        </el-button>
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
                <!-- 统一表单区域 -->
                <div class="form-section">
                  <div class="form-layout">
                    <!-- 服务器名称 -->
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
                        placeholder="例如：Weather-Server"
                        :class="{ 'error': formErrors.server_name }"
                      />
                      <span v-if="formErrors.server_name" class="error-text">{{ formErrors.server_name }}</span>
                    </div>

                    <!-- Logo -->
                    <div class="form-group">
                      <label>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M4 4h16v16H4z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                          <path d="M4 15l4-4 4 4 4-5 4 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                        </svg>
                        Logo
                      </label>
                      <el-upload
                        class="logo-upload-square"
                        action="/api/v1/upload"
                        :show-file-list="false"
                        :on-success="handleLogoUploadSuccess"
                        :on-error="handleLogoUploadError"
                        :before-upload="beforeLogoUpload"
                        accept="image/*"
                      >
                        <div v-if="formData.logo_url" class="logo-preview-square">
                          <img :src="formData.logo_url" alt="logo 预览" />
                          <div class="logo-overlay">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                              <path d="M12 5v14M5 12h14" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                          </div>
                        </div>
                        <div v-else class="logo-upload-placeholder" :class="{ 'uploading': uploadingLogo }">
                          <svg v-if="!uploadingLogo" width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 5v14M5 12h14" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                          </svg>
                          <span v-else class="uploading-text">上传中...</span>
                        </div>
                      </el-upload>
                      <span v-if="formErrors.logo_url" class="error-text">{{ formErrors.logo_url }}</span>
                    </div>

                    <!-- 服务配置 -->
                    <div class="form-group form-group-full">
                      <label for="imported_config">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <polyline points="10,9 9,9 8,9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        服务配置 <span v-if="!editingServer" class="required-mark">*</span>
                      </label>
                      <div class="textarea-wrapper">
                        <textarea 
                          id="imported_config"
                          v-model="configString" 
                          rows="8"
                          :placeholder="exampleConfig"
                          :class="{ 'error': formErrors.imported_config }"
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
                      <span v-if="formErrors.imported_config" class="error-text">{{ formErrors.imported_config }}</span>
                      <span v-if="editingServer" class="help-text">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <circle cx="12" cy="12" r="10" stroke="#909399" stroke-width="2"/>
                          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" stroke="#909399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <line x1="12" y1="17" x2="12.01" y2="17" stroke="#909399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        编辑模式下，如果不修改配置可以保持原样，只修改需要更新的字段
                      </span>
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
                  class="tool-item"
                  :class="{ 'expanded': expandedToolIndex === index }"
                  @click="toggleToolDetail(index)"
                >
                  <div class="tool-summary">
                    <div class="tool-info">
                      <div class="tool-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.77 3.77z" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                      </div>
                      <div class="tool-text">
                        <h4 class="tool-name">{{ tool.name }}</h4>
                        <p class="tool-description">{{ tool.description || '暂无描述' }}</p>
                      </div>
                    </div>
                    <div class="tool-expand-icon">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <polyline points="6 9 12 15 18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </div>
                  </div>
                  
                  <!-- 展开的详细信息 -->
                  <transition name="expand">
                    <div v-if="expandedToolIndex === index" class="tool-details" @click.stop>
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
                  </transition>
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
            <h3>
              <span class="config-server-name">{{ configuringServer?.server_name }}</span>
              <span class="config-title">个人配置</span>
            </h3>
            <button class="close-btn" @click="closeConfigDialog">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
          
          <div class="modal-body">
            <!-- 配置指引卡片 -->
            <div class="config-info">
              <div class="info-card">
                <div class="info-icon">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="#409eff" stroke-width="2"/>
                    <path d="M9 12l2 2 4-4" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <div class="info-text">
                  <h4>个人配置</h4>
                  <p>为此MCP服务配置您的个人参数，这些设置将仅对您的账户有效，不会影响其他用户。</p>
                </div>
              </div>
            </div>
            
            <!-- 顶部工具栏 -->
            <div class="editor-toolbar">
              <div class="toolbar-left">
                <button 
                  class="toolbar-btn" 
                  @click="insertExampleConfig" 
                  title="插入示例配置"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  <span>插入示例</span>
                </button>
              </div>
              <div class="toolbar-right">
                <span class="validation-status" :class="{ 'is-valid': configStatus.valid, 'is-invalid': !configStatus.valid }">
                  <svg v-if="configStatus.valid" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                    <path d="M12 8v4M12 16h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  <span>{{ configStatus.valid ? 'JSON有效' : configStatus.message }}</span>
                </span>
              </div>
            </div>
            
            <!-- JSON编辑器 -->
            <div class="editor-container">
              <div id="jsonEditor" class="json-editor"></div>
            </div>
            
            <!-- 帮助说明 -->
            <div class="config-help">
              <h4 class="help-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="#409eff" stroke-width="2"/>
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <line x1="12" y1="17" x2="12.01" y2="17" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                配置说明
              </h4>
              <div class="help-content">
                <div class="help-item">
                  <h5>配置格式</h5>
                  <p>配置必须是有效的JSON数组格式，每个配置项包含以下必填字段：</p>
                  <ul>
                    <li><code>key</code>: 配置项的唯一标识符</li>
                    <li><code>label</code>: 配置项的显示名称</li>
                    <li><code>value</code>: 配置项的值（可以是字符串、数字或布尔值）</li>
                  </ul>
                </div>
                <div class="help-item">
                  <h5>使用方法</h5>
                  <p>点击"插入示例"按钮可快速添加示例配置。完成编辑后点击"保存配置"按钮进行保存。</p>
                </div>
                <div class="help-item">
                  <h5>编辑器快捷键</h5>
                  <ul class="shortcut-list">
                    <li><span class="key">Ctrl+Space</span> 触发自动完成</li>
                    <li><span class="key">Ctrl+S</span> 格式化文档</li>
                    <li><span class="key">Alt+↑/↓</span> 移动行</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
          
          <div class="modal-footer">
            <button type="button" @click="closeConfigDialog" class="btn btn-cancel">
              取消
            </button>
            <button 
              type="button" 
              @click="handleConfigSubmit"
              :disabled="formLoading || !configStatus.valid"
              class="btn btn-primary"
              :title="!configStatus.valid ? configStatus.message : ''"
            >
              <span v-if="formLoading" class="loading-spinner"></span>
              保存配置
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 删除确认弹窗 -->
    <Teleport to="body">
      <div v-if="deleteDialogVisible" class="modal-overlay" @click.self="closeDeleteDialog">
        <div class="modal-dialog delete-dialog">
          <div class="modal-header delete-header">
            <div class="warning-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="#f56c6c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="rgba(245, 108, 108, 0.1)"/>
                <line x1="12" y1="9" x2="12" y2="13" stroke="#f56c6c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="12" y1="17" x2="12.01" y2="17" stroke="#f56c6c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h3>确认删除</h3>
            <button class="close-btn" @click="closeDeleteDialog">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
          
          <div class="modal-body delete-body">
            <div class="delete-warning">
              <p class="warning-text">
                您确定要删除MCP服务器 
                <strong class="server-name-highlight">{{ deletingServer?.server_name }}</strong> 
                吗？
              </p>
              <div class="warning-details">
                <div class="detail-item">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="#e6a23c" stroke-width="2"/>
                    <path d="M12 8v4" stroke="#e6a23c" stroke-width="2" stroke-linecap="round"/>
                    <path d="M12 16h.01" stroke="#e6a23c" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                  <span>此操作将永久删除该服务器配置</span>
                </div>
                <div class="detail-item">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="#e6a23c" stroke-width="2"/>
                    <path d="M12 8v4" stroke="#e6a23c" stroke-width="2" stroke-linecap="round"/>
                    <path d="M12 16h.01" stroke="#e6a23c" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                  <span>相关的工具和配置也将被移除</span>
                </div>
                <div class="detail-item">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="#e6a23c" stroke-width="2"/>
                    <path d="M12 8v4" stroke="#e6a23c" stroke-width="2" stroke-linecap="round"/>
                    <path d="M12 16h.01" stroke="#e6a23c" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                  <span>此操作不可恢复，请谨慎操作</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="modal-footer delete-footer">
            <button type="button" @click="closeDeleteDialog" class="btn btn-cancel">
              取消
            </button>
            <button 
              type="button" 
              @click="confirmDelete"
              :disabled="formLoading"
              class="btn btn-danger"
            >
              <span v-if="formLoading" class="loading-spinner"></span>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <polyline points="3 6 5 6 21 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="10" y1="11" x2="10" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="14" y1="11" x2="14" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              确认删除
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
  
  &.delete-dialog {
    max-width: 480px;
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
  overflow: hidden;
  flex: 1;
  background: #fafafa;
  
  &.tools-content {
    overflow-y: auto;
    max-height: calc(90vh - 140px);
  }
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  background: #fff;
}

// 删除对话框样式
.delete-dialog {
  .delete-header {
    background: linear-gradient(135deg, #fff5f5 0%, #fff0f0 100%);
    border-bottom-color: #fde2e2;
    position: relative;
    padding-left: 60px;
    
    .warning-icon {
      position: absolute;
      left: 20px;
      top: 50%;
      transform: translateY(-50%);
    }
    
    h3 {
      color: #f56c6c;
    }
  }
  
  .delete-body {
    padding: 24px;
  }
  
  .delete-warning {
    .warning-text {
      font-size: 16px;
      color: #303133;
      margin: 0 0 20px 0;
      line-height: 1.6;
      
      .server-name-highlight {
        color: #f56c6c;
        font-weight: 600;
        padding: 2px 6px;
        background: rgba(245, 108, 108, 0.1);
        border-radius: 4px;
      }
    }
    
    .warning-details {
      background: #fef0f0;
      border: 1px solid #fde2e2;
      border-radius: 8px;
      padding: 16px;
      
      .detail-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        margin-bottom: 12px;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        svg {
          flex-shrink: 0;
          margin-top: 2px;
        }
        
        span {
          font-size: 14px;
          color: #606266;
          line-height: 1.5;
        }
      }
    }
  }
  
  .delete-footer {
    background: #fafafa;
    
    .btn-danger {
      background: #f56c6c;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 6px;
      
      &:hover:not(:disabled) {
        background: #f78989;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(245, 108, 108, 0.3);
      }
      
      &:active:not(:disabled) {
        transform: translateY(0);
      }
      
      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      
      .loading-spinner {
        width: 14px;
        height: 14px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-top-color: white;
        border-radius: 50%;
        animation: spin 0.6s linear infinite;
      }
    }
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
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
      
      .required-mark {
        color: #f56c6c;
        margin-left: 4px;
      }
    }
  }
  
  .form-layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    
    @media (max-width: 768px) {
      grid-template-columns: 1fr;
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
    margin-bottom: 0;
    
    &.form-group-full {
      grid-column: 1 / -1;
      margin-bottom: 0;
    }
    
    label {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 12px;
      font-size: 14px;
      
      .required-mark {
        color: #f56c6c;
        margin-left: 2px;
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
      font-size: 16px;
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
    
    .help-text {
      display: flex;
      align-items: flex-start;
      gap: 6px;
      font-size: 12px;
      color: #909399;
      margin-top: 8px;
      line-height: 1.5;
      padding: 8px 12px;
      background: #f5f7fa;
      border-radius: 4px;
      border-left: 3px solid #409eff;
      
      svg {
        flex-shrink: 0;
        margin-top: 2px;
      }
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
    
    // 方形加号上传按钮样式
    .logo-upload-square {
      margin-left: 20px;
      
      :deep(.el-upload) {
        width: 100px;
        height: 100px;
        border: 2px solid #409eff;
        border-radius: 8px;
        cursor: pointer;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        background: #ecf5ff;
        display: block;
        box-sizing: border-box;
        
        &:hover {
          background: #409eff;
          border-color: #409eff;
          
          .logo-upload-placeholder {
            svg path {
              stroke: white !important;
            }
          }
        }
      }
      
      .logo-upload-placeholder {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #409eff;
        transition: all 0.3s ease;
        background: transparent;
        
        svg {
          width: 32px;
          height: 32px;
          display: block;
          
          path {
            stroke: #409eff !important;
            stroke-width: 2.5;
          }
        }
        
        &.uploading {
          .uploading-text {
            font-size: 12px;
            color: #409eff;
            font-weight: 500;
          }
        }
      }
      
      :deep(.el-upload:hover) {
        .logo-upload-placeholder {
          color: white;
          
          svg path {
            stroke: white !important;
          }
        }
      }
      
      .logo-preview-square {
        width: 100%;
        height: 100%;
        position: relative;
        border-radius: 8px;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        
        img {
          width: 50px;
          height: 50px;
          object-fit: cover;
          border-radius: 4px;
        }
        
        .logo-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          opacity: 0;
          transition: opacity 0.3s ease;
          
          &:hover {
            opacity: 1;
          }
        }
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
      .tool-item {
        background: white;
        border: 1px solid #ebeef5;
        border-radius: 12px;
        margin-bottom: 12px;
        overflow: hidden;
        transition: all 0.2s ease;
        cursor: pointer;
        
        &:hover {
          border-color: #409eff;
          box-shadow: 0 2px 12px rgba(64, 158, 255, 0.1);
        }
        
        &.expanded {
          border-color: #409eff;
          box-shadow: 0 4px 16px rgba(64, 158, 255, 0.15);
          
          .tool-expand-icon svg {
            transform: rotate(180deg);
          }
        }
        
        .tool-summary {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 24px;
          
          .tool-info {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            flex: 1;
            
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
              flex: 1;
              
              .tool-name {
                margin: 0 0 6px 0;
                font-size: 16px;
                font-weight: 600;
                color: #303133;
              }
              
              .tool-description {
                margin: 0;
                color: #606266;
                font-size: 14px;
                line-height: 1.5;
              }
            }
          }
          
          .tool-expand-icon {
            flex-shrink: 0;
            color: #909399;
            transition: all 0.3s ease;
            
            svg {
              transition: transform 0.3s ease;
            }
          }
        }
        
        .tool-details {
          border-top: 1px solid #ebeef5;
          padding: 0 24px 20px 24px;
          
          .tool-schema {
            background: #f8f9fa;
            border: 1px solid #ebeef5;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
            
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
    
    // 展开动画
    .expand-enter-active,
    .expand-leave-active {
      transition: all 0.3s ease;
      max-height: 2000px;
      overflow: hidden;
    }
    
    .expand-enter-from,
    .expand-leave-to {
      max-height: 0;
      opacity: 0;
    }
  }
}

.mcp-server-page {
  padding: 32px;
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    padding: 20px 28px;
    border-radius: 16px;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.06);
    border: 1px solid rgba(226, 232, 240, 0.6);
    
    .header-title {
      display: flex;
      align-items: center;
      gap: 14px;
      
      .title-icon {
        width: 36px;
        height: 36px;
      }
      
      h2 {
        margin: 0;
        font-size: 24px;
        font-weight: 600;
        background: linear-gradient(90deg, #1B7CE4, #409eff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
    }
    
    .header-actions {
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
    
    .action-buttons {
      display: flex;
      gap: 8px;
      justify-content: center;
      align-items: center;
      
      .el-button {
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
        
        &:hover {
          transform: translateY(-1px);
        }
      }
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

// 配置对话框样式改进
.config-dialog {
  max-width: 800px;
  
  .modal-header h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .config-server-name {
      font-weight: 700;
      color: #1e293b;
    }
    
    .config-title {
      color: #64748b;
      font-weight: 500;
    }
    
    &::before {
      content: '';
      display: inline-block;
      width: 4px;
      height: 18px;
      background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
      border-radius: 2px;
      margin-right: 8px;
    }
  }
  
  .config-info {
    margin-bottom: 20px;
    
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
        background: rgba(59, 130, 246, 0.1);
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
  
  // 编辑器工具栏
  .editor-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 12px;
    
    .toolbar-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      border: none;
      background: #f1f5f9;
      color: #475569;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
      
      &:hover {
        background: #e2e8f0;
        color: #334155;
      }
      
      svg {
        width: 16px;
        height: 16px;
      }
    }
    
    .validation-status {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      padding: 6px 12px;
      border-radius: 6px;
      
      &.is-valid {
        background: rgba(34, 197, 94, 0.1);
        color: #16a34a;
      }
      
      &.is-invalid {
        background: rgba(239, 68, 68, 0.1);
        color: #dc2626;
      }
    }
  }
  
  // 编辑器容器
  .editor-container {
    height: 300px;
    border: 1px solid #e2e8f0;
    border-bottom-left-radius: 8px;
    border-bottom-right-radius: 8px;
    overflow: hidden;
    
    .json-editor {
      height: 100%;
      width: 100%;
    }
  }
  
  // 帮助说明
  .config-help {
    margin-top: 24px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    overflow: hidden;
    
    .help-title {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
      padding: 12px 16px;
      background: #f1f5f9;
      color: #1e293b;
      font-size: 14px;
      font-weight: 600;
      border-bottom: 1px solid #e2e8f0;
    }
    
    .help-content {
      padding: 16px;
      
      .help-item {
        margin-bottom: 16px;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        h5 {
          margin: 0 0 8px 0;
          font-size: 14px;
          color: #334155;
          font-weight: 600;
        }
        
        p {
          margin: 0 0 8px 0;
          font-size: 13px;
          color: #475569;
          line-height: 1.5;
        }
        
        ul {
          margin: 0;
          padding-left: 20px;
          
          li {
            font-size: 13px;
            color: #475569;
            margin-bottom: 4px;
            
            code {
              background: #e2e8f0;
              padding: 2px 4px;
              border-radius: 4px;
              color: #334155;
              font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
              font-size: 12px;
            }
          }
        }
        
        .shortcut-list {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 8px;
          list-style-type: none;
          padding: 0;
          
          li {
            display: flex;
            align-items: center;
            gap: 8px;
            
            .key {
              background: #e2e8f0;
              padding: 2px 6px;
              border-radius: 4px;
              color: #475569;
              font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
              font-size: 12px;
              border: 1px solid #cbd5e1;
              box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
            }
          }
        }
      }
    }
  }
  
  .modal-footer {
    .btn-primary {
      &:disabled {
        opacity: 0.7;
        cursor: not-allowed;
      }
    }
  }
}

@media (max-width: 768px) {
  .config-dialog {
    .editor-container {
      height: 250px;
    }
    
    .config-help {
      .help-content {
        .help-item {
          .shortcut-list {
            grid-template-columns: 1fr;
          }
        }
      }
    }
  }
}

/* 空状态样式 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  margin: 20px auto;
  max-width: 600px;
  
  .empty-icon {
    width: 120px;
    height: 120px;
    display: flex;
    justify-content: center;
    align-items: center;
    background: rgba(64, 158, 255, 0.1);
    border-radius: 50%;
    margin-bottom: 20px;
    
    .empty-icon-symbol {
      font-size: 60px;
    }
  }
  
  h3 {
    font-size: 20px;
    color: #303133;
    margin: 0 0 16px;
  }
  
  p {
    margin: 0 0 20px;
    font-size: 16px;
    color: #909399;
    max-width: 300px;
  }
  
  .create-btn {
    padding: 12px 24px;
    font-size: 16px;
  }
}
</style>

<!-- 页面本身的样式使用scoped -->
<style lang="scss" scoped>
// 页面样式已移至底部scoped样式中，避免重复
</style>