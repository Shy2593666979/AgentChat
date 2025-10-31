<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElDialog, ElForm, ElFormItem, ElInput, ElButton } from 'element-plus'
import 'element-plus/es/components/dialog/style/css'
import 'element-plus/es/components/form/style/css'
import 'element-plus/es/components/form-item/style/css'
import 'element-plus/es/components/input/style/css'
import 'element-plus/es/components/button/style/css'
import { Plus, Document, Folder, Edit, Delete } from '@element-plus/icons-vue'
import knowledgeIcon from '../../assets/knowledge.svg'
import { 
  getKnowledgeListAPI, 
  createKnowledgeAPI,
  updateKnowledgeAPI,
  deleteKnowledgeAPI,
  KnowledgeResponse,
  type KnowledgeDeleteRequest,
  type KnowledgeCreateRequest,
  type KnowledgeUpdateRequest
} from '../../apis/knowledge'
import { KnowledgeListType } from '../../type'

const router = useRouter()
const knowledges = ref<KnowledgeListType[]>([])
const loading = ref(false)

// 创建知识库对话框
const createDialogVisible = ref(false)
const createForm = ref({
  knowledge_name: '',
  knowledge_desc: ''
})
const createLoading = ref(false)

// 编辑知识库对话框
const editDialogVisible = ref(false)
const editForm = ref({
  knowledge_id: '',
  knowledge_name: '',
  knowledge_desc: ''
})
const editLoading = ref(false)
const currentEditKnowledge = ref<KnowledgeListType | null>(null)

// 获取知识库列表
const fetchKnowledges = async () => {
  loading.value = true
  try {
         const response = await getKnowledgeListAPI()
     if (response.data.status_code === 200 && response.data.data) {
       knowledges.value = response.data.data.map((item: KnowledgeResponse) => ({
         id: item.id,
         name: item.name,
         description: item.description,
         user_id: item.user_id,
         create_time: item.create_time,
         update_time: item.update_time,
         count: item.count,
         file_size: item.file_size
       }))
     } else {
      ElMessage.error('获取知识库列表失败: ' + response.data.status_message)
    }
  } catch (error) {
    console.error('获取知识库列表失败:', error)
    ElMessage.error('获取知识库列表失败')
  } finally {
    loading.value = false
  }
}

// 删除知识库
const handleDelete = async (knowledge: KnowledgeListType) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除知识库"${knowledge.name}"吗？删除后无法恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    const deleteData: KnowledgeDeleteRequest = {
      knowledge_id: knowledge.id
    }
    
    const response = await deleteKnowledgeAPI(deleteData)
    if (response.data.status_code === 200) {
      ElMessage.success('删除成功')
      await fetchKnowledges() // 刷新列表
    } else {
      ElMessage.error('删除失败: ' + response.data.status_message)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除知识库失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleDateString('zh-CN')
}

// 跳转到文件管理页面
const goToFileManagement = (knowledge: KnowledgeListType) => {
  router.push({
    name: 'knowledge-file',
    params: { knowledgeId: knowledge.id },
    query: { name: knowledge.name }
  })
}

// 打开创建知识库对话框
const openCreateDialog = () => {
  createDialogVisible.value = true
  resetCreateForm()
}

// 重置创建表单
const resetCreateForm = () => {
  createForm.value = {
    knowledge_name: '',
    knowledge_desc: ''
  }
}

// 创建知识库
const handleCreate = async () => {
  const name = createForm.value.knowledge_name.trim()
  const desc = createForm.value.knowledge_desc.trim()
  
  if (!name) {
    ElMessage.error('请输入知识库名称')
    return
  }
  
  if (name.length < 2 || name.length > 10) {
    ElMessage.error('知识库名称长度必须在2-10个字符之间')
    return
  }
  
  if (desc && (desc.length < 10 || desc.length > 200)) {
    ElMessage.error('知识库描述长度必须在10-200个字符之间')
    return
  }
  
  createLoading.value = true
  try {
    const response = await createKnowledgeAPI(createForm.value)
    if (response.data.status_code === 200) {
      ElMessage.success('创建成功')
      createDialogVisible.value = false
      await fetchKnowledges() // 刷新列表
    } else {
      ElMessage.error('创建失败: ' + response.data.status_message)
    }
  } catch (error) {
    console.error('创建知识库失败:', error)
    ElMessage.error('创建失败')
  } finally {
    createLoading.value = false
  }
}

