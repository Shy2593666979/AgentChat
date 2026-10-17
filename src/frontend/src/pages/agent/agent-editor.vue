<script setup lang="ts">
import { modelProviderDisplayName } from '../../utils/model-provider-brand'
import ProviderLogo from "../../components/ProviderLogo.vue";
import { modelDisplayName } from "../../utils/model-display";
import UiIcon from '../../components/UiIcon.vue'
import AgentIdentity from '../../components/AgentIdentity.vue'
import { agentIcons, agentColors, automaticIdentity, identityUrl, parseIdentity, isLegacyAgentLogo } from '../../utils/agent-identity'
import CapabilityPicker from '../../components/CapabilityPicker.vue'
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Edit,
  Plus,
  Delete,
  VideoPlay,
  Check,
  ArrowDown,
  ArrowRight,
  ArrowLeft,
  ChatDotRound,
  Setting,
  DocumentCopy
} from '@element-plus/icons-vue'
import type { UploadProps, UploadUserFile } from 'element-plus'
import { createAgentAPI, updateAgentAPI, getAgentByIdAPI } from '../../apis/agent'
import { getVisibleLLMsAPI, getAgentModelsAPI, type LLMResponse } from '../../apis/llm'
import { getVisibleToolsAPI, type ToolResponse } from '../../apis/tool'
import { getMCPServersAPI, type MCPServer } from '../../apis/mcp-server'
import { getKnowledgeListAPI, type KnowledgeResponse } from '../../apis/knowledge'
import { getAgentSkillsAPI, type AgentSkill } from '../../apis/agent-skill'
import { Agent, AgentFormData } from '../../type'
import { uploadFileAPI } from '../../apis/file'

const route = useRoute()
const router = useRouter()

const emit = defineEmits<{
  update: []
}>()

// 响应式数据
const loading = ref(false)
const formRef = ref()
const isEditing = ref(false)
const editingBuiltin = ref(false)
const editingAgentId = ref('')
const fileList = ref<UploadUserFile[]>([])
const identityMode = ref<'auto' | 'preset' | 'upload'>('auto')
const chosenIcon = ref('bot'), chosenColor = ref('blue'), identityPickerOpen = ref(false)
const autoIdentity = computed(() => automaticIdentity(formData, toolOptions.value.filter(t => formData.tool_ids.includes(t.tool_id)).map(t => t.name).join(' ')))
const previewLogo = computed(() => identityMode.value === 'upload' ? formData.logo_url : identityMode.value === 'auto' ? identityUrl(autoIdentity.value.icon, autoIdentity.value.color, true) : identityUrl(chosenIcon.value, chosenColor.value))
function restoreIdentity() {
  const stored = parseIdentity(formData.logo_url)
  identityMode.value = stored ? stored.auto ? 'auto' : 'preset' : isLegacyAgentLogo(formData.logo_url) ? 'auto' : 'upload'
  chosenIcon.value = stored?.icon || 'bot'
  chosenColor.value = stored?.color || 'blue'
}
function selectIcon(icon: string) { chosenIcon.value = icon; identityMode.value = 'preset' }
function selectColor(color: string) { if (identityMode.value === 'auto') chosenIcon.value = autoIdentity.value.icon; chosenColor.value = color; identityMode.value = 'preset' }
function useAutomaticIcon() { identityMode.value = 'auto'; fileList.value = [] }


// 智能体表单数据
const formData = reactive<AgentFormData>({
  name: '',
  description: '',
  logo_url: '',
  tool_ids: [],
  llm_id: '',
  mcp_ids: [],
  system_prompt: '',
  knowledge_ids: [],
  agent_skill_ids: [],
  enable_memory: false
})

// 折叠面板状态
const collapseItems = ref({
  basic: false,
  aiModel: true,
  memory: false,
  knowledge: false,
  tools: false,
  mcp: false,
  skills: false
})

// 选项数据
const llmOptions = ref<Array<LLMResponse & { name: string }>>([])
const toolOptions = ref<Array<ToolResponse & { name: string; icon?: string }>>([])
const mcpOptions = ref<Array<MCPServer & { name: string; icon?: string }>>([])
const agentSkillOptions = ref<Array<AgentSkill & { name: string; icon: string }>>([])
const knowledgeOptions = ref<Array<KnowledgeResponse & {
  knowledge_id: string
  knowledge_name: string
  knowledge_desc: string
  name: string
  icon: string
}>>([])

// 数据加载状态
const resourceErrors = reactive({ llm: '', tool: '', mcp: '', agentSkill: '', knowledge: '' })
const dataLoading = ref({
  llm: false,
  tool: false,
  mcp: false,
  agentSkill: false,
  knowledge: false
})

// 表单验证规则
const rules = computed(() => ({
  name: [{ required: true, message: '请输入智能体名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入智能体描述', trigger: 'blur' }],
  system_prompt: [{ required: !editingBuiltin.value, message: '请输入系统提示词', trigger: 'blur' }],
  llm_id: [{ required: true, message: '请选择大模型', trigger: 'change' }]
}))





