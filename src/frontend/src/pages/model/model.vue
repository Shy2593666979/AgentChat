<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Connection, Cpu, Search, Refresh } from '@element-plus/icons-vue'
import { 
  getVisibleLLMsAPI, 
  createLLMAPI, 
  deleteLLMAPI,
  type LLMResponse,
  type CreateLLMRequest
} from '../../apis/llm'

const router = useRouter()

// 响应式数据
const models = ref<LLMResponse[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const llmTypes = ref<string[]>(['LLM', 'Embedding', 'Rerank'])

// 创建对话框控制
const createDialogVisible = ref(false)

// 表单相关
const createForm = ref<CreateLLMRequest>({
  model: '',
  api_key: '',
  base_url: '',
  provider: '',
  llm_type: 'LLM'
})

// 获取模型列表
const fetchModels = async () => {
  loading.value = true
  try {
    const response = await getVisibleLLMsAPI()
    
    if (response.data.status_code === 200) {
      const data = response.data.data || {}
      const allModels: LLMResponse[] = []
      
      Object.values(data).forEach((typeModels: any) => {
        if (Array.isArray(typeModels)) {
          allModels.push(...typeModels)
        }
      })
      
      models.value = allModels
    } else {
      ElMessage.error(response.data.status_message || '获取模型列表失败')
    }
  } catch (error) {
    ElMessage.error('获取模型列表失败')
    console.error('获取模型列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索模型
const searchModels = () => {
  fetchModels()
}

// 清空搜索
const clearSearch = () => {
  searchKeyword.value = ''
  fetchModels()
}

// 打开创建对话框
const openCreateDialog = () => {
  console.log('🎯 打开创建对话框')
  createDialogVisible.value = true
  // 重置表单
  Object.assign(createForm.value, {
    model: '',
    api_key: '',
    base_url: '',
    provider: '',
    llm_type: 'LLM'
  })
  console.log('表单重置完成:', createForm.value)
}

// 创建模型
const handleCreate = async () => {
  console.log('🎯 按钮被点击了！')
  
  // 检查必填字段
  if (!createForm.value.model || !createForm.value.api_key || !createForm.value.base_url || !createForm.value.provider || !createForm.value.llm_type) {
    ElMessage.error('请填写所有必填字段')
    return
  }
  
  console.log('创建模型，表单数据:', createForm.value)
  
  try {
    const response = await createLLMAPI(createForm.value)
    console.log('创建模型响应:', response)
    
    if (response.data.status_code === 200) {
      ElMessage.success('🎉 创建成功')
      createDialogVisible.value = false
      fetchModels()
    } else {
      ElMessage.error(response.data.status_message || '❌ 创建失败')
    }
  } catch (error) {
    console.error('创建模型失败:', error)
    ElMessage.error('❌ 创建失败，请检查网络连接')
  }
}

// 跳转到模型编辑器
const goToModelEditor = (model: LLMResponse) => {
  router.push({
    name: 'model-editor',
    query: { id: model.llm_id }
  })
}

// 简单测试函数
const simpleTest = () => {
  console.log('🧪 简单测试被点击了！')
  ElMessage.success('🧪 简单测试成功！')
}

// 删除模型
const handleDelete = async (model: LLMResponse) => {
  console.log('🗑️ 点击删除按钮，模型:', model)
  
  // 使用原生confirm但添加更美观的提示
  const confirmed = confirm(`⚠️ 确认删除模型\n\n模型名称: ${model.model}\n提供商: ${model.provider}\n类型: ${model.llm_type}\n\n此操作不可撤销！\n\n点击"确定"删除，点击"取消"保留。`)
  
  if (confirmed) {
    console.log('用户确认删除，开始调用API')
    try {
      const response = await deleteLLMAPI({ llm_id: model.llm_id })
      console.log('删除API响应:', response)
      
      if (response.data.status_code === 200) {
        ElMessage.success('🎉 删除成功')
        // 重新获取模型列表
        fetchModels()
      } else {
        ElMessage.error(response.data.status_message || '❌ 删除失败')
      }
    } catch (error) {
      console.error('删除模型失败:', error)
      ElMessage.error('❌ 删除失败，请检查网络连接')
    }
  } else {
    console.log('用户取消删除')
  }
}

// 测试模型连接
const testModel = async (model: LLMResponse) => {
  ElMessage.info(`正在测试 ${model.model} 连接...`)
  // 这里可以添加实际的测试逻辑
  setTimeout(() => {
    ElMessage.success(`${model.model} 连接测试完成`)
  }, 2000)
}

// 获取提供商颜色
const getProviderColor = (provider: string) => {
  const colors: Record<string, string> = {
    'OpenAI': 'primary',
    'Anthropic': 'success',
    '阿里云': 'warning',
    '百度': 'info',
    'Google': 'danger'
  }
  return colors[provider] || 'info'
}

// 获取模型类型颜色
const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    'LLM': 'primary',
    'Embedding': 'success',
    'Rerank': 'warning'
  }
  return colors[type] || 'info'
}

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleDateString('zh-CN')
}

onMounted(() => {
  fetchModels()
})
</script>

<template>
  <div class="model-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>🤖 模型管理</h2>
      <div class="header-actions">
        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            placeholder="🔍 搜索模型名称或提供商..."
            :prefix-icon="Search"
            @keyup.enter="searchModels"
            clearable
            @clear="clearSearch"
            style="width: 300px"
          />
        </div>
        
        <div class="action-buttons">
          <el-button 
            :icon="Refresh" 
            @click="fetchModels"
            :loading="loading"
            class="refresh-btn"
          >
            🔄 刷新
          </el-button>
          <el-button 
            type="primary" 
            :icon="Plus"
            @click="openCreateDialog"
            class="add-btn"
          >
            🚀 添加模型
          </el-button>
        </div>
      </div>
    </div>

    <!-- 模型列表 -->
    <div class="model-list" v-loading="loading">
      <div class="model-grid" v-if="models.length > 0">
        <div 
          v-for="model in models" 
          :key="model.llm_id" 
          class="model-card"
          @click="goToModelEditor(model)"
        >
          <!-- 卡片顶部装饰条 -->
          <div class="card-accent"></div>
          
          <!-- 模型图标和状态 -->
          <div class="card-header">
            <div class="model-icon">
              <span class="icon-emoji">🤖</span>
            </div>
            <div class="model-status">
              <div class="status-dot"></div>
              <span class="status-text">✨ 在线</span>
            </div>
          </div>
          
          <!-- 模型信息 -->
          <div class="card-content">
            <h3 class="model-name">
              <span class="name-prefix">🚀</span>
              {{ model.model }}
            </h3>
            <p class="model-description">🎯 AI模型配置 - 让智能对话更简单</p>
            
            <!-- 标签组 -->
            <div class="model-tags">
              <div class="tag provider-tag">
                <span class="tag-icon">🏢</span>
                <span class="tag-text">{{ model.provider }}</span>
              </div>
              <div class="tag type-tag">
                <span class="tag-icon">⚡</span>
                <span class="tag-text">{{ model.llm_type }}</span>
              </div>
            </div>
            
            <!-- 模型统计信息 -->
            <div class="model-stats">
              <div class="stat-item">
                <div class="stat-icon">📅</div>
                <div class="stat-info">
                  <span class="stat-label">🎉 创建于</span>
                  <span class="stat-value">{{ formatTime(model.create_time) }}</span>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">🔄</div>
                <div class="stat-info">
                  <span class="stat-label">✨ 更新于</span>
                  <span class="stat-value">{{ formatTime(model.update_time) }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 操作按钮 -->
          <div class="card-actions">
            <el-button 
              size="small" 
              type="primary"
              @click.stop="goToModelEditor(model)"
              class="action-btn edit-btn"
            >
              <span class="btn-icon">✏️</span>
              编辑
            </el-button>
            <el-button 
              size="small" 
              type="danger"
              @click.stop="handleDelete(model)"
              class="action-btn delete-btn"
            >
              <span class="btn-icon">🗑️</span>
              删除
            </el-button>
            <!-- 测试按钮 -->
            <el-button 
              size="small" 
              type="warning"
              @click.stop="simpleTest"
              class="action-btn test-btn"
            >
              <span class="btn-icon">🧪</span>
              测试
            </el-button>
          </div>
          
          <!-- 装饰元素 -->
          <div class="decoration-elements">
            <div class="decoration-dot dot-1">✨</div>
            <div class="decoration-dot dot-2">💫</div>
            <div class="decoration-dot dot-3">⭐</div>
          </div>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-else-if="!loading" class="empty-state">
        <div class="empty-icon">
          <span class="empty-emoji">🤖</span>
        </div>
        <h3>🎉 暂无模型</h3>
        <p>🌟 点击下方按钮创建您的第一个AI模型吧！</p>
        <el-button 
          type="primary" 
          :icon="Plus"
          @click="openCreateDialog"
          size="large"
        >
          🚀 立即创建
        </el-button>
      </div>
    </div>

    <!-- 创建模型对话框 -->
    <div v-if="createDialogVisible" class="dialog-overlay">
      <div class="dialog-container">
        <div class="dialog-header">
          <h3>🚀 添加模型</h3>
          <button class="close-btn" @click="createDialogVisible = false">✕</button>
        </div>
        
        <div class="dialog-body">
          <div class="form-item">
            <label>模型名称 <span style="color: red;">*</span></label>
            <div class="input-with-count">
              <input 
                v-model="createForm.model"
                type="text" 
                placeholder="请输入模型名称"
                maxlength="50"
              />
              <span class="char-count">
                {{ createForm.model.length }}/50
              </span>
            </div>
          </div>
          
          <div class="form-item">
            <label>API密钥 <span style="color: red;">*</span></label>
            <div class="input-with-count">
              <input 
                v-model="createForm.api_key"
                type="password" 
                placeholder="请输入API密钥"
                maxlength="200"
              />
              <span class="char-count">
                {{ createForm.api_key.length }}/200
              </span>
            </div>
          </div>
          
          <div class="form-item">
            <label>基础URL <span style="color: red;">*</span></label>
            <div class="input-with-count">
              <input 
                v-model="createForm.base_url"
                type="text" 
                placeholder="请输入基础URL"
                maxlength="200"
              />
              <span class="char-count">
                {{ createForm.base_url.length }}/200
              </span>
            </div>
          </div>
          
          <div class="form-item">
            <label>提供商 <span style="color: red;">*</span></label>
            <div class="input-with-count">
              <input 
                v-model="createForm.provider"
                type="text" 
                placeholder="请输入提供商"
                maxlength="50"
              />
              <span class="char-count">
                {{ createForm.provider.length }}/50
              </span>
            </div>
          </div>
          
          <div class="form-item">
            <label>模型类型 <span style="color: red;">*</span></label>
            <div class="select-container">
              <select v-model="createForm.llm_type">
                <option value="LLM">LLM</option>
                <option value="Embedding">Embedding</option>
                <option value="Rerank">Rerank</option>
              </select>
            </div>
          </div>
        </div>
        
        <div class="dialog-footer">
          <button @click.stop="createDialogVisible = false">❌ 取消</button>
          <button 
            class="primary-btn" 
            :disabled="!createForm.model || !createForm.api_key || !createForm.base_url || !createForm.provider || !createForm.llm_type"
            @click.stop="handleCreate"
          >
            ✅ 确定
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.model-page {
  padding: 20px;
  height: 100%;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h2 {
      margin: 0;
      font-size: 28px;
      font-weight: 700;
      color: #1e293b;
      display: flex;
      align-items: center;
      gap: 12px;
      background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    
    .header-actions {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .search-box {
        margin-right: 16px;
        
        .el-input {
          .el-input__wrapper {
            border-radius: 12px;
            border: 2px solid #e2e8f0;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            
            &:hover {
              border-color: #3b82f6;
              box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
            }
            
            &.is-focus {
              border-color: #3b82f6;
              box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
          }
          
          .el-input__inner {
            font-size: 14px;
            font-weight: 500;
            
            &::placeholder {
              color: #94a3b8;
              font-weight: 400;
            }
          }
        }
      }
      
      .action-buttons {
        display: flex;
        gap: 8px;
        
        .refresh-btn {
          transition: all 0.3s ease;
          border-radius: 8px;
          font-weight: 500;
          
          &:hover {
            transform: rotate(180deg);
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border-color: #10b981;
            color: white;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
          }
          
          &:active {
            transform: rotate(180deg) scale(0.95);
          }
        }
        
        .add-btn {
          background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
          border: none;
          border-radius: 8px;
          font-weight: 600;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
          overflow: hidden;
          
          &::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s ease;
          }
          
          &:hover {
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
            
            &::before {
              left: 100%;
            }
          }
          
          &:active {
            transform: translateY(0) scale(0.98);
          }
        }
      }
    }
  }
  
  .model-list {
    height: calc(100% - 80px);
    
    .model-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
      gap: 24px;
      
      .model-card {
        background: white;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(226, 232, 240, 0.6);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        cursor: pointer;
        
        &::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 4px;
          background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
          transform: scaleX(0);
          transition: transform 0.3s ease;
        }
        
        &:hover {
          box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
          transform: translateY(-8px);
          border-color: rgba(59, 130, 246, 0.3);
          
          &::before {
            transform: scaleX(1);
          }
        }
        
        .card-accent {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 6px;
          background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
          border-top-left-radius: 20px;
          border-top-right-radius: 20px;
        }
        
        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          
          .model-icon {
            width: 56px;
            height: 56px;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
            position: relative;
            overflow: hidden;
            
            &::before {
              content: '';
              position: absolute;
              top: -50%;
              left: -50%;
              width: 200%;
              height: 200%;
              background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
              animation: shimmer 3s infinite;
            }
            
            .icon-emoji {
              font-size: 28px;
              z-index: 1;
              position: relative;
              animation: bounce 2s infinite;
            }
          }
          
          .model-status {
            display: flex;
            align-items: center;
            gap: 8px;
            
            .status-dot {
              width: 12px;
              height: 12px;
              background: #10b981;
              border-radius: 50%;
              box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
              animation: pulse 2s infinite;
            }
            
            .status-text {
              font-size: 13px;
              color: #10b981;
              font-weight: 600;
            }
          }
        }
        
        .card-content {
          .model-name {
            font-size: 22px;
            font-weight: 700;
            color: #1e293b;
            margin: 0 0 8px 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            line-height: 1.3;
            display: flex;
            align-items: center;
            gap: 8px;
            
            .name-prefix {
              font-size: 20px;
              animation: rocket 3s infinite;
            }
          }
          
          .model-description {
            font-size: 14px;
            color: #64748b;
            margin-bottom: 16px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 6px;
          }
          
          .model-tags {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
            flex-wrap: wrap;
            
            .tag {
              display: flex;
              align-items: center;
              gap: 6px;
              padding: 8px 16px;
              border-radius: 25px;
              font-size: 13px;
              font-weight: 600;
              color: white;
              box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
              transition: all 0.3s ease;
              
              &:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
              }
              
              .tag-icon {
                font-size: 14px;
              }
              
              &.provider-tag {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
              }
              
              &.type-tag {
                background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
              }
            }
          }
          
          .model-stats {
            display: flex;
            gap: 24px;
            font-size: 13px;
            margin-bottom: 16px;
            
            .stat-item {
              display: flex;
              align-items: center;
              gap: 10px;
              padding: 12px 16px;
              background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
              border-radius: 12px;
              border: 1px solid #e2e8f0;
              transition: all 0.3s ease;
              
              &:hover {
                background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
                transform: translateY(-1px);
              }
              
              .stat-icon {
                font-size: 18px;
              }
              
              .stat-info {
                display: flex;
                flex-direction: column;
                gap: 2px;
                
                .stat-label {
                  color: #64748b;
                  font-size: 11px;
                  font-weight: 500;
                  text-transform: uppercase;
                  letter-spacing: 0.5px;
                }
                
                .stat-value {
                  color: #334155;
                  font-weight: 600;
                  font-size: 13px;
                }
              }
            }
          }
        }
        
        .card-actions {
          display: flex;
          gap: 12px;
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid #f1f5f9;
          position: relative;
          z-index: 10;
          
          .action-btn {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 2px solid transparent;
            position: relative;
            overflow: hidden;
            z-index: 10;
            min-width: 80px;
            min-height: 40px;
            pointer-events: auto;
            cursor: pointer;
            
            .btn-icon {
              font-size: 16px;
              animation: wiggle 2s infinite;
            }
            
            &::before {
              content: '';
              position: absolute;
              top: 0;
              left: -100%;
              width: 100%;
              height: 100%;
              background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
              transition: left 0.5s ease;
            }
            
            &:hover {
              transform: translateY(-2px);
              box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
              
              &::before {
                left: 100%;
              }
            }
            
            &.edit-btn {
              background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
              color: white;
              
              &:hover {
                background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
              }
            }
            
            &.delete-btn {
              background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
              color: white;
              
              &:hover {
                background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
              }
            }
          }
        }
        
        .decoration-elements {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            overflow: hidden;
            z-index: 1;
            
            .decoration-dot {
              position: absolute;
              font-size: 12px;
              opacity: 0.6;
              animation: float 4s infinite ease-in-out;
              
              &.dot-1 {
                top: 20%;
                right: 10%;
                animation-delay: 0s;
              }
              
              &.dot-2 {
                top: 60%;
                right: 15%;
                animation-delay: 1s;
              }
              
              &.dot-3 {
                top: 40%;
                right: 5%;
                animation-delay: 2s;
              }
            }
          }
        }
    }
    
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      text-align: center;
      background: white;
      border-radius: 20px;
      padding: 80px 40px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
      
      .empty-icon {
        font-size: 80px;
        color: #cbd5e1;
        margin-bottom: 24px;
        
        .empty-emoji {
          font-size: 80px;
          animation: bounce 2s infinite;
        }
      }
      
      h3 {
        margin: 0 0 12px 0;
        font-size: 24px;
        font-weight: 600;
        color: #475569;
      }
      
      p {
        margin: 0 0 32px 0;
        color: #64748b;
        font-size: 16px;
        line-height: 1.5;
      }
      
      .el-button {
        padding: 16px 32px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 16px;
      }
    }
  }
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.4);
  }
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%) translateY(-100%) rotate(45deg);
  }
  100% {
    transform: translateX(100%) translateY(100%) rotate(45deg);
  }
}

