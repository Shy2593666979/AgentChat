<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const searchQuery = ref('')
// 深度搜索开关已移除

// 检测是否为Mac系统
const isMac = computed(() => {
  return typeof navigator !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0
})

const modes: {key: string, label: string, color: string, icon: string}[] = []

const examples = [
  {
    title: '自动构建智能体',
    category: '自动模式',
    description: '使用多个工具相互配合完成自动构建智能体的任务',
    action: '开始构建 →'
  },
  {
    title: '深度搜索',
    category: '搜索模式',
    description: '连接外部互联网资源，扩展系统能力和数据源',
    action: '开始搜索 →'
  },
  {
    title: 'AI日报',
    category: '生成模式',
    description: '对最近的AI新闻进行整理总结，可生成下载下载链接',
    action: '生成日报 →'
  },
  {
    title: '知识库问答',
    category: '知识库模式',
    description: '基于已有知识库进行精准问答和信息检索',
    action: '查询知识 →'
  }
]

const handleSearch = async () => {
  if (searchQuery.value.trim()) {
    // 直接跳转到Mars对话页面，并传递用户输入
    router.push({
      path: '/mars',
      query: {
        message: searchQuery.value
      }
    })
  }
}

// 模式相关函数和深度搜索开关已移除

const handleKeydown = (event: KeyboardEvent) => {
  // Cmd+Enter (Mac) 或 Ctrl+Enter (Windows) 发送
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    event.preventDefault()
    handleSearch()
  }
  // Shift+Enter 换行（默认行为，不需要处理）
}

const handleExampleClick = async (example: any, index: number) => {
  // 根据索引确定example_id (索引从0开始，而example_id从1开始)
  const example_id = index + 1
  
  // 直接跳转到Mars对话页面，并传递example_id
  router.push({
    path: '/mars',
    query: {
      example_id: example_id
    }
  })
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
               placeholder="Mars Agent会完成你的任务并输出结果。"
               class="search-input"
               @keydown="handleKeydown"
               rows="3"
             ></textarea>
             
             <!-- 底部控制按钮 -->
             <div class="search-controls">
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

        <!-- 模式选择已移除 -->
      </div>
    </div>

    <!-- 优秀案例区域 -->
    <div class="examples-section">
      <h2 class="section-title">
        优秀案例
        <span class="section-subtitle">    </span>
      </h2>

      <div class="examples-grid">
        <div
          v-for="(example, index) in examples"
          :key="index"
          class="example-card"
          @click="handleExampleClick(example, index)"
        >
          <div class="example-header">
            <h3 class="example-title">{{ example.title }}</h3>
            <span class="example-category">{{ example.category }}</span>
          </div>
          <p class="example-description">{{ example.description }}</p>
          <div class="example-action">{{ example.action }}</div>
          
          <!-- 模拟图表/内容预览 -->
          <div class="example-preview">
            <div v-if="index === 0" class="robot-preview">
              <div class="assembly-icon"></div>
              <div class="assembly-tools">
                <div class="tool-box"></div>
                <div class="connector"></div>
                <div class="component"></div>
              </div>
            </div>
            <div v-else-if="index === 1" class="search-preview">
              <div class="search-container">
                <div class="search-box"></div>
                <div class="search-icon">🔍</div>
              </div>
              <div class="search-waves">
                <div class="wave wave1"></div>
                <div class="wave wave2"></div>
                <div class="wave wave3"></div>
              </div>
            </div>
            <div v-else-if="index === 2" class="news-preview">
              <div class="news-header">
                <div class="news-title"></div>
                <div class="news-date"></div>
              </div>
              <div class="news-content">
                <div class="news-line long"></div>
                <div class="news-line medium"></div>
                <div class="news-line short"></div>
                <div class="news-line medium"></div>
              </div>
              <div class="news-badge">AI</div>
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
  padding: 10px 15px; /* 进一步减少填充 */
  overflow-y: auto;
  /* 隐藏右侧滚动条，仍保留滚动功能 */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
  &::-webkit-scrollbar { display: none; } /* WebKit */
}

