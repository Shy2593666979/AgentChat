<div align='center'>
    <img src="https://github.com/user-attachments/assets/eb9b3b09-e2bf-4c9d-95a0-5c2d9712723d" alt="AgentChat Logo" width="70%">
</div>

<div align="center">

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/vue-3.4+-4FC08D.svg?style=for-the-badge&logo=vue.js&logoColor=white" alt="Vue Version" />
  <img src="https://img.shields.io/badge/fastapi-0.115+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge" alt="License" />
</p>

<p align="center">
  <b>基于大语言模型的现代化智能对话系统</b>
</p>

<p align="center">
  支持多Agent协作 • 知识库检索 • 工具调用 • MCP服务器集成 • 实时对话
</p>

<p align="center">
  <a href="https://shy2593666979.github.io/agentchat-docs/%E5%BF%AB%E9%80%9F%E5%85%A5%E9%97%A8.html">快速开始</a> •
  <a href="https://shy2593666979.github.io/agentchat-docs/%E5%BC%80%E5%8F%91%E6%8C%87%E5%8D%97/%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA.html">部署指南</a> •
  <a href="https://shy2593666979.github.io/agentchat-docs/">在线文档</a> •
  <a href="https://agentchat.cloud">在线体验</a> •
  <a href="https://github.com/Shy2593666979/agentchat-docs/blob/main/images/README.md">微信群聊</a>
</p>

</div>

---

## 目录