// 打开编辑知识库对话框
const openEditDialog = (knowledge: KnowledgeListType) => {
  currentEditKnowledge.value = knowledge
  editForm.value = {
    knowledge_id: knowledge.id,
    knowledge_name: knowledge.name,
    knowledge_desc: knowledge.description || ''
  }
  editDialogVisible.value = true
}

// 重置编辑表单
const resetEditForm = () => {
  editForm.value = {
    knowledge_id: '',
    knowledge_name: '',
    knowledge_desc: ''
  }
  currentEditKnowledge.value = null
}

// 编辑知识库
const handleEdit = async () => {
  const name = editForm.value.knowledge_name.trim()
  const desc = editForm.value.knowledge_desc.trim()
  
  if (!name) {
    ElMessage.error('请输入知识库名称')
    return
  }
  
  if (name.length < 2 || name.length > 10) {
    ElMessage.error('知识库名称长度必须在2-10个字符之间')
    return
  }
  
  if (desc && (desc.length < 10 || desc.length > 200)) {
    ElMessage.error('知识库描述长度必须在10-200个字符之间')
    return
  }
  
  editLoading.value = true
  try {
    const updateData: KnowledgeUpdateRequest = {
      knowledge_id: editForm.value.knowledge_id,
      knowledge_name: editForm.value.knowledge_name,
      knowledge_desc: editForm.value.knowledge_desc
    }
    
    const response = await updateKnowledgeAPI(updateData)
    if (response.data.status_code === 200) {
      ElMessage.success('更新成功')
      editDialogVisible.value = false
      await fetchKnowledges() // 刷新列表
    } else {
      ElMessage.error('更新失败: ' + response.data.status_message)
    }
  } catch (error) {
    console.error('更新知识库失败:', error)
    ElMessage.error('更新失败')
  } finally {
    editLoading.value = false
  }
}



onMounted(() => {
  fetchKnowledges()
})
</script>

