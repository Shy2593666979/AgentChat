<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
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
const editingAgentId = ref('')
const fileList = ref<UploadUserFile[]>([])


// 智能体表单数据
const formData = reactive<AgentFormData>({
  name: '',
  description: '',
  logo_url: '',
  tool_ids: [],
  llm_id: '',
  mcp_ids: [],
  system_prompt: `你是一个智能助手 tmg-GPT，具有丰富的自然语言处理经验，擅长理解和生成文本内容。

## 你的角色
- 智能助手专家
- 文本处理专家
- 问题解决专家

## 你的技能
1. 理解和生成自然语言
2. 分析复杂问题并提供解决方案
3. 提供清晰的步骤指导
4. 整理和总结信息

## 限制条件
- 始终保持专业和有帮助的态度
- 提供准确可靠的信息
- 遵循用户的具体指示`,
  knowledge_ids: [],
  use_embedding: false
})

// 调试相关数据
const currentMessage = ref('')
const debugLoading = ref(false)

// 折叠面板状态
const collapseItems = ref({
  basic: true,
  aiModel: true,
  knowledge: true,
  tools: true,
  skills: true
})

// 选项数据
const llmOptions = ref<Array<LLMResponse & { name: string }>>([])
const toolOptions = ref<Array<ToolResponse & { name: string; icon: string }>>([])
const mcpOptions = ref<Array<MCPServer & { name: string; icon: string }>>([])
const knowledgeOptions = ref<Array<KnowledgeResponse & { 
  knowledge_id: string
  knowledge_name: string 
  knowledge_desc: string
  name: string
  icon: string 
}>>([])

// 数据加载状态
const dataLoading = ref({
  llm: false,
  tool: false,
  mcp: false,
  knowledge: false
})

// 表单验证规则
const rules = {
  name: [{ required: true, message: '请输入智能体名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入智能体描述', trigger: 'blur' }],
  system_prompt: [{ required: true, message: '请输入系统提示词', trigger: 'blur' }],
  llm_id: [{ required: true, message: '请选择大模型', trigger: 'change' }]
}

// 系统提示词模板
const promptTemplates = ref([
  {
    name: '通用助手',
    content: `你是一个智能助手，具有广泛的知识和能力。

## 你的角色
- 通用智能助手
- 知识问答专家
- 任务执行助手

## 你的能力
1. 回答各种问题
2. 协助完成任务
3. 提供建议和指导

## 行为准则
- 准确可靠
- 友善专业
- 高效有用`
  },
  {
    name: '编程助手',
    content: `你是一个专业的编程助手，精通多种编程语言和开发技术。

## 你的专长
- 代码编写和优化
- 技术问题解答
- 架构设计建议
- 调试问题分析

## 技能范围
1. 前端开发（Vue、React、Angular）
2. 后端开发（Node.js、Python、Java）
3. 数据库设计和优化
4. DevOps和部署

## 工作原则
- 提供高质量代码
- 遵循最佳实践
- 详细解释思路`
  },
  {
    name: '内容创作',
    content: `你是一个专业的内容创作助手，擅长各种类型的文本创作。

## 创作领域
- 文章写作
- 营销文案
- 创意策划
- 文档整理

## 创作特点
1. 内容原创性高
2. 结构清晰合理
3. 语言生动准确
4. 符合目标受众

## 质量标准
- 逻辑清晰
- 信息准确
- 表达流畅`
  }
])



// 方法
const loadAgent = (agent?: Agent) => {
  if (agent) {
    console.log('📝 加载智能体数据进行编辑:', agent)
    isEditing.value = true
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
    
    Object.assign(formData, {
      name: agent.name || '',
      description: agent.description || '',
      logo_url: agent.logo_url || '',
      tool_ids: processedToolIds,
      llm_id: agent.llm_id || '',
      mcp_ids: processedMcpIds,
      system_prompt: agent.system_prompt || '',
      knowledge_ids: processedKnowledgeIds,
      use_embedding: agent.use_embedding || false
    })
    
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
    editingAgentId.value = ''
    
    // 重置为默认值
    Object.assign(formData, {
      name: '',
      description: '',
      logo_url: '',
      tool_ids: [],
      llm_id: '',
      mcp_ids: [],
      system_prompt: `你是一个智能助手 tmg-GPT，具有丰富的自然语言处理经验，擅长理解和生成文本内容。

## 你的角色
- 智能助手专家
- 文本处理专家
- 问题解决专家

## 你的技能
1. 理解和生成自然语言
2. 分析复杂问题并提供解决方案
3. 提供清晰的步骤指导
4. 整理和总结信息

## 限制条件
- 始终保持专业和有帮助的态度
- 提供准确可靠的信息
- 遵循用户的具体指示`,
      knowledge_ids: [],
      use_embedding: false
    })
    fileList.value = []
    console.log('✅ 表单已重置为创建模式')
  }
}

