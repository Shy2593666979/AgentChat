<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getWorkspacePluginsAPI } from '../../../apis/workspace'

const router = useRouter()
const inputMessage = ref('')
const selectedMode = ref('normal')
const plugins = ref<any[]>([])
const showModelSelector = ref(false)
const showToolSelector = ref(false)
const showSearchSelector = ref(false)
const selectedModel = ref('Kimi-K2')
const selectedTools = ref<string[]>([])
const showMcpSelector = ref(false)
const selectedMcpServers = ref<string[]>([])
const mcpServers = ref<any[]>([])
const webSearchEnabled = ref(false)
const toolDropdownRef = ref<HTMLElement | null>(null)
const mcpDropdownRef = ref<HTMLElement | null>(null)

// 检测是否为Mac系统
const isMac = computed(() => {
  return typeof navigator !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0
})

const modes = [
  {
    id: 'normal',
    label: '日常模式',
    icon: '💬'
  },
  {
    id: 'lingseek',
    label: '灵寻LingSeek',
    icon: '✨'
  }
]

const models = [
  { id: 'kimi-k2', name: 'Kimi-K2', icon: '🤖' },
  { id: 'gpt-4', name: 'GPT-4', icon: '🧠' },
  { id: 'claude', name: 'Claude', icon: '🎭' }
]

// 获取可用插件
const fetchPlugins = async () => {
  try {
    const response = await getWorkspacePluginsAPI()
    if (response.data.status_code === 200) {
      plugins.value = response.data.data || []
      console.log('可用插件:', plugins.value)
    }
  } catch (error) {
    console.error('获取插件列表出错:', error)
  }
}

// 选择模式
const selectMode = (modeId: string) => {
  selectedMode.value = modeId
}

// 选择模型
const selectModel = (modelId: string) => {
  const model = models.find(m => m.id === modelId)
  if (model) {
    selectedModel.value = model.name
  }
  showModelSelector.value = false
}

// 切换工具选择
const toggleTool = (toolId: string) => {
  const index = selectedTools.value.indexOf(toolId)
  if (index > -1) {
    selectedTools.value.splice(index, 1)
  } else {
    selectedTools.value.push(toolId)
  }
}

// 切换联网搜索
const toggleWebSearch = () => {
  webSearchEnabled.value = !webSearchEnabled.value
  showSearchSelector.value = false
}

// 点击空白处关闭工具/MCP下拉
const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as Node
  if (showToolSelector.value && toolDropdownRef.value && !toolDropdownRef.value.contains(target)) {
    showToolSelector.value = false
  }
  if (showMcpSelector.value && mcpDropdownRef.value && !mcpDropdownRef.value.contains(target)) {
    showMcpSelector.value = false
  }
}

// 切换 MCP 服务器选择
const toggleMcp = (serverId: string) => {
  const index = selectedMcpServers.value.indexOf(serverId)
  if (index > -1) {
    selectedMcpServers.value.splice(index, 1)
  } else {
    selectedMcpServers.value.push(serverId)
  }
}

// 发送消息
const handleSend = async () => {
  if (!inputMessage.value.trim()) {
    ElMessage.warning('请输入消息内容')
    return
  }
  
  const query = inputMessage.value.trim()
  
  // 根据模式跳转到不同的页面
  if (selectedMode.value === 'lingseek') {
    // 灵寻模式：直接跳转到任务流程图页面（三列布局）
    console.log('跳转到灵寻任务页面')
    console.log('query:', query)
    console.log('tools:', selectedTools.value)
    console.log('webSearch:', webSearchEnabled.value)
    
    router.push({
      name: 'taskGraphPage',
      query: {
        query: query,
        tools: JSON.stringify(selectedTools.value),
        webSearch: webSearchEnabled.value.toString(),
        mcp_servers: JSON.stringify(selectedMcpServers.value)
      }
    })
  } else {
    // 日常模式：TODO - 跳转到普通对话页面
    ElMessage.info('日常模式对话功能开发中')
  }
  
  // 清空输入框
  inputMessage.value = ''
}

