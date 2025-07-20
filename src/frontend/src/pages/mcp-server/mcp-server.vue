<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Connection, VideoPlay, Edit, Delete, View, Tools } from '@element-plus/icons-vue'
import { createMCPServerAPI, getMCPServersAPI, deleteMCPServerAPI, type MCPServer, type CreateMCPServerRequest, type MCPServerTool } from '../../apis/mcp-server'

const servers = ref<MCPServer[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const toolsDialogVisible = ref(false)
const formLoading = ref(false)
const editingServer = ref<MCPServer | null>(null)
const selectedServerTools = ref<MCPServerTool[]>([])
const selectedServerName = ref('')

// 表单数据
const formData = ref<CreateMCPServerRequest>({
  server_name: '',
  url: '',
  type: 'sse',
  config: '{}'
})

// 表单验证规则
const rules = {
  server_name: [
    { required: true, message: '请输入服务器名称', trigger: 'blur' },
    { min: 2, max: 50, message: '服务器名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  url: [
    { required: true, message: '请输入服务器地址', trigger: 'blur' },
    { type: 'url', message: '请输入正确的URL格式', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择连接类型', trigger: 'change' }
  ]
}

const fetchServers = async () => {
  loading.value = true
  try {
    const response = await getMCPServersAPI()
    
    if (response?.data?.status_code === 200) {
      servers.value = response.data.data || []
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
  // 重置表单
  formData.value = {
    server_name: '',
    url: '',
    type: 'sse',
    config: '{}'
  }
}

const handleEdit = (server: MCPServer) => {
  editingServer.value = server
  dialogVisible.value = true
  // 填充表单数据
  formData.value = {
    server_name: server.server_name,
    url: server.url,
    type: server.type,
    config: typeof server.config === 'object' ? JSON.stringify(server.config, null, 2) : server.config || '{}'
  }
}

const handleSubmit = async () => {
  if (!formData.value.server_name || !formData.value.url) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  // 处理配置字段
  let configData = {}
  if (formData.value.config && typeof formData.value.config === 'string') {
    try {
      configData = JSON.parse(formData.value.config)
    } catch (error) {
      ElMessage.warning('配置信息格式不正确，请输入有效的JSON格式')
      return
    }
  } else {
    configData = formData.value.config || {}
  }
  
  const submitData = {
    ...formData.value,
    config: configData
  }
  
  formLoading.value = true
  try {
    const response = await createMCPServerAPI(submitData)
    if (response.data.status_code === 200) {
      ElMessage.success(editingServer.value ? '更新MCP服务器成功' : '创建MCP服务器成功')
      dialogVisible.value = false
      await fetchServers() // 刷新列表
    } else {
      ElMessage.error(response.data.status_message || '操作失败')
    }
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  } finally {
    formLoading.value = false
  }
}

const handleDelete = async (server: MCPServer) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除MCP服务器 "${server.server_name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await deleteMCPServerAPI(server.mcp_server_id)
    if (response.data.status_code === 200) {
      ElMessage.success('删除成功')
      await fetchServers() // 刷新列表
    } else {
      ElMessage.error(response.data.status_message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除MCP服务器失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 查看工具详情
const viewTools = (server: MCPServer) => {
  selectedServerTools.value = server.params || []
  selectedServerName.value = server.server_name
  toolsDialogVisible.value = true
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
            <div class="server-name">
              <span class="name">{{ row.server_name }}</span>
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
            <el-tag :type="row.config_enabled ? 'warning' : 'success'" size="small">
              {{ row.config_enabled ? '需配置' : '已就绪' }}
            </el-tag>
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
              size="small" 
              type="primary"
              :icon="Edit"
              @click="handleEdit(row)"
              title="编辑"
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
              size="small" 
              type="danger" 
              :icon="Delete"
              @click="handleDelete(row)"
              title="删除"
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

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingServer ? '编辑MCP服务器' : '添加MCP服务器'"
      width="33%"
      :close-on-click-modal="false"
      class="mcp-edit-dialog"
    >
      <div class="dialog-header">
        <div class="dialog-icon">
          <el-icon size="32" color="#409eff">
            <Connection />
          </el-icon>
        </div>
        <div class="dialog-title-info">
          <h3>{{ editingServer ? '编辑服务器配置' : '添加新的MCP服务器' }}</h3>
          <p>请填写MCP服务器的基本信息和连接配置</p>
        </div>
      </div>
      
      <el-form 
        :model="formData" 
        :rules="rules"
        label-width="120px"
        class="mcp-form"
        ref="formRef"
        label-position="top"
      >
        <div class="form-row">
          <el-form-item label="服务器名称" prop="server_name">
            <el-input 
              v-model="formData.server_name" 
              placeholder="请输入服务器名称"
              size="large"
            />
          </el-form-item>
          
          <el-form-item label="连接类型" prop="type">
            <el-select 
              v-model="formData.type" 
              placeholder="请选择连接类型"
              size="large"
              style="width: 100%"
            >
              <el-option label="SSE (Server-Sent Events)" value="sse">
                <div class="option-item">
                  <span>SSE</span>
                  <span class="option-desc">服务器推送事件</span>
                </div>
              </el-option>
              <el-option label="WebSocket" value="websocket">
                <div class="option-item">
                  <span>WebSocket</span>
                  <span class="option-desc">双向通信协议</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
        </div>
        
        <el-form-item label="服务器地址" prop="url">
          <el-input 
            v-model="formData.url" 
            placeholder="请输入服务器地址，如：http://localhost:3001/sse"
            size="large"
          >
            <template #prepend>
              <el-icon><Connection /></el-icon>
            </template>
          </el-input>
          <div class="form-tip">
            确保服务器地址可以正常访问，支持HTTP和HTTPS协议
          </div>
        </el-form-item>
        
        <el-form-item label="配置信息">
          <el-input 
            v-model="formData.config" 
            type="textarea" 
            placeholder='可选的JSON格式配置信息，例如：&#10;{&#10;  "api_key": "your_api_key",&#10;  "timeout": 30000&#10;}'
            :rows="6"
            size="large"
          />
          <div class="form-tip">
            可选配置，请输入有效的JSON格式。留空则使用默认配置
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false" size="large">
            取消
          </el-button>
          <el-button 
            type="primary" 
            @click="handleSubmit"
            :loading="formLoading"
            size="large"
          >
            {{ editingServer ? '保存修改' : '添加服务器' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 工具详情对话框 -->
    <el-dialog
      v-model="toolsDialogVisible"
      :title="`${selectedServerName} - 可用工具`"
      width="800px"
      top="5vh"
    >
      <div class="tools-content">
        <div v-if="selectedServerTools.length === 0" class="no-tools">
          <el-empty description="该服务器暂无可用工具" />
        </div>
        <div v-else class="tools-list">
          <div 
            v-for="(tool, index) in selectedServerTools" 
            :key="index"
            class="tool-item"
          >
            <div class="tool-header">
              <h4 class="tool-name">{{ tool.name }}</h4>
              <el-tag type="primary" size="small">工具</el-tag>
            </div>
            <p class="tool-description">{{ tool.description }}</p>
            
            <div class="tool-schema">
              <h5>参数结构:</h5>
              <div class="schema-info">
                <p><strong>类型:</strong> {{ tool.input_schema?.type }}</p>
                <p><strong>标题:</strong> {{ tool.input_schema?.title }}</p>
                
                <div v-if="tool.input_schema?.required?.length" class="required-params">
                  <p><strong>必填参数:</strong></p>
                  <ul>
                    <li v-for="param in tool.input_schema.required" :key="param">
                      {{ param }}
                    </li>
                  </ul>
                </div>
                
                <div v-if="tool.input_schema?.properties" class="properties">
                  <p><strong>参数详情:</strong></p>
                  <div class="properties-grid">
                    <div 
                      v-for="(prop, propName) in tool.input_schema.properties" 
                      :key="propName"
                      class="property-item"
                    >
                      <div class="property-name">{{ propName }}</div>
                      <div class="property-details">
                        <span class="property-type">{{ prop.type }}</span>
                        <span v-if="prop.description" class="property-desc">{{ prop.description }}</span>
                        <span v-if="prop.default !== undefined" class="property-default">
                          默认值: {{ prop.default }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="toolsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.mcp-server-page {
  padding: 24px;
  min-height: calc(100vh - 60px);
  background-color: transparent;
  position: relative !important;
  z-index: 1 !important;
  pointer-events: auto !important;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    background: white;
    padding: 20px 24px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    
    h2 {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
      color: #2c3e50;
    }
  }
  
  .server-list {
    min-height: 400px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    overflow: auto;
    
    :deep(.el-table) {
      border-radius: 12px;
      
      .el-table__header {
        th {
          background-color: #f8f9fa;
          color: #2c3e50;
          font-weight: 600;
          font-size: 14px;
          padding: 16px 12px;
          border-bottom: 2px solid #e1e8ed;
        }
      }
      
      .el-table__body {
        tr {
          transition: background-color 0.3s ease;
          
          &:hover {
            background-color: #f8f9fa;
          }
          
          td {
            padding: 16px 12px;
            border-bottom: 1px solid #f0f0f0;
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
      
      .name {
        font-weight: 500;
        color: #2c3e50;
        font-size: 14px;
        display: block;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
    
    .user-info {
      display: flex;
      justify-content: center;
      
      .el-tag {
        font-size: 12px;
        padding: 4px 8px;
      }
    }
    
    .tools-count {
      .el-button {
        font-size: 12px;
        padding: 6px 12px;
      }
    }
    
    .create-time {
      font-size: 13px;
      color: #64748b;
    }
    
    // 固定列样式
    :deep(.el-table__fixed-right) {
      box-shadow: -2px 0 8px rgba(0, 0, 0, 0.06);
    }
    
    // 编辑删除按钮样式
    :deep(.el-table__body) {
      .el-button {
        &.el-button--small {
          padding: 8px 16px;
          font-size: 13px;
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
    
    .empty-state {
      text-align: center;
      padding: 80px 20px;
      color: #64748b;
      
      p {
        margin-top: 24px;
        font-size: 16px;
      }
    }
  }
}

// 编辑对话框样式
.mcp-edit-dialog {
  :deep(.el-dialog) {
    border-radius: 16px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    
    .el-dialog__header {
      padding: 0;
      border-bottom: none;
    }
    
    .el-dialog__body {
      padding: 24px;
    }
    
    .el-dialog__footer {
      padding: 0 24px 24px;
      border-top: 1px solid #f0f0f0;
      margin-top: 24px;
      padding-top: 24px;
    }
  }
  
  .dialog-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 24px;
    padding: 24px 24px 0;
    
    .dialog-icon {
      width: 64px;
      height: 64px;
      background: linear-gradient(135deg, #409eff, #67c23a);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .dialog-title-info {
      flex: 1;
      
      h3 {
        margin: 0 0 4px 0;
        font-size: 20px;
        font-weight: 600;
        color: #2c3e50;
      }
      
      p {
        margin: 0;
        color: #64748b;
        font-size: 14px;
      }
    }
  }
  
  .mcp-form {
    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 8px;
    }
    
    :deep(.el-form-item) {
      margin-bottom: 20px;
      
      .el-form-item__label {
        font-weight: 500;
        color: #2c3e50;
        margin-bottom: 8px;
        font-size: 14px;
      }
      
      .el-input, .el-select {
        .el-input__wrapper {
          border-radius: 8px;
          border: 1.5px solid #e1e8ed;
          transition: all 0.3s ease;
          
          &:hover {
            border-color: #c0c4cc;
          }
          
          &.is-focus {
            border-color: #409eff;
            box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
          }
        }
      }
      
      .el-textarea {
        .el-textarea__inner {
          border-radius: 8px;
          border: 1.5px solid #e1e8ed;
          transition: all 0.3s ease;
          font-family: 'Monaco', 'Consolas', monospace;
          
          &:hover {
            border-color: #c0c4cc;
          }
          
          &:focus {
            border-color: #409eff;
            box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
          }
        }
      }
    }
    
    .form-tip {
      font-size: 12px;
      color: #64748b;
      margin-top: 4px;
      line-height: 1.4;
    }
    
    .option-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .option-desc {
        font-size: 12px;
        color: #999;
      }
    }
  }
  
  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
}

.tools-content {
  max-height: 70vh;
  overflow-y: auto;
  
  .no-tools {
    text-align: center;
    padding: 40px;
  }
  
  .tools-list {
    .tool-item {
      border: 1px solid #e1e8ed;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 16px;
      background: #fafbfc;
      
      .tool-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        
        .tool-name {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: #2c3e50;
        }
      }
      
      .tool-description {
        color: #64748b;
        line-height: 1.5;
        margin-bottom: 16px;
      }
      
      .tool-schema {
        background: white;
        border-radius: 6px;
        padding: 12px;
        
        h5 {
          margin: 0 0 8px 0;
          font-size: 14px;
          font-weight: 600;
          color: #2c3e50;
        }
        
        .schema-info {
          font-size: 13px;
          
          p {
            margin: 4px 0;
          }
          
          .required-params {
            margin-top: 8px;
            
            ul {
              margin: 4px 0;
              padding-left: 20px;
              
              li {
                color: #e74c3c;
                font-weight: 500;
              }
            }
          }
          
          .properties {
            margin-top: 12px;
            
            .properties-grid {
              display: grid;
              gap: 8px;
              margin-top: 8px;
              
              .property-item {
                background: #f8f9fa;
                border-radius: 4px;
                padding: 8px;
                
                .property-name {
                  font-weight: 600;
                  color: #2c3e50;
                  margin-bottom: 4px;
                }
                
                .property-details {
                  display: flex;
                  flex-direction: column;
                  gap: 2px;
                  
                  .property-type {
                    color: #3498db;
                    font-weight: 500;
                    font-size: 12px;
                  }
                  
                  .property-desc {
                    color: #64748b;
                    font-size: 12px;
                    line-height: 1.4;
                  }
                  
                  .property-default {
                    color: #e67e22;
                    font-size: 11px;
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
  
  .mcp-edit-dialog {
    :deep(.el-dialog) {
      width: 90% !important;
      margin: 0 auto;
    }
    
    .mcp-form .form-row {
      grid-template-columns: 1fr;
    }
  }
}
</style> 