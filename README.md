
<div align='center'>
    <img src="https://github.com/user-attachments/assets/eb9b3b09-e2bf-4c9d-95a0-5c2d9712723d" alt="alt text" width="70%">
</div>

<div align="center">

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/vue-3.4+-4FC08D.svg?style=for-the-badge&logo=vue.js&logoColor=white" alt="Vue Version" />
  <img src="https://img.shields.io/badge/fastapi-0.115+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge" alt="License" />
</p>

<p align="center">
  <b>🌟 一个基于大语言模型的现代化智能对话系统 🌟</b>
</p>

<p align="center">
  支持多Agent协作 • 知识库检索 • 工具调用 • MCP服务器集成 • 实时对话
</p>

<p align="center">
  <a href="https://shy2593666979.github.io/agentchat-docs/%E5%BF%AB%E9%80%9F%E5%85%A5%E9%97%A8.html">🚀 快速开始</a> •
  <a href="https://shy2593666979.github.io/agentchat-docs/%E5%BC%80%E5%8F%91%E6%8C%87%E5%8D%97/%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA.html">📦 部署</a> •
  <a href="https://shy2593666979.github.io/agentchat-docs/">📖 在线文档</a> •
  <a href="https://agentchat.cloud">💻 在线体验</a>
</p>

</div>

---

## 最新版本更新日志 (2026-3-8)

