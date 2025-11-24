<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElUpload, ElButton, ElTable, ElTableColumn, ElIcon } from 'element-plus'
import { 
  Upload, 
  Delete, 
  Document, 
  FolderOpened,
  Loading,
  Check,
  Close
} from '@element-plus/icons-vue'
import { 
  getKnowledgeFileListAPI, 
  deleteKnowledgeFileAPI,
  createKnowledgeFileAPI,
  formatFileSize,
  getFileType,
  KnowledgeFileResponse,
  KnowledgeFileStatus,
  type KnowledgeFileDeleteRequest,
  type KnowledgeFileCreateRequest
} from '../../apis/knowledge-file'
import type { UploadProps, UploadUserFile } from 'element-plus'

const route = useRoute()
const router = useRouter()

// 获取知识库ID
const knowledgeId = computed(() => route.params.knowledgeId as string)
const knowledgeName = computed(() => route.query.name as string || '未知知识库')

// 状态管理
const files = ref<KnowledgeFileResponse[]>([])
const loading = ref(false)
const uploading = ref(false)

// 文件上传
const fileList = ref<UploadUserFile[]>([])

// 轮询相关
let pollingTimer: NodeJS.Timeout | null = null
const isPolling = ref(false)

// 排序相关
const sortType = ref('time') // 默认按时间排序
const sortOrder = ref('desc') // 默认降序（最新的在前）

// 检查是否有进行中的文件
const hasProcessingFiles = computed(() => {
  return files.value.some(file => 
    String(file.status).includes('🚀') ||
    String(file.status).includes('进行')
  )
})

// 排序后的文件列表
const sortedFiles = computed(() => {
  const filesCopy = [...files.value]
  
  return filesCopy.sort((a, b) => {
    let result = 0
    
    switch (sortType.value) {
      case 'time':
        result = new Date(a.create_time).getTime() - new Date(b.create_time).getTime()
        break
      case 'name':
        result = a.file_name.localeCompare(b.file_name, 'zh-CN')
        break
      case 'size':
        result = a.file_size - b.file_size
        break
      case 'status':
        // 按状态排序：进行中 > 完成 > 失败
        const statusOrder = { 
          '🚀 进行中': 3, 
          '✅ 完成': 2, 
          '❌ 失败': 1 
        }
        const aOrder = Object.entries(statusOrder).find(([key]) => String(a.status).includes(key.split(' ')[0]))?.[1] || 0
        const bOrder = Object.entries(statusOrder).find(([key]) => String(b.status).includes(key.split(' ')[0]))?.[1] || 0
        result = aOrder - bOrder
        break
      default:
        result = 0
    }
    
    // 应用排序顺序
    return sortOrder.value === 'desc' ? -result : result
  })
})

// 处理排序改变
const handleSortChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  sortType.value = target.value
}

// 开始轮询
const startPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
  }
  
  isPolling.value = true
  pollingTimer = setInterval(async () => {
    await fetchFiles(false) // 静默获取，不显示loading
    
    // 如果没有进行中的文件，停止轮询
    if (!hasProcessingFiles.value) {
      stopPolling()
    }
  }, 15000) // 15秒轮询一次
}

// 停止轮询
const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
  isPolling.value = false
}

// 获取文件列表
const fetchFiles = async (showLoading = true) => {
  if (!knowledgeId.value) {
    ElMessage.error('知识库ID不能为空')
    return
  }
  
  if (showLoading) {
    loading.value = true
  }
  
  try {
    const response = await getKnowledgeFileListAPI(knowledgeId.value)
    if (response.data.status_code === 200 && response.data.data) {
      // 调试：打印后端返回的状态值
      console.log('后端返回的文件数据:', response.data.data)
      response.data.data.forEach((file: any, index: number) => {
        console.log(`文件${index}: ${file.file_name}, 原状态: "${file.status}", 转换后: "${mapStatusToDisplay(file.status)}"`)
      })
      
      // 转换后端状态为前端显示状态
      const processedFiles = response.data.data.map((file: any) => ({
        ...file,
        status: mapStatusToDisplay(file.status)
      }))
      
      files.value = processedFiles
      
      // 检查是否需要开始或停止轮询
      if (hasProcessingFiles.value && !isPolling.value) {
        startPolling()
      } else if (!hasProcessingFiles.value && isPolling.value) {
        stopPolling()
      }
    } else {
      ElMessage.error('获取文件列表失败: ' + response.data.status_message)
    }
  } catch (error) {
    console.error('获取文件列表失败:', error)
    ElMessage.error('获取文件列表失败')
  } finally {
    if (showLoading) {
      loading.value = false
    }
  }
}

// 删除文件相关状态
const showConfirmDialog = ref(false)
const fileToDelete = ref<KnowledgeFileResponse | null>(null)

// 删除文件
const handleDelete = (file: KnowledgeFileResponse) => {
  // 显示确认对话框
  fileToDelete.value = file
  showConfirmDialog.value = true
}