// 方法
const loadAgent = (agent?: Agent) => {
  if (agent) {
    console.log('📝 加载智能体数据进行编辑:', agent)
    isEditing.value = true
    editingBuiltin.value = agent.is_custom === false
    editingAgentId.value = agent.agent_id

    // 处理knowledge_ids字段映射 - 确保与选择器的value一致
    const processedKnowledgeIds = Array.isArray(agent.knowledge_ids)
      ? agent.knowledge_ids.filter(id => id) // 过滤空值
      : []

    // 处理tool_ids字段映射 - 确保与选择器的value一致
    const processedToolIds = Array.isArray(agent.tool_ids)
      ? agent.tool_ids.filter(id => id) // 过滤空值
      : []

    // 处理mcp_ids字段映射 - 确保与选择器的value一致
    const processedMcpIds = Array.isArray(agent.mcp_ids)
      ? agent.mcp_ids.filter(id => id) // 过滤空值
      : []

    // 处理agent_skill_ids字段映射 - 确保与选择器的value一致
    const processedAgentSkillIds = Array.isArray(agent.agent_skill_ids)
      ? agent.agent_skill_ids.filter(id => id) // 过滤空值
      : []

    Object.assign(formData, {
      name: agent.name || '',
      description: agent.description || '',
      logo_url: agent.logo_url || '',
      tool_ids: processedToolIds,
      llm_id: agent.llm_id || '',
      mcp_ids: processedMcpIds,
      system_prompt: agent.system_prompt || '',
      knowledge_ids: processedKnowledgeIds,
      agent_skill_ids: processedAgentSkillIds,
      enable_memory: agent.enable_memory || false
    })

    restoreIdentity()
    console.log('✅ 表单数据已更新:', formData)
    console.log('🔧 当前工具选项:', toolOptions.value.map(t => ({ id: t.tool_id, name: t.name })))
    console.log('📚 当前知识库选项:', knowledgeOptions.value.map(k => ({ id: k.knowledge_id, name: k.name })))
    console.log('🤖 当前MCP选项:', mcpOptions.value.map(m => ({ id: m.mcp_server_id, name: m.name })))
    console.log('🧠 当前大模型选项:', llmOptions.value.map(l => ({ id: l.llm_id, name: l.name })))

    // 延迟验证ID匹配性，确保选择器已渲染
    setTimeout(() => {
      validateIdMatching()
    }, 100)

    if (agent.logo_url) {
      fileList.value = [{
        name: 'avatar',
        url: agent.logo_url
      }]
    } else {
      fileList.value = []
    }
  } else {
    console.log('🆕 创建新智能体，重置表单数据')
    isEditing.value = false
    editingBuiltin.value = false
    editingAgentId.value = ''

    // 重置为默认值
    Object.assign(formData, {
      name: '',
      description: '',
      logo_url: '',
      tool_ids: [],
      llm_id: '',
      mcp_ids: [],
      system_prompt: '',
      knowledge_ids: [],
      agent_skill_ids: [],
      enable_memory: false
    })
    fileList.value = []
    restoreIdentity()
    console.log('✅ 表单已重置为创建模式')
  }
}

// 切换折叠面板
const toggleCollapse = (key: keyof typeof collapseItems.value) => {
  collapseItems.value[key] = !collapseItems.value[key]
}



// 上传相关
const uploadLoading = ref(false)

const handleFileChange: UploadProps['onChange'] = async (uploadFile) => {
  if (uploadFile.raw) {
    const file = uploadFile.raw
    // 文件大小和类型检查
    const isLt2M = file.size / 1024 / 1024 < 2
    if (!isLt2M) {
      ElMessage.error('上传头像图片大小不能超过 2MB!')
      return
    }
    const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png'
    if (!isJpgOrPng) {
      ElMessage.error('上传头像图片只能是 JPG/PNG 格式!')
      return
    }

    // 开始上传
    uploadLoading.value = true
    try {
      const uploadFormData = new FormData()
      uploadFormData.append('file', file)

      const response = await uploadFileAPI(uploadFormData)

      if (response.data.status_code === 200) {
        formData.logo_url = response.data.data
        identityMode.value = 'upload'
        ElMessage.success('头像上传成功')
      } else {
        ElMessage.error(response.data.status_message || '头像上传失败')
      }
    } catch (error) {
      console.error('头像上传失败:', error)
      ElMessage.error('头像上传失败')
    } finally {
      uploadLoading.value = false
    }
  }
}

const handleFileRemove: UploadProps['onRemove'] = () => {
  identityMode.value = 'auto'
  formData.logo_url = ''
}

// 保存智能体
const saveAgent = async () => {
  if (loading.value || uploadLoading.value) return
  loading.value = true
  try {
    // 表单验证
    const valid = await formRef.value?.validate().catch(() => false)
    if (!valid) {
      activeEditorTab.value = 'basic'
      ElMessage.warning('请完善必填信息后再提交')
      return
    }

    loading.value = true

    // 构建请求数据，确保字段正确
    const requestData = {
      name: formData.name,
      description: formData.description,
      logo_url: previewLogo.value,
      tool_ids: formData.tool_ids,
      llm_id: formData.llm_id,
      mcp_ids: formData.mcp_ids,
      system_prompt: formData.system_prompt,
      knowledge_ids: formData.knowledge_ids,
      agent_skill_ids: formData.agent_skill_ids,
      enable_memory: formData.enable_memory
    }

    if (isEditing.value) {
      // 确保agent_id字段存在
      if (!editingAgentId.value) {
        ElMessage.error('缺少智能体ID，无法更新')
        loading.value = false
        return
      }

      // 将agent_id添加到请求数据中
      const updateData = {
        agent_id: editingAgentId.value,
        ...requestData
      }

      console.log('更新智能体数据:', updateData)
      const response = await updateAgentAPI(updateData)

      if (response.data.status_code === 200) {
        ElMessage.success('智能体更新成功')
        // 保存成功后跳转到智能体列表页
        router.push(route.query.from === 'explore' ? '/homepage' : '/agent')
      } else {
        ElMessage.error(response.data.status_message || '更新失败')
      }
    } else {
      console.log('创建智能体数据:', requestData)
      const response = await createAgentAPI(requestData)

      if (response.data.status_code === 200) {
        ElMessage.success('智能体创建成功')
        // 保存成功后跳转到智能体列表页
        router.push(route.query.from === 'explore' ? '/homepage' : '/agent')
      } else {
        ElMessage.error(response.data.status_message || '创建失败')
      }
    }
  } catch (error: any) {
    console.error('操作失败:', error)
    if (error.response?.data?.status_message) {
      ElMessage.error(error.response.data.status_message)
    } else if (error.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    } else {
      ElMessage.error(isEditing.value ? '智能体更新失败' : '智能体创建失败')
    }
  } finally {
    loading.value = false
  }
}





