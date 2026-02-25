<script setup lang="ts">
import { ref, onMounted, computed, nextTick, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete, Refresh, FolderOpened, Document, Edit, View, CloseBold, Files, Clock } from '@element-plus/icons-vue'
import skillIcon from '../../assets/skill.svg'
import * as monaco from 'monaco-editor'
import { 
  getAgentSkillsAPI, 
  createAgentSkillAPI, 
  deleteAgentSkillAPI,
  updateAgentSkillFileAPI,
  addAgentSkillFileAPI,
  deleteAgentSkillFileAPI,
  type AgentSkill,
  type AgentSkillFile,
  type AgentSkillFolder
} from '../../apis/agent-skill'

// Monaco 编辑器实例
let monacoEditor: monaco.editor.IStandaloneCodeEditor | null = null

// 响应式数据
const skills = ref<AgentSkill[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const currentSkill = ref<AgentSkill | null>(null)
const selectedFile = ref<AgentSkillFile | null>(null)
const fileContent = ref('')
const editMode = ref(false)
const showAddFileDialog = ref(false)
const savingFile = ref(false)

// 手写确认弹窗（替代 ElMessageBox / window.confirm）
type ConfirmDialogOptions = {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  variant?: 'default' | 'danger'
}

const confirmDialog = reactive({
  visible: false,
  title: '确认',
  message: '',
  confirmText: '确定',
  cancelText: '取消',
  variant: 'default' as 'default' | 'danger',
  resolve: null as null | ((ok: boolean) => void),
})

const openConfirmDialog = (options: ConfirmDialogOptions) => {
  confirmDialog.title = options.title ?? '确认'
  confirmDialog.message = options.message
  confirmDialog.confirmText = options.confirmText ?? '确定'
  confirmDialog.cancelText = options.cancelText ?? '取消'
  confirmDialog.variant = options.variant ?? 'default'
  confirmDialog.visible = true

  return new Promise<boolean>((resolve) => {
    confirmDialog.resolve = resolve
  })
}

const closeConfirmDialog = (ok: boolean) => {
  confirmDialog.visible = false
  const r = confirmDialog.resolve
  confirmDialog.resolve = null
  r?.(ok)
}
// 表单数据
const createForm = ref({
  name: '',
  description: ''
})

const addFileForm = ref({
  path: '',
  name: ''
})

// 表单验证规则
const createFormRules = {
  name: [
    { required: true, message: '请输入 Skill 名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入 Skill 描述', trigger: 'blur' },
    { max: 500, message: '描述不能超过 500 个字符', trigger: 'blur' }
  ]
}

// 获取文件数量
const getFileCount = (skill: AgentSkill) => {
  if (!skill.folder?.folder) return 0
  let count = 0
  const countFiles = (items: any[]) => {
    items.forEach(item => {
      if (item.type === 'file') count++
      if (item.folder) countFiles(item.folder)
    })
  }
  countFiles(skill.folder.folder)
  return count
}

// 获取 Skill 列表
const fetchSkills = async () => {
  loading.value = true
  try {
    const response = await getAgentSkillsAPI()
    if (response.data.status_code === 200) {
      skills.value = response.data.data || []
    } else {
      ElMessage.error(response.data.status_message || '获取 Skill 列表失败')
    }
  } catch (error) {
    console.error('获取 Skill 列表失败:', error)
    ElMessage.error('获取 Skill 列表失败')
  } finally {
    loading.value = false
  }
}

// 创建 Skill
const handleCreateSkill = async () => {
  if (!createForm.value.name || !createForm.value.description) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  try {
    const response = await createAgentSkillAPI(createForm.value)
    if (response.data.status_code === 200) {
      ElMessage.success('Skill 创建成功')
      showCreateDialog.value = false
      resetCreateForm()
      fetchSkills()
    } else {
      ElMessage.error(response.data.status_message || '创建 Skill 失败')
    }
  } catch (error) {
    console.error('创建 Skill 失败:', error)
    ElMessage.error('创建 Skill 失败')
  }
}

// 删除 Skill
const handleDeleteSkill = async (skill: AgentSkill, event?: Event) => {
  event?.stopPropagation()
  const confirmed = await openConfirmDialog({
    title: '确认删除',
    message: `确定要删除 Skill "${skill.name}" 吗？此操作不可恢复。`,
    confirmText: '确定删除',
    cancelText: '取消',
    variant: 'danger',
  })
  if (!confirmed) return

  try {
    const response = await deleteAgentSkillAPI({ agent_skill_id: skill.id })
    if (response.data.status_code === 200) {
      ElMessage.success('Skill 删除成功')
      fetchSkills()
    } else {
      ElMessage.error(response.data.status_message || '删除 Skill 失败')
    }
  } catch (error) {
    console.error('删除 Skill 失败:', error)
    ElMessage.error('删除 Skill 失败')
  }
}

// 打开详情弹窗
const openDetailDialog = (skill: AgentSkill) => {
  currentSkill.value = skill
  selectedFile.value = null
  fileContent.value = ''
  editMode.value = false
  showDetailDialog.value = true
  document.body.style.overflow = 'hidden'
}

// 关闭详情弹窗
const closeDetailDialog = () => {
  showDetailDialog.value = false
  currentSkill.value = null
  selectedFile.value = null
  fileContent.value = ''
  editMode.value = false
  document.body.style.overflow = 'auto'
  
  // 销毁编辑器
  if (monacoEditor) {
    monacoEditor.dispose()
    monacoEditor = null
  }
}

// 初始化 Monaco 编辑器
const initMonacoEditor = () => {
  nextTick(() => {
    const container = document.getElementById('skill-monaco-editor')
    if (container && !monacoEditor) {
      monacoEditor = monaco.editor.create(container, {
        value: fileContent.value,
        language: getFileLanguage(selectedFile.value?.name || ''),
        theme: 'vs',
        automaticLayout: true,
        minimap: { enabled: false },
        lineNumbers: 'on',
        roundedSelection: true,
        scrollBeyondLastLine: false,
        fontSize: 14,
        tabSize: 2,
        renderLineHighlight: 'all',
        padding: { top: 16, bottom: 16 },
        scrollbar: {
          vertical: 'auto',
          horizontal: 'auto',
        }
      })
    } else if (monacoEditor) {
      monacoEditor.setValue(fileContent.value)
      monaco.editor.setModelLanguage(
        monacoEditor.getModel()!,
        getFileLanguage(selectedFile.value?.name || '')
      )
    }
  })
}

// 获取文件语言
const getFileLanguage = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  const languageMap: Record<string, string> = {
    'py': 'python',
    'js': 'javascript',
    'ts': 'typescript',
    'json': 'json',
    'md': 'markdown',
    'yaml': 'yaml',
    'yml': 'yaml',
    'html': 'html',
    'css': 'css',
    'sh': 'shell',
    'bash': 'shell',
    'txt': 'plaintext'
  }
  return languageMap[ext || ''] || 'plaintext'
}

