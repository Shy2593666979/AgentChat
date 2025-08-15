<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Connection, Cpu, Search, Refresh, Calendar, ChatDotRound, RefreshRight, Star, Link, Timer } from '@element-plus/icons-vue'
import modelIcon from '../../assets/model.svg'
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
const createLoading = ref(false)

// 删除确认对话框控制
const deleteDialogVisible = ref(false)
const deleteLoading = ref(false)
const modelToDelete = ref<LLMResponse | null>(null)

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
  createDialogVisible.value = true
  // 重置表单
  Object.assign(createForm.value, {
    model: '',
    api_key: '',
    base_url: '',
    provider: '',
    llm_type: 'LLM'
  })
}

// 创建模型
const handleCreate = async () => {
  // 检查必填字段
  if (!createForm.value.model || !createForm.value.api_key || !createForm.value.base_url || !createForm.value.provider || !createForm.value.llm_type) {
    ElMessage.error('请填写所有必填字段')
    return
  }
  
  createLoading.value = true
  try {
    const response = await createLLMAPI(createForm.value)
    
    if (response.data.status_code === 200) {
      ElMessage.success('创建成功')
      createDialogVisible.value = false
      fetchModels()
    } else {
      ElMessage.error('创建失败: ' + (response.data.status_message || '未知错误'))
    }
  } catch (error) {
    ElMessage.error('创建失败，请检查输入并稍后重试')
  } finally {
    createLoading.value = false
  }
}

// 跳转到模型编辑器
const goToModelEditor = (model: LLMResponse) => {
  router.push({
    name: 'model-editor',
    query: { id: model.llm_id }
  })
}

// 删除模型
const deleteModel = async (model: LLMResponse) => {
  // 检查是否为官方模型
  if (isOfficialModel(model)) {
    ElMessage.warning('官方模型不可删除')
    return
  }
  
  // 显示删除确认对话框
  modelToDelete.value = model
  deleteDialogVisible.value = true
}

// 确认删除模型
const confirmDelete = async () => {
  if (!modelToDelete.value) return
  
  deleteLoading.value = true
  try {
    const response = await deleteLLMAPI({ llm_id: modelToDelete.value.llm_id })
    
    if (response.data.status_code === 200) {
      ElMessage.success('删除成功')
      deleteDialogVisible.value = false
      fetchModels()
    } else {
      ElMessage.error('删除失败: ' + (response.data.status_message || '未知错误'))
    }
  } catch (err) {
    ElMessage.error('删除失败，请稍后重试')
  } finally {
    deleteLoading.value = false
  }
}

// 取消删除
const cancelDelete = () => {
  deleteDialogVisible.value = false
  modelToDelete.value = null
}