// 加载大模型数据
const loadLLMOptions = async () => {
  try {
    dataLoading.value.llm = true
    resourceErrors.llm = ''
    console.log('🔄 开始加载大模型数据...')

    // 优先使用智能体专用的大模型API
    let response
    try {
      response = await getAgentModelsAPI()
      console.log('📡 智能体大模型API响应:', response)
    } catch (error) {
      console.log('⚠️ 智能体大模型API失败，尝试使用通用API:', error)
      response = await getVisibleLLMsAPI()
      console.log('📡 通用大模型API响应:', response)
    }

    if (response.data.status_code === 200) {
      const rawData = response.data.data
      console.log('📦 原始大模型数据:', rawData)

      // 处理数据结构：可能是 Record<string, LLMResponse[]> 或直接的 LLMResponse[]
      let llmArray: LLMResponse[] = []

      if (Array.isArray(rawData)) {
        // 如果是直接数组（智能体API返回的）
        llmArray = rawData
      } else if (typeof rawData === 'object' && rawData !== null) {
        // 如果是对象（通用API返回的），提取LLM类型的模型
        if (rawData.LLM && Array.isArray(rawData.LLM)) {
          llmArray = rawData.LLM
        } else {
          // 如果没有LLM字段，尝试提取所有值并合并
          llmArray = Object.values(rawData).flat() as LLMResponse[]
        }
      }

      console.log('模型列表数量:', llmArray.length)

      llmOptions.value = llmArray.map(llm => ({
        ...llm,
        name: `${modelDisplayName(llm)} (${modelProviderDisplayName(llm.provider)})`
      }))

      console.log(`✅ 成功加载 ${llmOptions.value.length} 个大模型`)
      console.log('模型选项数量:', llmOptions.value.length)
      // 新建模式下默认选第一个
      if (!isEditing.value && !formData.llm_id && llmOptions.value.length > 0) {
        formData.llm_id = llmOptions.value[0].llm_id
      }
    } else {
      resourceErrors.llm = '模型加载失败，请重试'
      console.error('❌ 大模型API返回错误:', response.data.status_message)
      ElMessage.error(`加载大模型失败: ${response.data.status_message}`)
    }
  } catch (error) {
    resourceErrors.llm = '加载失败，请重试'
    console.error('❌ 加载大模型失败:', error)
    ElMessage.error('加载大模型列表失败')
  } finally {
    dataLoading.value.llm = false
  }
}

// 加载工具数据
const loadToolOptions = async () => {
  try {
    dataLoading.value.tool = true
    resourceErrors.tool = ''
    console.log('🔄 开始加载工具数据...')

    const response = await getVisibleToolsAPI()
    console.log('📡 工具API响应:', response)

    if (response.data.status_code === 200) {
      const rawData = response.data.data
      console.log('📦 原始工具数据:', rawData)

      toolOptions.value = rawData.map(tool => ({
        ...tool,
        name: tool.display_name || tool.name
      }))

      console.log(`✅ 成功加载 ${toolOptions.value.length} 个工具`)
      console.log('🔧 处理后的工具数据:', toolOptions.value)
    } else {
      resourceErrors.tool = '工具加载失败，请重试'
      console.error('❌ 工具API返回错误:', response.data.status_message)
    }
  } catch (error) {
    resourceErrors.tool = '加载失败，请重试'
    console.error('❌ 加载工具失败:', error)
    ElMessage.error('加载工具列表失败')
  } finally {
    dataLoading.value.tool = false
  }
}

// 加载MCP服务器数据
const loadMCPOptions = async () => {
  try {
    dataLoading.value.mcp = true
    resourceErrors.mcp = ''
    const response = await getMCPServersAPI()

    // 处理不同的响应格式
    let mcpData: MCPServer[] = []
    if (response.data.status_code !== 200) throw new Error(response.data.status_message || '加载失败')
    if (response.data.status_code === 200) {
      // 检查data字段是否存在且不为null
      if (response.data.data && Array.isArray(response.data.data)) {
        mcpData = response.data.data
      }
    }

    mcpOptions.value = mcpData.map(mcp => ({
      ...mcp,
      name: mcp.server_name
    }))
    console.log(`✅ 成功加载 ${mcpOptions.value.length} 个MCP服务器`)
  } catch (error) {
    resourceErrors.mcp = '加载失败，请重试'
    console.error('加载MCP服务器失败:', error)
    ElMessage.error('加载MCP服务器列表失败')
  } finally {
    dataLoading.value.mcp = false
  }
}

// 加载Agent Skill数据
const loadAgentSkillOptions = async () => {
  try {
    dataLoading.value.agentSkill = true
    resourceErrors.agentSkill = ''
    const response = await getAgentSkillsAPI()

    if (response.data.status_code !== 200) throw new Error(response.data.status_message || '加载失败')
    if (response.data.status_code === 200) {
      const skillData = response.data.data || []
      agentSkillOptions.value = skillData.map(skill => ({
        ...skill,
        name: skill.name,
        icon: '🎯'
      }))
      console.log(`✅ 成功加载 ${agentSkillOptions.value.length} 个Agent Skill`)
    }
  } catch (error) {
    resourceErrors.agentSkill = '加载失败，请重试'
    console.error('加载Agent Skill失败:', error)
    ElMessage.error('加载Agent Skill列表失败')
  } finally {
    dataLoading.value.agentSkill = false
  }
}

// 加载知识库数据
const loadKnowledgeOptions = async () => {
  try {
    dataLoading.value.knowledge = true
    resourceErrors.knowledge = ''
    const response = await getKnowledgeListAPI()
    if (response.data.status_code !== 200) throw new Error(response.data.status_message || '加载失败')
    if (response.data.status_code === 200) {
      knowledgeOptions.value = response.data.data.map(knowledge => ({
        ...knowledge,
        knowledge_id: knowledge.id,           // 映射 id -> knowledge_id
        knowledge_name: knowledge.name,       // 映射 name -> knowledge_name
        knowledge_desc: knowledge.description, // 映射 description -> knowledge_desc
        name: knowledge.name,                 // 用于显示的名称
        icon: getKnowledgeIcon(knowledge.name)
      }))
      console.log(`✅ 成功加载 ${knowledgeOptions.value.length} 个知识库`)
    }
  } catch (error) {
    resourceErrors.knowledge = '加载失败，请重试'
    console.error('加载知识库失败:', error)
    ElMessage.error('加载知识库列表失败')
  } finally {
    dataLoading.value.knowledge = false
  }
}