// 判断是否可以删除文件（只有 scripts 和 reference 目录下的文件可以删除）
const canDeleteFile = (file: AgentSkillFile, parentPath: string) => {
  // 根目录的文件（如 SKILL.md）不能删除
  if (parentPath === currentSkill.value?.folder?.path) {
    return false
  }
  // scripts 和 reference 目录下的文件可以删除
  return parentPath.includes('/scripts') || parentPath.includes('/reference')
}

// 判断文件夹是否可以添加文件（只有 scripts 和 reference 可以）
const canAddToFolder = (folderName: string) => {
  return folderName === 'scripts' || folderName === 'reference'
}

// 获取可添加文件的目录列表
const getAddableFolders = computed(() => {
  if (!currentSkill.value?.folder?.folder) return []
  return currentSkill.value.folder.folder.filter(
    item => item.type === 'folder' && canAddToFolder(item.name)
  )
})

// 选择文件
const selectFile = (file: AgentSkillFile) => {
  selectedFile.value = file
  fileContent.value = file.content
  editMode.value = false
  
  // 销毁旧编辑器
  if (monacoEditor) {
    monacoEditor.dispose()
    monacoEditor = null
  }
}

// 进入编辑模式
const enterEditMode = () => {
  editMode.value = true
  nextTick(() => {
    initMonacoEditor()
  })
}

// 取消编辑
const cancelEdit = () => {
  editMode.value = false
  fileContent.value = selectedFile.value?.content || ''
  if (monacoEditor) {
    monacoEditor.dispose()
    monacoEditor = null
  }
}

// 保存文件内容
const saveFileContent = async () => {
  if (!currentSkill.value || !selectedFile.value) return
  
  savingFile.value = true
  try {
    const content = monacoEditor ? monacoEditor.getValue() : fileContent.value
    const response = await updateAgentSkillFileAPI({
      agent_skill_id: currentSkill.value.id,
      path: selectedFile.value.path,
      content: content
    })
    
    if (response.data.status_code === 200) {
      ElMessage.success('文件保存成功')
      editMode.value = false
      fileContent.value = content
      if (selectedFile.value) {
        selectedFile.value.content = content
      }
      currentSkill.value = response.data.data
      fetchSkills()
      
      if (monacoEditor) {
        monacoEditor.dispose()
        monacoEditor = null
      }
    } else {
      ElMessage.error(response.data.status_message || '保存失败')
    }
  } catch (error) {
    console.error('保存文件失败:', error)
    ElMessage.error('保存文件失败')
  } finally {
    savingFile.value = false
  }
}

// 关闭添加文件对话框
const closeAddFileDialog = () => {
  showAddFileDialog.value = false
  addFileForm.value = { path: '', name: '' }
}

// 添加文件
const addingFile = ref(false)
const handleAddFile = async () => {
  if (!currentSkill.value) {
    ElMessage.warning('请先选择一个 Skill')
    return
  }
  
  if (!addFileForm.value.path) {
    ElMessage.warning('请选择目标目录')
    return
  }
  
  if (!addFileForm.value.name) {
    ElMessage.warning('请输入文件名称')
    return
  }
  
  addingFile.value = true
  try {
    const response = await addAgentSkillFileAPI({
      agent_skill_id: currentSkill.value.id,
      path: addFileForm.value.path,
      name: addFileForm.value.name
    })

    if (response.data.status_code === 200) {
      ElMessage.success('文件添加成功')
      closeAddFileDialog()
      currentSkill.value = response.data.data
      fetchSkills()
    } else {
      ElMessage.error(response.data.status_message || '添加文件失败')
    }
  } catch (error: any) {
    console.error('添加文件失败:', error)
    ElMessage.error(error?.response?.data?.status_message || error?.message || '添加文件失败')
  } finally {
    addingFile.value = false
  }
}

// 删除文件
const handleDeleteFile = async (file: AgentSkillFile, parentPath: string) => {
  if (!currentSkill.value) return
  const confirmed = await openConfirmDialog({
    title: '确认删除',
    message: `确定要删除文件 "${file.name}" 吗？`,
    confirmText: '确定删除',
    cancelText: '取消',
    variant: 'danger',
  })
  if (!confirmed) return
  
  try {
    const response = await deleteAgentSkillFileAPI({
      agent_skill_id: currentSkill.value.id,
      path: parentPath,
      name: file.name
    })
    
    if (response.data.status_code === 200) {
      ElMessage.success('文件删除成功')
      currentSkill.value = response.data.data
      if (selectedFile.value?.path === file.path) {
        selectedFile.value = null
        fileContent.value = ''
      }
      fetchSkills()
    } else {
      ElMessage.error(response.data.status_message || '删除文件失败')
    }
  } catch (error) {
    console.error('删除文件失败:', error)
    ElMessage.error('删除文件失败')
  }
}