### 1. 支持MiniO本地对象存储
现在支持OSS和MiniO两种对象存储方式，参考文档: [本地安装MiniO](docs/development/install_minio_win.md)，感谢提供Issue的朋友:
- 👤 [@xiaoyan011016](https://github.com/xiaoyan011016)
- 👤 [@shenmi888](https://github.com/shenmi888)

### 2. 优化Docker直接部署项目
(1) 前版本docker部署经常会出现 `agentchat-frontend` 连不上 `agentchat-backend` 的网络失败情况，已经修复该bug

(2) 缺少Win系统下的一键部署脚本，目前已经加上 (start_win.bat)

感谢提供Issue朋友:
- 👤 [@R-322](https://github.com/R-322)

### 3. 支持自定义工具
之前点击自定义工具是无事件，目前可通过上传 Swagger/OpenAPI 构建自己的工具，感谢提供Issue朋友：
- 👤 [@shenmi888](https://github.com/shenmi888)

### 4. 支持Skill
现已支持通过创建 Skill 绑定到智能体渐进式加载 Prompt 去教模型如何做事，感谢提供Issue朋友：
- 👤 [@opaquezxd](https://github.com/opaquezxd)

### 5.优化页面样式
前版本中系统设置为空白，现在已经去除，感谢提供Issue朋友：
- 👤[@wxliu07](https://github.com/wxliu07)

---

## 📋 目录

- [🎯 项目简介](#-项目简介)
- [✨ 功能展示](#-功能展示)
- [🚨 重要版本说明](#-重要版本说明)
- [💡 功能特性](#-功能特性)
- [🛠 技术栈](#-技术栈)
- [📁 项目结构](#-项目结构)
- [🚀 快速开始](#-快速开始)
- [📦 部署](#-高级部署指南)
- [📖 文档](#-文档)
- [📄 许可证](#-许可证)

---

## 🎯 项目简介

AgentChat 是一个现代化的智能对话系统，基于大语言模型构建，提供了丰富的AI对话功能。系统采用前后端分离架构，支持多种AI模型、知识库检索、工具调用、MCP服务器集成等高级功能。

### 🌟 核心亮点

- 🤖 **多模型支持**: 集成OpenAI、DeepSeek、Qwen等主流大语言模型
- 🧠 **智能Agent**: 支持多Agent协作，具备推理和决策能力
- 📚 **知识库检索**: RAG技术实现精准知识检索和问答
- 🔧 **工具生态**: 内置多种实用工具，支持自定义扩展
- 🌐 **MCP集成**: 支持Model Context Protocol服务器
- 💬 **实时对话**: 流式响应，提供流畅的对话体验
- 🎨 **现代界面**: 基于Vue 3和Element Plus的美观UI

---

## ✨ 功能展示

> 🎨 **界面预览** - 体验现代化的智能对话系统

<div align="center">

### 🖥️新增工作区
*新增工作区，工作区和应用中心可随意切换*
<img width="800" height="450" alt="c453afd6-84ed-4bb7-b268-407fb531a1c9" src="https://github.com/user-attachments/assets/766c7628-2256-4c8b-a838-c400eaa78d6b" />


### ✨灵寻任务规划
*实时的任务流程图，更加直观的感受*
<img width="800" height="450" alt="cc59faad-4112-48cd-b9b1-6f89d3cbdb39" src="https://github.com/user-attachments/assets/53f7fe9f-d70d-4cc2-bf7e-b47a712a6d7a" />

### 📊数据看板
*能够根据Agent、模型、时间范围进行筛选调用次数和Token使用量* 
<img width="800" height="450" alt="73f74567-7a97-4cd8-ab05-34759efa25cc" src="https://github.com/user-attachments/assets/b0cb4ccf-b868-4f1b-9b26-8a882d8130da" />


### 🏠 智言平台首页
*简洁现代的主界面，提供直观的功能导航*
<img width="800" height="450" alt="d0aaf6bb-d1db-487b-b78b-2a5c6ef565d2" src="https://github.com/user-attachments/assets/dc626494-4797-4a86-b350-3a0759d52d64" />



### 🔐 智言平台登录页
*安全便捷的用户认证系统*

<img width="800" height="450" alt="d67ba546-b3bd-40e0-b09c-9b1615afda29" src="https://github.com/user-attachments/assets/87b6e15c-a4aa-47c5-b588-0bc977599311" />


### 🤖 智能体管理页面
*强大的Agent配置和管理中心*

<img width="800" height="450" alt="66830e14-e225-48e6-9d3c-7736cea7b336" src="https://github.com/user-attachments/assets/b24d47ee-17ea-4cc3-bfd2-53cf93c87ebb" />

</div>

### 🌟 智能Agent功能演示

<table>
<tr>
<td width="50%">

#### 🌤️ 天气查询Agent
*实时天气信息查询和预报*

<img width="400" height="240" alt="天气查询Agent" src="https://github.com/user-attachments/assets/91a95c2b-f194-4c25-ba0f-f8cb393cba50" />

</td>
<td width="50%">

#### 🎨 文生图Agent
*AI驱动的图像生成服务*

<img width="400" height="240" alt="文生图Agent" src="https://github.com/user-attachments/assets/58194798-5c3e-4d7d-895c-944b6665e5a6" />


</td>
</tr>
</table>

<div align="center">

<div align="center">

### 🔁智能体工具多轮调用

平台中智能体支持工具多轮调用（指的是根据工具C依赖工具B结果，执行工具B依赖工具A结果，所以调用工具的顺序是 A --> B --> C）
<img width="800" height="450" alt="dc426a1b220af20a06b068a4ffc2bb10" src="https://github.com/user-attachments/assets/029c70ce-e5fa-4f2c-926a-a5dfd719e237" />

<div align="center">

### 🔌 MCP服务器集成
*支持Model Context Protocol，可上传自定义MCP服务*

<img width="800" height="450" alt="7a88f691-a1e5-4568-91c0-c74488914d5c" src="https://github.com/user-attachments/assets/79bfa401-bd94-4290-b7ae-bcb69cc00f64" />


### 📚 知识库管理系统
*智能知识管理，为Agent提供丰富的外部知识支持*

<img width="800" height="450" alt="99c68f9f-d787-4434-b609-000f578e5977" src="https://github.com/user-attachments/assets/0de41202-295a-43c5-a15c-c0b3cc55e5f8" />


### 📄 文档解析引擎
*支持PDF、Markdown、Docx、Txt等多种格式的智能解析*

<img width="800" height="450" alt="5c7d4514-3e73-4dee-a25e-640e2b345bc6" src="https://github.com/user-attachments/assets/c5eba600-7dc2-429a-88f9-50f8811f293b" />


### 🛠️ 工具管理中心
*丰富的内置工具集，支持用户自定义上传工具*

<img width="800" height="450" alt="7c50278e-3152-4fa0-99c6-46462cb66b7e" src="https://github.com/user-attachments/assets/6a0126d2-5042-4131-816e-5d049d09728c" />


### 🧠 AI模型管理
*多模型支持，灵活配置不同AI服务*

<img width="800" height="450" alt="32c29244-175c-4b20-8485-63f87a35216e" src="https://github.com/user-attachments/assets/97053c0d-a57c-4347-9cf1-1ab96fa7fc22" />


### 📰 生成AI日报
*获取最新的AI咨询，支持生成图片类型的日报*

<img width="500" height="1500" alt="image" src="https://github.com/user-attachments/assets/a4f4489a-19bf-4516-96db-77ff2525beb8" />


</div>


## 🚨 重要版本说明

> **⚠️ 从 AgentChat v2.2.0 版本开始，LangChain 已升级至 1.0 版本，代码改动较大！**

<div align="center">

| 🔄 **版本** | 📦 **LangChain版本** | 🔧 **兼容性** | 📝 **说明** |
|:---:|:---:|:---:|:---|
| **v2.1.x 及以下** | 0.x | ⚠️ 旧版本 | 使用旧版LangChain API |
| **v2.2.0+** | 1.0+ | ✅ 最新版本 | **重大更新**，API变化较大 |

</div>

**升级注意事项：**
- 🔄 LangChain 1.0 引入了重大API变更
- 📚 部分工具和Agent配置方式已更新
- 🛠️ 建议查看[迁移指南](docs/reference/migration.md)了解详细变更
- 💡 新用户建议直接使用最新版本

---

## 💡 功能特性

> ⭐ **全方位的AI智能服务** - 从对话到工具，从知识到决策

<div align="center">

### 🎯 核心功能模块

</div>

<table>
<tr>
<td width="50%">

#### 🤖 **AI对话引擎**
> *智能、自然、高效的对话体验*

- ✨ **多模型生态**: 支持OpenAI、Anthropic、通义千问等主流LLM
- 🌊 **流式响应**: 实时显示生成内容，无需等待
- 🧠 **上下文记忆**: 支持长对话，智能理解对话历史
- 🔍 **思考可视化**: 深度思考面板，展示AI推理过程
- 📝 **对话管理**: 完整的对话历史存储和检索
- 🎛️ **参数调优**: 温度、Top-p等参数精细控制

</td>
<td width="50%">

#### 🧠 **智能Agent系统**
> *多智能体协作，自动化任务执行*

- 🤝 **多Agent协作**: 智能体间任务分工与协调
- 🔧 **任务自动化**: 智能分解复杂任务，自动执行
- ⚙️ **能力配置**: 灵活的Agent能力定义和管理
- 🔄 **工作流编排**: 可视化工作流设计和执行
- 📊 **执行监控**: 实时监控Agent执行状态
- 🎯 **目标导向**: 基于目标的智能决策和行动

</td>
</tr>
</table>

<table>
<tr>
<td width="50%">

#### 📚 **知识库系统**
> *企业级知识管理，RAG技术加持*

- 📎 **多格式支持**: PDF、Word、Excel、Markdown、TXT等
- 🧩 **智能分块**: 语义级别的文档分割和处理
- 🔍 **向量检索**: 基于语义的精准知识检索
- 💡 **RAG问答**: 检索增强生成，提高回答准确性
- 🗂️ **知识组织**: 分类管理，标签系统
- 📈 **使用统计**: 知识库使用情况分析

</td>
<td width="50%">

#### 🛠️ **丰富工具生态**
> *10+内置工具，无限扩展可能*

- 📧 **通信工具**: 邮件发送、消息推送
- 🔍 **信息检索**: Google搜索、学术论文搜索
- 🌤️ **生活服务**: 天气查询、快递追踪
- 📄 **文档处理**: 格式转换、内容提取
- 🎨 **多媒体**: 文生图、图像识别、OCR
- 📊 **数据分析**: Excel处理、数据可视化
- 🤖 **自动化**: 简历优化、内容重写
- 🕷️ **网络工具**: 网页爬取、内容抓取

</td>
</tr>
</table>

<div align="center">

### 🔧 **高级特性**

</div>

<table>
<tr>
<td width="33%">

#### 🌐 **MCP服务器**
*Model Context Protocol集成*

- 🔌 **协议支持**: 完整MCP协议实现
- 🏗️ **自定义服务**: 支持用户自定义MCP服务器
- 📦 **内置服务**: 天气、ArXiv等预构建服务
- 🔄 **动态加载**: 运行时动态加载MCP服务
- ⚡ **高性能**: 异步处理，快速响应

</td>
<td width="33%">

#### 👤 **用户管理**
*安全的身份认证与权限控制*

- 🔐 **安全认证**: JWT令牌，安全可靠
- 👥 **用户系统**: 注册、登录、个人资料
- 🛡️ **权限控制**: 细粒度权限管理
- ⚙️ **个性配置**: 个人偏好设置
- 📊 **使用统计**: 用户行为分析

</td>
<td width="33%">

#### 🏗️ **系统架构**
*现代化的技术架构*

- 🔄 **前后端分离**: Vue3 + FastAPI
- 📡 **实时通信**: WebSocket支持
- 💾 **多数据库**: MySQL、Redis、ChromaDB
- 🐳 **容器化**: Docker部署，易于扩展
- 📈 **可监控**: 完整的日志和监控体系

</td>
</tr>
</table>

### 🎨 **技术亮点**

<div align="center">

| 🌟 **特性** | 📝 **描述** | 🔧 **技术** |
|:---:|:---|:---|
| **流式响应** | 实时生成内容，提升用户体验 | Server-Sent Events |
| **向量检索** | 语义级别的知识检索 | ChromaDB + Embedding |
| **异步处理** | 高并发任务处理 | FastAPI + AsyncIO |
| **模块化设计** | 松耦合架构，易于扩展 | 微服务架构 |
| **智能缓存** | Redis缓存，提升响应速度 | Redis + 智能缓存策略 |

</div>

---

## 🛠 技术栈

### 后端技术
- **框架**: FastAPI (Python 3.12+)
- **AI集成**: LangChain, OpenAI, Anthropic
- **数据库**: MySQL 8.0, Redis 7.0
- **向量数据库**: ChromaDB, Milvus
- **搜索引擎**: Elasticsearch
- **文档处理**: PyMuPDF, Unstructured
- **异步任务**: Celery
- **部署**: Docker, Gunicorn, Uvicorn

### 前端技术
- **框架**: Vue 3.4+ (Composition API)
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **构建工具**: Vite 5
- **开发语言**: TypeScript
- **样式**: SCSS
- **Markdown**: md-editor-v3

### 开发工具
- **包管理**: Poetry (后端), npm (前端)
- **代码格式**: Black, Prettier
- **类型检查**: mypy, TypeScript
- **容器化**: Docker, Docker Compose

---

## 📁 项目结构

> 🏗️ **完整的项目架构** - 模块化设计，清晰的职责分离

<details>
<summary><b>🔍 点击展开完整项目结构</b></summary>

```
AgentChat/                          # 🏠 项目根目录
├── 📄 README.md                   # 📖 项目说明文档
├── 📄 LICENSE                     # ⚖️ 开源许可证
├── 📄 .gitignore                  # 🚫 Git忽略文件配置
├── 📄 pyproject.toml              # 🐍 Python项目配置
├── 📄 requirements.txt            # 📦 Python依赖包列表
│
├── 📁 .vscode/                    # 🔧 VSCode编辑器配置
├── 📁 .idea/                      # 💡 JetBrains IDE配置
│
├── 📁 docs/                       # 📚 项目文档目录
│   ├── 📄 API_Documentation_v3.0.md  # 🔄 最新API文档
│   ├── 📄 API_Documentation_v2.0.md  # 📋 v2.0 API文档
│   └── 📄 API_Documentation_v1.0.md  # 📝 v1.0 API文档
│
├── 📁 docker/                     # 🐳 容器化配置
│   ├── 📄 Dockerfile              # 🐳 Docker镜像构建文件
│   └── 📄 docker-compose.yml      # 🔧 Docker编排配置
│
└── 📁 src/                        # 💻 源代码目录
    ├── 📁 backend/                # 🔧 后端服务
    │   ├── 📁 chroma_db/          # 🗄️ ChromaDB向量数据库
    │   └── 📁 agentchat/          # 🤖 核心后端应用
    │       ├── 📄 __init__.py     # 🐍 Python包初始化文件
    │       ├── 📄 main.py         # 🚀 FastAPI应用入口
    │       ├── 📄 settings.py     # ⚙️ 应用配置设置
    │       ├── 📄 config.yaml     # 📋 YAML配置文件
    │       │
    │       ├── 📁 api/            # 🌐 API路由层
    │       │   ├── 📄 __init__.py
    │       │   ├── 📄 router.py   # 🔀 主路由配置
    │       │   ├── 📄 JWT.py      # 🔐 JWT认证处理
    │       │   ├── 📁 v1/         # 📊 v1版本API接口
    │       │   ├── 📁 services/   # 🔧 服务层API
    │       │   └── 📁 errcode/    # ❌ 错误码定义
    │       │
    │       ├── 📁 core/           # 🏗️ 核心功能模块
    │       │   ├── 📄 __init__.py
    │       │   └── 📁 models/     # 🧠 AI模型管理
    │       │
    │       ├── 📁 database/       # 🗃️ 数据库层
    │       │   ├── 📄 __init__.py # 🔗 数据库连接配置
    │       │   ├── 📄 init_data.py # 🏗️ 数据库初始化脚本
    │       │   ├── 📁 models/     # 📊 数据模型定义
    │       │   └── 📁 dao/        # 💾 数据访问对象
    │       │
    │       ├── 📁 services/       # 🎯 业务服务层
    │       │   ├── 📄 __init__.py
    │       │   ├── 📄 retrieval.py      # 🔍 信息检索服务
    │       │   ├── 📄 rag_handler.py    # 📚 RAG处理服务
    │       │   ├── 📄 aliyun_oss.py     # ☁️ 阿里云OSS服务
    │       │   ├── 📄 redis.py          # 💾 Redis缓存服务
    │       │   ├── 📁 rag/              # 📖 RAG检索增强生成
    │       │   ├── 📁 mars/             # 🚀 Mars智能体服务
    │       │   ├── 📁 mcp/              # 🔌 MCP协议服务
    │       │   ├── 📁 mcp_agent/        # 🤖 MCP Agent服务
    │       │   ├── 📁 mcp_openai/       # 🧠 MCP OpenAI集成
    │       │   ├── 📁 deepsearch/       # 🕵️ 深度搜索服务
    │       │   ├── 📁 transform_paper/  # 📄 论文转换服务
    │       │   ├── 📁 autobuild/        # 🏗️ 自动构建服务
    │       │   └── 📁 rewrite/          # ✏️ 内容重写服务
    │       │
    │       ├── 📁 tools/          # 🛠️ 工具集成
    │       │   ├── 📄 __init__.py # 🧰 工具注册和管理
    │       │   ├── 📁 arxiv/      # 📚 ArXiv论文工具
    │       │   ├── 📁 delivery/   # 📦 快递查询工具
    │       │   ├── 📁 web_search/ # 🔍 网络搜索工具
    │       │   ├── 📁 get_weather/     # 🌤️ 天气查询工具
    │       │   ├── 📁 send_email/      # 📧 邮件发送工具
    │       │   ├── 📁 text2image/      # 🎨 文本转图片工具
    │       │   ├── 📁 image2text/      # 👁️ 图片转文本工具
    │       │   ├── 📁 convert_to_pdf/  # 📄 PDF转换工具
    │       │   ├── 📁 convert_to_docx/ # 📝 Word转换工具
    │       │   ├── 📁 resume_optimizer/# 📋 简历优化工具
    │       │   ├── 📁 rag_data/        # 📊 RAG数据处理工具
    │       │   └── 📁 crawl_web/       # 🕷️ 网页爬虫工具
    │       │
    │       ├── 📁 mcp_servers/    # 🖥️ MCP服务器集合
    │       ├── 📁 prompts/        # 💬 提示词模板库
    │       ├── 📁 config/         # ⚙️ 配置文件目录
    │       ├── 📁 schema/         # 📋 数据模式定义
    │       ├── 📁 data/           # 💾 数据存储目录
    │       ├── 📁 utils/          # 🧰 通用工具函数
    │       └── 📁 test/           # 🧪 测试代码目录
    │
    └── 📁 frontend/               # 🎨 前端应用
        ├── 📄 package.json       # 📦 Node.js项目配置
        ├── 📄 package-lock.json  # 🔒 依赖版本锁定
        ├── 📄 tsconfig.json      # 🔧 TypeScript配置
        ├── 📄 tsconfig.app.json  # 📱 应用TypeScript配置
        ├── 📄 tsconfig.node.json # 🔧 Node环境TypeScript配置
        ├── 📄 vite.config.ts     # ⚡ Vite构建配置
        ├── 📄 index.html         # 🌐 HTML入口文件
        ├── 📄 .gitignore         # 🚫 前端Git忽略配置
        ├── 📄 README.md          # 📖 前端说明文档
        ├── 📄 DEBUGGING_GUIDE.md # 🐛 调试指南
        ├── 📄 auto-imports.d.ts  # 🔄 自动导入类型声明
        ├── 📄 components.d.ts    # 🧩 组件类型声明
        │
        ├── 📁 public/            # 🌍 静态资源目录
        │
        └── 📁 src/               # 💻 前端源代码
            ├── 📄 main.ts        # 🚀 Vue应用入口
            ├── 📄 App.vue        # 🏠 根组件
            ├── 📄 style.css      # 🎨 全局样式
            ├── 📄 type.ts        # 📋 TypeScript类型定义
            ├── 📄 vite-env.d.ts  # 🔧 Vite环境类型声明
            │
            ├── 📁 components/    # 🧩 可复用组件库
            │   ├── 📁 agentCard/      # 🤖 Agent卡片组件
            │   ├── 📁 commonCard/     # 🃏 通用卡片组件
            │   ├── 📁 dialog/         # 💬 对话框组件
            │   ├── 📁 drawer/         # 📜 抽屉组件
            │   └── 📁 historyCard/    # 📜 历史记录卡片
            │
            ├── 📁 pages/         # 📄 页面组件
            │   ├── 📄 index.vue       # 🏠 首页
            │   ├── 📁 agent/          # 🤖 Agent管理页面
            │   ├── 📁 configuration/ # ⚙️ 配置页面
            │   ├── 📁 construct/      # 🏗️ 构建页面
            │   ├── 📁 conversation/   # 💬 对话页面
            │   ├── 📁 homepage/       # 🏠 主页模块
            │   ├── 📁 knowledge/      # 📚 知识库页面
            │   ├── 📁 login/          # 🔐 登录页面
            │   ├── 📁 mars/           # 🚀 Mars对话页面
            │   ├── 📁 mcp-server/     # 🖥️ MCP服务器页面
            │   ├── 📁 model/          # 🧠 模型管理页面
            │   ├── 📁 notFound/       # ❓ 404页面
            │   ├── 📁 profile/        # 👤 用户资料页面
            │   └── 📁 tool/           # 🛠️ 工具管理页面
            │
            ├── 📁 router/        # 🛣️ 路由配置
            ├── 📁 store/         # 🗄️ 状态管理(Pinia)
            ├── 📁 apis/          # 🌐 API接口定义
            ├── 📁 utils/         # 🧰 工具函数库
            └── 📁 assets/        # 🖼️ 静态资源(图片、字体等)
```

</details>

### 📊 项目统计

<div align="center">

| 📂 **类别** | 📈 **数量** | 📝 **说明** |
|:---:|:---:|:---|
| **后端模块** | 15+ | API、服务、工具、数据库等核心模块 |
| **前端页面** | 12+ | 完整的用户界面和交互页面 |
| **内置工具** | 10+ | 涵盖搜索、文档、图像、通信等功能 |
| **AI模型** | 5+ | 支持主流大语言模型和嵌入模型 |
| **MCP服务** | 多个 | 可扩展的MCP协议服务器 |

</div>


---

## 🚀 快速开始

> 🎯 **三种部署方式任你选择** - Docker一键部署 | 本地开发 | 生产环境

<div align="center">

### 📋 系统要求

| 🛠️ **组件** | 🔢 **版本要求** | 📝 **说明** |
|:---:|:---:|:---|
| **Python** | 3.12+ | 后端运行环境 |
| **Node.js** | 18+ | 前端构建环境 |
| **MySQL** | 8.0+ | 主数据库 |
| **Redis** | 7.0+ | 缓存和会话存储 |
| **Docker** | 20.10+ | 容器化部署（推荐） |

</div>

### 🎉 **方式一：Docker一键部署（推荐）**

<details>
<summary><b>💫 点击展开Docker部署步骤</b></summary>

#### 🔥 **超简单三步部署**

```bash
# 1️⃣ 克隆项目
git clone https://github.com/Shy2593666979/AgentChat.git
cd AgentChat

# 2️⃣ 配置API密钥
cp src/backend/agentchat/config.yaml.example src/backend/agentchat/config.yaml
# 编辑配置文件，填入你的API密钥

# 3️⃣ 一键启动
cd docker
docker-compose up --build -d
```

#### ✅ **验证部署**
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

🎊 **完成！** 访问 [http://localhost:8090](http://localhost:8090) 开始使用！

</details>

### 🛠️ **方式二：本地开发环境**

<details>
<summary><b>👨‍💻 点击展开本地开发步骤</b></summary>

#### 🔧 **后端环境搭建**

```bash
# 1️⃣ 克隆项目
git clone https://github.com/Shy2593666979/AgentChat.git
cd AgentChat

# 使用pip安装依赖
pip install -r requirements.txt
```


#### ⚙️ **配置文件设置**

创建并编辑配置文件 `src/backend/agentchat/config.yaml`:

#### 🚀 **启动服务**

```bash
# 后端服务
cd src/backend
uvicorn agentchat.main:app --port 7860 --host 0.0.0.0

# 新终端 - 前端服务
cd src/frontend
npm install
npm run dev
```

#### 🌐 **访问地址**

| 🎯 **服务** | 🔗 **地址** | 📝 **说明** |
|:---:|:---:|:---|
| **前端界面** | [localhost:8090](http://localhost:8090) | 用户界面 |
| **后端API** | [localhost:7860](http://localhost:7860) | API服务 |
| **API文档** | [localhost:7860/docs](http://localhost:7860/docs) | Swagger文档 |

</details>


---

## 📦 高级部署指南

> 🎯 **灵活的部署选择** - 从开发测试到生产环境的完整方案

### 🌐 **部署架构选择**

<table>
<tr>
  
<td width="33%">


---

## 📖 文档

### 📚 API文档
- [AgentChat Document](docs/reference/agentchat.md) - agentchat具体文档
- [API Documentation v3.0](docs/reference/api.md) - 最新API文档

### 🔧 开发文档
- **在线API文档**: 启动后端服务后访问 `/docs`
- **前端调试指南**: [src/frontend/DEBUGGING_GUIDE.md](src/frontend/DEBUGGING_GUIDE.md)

### 📋 配置指南

#### 向量数据库配置
- **Milvus**: [安装指南](https://milvus.io/docs/zh/install_standalone-windows.md)
- **ChromaDB**: 项目中已集成，无需额外配置

#### 模型服务配置
- **Rerank模型**: [阿里云模型服务](https://help.aliyun.com/zh/model-studio/text-rerank-api)
- **Embedding模型**: [OpenAI兼容接口](https://help.aliyun.com/zh/model-studio/embedding-interfaces-compatible-with-openai)

#### 搜索引擎配置
- **Elasticsearch**: [IK分词器](https://release.infinilabs.com/analysis-ik/stable/)

---

## 🔧 开发指南

### ⚠️ 重要提示 (目前已单独放到与agentchat并列，不需要再额外处理)

由于 `fastapi-jwt-auth` 库使用较旧版本的 Pydantic，而项目中的 LangChain、MCP 等组件需要 Pydantic >= 2，需要手动修改库文件：

找到你的虚拟环境中的文件：
```
/path/to/your/env/lib/python3.12/site-packages/fastapi_jwt_auth/config.py
```

替换为以下内容：

<details>
<summary>点击展开配置代码</summary>

```python
from datetime import timedelta
from typing import Optional, Union, Sequence, List
from pydantic import (
    BaseModel,
    validator,
    StrictBool,
    StrictInt,
    StrictStr
)

class LoadConfig(BaseModel):
    authjwt_token_location: Optional[List[StrictStr]] = ['headers']
    authjwt_secret_key: Optional[StrictStr] = None
    authjwt_public_key: Optional[StrictStr] = None
    authjwt_private_key: Optional[StrictStr] = None
    authjwt_algorithm: Optional[StrictStr] = "HS256"
    authjwt_decode_algorithms: Optional[List[StrictStr]] = None
    authjwt_decode_leeway: Optional[Union[StrictInt,timedelta]] = 0
    authjwt_encode_issuer: Optional[StrictStr] = None
    authjwt_decode_issuer: Optional[StrictStr] = None
    authjwt_decode_audience: Optional[Union[StrictStr,Sequence[StrictStr]]] = None
    authjwt_denylist_enabled: Optional[StrictBool] = False
    authjwt_denylist_token_checks: Optional[List[StrictStr]] = ['access','refresh']
    authjwt_header_name: Optional[StrictStr] = "Authorization"
    authjwt_header_type: Optional[StrictStr] = "Bearer"
    authjwt_access_token_expires: Optional[Union[StrictBool,StrictInt,timedelta]] = timedelta(minutes=15)
    authjwt_refresh_token_expires: Optional[Union[StrictBool,StrictInt,timedelta]] = timedelta(days=30)
    # # option for create cookies
    authjwt_access_cookie_key: Optional[StrictStr] = "access_token_cookie"
    authjwt_refresh_cookie_key: Optional[StrictStr] = "refresh_token_cookie"
    authjwt_access_cookie_path: Optional[StrictStr] = "/"
    authjwt_refresh_cookie_path: Optional[StrictStr] = "/"
    authjwt_cookie_max_age: Optional[StrictInt] = None
    authjwt_cookie_domain: Optional[StrictStr] = None
    authjwt_cookie_secure: Optional[StrictBool] = False
    authjwt_cookie_samesite: Optional[StrictStr] = None
    # # option for double submit csrf protection
    authjwt_cookie_csrf_protect: Optional[StrictBool] = True
    authjwt_access_csrf_cookie_key: Optional[StrictStr] = "csrf_access_token"
    authjwt_refresh_csrf_cookie_key: Optional[StrictStr] = "csrf_refresh_token"
    authjwt_access_csrf_cookie_path: Optional[StrictStr] = "/"
    authjwt_refresh_csrf_cookie_path: Optional[StrictStr] = "/"
    authjwt_access_csrf_header_name: Optional[StrictStr] = "X-CSRF-Token"
    authjwt_refresh_csrf_header_name: Optional[StrictStr] = "X-CSRF-Token"
    authjwt_csrf_methods: Optional[List[StrictStr]] = ['POST','PUT','PATCH','DELETE']

    @validator('authjwt_access_token_expires')
    def validate_access_token_expires(cls, v):
        if v is True:
            raise ValueError("The 'authjwt_access_token_expires' only accept value False (bool)")
        return v

    @validator('authjwt_refresh_token_expires')
    def validate_refresh_token_expires(cls, v):
        if v is True:
            raise ValueError("The 'authjwt_refresh_token_expires' only accept value False (bool)")
        return v

    @validator('authjwt_denylist_token_checks', each_item=True)
    def validate_denylist_token_checks(cls, v):
        if v not in ['access','refresh']:
            raise ValueError("The 'authjwt_denylist_token_checks' must be between 'access' or 'refresh'")
        return v

    @validator('authjwt_token_location', each_item=True)
    def validate_token_location(cls, v):
        if v not in ['headers','cookies']:
            raise ValueError("The 'authjwt_token_location' must be between 'headers' or 'cookies'")
        return v

    @validator('authjwt_cookie_samesite')
    def validate_cookie_samesite(cls, v):
        if v not in ['strict','lax','none']:
            raise ValueError("The 'authjwt_cookie_samesite' must be between 'strict', 'lax', 'none'")
        return v

    @validator('authjwt_csrf_methods', each_item=True)
    def validate_csrf_methods(cls, v):
        if v.upper() not in ["GET", "HEAD", "POST", "PUT", "DELETE", "PATCH"]:
            raise ValueError("The 'authjwt_csrf_methods' must be between http request methods")
        return v.upper()

    class Config:
        str_min_length = 1
        str_strip_whitespace = True
```

</details>

其实找起来挺麻烦的，所以提供了一个直接修改源代码的脚本
```python
python scripts/fix_fastapi_jwt_auth.py # 进行脚本修复(前提是需要将依赖包安装完整)
```


## 🤝 贡献指南

> 💪 **共建AI未来** - 每一个贡献都让AgentChat变得更好

<div align="center">

### 🌟 **我们欢迎所有形式的贡献！**

</div>

<table>
<tr>
<td width="25%">

#### 🐛 **Bug修复**
*发现问题，解决问题*

1. 🔍 搜索已有Issues
2. 📝 创建详细Bug报告
3. 🧪 提供复现步骤
4. 💡 提交修复方案

</td>
<td width="25%">

#### ✨ **功能开发**
*新想法，新功能*

1. 💭 创建Feature Request
2. 📋 详细描述需求场景
3. 🎨 设计实现方案
4. 🚀 开发并测试

</td>
<td width="25%">

#### 📚 **文档完善**
*知识共享，助力他人*

1. 📖 补充API文档
2. ✍️ 编写使用教程
3. 🌍 多语言翻译
4. 🎥 制作视频教程

</td>
<td width="25%">

#### 🧪 **社区支持**
*帮助他人，分享经验*

1. ❓ 回答社区问题
2. 💬 参与技术讨论
3. 🎤 分享使用心得
4. 🤝 推广项目

</td>
</tr>
</table>





## 📄 **许可证**

<div align="center">

本项目采用 **[MIT License](LICENSE)** 开源许可证

*这意味着你可以自由使用、修改和分发本项目 🎉*

</div>

---

<div align="center">

## 🌟 **感谢支持 AgentChat！**

### 如果这个项目对你有帮助，请给我们一个 ⭐️

*让更多的人发现这个项目，一起构建AI的未来！*

*Made with ❤ by the AgentChat Author MingGuang Tian*


<picture>
  <source
    media="(prefers-color-scheme: dark)"
    srcset="
      https://api.star-history.com/svg?repos=Shy2593666979/AgentChat&type=Date&theme=dark
    "
  />
  <source
    media="(prefers-color-scheme: light)"
    srcset="
      https://api.star-history.com/svg?repos=Shy2593666979/AgentChat&type=Date
    "
  />
  <img
    alt="Star History Chart"
    src="https://api.star-history.com/svg?repos=Shy2593666979/AgentChat&type=Date"
  />
</picture>

</div>
