
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
  <b>一个基于大模型的现代化智能对话系统</b>
</p>

<p align="center">
  <a href="https://shy2593666979.github.io/agentchat-docs/%E5%BF%AB%E9%80%9F%E5%85%A5%E9%97%A8.html">快速开始</a> •
  <a href="https://shy2593666979.github.io/agentchat-docs/%E5%BC%80%E5%8F%91%E6%8C%87%E5%8D%97/%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA.html">部署指南</a> •
  <a href="https://shy2593666979.github.io/agentchat-docs/">在线文档</a> •
  <a href="https://agentchat.cloud">在线体验</a> •
  <a href="https://github.com/Shy2593666979/agentchat-docs/blob/main/images/README.md">加入微信交流群🌟</a>
</p>

</div>

---

## 最新版本更新日志 (2026-4-12)

### 1. 基于人机协同（HITL）的OpenAPI信息对话式MCP Server生成

- 支持将OpenAPI信息以人机协同方式进行对话式MCP Server生成。
- 在生成MCP Server的过程中，关键决策节点支持人工介入与确认，实现动态配置与实时交互。
- 提升了服务器的生成灵活性与系统可控性，让用户在自动化流程中保留充分的主动权。

### 2. 优化对话上下文管理
重构对话上下文管理策略，从简单的"最近5段对话"升级为智能三层记忆架构：
- 短期记忆 (Short-Term Memory): 保持最近3000 tokens以内的对话内容，确保即时上下文连贯
- 历史信息总结: 自动总结超过3000 tokens的历史对话，提取关键信息
- 长期记忆 (Long-Term Memory): 持久化记录用户偏好、习惯和重要信息，实现个性化对话体验

### 3. 修复依赖冲突问题
解决了多个依赖包版本冲突问题，特别是 Pydantic、LangChain、FastAPI 等核心库的兼容性问题，提升系统稳定性。

### 4. 优化首次启动体验
修复首次启动时缺少模型配置导致的错误，新增配置检查和友好提示，引导用户完成初始化配置，降低使用门槛。

---

<details>
<summary><b>历史版本更新日志 (2026-3-8)</b></summary>

### 1. 支持MiniO本地对象存储
现在支持OSS和MiniO两种对象存储方式，参考文档: [本地安装MiniO](docs/development/install_minio_win.md)，感谢提供Issue的朋友:
- @xiaoyan011016
- @shenmi888

### 2. 优化Docker直接部署项目
(1) 前版本docker部署经常会出现 agentchat-frontend 连不上 agentchat-backend 的网络失败情况，已经修复该bug
(2) 缺少Win系统下的一键部署脚本，目前已经加上 (start_win.bat)

### 3. 支持自定义工具
之前点击自定义工具是无事件，目前可通过上传 Swagger/OpenAPI 构建自己的工具。

### 4. 支持Skill
现已支持通过创建 Skill 绑定到智能体渐进式加载 Prompt 去教模型如何做事。

### 5. 优化页面样式
前版本中系统设置为空白，现在已经去除。

</details>

---

## 目录