// 获取知识库图标
const getKnowledgeIcon = (knowledgeName: string): string => {
  const iconMap: { [key: string]: string } = {
    '文档': '📚',
    '手册': '📖',
    '问题': '❓',
    '技术': '⚙️',
    '产品': '📦'
  }

  for (const [key, icon] of Object.entries(iconMap)) {
    if (knowledgeName.includes(key)) {
      return icon
    }
  }
  return '📄'
}

// 验证ID匹配性
const validateIdMatching = () => {
  // 验证大模型ID匹配
  if (formData.llm_id) {
    const llmExists = llmOptions.value.some(llm => llm.llm_id === formData.llm_id)
    if (!llmExists) {
      console.warn('⚠️ 大模型ID不匹配:', formData.llm_id, '可用选项:', llmOptions.value.map(l => l.llm_id))
    }
  }

  // 验证工具ID匹配
  if (formData.tool_ids.length > 0) {
    const toolOptionsIds = toolOptions.value.map(t => t.tool_id)
    const unmatchedToolIds = formData.tool_ids.filter(id => !toolOptionsIds.includes(id))
    if (unmatchedToolIds.length > 0) {
      console.warn('⚠️ 工具ID不匹配:', unmatchedToolIds, '可用选项:', toolOptionsIds)
    }
  }

  // 验证知识库ID匹配
  if (formData.knowledge_ids.length > 0) {
    const knowledgeOptionsIds = knowledgeOptions.value.map(k => k.knowledge_id)
    const unmatchedKnowledgeIds = formData.knowledge_ids.filter(id => !knowledgeOptionsIds.includes(id))
    if (unmatchedKnowledgeIds.length > 0) {
      console.warn('⚠️ 知识库ID不匹配:', unmatchedKnowledgeIds, '可用选项:', knowledgeOptionsIds)
    }
  }

  // 验证MCP ID匹配
  if (formData.mcp_ids.length > 0) {
    const mcpOptionsIds = mcpOptions.value.map(m => m.mcp_server_id)
    const unmatchedMcpIds = formData.mcp_ids.filter(id => !mcpOptionsIds.includes(id))
    if (unmatchedMcpIds.length > 0) {
      console.warn('⚠️ MCP ID不匹配:', unmatchedMcpIds, '可用选项:', mcpOptionsIds)
    }
  }
}

// 从API加载智能体数据
const loadAgentFromAPI = async (agentId: string) => {
  try {
    loading.value = true
    // ElMessage.info('正在加载智能体数据...')

    const response = await getAgentByIdAPI(agentId)
    if (response.data.status_code === 200 && response.data.data) {
      const agentData = response.data.data as any
      // console.log('🔍 API返回的智能体原始数据:', agentData)

      // 转换API数据为Agent类型，兼容 id 和 agent_id
      const agent: Agent = {
        agent_id: agentData.id || agentData.agent_id,
        is_custom: agentData.is_custom,
        name: agentData.name,
        description: agentData.description,
        logo_url: agentData.logo_url,
        tool_ids: agentData.tool_ids || [],
        llm_id: agentData.llm_id,
        mcp_ids: agentData.mcp_ids || [],
        system_prompt: agentData.system_prompt,
        knowledge_ids: agentData.knowledge_ids || [],
        agent_skill_ids: agentData.agent_skill_ids || [],
        enable_memory: agentData.enable_memory,
        created_time: new Date().toISOString()
      }

      // console.log('🔄 转换后的智能体数据:', agent)
      loadAgent(agent)
      ElMessage.success('智能体数据加载成功')
    } else {
      ElMessage.error(response.data.status_message || '智能体不存在')
      goBack()
    }
  } catch (error) {
    console.error('加载智能体失败:', error)
    ElMessage.error('加载智能体数据失败')
    goBack()
  } finally {
    loading.value = false
  }
}

// 返回智能体列表
const goBack = () => {
  router.push(route.query.from === 'explore' ? '/homepage' : '/agent')
}

// 初始化数据
const initializeData = async () => {
  console.log('🔄 开始初始化数据...')

  try {
    await Promise.all([
      loadLLMOptions(),
      loadToolOptions(),
      loadMCPOptions(),
      loadAgentSkillOptions(),
      loadKnowledgeOptions()
    ])

    console.log('✅ 数据初始化完成')
    console.log('📊 数据统计:')
    console.log('  - 大模型:', llmOptions.value.length, '个')
    console.log('  - 工具:', toolOptions.value.length, '个')
    console.log('  - MCP:', mcpOptions.value.length, '个')
    console.log('  - Agent Skill:', agentSkillOptions.value.length, '个')
    console.log('  - 知识库:', knowledgeOptions.value.length, '个')

  } catch (error) {
    console.error('❌ 数据初始化失败:', error)
  }
}

onMounted(async () => {
  console.log('📱 页面加载开始...')
  console.log('🔍 当前路由参数:', route.query)

  // 先加载选项数据，这是前提条件
  console.log('⏳ 正在加载选项数据...')
  await initializeData()
  console.log('✅ 选项数据加载完成')

  // 確保所有選項數據都加載完成後，再加載智能體數據
  const agentId = route.query.id as string
  if (agentId) {
    console.log('🔄 开始加载智能体数据，ID:', agentId, '类型:', typeof agentId)
    await loadAgentFromAPI(agentId)
  } else {
    console.log('🆕 创建新智能体模式')
    // 创建模式下，清空表单并设置默认值
    loadAgent()
    // 确保默认选中第一个模型
    if (!formData.llm_id && llmOptions.value.length > 0) {
      formData.llm_id = llmOptions.value[0].llm_id
    }
  }


})