// 切换折叠面板
const toggleCollapse = (key: keyof typeof collapseItems.value) => {
  collapseItems.value[key] = !collapseItems.value[key]
}

// 应用提示词模板
const applyTemplate = (template: typeof promptTemplates.value[0]) => {
  formData.system_prompt = template.content
  ElMessage.success(`已应用"${template.name}"模板`)
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
  formData.logo_url = ''
}

// 保存智能体
const saveAgent = async () => {
  try {
    // 表单验证
    const valid = await formRef.value?.validate()
    if (!valid) {
      ElMessage.warning('请完善必填信息后再提交')
      return
    }
    
    loading.value = true
    
    // 构建请求数据，确保字段正确
    const requestData = {
      name: formData.name,
      description: formData.description,
      logo_url: formData.logo_url,
      tool_ids: formData.tool_ids,
      llm_id: formData.llm_id,
      mcp_ids: formData.mcp_ids,
      system_prompt: formData.system_prompt,
      knowledge_ids: formData.knowledge_ids,
      use_embedding: formData.use_embedding
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
        router.push('/agent')
      } else {
        ElMessage.error(response.data.status_message || '更新失败')
      }
    } else {
      console.log('创建智能体数据:', requestData)
      const response = await createAgentAPI(requestData)
      
      if (response.data.status_code === 200) {
        ElMessage.success('智能体创建成功')
        // 保存成功后跳转到智能体列表页
        router.push('/agent')
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

// 发送调试消息
const sendDebugMessage = async () => {
  if (!currentMessage.value.trim()) return
  
  const userInput = currentMessage.value
  currentMessage.value = ''
  debugLoading.value = true
  
  try {
    // 模拟AI回复
    setTimeout(() => {
      ElMessage.success('消息已发送（模拟）')
      debugLoading.value = false
    }, 1000)
  } catch (error) {
    ElMessage.error('调试消息发送失败')
    debugLoading.value = false
  }
}



// 加载大模型数据
const loadLLMOptions = async () => {
  try {
    dataLoading.value.llm = true
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
          llmArray = Object.values(rawData).flat()
        }
      }
      
      console.log('🔄 处理后的数组:', llmArray)
      
      llmOptions.value = llmArray.map(llm => ({
        ...llm,
        name: `${llm.model} (${llm.provider})`
      }))
      
      console.log(`✅ 成功加载 ${llmOptions.value.length} 个大模型`)
      console.log('🧠 处理后的大模型数据:', llmOptions.value)
    } else {
      console.error('❌ 大模型API返回错误:', response.data.status_message)
      ElMessage.error(`加载大模型失败: ${response.data.status_message}`)
    }
  } catch (error) {
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
    console.log('🔄 开始加载工具数据...')
    
    const response = await getVisibleToolsAPI()
    console.log('📡 工具API响应:', response)
    
    if (response.data.status_code === 200) {
      const rawData = response.data.data
      console.log('📦 原始工具数据:', rawData)
      
      toolOptions.value = rawData.map(tool => ({
        ...tool,
        name: tool.zh_name || tool.en_name,
        icon: getToolIcon(tool.zh_name || tool.en_name)
      }))
      
      console.log(`✅ 成功加载 ${toolOptions.value.length} 个工具`)
      console.log('🔧 处理后的工具数据:', toolOptions.value)
    } else {
      console.error('❌ 工具API返回错误:', response.data.status_message)
    }
  } catch (error) {
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
    const response = await getMCPServersAPI()
    
    // 处理不同的响应格式
    let mcpData: MCPServer[] = []
    if (response.data.status_code === 200) {
      // 检查data字段是否存在且不为null
      if (response.data.data && Array.isArray(response.data.data)) {
        mcpData = response.data.data
      }
    }
    
    mcpOptions.value = mcpData.map(mcp => ({
      ...mcp,
      name: mcp.server_name,
      icon: getMCPIcon(mcp.server_name)
    }))
    console.log(`✅ 成功加载 ${mcpOptions.value.length} 个MCP服务器`)
  } catch (error) {
    console.error('加载MCP服务器失败:', error)
    ElMessage.error('加载MCP服务器列表失败')
  } finally {
    dataLoading.value.mcp = false
  }
}