// 重置创建表单
const resetCreateForm = () => {
  createForm.value = {
    name: '',
    description: ''
  }
}

// 刷新数据
const handleRefresh = () => {
  fetchSkills()
}

// 格式化时间
const formatTime = (timeStr?: string) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

// 格式化相对时间
const formatRelativeTime = (timeStr?: string) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  if (days < 30) return `${Math.floor(days / 7)}周前`
  return formatTime(timeStr)
}

onMounted(() => {
  fetchSkills()
})
</script>

<template>
  <div class="skill-page">
    <!-- 页面头部 - 增强设计 -->
    <div class="page-header">
      <div class="header-title">
        <img :src="skillIcon" alt="Skill" class="title-icon" />
        <h2>Agent Skill</h2>
      </div>
      <div class="header-actions">
        <el-button 
          :icon="Refresh" 
          @click="handleRefresh" 
          :loading="loading"
          class="refresh-btn"
        >
          刷新
        </el-button>
        <el-button 
          type="primary" 
          :icon="Plus" 
          @click="showCreateDialog = true"
          class="create-btn"
        >
          创建 Skill
        </el-button>
      </div>
    </div>

    <!-- Skill 列表 -->
    <div class="skill-container" v-loading="loading">
      <!-- 列表头部 -->
      <div class="list-header" v-if="skills.length > 0">
        <div class="col-name">名称</div>
        <div class="col-desc">描述</div>
        <div class="col-files">文件数</div>
        <div class="col-time">创建时间</div>
        <div class="col-actions">操作</div>
      </div>
      
      <!-- 列表内容 -->
      <div class="skill-list" v-if="skills.length > 0">
        <div 
          v-for="(skill, index) in skills" 
          :key="skill.id" 
          class="skill-row"
          @click="openDetailDialog(skill)"
        >
          <div class="col-name">
            <div class="skill-info">
              <div class="skill-avatar">
                <img :src="skillIcon" alt="Skill" />
              </div>
              <span class="skill-name">{{ skill.name }}</span>
            </div>
          </div>
          <div class="col-desc">
            <span class="skill-desc">{{ skill.description }}</span>
          </div>
          <div class="col-files">
            <span class="file-badge">
              <el-icon><Document /></el-icon>
              {{ getFileCount(skill) }}
            </span>
          </div>
          <div class="col-time">
            <span class="time-text">{{ formatRelativeTime(skill.create_time) }}</span>
          </div>
          <div class="col-actions" @click.stop>
            <el-tooltip content="查看详情" placement="top">
              <button class="action-btn view-btn" @click="openDetailDialog(skill)">
                <el-icon><View /></el-icon>
              </button>
            </el-tooltip>
            <el-tooltip content="删除" placement="top">
              <button class="action-btn delete-btn" @click="handleDeleteSkill(skill, $event)">
                <el-icon><Delete /></el-icon>
              </button>
            </el-tooltip>
          </div>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-if="skills.length === 0 && !loading" class="empty-state">
        <div class="empty-visual">
          <div class="empty-icon-wrapper">
            <img :src="skillIcon" alt="No Skills" class="empty-icon" />
          </div>
        </div>
        <div class="empty-content">
          <h3>还没有创建任何 Skill</h3>
          <p>Agent Skill 可以让智能体拥有更专业的能力，开始创建你的第一个 Skill 吧！</p>
          <el-button 
            type="primary"
            :icon="Plus"
            @click="showCreateDialog = true"
            class="empty-btn"
          >
            创建第一个 Skill
          </el-button>
        </div>
      </div>
    </div>

    <!-- 创建 Skill 对话框 - 增强设计 -->
    <Teleport to="body">
      <div v-if="showCreateDialog" class="modal-overlay create-modal" @click.self="showCreateDialog = false">
        <div class="modal-dialog create-dialog">
          <div class="dialog-header">
            <div class="dialog-icon">
              <img :src="skillIcon" alt="Create Skill" />
            </div>
            <div class="dialog-title-wrapper">
              <h3>创建新 Skill</h3>
              <p>为智能体添加一项新的专业技能</p>
            </div>
            <button class="close-btn" @click="showCreateDialog = false">
              <el-icon><CloseBold /></el-icon>
            </button>
          </div>
          
          <div class="dialog-body">
            <div class="form-tip">
              <div class="tip-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" stroke="#1B7CE4" stroke-width="2"/>
                  <path d="M12 16v-4M12 8h.01" stroke="#1B7CE4" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <p>Skill 包含一组预定义的文件和脚本，用于赋予智能体特定的专业能力</p>
            </div>
            
            <el-form
              :model="createForm"
              :rules="createFormRules"
              label-position="top"
              class="create-form"
            >
              <el-form-item label="Skill 名称" prop="name">
                <el-input 
                  v-model="createForm.name" 
                  placeholder="例如：数据分析专家、代码审查助手"
                  maxlength="50"
                  show-word-limit
                  size="large"
                />
              </el-form-item>
              
              <el-form-item label="Skill 描述" prop="description">
                <el-input 
                  v-model="createForm.description" 
                  type="textarea"
                  :rows="4"
                  placeholder="详细描述这个 Skill 的功能、适用场景和特点..."
                  maxlength="500"
                  show-word-limit
                />
              </el-form-item>
            </el-form>
          </div>
          
          <div class="dialog-footer">
            <el-button @click="showCreateDialog = false" size="large">取消</el-button>
            <el-button type="primary" @click="handleCreateSkill" size="large">
              <el-icon><Plus /></el-icon>
              创建 Skill
            </el-button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Skill 详情对话框 - 代码编辑器风格 -->
    <Teleport to="body">
      <div v-if="showDetailDialog" class="modal-overlay detail-modal" @click.self="closeDetailDialog">
        <div class="modal-dialog detail-dialog">
          <!-- IDE 风格头部 -->
          <div class="ide-header">
            <div class="ide-tabs">
              <div class="ide-tab active">
                <img :src="skillIcon" class="tab-icon" alt="Skill" />
                <span class="tab-name">{{ currentSkill?.name }}</span>
              </div>
            </div>
            <div class="ide-actions">
              <button class="ide-btn" @click="closeDetailDialog">
                <el-icon><CloseBold /></el-icon>
              </button>
            </div>
          </div>
          
          <!-- IDE 内容区 -->
          <div class="ide-body">
            <!-- 侧边栏 - 文件资源管理器 -->
            <div class="ide-sidebar">
              <div class="sidebar-header">
                <span class="sidebar-title">资源管理器</span>
                <el-tooltip content="只能在 scripts 或 reference 目录下添加文件" placement="bottom">
                  <span class="sidebar-hint">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                      <path d="M12 16v-4M12 8h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                  </span>
                </el-tooltip>
              </div>
              
              <div class="file-explorer">
                <template v-if="currentSkill?.folder">
                  <!-- 项目根目录 -->
                  <div class="explorer-item project-root">
                    <el-icon class="item-icon folder-icon"><FolderOpened /></el-icon>
                    <span class="item-name">{{ currentSkill.folder.name }}</span>
                  </div>
                  
                  <!-- 文件和文件夹 -->
                  <div class="explorer-tree">
                    <template v-for="item in currentSkill.folder.folder" :key="item.path">
                      <!-- 根目录文件（如 SKILL.md）- 只能查看编辑，不能删除 -->
                      <div 
                        v-if="item.type === 'file'"
                        class="explorer-item file-item"
                        :class="{ active: selectedFile?.path === item.path }"
                        @click="selectFile(item as AgentSkillFile)"
                      >
                        <el-icon class="item-icon file-icon"><Document /></el-icon>
                        <span class="item-name">{{ item.name }}</span>
                        <span class="item-badge readonly">只读</span>
                      </div>
                      
                      <!-- 文件夹（scripts / reference） -->
                      <template v-else>
                        <div class="explorer-item folder-item" :class="{ 'can-add': canAddToFolder(item.name) }">
                          <el-icon class="item-icon folder-icon"><FolderOpened /></el-icon>
                          <span class="item-name">{{ item.name }}</span>
                          <!-- 只有 scripts 和 reference 可以添加文件 -->
                          <el-tooltip v-if="canAddToFolder(item.name)" content="添加文件" placement="right">
                            <button 
                              class="item-add"
                              @click.stop="addFileForm.path = item.path; showAddFileDialog = true"
                            >
                              <el-icon><Plus /></el-icon>
                            </button>
                          </el-tooltip>
                        </div>
                        
                        <!-- 子文件 - 可以增删改 -->
                        <div 
                          v-for="subItem in (item as AgentSkillFolder).folder" 
                          :key="subItem.path"
                          class="explorer-item file-item nested"
                          :class="{ active: selectedFile?.path === subItem.path }"
                          @click="selectFile(subItem as AgentSkillFile)"
                        >
                          <el-icon class="item-icon file-icon"><Document /></el-icon>
                          <span class="item-name">{{ subItem.name }}</span>
                          <button 
                            v-if="canDeleteFile(subItem as AgentSkillFile, item.path)"
                            class="item-delete"
                            @click.stop="handleDeleteFile(subItem as AgentSkillFile, item.path)"
                          >
                            <el-icon><Delete /></el-icon>
                          </button>
                        </div>
                        
                        <!-- 空文件夹提示 -->
                        <div 
                          v-if="!(item as AgentSkillFolder).folder?.length && canAddToFolder(item.name)"
                          class="explorer-item empty-hint nested"
                        >
                          <span>暂无文件，点击 + 添加</span>
                        </div>
                      </template>
                    </template>
                  </div>
                </template>
              </div>
              
              <!-- Skill 信息面板 -->
              <div class="skill-info-panel">
                <h4>Skill 信息</h4>
                <p class="info-desc">{{ currentSkill?.description }}</p>
                <div class="info-meta">
                  <span>
                    <el-icon><Clock /></el-icon>
                    创建于 {{ formatTime(currentSkill?.create_time) }}
                  </span>
                </div>
              </div>
            </div>
            
            <!-- 主内容区 - 代码编辑器 -->
            <div class="ide-main">
              <template v-if="selectedFile">
                <!-- 编辑器标签栏 -->
                <div class="editor-tabs">
                  <div class="editor-tab active">
                    <el-icon><Document /></el-icon>
                    <span>{{ selectedFile.name }}</span>
                  </div>
                  <div class="editor-actions">
                    <template v-if="!editMode">
                      <el-button 
                        class="editor-btn editor-btn--ghost"
                        size="small" 
                        :icon="Edit"
                        @click="enterEditMode"
                      >
                        编辑文件
                      </el-button>
                    </template>
                    <template v-else>
                      <el-button 
                        class="editor-btn editor-btn--cancel" 
                        size="small" 
                        @click="cancelEdit"
                      >
                        取消
                      </el-button>
                      <el-button 
                        class="editor-btn editor-btn--primary" 
                        size="small" 
                        @click="saveFileContent"
                        :loading="savingFile"
                      >
                        保存更改
                      </el-button>
                    </template>
                  </div>
                </div>
                
                <!-- 代码内容 -->
                <div class="editor-content">
                  <div v-if="editMode" id="skill-monaco-editor" class="monaco-container"></div>
                  <pre v-else class="code-preview"><code>{{ fileContent }}</code></pre>
                </div>
              </template>
              
              <!-- 无文件选中状态 -->
              <div v-else class="no-file-state">
                <div class="no-file-visual">
                  <el-icon :size="64" class="no-file-icon"><Document /></el-icon>
                </div>
                <h3>选择一个文件开始编辑</h3>
                <p>从左侧文件资源管理器中选择文件，或创建新文件</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 添加文件对话框 - 使用 Teleport 确保显示在最上层 -->
    <Teleport to="body">
      <div v-if="showAddFileDialog" class="modal-overlay add-file-modal" @click.self="closeAddFileDialog">
        <div class="modal-dialog add-file-dialog">
          <div class="dialog-header">
            <div class="dialog-icon add-icon">
              <el-icon><Document /></el-icon>
            </div>
            <div class="dialog-title-wrapper">
              <h3>新建文件</h3>
              <p>在 {{ addFileForm.path || '选择的目录' }} 中创建新文件</p>
            </div>
            <button class="close-btn" @click="closeAddFileDialog">
              <el-icon><CloseBold /></el-icon>
            </button>
          </div>
          
          <div class="dialog-body">
            <div class="add-file-tip">
              <el-icon><Document /></el-icon>
              <span>文件只能添加到 <strong>scripts</strong> 或 <strong>reference</strong> 目录下</span>
            </div>
            
            <div class="form-group">
              <label>目标目录</label>
              <el-select v-model="addFileForm.path" placeholder="选择文件存放目录" style="width: 100%" size="large">
                <template v-if="currentSkill?.folder?.folder">
                  <el-option 
                    v-for="item in getAddableFolders"
                    :key="item.path"
                    :value="item.path"
                  >
                    <div class="folder-option">
                      <el-icon class="folder-option-icon"><FolderOpened /></el-icon>
                      <span>{{ item.name }}</span>
                      <span class="folder-option-path">{{ item.path }}</span>
                    </div>
                  </el-option>
                </template>
              </el-select>
            </div>
            
            <div class="form-group">
              <label>文件名称</label>
              <el-input 
                v-model="addFileForm.name" 
                placeholder="例如：my_script.py, data.json, README.md"
                size="large"
                @keyup.enter="handleAddFile"
              >
                <template #prefix>
                  <el-icon><Document /></el-icon>
                </template>
              </el-input>
              <div class="file-name-hint">
                支持的文件类型：.py, .js, .ts, .json, .md, .yaml, .sh 等
              </div>
            </div>
          </div>
          
          <div class="dialog-footer">
            <el-button @click="closeAddFileDialog" size="large">取消</el-button>
            <el-button 
              type="primary" 
              @click="handleAddFile" 
              :disabled="!addFileForm.path || !addFileForm.name"
              :loading="addingFile"
              size="large"
            >
              <el-icon v-if="!addingFile"><Plus /></el-icon>
              {{ addingFile ? '创建中...' : '创建文件' }}
            </el-button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 手写确认弹窗（Element 风格，但不依赖 Element 组件） -->
    <Teleport to="body">
      <div
        v-if="confirmDialog.visible"
        class="modal-overlay confirm-modal"
        @click.self="closeConfirmDialog(false)"
      >
        <div class="modal-dialog confirm-dialog" role="dialog" aria-modal="true">
          <div class="dialog-header">
            <div class="dialog-title">{{ confirmDialog.title }}</div>
            <button class="dialog-close" type="button" @click="closeConfirmDialog(false)" aria-label="关闭">
              ×
            </button>
          </div>
          <div class="dialog-body">
            <p class="dialog-message">{{ confirmDialog.message }}</p>
          </div>
          <div class="dialog-footer">
            <button class="btn btn-default" type="button" @click="closeConfirmDialog(false)">
              {{ confirmDialog.cancelText }}
            </button>
            <button
              class="btn"
              :class="confirmDialog.variant === 'danger' ? 'btn-danger' : 'btn-primary'"
              type="button"
              @click="closeConfirmDialog(true)"
            >
              {{ confirmDialog.confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style lang="scss">
// 全局弹窗样式
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99999;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

// 手写确认弹窗样式（Element MessageBox 观感）
.confirm-modal {
  z-index: 1000000 !important;

  .confirm-dialog {
    width: 90%;
    max-width: 420px;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.25);
    overflow: hidden;
    animation: slideUp 0.22s ease;
    border: 1px solid rgba(0, 0, 0, 0.06);
  }

  .dialog-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px;
    border-bottom: 1px solid #ebeef5;
    background: #fff;

    .dialog-title {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }

    .dialog-close {
      width: 28px;
      height: 28px;
      border: none;
      background: transparent;
      color: #909399;
      cursor: pointer;
      border-radius: 6px;
      font-size: 18px;
      line-height: 28px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s ease;

      &:hover {
        background: rgba(144, 147, 153, 0.12);
        color: #606266;
      }
    }
  }

  .dialog-body {
    padding: 18px 16px 6px;

    .dialog-message {
      margin: 0;
      font-size: 14px;
      color: #606266;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
    }
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    padding: 12px 16px 16px;
    background: #fff;

    .btn {
      height: 32px;
      padding: 0 14px;
      border-radius: 6px;
      border: 1px solid transparent;
      font-size: 14px;
      cursor: pointer;
      transition: all 0.15s ease;
      user-select: none;
    }

    .btn-default {
      background: #fff;
      border-color: #dcdfe6;
      color: #606266;

      &:hover {
        border-color: #c0c4cc;
        color: #409eff;
      }
    }

    .btn-primary {
      background: #409eff;
      border-color: #409eff;
      color: #fff;

      &:hover {
        filter: brightness(1.03);
      }
    }

    .btn-danger {
      background: #f56c6c;
      border-color: #f56c6c;
      color: #fff;

      &:hover {
        filter: brightness(1.03);
      }
    }
  }
}