defineExpose({ loadAgent })

const activeEditorTab = ref('basic')
const expandedPrompt = ref(false), promptTemplateOpen = ref(false), avatarFailed = ref(false)
watch(() => formData.logo_url, () => { avatarFailed.value = false })
const editorTabs = [{ id: 'basic', label: '基础信息' }, { id: 'prompt', label: '提示词' }, { id: 'advanced', label: '高级设置' }]
const capabilityGroups = computed(() => [
  { field: 'tool_ids' as const, label: '工具', icon: 'cube', managePath: '/tool', loading: dataLoading.value.tool, error: resourceErrors.tool, retry: loadToolOptions, options: toolOptions.value.map(item => ({ id: item.tool_id, name: item.name })) },
  { field: 'mcp_ids' as const, label: 'MCP', icon: 'connect', managePath: '/mcp-server', loading: dataLoading.value.mcp, error: resourceErrors.mcp, retry: loadMCPOptions, options: mcpOptions.value.map(item => ({ id: item.mcp_server_id, name: item.name })) },
  { field: 'agent_skill_ids' as const, label: 'Skill', icon: 'layers', managePath: '/agent-skill', loading: dataLoading.value.agentSkill, error: resourceErrors.agentSkill, retry: loadAgentSkillOptions, options: agentSkillOptions.value.map(item => ({ id: item.id, name: item.name })) },
  { field: 'knowledge_ids' as const, label: '知识库', icon: 'book', managePath: '/knowledge', loading: dataLoading.value.knowledge, error: resourceErrors.knowledge, retry: loadKnowledgeOptions, options: knowledgeOptions.value.map(item => ({ id: item.knowledge_id, name: item.name })) }
])
const selectedModel = computed(() => llmOptions.value.find(model => model.llm_id === formData.llm_id))
const promptTemplates = [
  { title: '深度研究助手', description: '明确问题、收集资料、核验事实并整理研究报告', prompt: '你是一位专业的研究助手。先明确用户的研究目标和范围，再收集并核验信息，区分事实和推断，最后提供结构清晰、注明来源的研究报告。信息不足时先提出必要的问题。' },
  { title: '写作助手', description: '根据受众、目标与语气，撰写和修改内容', prompt: '你是一位写作助手。先理解内容的用途、目标受众、语气和格式要求，再组织结构并撰写内容。修改时保留原意，使用简洁、自然的语言，避免编造事实。' },
  { title: '数据分析助手', description: '检查数据质量、分析趋势并提出可验证的结论', prompt: '你是一位数据分析助手。先检查数据字段、单位、缺失值与异常值，再依据用户目标开展分析。说明方法、关键发现及其局限，区分相关性与因果关系，并提出可执行的建议。' }
]
async function applyPromptTemplate(template: typeof promptTemplates[number]) {
  try {
    if (formData.system_prompt.trim()) await ElMessageBox.confirm('应用模板将替换当前系统提示词，是否继续？', '应用提示词模板', { confirmButtonText: '替换', cancelButtonText: '取消' })
    formData.system_prompt = template.prompt
    promptTemplateOpen.value = false
  } catch { /* Keep the current prompt when the dialog is dismissed. */ }
}
</script>

<template>
  <div class="b2-agent-editor" v-loading="loading">
    <svg class="sprite" xmlns="http://www.w3.org/2000/svg"><defs>