// 键盘事件处理
const handleKeydown = (event: KeyboardEvent) => {
  // Cmd+Enter (Mac) 或 Ctrl+Enter (Windows) 发送
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    event.preventDefault()
    handleSend()
  }
}

onMounted(() => {
  fetchPlugins()
  // 懒加载 MCP 列表（用于选择）
  import('../../../apis/mcp-server').then(async ({ getMCPServersAPI }) => {
    try {
      const res = await getMCPServersAPI()
      if (res.data && res.data.status_code === 200 && Array.isArray(res.data.data)) {
        mcpServers.value = res.data.data
      }
    } catch (e) {
      console.error('加载 MCP 服务器失败', e)
    }
  })
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="chat-page">
    <div class="chat-container">
      <!-- 欢迎区域 -->
      <div class="welcome-section">
        <div class="avatar-wrapper">
          <img src="../../../assets/robot.svg" alt="智言" class="avatar" />
        </div>
        <h1 class="welcome-title">我是智言小助手，很高兴见到你！</h1>
        <p class="welcome-subtitle">
          欢迎体验智言产品，智言灵寻，一位懂得完成复杂任务的Agent助理~
        </p>
      </div>

      <!-- 模式选择 -->
      <div class="mode-selector">
        <button
          v-for="mode in modes"
          :key="mode.id"
          :class="['mode-btn', { active: selectedMode === mode.id }]"
          @click="selectMode(mode.id)"
        >
          <span class="mode-icon">{{ mode.icon }}</span>
          <span class="mode-label">{{ mode.label }}</span>
        </button>
      </div>

      <!-- 输入区域 -->
      <div class="input-section">
        <div class="input-wrapper">
          <textarea
            v-model="inputMessage"
            placeholder="给智言发消息，让智言帮你完成任务~"
            class="message-input"
            rows="4"
            @keydown="handleKeydown"
          ></textarea>
          
          <!-- 底部控制栏 -->
          <div class="input-footer">
            <div class="footer-left">
              <!-- 模型选择（仅日常模式显示） -->
              <div v-if="selectedMode === 'normal'" class="selector-dropdown">
                <div 
                  class="selector-item"
                  @click="showModelSelector = !showModelSelector"
                >
                  <span class="selector-icon">🤖</span>
                  <span class="selector-text">{{ selectedModel }}</span>
                  <span class="selector-arrow">▼</span>
                </div>
                
                <!-- 模型下拉菜单 -->
                <transition name="dropdown">
                  <div v-if="showModelSelector" class="dropdown-menu">
                    <div
                      v-for="model in models"
                      :key="model.id"
                      class="dropdown-item"
                      @click="selectModel(model.id)"
                    >
                      <span class="item-icon">{{ model.icon }}</span>
                      <span class="item-text">{{ model.name }}</span>
                      <span v-if="selectedModel === model.name" class="item-check">✓</span>
                    </div>
                  </div>
                </transition>
              </div>

              <!-- 联网搜索（仅灵寻模式显示） -->
              <div v-if="selectedMode === 'lingseek'" class="selector-dropdown">
                <div 
                  :class="['selector-item', { active: webSearchEnabled }]"
                  @click="toggleWebSearch"
                >
                  <span class="selector-icon">🌐</span>
                  <span class="selector-text">联网搜索</span>
                  <span v-if="webSearchEnabled" class="selector-check">✓</span>
                </div>
              </div>
              
              <!-- 工具选择 -->
              <div class="selector-dropdown" ref="toolDropdownRef">
                <div 
                  class="selector-item"
                  @click="showToolSelector = !showToolSelector"
                >
                  <span class="selector-icon">🔧</span>
                  <span class="selector-text">
                    {{ selectedTools.length > 0 ? `已选 ${selectedTools.length} 个` : '选择工具' }}
                  </span>
                  <span class="selector-arrow">▼</span>
                </div>
                
                <!-- 工具下拉菜单 -->
                <transition name="dropdown">
                  <div v-if="showToolSelector" class="dropdown-menu tool-menu">
                    <!-- 标题 -->
                    <div class="dropdown-header">
                      <span class="header-title">选择工具</span>
                      <span class="header-count">{{ plugins.length }} 个可用</span>
                    </div>

                    <!-- 工具列表 -->
                    <div class="dropdown-list">
                      <div v-if="plugins.length === 0" class="dropdown-empty">
                        <span class="empty-icon">🔧</span>
                        <span class="empty-text">暂无可用工具</span>
                      </div>
                      <div
                        v-for="plugin in plugins"
                        :key="plugin.id || plugin.tool_id"
                        :class="['dropdown-item', { selected: selectedTools.includes(plugin.id || plugin.tool_id) }]"
                        @click="toggleTool(plugin.id || plugin.tool_id)"
                      >
                        <div class="item-left">
                          <div class="item-icon-wrapper">
                            <img 
                              v-if="plugin.logo_url" 
                              :src="plugin.logo_url" 
                              :alt="plugin.zh_name || plugin.name"
                              class="item-icon-img"
                            />
                            <span v-else class="item-icon">🔧</span>
                          </div>
                          <div class="item-content">
                            <div class="item-text">{{ plugin.zh_name || plugin.name || plugin.tool_name }}</div>
                            <div class="item-desc">{{ plugin.description || '暂无描述' }}</div>
                          </div>
                        </div>
                        <div 
                          v-if="selectedTools.includes(plugin.id || plugin.tool_id)" 
                          class="item-check-wrapper"
                        >
                          <span class="item-check">✓</span>
                        </div>
                      </div>
                    </div>

                    <!-- 底部操作栏 -->
                    <div v-if="selectedTools.length > 0" class="dropdown-footer">
                      <button 
                        class="clear-btn"
                        @click.stop="selectedTools = []"
                      >
                        <span>清空</span>
                      </button>
                      <div class="selected-info">
                        <span class="selected-count">已选 {{ selectedTools.length }} 个工具</span>
                      </div>
                    </div>
                  </div>
                </transition>
              </div>

              <!-- MCP 服务器选择（紧跟工具选择后） -->
              <div class="selector-dropdown" ref="mcpDropdownRef">
                <div 
                  class="selector-item"
                  @click="showMcpSelector = !showMcpSelector"
                >
                  <span class="selector-icon">🧩</span>
                  <span class="selector-text">
                    {{ selectedMcpServers.length > 0 ? `已选 ${selectedMcpServers.length} 个MCP` : '选择MCP' }}
                  </span>
                  <span class="selector-arrow">▼</span>
                </div>
                
                <!-- MCP 下拉菜单 -->
                <transition name="dropdown">
                  <div v-if="showMcpSelector" class="dropdown-menu tool-menu">
                    <!-- 标题 -->
                    <div class="dropdown-header">
                      <span class="header-title">选择MCP服务器</span>
                      <span class="header-count">{{ mcpServers.length }} 个可用</span>
                    </div>

                    <!-- 列表 -->
                    <div class="dropdown-list">
                      <div v-if="mcpServers.length === 0" class="dropdown-empty">
                        <span class="empty-icon">🧩</span>
                        <span class="empty-text">暂无可用MCP服务器</span>
                      </div>
                      <div
                        v-for="mcp in mcpServers"
                        :key="mcp.mcp_server_id"
                        :class="['dropdown-item', { selected: selectedMcpServers.includes(mcp.mcp_server_id) }]"
                        @click="toggleMcp(mcp.mcp_server_id)"
                      >
                        <div class="item-left">
                          <div class="item-icon-wrapper">
                            <img 
                              v-if="mcp.logo_url" 
                              :src="mcp.logo_url" 
                              :alt="mcp.server_name"
                              class="item-icon-img"
                            />
                            <span v-else class="item-icon">🧩</span>
                          </div>
                          <div class="item-content">
                            <div class="item-text">{{ mcp.server_name }}</div>
                          </div>
                        </div>
                        <div 
                          v-if="selectedMcpServers.includes(mcp.mcp_server_id)" 
                          class="item-check-wrapper"
                        >
                          <span class="item-check">✓</span>
                        </div>
                      </div>
                    </div>

                    <!-- 底部操作栏 -->
                    <div v-if="selectedMcpServers.length > 0" class="dropdown-footer">
                      <button 
                        class="clear-btn"
                        @click.stop="selectedMcpServers = []"
                      >
                        <span>清空</span>
                      </button>
                      <div class="selected-info">
                        <span class="selected-count">已选 {{ selectedMcpServers.length }} 个MCP</span>
                      </div>
                    </div>
                  </div>
                </transition>
              </div>
            </div>
            
            <div class="footer-right">
              <!-- 附件按钮 -->
              <button class="icon-btn" title="上传附件">
                <span>📎</span>
              </button>
              
              <!-- 发送按钮 -->
              <button class="send-btn" @click="handleSend">
                <span>➤</span>
              </button>
            </div>
          </div>
        </div>
        
        <!-- 快捷键提示 -->
        <div class="hint-text">
          {{ isMac ? '⌘' : 'Ctrl' }} + Enter 发送
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.chat-page {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  background: linear-gradient(180deg, #fafbfc 0%, #ffffff 100%);
  padding: 60px 20px 40px;
  overflow-y: auto;
}

.chat-container {
  max-width: 820px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.welcome-section {
  text-align: center;
  margin-bottom: 40px;
  animation: fadeInUp 0.6s ease;

  .avatar-wrapper {
    margin-bottom: 20px;
    display: flex;
    justify-content: center;
    position: relative;

    .avatar {
      width: 120px;
      height: 120px;
      object-fit: contain;
      transition: all 0.3s ease;
      filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.08));

      &:hover {
        transform: scale(1.05);
        filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.12));
      }
    }
  }

  .welcome-title {
    font-size: 32px;
    font-weight: 700;
    background: linear-gradient(135deg, #1f2937 0%, #4b5563 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 12px 0;
    letter-spacing: -0.5px;
  }

  .welcome-subtitle {
    font-size: 15px;
    color: #6b7280;
    margin: 0;
    line-height: 1.7;
    max-width: 500px;
    margin: 0 auto;
  }
}

.mode-selector {
  display: flex;
  gap: 14px;
  margin-bottom: 36px;
  animation: fadeInUp 0.6s ease 0.1s both;

  .mode-btn {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 24px;
    border: 2px solid #e5e7eb;
    border-radius: 24px;
    background: white;
    color: #6b7280;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);

    .mode-icon {
      font-size: 18px;
      transition: transform 0.3s ease;
    }

    .mode-label {
      font-weight: 600;
    }

    &:hover {
      border-color: #667eea;
      background: #f8f9ff;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);

      .mode-icon {
        transform: scale(1.1);
      }
    }

    &.active {
      border-color: #667eea;
      background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
      color: #667eea;
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
      transform: translateY(-2px);

      .mode-icon {
        transform: scale(1.15);
      }
    }
  }
}

// 动画
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes rotate {
  from {
    transform: translate(-50%, -50%) rotate(0deg);
  }
  to {
    transform: translate(-50%, -50%) rotate(360deg);
  }
}

.input-section {
  width: 100%;
  max-width: 800px;
  animation: fadeInUp 0.6s ease 0.2s both;

  .input-wrapper {
    background: #ffffff;
    border: 2px solid #e5e7eb;
    border-radius: 20px;
    padding: 24px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);

    &:focus-within {
      border-color: #667eea;
      box-shadow: 0 6px 24px rgba(102, 126, 234, 0.15);
      transform: translateY(-2px);
    }

    .message-input {
      width: 100%;
      border: none;
      background: transparent;
      font-size: 15px;
      line-height: 1.6;
      color: #1f2937;
      resize: none;
      outline: none;
      font-family: inherit;
      min-height: 90px;
      margin-bottom: 16px;

      &::placeholder {
        color: #9ca3af;
      }
    }

    .input-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .footer-left {
        display: flex;
        gap: 10px;

          .selector-dropdown {
          position: relative;

          .selector-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 14px;
            background: #f8f9fa;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            font-size: 13px;
            color: #4b5563;
            cursor: pointer;
            transition: all 0.2s ease;
            user-select: none;

            .selector-icon {
              font-size: 16px;
            }

            .selector-text {
              font-weight: 500;
            }

            .selector-arrow {
              font-size: 10px;
              opacity: 0.5;
              transition: transform 0.2s ease;
            }

            .selector-check {
              font-size: 14px;
              color: #667eea;
              font-weight: 600;
            }

            &:hover {
              border-color: #667eea;
              background: #f0f4ff;
              color: #667eea;
            }

            &.active {
              background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
              border-color: #667eea;
              color: #667eea;
              box-shadow: 0 2px 6px rgba(102, 126, 234, 0.15);
            }

            &:active {
              transform: scale(0.98);
            }
          }

          .dropdown-menu {
            position: absolute;
            top: calc(100% + 8px);
            left: 0;
            min-width: 200px;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
            z-index: 1000;
            max-height: 320px;
            overflow: hidden;
            display: flex;
            flex-direction: column;

            &.tool-menu {
              min-width: 360px;
              max-height: 450px;
            }

            .dropdown-header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              padding: 12px 16px;
              background: linear-gradient(135deg, #f8f9fa 0%, #f0f2f5 100%);
              border-bottom: 1px solid #e5e7eb;

              .header-title {
                font-size: 14px;
                font-weight: 600;
                color: #1f2937;
              }

              .header-count {
                font-size: 12px;
                color: #6b7280;
                background: white;
                padding: 2px 8px;
                border-radius: 10px;
                border: 1px solid #e5e7eb;
              }
            }

            .dropdown-list {
              flex: 1;
              overflow-y: auto;
              padding: 8px;

              &::-webkit-scrollbar {
                width: 8px;
              }

              &::-webkit-scrollbar-track {
                background: transparent;
              }

              &::-webkit-scrollbar-thumb {
                background: #e0e0e0;
                border-radius: 4px;

                &:hover {
                  background: #bdbdbd;
                }
              }
            }

            .dropdown-empty {
              padding: 48px 20px;
              text-align: center;
              color: #9ca3af;
              display: flex;
              flex-direction: column;
              align-items: center;
              gap: 12px;

              .empty-icon {
                font-size: 48px;
                opacity: 0.3;
              }

              .empty-text {
                font-size: 14px;
                color: #6b7280;
              }
            }

            .dropdown-item {
              display: flex;
              align-items: center;
              justify-content: space-between;
              gap: 12px;
              padding: 14px 12px;
              border-radius: 10px;
              cursor: pointer;
              transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
              margin-bottom: 4px;
              border: 2px solid transparent;
              background: #fafafa;

              .item-left {
                display: flex;
                align-items: center;
                gap: 12px;
                flex: 1;
                min-width: 0;
              }

              .item-icon-wrapper {
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
                border-radius: 10px;
                flex-shrink: 0;
                transition: all 0.3s ease;
                overflow: hidden;

                .item-icon-img {
                  width: 100%;
                  height: 100%;
                  object-fit: cover;
                }

                .item-icon {
                  font-size: 20px;
                }
              }

              .item-content {
                flex: 1;
                min-width: 0;

                .item-text {
                  font-size: 15px;
                  font-weight: 600;
                  color: #1f2937;
                  margin-bottom: 4px;
                  line-height: 1.3;
                }

                .item-desc {
                  font-size: 12px;
                  color: #6b7280;
                  overflow: hidden;
                  text-overflow: ellipsis;
                  display: -webkit-box;
                  -webkit-line-clamp: 2;
                  line-clamp: 2;
                  -webkit-box-orient: vertical;
                  line-height: 1.5;
                }
              }

              .item-check-wrapper {
                width: 28px;
                height: 28px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 50%;
                flex-shrink: 0;
                box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);

                .item-check {
                  font-size: 16px;
                  color: white;
                  font-weight: 700;
                }
              }

              &:hover {
                background: #f5f7fa;
                transform: translateX(2px);
                border-color: #e5e7eb;

                .item-icon-wrapper {
                  background: linear-gradient(135deg, #e5e7eb 0%, #d1d5db 100%);
                  transform: scale(1.05);
                }
              }

              &.selected {
                background: linear-gradient(135deg, #eff6ff 0%, #e0f2fe 100%);
                border-color: #667eea;
                box-shadow: 0 2px 8px rgba(102, 126, 234, 0.12);

                .item-icon-wrapper {
                  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
                  
                  .item-icon-img {
                    filter: brightness(1.2);
                  }

                  .item-icon {
                    filter: brightness(0) invert(1);
                  }
                }

                .item-text {
                  color: #667eea;
                }
              }

              &:active {
                transform: scale(0.98) translateX(2px);
              }
            }

            .dropdown-footer {
              display: flex;
              justify-content: space-between;
              align-items: center;
              padding: 12px 16px;
              border-top: 2px solid #f0f0f0;
              background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%);

              .clear-btn {
                padding: 8px 16px;
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                font-size: 13px;
                color: #6b7280;
                cursor: pointer;
                transition: all 0.25s ease;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 6px;

                &:hover {
                  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
                  border-color: #ef4444;
                  color: #dc2626;
                  transform: translateY(-1px);
                  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.2);
                }

                &:active {
                  transform: translateY(0);
                }
              }

              .selected-info {
                display: flex;
                align-items: center;
                gap: 8px;

                .selected-count {
                  font-size: 13px;
                  color: #667eea;
                  font-weight: 600;
                  padding: 4px 12px;
                  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                  border-radius: 12px;
                  border: 1px solid #667eea;
                }
              }
            }
          }
        }
      }

      .footer-right {
        display: flex;
        gap: 10px;
        align-items: center;

        .icon-btn {
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f8f9fa;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
          font-size: 18px;

          &:hover {
            border-color: #667eea;
            background: #f0f4ff;
            transform: translateY(-1px);
          }

          &:active {
            transform: translateY(0);
          }
        }

        .send-btn {
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border: none;
          border-radius: 8px;
          color: white;
          cursor: pointer;
          transition: all 0.2s ease;
          font-size: 16px;
          box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);

          &:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
          }

          &:active {
            transform: translateY(0);
          }
        }
      }
    }
  }

  .hint-text {
    margin-top: 10px;
    text-align: right;
    font-size: 12px;
    color: #9ca3af;
  }
}

// 下拉菜单动画
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@media (max-width: 768px) {
  .chat-page {
    padding: 40px 16px 20px;
  }

  .welcome-section {
    margin-bottom: 32px;

    .avatar-wrapper {
      .avatar {
        width: 80px;
        height: 80px;
      }
    }

    .welcome-title {
      font-size: 26px;
    }

    .welcome-subtitle {
      font-size: 14px;
    }
  }

  .mode-selector {
    margin-bottom: 28px;
    
    .mode-btn {
      padding: 10px 18px;
      font-size: 13px;
    }
  }

  .input-section {
    .input-wrapper {
      padding: 18px;

      .input-footer {
        .footer-left {
          flex-wrap: wrap;
        }
      }
    }
  }
}
</style>