<template>
  <div class="knowledge-page">
    <div class="page-header">
      <h2>
        <img :src="knowledgeIcon" class="knowledge-icon" alt="Knowledge" />
        知识库管理
      </h2>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">
        创建知识库
      </el-button>
    </div>

    <div class="knowledge-list" v-loading="loading">
      <div class="knowledge-grid">
        <div 
          v-for="knowledge in knowledges" 
          :key="knowledge.id" 
          class="knowledge-card"
        >
                        <h3 class="knowledge-name" :title="knowledge.name">
                <span class="name-icon">
                  <svg viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" width="20" height="20">
                    <path d="M728.18789136 299.43681581v-115.21390618c0-70.94069728-58.12476839-128.93601185-128.93601186-128.93601185H161.05067457c-70.94069728 0-128.93601185 58.12476839-128.93601185 128.93601185v274.31265976l0.51781531-127.25311211" fill="#73c7ff"></path>
                    <path d="M72.89261827 458.6650232l-81.68536494-0.12945381V184.22290963c0-93.59511703 76.24830419-169.97287506 169.97287506-169.97287506h438.07175111c93.59511703 0 169.97287506 76.24830419 169.97287507 169.97287506v115.21390618h-81.68536494v-115.21390618c0-48.54518518-39.61287111-88.1580563-88.1580563-88.1580563H161.05067457c-48.54518518 0-88.1580563 39.61287111-88.1580563 88.1580563v147.18900148h0.51781531l-0.51781531 127.25311209z m0 0" fill="#4880FF"></path>
                    <path d="M874.47071605 1003.53618173H160.79176691c-44.92047803 0-89.32314075-21.23042765-121.94550518-58.6425837-30.5511032-34.95253333-48.02736987-80.26137283-48.02736988-124.66403556V464.74935309c0-93.59511703 76.24830419-169.84342124 169.97287506-169.84342124H874.47071605c93.59511703 0 169.97287506 76.24830419 169.97287506 169.84342124v355.48020938c0 44.40266272-17.47626667 89.71150222-48.02736987 124.66403556-32.62236445 37.41215605-77.02502717 58.6425837-121.94550519 58.6425837zM160.79176691 376.5912968c-48.54518518 0-88.1580563 39.61287111-88.1580563 88.15805629v355.48020938c0 24.46677333 10.48576 51.0048079 27.83257286 70.94069728 10.09739852 11.52139061 31.19837235 30.68055703 60.32548344 30.68055705H874.47071605c29.12711111 0 50.35753876-19.15916642 60.32548345-30.68055705 17.34681283-19.93588939 27.83257283-46.47392395 27.83257285-70.94069728V464.74935309c0-48.54518518-39.61287111-88.1580563-88.1580563-88.15805629H160.79176691z m0 0" fill="#4880FF"></path>
                  </svg>
                </span>
                <span class="name-text">{{ knowledge.name }}</span>
              </h3>
          
          <div class="knowledge-info">
            <div class="knowledge-stats">
              <div class="stat-item files">
                <div class="stat-icon">
                  <el-icon><Document /></el-icon>
                </div>
                <div class="stat-content">
                  <span class="stat-label">文件数量</span>
                  <span class="stat-value">{{ knowledge.count }}</span>
                </div>
              </div>
              <div class="stat-item size">
                <div class="stat-icon">
                  📁
                </div>
                <div class="stat-content">
                  <span class="stat-label">存储大小</span>
                  <span class="stat-value">{{ knowledge.file_size }}</span>
                </div>
              </div>
            </div>
            
            <div class="knowledge-time">
              <div class="time-item created">
                <span class="time-icon">🎯</span>
                <div class="time-content">
                  <span class="time-label">创建时间</span>
                  <span class="time-value">{{ formatTime(knowledge.create_time) }}</span>
                </div>
              </div>
              <div class="time-item updated">
                <span class="time-icon">🔄</span>
                <div class="time-content">
                  <span class="time-label">更新时间</span>
                  <span class="time-value">{{ formatTime(knowledge.update_time) }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="knowledge-actions">
            <button class="action-btn primary" @click="goToFileManagement(knowledge)">
              <span class="btn-icon">📁</span>
              <span class="btn-text">管理文件</span>
            </button>
            <button class="action-btn secondary" @click="openEditDialog(knowledge)">
              <span class="btn-icon">✏️</span>
              <span class="btn-text">编辑</span>
            </button>
            <button class="action-btn danger" @click="handleDelete(knowledge)">
              <span class="btn-icon">🗑️</span>
              <span class="btn-text">删除</span>
            </button>
          </div>
        </div>
      </div>
      
      <div v-if="knowledges.length === 0 && !loading" class="empty-state">
        <div class="empty-icon">
          <i class="empty-icon-symbol">📚</i>
        </div>
        <h3>暂无知识库</h3>
        <p>您可以创建知识库来存储和管理您的文档资料</p>
        <el-button type="primary" @click="createDialogVisible = true" class="create-btn">
          创建知识库
        </el-button>
      </div>
    </div>

    <!-- 创建知识库对话框 -->
    <div v-if="createDialogVisible" class="dialog-overlay">
      <div class="dialog-container">
        <div class="dialog-header">
          <h3>创建知识库</h3>
          <button class="close-btn" @click="createDialogVisible = false">×</button>
        </div>
        
        <div class="dialog-body">
          <div class="form-item">
            <label>知识库名称 <span style="color: red;">*</span></label>
            <div class="input-with-count">
              <input 
                v-model="createForm.knowledge_name"
                type="text" 
                placeholder="请输入知识库名称（2-10个字符）"
                maxlength="10"
                :class="{ 'error': createForm.knowledge_name.length > 0 && (createForm.knowledge_name.length < 2 || createForm.knowledge_name.length > 10) }"
              />
              <span class="char-count" :class="{ 'error': createForm.knowledge_name.length < 2 || createForm.knowledge_name.length > 10 }">
                {{ createForm.knowledge_name.length }}/10
              </span>
            </div>
          </div>
          
          <div class="form-item">
            <label>知识库描述 <span style="color: #909399; font-size: 12px;">(可选，10-200字符)</span></label>
            <div class="textarea-with-count">
              <textarea 
                v-model="createForm.knowledge_desc"
                placeholder="请输入知识库描述（可选，10-200字符）"
                rows="4"
                maxlength="200"
                :class="{ 'error': createForm.knowledge_desc.length > 0 && (createForm.knowledge_desc.length < 10 || createForm.knowledge_desc.length > 200) }"
              ></textarea>
              <span class="char-count" :class="{ 'error': createForm.knowledge_desc.length > 0 && (createForm.knowledge_desc.length < 10 || createForm.knowledge_desc.length > 200) }">
                {{ createForm.knowledge_desc.length }}/200
              </span>
            </div>
          </div>
        </div>
        
        <div class="dialog-footer">
          <button @click="createDialogVisible = false">取消</button>
          <button 
            class="primary-btn" 
            :disabled="createLoading" 
            @click="handleCreate"
          >
            {{ createLoading ? '创建中...' : '确定' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 编辑知识库对话框 -->
    <div v-if="editDialogVisible" class="dialog-overlay">
      <div class="dialog-container">
        <div class="dialog-header">
          <h3>编辑知识库</h3>
          <button class="close-btn" @click="editDialogVisible = false; resetEditForm()">×</button>
        </div>
        
        <div class="dialog-body">
          <div class="form-item">
            <label>知识库名称 <span style="color: red;">*</span></label>
            <div class="input-with-count">
              <input 
                v-model="editForm.knowledge_name"
                type="text" 
                placeholder="请输入知识库名称（2-10个字符）"
                maxlength="10"
                :class="{ 'error': editForm.knowledge_name.length > 0 && (editForm.knowledge_name.length < 2 || editForm.knowledge_name.length > 10) }"
              />
              <span class="char-count" :class="{ 'error': editForm.knowledge_name.length < 2 || editForm.knowledge_name.length > 10 }">
                {{ editForm.knowledge_name.length }}/10
              </span>
            </div>
          </div>
          
          <div class="form-item">
            <label>知识库描述 <span style="color: #909399; font-size: 12px;">(可选，10-200字符)</span></label>
            <div class="textarea-with-count">
              <textarea 
                v-model="editForm.knowledge_desc"
                placeholder="请输入知识库描述（可选，10-200字符）"
                rows="4"
                maxlength="200"
                :class="{ 'error': editForm.knowledge_desc.length > 0 && (editForm.knowledge_desc.length < 10 || editForm.knowledge_desc.length > 200) }"
              ></textarea>
              <span class="char-count" :class="{ 'error': editForm.knowledge_desc.length > 0 && (editForm.knowledge_desc.length < 10 || editForm.knowledge_desc.length > 200) }">
                {{ editForm.knowledge_desc.length }}/200
              </span>
            </div>
          </div>
        </div>
        
        <div class="dialog-footer">
          <button @click="editDialogVisible = false; resetEditForm()">取消</button>
          <button 
            class="primary-btn" 
            :disabled="editLoading" 
            @click="handleEdit"
          >
            {{ editLoading ? '更新中...' : '确定' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.knowledge-page {
  padding: 16px;
  height: 100%;
  min-height: calc(100vh - 60px);
  background-color: #f5f7fa;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    background: linear-gradient(to right, #ffffff, #f8fafc);
    padding: 16px 20px;
    border-radius: 12px;
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
      background: linear-gradient(90deg, #4880FF, #73c7ff, #67c23a);
    }

    h2 {
      margin: 0;
      font-size: 26px;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 12px;
      background: linear-gradient(90deg, #4880FF, #73c7ff); // 与knowledge.svg图标颜色匹配
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      
      .knowledge-icon {
        width: 32px;
        height: 32px;
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
  
  .knowledge-list {
    height: calc(100% - 60px);
    
    .knowledge-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 16px;
      
      .knowledge-card {
        background: white;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        border: 1px solid #e1e5e9;
        transition: all 0.3s ease;
        
        &:hover {
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
          transform: translateY(-2px);
        }
        
        .knowledge-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;
          
          .knowledge-icon {
            color: #4f81ff;
          }
        }
        
        .knowledge-info {
          .knowledge-name {
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
            margin: 0 0 8px 0;
          }
          

          
          .knowledge-stats {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            
            .stat-item {
              font-size: 14px; /* 从12px增加到14px */
              font-weight: 500; /* 增加字重 */
              color: #888;
              display: flex;
              align-items: center;
              gap: 4px;
            }
          }
          
          .knowledge-time {
            font-size: 13px; /* 从12px增加到13px */
            font-weight: 500; /* 增加字重 */
            color: #999;
            line-height: 1.4;
          }
        }
        
        .knowledge-actions {
          margin-top: 12px;
          display: flex;
          gap: 8px;
          justify-content: flex-end;
        }
        
        .action-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 12px;
          border: 1px solid #e1e5e9;
          border-radius: 8px;
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
          background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
          color: #606266;
          min-width: 70px;
          justify-content: center;
        }
        
        .action-btn:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        
        .action-btn.primary {
          background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
          color: white;
          border-color: #409eff;
        }
        
        .action-btn.primary:hover {
          background: linear-gradient(135deg, #66b1ff 0%, #85c1ff 100%);
          box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
        }
        
        .action-btn.secondary {
          background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
          color: #606266;
          border-color: #e1e5e9;
        }
        
        .action-btn.secondary:hover {
          background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
          border-color: #409eff;
          color: #409eff;
        }
        
        .action-btn.danger {
          background: linear-gradient(135deg, #fef0f0 0%, #fde2e2 100%);
          color: #f56c6c;
          border-color: #fbc4c4;
        }
        
        .action-btn.danger:hover {
          background: linear-gradient(135deg, #fde2e2 0%, #fbbfbf 100%);
          border-color: #f56c6c;
          box-shadow: 0 4px 12px rgba(245, 108, 108, 0.2);
        }
        
        .action-btn .btn-icon {
          font-size: 14px;
        }
        
        .action-btn .btn-text {
          font-size: 13px;
          font-weight: 500;
        }
      }
    }
    
    .empty-state {
      text-align: center;
      padding: 60px 20px;
      color: #999;
      
      p {
        margin-top: 20px;
        font-size: 16px;
      }
    }
  }
}

/* 原生对话框样式 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.dialog-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  width: 500px;
  max-width: 90vw;
  max-height: 80vh;
  overflow: hidden;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 20px 0 20px;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 20px;
  
  h3 {
    margin: 0;
    font-size: 18px;
    color: #303133;
  }
  
  .close-btn {
    background: none;
    border: none;
    font-size: 24px;
    color: #909399;
    cursor: pointer;
    padding: 0;
    width: 24px;
    height: 24px;
    
    &:hover {
      color: #f56c6c;
    }
  }
}

.dialog-body {
  padding: 0 20px 20px 20px;
  
  .form-item {
    margin-bottom: 20px;
    
    label {
      display: block;
      margin-bottom: 8px;
      font-size: 14px;
      color: #606266;
      font-weight: 500;
    }
    
    input, textarea {
      width: 100%;
      padding: 12px;
      border: 1px solid #dcdfe6;
      border-radius: 4px;
      font-size: 14px;
      box-sizing: border-box;
      transition: border-color 0.2s;
      
      &:focus {
        outline: none;
        border-color: #409eff;
      }
      
      &::placeholder {
        color: #c0c4cc;
      }
    }
    
    textarea {
      resize: vertical;
      font-family: inherit;
    }
  }
}

.dialog-footer {
  padding: 20px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  
  button {
    padding: 8px 20px;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      opacity: 0.8;
    }
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }
  
  .primary-btn {
    background: #409eff;
    color: white;
    border-color: #409eff;
    
    &:hover:not(:disabled) {
      background: #66b1ff;
      border-color: #66b1ff;
    }
  }
}

/* 输入框字符计数器样式 */
.input-with-count, .textarea-with-count {
  position: relative;
  
  input.error, textarea.error {
    border-color: #f56c6c !important;
    box-shadow: 0 0 0 2px rgba(245, 108, 108, 0.2);
  }
  
  .char-count {
    position: absolute;
    font-size: 11px;
    color: #909399;
    background: rgba(255, 255, 255, 0.9);
    padding: 2px 4px;
    border-radius: 4px;
    font-weight: 500;
    
    &.error {
      color: #f56c6c;
      background: rgba(245, 108, 108, 0.1);
    }
  }
}

.input-with-count .char-count {
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
}

.textarea-with-count .char-count {
  right: 8px;
  bottom: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}





.knowledge-grid .knowledge-card .knowledge-name {
  margin: 0 0 12px 0;
  padding: 14px 18px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  color: #303133;
  border-radius: 8px;
  font-size: 18px;
  font-weight: 600;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  letter-spacing: -0.01em;
  line-height: 1.3;
  border: 1px solid #e1e5e9;
  cursor: help;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
  box-sizing: border-box;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.knowledge-grid .knowledge-card .knowledge-name:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
}

.knowledge-grid .knowledge-card .knowledge-name .name-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.knowledge-grid .knowledge-card .knowledge-name .name-icon svg {
  width: 26px;
  height: 26px;
  fill: #409eff;
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-name .name-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}



/* 美化知识库统计信息样式 */
.knowledge-grid .knowledge-card .knowledge-info .knowledge-stats {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-stats .stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 10px;
  border: 1px solid #e1e5e9;
  transition: all 0.3s ease;
  flex: 1;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-stats .stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
  background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-stats .stat-item.files {
  border-left: 4px solid #409eff;
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-stats .stat-item.size {
  border-left: 4px solid #67c23a;
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-stats .stat-icon {
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(64, 158, 255, 0.15);
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-stats .stat-icon .el-icon {
  color: #409eff;
  font-size: 16px;
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-stats .stat-content {
  display: flex;
  flex-direction: column;
  gap: 1px;
  flex: 1;
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-stats .stat-label {
  font-size: 10px;
  color: #909399;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 1px;
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-stats .stat-value {
  font-size: 14px;
  font-weight: 700;
  color: #303133;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* 美化时间信息样式 */
.knowledge-grid .knowledge-card .knowledge-info .knowledge-time {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-time .time-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: linear-gradient(135deg, #fafbfc 0%, #f1f3f4 100%);
  border-radius: 8px;
  border: 1px solid #e8eaec;
  transition: all 0.2s ease;
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-time .time-item:hover {
  background: linear-gradient(135deg, #f0f2f5 0%, #e6e8eb 100%);
  transform: scale(1.02);
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-time .time-item.created {
  border-left: 3px solid #e6a23c;
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-time .time-item.updated {
  border-left: 3px solid #67c23a;
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-time .time-icon {
  font-size: 16px;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1));
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-time .time-content {
  display: flex;
  flex-direction: column;
  gap: 1px;
  flex: 1;
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-time .time-label {
  font-size: 10px;
  color: #909399;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.knowledge-grid .knowledge-card .knowledge-info .knowledge-time .time-value {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  font-family: 'SF Mono', Monaco, Consolas, 'Liberation Mono', monospace;
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.05);
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