// 确认删除
const confirmDelete = async () => {
  if (!fileToDelete.value) return
  
  try {
    const deleteData: KnowledgeFileDeleteRequest = {
      knowledge_file_id: fileToDelete.value.id
    }
    
    const response = await deleteKnowledgeFileAPI(deleteData)
    
    if (response.data.status_code === 200) {
      ElMessage.success('删除成功')
      await fetchFiles() // 刷新列表
    } else {
      ElMessage.error('删除失败: ' + response.data.status_message)
    }
  } catch (error: any) {
    console.error('删除文件失败:', error)
    ElMessage.error('删除失败: ' + (error?.message || error))
  } finally {
    // 关闭确认对话框
    showConfirmDialog.value = false
    fileToDelete.value = null
  }
}

// 取消删除
const cancelDelete = () => {
  showConfirmDialog.value = false
  fileToDelete.value = null
}

// 文件上传前处理
const beforeUpload: UploadProps['beforeUpload'] = (rawFile) => {
  // 文件大小限制：100MB
  const maxSize = 100 * 1024 * 1024
  if (rawFile.size > maxSize) {
    ElMessage.error('文件大小不能超过100MB')
    return false
  }
  
  // 支持的文件类型
  const supportedTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/markdown',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'image/jpeg',
    'image/png',
    'image/gif'
  ]
  
  if (!supportedTypes.includes(rawFile.type)) {
    ElMessage.error('不支持的文件类型，请上传PDF、Word、Excel、文本或图片文件')
    return false
  }
  
  // 立即添加文件到列表，显示为处理中状态
  const tempFile: KnowledgeFileResponse = {
    id: `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    file_name: rawFile.name,
    knowledge_id: knowledgeId.value,
    status: KnowledgeFileStatus.PROCESS,
    user_id: '',
    oss_url: '',
    file_size: rawFile.size,
    create_time: new Date().toISOString(),
    update_time: new Date().toISOString()
  }
  
  files.value.unshift(tempFile) // 添加到列表顶部
  
  // 开始轮询（如果还没有开始）
  if (!isPolling.value) {
    startPolling()
  }
  
  // 设置上传状态
  uploading.value = true
  return true
}

// 文件上传成功处理
const handleUploadSuccess = async (response: any, file: any, fileList: any) => {
  try {
    // 后端返回的response格式是: { status_code: 200, status_message: "success", data: "file_url" }
    if (response && response.status_code === 200 && response.data) {
      // 找到对应的临时文件，将状态设置为解析中
      const tempFileIndex = files.value.findIndex(f => f.file_name === file.name && f.id.startsWith('temp_'))
      
      if (tempFileIndex !== -1) {
        files.value[tempFileIndex].status = KnowledgeFileStatus.PROCESS // 设置为解析中
      }
      
      // 提示用户文件正在解析
      // ElMessage.info('文件上传成功，正在解析中，请稍候...')
      
      const createData: KnowledgeFileCreateRequest = {
        knowledge_id: knowledgeId.value,
        file_url: response.data
      }
      
      // 调用解析接口
      const apiResponse = await createKnowledgeFileAPI(createData)
      
      // 根据解析接口返回的状态码决定最终状态
      if (apiResponse.data.status_code === 200) {
        ElMessage.success('文件解析成功')
        
        // 移除临时文件
        if (tempFileIndex !== -1) {
          files.value.splice(tempFileIndex, 1)
        }
        
        // 刷新列表获取真实数据
        await fetchFiles(false)
      } else if (apiResponse.data.status_code === 500) {
        ElMessage.error('文件解析失败: ' + apiResponse.data.status_message)
        
        // 解析失败，将临时文件状态改为失败
        if (tempFileIndex !== -1) {
          files.value[tempFileIndex].status = KnowledgeFileStatus.FAIL
        }
      } else {
        ElMessage.error('文件处理失败: ' + apiResponse.data.status_message)
        
        // 其他错误，将临时文件状态改为失败
        if (tempFileIndex !== -1) {
          files.value[tempFileIndex].status = KnowledgeFileStatus.FAIL
        }
      }
      
      fileList.value = [] // 清空上传列表
    } else {
      ElMessage.error('文件上传失败: ' + (response?.status_message || '未知错误'))
      
      // 上传失败，将临时文件状态改为失败
      const tempFileIndex = files.value.findIndex(f => f.file_name === file.name && f.id.startsWith('temp_'))
      if (tempFileIndex !== -1) {
        files.value[tempFileIndex].status = KnowledgeFileStatus.FAIL
      }
    }
  } catch (error: any) {
    console.error('文件解析异常:', error?.message || error)
    
    // 处理超时情况
    if (error?.code === 'ECONNABORTED' && error?.message?.includes('timeout')) {
      ElMessage.warning('文件解析时间较长，请稍后刷新查看结果')
      // 不要将状态设为失败，因为后端可能还在处理中
    } else {
      ElMessage.error('文件解析失败: ' + (error?.message || error))
      
      // 其他错误才设置为失败
      const tempFileIndex = files.value.findIndex(f => f.file_name === file.name && f.id.startsWith('temp_'))
      if (tempFileIndex !== -1) {
        files.value[tempFileIndex].status = KnowledgeFileStatus.FAIL
      }
    }
  } finally {
    uploading.value = false
  }
}

// 文件上传失败处理
const handleUploadError = (error: any, file: any) => {
  console.error('文件上传失败:', error)
  ElMessage.error('文件上传失败')
  
  // 上传失败，将临时文件状态改为失败
  const tempFileIndex = files.value.findIndex(f => f.file_name === file.name && f.id.startsWith('temp_'))
  if (tempFileIndex !== -1) {
    files.value[tempFileIndex].status = KnowledgeFileStatus.FAIL
  }
  
  uploading.value = false
}

// 获取状态标签类型
const getStatusTagType = (status: KnowledgeFileStatus) => {
  switch (status) {
    case KnowledgeFileStatus.SUCCESS:
      return 'success'
    case KnowledgeFileStatus.PROCESS:
      return 'warning'
    case KnowledgeFileStatus.FAIL:
      return 'danger'
    default:
      return 'info'
  }
}

// 获取状态样式类
const getStatusClass = (status: KnowledgeFileStatus) => {
  switch (status) {
    case KnowledgeFileStatus.SUCCESS:
      return 'status-success'
    case KnowledgeFileStatus.PROCESS:
      return 'status-process'
    case KnowledgeFileStatus.FAIL:
      return 'status-fail'
    default:
      return 'status-default'
  }
}

// 获取状态图标
const getStatusIcon = (status: KnowledgeFileStatus) => {
  switch (status) {
    case KnowledgeFileStatus.SUCCESS:
      return Check
    case KnowledgeFileStatus.PROCESS:
      return Loading
    case KnowledgeFileStatus.FAIL:
      return Close
    default:
      return Document
  }
}

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}

// 获取认证token
const getToken = () => {
  return localStorage.getItem('token') || ''
}

// 返回上一页
const goBack = () => {
  router.push('/knowledge')
}

// 刷新当前页面（点击当前知识库名称时的操作）
const refreshCurrentPage = () => {
  // 刷新文件列表，给用户文件夹点击的反馈
  fetchFiles()
}

// 是否为临时文件
const isTempFile = (file: KnowledgeFileResponse) => {
  return file.id.startsWith('temp_')
}

// 状态映射函数 - 将后端英文状态转换为前端显示状态
const mapStatusToDisplay = (backendStatus: string) => {
  const statusMap: { [key: string]: string } = {
    'success': KnowledgeFileStatus.SUCCESS, // '✅ 完成'
    'fail': KnowledgeFileStatus.FAIL,       // '❌ 失败'
    'process': KnowledgeFileStatus.PROCESS  // '🚀 进行中'
  }
  return statusMap[backendStatus] || `❓ ${backendStatus}`
}

// 获取文件图标
const getFileIcon = (fileName: string) => {
  const ext = fileName.split('.').pop()?.toLowerCase()
  const iconMap: { [key: string]: string } = {
    pdf: '📄',
    doc: '📝',
    docx: '📝',
    txt: '📃',
    md: '📋',
    xls: '📊',
    xlsx: '📊',
    ppt: '📊',
    pptx: '📊',
    jpg: '🖼️',
    jpeg: '🖼️',
    png: '🖼️',
    gif: '🖼️',
    bmp: '🖼️',
    zip: '🗜️',
    rar: '🗜️',
    '7z': '🗜️'
  }
  return iconMap[ext || ''] || '📁'
}

// 获取文件大小颜色
const getFileSizeColor = (size: number) => {
  if (size < 1024 * 1024) return '#67c23a' // 绿色 < 1MB
  if (size < 10 * 1024 * 1024) return '#e6a23c' // 橙色 < 10MB  
  return '#f56c6c' // 红色 >= 10MB
}

// 获取状态动画类
const getStatusAnimationClass = (status: string) => {
  if (status.includes('🚀') || status.includes('进行')) {
    return 'status-pulse'
  } else if (status.includes('✅') || status.includes('完成')) {
    return 'status-success-glow'
  } else if (status.includes('❌') || status.includes('失败')) {
    return '' // 失败状态不需要动画
  }
  return ''
}

onMounted(() => {
  // 调试：检查API函数是否正确导入
  console.log('检查API函数导入:')
  console.log('getKnowledgeFileListAPI:', getKnowledgeFileListAPI)
  console.log('deleteKnowledgeFileAPI:', deleteKnowledgeFileAPI)
  console.log('createKnowledgeFileAPI:', createKnowledgeFileAPI)
  
  if (knowledgeId.value) {
    fetchFiles()
  } else {
    ElMessage.error('知识库ID参数缺失')
    router.push('/knowledge')
  }
})

// 组件卸载时清理轮询
onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="knowledge-file-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <!-- 导航面包屑 -->
        <div class="navigation-section">
          <div class="nav-title">
            <span class="title-icon">🗂️</span>
            <span class="title-text">文件管理</span>
          </div>
          <div class="breadcrumb">
            <span class="breadcrumb-item clickable" @click="goBack">
              <span class="breadcrumb-icon">📚</span>
              <span class="breadcrumb-text">知识库管理</span>
            </span>
            <span class="breadcrumb-separator">
              <span class="separator-icon">▶</span>
            </span>
            <span class="breadcrumb-item clickable current" @click="refreshCurrentPage">
              <span class="breadcrumb-icon">📂</span>
              <span class="breadcrumb-text">{{ knowledgeName }}</span>
            </span>
          </div>
        </div>
      </div>
      
      <div class="header-right">
        <!-- 状态与操作区域 -->
        <div class="action-section">
          <!-- 文件统计卡片 -->
          <div class="stat-card total">
            <div class="stat-icon-wrapper">
              <span class="stat-icon">📊</span>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ files.length }}</div>
              <div class="stat-label">文件总数</div>
            </div>
          </div>
          
          <div class="stat-card processing">
            <div class="stat-icon-wrapper">
              <span class="stat-icon processing-icon">🚀</span>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ files.filter((f: KnowledgeFileResponse) => String(f.status).includes('🚀')).length }}</div>
              <div class="stat-label">处理中</div>
            </div>
          </div>
          
          <div class="stat-card success">
            <div class="stat-icon-wrapper">
              <span class="stat-icon">✅</span>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ files.filter((f: KnowledgeFileResponse) => String(f.status).includes('✅')).length }}</div>
              <div class="stat-label">已完成</div>
            </div>
          </div>
          
          <!-- 轮询状态指示器 -->
          <div v-if="isPolling" class="sync-indicator">
            <div class="sync-animation">
              <div class="sync-dot"></div>
              <div class="sync-dot"></div>
              <div class="sync-dot"></div>
            </div>
            <span class="sync-text">实时同步</span>
          </div>
          
          <!-- 上传按钮 -->
          <el-upload
            v-model:file-list="fileList"
            :action="`/api/v1/upload`"
            :before-upload="beforeUpload"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :multiple="true"
            :show-file-list="false"
            :disabled="uploading"
            :headers="{ Authorization: `Bearer ${getToken()}` }"
          >
            <div class="upload-button-wrapper">
              <button class="upload-btn-custom" :class="{ 'uploading': uploading }">
                <div class="btn-icon-wrapper">
                  <span v-if="!uploading" class="btn-icon">📤</span>
                  <div v-else class="loading-spinner"></div>
                </div>
                <div class="btn-text-wrapper">
                  <span class="btn-main-text">{{ uploading ? '上传中' : '上传文件' }}</span>
                  <span class="btn-sub-text">{{ uploading ? '请稍候...' : '支持多种格式' }}</span>
                </div>
              </button>
            </div>
          </el-upload>
        </div>
      </div>
    </div>

    <!-- 文件列表 -->
    <div class="file-list" v-loading="loading">
      <!-- 文件列表头部工具栏 -->
      <div v-if="files.length > 0" class="file-toolbar">
        <div class="toolbar-left">
          <h3 class="list-title">
            <span class="title-icon">📋</span>
            文件列表
          </h3>
        </div>
        <div class="toolbar-right">
          <div class="view-options">
            <div class="sort-wrapper">
              <div class="sort-label">
                <span class="sort-icon">⚡</span>
                <span class="sort-text">排序</span>
              </div>
              <div class="sort-dropdown">
                <select 
                  class="sort-select" 
                  v-model="sortType" 
                  @change="handleSortChange"
                >
                  <option value="time">🕐 按时间</option>
                  <option value="name">📝 按名称</option>
                  <option value="size">📏 按大小</option>
                  <option value="status">⚡ 按状态</option>
                </select>
                <div class="dropdown-arrow">
                  <span class="arrow-icon">▼</span>
                </div>
              </div>
              <button 
                class="sort-order-btn" 
                @click="sortOrder = sortOrder === 'desc' ? 'asc' : 'desc'"
                :title="sortOrder === 'desc' ? '点击升序排列' : '点击降序排列'"
              >
                <span v-if="sortOrder === 'desc'" class="sort-order-icon">⬇️</span>
                <span v-else class="sort-order-icon">⬆️</span>
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="files.length > 0" class="file-table">
        <table class="custom-table">
          <thead>
            <tr>
              <th class="col-name">
                <span class="th-content">
                  <span class="th-icon">📄</span>
                  文件名
                </span>
              </th>
              <th class="col-type">
                <span class="th-content">
                  <span class="th-icon">🏷️</span>
                  类型
                </span>
              </th>
              <th class="col-size">
                <span class="th-content">
                  <span class="th-icon">📏</span>
                  大小
                </span>
              </th>
              <th class="col-status">
                <span class="th-content">
                  <span class="th-icon">⚡</span>
                  状态
                </span>
              </th>
              <th class="col-time">
                <span class="th-content">
                  <span class="th-icon">🕐</span>
                  时间
                </span>
              </th>
              <th class="col-action">
                <span class="th-content">
                  <span class="th-icon">⚙️</span>
                  操作
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="file in sortedFiles" :key="file.id" class="file-row" :class="{ 'temp-file': isTempFile(file) }">
              <td class="col-name">
                <div class="file-info">
                  <div class="file-icon-wrapper">
                    <span class="file-icon">{{ getFileIcon(file.file_name) }}</span>
                    <div v-if="isTempFile(file)" class="upload-overlay">
                      <div class="upload-progress"></div>
                    </div>
                  </div>
                  <div class="file-details">
                    <span class="file-name">{{ file.file_name }}</span>
                    <span v-if="isTempFile(file)" class="temp-badge">
                      <span class="badge-icon">⬆️</span>
                      上传中
                    </span>
                  </div>
                </div>
              </td>
              <td class="col-type">
                <span class="type-tag">{{ getFileType(file.file_name) }}</span>
              </td>
              <td class="col-size">
                <span class="size-tag" :style="{ color: getFileSizeColor(file.file_size) }">
                  <span class="size-icon">💾</span>
                  {{ formatFileSize(file.file_size) }}
                </span>
              </td>
              <td class="col-status">
                <span class="status-tag" :class="[getStatusClass(file.status), getStatusAnimationClass(file.status)]">
                  <span class="status-display">{{ file.status }}</span>
                </span>
              </td>
              <td class="col-time">
                <div class="time-info">
                  <span class="time-icon">📅</span>
                  <span class="time-text">{{ formatTime(file.create_time) }}</span>
                </div>
              </td>
              <td class="col-action">
                <div class="action-buttons">
                  <button 
                    v-if="!isTempFile(file)"
                    class="delete-btn"
                    @click="handleDelete(file)"
                    title="删除文件"
                  >
                    <span class="btn-icon">🗑️</span>
                    <span class="btn-text">删除</span>
                  </button>
                  <div v-else class="uploading-indicator">
                    <span class="uploading-icon">⏳</span>
                    <span class="uploading-text">处理中</span>
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- 空状态 -->
      <div v-else-if="!loading" class="empty-state">
        <div class="empty-illustration">
          <div class="empty-cloud">
            <span class="cloud-icon">☁️</span>
            <div class="cloud-files">
              <span class="file-float">📄</span>
              <span class="file-float">📊</span>
              <span class="file-float">🖼️</span>
            </div>
          </div>
        </div>
        <h3 class="empty-title">
          <span class="title-icon">📁</span>
          知识库暂无文件
        </h3>
        <p class="empty-description">
          开始构建您的企业知识库，支持多种文件格式
        </p>
        <div class="empty-features">
          <div class="feature-item">
            <span class="feature-icon">📝</span>
            <span class="feature-text">支持 Word、PDF</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">📊</span>
            <span class="feature-text">支持 Excel、PPT</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">🖼️</span>
            <span class="feature-text">支持图片格式</span>
          </div>
        </div>
        <el-upload
          v-model:file-list="fileList"
          :action="`/api/v1/upload`"
          :before-upload="beforeUpload"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :multiple="true"
          :show-file-list="false"
          :disabled="uploading"
          :headers="{ Authorization: `Bearer ${getToken()}` }"
        >
          <el-button type="primary" size="large" class="empty-upload-btn">
            <span class="btn-icon">🚀</span>
            立即上传文件
          </el-button>
        </el-upload>
      </div>
    </div>

    <!-- 确认删除对话框 -->
    <div v-if="showConfirmDialog" class="custom-confirm-dialog">
      <div class="confirm-dialog-content">
        <h3 class="dialog-title">确认删除</h3>
        <div class="dialog-body">
          确定要删除文件 "{{ fileToDelete?.file_name }}" 吗？删除后无法恢复。
        </div>
        <div class="dialog-footer">
          <button class="btn-cancel" @click="cancelDelete">取消</button>
          <button class="btn-confirm" @click="confirmDelete">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.knowledge-file-page {
  padding: 24px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
  min-height: 100vh;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding: 16px 24px;
    background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.6);
    position: relative;
    overflow: hidden;
    
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 4px;
      background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #4facfe 100%);
    }
    
    .header-left {
      display: flex;
      align-items: center;
      gap: 20px;
      
      .navigation-section {
        display: flex;
        align-items: center;
        gap: 16px;
        
        .nav-title {
          display: flex;
          align-items: center;
          gap: 8px;
          
          .title-icon {
            font-size: 18px;
          }
          
          .title-text {
            font-size: 16px;
            font-weight: 700;
            color: #2c3e50;
            letter-spacing: 0.5px;
          }
        }
      
        .breadcrumb {
          display: flex;
          align-items: center;
          font-size: 14px;
          font-weight: 500;
          
          .breadcrumb-item {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #606266;
            transition: all 0.3s ease;
            
            .breadcrumb-icon {
              font-size: 16px;
            }
            
            .breadcrumb-text {
              font-weight: 500;
            }
            
            &.clickable {
              cursor: pointer;
              padding: 10px 16px;
              border-radius: 12px;
              background: rgba(255, 255, 255, 0.6);
              backdrop-filter: blur(10px);
              border: 1px solid rgba(255, 255, 255, 0.3);
              
              &:hover {
                background: rgba(64, 158, 255, 0.1);
                color: #409eff;
                transform: translateY(-2px);
                box-shadow: 0 4px 16px rgba(64, 158, 255, 0.2);
                border-color: rgba(64, 158, 255, 0.3);
              }
              
              &:active {
                transform: translateY(0);
              }
            }
            
            &.current {
              color: #409eff;
              font-weight: 600;
              background: linear-gradient(135deg, rgba(64, 158, 255, 0.1) 0%, rgba(100, 200, 255, 0.1) 100%);
              border: 1px solid rgba(64, 158, 255, 0.2);
              
              &:hover {
                background: linear-gradient(135deg, rgba(64, 158, 255, 0.2) 0%, rgba(100, 200, 255, 0.2) 100%);
                box-shadow: 0 6px 20px rgba(64, 158, 255, 0.25);
              }
            }
          }
          
          .breadcrumb-separator {
            margin: 0 16px;
            
            .separator-icon {
              color: #409eff;
              font-size: 12px;
              opacity: 0.7;
            }
          }
        }
      }
    }
    
    .header-right {
      display: flex;
      align-items: center;
      
      .action-section {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .stat-card {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 12px 16px;
          background: white;
          border-radius: 12px;
          box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
          border: 1px solid rgba(255, 255, 255, 0.8);
          backdrop-filter: blur(10px);
          transition: all 0.3s ease;
          min-width: 100px;
            
            &:hover {
              transform: translateY(-2px);
              box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
            }
            
                    .stat-icon-wrapper {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            border-radius: 10px;
            
            .stat-icon {
              font-size: 16px;
            }
            
            .processing-icon {
              animation: rocketLaunch 2s infinite;
            }
          }
          
          .stat-content {
            display: flex;
            flex-direction: column;
            
            .stat-number {
              font-size: 16px;
              font-weight: 700;
              line-height: 1;
              margin-bottom: 2px;
            }
            
            .stat-label {
              font-size: 11px;
              opacity: 0.7;
              font-weight: 500;
            }
          }
            
          &.total {
            .stat-icon-wrapper {
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              .stat-icon {
                filter: invert(1);
              }
            }
            .stat-number {
              color: #667eea;
            }
          }
          
          &.processing {
            .stat-icon-wrapper {
              background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            }
            .stat-number {
              color: #f59e0b;
            }
          }
          
          &.success {
            .stat-icon-wrapper {
              background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
            }
            .stat-number {
              color: #10b981;
            }
          }
        }
        
        .sync-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 12px;
          background: rgba(64, 158, 255, 0.1);
          border-radius: 10px;
          border: 1px solid rgba(64, 158, 255, 0.2);
          
          .sync-animation {
            display: flex;
            gap: 3px;
            
            .sync-dot {
              width: 5px;
              height: 5px;
              background: #409eff;
              border-radius: 50%;
              animation: syncWave 1.5s infinite ease-in-out;
              
              &:nth-child(1) { animation-delay: 0s; }
              &:nth-child(2) { animation-delay: 0.2s; }
              &:nth-child(3) { animation-delay: 0.4s; }
            }
          }
          
          .sync-text {
            font-size: 12px;
            color: #409eff;
            font-weight: 500;
          }
        }
        
        .upload-button-wrapper {
          .upload-btn-custom {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 20px;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            border: none;
            border-radius: 12px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 16px rgba(79, 172, 254, 0.3);
            
            &:hover {
              transform: translateY(-2px);
              box-shadow: 0 6px 20px rgba(79, 172, 254, 0.4);
            }
            
            &:active {
              transform: translateY(0);
            }
            
            .btn-icon-wrapper {
              display: flex;
              align-items: center;
              justify-content: center;
              width: 28px;
              height: 28px;
              background: rgba(255, 255, 255, 0.2);
              border-radius: 6px;
              
              .btn-icon {
                font-size: 16px;
              }
              
              .loading-spinner {
                width: 16px;
                height: 16px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-top: 2px solid white;
                border-radius: 50%;
                animation: spin 1s linear infinite;
              }
            }
            
            .btn-text-wrapper {
              display: flex;
              flex-direction: column;
              align-items: flex-start;
              
              .btn-main-text {
                font-size: 13px;
                font-weight: 600;
                line-height: 1;
                margin-bottom: 2px;
              }
              
              .btn-sub-text {
                font-size: 10px;
                opacity: 0.8;
                line-height: 1;
              }
            }
            
            &.uploading {
              background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
              cursor: not-allowed;
            }
          }
        }
      }
    }
  }
  
  .file-list {
    flex: 1;
    overflow: hidden;
    
    .file-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      padding: 16px 24px;
      background: white;
      border-radius: 12px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
      
      .toolbar-left {
        .list-title {
          display: flex;
          align-items: center;
          gap: 10px;
          margin: 0;
          padding: 8px 16px;
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          border-radius: 12px;
          color: white;
          font-size: 16px;
          font-weight: 700;
          box-shadow: 0 3px 12px rgba(240, 147, 251, 0.3);
          letter-spacing: 0.5px;
          
          .title-icon {
            font-size: 18px;
            filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2));
          }
        }
      }
      
      .toolbar-right {
        .view-options {
          display: flex;
          align-items: center;
          
          .sort-wrapper {
            display: flex;
            align-items: center;
            gap: 12px;
            
            .sort-label {
              display: flex;
              align-items: center;
              gap: 6px;
              padding: 8px 12px;
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              border-radius: 10px;
              color: white;
              font-size: 13px;
              font-weight: 600;
              box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
              
              .sort-icon {
                font-size: 14px;
              }
              
              .sort-text {
                letter-spacing: 0.5px;
              }
            }
            
            .sort-dropdown {
              position: relative;
              display: flex;
              align-items: center;
              
              .sort-select {
                appearance: none;
                padding: 10px 40px 10px 16px;
                border: 2px solid #e1e5e9;
                border-radius: 12px;
                background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
                color: #2c3e50;
                font-size: 13px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s ease;
                min-width: 120px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
                
                &:hover {
                  border-color: #409eff;
                  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.2);
                  transform: translateY(-1px);
                }
                
                &:focus {
                  outline: none;
                  border-color: #409eff;
                  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.2);
                  transform: translateY(-1px);
                }
                
                option {
                  padding: 8px 12px;
                  background: white;
                  color: #2c3e50;
                  font-weight: 500;
                }
              }
              
              .dropdown-arrow {
                position: absolute;
                right: 12px;
                top: 50%;
                transform: translateY(-50%);
                pointer-events: none;
                
                .arrow-icon {
                  color: #409eff;
                  font-size: 10px;
                  transition: transform 0.2s ease;
                }
              }
              
              &:hover .dropdown-arrow .arrow-icon {
                transform: scale(1.2);
              }
            }
          }
          
          .sort-order-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
            
            .sort-order-icon {
              font-size: 14px;
              filter: invert(1);
            }
            
            &:hover {
              transform: translateY(-2px);
              box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
            }
            
            &:active {
              transform: translateY(0);
            }
          }
        }
      }
    }
    
    .file-table {
      height: 100%;
      
      .custom-table {
        width: 100%;
        border-collapse: collapse;
        background: white;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        
        th {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          font-weight: 600;
          padding: 16px 20px;
          text-align: left;
          border-bottom: none;
          font-size: 14px;
          position: relative;
          
          .th-content {
            display: flex;
            align-items: center;
            gap: 8px;
            
            .th-icon {
              font-size: 16px;
              opacity: 0.9;
            }
          }
          
          &:first-child {
            border-top-left-radius: 16px;
          }
          
          &:last-child {
            border-top-right-radius: 16px;
          }
        }
        
        .file-row {
          border-bottom: 1px solid rgba(0, 0, 0, 0.05);
          transition: all 0.3s ease;
          position: relative;
          
          &:hover {
            background: linear-gradient(135deg, rgba(79, 172, 254, 0.05) 0%, rgba(0, 242, 254, 0.05) 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
          }
          
          &:last-child {
            border-bottom: none;
          }
          
          &.temp-file {
            background: linear-gradient(135deg, rgba(64, 158, 255, 0.1) 0%, rgba(100, 200, 255, 0.1) 100%);
            border-left: 4px solid #409eff;
            animation: uploadPulse 2s infinite;
          }
        }
        
        td {
          padding: 16px 20px;
          vertical-align: middle;
          font-size: 14px;
          color: #2c3e50;
          font-weight: 500;
        }
        
        .col-name {
          min-width: 200px;
        }
        
        .col-type, .col-size, .col-status {
          width: 120px;
        }
        
        .col-time {
          width: 180px;
        }
        
        .col-action {
          width: 120px;
        }
      }
      
      .file-info {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .file-icon-wrapper {
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 40px;
          height: 40px;
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          border-radius: 12px;
          box-shadow: 0 4px 12px rgba(240, 147, 251, 0.3);
          
          .file-icon {
            font-size: 20px;
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
          }
          
          .upload-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(64, 158, 255, 0.8);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            
            .upload-progress {
              width: 20px;
              height: 20px;
              border: 2px solid white;
              border-top: 2px solid transparent;
              border-radius: 50%;
              animation: spin 1s linear infinite;
            }
          }
        }
        
        .file-details {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 4px;
          
          .file-name {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-weight: 600;
            color: #2c3e50;
            font-size: 15px;
          }
          
          .temp-badge {
            display: flex;
            align-items: center;
            gap: 4px;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            width: fit-content;
            box-shadow: 0 2px 8px rgba(79, 172, 254, 0.3);
            animation: pulse 2s infinite;
            
            .badge-icon {
              font-size: 12px;
            }
          }
        }
      }
      
      .type-tag {
        display: inline-block;
        padding: 6px 12px;
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        color: #2c3e50;
        border-radius: 16px;
        font-size: 12px;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(168, 237, 234, 0.3);
      }
      
      .size-tag {
        display: flex;
        align-items: center;
        gap: 4px;
        font-weight: 600;
        
        .size-icon {
          font-size: 14px;
        }
      }
      
      .time-info {
        display: flex;
        align-items: center;
        gap: 6px;
        
        .time-icon {
          font-size: 14px;
          opacity: 0.7;
        }
        
        .time-text {
          font-size: 13px;
          color: #606266;
        }
      }
      
              .status-tag {
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 8px 12px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 600;
          min-width: 80px;
          
          .status-display {
            display: flex;
            align-items: center;
            gap: 4px;
          }
        
        &.status-success {
          background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
          color: #0d5f3c;
          box-shadow: 0 4px 12px rgba(132, 250, 176, 0.3);
        }
        
        &.status-process {
          background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
          color: #b45309;
          box-shadow: 0 4px 12px rgba(252, 182, 159, 0.3);
        }
        
        &.status-fail {
          background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
          color: #d63031;
          box-shadow: 0 4px 12px rgba(250, 177, 160, 0.3);
        }
        
        &.status-default {
          background: linear-gradient(135deg, #ddd6fe 0%, #e879f9 100%);
          color: #6b7280;
          box-shadow: 0 4px 12px rgba(221, 214, 254, 0.3);
        }
        
                  &.status-pulse {
            animation: pulse 2s infinite;
            
            .status-display {
              animation: rocketLaunch 2s infinite;
            }
          }
        
                  &.status-success-glow {
            animation: glow 2s infinite;
          }
        
        .rotating {
          animation: rotate 2s linear infinite;
        }
      }
      
      .action-buttons {
        display: flex;
        align-items: center;
        justify-content: center;
        
        .delete-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 16px;
          background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
          color: white;
          border: none;
          border-radius: 12px;
          cursor: pointer;
          font-size: 12px;
          font-weight: 600;
          transition: all 0.3s ease;
          box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
          
          .btn-icon {
            font-size: 14px;
          }
          
          .btn-text {
            font-size: 12px;
          }
          
          &:hover {
            background: linear-gradient(135deg, #ee5a52 0%, #e74c3c 100%);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
          }
          
          &:active {
            transform: translateY(0);
          }
        }
        
        .uploading-indicator {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 16px;
          background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
          color: white;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
          box-shadow: 0 4px 12px rgba(116, 185, 255, 0.3);
          
          .uploading-icon {
            font-size: 14px;
            animation: pulse 2s infinite;
          }
          
          .uploading-text {
            font-size: 12px;
          }
        }
      }
    }
    
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 500px;
      background: white;
      border-radius: 16px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
      padding: 40px;
      
      .empty-illustration {
        margin-bottom: 24px;
        
        .empty-cloud {
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
          
          .cloud-icon {
            font-size: 80px;
            opacity: 0.8;
          }
          
          .cloud-files {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            
            .file-float {
              font-size: 20px;
              animation: float 3s ease-in-out infinite;
              
              &:nth-child(1) {
                animation-delay: 0s;
              }
              
              &:nth-child(2) {
                animation-delay: 1s;
              }
              
              &:nth-child(3) {
                animation-delay: 2s;
              }
            }
          }
        }
      }
      
      .empty-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 24px;
        font-weight: 600;
        color: #2c3e50;
        margin: 0 0 12px 0;
        
        .title-icon {
          font-size: 28px;
        }
      }
      
      .empty-description {
        font-size: 16px;
        color: #606266;
        margin: 0 0 24px 0;
        text-align: center;
        line-height: 1.5;
      }
      
      .empty-features {
        display: flex;
        gap: 20px;
        margin-bottom: 32px;
        
        .feature-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          padding: 16px;
          background: linear-gradient(135deg, #f8f9ff 0%, #e3f2fd 100%);
          border-radius: 12px;
          min-width: 100px;
          
          .feature-icon {
            font-size: 24px;
          }
          
          .feature-text {
            font-size: 12px;
            color: #606266;
            font-weight: 500;
            text-align: center;
          }
        }
      }
      
      .empty-upload-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 12px;
        padding: 16px 32px;
        font-size: 16px;
        font-weight: 600;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
        
        .btn-icon {
          margin-right: 8px;
          font-size: 18px;
        }
        
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 12px 30px rgba(102, 126, 234, 0.4);
        }
      }
    }
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 0.7;
  }
  50% {
    transform: scale(1.05);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 0.7;
  }
}

@keyframes glow {
  0% {
    box-shadow: 0 0 5px rgba(255, 215, 0, 0.5);
  }
  50% {
    box-shadow: 0 0 10px rgba(255, 215, 0, 0.8);
  }
  100% {
    box-shadow: 0 0 5px rgba(255, 215, 0, 0.5);
  }
}

@keyframes shake {
  0%, 100% {
    transform: translateX(0);
  }
  20%, 60% {
    transform: translateX(-3px);
  }
  40%, 80% {
    transform: translateX(3px);
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes uploadPulse {
  0% {
    border-left-color: #409eff;
    background: linear-gradient(135deg, rgba(64, 158, 255, 0.1) 0%, rgba(100, 200, 255, 0.1) 100%);
  }
  50% {
    border-left-color: #74b9ff;
    background: linear-gradient(135deg, rgba(116, 185, 255, 0.15) 0%, rgba(132, 220, 255, 0.15) 100%);
  }
  100% {
    border-left-color: #409eff;
    background: linear-gradient(135deg, rgba(64, 158, 255, 0.1) 0%, rgba(100, 200, 255, 0.1) 100%);
  }
}

@keyframes float {
  0% {
    transform: translateY(0px) rotate(0deg);
    opacity: 0.7;
  }
  50% {
    transform: translateY(-10px) rotate(180deg);
    opacity: 1;
  }
  100% {
    transform: translateY(0px) rotate(360deg);
    opacity: 0.7;
  }
}

@keyframes rocketLaunch {
  0% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-3px);
  }
  100% {
    transform: translateY(0px);
  }
}

@keyframes syncWave {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

:deep(.el-upload) {
  display: inline-block;
}

.custom-confirm-dialog {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;

  .confirm-dialog-content {
    background-color: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
    text-align: center;
    width: 350px;
    max-width: 90%;

    .dialog-title {
      font-size: 20px;
      font-weight: 700;
      color: #333;
      margin-bottom: 16px;
    }

    .dialog-body {
      font-size: 16px;
      color: #555;
      margin-bottom: 24px;
      line-height: 1.6;
    }

    .dialog-footer {
      display: flex;
      justify-content: center;
      gap: 20px;

      .btn-cancel, .btn-confirm {
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
      }

      .btn-cancel {
        background-color: #f5f5f5;
        color: #333;
        border: 1px solid #ddd;
        
        &:hover {
          background-color: #e5e5e5;
        }
      }

      .btn-confirm {
        background-color: #f56c6c;
        color: white;
        border: none;
        
        &:hover {
          background-color: #ff8080;
          transform: scale(1.05);
        }
        
        &:active {
          transform: scale(0.95);
        }
      }
    }
  }
}
</style> 