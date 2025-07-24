<script setup lang="ts">
import { ref, computed } from 'vue'

const searchQuery = ref('')
const activeMode = ref('tool')
const deepSearchEnabled = ref(false)

// 检测是否为Mac系统
const isMac = computed(() => {
  return typeof navigator !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0
})

const modes = [
  { key: 'tool', label: '工具模式', color: '#52c41a', icon: '🔧' },
  { key: 'mcp', label: 'MCP模式', color: '#1890ff', icon: '🔗' },
  { key: 'agent', label: '智能体模式', color: '#fa8c16', icon: '🤖' },
  { key: 'knowledge', label: '知识库模式', color: '#f5222d', icon: '📚' }
]

const examples = [
  {
    title: '多工具协作任务',
    category: '工具模式',
    description: '使用多个工具配合完成复杂任务，如搜索+分析+生成报告',
    action: '开始使用 →'
  },
  {
    title: 'MCP服务器集成',
    category: 'MCP模式',
    description: '连接外部MCP服务器，扩展系统能力和数据源',
    action: '连接服务 →'
  },
  {
    title: '智能体自动化',
    category: '智能体模式',
    description: '使用专业智能体处理特定领域的复杂任务',
    action: '选择智能体 →'
  },
  {
    title: '知识库问答',
    category: '知识库模式',
    description: '基于已有知识库进行精准问答和信息检索',
    action: '查询知识 →'
  }
]

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    console.log('搜索:', searchQuery.value, '模式:', activeMode.value, '深度搜索:', deepSearchEnabled.value)
    // 这里可以添加搜索逻辑
  }
}

const handleModeChange = (mode: string) => {
  activeMode.value = mode
}

const toggleDeepSearch = () => {
  deepSearchEnabled.value = !deepSearchEnabled.value
}

const handleKeydown = (event: KeyboardEvent) => {
  // Cmd+Enter (Mac) 或 Ctrl+Enter (Windows) 发送
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    event.preventDefault()
    handleSearch()
  }
  // Shift+Enter 换行（默认行为，不需要处理）
}

const handleExampleClick = (example: any) => {
  searchQuery.value = example.description
  handleSearch()
}
</script>