// 创建弹窗样式
.create-modal {
  .create-dialog {
    background: white;
    border-radius: 20px;
    width: 90%;
    max-width: 520px;
    box-shadow: 0 32px 64px rgba(0, 0, 0, 0.2);
    animation: slideUp 0.3s ease;
    overflow: hidden;
    
    .dialog-header {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 24px 24px 20px;
      background: linear-gradient(135deg, #f0f7ff 0%, #e8f4fd 100%);
      border-bottom: 1px solid #e1ecf4;
      position: relative;
      
      .dialog-icon {
        width: 56px;
        height: 56px;
        background: white;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(27, 124, 228, 0.15);
        
        img {
          width: 36px;
          height: 36px;
        }
      }
      
      .dialog-title-wrapper {
        flex: 1;
        
        h3 {
          margin: 0 0 4px;
          font-size: 20px;
          font-weight: 600;
          color: #1a1a1a;
        }
        
        p {
          margin: 0;
          font-size: 14px;
          color: #666;
        }
      }
      
      .close-btn {
        position: absolute;
        top: 16px;
        right: 16px;
        width: 32px;
        height: 32px;
        border: none;
        background: rgba(0, 0, 0, 0.05);
        border-radius: 8px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #666;
        transition: all 0.2s ease;
        
        &:hover {
          background: rgba(0, 0, 0, 0.1);
          color: #333;
        }
      }
    }
    
    .dialog-body {
      padding: 24px;
      
      .form-tip {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 16px;
        background: linear-gradient(135deg, #f8fbff 0%, #f0f7ff 100%);
        border: 1px solid #d4e5f7;
        border-radius: 12px;
        margin-bottom: 24px;
        
        .tip-icon {
          flex-shrink: 0;
          margin-top: 2px;
        }
        
        p {
          margin: 0;
          font-size: 14px;
          color: #1B7CE4;
          line-height: 1.6;
        }
      }
      
      .create-form {
        .el-form-item__label {
          font-weight: 600;
          color: #333;
          padding-bottom: 8px;
        }
        
        .el-input__wrapper,
        .el-textarea__inner {
          border-radius: 10px;
        }
      }
    }
    
    .dialog-footer {
      padding: 16px 24px 24px;
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      
      .el-button {
        border-radius: 10px;
        padding: 12px 24px;
      }
    }
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// 添加文件弹窗样式
.add-file-modal {
  z-index: 999999 !important;
  
  .add-file-dialog {
    background: white;
    border-radius: 16px;
    width: 90%;
    max-width: 480px;
    box-shadow: 0 32px 64px rgba(0, 0, 0, 0.25);
    animation: slideUp 0.3s ease;
    overflow: hidden;
    
    .dialog-header {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 20px 24px;
      background: linear-gradient(135deg, #eef4ff 0%, #e0ecff 100%);
      border-bottom: 1px solid #c7ddff;
      position: relative;
      
      .dialog-icon.add-icon {
        width: 48px;
        height: 48px;
        background: white;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(27, 124, 228, 0.2);
        color: #1B7CE4;
        font-size: 24px;
      }
      
      .dialog-title-wrapper {
        flex: 1;
        
        h3 {
          margin: 0 0 4px;
          font-size: 18px;
          font-weight: 600;
          color: #1f2937;
        }
        
        p {
          margin: 0;
          font-size: 13px;
          color: #64748b;
        }
      }
      
      .close-btn {
        position: absolute;
        top: 12px;
        right: 12px;
        width: 32px;
        height: 32px;
        border: none;
        background: rgba(0, 0, 0, 0.05);
        border-radius: 8px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #666;
        transition: all 0.2s ease;
        
        &:hover {
          background: rgba(0, 0, 0, 0.1);
          color: #333;
        }
      }
    }
    
    .dialog-body {
      padding: 24px;
      
      .add-file-tip {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 14px 16px;
        background: linear-gradient(135deg, #f0f7ff 0%, #e8f4fd 100%);
        border: 1px solid #d4e5f7;
        border-radius: 10px;
        margin-bottom: 20px;
        color: #1B7CE4;
        font-size: 14px;
        
        .el-icon {
          font-size: 18px;
        }
        
        strong {
          color: #0958d9;
          font-weight: 600;
        }
      }
      
      .form-group {
        margin-bottom: 20px;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        label {
          display: block;
          font-size: 14px;
          font-weight: 600;
          color: #333;
          margin-bottom: 8px;
        }
        
        .file-name-hint {
          margin-top: 8px;
          font-size: 12px;
          color: #909399;
        }
      }
      
      .folder-option {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .folder-option-icon {
          color: #dcb67a;
        }
        
        .folder-option-path {
          margin-left: auto;
          color: #909399;
          font-size: 12px;
        }
      }
    }
    
    .dialog-footer {
      padding: 16px 24px;
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      border-top: 1px solid #ebeef5;
      background: #fafafa;
      
      .el-button {
        border-radius: 8px;
      }
    }
  }
}

// 详情弹窗 - IDE 风格
.detail-modal {
  .detail-dialog {
    background: #ffffff;
    border-radius: 16px;
    width: 95%;
    max-width: 1400px;
    height: 80vh;
    border: 1px solid #e5e7eb;
    box-shadow: 0 24px 48px rgba(15, 23, 42, 0.18);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    animation: slideUp 0.3s ease;
    
    // IDE 头部
    .ide-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: #f8fafc;
      border-bottom: 1px solid #e5e7eb;
      height: 40px;
      padding: 0 12px;
      
      .ide-tabs {
        display: flex;
        align-items: center;
        height: 100%;
        
        .ide-tab {
          display: flex;
          align-items: center;
          gap: 8px;
          height: 100%;
          padding: 0 16px;
          background: #ffffff;
          border-top: 2px solid #1B7CE4;
          color: #1f2937;
          font-size: 13px;
          
          .tab-icon {
            width: 16px;
            height: 16px;
          }
        }
      }
      
      .ide-actions {
        .ide-btn {
          width: 32px;
          height: 32px;
          border: none;
          background: transparent;
          color: #64748b;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 4px;
          transition: all 0.2s ease;
          
          &:hover {
            background: #e2e8f0;
            color: #1f2937;
          }
        }
      }
    }
    
    // IDE 内容区
    .ide-body {
      flex: 1;
      display: flex;
      overflow: hidden;
      
      // 侧边栏
      .ide-sidebar {
        width: 260px;
        background: #f8fafc;
        border-right: 1px solid #e5e7eb;
        display: flex;
        flex-direction: column;
        
        .sidebar-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          color: #64748b;
          font-size: 11px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          border-bottom: 1px solid #e5e7eb;
          
          .sidebar-hint {
            color: #94a3b8;
            cursor: help;
            display: flex;
            align-items: center;
            
            &:hover {
              color: #64748b;
            }
          }
        }
        
        .file-explorer {
          flex: 1;
          overflow-y: auto;
          padding: 8px 0;
          
          .explorer-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 16px;
            color: #334155;
            font-size: 13px;
            cursor: pointer;
            position: relative;
            
            &:hover {
              background: #f1f5f9;
              
              .item-delete {
                opacity: 1;
              }
            }
            
            &.active {
              background: #e8f2ff;
              color: #1f2937;
              
              &::before {
                content: '';
                position: absolute;
                left: 0;
                top: 0;
                bottom: 0;
                width: 2px;
                background: #1B7CE4;
              }
            }
            
            &.project-root {
              color: #0f172a;
              font-weight: 500;
              padding-top: 8px;
              padding-bottom: 8px;
            }
            
            &.folder-item {
              color: #b7791f;
              
              &.can-add:hover {
                .item-add {
                  opacity: 1;
                }
              }
            }
            
            &.nested {
              padding-left: 40px;
            }
            
            &.empty-hint {
              color: #94a3b8;
              font-size: 12px;
              font-style: italic;
              cursor: default;
              
              &:hover {
                background: transparent;
              }
            }
            
            .item-badge {
              font-size: 10px;
              padding: 2px 6px;
              border-radius: 4px;
              margin-left: auto;
              
              &.readonly {
                background: rgba(102, 102, 102, 0.3);
                color: #999;
              }
            }
            
            .item-add {
              opacity: 0;
              width: 20px;
              height: 20px;
              border: none;
              background: transparent;
              color: #4caf50;
              cursor: pointer;
              display: flex;
              align-items: center;
              justify-content: center;
              border-radius: 4px;
              transition: all 0.2s ease;
              margin-left: auto;
              
              &:hover {
                background: rgba(76, 175, 80, 0.2);
                color: #81c784;
              }
            }
            
            .item-icon {
              font-size: 16px;
              flex-shrink: 0;
              
              &.folder-icon {
                color: #b7791f;
              }
              
              &.file-icon {
                color: #2563eb;
              }
            }
            
            .item-name {
              flex: 1;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }
            
            .item-delete {
              opacity: 0;
              width: 20px;
              height: 20px;
              border: none;
              background: transparent;
              color: #ef4444;
              cursor: pointer;
              display: flex;
              align-items: center;
              justify-content: center;
              border-radius: 4px;
              transition: opacity 0.2s ease;
              
              &:hover {
                background: rgba(239, 68, 68, 0.15);
              }
            }
          }
        }
        
        .skill-info-panel {
          padding: 16px;
          background: #ffffff;
          border-top: 1px solid #e5e7eb;
          
          h4 {
            margin: 0 0 8px;
            font-size: 12px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          
          .info-desc {
            margin: 0 0 12px;
            font-size: 13px;
            color: #475569;
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
          }
          
          .info-meta {
            font-size: 12px;
            color: #94a3b8;
            
            span {
              display: flex;
              align-items: center;
              gap: 6px;
            }
          }
        }
      }
      
      // 主编辑区
      .ide-main {
        flex: 1;
        display: flex;
        flex-direction: column;
        background: #ffffff;
        
        .editor-tabs {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 16px;
          height: 48px;
          background: #ffffff;
          border-bottom: 1px solid #e5e7eb;
          
          .editor-tab {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #334155;
            font-size: 13px;
            
            .el-icon {
              color: #1B7CE4;
            }
          }
          
          .editor-actions {
            display: flex;
            gap: 8px;

            .editor-btn {
              display: inline-flex;
              align-items: center;
              gap: 6px;
              height: 30px;
              padding: 0 14px;
              border-radius: 999px;
              font-size: 12px;
              font-weight: 500;
              border: 1px solid transparent;
              background: transparent;
              color: #475569;
              transition: all 0.18s ease;

              .el-icon {
                font-size: 14px;
              }

              &--ghost {
                border-color: #dbeafe;
                background: #eff6ff;
                color: #1d4ed8;

                &:hover {
                  background: #dbeafe;
                  border-color: #bfdbfe;
                  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.15);
                  transform: translateY(-0.5px);
                }
              }

              &--cancel {
                background: transparent;
                color: #64748b;
                border-color: #e2e8f0;

                &:hover {
                  background: #f8fafc;
                  border-color: #cbd5e1;
                }
              }

              &--primary {
                background: linear-gradient(135deg, #1B7CE4 0%, #0ea5e9 100%);
                border-color: transparent;
                color: #ffffff;
                box-shadow: 0 4px 10px rgba(37, 99, 235, 0.25);

                &:hover {
                  filter: brightness(1.05);
                  box-shadow: 0 6px 14px rgba(37, 99, 235, 0.3);
                  transform: translateY(-0.5px);
                }

                &.is-loading {
                  opacity: 0.8;
                  box-shadow: none;
                  transform: none;
                }
              }
            }
          }
        }
        
        .editor-content {
          flex: 1;
          overflow: hidden;
          
          .monaco-container {
            width: 100%;
            height: 100%;
          }
          
          .code-preview {
            margin: 0;
            padding: 20px;
            height: 100%;
            overflow: auto;
            background: #f8fafc;
            
            code {
              font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
              font-size: 14px;
              line-height: 1.6;
              color: #1f2937;
              white-space: pre-wrap;
              word-wrap: break-word;
            }
          }
        }
        
        .no-file-state {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: #64748b;
          
          .no-file-icon {
            color: #cbd5e1;
            margin-bottom: 16px;
          }
          
          h3 {
            margin: 0 0 8px;
            font-size: 18px;
            color: #334155;
          }
          
          p {
            margin: 0;
            font-size: 14px;
          }
        }
      }
    }
  }
}
</style>

<style lang="scss" scoped>
.skill-page {
  padding: 32px;
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  
  // 页面头部
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
      display: flex;
      gap: 12px;
      
      :deep(.el-button) {
        border-radius: 12px;
        font-weight: 600;
        padding: 12px 24px;
        font-size: 14px;
        transition: all 0.3s ease;
        
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(75, 142, 230, 0.3);
        }
      }
    }
  }
  
  // 列表容器
  .skill-container {
    background: #ffffff;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    overflow: hidden;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
    
    // 列表头部
    .list-header {
      display: flex;
      align-items: center;
      padding: 14px 24px;
      background: #f8fafc;
      border-bottom: 1px solid #e5e7eb;
      font-size: 12px;
      font-weight: 600;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      
      .col-name { flex: 0 0 240px; }
      .col-desc { flex: 1; min-width: 200px; }
      .col-files { flex: 0 0 100px; text-align: center; }
      .col-time { flex: 0 0 120px; }
      .col-actions { flex: 0 0 100px; text-align: right; }
    }
    
    // 列表内容
    .skill-list {
      .skill-row {
        display: flex;
        align-items: center;
        padding: 16px 24px;
        border-bottom: 1px solid #f1f5f9;
        cursor: pointer;
        transition: all 0.2s ease;
        
        &:last-child {
          border-bottom: none;
        }
        
        &:hover {
          background: #f8fafc;
          
          .col-name .skill-info .skill-avatar {
            transform: scale(1.05);
            box-shadow: 0 0 0 3px rgba(27, 124, 228, 0.1);
          }
          
          .col-actions .action-btn {
            opacity: 1;
          }
        }
        
        .col-name {
          flex: 0 0 240px;
          
          .skill-info {
            display: flex;
            align-items: center;
            gap: 14px;
            
            .skill-avatar {
              width: 40px;
              height: 40px;
              background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
              border-radius: 10px;
              display: flex;
              align-items: center;
              justify-content: center;
              border: 1px solid #e0f2fe;
              transition: all 0.2s ease;
              flex-shrink: 0;
              
              img {
                width: 22px;
                height: 22px;
              }
            }
            
            .skill-name {
              font-size: 15px;
              font-weight: 600;
              color: #1e293b;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
            }
          }
        }
        
        .col-desc {
          flex: 1;
          min-width: 200px;
          padding-right: 24px;
          
          .skill-desc {
            font-size: 14px;
            color: #64748b;
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 1;
            -webkit-box-orient: vertical;
            overflow: hidden;
          }
        }
        
        .col-files {
          flex: 0 0 100px;
          text-align: center;
          
          .file-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            background: #e0f2fe;
            color: #0284c7;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
            
            .el-icon {
              font-size: 14px;
            }
          }
        }
        
        .col-time {
          flex: 0 0 120px;
          
          .time-text {
            font-size: 13px;
            color: #94a3b8;
          }
        }
        
        .col-actions {
          flex: 0 0 100px;
          display: flex;
          justify-content: flex-end;
          gap: 8px;
          
          .action-btn {
            width: 32px;
            height: 32px;
            border: 1px solid transparent;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            font-size: 14px;
            opacity: 0.5;
            
            &.view-btn {
              background: #f1f5f9;
              color: #64748b;
              
              &:hover {
                background: #e0f2fe;
                color: #0284c7;
                border-color: #bae6fd;
                opacity: 1;
              }
            }
            
            &.delete-btn {
              background: #fff1f2;
              color: #ef4444;
              
              &:hover {
                background: #fee2e2;
                color: #dc2626;
                border-color: #fecaca;
                opacity: 1;
              }
            }
          }
        }
      }
    }
    
    // 空状态 - 放在 skill-container 内部
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 80px 20px;
      
      .empty-visual {
        margin-bottom: 24px;
        
        .empty-icon-wrapper {
          width: 80px;
          height: 80px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f8fafc;
          border-radius: 50%;
          
          .empty-icon {
            width: 44px;
            height: 44px;
            opacity: 0.4;
          }
        }
      }
      
      .empty-content {
        text-align: center;
        
        h3 {
          margin: 0 0 8px;
          font-size: 18px;
          font-weight: 600;
          color: #1e293b;
        }
        
        p {
          margin: 0 0 24px;
          font-size: 14px;
          color: #64748b;
          max-width: 360px;
        }
        
        .empty-btn {
          height: 40px;
          padding: 0 24px;
          border-radius: 10px;
          font-size: 14px;
          font-weight: 600;
        }
      }
    }
  }
}

// 动画
@keyframes cardAppear {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes ringPulse {
  0% {
    transform: scale(0.5);
    opacity: 0.6;
  }
  100% {
    transform: scale(1);
    opacity: 0;
  }
}

// 卡片列表动画
.card-list-enter-active,
.card-list-leave-active {
  transition: all 0.4s ease;
}

.card-list-enter-from,
.card-list-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

// 响应式
@media (max-width: 768px) {
  .skill-page {
    padding: 16px;
    
    .page-header .header-content {
      flex-direction: column;
      gap: 24px;
      
      .header-right {
        width: 100%;
        flex-direction: column;
        gap: 16px;
        
        .stats-cards {
          width: 100%;
          
          .stat-card {
            width: 100%;
            justify-content: center;
          }
        }
        
        .header-actions {
          width: 100%;
          justify-content: center;
        }
      }
    }
    
    .filter-section {
      flex-direction: column;
      gap: 16px;
      align-items: stretch;
      
      .search-wrapper .search-input {
        width: 100%;
      }
      
      .filter-info {
        justify-content: space-between;
      }
    }
    
    .skill-container .skill-grid {
      grid-template-columns: 1fr;
    }
  }
}
</style>