- [项目简介](#项目简介)
- [最新更新](#最新更新)
- [核心特性](#核心特性)
- [技术栈](#技术栈)
- [功能展示](#功能展示)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [开发指南](#开发指南)
- [部署方案](#部署方案)
- [文档资源](#文档资源)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 项目简介

AgentChat 是一个现代化的智能对话系统，基于大语言模型构建，提供丰富的 AI 对话功能。系统采用前后端分离架构，支持多种 AI 模型、知识库检索、工具调用、MCP 服务器集成等高级功能。

### 核心亮点

- **多模型支持** - 集成 OpenAI、DeepSeek、Qwen 等主流大语言模型
- **智能 Agent** - 支持多 Agent 协作，具备推理和决策能力
- **知识库检索** - RAG 技术实现精准知识检索和问答
- **工具生态** - 内置多种实用工具，支持自定义扩展
- **MCP 集成** - 支持 Model Context Protocol 服务器
- **实时对话** - 流式响应，提供流畅的对话体验
- **现代界面** - 基于 Vue 3 和 Element Plus 的美观 UI

---

## 最新更新

### v2.2.0 (2026-3-8)

#### 1. 支持 MiniO 本地对象存储
现在支持 OSS 和 MiniO 两种对象存储方式，参考文档: [本地安装 MiniO](docs/development/install_minio_win.md)

感谢贡献者:
- [@xiaoyan011016](https://github.com/xiaoyan011016)
- [@shenmi888](https://github.com/shenmi888)

#### 2. 优化 Docker 部署
- 修复 `agentchat-frontend` 连接 `agentchat-backend` 的网络问题
- 新增 Windows 系统一键部署脚本 (start_win.bat)

感谢贡献者: [@R-322](https://github.com/R-322)

#### 3. 支持自定义工具
支持通过上传 Swagger/OpenAPI 构建自定义工具

感谢贡献者: [@shenmi888](https://github.com/shenmi888)

#### 4. 支持 Skill 功能
支持通过创建 Skill 绑定到智能体，渐进式加载 Prompt

感谢贡献者: [@opaquezxd](https://github.com/opaquezxd)

#### 5. 优化页面样式
移除空白的系统设置页面

感谢贡献者: [@wxliu07](https://github.com/wxliu07)

### 重要版本说明

> **从 AgentChat v2.2.0 版本开始，LangChain 已升级至 1.0 版本，代码改动较大**

| 版本 | LangChain 版本 | 兼容性 | 说明 |
|:---:|:---:|:---:|:---|
| v2.1.x 及以下 | 0.x | 旧版本 | 使用旧版 LangChain API |
| v2.2.0+ | 1.0+ | 最新版本 | 重大更新，API 变化较大 |

**升级注意事项:**
- LangChain 1.0 引入了重大 API 变更
- 部分工具和 Agent 配置方式已更新
- 建议查看[迁移指南](docs/reference/migration.md)了解详细变更
- 新用户建议直接使用最新版本

---

## 核心特性

### AI 对话引擎

- **多模型生态** - 支持 OpenAI、Anthropic、通义千问等主流 LLM
- **流式响应** - 实时显示生成内容，无需等待
- **上下文记忆** - 支持长对话，智能理解对话历史
- **思考可视化** - 深度思考面板，展示 AI 推理过程
- **对话管理** - 完整的对话历史存储和检索
- **参数调优** - 温度、Top-p 等参数精细控制

### 智能 Agent 系统

- **多 Agent 协作** - 智能体间任务分工与协调
- **任务自动化** - 智能分解复杂任务，自动执行
- **能力配置** - 灵活的 Agent 能力定义和管理
- **工作流编排** - 可视化工作流设计和执行
- **执行监控** - 实时监控 Agent 执行状态
- **目标导向** - 基于目标的智能决策和行动

### 知识库系统

- **多格式支持** - PDF、Word、Excel、Markdown、TXT 等
- **智能分块** - 语义级别的文档分割和处理
- **向量检索** - 基于语义的精准知识检索
- **RAG 问答** - 检索增强生成，提高回答准确性
- **知识组织** - 分类管理，标签系统
- **使用统计** - 知识库使用情况分析

### 工具生态

内置 10+ 实用工具:

- **通信工具** - 邮件发送、消息推送
- **信息检索** - Google 搜索、学术论文搜索
- **生活服务** - 天气查询、快递追踪
- **文档处理** - 格式转换、内容提取
- **多媒体** - 文生图、图像识别、OCR
- **数据分析** - Excel 处理、数据可视化
- **自动化** - 简历优化、内容重写
- **网络工具** - 网页爬取、内容抓取

### MCP 服务器

- **协议支持** - 完整 MCP 协议实现
- **自定义服务** - 支持用户自定义 MCP 服务器
- **内置服务** - 天气、ArXiv 等预构建服务
- **动态加载** - 运行时动态加载 MCP 服务
- **高性能** - 异步处理，快速响应

### 用户管理

- **安全认证** - JWT 令牌，安全可靠
- **用户系统** - 注册、登录、个人资料
- **权限控制** - 细粒度权限管理
- **个性配置** - 个人偏好设置
- **使用统计** - 用户行为分析

---

## 技术栈

### 后端技术

- **框架**: FastAPI (Python 3.12+)
- **AI 集成**: LangChain 1.0+, OpenAI, Anthropic
- **数据库**: MySQL 8.0, Redis 7.0
- **向量数据库**: ChromaDB, Milvus
- **搜索引擎**: Elasticsearch
- **文档处理**: PyMuPDF, Unstructured
- **异步任务**: Celery
- **部署**: Docker, Gunicorn, Uvicorn

### 前端技术

- **框架**: Vue 3.4+ (Composition API)
- **UI 组件**: Element Plus
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

## 功能展示

### 工作区界面
新增工作区，工作区和应用中心可随意切换

<img width="800" alt="工作区" src="https://github.com/user-attachments/assets/766c7628-2256-4c8b-a838-c400eaa78d6b" />

### 灵寻任务规划
实时的任务流程图，更加直观的感受

<img width="800" alt="任务规划" src="https://github.com/user-attachments/assets/53f7fe9f-d70d-4cc2-bf7e-b47a712a6d7a" />

### 数据看板
能够根据 Agent、模型、时间范围进行筛选调用次数和 Token 使用量

<img width="800" alt="数据看板" src="https://github.com/user-attachments/assets/b0cb4ccf-b868-4f1b-9b26-8a882d8130da" />

### 智言平台首页
简洁现代的主界面，提供直观的功能导航

<img width="800" alt="首页" src="https://github.com/user-attachments/assets/dc626494-4797-4a86-b350-3a0759d52d64" />

### 智能体管理
强大的 Agent 配置和管理中心

<img width="800" alt="智能体管理" src="https://github.com/user-attachments/assets/b24d47ee-17ea-4cc3-bfd2-53cf93c87ebb" />

### 智能体工具多轮调用
平台中智能体支持工具多轮调用（根据工具依赖关系自动调用顺序 A → B → C）

<img width="800" alt="多轮调用" src="https://github.com/user-attachments/assets/029c70ce-e5fa-4f2c-926a-a5dfd719e237" />

### MCP 服务器集成
支持 Model Context Protocol，可上传自定义 MCP 服务

<img width="800" alt="MCP服务器" src="https://github.com/user-attachments/assets/79bfa401-bd94-4290-b7ae-bcb69cc00f64" />

### 知识库管理
智能知识管理，为 Agent 提供丰富的外部知识支持

<img width="800" alt="知识库" src="https://github.com/user-attachments/assets/0de41202-295a-43c5-a15c-c0b3cc55e5f8" />

### 文档解析引擎
支持 PDF、Markdown、Docx、Txt 等多种格式的智能解析

<img width="800" alt="文档解析" src="https://github.com/user-attachments/assets/c5eba600-7dc2-429a-88f9-50f8811f293b" />

### 工具管理中心
丰富的内置工具集，支持用户自定义上传工具

<img width="800" alt="工具管理" src="https://github.com/user-attachments/assets/6a0126d2-5042-4131-816e-5d049d09728c" />

### AI 模型管理
多模型支持，灵活配置不同 AI 服务

<img width="800" alt="模型管理" src="https://github.com/user-attachments/assets/97053c0d-a57c-4347-9cf1-1ab96fa7fc22" />

---

## 快速开始

### 系统要求

| 组件 | 版本要求 | 说明 |
|:---:|:---:|:---|
| Python | 3.12+ | 后端运行环境 |
| Node.js | 18+ | 前端构建环境 |
| MySQL | 8.0+ | 主数据库 |
| Redis | 7.0+ | 缓存和会话存储 |
| Docker | 20.10+ | 容器化部署（推荐） |

### 方式一: Docker 一键部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/Shy2593666979/AgentChat.git
cd AgentChat

# 2. 配置 API 密钥
cp src/backend/agentchat/config.yaml.example src/backend/agentchat/config.yaml
# 编辑配置文件，填入你的 API 密钥

# 3. 一键启动
cd docker
docker-compose up --build -d
```

验证部署:
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

访问 [http://localhost:8090](http://localhost:8090) 开始使用

### 方式二: 本地开发环境

#### 后端环境搭建

```bash
# 1. 克隆项目
git clone https://github.com/Shy2593666979/AgentChat.git
cd AgentChat

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置文件
# 创建并编辑 src/backend/agentchat/config.yaml

# 4. 启动后端服务
cd src/backend
uvicorn agentchat.main:app --port 7860 --host 0.0.0.0
```

#### 前端环境搭建

```bash
# 新终端
cd src/frontend
npm install
npm run dev
```

#### 访问地址

| 服务 | 地址 | 说明 |
|:---:|:---:|:---|
| 前端界面 | [localhost:8090](http://localhost:8090) | 用户界面 |
| 后端 API | [localhost:7860](http://localhost:7860) | API 服务 |
| API 文档 | [localhost:7860/docs](http://localhost:7860/docs) | Swagger 文档 |

---

## 项目结构

```
AgentChat/
├── README.md                      # 项目说明文档
├── LICENSE                        # 开源许可证
├── pyproject.toml                 # Python 项目配置
├── requirements.txt               # Python 依赖包列表
│
├── docs/                          # 项目文档目录
│   ├── development/               # 开发文档
│   └── reference/                 # 参考文档
│       ├── agentchat.md          # AgentChat 文档
│       ├── api.md                # API 文档
│       ├── core.md               # 核心模块文档
│       ├── database.md           # 数据库文档
│       ├── migration.md          # 迁移指南
│       └── service.md            # 服务文档
│
├── docker/                        # 容器化配置
│   ├── Dockerfile                # Docker 镜像构建文件
│   ├── Dockerfile.frontend       # 前端 Docker 文件
│   ├── docker-compose.yml        # Docker 编排配置
│   ├── start_linux.sh            # Linux 启动脚本
│   └── start_win.bat             # Windows 启动脚本
│
├── scripts/                       # 脚本目录
│   ├── fix_fastapi_jwt_auth.py   # JWT 修复脚本
│   └── start.py                  # 启动脚本
│
└── src/                          # 源代码目录
    ├── backend/                  # 后端服务
    │   └── agentchat/           # 核心后端应用
    │       ├── main.py          # FastAPI 应用入口
    │       ├── settings.py      # 应用配置设置
    │       ├── config.yaml      # YAML 配置文件
    │       ├── api/             # API 路由层
    │       │   ├── v1/          # v1 版本 API 接口
    │       │   ├── services/    # 服务层 API
    │       │   ├── errcode/     # 错误码定义
    │       │   └── mcp_proxy/   # MCP 代理
    │       ├── core/            # 核心功能模块
    │       │   ├── agents/      # Agent 实现
    │       │   ├── models/      # AI 模型管理
    │       │   └── callbacks/   # 回调处理
    │       ├── database/        # 数据库层
    │       │   ├── models/      # 数据模型定义
    │       │   └── dao/         # 数据访问对象
    │       ├── services/        # 业务服务层
    │       │   ├── rag/         # RAG 检索增强生成
    │       │   ├── mcp/         # MCP 协议服务
    │       │   └── mars/        # Mars 智能体服务
    │       ├── tools/           # 工具集成
    │       │   ├── arxiv/       # ArXiv 论文工具
    │       │   ├── web_search/  # 网络搜索工具
    │       │   ├── get_weather/ # 天气查询工具
    │       │   └── text2image/  # 文本转图片工具
    │       ├── mcp_servers/     # MCP 服务器集合
    │       ├── prompts/         # 提示词模板库
    │       ├── config/          # 配置文件目录
    │       ├── schema/          # 数据模式定义
    │       └── utils/           # 通用工具函数
    │
    └── frontend/                # 前端应用
        ├── package.json         # Node.js 项目配置
        ├── vite.config.ts       # Vite 构建配置
        ├── tsconfig.json        # TypeScript 配置
        └── src/                 # 前端源代码
            ├── main.ts          # Vue 应用入口
            ├── App.vue          # 根组件
            ├── components/      # 可复用组件库
            ├── pages/           # 页面组件
            │   ├── agent/       # Agent 管理页面
            │   ├── knowledge/   # 知识库页面
            │   ├── tool/        # 工具管理页面
            │   ├── mcp-server/  # MCP 服务器页面
            │   └── conversation/# 对话页面
            ├── router/          # 路由配置
            ├── store/           # 状态管理 (Pinia)
            ├── apis/            # API 接口定义
            └── utils/           # 工具函数库
```

---

## 开发指南

### 重要提示: fastapi-jwt-auth 兼容性修复

由于 `fastapi-jwt-auth` 库使用较旧版本的 Pydantic，而项目中的 LangChain、MCP 等组件需要 Pydantic >= 2，需要手动修复。

**方式一: 使用自动修复脚本（推荐）**

```bash
python scripts/fix_fastapi_jwt_auth.py
```

**方式二: 手动修复**

找到虚拟环境中的文件:
```
/path/to/your/env/lib/python3.12/site-packages/fastapi_jwt_auth/config.py
```

替换为项目提供的兼容版本（详见 `scripts/fix_fastapi_jwt_auth.py`）

### 配置文件说明

主配置文件位于 `src/backend/agentchat/config.yaml`，包含以下配置项:

- **数据库配置** - MySQL、Redis 连接信息
- **AI 模型配置** - OpenAI、Anthropic 等模型 API 密钥
- **向量数据库配置** - ChromaDB、Milvus 配置
- **对象存储配置** - OSS、MiniO 配置
- **搜索引擎配置** - Elasticsearch 配置

---

## 部署方案

### Docker 部署（生产环境推荐）

```bash
# 使用 docker-compose 部署
cd docker
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 手动部署

#### 后端部署

```bash
# 安装依赖
pip install -r requirements.txt

# 运行数据库迁移
python scripts/init_database.py

# 启动服务
cd src/backend
gunicorn agentchat.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:7860
```

#### 前端部署

```bash
# 构建前端
cd src/frontend
npm install
npm run build

# 使用 nginx 部署
# 将 dist 目录部署到 nginx 静态文件目录
```

---

## 文档资源

### API 文档
- [AgentChat 文档](docs/reference/agentchat.md) - AgentChat 具体文档
- [API 文档 v3.0](docs/reference/api.md) - 最新 API 文档
- [在线 API 文档](http://localhost:7860/docs) - Swagger 交互式文档

### 开发文档
- [前端调试指南](src/frontend/DEBUGGING_GUIDE.md)
- [迁移指南](docs/reference/migration.md) - LangChain 1.0 迁移指南

### 配置指南

#### 向量数据库
- **Milvus**: [安装指南](https://milvus.io/docs/zh/install_standalone-windows.md)
- **ChromaDB**: 项目中已集成，无需额外配置

#### 模型服务
- **Rerank 模型**: [阿里云模型服务](https://help.aliyun.com/zh/model-studio/text-rerank-api)
- **Embedding 模型**: [OpenAI 兼容接口](https://help.aliyun.com/zh/model-studio/embedding-interfaces-compatible-with-openai)

#### 搜索引擎
- **Elasticsearch**: [IK 分词器](https://release.infinilabs.com/analysis-ik/stable/)

#### 对象存储
- **MiniO**: [本地安装 MiniO](docs/development/install_minio_win.md)

---

## 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. **Bug 修复**
   - 搜索已有 Issues
   - 创建详细 Bug 报告
   - 提供复现步骤
   - 提交修复方案

2. **功能开发**
   - 创建 Feature Request
   - 详细描述需求场景
   - 设计实现方案
   - 开发并测试

3. **文档完善**
   - 补充 API 文档
   - 编写使用教程
   - 多语言翻译
   - 制作视频教程

4. **社区支持**
   - 回答社区问题
   - 参与技术讨论
   - 分享使用心得
   - 推广项目

### 贡献流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 许可证

本项目采用 [MIT License](LICENSE) 开源许可证

---

<div align="center">

## Star History

<picture>
  <source
    media="(prefers-color-scheme: dark)"
    srcset="https://api.star-history.com/svg?repos=Shy2593666979/AgentChat&type=Date&theme=dark"
  />
  <source
    media="(prefers-color-scheme: light)"
    srcset="https://api.star-history.com/svg?repos=Shy2593666979/AgentChat&type=Date"
  />
  <img
    alt="Star History Chart"
    src="https://api.star-history.com/svg?repos=Shy2593666979/AgentChat&type=Date"
  />
</picture>

---

**如果这个项目对你有帮助，请给我们一个 ⭐**

Made with ❤ by MingGuang Tian

</div>