<template>
  <div class="homepage">
    <!-- Logo区域 -->
    <div class="logo-section">
      <div class="logo-container">
                 <img src="../../assets/mars-agent.svg" alt="Mars Agent" class="logo" />
         <h1 class="brand-name">Mars Agent</h1>
      </div>
    </div>

    <!-- 搜索区域 -->
    <div class="search-section">
      <div class="search-container">
        <div class="search-box">
                     <div class="search-input-wrapper">
             <textarea
               v-model="searchQuery"
               placeholder="Mars Agent会完成你的任务输出报告。"
               class="search-input"
               @keydown="handleKeydown"
               rows="3"
             ></textarea>
             
             <!-- 底部控制按钮 -->
             <div class="search-controls">
               <!-- 深度搜索开关 -->
               <div class="search-toggle-container">
                 <button 
                   :class="['search-toggle', { 'active': deepSearchEnabled }]" 
                   @click="toggleDeepSearch"
                 >
                   🔍 深度搜索
                 </button>
               </div>
               
               <!-- 发送按钮和快捷键提示 -->
               <div class="search-send-container">
                 <span class="shortcut-hint">{{ isMac ? '⌘+↵' : 'Ctrl + ↵ ' }}发送</span>
                 <button class="send-button" @click="handleSearch">
                   ➤
                 </button>
               </div>
             </div>
           </div>
        </div>

        <!-- 模式选择 -->
        <div class="mode-selector">
          <div
            v-for="mode in modes"
            :key="mode.key"
            :class="['mode-item', { active: activeMode === mode.key }]"
            :style="{ '--mode-color': mode.color }"
            @click="handleModeChange(mode.key)"
          >
            <span class="mode-icon">{{ mode.icon }}</span>
            <span class="mode-label">{{ mode.label }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 优秀案例区域 -->
    <div class="examples-section">
      <h2 class="section-title">
        优秀案例
        <span class="section-subtitle">和 Mars 一起提升工作效率</span>
      </h2>

      <div class="examples-grid">
        <div
          v-for="(example, index) in examples"
          :key="index"
          class="example-card"
          @click="handleExampleClick(example)"
        >
          <div class="example-header">
            <h3 class="example-title">{{ example.title }}</h3>
            <span class="example-category">{{ example.category }}</span>
          </div>
          <p class="example-description">{{ example.description }}</p>
          <div class="example-action">{{ example.action }}</div>
          
          <!-- 模拟图表/内容预览 -->
          <div class="example-preview">
            <div v-if="index === 0" class="code-preview">
              <div class="code-lines">
                <div class="code-line"></div>
                <div class="code-line short"></div>
                <div class="code-line"></div>
                <div class="code-line medium"></div>
              </div>
            </div>
            <div v-else-if="index === 1" class="chart-preview">
              <div class="chart-bars">
                <div class="bar" style="height: 60%"></div>
                <div class="bar" style="height: 80%"></div>
                <div class="bar" style="height: 45%"></div>
                <div class="bar" style="height: 90%"></div>
              </div>
            </div>
            <div v-else-if="index === 2" class="table-preview">
              <div class="table-row header"></div>
              <div class="table-row"></div>
              <div class="table-row"></div>
              <div class="table-row"></div>
            </div>
            <div v-else class="pie-preview">
              <div class="pie-chart">
                <div class="pie-slice slice1"></div>
                <div class="pie-slice slice2"></div>
                <div class="pie-slice slice3"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.homepage {
  min-height: 100vh;
  background: #ffffff;
  padding: 40px 20px;
  overflow-y: auto;
}

.logo-section {
  text-align: center;
  margin-bottom: 60px;
  
  .logo-container {
    display: inline-flex;
    align-items: center;
    gap: 16px;
    
    .logo {
      width: 64px;
      height: 64px;
      filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.15));
    }
    
         .brand-name {
       font-size: 48px;
       font-weight: 800;
       background: linear-gradient(135deg, #667eea 0%, #764ba2 30%, #8b5cf6 60%, #6366f1 100%);
       -webkit-background-clip: text;
       -webkit-text-fill-color: transparent;
       background-clip: text;
       margin: 0;
       position: relative;
       letter-spacing: -1px;
       
       &::before {
         content: 'Mars Agent';
         position: absolute;
         top: 2px;
         left: 2px;
         background: linear-gradient(135deg, rgba(102, 126, 234, 0.4), rgba(118, 75, 162, 0.4));
         -webkit-background-clip: text;
         -webkit-text-fill-color: transparent;
         background-clip: text;
         z-index: -1;
         filter: blur(1px);
       }
       
       &::after {
         content: '';
         position: absolute;
         bottom: -8px;
         left: 0;
         right: 0;
         height: 3px;
         background: linear-gradient(90deg, transparent, #6366f1, #8b5cf6, #6366f1, transparent);
         border-radius: 2px;
         opacity: 0.6;
       }
     }
  }
}

.search-section {
  max-width: 800px;
  margin: 0 auto 80px;
  
     .search-container {
     background: #ffffff;
     border-radius: 24px;
     padding: 48px;
     box-shadow: 0 12px 40px rgba(0, 0, 0, 0.08);
     border: 1px solid #f1f5f9;
   }
  
  .search-box {
    margin-bottom: 32px;
    
         .search-input-wrapper {
       background: #f8f9fa;
       border-radius: 20px;
       padding: 12px;
       border: 2px solid #e9ecef;
       transition: all 0.3s ease;
       min-height: 120px;
       width: 100%;
       display: block;
       position: relative;
       
       &:focus-within {
         border-color: #6366f1;
         box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
       }
      
             .search-input {
         width: 100%;
         border: none;
         background: transparent;
         padding: 12px 16px 48px 16px;
         font-size: 18px;
         outline: none;
         color: #333;
         line-height: 1.5;
         resize: none;
         font-family: inherit;
         min-height: 90px;
         box-sizing: border-box;
         
         &::placeholder {
           color: #8a8a8a;
         }
       }
      
      
    }
  }
  
  .mode-selector {
    display: flex;
    gap: 16px;
    justify-content: center;
    flex-wrap: wrap;
    
    .mode-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 20px;
      background: #f8f9fa;
      border: 2px solid #e9ecef;
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.3s ease;
      font-weight: 500;
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }
      
      &.active {
        background: var(--mode-color);
        color: white;
        border-color: var(--mode-color);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
      }
      
      .mode-icon {
        font-size: 18px;
      }
      
      .mode-label {
        font-size: 14px;
      }
    }
  }
  
  .search-controls {
    position: absolute;
    bottom: 8px;
    left: 12px;
    right: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    pointer-events: none;
    
    > * {
      pointer-events: auto;
    }
  }
  
  .search-toggle-container {
    display: flex;
    
    .search-toggle {
      background: #ffffff;
      color: #9ca3af;
      border: 1px solid #e5e7eb;
      padding: 6px 12px;
      border-radius: 16px;
      font-weight: 500;
      font-size: 13px;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      
      &:hover {
        border-color: #6366f1;
        color: #6366f1;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
      }
      
      &.active {
        background: #6366f1;
        color: white;
        border-color: #6366f1;
        box-shadow: 0 2px 6px rgba(99, 102, 241, 0.3);
        
        &:hover {
          background: #4f46e5;
          border-color: #4f46e5;
        }
      }
    }
  }
  
  .search-send-container {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .shortcut-hint {
      color: #9ca3af;
      font-size: 12px;
      font-weight: 400;
    }
    
    .send-button {
      background: #6366f1;
      color: white;
      border: none;
      padding: 8px;
      border-radius: 8px;
      font-size: 16px;
      cursor: pointer;
      transition: all 0.2s ease;
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2px 6px rgba(99, 102, 241, 0.3);
      
      &:hover {
        background: #4f46e5;
        box-shadow: 0 3px 8px rgba(99, 102, 241, 0.4);
      }
      
      &:active {
        background: #3730a3;
        box-shadow: 0 1px 3px rgba(99, 102, 241, 0.3);
      }
    }
  }
}