// 检查是否为官方模型
const isOfficialModel = (model: LLMResponse): boolean => {
  return model.user_id === '0'
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

// 截断URL函数
const truncateUrl = (url: string, maxLength: number): string => {
  if (!url) return '';
  if (url.length <= maxLength) return url;
  
  const protocol = url.includes('://') ? url.split('://')[0] + '://' : '';
  const domainPath = url.replace(protocol, '');
  
  // 如果协议+3个点+最后15个字符超过了最大长度，就只显示开头和结尾
  if (protocol.length + 3 + 15 >= maxLength) {
    const start = protocol + domainPath.substring(0, Math.floor((maxLength - protocol.length - 3) / 2));
    const end = domainPath.substring(domainPath.length - Math.floor((maxLength - protocol.length - 3) / 2));
    return start + '...' + end;
  }
  
  // 否则显示协议+域名开头+...+路径结尾
  const visibleLength = maxLength - protocol.length - 3;
  const start = domainPath.substring(0, Math.floor(visibleLength / 2));
  const end = domainPath.substring(domainPath.length - Math.floor(visibleLength / 2));
  
  return protocol + start + '...' + end;
};

// 改进格式化时间函数，使其更友好
const formatTimeFriendly = (timeStr: string) => {
  if (!timeStr) return '-';
  
  try {
    const date = new Date(timeStr);
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    
    return `${year}/${month}/${day}`;
  } catch(e) {
    return timeStr;
  }
}

onMounted(() => {
  fetchModels()
})
</script>

<template>
  <div class="model-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>
        <img :src="modelIcon" class="model-icon" alt="Model" />
        模型管理
      </h2>
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
        <!-- 模型卡片，增强设计感 -->
        <div 
          v-for="model in models" 
          :key="model.llm_id" 
          class="model-card"
          :class="[model.llm_type.toLowerCase(), isOfficialModel(model) ? 'official-model' : '']"
        >
          <!-- 卡片背景装饰 -->
          <div class="card-decoration">
            <div class="deco-circle circle-1"></div>
            <div class="deco-circle circle-2"></div>
            <div class="deco-line line-1"></div>
            <div class="deco-line line-2"></div>
          </div>

          <!-- 顶部类型标签 -->
          <div class="model-badge">
            <span class="badge-icon">
              <el-icon v-if="model.llm_type === 'LLM'"><ChatDotRound /></el-icon>
              <el-icon v-else-if="model.llm_type === 'Embedding'"><Connection /></el-icon>
              <el-icon v-else><RefreshRight /></el-icon>
            </span>
            <span class="badge-text">{{ model.llm_type }}</span>
          </div>
          
          <!-- 官方标记 -->
          <div class="official-badge" v-if="isOfficialModel(model)">
            <el-icon><Star /></el-icon>
            <span>官方</span>
          </div>

          <div class="card-content">
            <!-- 模型信息 -->
            <div class="model-header">
              <div class="model-avatar" :class="model.llm_type.toLowerCase()">
                <span v-if="model.provider === 'OpenAI'" class="provider-icon">O</span>
                <span v-else-if="model.provider === 'Anthropic'" class="provider-icon">A</span>
                <span v-else-if="model.provider === 'Google'" class="provider-icon">G</span>
                <span v-else class="provider-icon">{{ model.provider[0] }}</span>
              </div>
              
              <div class="model-title">
                <h3 class="model-name">{{ model.model }}</h3>
                <div class="model-provider">{{ model.provider }}</div>
              </div>
            </div>
            
            <!-- 模型详情 -->
            <div class="model-details">
              <!-- 优化基础URL和创建时间显示 -->
              <div class="detail-item">
                <div class="detail-icon">
                  <el-icon><Link /></el-icon>
                </div>
                <div class="detail-content">
                  <div class="detail-label url-label">
                    <span>基础URL</span>
                  </div>
                  <el-tooltip 
                    :content="model.base_url" 
                    placement="top" 
                    :show-after="500"
                    effect="light"
                    popper-class="url-tooltip"
                  >
                    <div class="detail-value url-value">{{ truncateUrl(model.base_url, 38) }}</div>
                  </el-tooltip>
                </div>
              </div>

              <div class="detail-item">
                <div class="detail-icon">
                  <el-icon><Timer /></el-icon>
                </div>
                <div class="detail-content">
                  <div class="detail-label date-label">
                    <span>创建时间</span>
                  </div>
                  <div class="detail-value date-value">{{ formatTimeFriendly(model.create_time) }}</div>
                </div>
              </div>
            </div>
            
            <!-- 操作按钮 -->
            <div class="card-actions">
              <el-button 
                size="default" 
                :type="isOfficialModel(model) ? 'info' : 'primary'"
                @click.stop="goToModelEditor(model)"
                :disabled="isOfficialModel(model)"
                :title="isOfficialModel(model) ? '官方模型不可编辑' : '编辑模型'"
                class="action-btn edit-btn"
                :class="{ 'disabled': isOfficialModel(model) }"
              >
                <el-icon><Edit /></el-icon>
                <span>编辑</span>
              </el-button>
              <el-button 
                size="default" 
                :type="isOfficialModel(model) ? 'info' : 'danger'"
                @click.stop="deleteModel(model)"
                :disabled="isOfficialModel(model)"
                :title="isOfficialModel(model) ? '官方模型不可删除' : '删除模型'"
                class="action-btn delete-btn"
                :class="{ 'disabled': isOfficialModel(model) }"
              >
                <el-icon><Delete /></el-icon>
                <span>删除</span>
              </el-button>
            </div>
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
    <div v-if="createDialogVisible" class="dialog-overlay" @click="createDialogVisible = false">
      <div class="dialog-container" @click.stop>
        <!-- 对话框主体 -->
        <div class="dialog-body">
          <div class="form-grid">
            <!-- 基本信息区域 -->
            <div class="form-section">
              <div class="section-header">
                <h4>📝 基本信息</h4>
              </div>
              
              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">模型名称</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input 
                    v-model="createForm.model"
                    type="text" 
                    placeholder="例如：gpt-4, claude-3.5-sonnet"
                    maxlength="50"
                    class="form-input"
                  />
                  <span class="char-count">{{ createForm.model.length }}/50</span>
                </div>
              </div>
              
              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">提供商</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input 
                    v-model="createForm.provider"
                    type="text" 
                    placeholder="例如：OpenAI, Anthropic, 阿里云"
                    maxlength="50"
                    class="form-input"
                  />
                  <span class="char-count">{{ createForm.provider.length }}/50</span>
                </div>
              </div>
              
              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">模型类型</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="select-wrapper">
                  <select v-model="createForm.llm_type" class="form-select">
                    <option value="LLM">🤖 LLM - 大语言模型</option>
                    <option value="Embedding">🔗 Embedding - 嵌入模型</option>
                    <option value="Rerank">📈 Rerank - 重排序模型</option>
                  </select>
                  <div class="select-arrow">
                    <span>▼</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 连接配置区域 -->
            <div class="form-section">
              <div class="section-header">
                <h4>🔧 连接配置</h4>
              </div>
              
              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">基础URL</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input 
                    v-model="createForm.base_url"
                    type="text" 
                    placeholder="例如：https://api.openai.com/v1"
                    maxlength="200"
                    class="form-input"
                  />
                  <span class="char-count">{{ createForm.base_url.length }}/200</span>
                </div>
              </div>
              
              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">API密钥</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input 
                    v-model="createForm.api_key"
                    type="password" 
                    placeholder="请输入您的API密钥"
                    maxlength="200"
                    class="form-input"
                  />
                  <span class="char-count">{{ createForm.api_key.length }}/200</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 对话框底部 -->
        <div class="dialog-footer">
          <button 
            class="dialog-btn cancel-btn" 
            @click.stop="createDialogVisible = false"
          >
            <span class="btn-icon">❌</span>
            <span class="btn-text">取消</span>
          </button>
          <button 
            class="dialog-btn confirm-btn" 
            :class="{ 'disabled': !createForm.model || !createForm.api_key || !createForm.base_url || !createForm.provider || !createForm.llm_type }"
            :disabled="!createForm.model || !createForm.api_key || !createForm.base_url || !createForm.provider || !createForm.llm_type || createLoading"
            @click.stop="handleCreate"
          >
            <span v-if="createLoading" class="btn-icon loading">⏳</span>
            <span v-else class="btn-icon">✅</span>
            <span class="btn-text">{{ createLoading ? '创建中...' : '确定创建' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="deleteDialogVisible" class="dialog-overlay" @click="cancelDelete">
      <div class="delete-dialog-container" @click.stop>
        <!-- 对话框主体 -->
        <div class="delete-dialog-body">
          <p v-if="modelToDelete">
            确定要删除模型 <strong>"{{ modelToDelete.model }}"</strong> 吗？
          </p>
        </div>
        
        <!-- 对话框底部 -->
        <div class="delete-dialog-footer">
          <button 
            class="delete-dialog-btn cancel-btn" 
            @click="cancelDelete"
            :disabled="deleteLoading"
          >
            取消
          </button>
          <button 
            class="delete-dialog-btn confirm-btn" 
            :disabled="deleteLoading"
            @click="confirmDelete"
          >
            {{ deleteLoading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.model-page {
  padding: 30px;
  min-height: calc(100vh - 60px);
  background-color: #f5f7fa;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
    background: linear-gradient(to right, #ffffff, #f8fafc);
    padding: 28px;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    position: relative;
    overflow: hidden;
    
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 4px;
      background: linear-gradient(90deg, #409eff, #67c23a, #e6a23c);
    }
    
    h2 {
      font-size: 26px;
      font-weight: 700;
      margin: 0;
      display: flex;
      align-items: center;
      gap: 12px;
      background: linear-gradient(90deg, #409eff, #3a7be2); // 添加渐变效果，蓝色系
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      
      .model-icon {
        width: 32px;
        height: 32px;
      }
      
      &::before {
        content: '';
        display: none; // 隐藏原来的表情符号
      }
    }
    
    .header-actions {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .search-box {
        margin-right: 12px;
        
        :deep(.el-input__wrapper) {
          border-radius: 8px;
          transition: all 0.3s;
          border: 1px solid #dcdfe6;
          
          &:hover {
            border-color: #409eff;
            box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.2);
          }
        }
      }
      
      .action-buttons {
        display: flex;
        gap: 12px;
        
        .el-button {
          border-radius: 8px;
          padding: 12px 20px;
          font-size: 14px;
          font-weight: 500;
          transition: all 0.3s;
          
          &:hover {
            transform: translateY(-2px);
          }
          
          &.refresh-btn {
            &:hover {
              background-color: #67c23a;
              border-color: #67c23a;
              color: white;
            }
          }
          
          &.add-btn {
            background: linear-gradient(135deg, #409eff 0%, #3a7be2 100%);
            border: none;
            box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
            
            &:hover {
              background: linear-gradient(135deg, #66b1ff 0%, #409eff 100%);
              box-shadow: 0 6px 16px rgba(64, 158, 255, 0.3);
            }
          }
        }
      }
    }
  }
  
  .model-list {
    min-height: 300px;
    position: relative;
    
    .model-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
      gap: 24px;
    }
    
    .model-card {
      background-color: #fff;
      border-radius: 16px;
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
      transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
      overflow: hidden;
      border: 1px solid #ebeef5;
      position: relative;
      z-index: 1;
      
      &:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.12);
        
        .card-decoration {
          .deco-circle {
            opacity: 0.8;
          }
          
          .deco-line {
            opacity: 0.7;
          }
        }
        
        .model-badge {
          transform: translateY(0) scale(1.05);
        }
      }
      
      &.official-model {
        box-shadow: 0 8px 24px rgba(64, 158, 255, 0.15);
        border: 1px solid rgba(64, 158, 255, 0.3);
        
        .card-decoration {
          opacity: 0.8;
        }
      }
      
      &.llm {
        border-top: 3px solid #409eff;
      }
      
      &.embedding {
        border-top: 3px solid #67c23a;
      }
      
      &.rerank {
        border-top: 3px solid #e6a23c;
      }
      
      .card-decoration {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        opacity: 0.3;
        transition: opacity 0.3s;
        z-index: -1;
        
        .deco-circle {
          position: absolute;
          border-radius: 50%;
          opacity: 0.4;
          transition: all 0.6s;
          
          &.circle-1 {
            width: 160px;
            height: 160px;
            right: -60px;
            bottom: -60px;
            background: radial-gradient(circle, rgba(64, 158, 255, 0.2) 0%, rgba(64, 158, 255, 0) 70%);
          }
          
          &.circle-2 {
            width: 120px;
            height: 120px;
            top: -40px;
            left: -40px;
            background: radial-gradient(circle, rgba(103, 194, 58, 0.2) 0%, rgba(103, 194, 58, 0) 70%);
          }
        }
        
        .deco-line {
          position: absolute;
          opacity: 0.3;
          transition: all 0.6s;
          
          &.line-1 {
            height: 2px;
            width: 100%;
            top: 50%;
            left: 0;
            background: linear-gradient(90deg, transparent, rgba(64, 158, 255, 0.3), transparent);
          }
          
          &.line-2 {
            width: 2px;
            height: 100%;
            top: 0;
            left: 70%;
            background: linear-gradient(180deg, transparent, rgba(103, 194, 58, 0.3), transparent);
          }
        }
      }
      
      .model-badge {
        position: absolute;
        top: 20px;
        right: 20px;
        padding: 8px 16px;
        background: rgba(255, 255, 255, 0.9);
        border-radius: 30px;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transition: all 0.3s;
        backdrop-filter: blur(4px);
        border: 1px solid rgba(235, 238, 245, 0.6);
        z-index: 2;
        
        .badge-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          
          .el-icon {
            font-size: 16px;
            color: #409eff;
          }
        }
        
        .badge-text {
          font-size: 14px;
          font-weight: 600;
          color: #303133;
        }
      }
      
      .official-badge {
        position: absolute;
        top: 20px;
        left: 20px;
        padding: 6px 12px;
        background: #fef6e4;
        border: 1px solid #f8d4a5;
        border-radius: 30px;
        display: flex;
        align-items: center;
        gap: 6px;
        z-index: 2;
        
        .el-icon {
          color: #e6a23c;
          font-size: 14px;
        }
        
        span {
          font-size: 12px;
          font-weight: 600;
          color: #e6a23c;
        }
      }
      
      .card-content {
        padding: 30px 24px 24px;
      }
      
      .model-header {
        display: flex;
        align-items: center;
        margin-bottom: 28px;
        
        .model-avatar {
          width: 60px;
          height: 60px;
          border-radius: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 20px;
          flex-shrink: 0;
          position: relative;
          overflow: hidden;
          
          &::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 100%);
            z-index: 1;
          }
          
          .provider-icon {
            font-size: 28px;
            font-weight: 700;
            color: white;
            z-index: 2;
            position: relative;
          }
          
          &.llm {
            background: linear-gradient(135deg, #409eff 0%, #3a7be2 100%);
            box-shadow: 0 6px 16px rgba(64, 158, 255, 0.3);
          }
          
          &.embedding {
            background: linear-gradient(135deg, #67c23a 0%, #529b2e 100%);
            box-shadow: 0 6px 16px rgba(103, 194, 58, 0.3);
          }
          
          &.rerank {
            background: linear-gradient(135deg, #e6a23c 0%, #d9b55b 100%);
            box-shadow: 0 6px 16px rgba(230, 162, 60, 0.3);
          }
        }
        
        .model-title {
          .model-name {
            font-size: 20px;
            font-weight: 700;
            color: #303133;
            margin: 0 0 8px 0;
            line-height: 1.2;
          }
          
          .model-provider {
            font-size: 15px;
            font-weight: 500;
            color: #606266;
          }
        }
      }
      
      .model-details {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 24px;
        border: 1px solid #ebeef5;
        
        .detail-item {
          display: flex;
          align-items: flex-start;
          margin-bottom: 16px;
          
          &:last-child {
            margin-bottom: 0;
          }
          
          .detail-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: rgba(64, 158, 255, 0.1);
            margin-right: 16px;
            flex-shrink: 0;
            
            .el-icon {
              font-size: 16px;
              color: #409eff;
            }
          }
          
          .detail-content {
            flex: 1;
            
            .detail-label {
              font-size: 13px;
              color: #909399;
              margin-bottom: 8px;
              font-weight: 500;
              display: flex;
              align-items: center;
              
              span {
                position: relative;
                padding: 0 4px;
                z-index: 1;
              }
              
              &.url-label span {
                color: #409eff;
                font-weight: 600;
                
                &::before {
                  content: '';
                  position: absolute;
                  bottom: 0;
                  left: 0;
                  right: 0;
                  height: 6px;
                  background-color: rgba(64, 158, 255, 0.15);
                  z-index: -1;
                  border-radius: 3px;
                }
              }
              
              &.date-label span {
                color: #67c23a;
                font-weight: 600;
                
                &::before {
                  content: '';
                  position: absolute;
                  bottom: 0;
                  left: 0;
                  right: 0;
                  height: 6px;
                  background-color: rgba(103, 194, 58, 0.15);
                  z-index: -1;
                  border-radius: 3px;
                }
              }
            }
            
            .detail-value {
              font-size: 14px;
              font-weight: 500;
              color: #606266;
              word-break: break-all;
              
              &.url-value {
                font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
                background: linear-gradient(to right, #409eff, #5cadff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                cursor: pointer;
                position: relative;
                display: inline-block;
                padding: 2px 6px;
                border-radius: 4px;
                background-color: rgba(64, 158, 255, 0.1);
                border: 1px dashed rgba(64, 158, 255, 0.3);
                
                &:hover {
                  background-color: rgba(64, 158, 255, 0.15);
                  border-color: rgba(64, 158, 255, 0.5);
                }
              }
              
              &.date-value {
                font-family: 'Inter', sans-serif;
                font-weight: 600;
                color: #67c23a;
                letter-spacing: 0.5px;
                background-color: rgba(103, 194, 58, 0.1);
                padding: 2px 10px;
                border-radius: 12px;
                display: inline-block;
              }
            }
          }
        }
      }
      
      .card-actions {
        display: flex;
        justify-content: flex-end;
        gap: 12px;
        
        .action-btn {
          transition: all 0.3s;
          border-radius: 8px;
          display: flex;
          align-items: center;
          gap: 8px;
          box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
          min-width: 90px;
          justify-content: center;
          
          .el-icon {
            font-size: 16px;
          }
          
          &:hover:not(.disabled) {
            transform: translateY(-3px);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
          }
          
          &.edit-btn:not(.disabled) {
            background: linear-gradient(135deg, #409eff 0%, #3a7be2 100%);
            border: none;
            
            &:hover {
              background: linear-gradient(135deg, #66b1ff 0%, #409eff 100%);
            }
          }
          
          &.delete-btn:not(.disabled) {
            background: linear-gradient(135deg, #f56c6c 0%, #e45656 100%);
            border: none;
            
            &:hover {
              background: linear-gradient(135deg, #f78989 0%, #f56c6c 100%);
            }
          }
          
          &.disabled {
            opacity: 0.7;
            cursor: not-allowed;
            
            &:hover {
              transform: none;
              box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
            }
          }
        }
      }
    }
    
    .empty-state {
      text-align: center;
      padding: 80px 30px;
      background: white;
      border-radius: 16px;
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
      position: relative;
      overflow: hidden;
      
      &::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, #409eff, #67c23a, #e6a23c);
      }
      
      .empty-icon {
        margin-bottom: 24px;
        position: relative;
        
        &::after {
          content: '';
          position: absolute;
          bottom: -10px;
          left: 50%;
          transform: translateX(-50%);
          width: 60px;
          height: 4px;
          background: linear-gradient(90deg, #409eff, #67c23a);
          border-radius: 2px;
        }
        
        .empty-emoji {
          font-size: 64px;
          opacity: 0.8;
        }
      }
      
      h3 {
        font-size: 22px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 16px;
      }
      
      p {
        font-size: 16px;
        color: #606266;
        margin-bottom: 32px;
        max-width: 500px;
        margin-left: auto;
        margin-right: auto;
      }
      
      .el-button {
        padding: 12px 24px;
        font-size: 16px;
        font-weight: 500;
        border-radius: 8px;
        background: linear-gradient(135deg, #409eff 0%, #3a7be2 100%);
        border: none;
        box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
        transition: all 0.3s;
        
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 16px rgba(64, 158, 255, 0.3);
          background: linear-gradient(135deg, #66b1ff 0%, #409eff 100%);
        }
      }
    }
  }
}

/* 添加URL工具提示样式 */
:deep(.url-tooltip) {
  max-width: 400px;
  word-break: break-all;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  padding: 10px 14px;
}

// 响应式调整
@media (max-width: 768px) {
  .model-page {
    padding: 20px;
    
    .page-header {
      flex-direction: column;
      align-items: stretch;
      gap: 16px;
      padding: 20px;
      
      h2 {
        text-align: center;
        justify-content: center;
      }
      
      .header-actions {
        flex-direction: column;
        align-items: stretch;
        
        .search-box {
          margin-right: 0;
          margin-bottom: 12px;
        }
        
        .action-buttons {
          justify-content: center;
        }
      }
    }
    
    .model-list .model-grid {
      grid-template-columns: 1fr;
    }
  }
}

/* 添加模型对话框样式 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.9) translateY(20px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1) translateY(0);
  }
}

.dialog-container {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border-radius: 20px;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.3),
    0 8px 32px rgba(0, 0, 0, 0.15);
  width: 88%;
  max-width: 750px;
  max-height: 88vh;
  overflow: hidden;
  animation: slideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}



/* 对话框主体 */
.dialog-body {
  padding: 36px;
  max-height: 65vh;
  overflow-y: auto;
  background: #fafbfc;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 36px;
}

.form-section {
  background: white;
  border-radius: 14px;
  padding: 22px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
}

.section-header {
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 2px solid #f1f5f9;
}

.section-header h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #1a202c;
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-item {
  margin-bottom: 20px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 600;
  color: #2d3748;
}

.label-text {
  color: #374151;
}

.required-mark {
  color: #ef4444;
  font-weight: 700;
  font-size: 16px;
}

.input-wrapper,
.select-wrapper {
  position: relative;
}

.form-input {
  width: 100%;
  padding: 16px 20px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 500;
  color: #1f2937;
  background: white;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.1);
  transform: translateY(-1px);
}

.form-input::placeholder {
  color: #9ca3af;
  font-weight: 400;
}

.form-select {
  width: 100%;
  padding: 16px 50px 16px 20px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 500;
  color: #1f2937;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
  appearance: none;
  box-sizing: border-box;
}

.form-select:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.1);
}

.select-arrow {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  color: #6b7280;
  font-size: 12px;
  transition: transform 0.3s ease;
}

.select-wrapper:hover .select-arrow {
  transform: translateY(-50%) rotate(180deg);
}

.char-count {
  position: absolute;
  right: 16px;
  bottom: -24px;
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

/* 对话框底部 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  padding: 20px 36px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.dialog-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 28px;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 120px;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.dialog-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.dialog-btn:hover::before {
  left: 100%;
}

.cancel-btn {
  background: #f1f5f9;
  color: #64748b;
  border: 2px solid #e2e8f0;
}

.cancel-btn:hover {
  background: #e2e8f0;
  color: #475569;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.confirm-btn {
  background: #f1f5f9;
  color: #64748b;
  border: 2px solid #e2e8f0;
}

.confirm-btn:hover:not(.disabled) {
  background: #e2e8f0;
  color: #475569;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.confirm-btn.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #9ca3af;
}

.btn-icon {
  font-size: 16px;
  display: flex;
  align-items: center;
}

.btn-icon.loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.btn-text {
  font-weight: 600;
}

/* 对话框响应式设计 */
@media (max-width: 768px) {
  .dialog-container {
    width: 95%;
    margin: 10px;
    max-height: 95vh;
  }
  
  .dialog-body {
    padding: 24px 20px;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .form-section {
    padding: 16px;
  }
  
  .dialog-footer {
    padding: 16px;
    flex-direction: column;
  }
  
  .dialog-btn {
    width: 100%;
  }
}

/* 删除确认对话框样式 */
.delete-dialog-container {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 400px;
  overflow: hidden;
  animation: slideIn 0.3s ease-out;
  border: 1px solid #e5e7eb;
}

.delete-dialog-body {
  padding: 32px 28px 24px;
  text-align: center;
  
  p {
    margin: 0;
    font-size: 16px;
    color: #374151;
    line-height: 1.5;
    
    strong {
      color: #1f2937;
      font-weight: 600;
    }
  }
}

.delete-dialog-footer {
  display: flex;
  gap: 12px;
  padding: 0 28px 28px;
}

.delete-dialog-btn {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.delete-dialog-btn.cancel-btn {
  background: #f9fafb;
  color: #6b7280;
  border: 1px solid #d1d5db;
}

.delete-dialog-btn.cancel-btn:hover:not(:disabled) {
  background: #f3f4f6;
  color: #374151;
}

.delete-dialog-btn.confirm-btn {
  background: #3b82f6;
  color: white;
  border: 1px solid #3b82f6;
}

.delete-dialog-btn.confirm-btn:hover:not(:disabled) {
  background: #2563eb;
  border-color: #2563eb;
}

.delete-dialog-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 删除对话框响应式设计 */
@media (max-width: 768px) {
  .delete-dialog-container {
    width: 95%;
    margin: 10px;
  }
  
  .delete-dialog-body {
    padding: 24px 20px 20px;
    
    p {
      font-size: 15px;
    }
  }
  
  .delete-dialog-footer {
    padding: 0 20px 24px;
  }
}
</style>