.logo-section {
  text-align: center;
  margin-bottom: 30px; /* 增加顶部Logo与搜索框的间距 */
  
  .logo-container {
    display: inline-flex;
    align-items: center;
    gap: 16px; /* 增加间距 */
    
    .logo {
      width: 60px; /* 增大logo尺寸 */
      height: 60px; /* 增大logo尺寸 */
      filter: drop-shadow(0 5px 15px rgba(0, 0, 0, 0.18));
    }
    
    .brand-name {
       font-size: 48px; /* 增大品牌名称字体大小 */
       font-weight: 800;
      background: linear-gradient(135deg, #3b82f6 0%, #2563eb 35%, #1d4ed8 70%, #60a5fa 100%);
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
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.4), rgba(29, 78, 216, 0.4));
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
        background: linear-gradient(90deg, transparent, #3b82f6, #60a5fa, #3b82f6, transparent);
         border-radius: 2px;
         opacity: 0.6;
       }
     }
  }
  

}

.search-section {
  max-width: 750px; /* 进一步增加最大宽度 */
  margin: 0 auto 28px; /* 进一步增加搜索框与优秀案例之间的间距 */
  
     .search-container {
     background: #ffffff;
     border-radius: 22px; /* 增加圆角 */
     padding: 32px; /* 进一步增加内部填充 */
     box-shadow: 0 12px 40px rgba(0, 0, 0, 0.08); /* 增强阴影效果 */
     border: 1px solid #f1f5f9;
   }
  
  .search-box {
    margin-bottom: 18px; /* 增加搜索框内部元素间距 */
    
         .search-input-wrapper {
       background: #f8f9fa;
       border-radius: 16px; /* 减小圆角 */
       padding: 14px; /* 进一步增加内边距 */
       border: 1px solid #e9ecef; /* 减小边框 */
       transition: all 0.3s ease;
       min-height: 160px; /* 进一步增加输入框高度，充分利用底部留白 */
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
         padding: 12px 18px 45px 18px; /* 进一步增加内边距 */
         font-size: 19px; /* 进一步增加字体大小 */
         outline: none;
         color: #333;
         line-height: 1.6; /* 增加行高 */
         resize: none;
         font-family: inherit;
         min-height: 130px; /* 进一步增加最小高度 */
         box-sizing: border-box;
         
         &::placeholder {
           color: #8a8a8a;
         }
       }
      
      
    }
  }
  
  /* 模式选择器样式已移除 */
  
  .search-controls {
    position: absolute;
    bottom: 8px;
    left: 12px;
    right: 12px;
    display: flex;
    justify-content: flex-end;
    align-items: center;
    pointer-events: none;
    
    > * {
      pointer-events: auto;
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
  max-width: 1100px; /* 减小最大宽度 */
  margin: 0 auto;
  padding-top: 5px; /* 减少顶部填充 */
  
  .section-title {
    text-align: center;
    font-size: 24px; /* 进一步减小标题字体大小 */
    font-weight: 700;
    color: #333333;
    margin-bottom: 5px; /* 进一步减少标题底部间距 */
    
    .section-subtitle {
      display: block;
      font-size: 14px; /* 减小副标题字体大小 */
      font-weight: 400;
      color: #666666;
      margin-top: 4px; /* 减少上边距 */
    }
  }
  
  .examples-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); /* 稍微增加卡片最小宽度 */
    gap: 18px; /* 增加卡片间距 */
    margin-top: 12px; /* 增加顶部间距 */
    
         .example-card {
       background: #ffffff;
       border-radius: 12px; /* 进一步减小圆角 */
       padding: 15px; /* 进一步减少内部填充 */
       cursor: pointer;
       transition: all 0.3s ease;
       border: 1px solid #f1f5f9;
       position: relative;
       overflow: hidden;
       box-shadow: 0 3px 8px rgba(0, 0, 0, 0.03); /* 减轻阴影 */
       
       &:hover {
         transform: translateY(-8px);
         box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
         border-color: #e2e8f0;
       }
      
      .example-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 8px; /* 减少底部间距 */
        
        .example-title {
          font-size: 16px; /* 减小标题字体大小 */
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
        line-height: 1.4; /* 减小行高 */
        margin-bottom: 10px; /* 减少底部间距 */
        font-size: 13px; /* 减小字体大小 */
      }
      
             .example-action {
         color: #6366f1;
         font-weight: 500;
         font-size: 13px; /* 减小字体大小 */
         margin-bottom: 12px; /* 减少底部间距 */
       }
      
      .example-preview {
        height: 60px; /* 进一步减少预览区域高度 */
        border-radius: 6px; /* 减小圆角 */
        background: #f8f9fa;
        padding: 8px; /* 进一步减少内部填充 */
        
        .robot-preview {
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          height: 100%;
          position: relative;
          
          .assembly-icon {
            width: 24px;
            height: 24px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            border-radius: 6px;
            position: relative;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 6px rgba(99, 102, 241, 0.3);
            
            &::before {
              content: '⚡';
              color: white;
              font-size: 12px;
            }
          }
          
          .assembly-tools {
            display: flex;
            align-items: center;
            gap: 4px;
            
            .tool-box {
              width: 8px;
              height: 6px;
              background: linear-gradient(135deg, #f59e0b, #d97706);
              border-radius: 2px;
              box-shadow: 0 1px 2px rgba(245, 158, 11, 0.3);
            }
            
            .connector {
              width: 12px;
              height: 2px;
              background: #64748b;
              border-radius: 1px;
            }
            
            .component {
              width: 6px;
              height: 6px;
              background: linear-gradient(135deg, #10b981, #059669);
              border-radius: 50%;
              box-shadow: 0 1px 2px rgba(16, 185, 129, 0.3);
            }
          }
        }
        
                .search-preview {
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          height: 100%;
          position: relative;
          
          .search-container {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 8px;
            
            .search-box {
              width: 35px;
              height: 12px;
              background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
              border: 2px solid #3b82f6;
              border-radius: 8px;
              position: relative;
              box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.3);
              
              &::before {
                content: '';
                position: absolute;
                left: 3px;
                top: 50%;
                transform: translateY(-50%);
                width: 6px;
                height: 2px;
                background: #64748b;
                border-radius: 1px;
              }
            }
            
            .search-icon {
              font-size: 12px;
              filter: drop-shadow(0 1px 2px rgba(59, 130, 246, 0.4));
            }
          }
          
          .search-waves {
            position: absolute;
            bottom: 8px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 2px;
            
            .wave {
              width: 3px;
              background: linear-gradient(to top, #3b82f6, #60a5fa);
              border-radius: 2px;
              
              &.wave1 {
                height: 4px;
              }
              &.wave2 {
                height: 6px;
              }
              &.wave3 {
                height: 5px;
              }
            }
          }
        }
        
                .news-preview {
          padding: 6px;
          background: linear-gradient(135deg, #fefefe, #f8fafc);
          border: 1px solid #e2e8f0;
          border-radius: 4px;
          position: relative;
          
          .news-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            
            .news-title {
              width: 70%;
              height: 8px;
              background: linear-gradient(90deg, #1e40af, #3b82f6);
              border-radius: 2px;
              box-shadow: 0 1px 3px rgba(30, 64, 175, 0.3);
            }
            
            .news-date {
              width: 20%;
              height: 4px;
              background: #94a3b8;
              border-radius: 2px;
            }
          }
          
          .news-content {
            .news-line {
              height: 4px;
              background: linear-gradient(90deg, #64748b, #94a3b8);
              border-radius: 2px;
              margin-bottom: 3px;
              
              &.long { 
                width: 100%; 
              }
              &.medium { 
                width: 75%; 
              }
              &.short { 
                width: 45%; 
              }
            }
          }
          
          .news-badge {
            position: absolute;
            top: 4px;
            right: 4px;
            background: linear-gradient(135deg, #dc2626, #ef4444);
            color: white;
            font-size: 8px;
            font-weight: 700;
            padding: 2px 4px;
            border-radius: 3px;
            box-shadow: 0 1px 3px rgba(220, 38, 38, 0.4);
          }
          
          &::before {
            content: '📰';
            position: absolute;
            bottom: 2px;
            left: 4px;
            font-size: 10px;
            opacity: 0.6;
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
            background: conic-gradient(
              #6366f1 0deg 120deg, 
              #8b5cf6 120deg 240deg, 
              #f59e0b 240deg
            );
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
            
            &::before {
              content: '';
              position: absolute;
              top: 50%;
              left: 50%;
              transform: translate(-50%, -50%);
              width: 20px;
              height: 20px;
              background: white;
              border-radius: 50%;
              box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
            }
            
            &::after {
              content: '';
              position: absolute;
              top: 50%;
              left: 50%;
              transform: translate(-50%, -50%);
              width: 8px;
              height: 8px;
              background: linear-gradient(45deg, #6366f1, #8b5cf6);
              border-radius: 50%;
            }
          }
        }
      }
    }
  }
}

// 静态样式，不再需要动画

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