.examples-section {
  max-width: 1200px;
  margin: 0 auto;
  
  .section-title {
    text-align: center;
    font-size: 32px;
    font-weight: 700;
    color: #333333;
    margin-bottom: 16px;
    
    .section-subtitle {
      display: block;
      font-size: 16px;
      font-weight: 400;
      color: #666666;
      margin-top: 8px;
    }
  }
  
  .examples-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 24px;
    margin-top: 40px;
    
         .example-card {
       background: #ffffff;
       border-radius: 20px;
       padding: 24px;
       cursor: pointer;
       transition: all 0.3s ease;
       border: 1px solid #f1f5f9;
       position: relative;
       overflow: hidden;
       box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
       
       &:hover {
         transform: translateY(-8px);
         box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
         border-color: #e2e8f0;
       }
      
      .example-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
        
        .example-title {
          font-size: 18px;
          font-weight: 600;
          color: #333;
          margin: 0;
          flex: 1;
        }
        
        .example-category {
          background: #e3f2fd;
          color: #1976d2;
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
          white-space: nowrap;
          margin-left: 12px;
        }
      }
      
      .example-description {
        color: #666;
        line-height: 1.6;
        margin-bottom: 16px;
        font-size: 14px;
      }
      
             .example-action {
         color: #6366f1;
         font-weight: 500;
         font-size: 14px;
         margin-bottom: 20px;
       }
      
      .example-preview {
        height: 80px;
        border-radius: 8px;
        background: #f8f9fa;
        padding: 12px;
        
        .code-preview {
          .code-lines {
            .code-line {
              height: 8px;
              background: #ddd;
              border-radius: 4px;
              margin-bottom: 6px;
              
              &.short { width: 60%; }
              &.medium { width: 80%; }
            }
          }
        }
        
        .chart-preview {
          .chart-bars {
            display: flex;
            align-items: end;
            gap: 8px;
            height: 100%;
            
                         .bar {
               flex: 1;
               background: linear-gradient(to top, #6366f1, #8b5cf6);
               border-radius: 2px;
               min-height: 20%;
             }
          }
        }
        
        .table-preview {
                     .table-row {
             height: 12px;
             background: #ddd;
             border-radius: 2px;
             margin-bottom: 4px;
             
             &.header {
               background: #6366f1;
             }
           }
        }
        
        .pie-preview {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100%;
          
                     .pie-chart {
             width: 50px;
             height: 50px;
             border-radius: 50%;
             position: relative;
             background: conic-gradient(#6366f1 0deg 120deg, #8b5cf6 120deg 240deg, #f59e0b 240deg);
           }
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .homepage {
    padding: 20px 10px;
  }
  
  .logo-section {
    .logo-container {
      flex-direction: column;
      gap: 12px;
      
      .brand-name {
        font-size: 36px;
      }
    }
  }
  
     .search-section {
     .search-container {
       padding: 24px;
       
       .search-box .search-input-wrapper {
         min-height: 140px;
         
         .search-input {
           min-height: 100px;
         }
       }
       
       .search-input {
         padding: 12px 16px 52px 16px;
       }
       
       .search-controls {
         bottom: 8px;
         left: 16px;
         right: 16px;
         
         .search-toggle {
           padding: 8px 16px;
           font-size: 14px;
         }
         
         .search-send-container {
           .shortcut-hint {
             display: none;
           }
           
           .send-button {
             width: 36px;
             height: 36px;
             font-size: 18px;
           }
         }
       }
     }
   }
  
  .examples-section {
    .examples-grid {
      grid-template-columns: 1fr;
    }
  }
}
</style> 