@keyframes rocket {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  25% {
    transform: translateY(-3px) rotate(-5deg);
  }
  75% {
    transform: translateY(-3px) rotate(5deg);
  }
}

@keyframes wiggle {
  0%, 100% {
    transform: rotate(0deg);
  }
  25% {
    transform: rotate(-5deg);
  }
  75% {
    transform: rotate(5deg);
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-10px) rotate(180deg);
  }
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  
  .dialog-container {
    background: white;
    border-radius: 20px;
    padding: 0;
    width: 90%;
    max-width: 500px;
    max-height: 90vh;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    animation: dialogSlideIn 0.3s ease-out;
    
    .dialog-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 24px 24px 0 24px;
      border-bottom: 1px solid #e2e8f0;
      margin-bottom: 20px;
      
      h3 {
        margin: 0;
        font-size: 20px;
        font-weight: 600;
        color: #1e293b;
      }
      
      .close-btn {
        background: none;
        border: none;
        font-size: 24px;
        color: #64748b;
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        transition: all 0.2s ease;
        
        &:hover {
          background: #f1f5f9;
          color: #475569;
        }
      }
    }
    
    .dialog-body {
      padding: 0 24px 24px 24px;
      
      .form-item {
        margin-bottom: 20px;
        
        label {
          display: block;
          margin-bottom: 8px;
          font-weight: 500;
          color: #374151;
          font-size: 14px;
        }
        
        .input-with-count {
          position: relative;
          
          input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            font-size: 14px;
            transition: all 0.3s ease;
            box-sizing: border-box;
            
            &:focus {
              outline: none;
              border-color: #3b82f6;
              box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            
            &::placeholder {
              color: #9ca3af;
            }
          }
          
          .char-count {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 12px;
            color: #9ca3af;
          }
        }
        
        .select-container {
          select {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            font-size: 14px;
            background: white;
            transition: all 0.3s ease;
            box-sizing: border-box;
            
            &:focus {
              outline: none;
              border-color: #3b82f6;
              box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
          }
        }
      }
    }
    
    .dialog-footer {
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      padding: 20px 24px;
      border-top: 1px solid #e2e8f0;
      
      button {
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
        border: 2px solid transparent;
        
        &:first-child {
          background: #f8fafc;
          color: #64748b;
          border-color: #e2e8f0;
          
          &:hover {
            background: #f1f5f9;
            border-color: #cbd5e1;
          }
        }
        
        &.primary-btn {
          background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
          color: white;
          border-color: #3b82f6;
          
          &:hover {
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
          }
          
          &:disabled {
            background: #9ca3af;
            border-color: #9ca3af;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
          }
        }
      }
    }
  }
}
</style>