// 加载知识库数据
const loadKnowledgeOptions = async () => {
  try {
    dataLoading.value.knowledge = true
    const response = await getKnowledgeListAPI()
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
    console.error('加载知识库失败:', error)
    ElMessage.error('加载知识库列表失败')
  } finally {
    dataLoading.value.knowledge = false
  }
}

// 获取工具图标
const getToolIcon = (toolName: string): string => {
  const iconMap: { [key: string]: string } = {
    '搜索': '🔍',
    '代码': '💻',
    '图片': '🎨',
    '天气': '🌤️',
    '邮件': '📧',
    '翻译': '🌐',
    '计算': '🧮'
  }
  
  for (const [key, icon] of Object.entries(iconMap)) {
    if (toolName.includes(key)) {
      return icon
    }
  }
  return '🔧'
}

// 获取MCP图标
const getMCPIcon = (mcpName: string): string => {
  const iconMap: { [key: string]: string } = {
    '天气': '🌤️',
    '邮件': '📧',
    '日历': '📅',
    '文件': '📁',
    '数据库': '🗄️'
  }
  
  for (const [key, icon] of Object.entries(iconMap)) {
    if (mcpName.includes(key)) {
      return icon
    }
  }
  return '🤖'
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
    ElMessage.info('正在加载智能体数据...')
    
    const response = await getAgentByIdAPI(agentId)
    if (response.data.status_code === 200 && response.data.data) {
      const agentData = response.data.data as any
      console.log('🔍 API返回的智能体原始数据:', agentData)
      
      // 转换API数据为Agent类型，兼容 id 和 agent_id
      const agent: Agent = {
        agent_id: agentData.id || agentData.agent_id,
        name: agentData.name,
        description: agentData.description,
        logo_url: agentData.logo_url,
        tool_ids: agentData.tool_ids || [],
        llm_id: agentData.llm_id,
        mcp_ids: agentData.mcp_ids || [],
        system_prompt: agentData.system_prompt,
        knowledge_ids: agentData.knowledge_ids || [],
        use_embedding: agentData.use_embedding,
        created_time: new Date().toISOString()
      }
      
      console.log('🔄 转换后的智能体数据:', agent)
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
  router.push('/agent')
}

// 初始化数据
const initializeData = async () => {
  console.log('🔄 开始初始化数据...')
  
  try {
    await Promise.all([
      loadLLMOptions(),
      loadToolOptions(),
      loadMCPOptions(),
      loadKnowledgeOptions()
    ])
    
    console.log('✅ 数据初始化完成')
    console.log('📊 数据统计:')
    console.log('  - 大模型:', llmOptions.value.length, '个')
    console.log('  - 工具:', toolOptions.value.length, '个')
    console.log('  - MCP:', mcpOptions.value.length, '个')
    console.log('  - 知识库:', knowledgeOptions.value.length, '个')
    
    // 如果没有数据，添加一些测试数据
    if (toolOptions.value.length === 0) {
      console.log('⚠️ 工具数据为空，添加测试数据')
      toolOptions.value.push({
        tool_id: 'test_tool_1',
        zh_name: '搜索工具',
        en_name: 'Search Tool',
        user_id: 'test',
        description: '用于搜索网络信息',
        logo_url: '',
        name: '🔍 搜索工具',
        icon: '🔍'
      } as any)
    }
    
    if (mcpOptions.value.length === 0) {
      console.log('⚠️ MCP数据为空，添加测试数据')
      mcpOptions.value.push({
        mcp_server_id: 'test_mcp_1',
        server_name: '邮件服务',
        url: 'http://localhost:8080',
        type: 'email',
        config: {},
        config_enabled: false,
        tools: [],
        params: [],
        name: '📧 邮件服务',
        icon: '📧'
      } as any)
    }
    
    if (knowledgeOptions.value.length === 0) {
      console.log('⚠️ 知识库数据为空，添加测试数据')
      knowledgeOptions.value.push({
        id: 'test_knowledge_1',
        name: '技术文档',
        description: '技术相关文档',
        user_id: 'test',
        create_time: new Date().toISOString(),
        update_time: new Date().toISOString(),
        count: 0,
        file_size: '0',
        knowledge_id: 'test_knowledge_1',
        knowledge_name: '技术文档',
        knowledge_desc: '技术相关文档',
        icon: '📚'
      } as any)
    }
    
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
  
  // 确保所有选项数据都加载完成后，再加载智能体数据
  const agentId = route.query.id as string
  if (agentId) {
    console.log('🔄 开始加载智能体数据，ID:', agentId, '类型:', typeof agentId)
    await loadAgentFromAPI(agentId)
  } else {
    console.log('🆕 创建新智能体模式')
    // 创建模式下，清空表单并设置默认值
    loadAgent()
  }
  

})

defineExpose({ loadAgent })
</script>

<template>
  <div class="agent-editor">
    <!-- 顶部工具栏 -->
    <div class="editor-header">
      <div class="header-left">
        <el-button @click="goBack" :icon="ArrowLeft" circle title="返回列表" class="back-btn"></el-button>
        <div class="header-info">
          <el-icon class="header-icon"><Edit /></el-icon>
          <span class="header-title">{{ isEditing ? '编辑智能体' : '创建智能体' }}</span>
          <div class="header-tags">
            <el-tag v-if="formData.name" type="primary" size="small" effect="dark">{{ formData.name }}</el-tag>
            <el-tag v-if="isEditing" type="success" size="small" effect="dark">ID: {{ editingAgentId }}</el-tag>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <el-button @click="goBack" :disabled="loading" class="cancel-btn">取消</el-button>
        <el-button @click="saveAgent" type="primary" :loading="loading" :icon="Check" class="save-btn">
          {{ isEditing ? '保存更改' : '创建智能体' }}
        </el-button>
      </div>
    </div>

    <!-- 三栏布局主体 -->
    <div class="editor-body">
      <!-- 左侧：系统提示词编辑器 -->
      <div class="left-panel">
        <div class="panel-header">
          <div class="header-content">
            <el-icon class="panel-icon"><DocumentCopy /></el-icon>
            <span class="panel-title">系统提示词</span>
            <span class="panel-subtitle">定义智能体的角色和行为</span>
          </div>
          <div class="header-actions">
            <el-dropdown trigger="click">
              <el-button size="small" type="primary" :icon="Plus" class="template-btn">模板</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item 
                    v-for="template in promptTemplates" 
                    :key="template.name"
                    @click="applyTemplate(template)"
                  >
                    {{ template.name }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        
        <div class="panel-content">
          <div class="prompt-editor-wrapper">
            <el-input
              v-model="formData.system_prompt"
              type="textarea"
              :rows="25"
              placeholder="请输入系统提示词，定义智能体的角色、能力和行为规范..."
              class="prompt-editor"
            />
            
            <div class="prompt-info">
              <div class="info-item">
                <span class="info-label">字符数:</span>
                <span class="info-value">{{ formData.system_prompt.length }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">行数:</span>
                <span class="info-value">{{ formData.system_prompt.split('\n').length }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间：智能体配置 -->
      <div class="center-panel">
        <div class="panel-header">
          <div class="header-content">
            <el-icon class="panel-icon"><Setting /></el-icon>
            <span class="panel-title">智能体配置</span>
            <span class="panel-subtitle">设置基本信息和能力</span>
          </div>
        </div>
        
        <div class="panel-content">
          <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px" class="config-form">
            <!-- 基础信息 -->
            <div class="config-section">
              <div class="section-header" @click="toggleCollapse('basic')">
                <div class="section-title">
                  <el-icon class="section-icon">
                    <ArrowDown v-if="collapseItems.basic" />
                    <ArrowRight v-else />
                  </el-icon>
                  <span>基础信息</span>
                </div>
                <div class="section-badge">
                  <el-tag size="small" type="info" effect="plain">必填</el-tag>
                </div>
              </div>
              <div v-show="collapseItems.basic" class="section-content">
                <el-form-item label="头像" class="avatar-item">
                  <el-upload
                    v-model:file-list="fileList"
                    class="avatar-uploader"
                    action="#"
                    :show-file-list="false"
                    :auto-upload="false"
                    :on-change="handleFileChange"
                    :on-remove="handleFileRemove"
                  >
                    <div class="avatar-wrapper">
                      <img v-if="formData.logo_url" :src="formData.logo_url" class="avatar" />
                      <div v-else class="avatar-placeholder">
                        <el-icon class="avatar-icon"><Plus /></el-icon>
                        <span class="avatar-text">上传头像</span>
                      </div>
                    </div>
                  </el-upload>
                </el-form-item>
                
                <el-form-item label="名称" prop="name">
                  <el-input v-model="formData.name" placeholder="请输入智能体名称" class="form-input" />
                </el-form-item>
                
                <el-form-item label="描述" prop="description">
                  <el-input
                    v-model="formData.description"
                    type="textarea"
                    :rows="3"
                    placeholder="请输入智能体描述"
                    class="form-textarea"
                  />
                </el-form-item>
              </div>
            </div>

            <!-- AI模型 -->
            <div class="config-section">
              <div class="section-header" @click="toggleCollapse('aiModel')">
                <div class="section-title">
                  <el-icon class="section-icon">
                    <ArrowDown v-if="collapseItems.aiModel" />
                    <ArrowRight v-else />
                  </el-icon>
                  <span>AI模型</span>
                </div>
                <div class="section-badge">
                  <el-tag size="small" type="warning" effect="plain">核心</el-tag>
                </div>
              </div>
              <div v-show="collapseItems.aiModel" class="section-content">
                <el-form-item label="模型" prop="llm_id">
                  <el-select 
                    v-model="formData.llm_id" 
                    placeholder="选择大语言模型"
                    :loading="dataLoading.llm"
                    class="form-select"
                  >
                    <el-option
                      v-for="llm in llmOptions"
                      :key="llm.llm_id"
                      :label="llm.name"
                      :value="llm.llm_id"
                    >
                      <span>{{ llm.name }} ({{ llm.llm_type }})</span>
                    </el-option>
                  </el-select>
                </el-form-item>
              </div>
            </div>

            <!-- 知识库 -->
            <div class="config-section">
              <div class="section-header" @click="toggleCollapse('knowledge')">
                <div class="section-title">
                  <el-icon class="section-icon">
                    <ArrowDown v-if="collapseItems.knowledge" />
                    <ArrowRight v-else />
                  </el-icon>
                  <span>知识库</span>
                </div>
                <div class="section-badge">
                  <el-badge :value="formData.knowledge_ids.length" class="badge" />
                </div>
              </div>
              <div v-show="collapseItems.knowledge" class="section-content">
                <el-form-item label="知识库">
                  <el-select
                    v-model="formData.knowledge_ids"
                    multiple
                    placeholder="选择知识库"
                    class="form-select"
                    :loading="dataLoading.knowledge"
                  >
                    <template #prefix>
                      <span v-if="dataLoading.knowledge" style="color: #909399; font-size: 12px;">加载中...</span>
                      <span v-else style="color: #909399; font-size: 12px;">{{ knowledgeOptions.length }}个</span>
                    </template>
                    <el-option
                      v-for="knowledge in knowledgeOptions"
                      :key="knowledge.knowledge_id"
                      :label="knowledge.name"
                      :value="knowledge.knowledge_id"
                    >
                      <span>{{ knowledge.icon }} {{ knowledge.name }}</span>
                    </el-option>
                  </el-select>
                </el-form-item>
              </div>
            </div>

            <!-- 工具 -->
            <div class="config-section">
              <div class="section-header" @click="toggleCollapse('tools')">
                <div class="section-title">
                  <el-icon class="section-icon">
                    <ArrowDown v-if="collapseItems.tools" />
                    <ArrowRight v-else />
                  </el-icon>
                  <span>工具</span>
                </div>
                <div class="section-badge">
                  <el-badge :value="formData.tool_ids.length" class="badge" />
                </div>
              </div>
              <div v-show="collapseItems.tools" class="section-content">
                <el-form-item label="选择工具">
                  <el-select
                    v-model="formData.tool_ids"
                    multiple
                    placeholder="选择工具"
                    class="form-select"
                    :loading="dataLoading.tool"
                  >
                    <template #prefix>
                      <span v-if="dataLoading.tool" style="color: #909399; font-size: 12px;">加载中...</span>
                      <span v-else style="color: #909399; font-size: 12px;">{{ toolOptions.length }}个</span>
                    </template>
                    <el-option
                      v-for="tool in toolOptions"
                      :key="tool.tool_id"
                      :label="tool.name"
                      :value="tool.tool_id"
                    >
                      <span>{{ tool.icon }} {{ tool.name }}</span>
                    </el-option>
                  </el-select>
                </el-form-item>
              </div>
            </div>

            <!-- 技能 -->
            <div class="config-section">
              <div class="section-header" @click="toggleCollapse('skills')">
                <div class="section-title">
                  <el-icon class="section-icon">
                    <ArrowDown v-if="collapseItems.skills" />
                    <ArrowRight v-else />
                  </el-icon>
                  <span>技能（MCP）</span>
                </div>
                <div class="section-badge">
                  <el-badge :value="formData.mcp_ids.length" class="badge" />
                </div>
              </div>
              <div v-show="collapseItems.skills" class="section-content">
                <el-form-item label="MCP服务">
                  <el-select
                    v-model="formData.mcp_ids"
                    multiple
                    placeholder="选择MCP服务器"
                    class="form-select"
                    :loading="dataLoading.mcp"
                  >
                    <template #prefix>
                      <span v-if="dataLoading.mcp" style="color: #909399; font-size: 12px;">加载中...</span>
                      <span v-else style="color: #909399; font-size: 12px;">{{ mcpOptions.length }}个</span>
                    </template>
                    <el-option
                      v-for="mcp in mcpOptions"
                      :key="mcp.mcp_server_id"
                      :label="mcp.name"
                      :value="mcp.mcp_server_id"
                    >
                      <span>{{ mcp.icon }} {{ mcp.name }}</span>
                    </el-option>
                  </el-select>
                </el-form-item>
              </div>
            </div>
          </el-form>
        </div>
      </div>

      <!-- 右侧：调试面板 -->
      <div class="right-panel">
        <div class="panel-header">
          <div class="header-content">
            <el-icon class="panel-icon"><ChatDotRound /></el-icon>
            <span class="panel-title">智能体预览</span>
            <span class="panel-subtitle">测试智能体功能</span>
          </div>
        </div>
        
        <div class="panel-content">
          <!-- 智能体信息卡片 -->
          <div class="agent-preview-card" v-if="formData.name">
            <div class="agent-avatar">
              <img :src="formData.logo_url || '/src/assets/robot.svg'" :alt="formData.name" />
            </div>
            <div class="agent-info">
              <h4>{{ formData.name }}</h4>
              <p>{{ formData.description || '暂无描述' }}</p>
              <div class="agent-stats">
                <span class="stat-item">
                  <i class="stat-icon">🔧</i>
                  {{ formData.tool_ids.length }} 工具
                </span>
                <span class="stat-item">
                  <i class="stat-icon">📚</i>
                  {{ formData.knowledge_ids.length }} 知识库
                </span>
                <span class="stat-item">
                  <i class="stat-icon">🤖</i>
                  {{ formData.mcp_ids.length }} MCP
                </span>
              </div>
            </div>
          </div>

          <!-- 输入框 -->
          <div class="chat-input-section">
            <div class="input-wrapper">
              <el-input
                v-model="currentMessage"
                type="textarea"
                :rows="8"
                placeholder="输入消息测试智能体... (Ctrl+Enter 发送)"
                @keydown.ctrl.enter="sendDebugMessage"
                class="message-input"
              />
              <div class="input-actions">
                <el-button
                  type="primary"
                  :icon="VideoPlay"
                  @click="sendDebugMessage"
                  :loading="debugLoading"
                  :disabled="!currentMessage.trim()"
                  class="send-btn"
                >
                  {{ debugLoading ? '发送中...' : '发送' }}
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.agent-editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);

  .editor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 32px;
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    border-bottom: 1px solid rgba(226, 232, 240, 0.8);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);

    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;

      .back-btn {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        border: none;
        color: white;
        transition: all 0.3s ease;
        
        &:hover {
          transform: translateX(-2px);
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }
      }

      .header-info {
        display: flex;
        align-items: center;
        gap: 12px;

        .header-icon {
          color: #3b82f6;
          font-size: 24px;
        }

        .header-title {
          font-size: 20px;
          font-weight: 700;
          background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .header-tags {
          display: flex;
          gap: 8px;
        }
      }
    }

    .header-actions {
      display: flex;
      gap: 12px;

      .cancel-btn {
        border: 1px solid #e2e8f0;
        color: #64748b;
        background: white;
        transition: all 0.3s ease;
        
        &:hover {
          border-color: #3b82f6;
          color: #3b82f6;
        }
      }

      .save-btn {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        border: none;
        font-weight: 600;
        transition: all 0.3s ease;
        
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);
        }
      }
    }
  }

  .editor-body {
    display: flex;
    flex: 1;
    overflow: hidden;
    gap: 2px;
    padding: 2px;

    .left-panel,
    .center-panel,
    .right-panel {
      display: flex;
      flex-direction: column;
      background: white;
      border-radius: 16px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
      overflow: hidden;

      .panel-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 20px 24px;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-bottom: 1px solid rgba(226, 232, 240, 0.6);

        .header-content {
          display: flex;
          flex-direction: column;
          gap: 4px;

          .panel-icon {
            color: #3b82f6;
            font-size: 20px;
            margin-bottom: 4px;
          }

          .panel-title {
            font-size: 16px;
            font-weight: 600;
            color: #1e293b;
          }

          .panel-subtitle {
            font-size: 12px;
            color: #64748b;
          }
        }

        .header-actions {
          .template-btn {
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            border: none;
            font-weight: 500;
            transition: all 0.3s ease;
            
            &:hover {
              transform: translateY(-1px);
              box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
            }
          }
        }
      }

      .panel-content {
        flex: 1;
        overflow-y: auto;
        padding: 24px;
      }
    }

    .left-panel {
      width: 35%;

      .prompt-editor-wrapper {
        .prompt-editor {
          :deep(.el-textarea__inner) {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            line-height: 1.6;
            font-size: 14px;
            resize: none;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px;
            background: #fafbfc;
            transition: all 0.3s ease;
            
            &:focus {
              border-color: #3b82f6;
              background: white;
              box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
          }
        }

        .prompt-info {
          display: flex;
          justify-content: space-between;
          margin-top: 16px;
          padding: 12px 16px;
          background: #f8fafc;
          border-radius: 8px;
          border: 1px solid #e2e8f0;

          .info-item {
            display: flex;
            align-items: center;
            gap: 8px;

            .info-label {
              font-size: 12px;
              color: #64748b;
              font-weight: 500;
            }

            .info-value {
              font-size: 14px;
              color: #1e293b;
              font-weight: 600;
            }
          }
        }
      }
    }

    .center-panel {
      width: 30%;

      .config-form {
        .config-section {
          margin-bottom: 20px;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          overflow: hidden;
          transition: all 0.3s ease;

          &:hover {
            border-color: #3b82f6;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
          }

          .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 20px;
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            cursor: pointer;
            user-select: none;
            transition: all 0.3s ease;

            &:hover {
              background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            }

            .section-title {
              display: flex;
              align-items: center;
              gap: 12px;

              .section-icon {
                color: #3b82f6;
                font-size: 16px;
              }

              span {
                font-weight: 600;
                color: #1e293b;
                font-size: 14px;
              }
            }

            .section-badge {
              .badge {
                margin-left: auto;
              }
            }
          }

          .section-content {
            padding: 20px;
            background: white;

            .el-form-item {
              margin-bottom: 20px;

              &:last-child {
                margin-bottom: 0;
              }
            }
          }
        }
      }

      .avatar-item {
        .avatar-uploader {
          :deep(.el-upload) {
            border: 2px dashed #e2e8f0;
            border-radius: 12px;
            cursor: pointer;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
            width: 80px;
            height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f8fafc;

            &:hover {
              border-color: #3b82f6;
              background: #eff6ff;
              transform: translateY(-2px);
              box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
            }
          }

          .avatar-wrapper {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;

            .avatar {
              width: 100%;
              height: 100%;
              object-fit: cover;
              border-radius: 10px;
            }

            .avatar-placeholder {
              display: flex;
              flex-direction: column;
              align-items: center;
              gap: 8px;

              .avatar-icon {
                font-size: 24px;
                color: #64748b;
              }

              .avatar-text {
                font-size: 12px;
                color: #64748b;
                font-weight: 500;
              }
            }
          }
        }
      }

      .form-input,
      .form-textarea,
      .form-select {
        :deep(.el-input__wrapper) {
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          background: #fafbfc;
          transition: all 0.3s ease;
          box-shadow: none;

          &:hover {
            border-color: #3b82f6;
          }

          &.is-focus {
            border-color: #3b82f6;
            background: white;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
          }
        }

        :deep(.el-textarea__inner) {
          border: none;
          background: transparent;
          font-size: 14px;
          line-height: 1.6;
        }
      }


    }

    .right-panel {
      width: 35%;

      .panel-content {
        display: flex;
        flex-direction: column;
        height: 100%;
        gap: 20px;
      }

      .agent-preview-card {
        display: flex;
        align-items: center;
        padding: 20px;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        transition: all 0.3s ease;

        &:hover {
          border-color: #3b82f6;
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
        }

        .agent-avatar {
          width: 60px;
          height: 60px;
          margin-right: 16px;
          border-radius: 12px;
          overflow: hidden;
          border: 2px solid #e2e8f0;

          img {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }
        }

        .agent-info {
          flex: 1;

          h4 {
            margin: 0 0 6px 0;
            font-size: 18px;
            color: #1e293b;
            font-weight: 600;
          }

          p {
            margin: 0 0 12px 0;
            font-size: 14px;
            color: #64748b;
            line-height: 1.5;
          }

          .agent-stats {
            display: flex;
            gap: 16px;
            font-size: 12px;

            .stat-item {
              display: flex;
              align-items: center;
              padding: 6px 10px;
              background: white;
              border-radius: 6px;
              border: 1px solid #e2e8f0;
              color: #64748b;
              font-weight: 500;

              .stat-icon {
                margin-right: 6px;
                font-size: 14px;
              }
            }
          }
        }
      }



      .chat-input-section {
        flex: 1;
        display: flex;
        flex-direction: column;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        transition: all 0.3s ease;

        &:hover {
          border-color: #3b82f6;
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
        }

        .input-wrapper {
          display: flex;
          flex-direction: column;
          gap: 16px;
          height: 100%;

          .message-input {
            flex: 1;
            :deep(.el-textarea__inner) {
              font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
              line-height: 1.6;
              font-size: 14px;
              resize: none;
              border: 1px solid #e2e8f0;
              border-radius: 8px;
              padding: 16px;
              background: white;
              transition: all 0.3s ease;
              
              &:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
              }
            }
          }

          .input-actions {
            display: flex;
            justify-content: flex-end;

            .send-btn {
              background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
              border: none;
              font-weight: 600;
              padding: 12px 24px;
              border-radius: 8px;
              transition: all 0.3s ease;
              
              &:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);
              }
            }
          }
        }
      }
    }
  }
}



// 响应式适配
@media (max-width: 1400px) {
  .agent-editor .editor-body {
    .left-panel {
      width: 38%;
    }
    .center-panel {
      width: 32%;
    }
    .right-panel {
      width: 30%;
    }
  }
}

@media (max-width: 1200px) {
  .agent-editor .editor-body {
    flex-direction: column;
    gap: 16px;
    padding: 16px;
    
    .left-panel,
    .center-panel,
    .right-panel {
      width: 100%;
      height: auto;
      min-height: 400px;
    }
  }
  
  .agent-editor .editor-header {
    padding: 16px 20px;
    
    .header-left .header-info .header-title {
      font-size: 18px;
    }
  }
}

@media (max-width: 768px) {
  .agent-editor {
    .editor-header {
      flex-direction: column;
      gap: 16px;
      align-items: stretch;
      padding: 16px;
      
      .header-left {
        justify-content: center;
      }
      
      .header-actions {
        justify-content: center;
      }
    }
    
    .editor-body {
      padding: 12px;
      
      .left-panel,
      .center-panel,
      .right-panel {
        .panel-header {
          padding: 16px;
        }
        
        .panel-content {
          padding: 16px;
        }
      }
    }
  }
}
</style> 