<symbol id="i-home" viewBox="0 0 24 24"><path d="M3 10.5 12 3l9 7.5M5 9v11h5v-7h4v7h5V9" fill="currentColor" stroke="currentColor" opacity=".72"/></symbol>
<symbol id="i-search" viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="7.5"/><path d="m16 16 5 5"/></symbol>
<symbol id="i-chat" viewBox="0 0 24 24"><path d="M21 11.5a9 9 0 0 1-9 9H3l1.7-4.4A9 9 0 1 1 21 11.5Z"/><path d="M8 11.5h.01m4 0h.01m4 0h.01" stroke-width="2.7"/></symbol>
<symbol id="i-robot" viewBox="0 0 24 24"><rect x="4" y="6.5" width="16" height="14" rx="4"/><path d="M12 3v3M1.5 11v5M22.5 11v5M9 16.5c1.7 1.3 4.3 1.3 6 0"/><path d="M8.5 11.5v1m7-1v1" stroke-width="2.5"/><circle cx="12" cy="2.5" r=".8" fill="currentColor"/></symbol>
<symbol id="i-link" viewBox="0 0 24 24"><path d="m9.5 7.5 3-3a5 5 0 0 1 7 7l-4 4a5 5 0 0 1-7 0M14.5 16.5l-3 3a5 5 0 0 1-7-7l4-4a5 5 0 0 1 7 0M8.5 15.5l7-7"/></symbol>
<symbol id="i-cube" viewBox="0 0 24 24"><path d="m12 2 9 5v10l-9 5-9-5V7l9-5Zm0 10 9-5M12 12 3 7m9 5v10"/></symbol>
<symbol id="i-book" viewBox="0 0 24 24"><path d="M12 5v16M12 5C8 1.5 2 3 2 4v15c4-1.5 7-1 10 2 3-3 6-3.5 10-2V4c0-1-6-2.5-10 1Z"/></symbol>
<symbol id="i-chart" viewBox="0 0 24 24"><path d="M4 21V12m8 9V4m8 17V8" stroke-width="2.7"/></symbol>
<symbol id="i-grid" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="2.5"/><rect x="14" y="3" width="7" height="7" rx="2.5"/><rect x="3" y="14" width="7" height="7" rx="2.5"/><rect x="14" y="14" width="7" height="7" rx="2.5"/></symbol>
<symbol id="i-layers" viewBox="0 0 24 24"><path d="m12 2 10 6-10 6L2 8l10-6Zm10 11-10 6-10-6m20 5-10 6-10-6" transform="translate(0 -1)"/></symbol>
<symbol id="i-arrow" viewBox="0 0 24 24"><path d="M19 12H5m7-7-7 7 7 7"/></symbol>
<symbol id="i-chevron" viewBox="0 0 24 24"><path d="m5 9 7 7 7-7"/></symbol>
<symbol id="i-collapse" viewBox="0 0 24 24"><path d="m12 5-7 7 7 7m6-14-7 7 7 7"/></symbol>
<symbol id="i-tools" viewBox="0 0 24 24"><path d="M14 3a6 6 0 0 0-5 8L3 17a2.8 2.8 0 0 0 4 4l6-6a6 6 0 0 0 8-7l-4 4-4-4 4-4a6 6 0 0 0-3-1Z"/><path d="m3 3 4 4M3 2l-1 1 3 4 2-2M17 17l4 4m-5-3 3-3"/></symbol>
<symbol id="i-toolbox" viewBox="0 0 24 24"><path d="m4 7 8-3 8 3v11l-8 4-8-4V7Zm5-2V2h6v3m-3-1v4"/></symbol>
<symbol id="i-plus" viewBox="0 0 24 24"><path d="M12 4v16M4 12h16"/></symbol>
<symbol id="i-x" viewBox="0 0 24 24"><path d="m6 6 12 12M6 18 18 6"/></symbol>
<symbol id="i-globe" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18M5 6.5h14M5 17.5h14"/></symbol>
<symbol id="i-file" viewBox="0 0 24 24"><path d="M5 3h10l4 4v14H5V3Zm9 0v5h5M9 12h6m-6 4h6"/></symbol>
<symbol id="i-code" viewBox="0 0 24 24"><path d="m7 7-5 5 5 5m10-10 5 5-5 5m-4-9-2 8"/></symbol>
<symbol id="i-edit" viewBox="0 0 24 24"><path d="M10 4H4v16h16v-7M9 15l1-5L19 1l4 4-9 9-5 1Zm8-12 4 4"/></symbol>
<symbol id="i-folder" viewBox="0 0 24 24"><path d="M2 7V4h8l2 3h10v14H2V7Z"/><path d="M2 9h20" stroke="#fff" stroke-width="1"/></symbol>
<symbol id="i-database" viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="8" ry="3.5"/><path d="M4 5v14c0 4.5 16 4.5 16 0V5M4 12c0 4.5 16 4.5 16 0"/></symbol>
<symbol id="i-expand" viewBox="0 0 24 24"><path d="M15 3h6v6m0-6-7 7M9 21H3v-6m0 6 7-7"/></symbol>
<symbol id="i-template" viewBox="0 0 24 24"><path d="M4 5h3v3H4zM4 11h3v3H4zM4 17h3v3H4z" fill="currentColor" stroke="none"/><path d="M11 5h9m-9 6h9m-9 6h9M14 3v17" stroke-width="2"/></symbol>
<symbol id="i-camera" viewBox="0 0 24 24"><path d="M3 7h5l2-3h4l2 3h5v14H3V7Z"/><circle cx="12" cy="13" r="4"/></symbol>
<symbol id="i-menu" viewBox="0 0 24 24"><path d="M3 6h18M3 12h18M3 18h18"/></symbol>
<symbol id="logo" viewBox="0 0 40 40"><defs><linearGradient id="logo-bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#3d8aff"/><stop offset="1" stop-color="#034aff"/></linearGradient></defs><rect x="1" y="1" width="38" height="38" rx="10" fill="url(#logo-bg)"/><rect x="3" y="3" width="34" height="34" rx="8" fill="none" stroke="#75adff" stroke-opacity=".45"/><path d="M13 15c0-5 14-5 14 0v1h2v11H11V16h2Z" fill="#fff"/><rect x="9" y="16" width="22" height="13" rx="6" fill="#fff"/><rect x="15" y="19" width="3" height="5" rx="1.5" fill="#316aff"/><rect x="22" y="19" width="3" height="5" rx="1.5" fill="#316aff"/><circle cx="29" cy="10" r="2.5" fill="#fff"/></symbol>
<symbol id="avatar" viewBox="0 0 122 120"><defs><linearGradient id="av-bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#c280ff"/><stop offset=".48" stop-color="#8e78ff"/><stop offset="1" stop-color="#485bff"/></linearGradient><linearGradient id="av-body" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fff"/><stop offset="1" stop-color="#eeebff"/></linearGradient><linearGradient id="av-eye" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#6652ff"/><stop offset="1" stop-color="#447bff"/></linearGradient><filter id="av-shadow"><feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#4435d8" flood-opacity=".3"/></filter></defs><rect width="122" height="120" rx="28" fill="url(#av-bg)"/><path d="M0 23C29 43 35 22 23 0H0Zm50-23c-8 31 6 43 31 40s24-18 41-12V0ZM0 70c28-21 43-25 48-8S31 89 17 98s-4 16 8 22H0Z" fill="#d9a3ff" opacity=".25"/><path d="M70 120c-15-23 3-25 25-43s20-18 27-20v63Z" fill="#bec3ff" opacity=".3"/><path d="M8 44c-10 20 3 23 22 11s26-9 22-30C42 50 24 17 8 44ZM37 113c-6-18 19-22 20-38s15-22 29-19-18 25-16 38-10 22-33 19Z" fill="#7942ff" opacity=".26"/><circle cx="103" cy="27" r="17" fill="#a8a6ff" opacity=".18"/><path d="M91 19c1 5 3 7 7 8-5 1-6 3-7 7-1-4-3-6-7-7 4-1 6-3 7-8Z" fill="white"/><g filter="url(#av-shadow)"><rect x="29" y="51" width="7" height="24" rx="3.5" fill="#fff" opacity=".7"/><rect x="86" y="51" width="7" height="24" rx="3.5" fill="#fff" opacity=".7"/><rect x="34" y="39" width="54" height="48" rx="16" fill="url(#av-body)"/><rect x="57" y="24" width="7" height="15" rx="3.5" fill="#ffbe68"/><circle cx="60.5" cy="25" r="4" fill="#ffbf70"/><path d="M45 38c0-4 32-4 32 0" stroke="#fff" stroke-width="3" fill="none" opacity=".6"/><rect x="45" y="52" width="9" height="12" rx="4.5" fill="url(#av-eye)"/><rect x="67" y="52" width="9" height="12" rx="4.5" fill="url(#av-eye)"/><path d="M54 72c4 3 10 3 14 0" stroke="#6564ff" stroke-width="6" stroke-linecap="round" fill="none"/></g><rect x="38" y="44" width="7" height="37" rx="3.5" fill="#fff" opacity=".42"/></symbol>
<symbol id="deepseek" viewBox="0 0 32 24"><path d="M5 8c3-5 10-5 15-1 4 4 7 2 9-1 0 6-3 9-7 9 0 4-4 7-8 6C6 20 1 14 3 9l2-1Z" fill="#5357ff"/><path d="M6 9c4 1 7 4 10 9M11 8c-1 5 3 8 8 9" stroke="#fff" stroke-width="1.1" fill="none"/><path d="m20 6 7-4-1 7M7 19l-4 3 7-1" fill="#7775ff"/><circle cx="19" cy="9" r="1" fill="white"/></symbol>
<symbol id="notion" viewBox="0 0 24 24"><path d="m3 3 13-1 5 3v17L5 23l-3-4V4Z" fill="#fff" stroke="#111" stroke-width="1.5"/><path d="m3 3 3 3 15-1M6 6v16" fill="none" stroke="#111" stroke-width="1.4"/><path d="M8 18V8h2l6 8V7h2v12h-2L10 11v7Z" fill="#111"/></symbol>
<symbol id="github" viewBox="0 0 24 24"><path fill="#080b0e" d="M12 .5a12 12 0 0 0-3.8 23.4c.6.1.8-.3.8-.6v-2.4c-3.3.7-4-1.4-4-1.4-.6-1.4-1.3-1.8-1.3-1.8-1.1-.8.1-.8.1-.8 1.2.1 1.8 1.2 1.8 1.2 1.1 1.9 2.8 1.3 3.5 1 .1-.8.4-1.3.8-1.6-2.7-.3-5.5-1.3-5.5-5.9 0-1.3.5-2.4 1.2-3.2-.1-.3-.5-1.6.1-3.2 0 0 1-.3 3.3 1.2a11.6 11.6 0 0 1 6 0c2.3-1.5 3.3-1.2 3.3-1.2.6 1.6.2 2.9.1 3.2.8.8 1.2 1.9 1.2 3.2 0 4.6-2.8 5.6-5.5 5.9.4.4.8 1.1.8 2.2v3.4c0 .3.2.7.8.6A12 12 0 0 0 12 .5Z"/></symbol>
</defs></svg>
    <header class="page-header">
      <div><div class="breadcrumb"><button @click="goBack" aria-label="返回列表">←</button><span>{{ route.query.from === 'explore' ? '我的助手' : '智能体' }}</span><span>/</span><span class="current">{{ formData.name || '新建智能体' }}</span></div><h1>{{ isEditing ? '编辑智能体' : '创建智能体' }}</h1></div>
      <div class="page-actions"><el-button @click="goBack" :disabled="loading || uploadLoading">取消</el-button><el-button type="primary" @click="saveAgent" :loading="loading" :disabled="uploadLoading">{{ isEditing ? '保存配置' : '创建智能体' }}</el-button></div>
    </header>
    <el-form ref="formRef" :model="formData" :rules="rules" label-position="top" class="editor-grid" :disabled="loading">
      <section class="card editor-card">
        <div class="editor-tabs" role="group" aria-label="智能体设置分区"><button v-for="tab in editorTabs" :key="tab.id" type="button" class="editor-tab" :class="{ active: activeEditorTab === tab.id }" :aria-pressed="activeEditorTab === tab.id" @click="activeEditorTab = tab.id">{{ tab.label }}</button></div>
        <div v-show="activeEditorTab === 'basic'" class="basic-fields">
          <div class="identity-editor"><label class="field-label">智能体图标</label><button type="button" class="identity-preview" aria-label="选择智能体图标" @click="identityPickerOpen = true"><AgentIdentity :agent="{ ...formData, logo_url: previewLogo }"/><span class="identity-edit"><UiIcon name="edit"/></span></button><button type="button" class="identity-choose" @click="identityPickerOpen = true">图标与颜色</button><span class="identity-mode">{{ identityMode === 'auto' ? '自动匹配' : identityMode === 'preset' ? '内置图标' : '自定义图片' }}</span></div>
          <div><el-form-item label="名称" prop="name"><el-input v-model="formData.name" maxlength="50" show-word-limit placeholder="为智能体起个名字"/></el-form-item><el-form-item label="描述" prop="description"><el-input v-model="formData.description" type="textarea" :rows="3" maxlength="200" show-word-limit placeholder="描述它可以帮助你完成的任务"/></el-form-item></div>
        </div>
        <div v-show="activeEditorTab !== 'advanced'" class="prompt-section"><div class="prompt-toolbar"><button class="template-button" type="button" @click="promptTemplateOpen = true"><UiIcon name="grid"/>提示词模板</button><button class="expand-button" type="button" aria-label="放大系统提示词编辑器" @click="expandedPrompt = true"><UiIcon name="expand"/></button></div><el-form-item label="系统提示词" prop="system_prompt"><el-input v-model="formData.system_prompt" type="textarea" :rows="20" class="prompt-field" placeholder="定义智能体的角色、目标、工作流程和输出要求…"/><p class="prompt-count">{{ formData.system_prompt.length }} 字符</p></el-form-item></div>
        <section v-show="activeEditorTab === 'advanced'" class="advanced-panel"><h2>能力与记忆</h2><p>在右侧配置智能体使用的模型、工具、MCP、Skill 和知识库。开启记忆后，智能体可在后续会话中调用历史信息。</p><div class="advanced-summary"><div v-for="group in capabilityGroups" :key="group.field"><strong>{{ formData[group.field].length }} 项</strong><span>已选择{{ group.label }}</span></div></div></section>
      </section>
      <aside class="configuration">
        <section class="card config-card model-card"><div class="config-heading"><span class="config-icon"><UiIcon name="cube"/></span><div><h2>模型配置</h2><p>选择合适的模型处理任务</p></div></div><el-form-item label="基础模型" prop="llm_id"><el-select v-model="formData.llm_id" filterable :loading="dataLoading.llm" placeholder="选择模型" style="width:100%"><template #prefix><ProviderLogo v-if="selectedModel" class="dropdown-option-logo" :provider="selectedModel.provider" :base-url="selectedModel.base_url"/></template><el-option v-for="llm in llmOptions" :key="llm.llm_id" :value="llm.llm_id" :label="modelDisplayName(llm)"><span class="dropdown-option-row"><ProviderLogo class="dropdown-option-logo" :provider="llm.provider" :base-url="llm.base_url"/><span>{{modelDisplayName(llm)}}</span></span></el-option></el-select></el-form-item><p v-if="!dataLoading.llm && !llmOptions.length" class="empty-model">暂无可用模型，请先添加模型。</p><dl class="model-details"><div><dt>服务提供方</dt><dd>{{ modelProviderDisplayName(selectedModel?.provider) || '—' }}</dd></div><div><dt>模型类型</dt><dd>{{ selectedModel ? (selectedModel.llm_type === 'LLM' ? '对话模型' : selectedModel.llm_type) : '—' }}</dd></div></dl><div class="model-info"><span>使用已连接的模型</span><router-link to="/model">管理模型 →</router-link></div></section>
        <section class="card config-card capability-card"><div class="config-heading"><span class="config-icon"><UiIcon name="tool"/></span><div><h2>能力配置</h2><p>为智能体选择合适的工具和能力</p></div></div><CapabilityPicker v-for="group in capabilityGroups" :key="group.field" v-model="formData[group.field]" :label="group.label" :icon="group.icon" :options="group.options" :loading="group.loading" :manage-path="group.managePath" :error="group.error" @retry="group.retry"/></section>
        <section class="card config-card memory-card"><div class="config-heading"><span class="config-icon"><UiIcon name="database"/></span><div class="memory-copy"><h2>记忆</h2><p>开启后，智能体可记住对话中的信息</p></div><el-switch v-model="formData.enable_memory" aria-label="启用记忆"/></div></section>
      </aside>
    </el-form>
    <el-dialog v-model="identityPickerOpen" title="智能体图标" width="min(480px, calc(100vw - 32px))" append-to-body><div class="identity-picker"><div class="identity-picker-preview"><AgentIdentity :agent="{ ...formData, logo_url: previewLogo }"/><div><strong>{{ formData.name || '你的智能体' }}</strong><p>不上传图片，也能拥有清晰统一的标识</p></div></div><button type="button" class="auto-identity" :class="{ selected: identityMode === 'auto' }" :disabled="uploadLoading" @click="useAutomaticIcon"><UiIcon name="spark"/>自动匹配图标<span v-if="identityMode === 'auto'">已启用</span></button><label class="field-label">选择图标</label><div class="identity-icons"><button v-for="icon in agentIcons" :key="icon.id" type="button" :class="{ selected: identityMode === 'preset' && chosenIcon === icon.id }" :disabled="uploadLoading" :aria-pressed="identityMode === 'preset' && chosenIcon === icon.id" @click="selectIcon(icon.id)"><img :src="identityUrl(icon.id, identityMode === 'auto' ? autoIdentity.color : chosenColor)" alt=""/><span>{{ icon.label }}</span></button></div><label class="field-label">背景颜色</label><div class="identity-colors"><button v-for="color in agentColors" :key="color.id" type="button" :style="{ background: color.tint, color: color.ink }" :class="{ selected: identityMode !== 'upload' && (identityMode === 'auto' ? autoIdentity.color : chosenColor) === color.id }" :aria-label="color.label" :disabled="uploadLoading" @click="selectColor(color.id)"><UiIcon v-if="identityMode !== 'upload' && (identityMode === 'auto' ? autoIdentity.color : chosenColor) === color.id" name="check"/></button></div><div class="identity-upload-row"><el-upload v-model:file-list="fileList" :show-file-list="false" :auto-upload="false" :on-change="handleFileChange" :on-remove="handleFileRemove" accept="image/png,image/jpeg" :disabled="uploadLoading"><el-button :loading="uploadLoading"><UiIcon name="upload"/>上传自己的图片</el-button></el-upload><span>PNG / JPG · 小于 2MB</span></div><button v-if="identityMode === 'upload'" class="identity-choose" type="button" @click="useAutomaticIcon">移除图片，恢复自动图标</button></div><template #footer><el-button type="primary" :disabled="uploadLoading" @click="identityPickerOpen = false">完成</el-button></template></el-dialog>
    <el-dialog v-model="promptTemplateOpen" title="提示词模板" width="560px" append-to-body><div class="template-list"><button v-for="template in promptTemplates" :key="template.title" @click="applyPromptTemplate(template)"><strong>{{ template.title }}</strong><span>{{ template.description }}</span></button></div></el-dialog>
    <el-dialog v-model="expandedPrompt" title="系统提示词" width="min(900px, calc(100vw - 32px))" append-to-body><el-input v-model="formData.system_prompt" type="textarea" :rows="22" class="expanded-prompt" aria-label="系统提示词"/><template #footer><el-button type="primary" @click="expandedPrompt = false">完成</el-button></template></el-dialog>
  </div>
</template>
<style scoped src="./agent-editor.css"></style>