- [一、项目简介](#一项目简介)
- [二、功能展示](#二功能展示)
- [三、重要版本说明](#三重要版本说明)
- [四、功能特性](#四功能特性)
- [五、技术栈](#五技术栈)
- [六、快速开始](#六快速开始)
- [七、高级部署指南](#七高级部署指南)
- [八、文档](#八文档)
- [九、许可证](#九许可证)

---

## 一、项目简介

AgentChat 是一个现代化的智能对话系统，基于大语言模型构建，提供了丰富的AI对话功能。系统采用前后端分离架构，支持多种AI模型、知识库检索、工具调用、MCP服务器集成等高级功能。

<div align="center">
<img width="800" height="400" src="https://github.com/user-attachments/assets/f35e8a9a-0905-46a2-a167-a3c8e876760a" />
</div>

### 1. 核心亮点

- 智能Agent: 支持Sub-Agents协作，具备推理和决策能力
- 知识库检索: RAG技术实现精准知识检索和问答
- 工具生态: 内置多种实用工具，支持自定义扩展
- MCP集成: 支持Model Context Protocol服务器
- 现代界面: 基于Vue 3和Element Plus的美观UI
- 三层记忆: 短期保留上下文，历史自动总结，长期记录用户偏好
- 人机协同生成: 基于HITL对话式生成MCP Server，关键节点可人工介入
---

## 二、功能展示

<div align="center">

### 1. 人机协同（HITL）
使用Human-In-The-Loop机制将API信息对话式生成MCP Server
<img width="800" height="450" src="https://github.com/user-attachments/assets/cabb59d8-0e14-432a-9aee-aa9115e266cd" />

### 2. 新增工作区
新增工作区，工作区和应用中心可随意切换
<img width="800" height="450" src="https://github.com/user-attachments/assets/766c7628-2256-4c8b-a838-c400eaa78d6b" />

### 3. 灵寻任务规划
实时的任务流程图，更加直观的感受
<img width="800" height="450" src="https://github.com/user-attachments/assets/53f7fe9f-d70d-4cc2-bf7e-b47a712a6d7a" />

### 4. 数据看板
能够根据Agent、模型、时间范围进行筛选调用次数和Token使用量
<img width="800" height="450" src="https://github.com/user-attachments/assets/b0cb4ccf-b868-4f1b-9b26-8a882d8130da" />

### 5. 智言平台首页
简洁现代的主界面，提供直观的功能导航
<img width="800" height="450" src="https://github.com/user-attachments/assets/dc626494-4797-4a86-b350-3a0759d52d64" />

</div>

### 6. 智能Agent功能演示

<table>
<tr>
<td width="50%">

#### 天气查询Agent
实时天气信息查询和预报
<img width="400" height="240" src="https://github.com/user-attachments/assets/91a95c2b-f194-4c25-ba0f-f8cb393cba50" />

</td>
<td width="50%">

#### 文生图Agent
AI驱动的图像生成服务
<img width="400" height="240" src="https://github.com/user-attachments/assets/58194798-5c3e-4d7d-895c-944b6665e5a6" />

</td>
</tr>
</table>

### 7. 智能体工具多轮调用

平台中智能体支持工具多轮调用（指的是根据工具C依赖工具B结果，执行工具B依赖工具A结果，所以调用工具的顺序是 A --> B --> C）
<div align="center">
<img width="800" height="450" src="https://github.com/user-attachments/assets/029c70ce-e5fa-4f2c-926a-a5dfd719e237" />
</div>

---

## 三、重要版本说明

从 AgentChat v2.2.0 版本开始，LangChain 已升级至 1.0 版本。

<div align="center">

| 版本 | LangChain版本 | 兼容性 | 说明 |
|:---:|:---:|:---:|:---|
| v2.1.x 及以下 | 0.x | 旧版本 | 使用旧版LangChain API |
| v2.2.0+ | 1.0+ | 最新版本 | 重大更新，API变化较大 |

</div>

1. LangChain 1.0 引入了重大API变更。
2. 部分工具和Agent配置方式已更新。
3. 建议查看迁移指南了解详细变更。

---

## 四、功能特性

### 1. 核心功能模块

- AI对话引擎: 支持多模型生态、流式响应、上下文记忆、思考可视化。
- 智能Agent系统: 多Agent协作、任务自动化、工作流编排、目标导向。
- 知识库系统: 多格式支持、语义分块、向量检索、RAG问答。
- 工具生态: 内置10+实用工具，支持自定义上传与扩展。

### 2. 高级特性

- MCP服务器: 完整协议支持，运行时动态加载。
- 用户管理: 安全认证、细粒度权限控制、个性化配置。
- 系统架构: 前后端分离，Docker部署，异步高性能处理。

---

## 五、技术栈

- 后端: FastAPI, Python 3.12+, LangChain, MySQL, Redis, ChromaDB.
- 前端: Vue 3.4+, Element Plus, Pinia, Vite 5, TypeScript.
- 部署: Docker, Docker Compose, Poetry, npm.

---

## 六、快速开始

### 1. 系统要求

- Python 3.12+
- Node.js 18+
- MySQL 8.0+, Redis 7.0+
- Docker 20.10+

### 2. Docker一键部署

```bash
# 1. 克隆项目
git clone https://github.com/Shy2593666979/AgentChat.git
cd AgentChat

# 2. 编辑配置文件
vim docker/docker_config.yaml

# 3. 启动
cd docker
docker-compose up --build -d
````

### 3. 本地一键部署

克隆项目
```bash
git clone https://github.com/Shy2593666979/AgentChat.git

cd AgentChat
```


后端启动服务
```bash
cd src/backend

# 安装依赖
1. pip install -r requirements.txt

# 或者使用uv (更推荐)
1. pip install uv
2. uv sync 
```

前端启动服务
```bash
cd src/frontend

# 下载依赖
npm install
npm run dev
```

-----

## 七、高级部署指南

系统支持多种向量数据库（Milvus/ChromaDB）和搜索引擎（Elasticsearch）的配置。具体请参阅部署文档。

-----

## 八、文档

  - API文档: [AgentChat Document](https://www.google.com/search?q=docs/reference/agentchat.md)
  - 开发指南: 启动后端后访问 /docs 查看 Swagger 文档。

-----

## 九、许可证

本项目采用 **[MIT License](LICENSE)** 开源许可证

*这意味着你可以自由使用、修改和分发本项目*


-----


## 十、感谢支持 AgentChat

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
