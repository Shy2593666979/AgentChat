
<div align="center">

<img width="649" height="209" alt="image-Photoroom (2)" src="https://github.com/user-attachments/assets/2e19a214-a87d-473f-a4fd-ee879f4e7149" />


[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![Vue Version](https://img.shields.io/badge/vue-3.4+-green.svg)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/fastapi-0.115+-red.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

*一个基于大语言模型的智能对话系统，支持多Agent协作、知识库检索、工具调用等功能*

[🚀 快速开始](#快速开始) • [💡 功能特性](#功能特性) • [🛠 技术栈](#技术栈) • [📦 部署](#部署) • [📖 文档](#文档)

</div>

---

## 📋 目录

- [🎯 项目简介](#项目简介)
- [✨ 功能展示](#功能展示)
- [💡 功能特性](#功能特性)
- [🛠 技术栈](#技术栈)
- [📁 项目结构](#项目结构)
- [🚀 快速开始](#快速开始)
- [📦 部署](#部署)
- [📖 文档](#文档)
- [🔧 开发指南](#开发指南)
- [🤝 贡献指南](#贡献指南)
- [📄 许可证](#许可证)

---

## 🎯 项目简介

AgentChat 是一个现代化的智能对话系统，基于大语言模型构建，提供了丰富的AI对话功能。系统采用前后端分离架构，支持多种AI模型、知识库检索、工具调用、MCP服务器集成等高级功能。

### 🌟 核心亮点

- 🤖 **多模型支持**: 集成OpenAI、Anthropic、Google等主流大语言模型
- 🧠 **智能Agent**: 支持多Agent协作，具备推理和决策能力
- 📚 **知识库检索**: RAG技术实现精准知识检索和问答
- 🔧 **工具生态**: 内置多种实用工具，支持自定义扩展
- 🌐 **MCP集成**: 支持Model Context Protocol服务器
- 💬 **实时对话**: 流式响应，提供流畅的对话体验
- 🎨 **现代界面**: 基于Vue 3和Element Plus的美观UI

---

## ✨ 功能展示

### 🏠 智言平台首页
<img width="1920" height="922" alt="d66191fe5a094da3989d7ad45f314ab" src="https://github.com/user-attachments/assets/8f326b6b-8987-493a-828c-fb8cf0a49ddf" />

### 智言平台登录页

<img width="1920" height="922" alt="8f0a3a34e6a4a147800d3b931f299c2" src="https://github.com/user-attachments/assets/18f79604-0631-483f-b1eb-8831bf329063" />


### 智能体页面
<img width="1920" height="922" alt="55e38b2c651a4dc4c81e01f73cf2202" src="https://github.com/user-attachments/assets/e58f120e-2e53-4041-b3f8-2243083dccf3" />


#### 使用天气查询Agent

<img width="1920" height="922" alt="5fbfdfefce4f61a05d61675aca9b9a3" src="https://github.com/user-attachments/assets/7774b08b-15af-4407-9b8f-4499777e6cf7" />

#### 使用文生图Agent

<img width="1920" height="922" alt="84a8c857d506e714b9b4c75826afafd" src="https://github.com/user-attachments/assets/ad8de033-b397-472b-8aca-1a3befd99dec" />

### 平台已接入MCP

用户可根据自己的需求进行上传自己的MCP服务
<img width="1920" height="922" alt="f852b494270ab83cd1da8f168af3627" src="https://github.com/user-attachments/assets/7a9f4588-1098-4388-85d9-78a1a4130ec3" />

### 知识库管理页面

用户可自行创建知识库， 为自己的Agent增加更多外部知识
<img width="1920" height="922" alt="4d31fece6ad6faba4f07d56d129882e" src="https://github.com/user-attachments/assets/471ad0d3-e99b-4da0-9338-4fae41eaad68" />

### 知识库文件解析页面

知识库文件解析，支持PDF、Markdown、Docx、Txt等常见文件的解析

<img width="1920" height="922" alt="2e0609b32bebb158221ac95ad67bd6c" src="https://github.com/user-attachments/assets/0d030916-b6e2-482c-b828-b760fc574cae" />

### 工具管理

目前仅支持使用官方工具，后续支持用户自定义工具类型.....

<img width="1920" height="922" alt="8284f57595350ab98e2f1cc8559f619" src="https://github.com/user-attachments/assets/70fe68ce-56e0-44be-b78a-817ed32d4708" />

### 模型管理

用户可以增添模型，让自己的Agent能够更好的输出

<img width="1920" height="922" alt="08ec01e8f6a843dce562f61a3d1f0a9" src="https://github.com/user-attachments/assets/41a49873-f758-49f2-86a4-1a1a57677018" />


## 💡 功能特性

### 🤖 AI对话功能
- ✅ 多种大语言模型支持（OpenAI、Anthropic、Qwen等）
- ✅ 流式响应，实时显示生成内容
- ✅ 上下文记忆，支持长对话
- ✅ 思考过程可视化（深度思考面板）
- ✅ 对话历史管理

### 🧠 智能Agent系统
- ✅ 多Agent协作框架
- ✅ 自动任务分解和执行
- ✅ Agent能力配置和管理
- ✅ 工作流编排

### 📚 知识库管理
- ✅ 多格式文档上传（PDF、Word、Excel、Markdown、TXT等）
- ✅ 智能文档解析和分块
- ✅ 向量化存储和检索
- ✅ 知识库问答（RAG）

### 🔧 内置工具集
- 📧 **邮件发送**: 自动发送邮件给指定收件人
- 🔍 **智能搜索**: Google搜索、Tavily搜索，获取最新信息
- 🌤️ **天气查询**: 查询指定地区的当前天气和预报
- 📰 **论文检索**: ArXiv论文搜索和摘要提取
- 📦 **快递追踪**: 根据快递公司和单号查询物流信息
- 📄 **文档处理**: PDF/Word转换、文档解析
- 🖼️ **多媒体**: 图片生成、图文转换
- 📊 **数据处理**: Excel处理、数据分析

### 🌐 MCP服务器
- ✅ MCP协议支持
- ✅ 自定义MCP服务器集成
- ✅ 天气、ArXiv等内置服务

### 👤 用户管理
- ✅ 用户注册和登录
- ✅ JWT身份验证
- ✅ 个人配置管理
- ✅ 权限控制

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

```
AgentChat/
├── 📁 src/
│   ├── 📁 backend/                 # 后端代码
│   │   └── 📁 agentchat/
│   │       ├── 📁 api/             # API路由
│   │       │   ├── 📁 v1/          # v1版本API
│   │       │   └── 📁 services/    # 服务层API
│   │       ├── 📁 core/            # 核心模块
│   │       │   └── 📁 models/      # AI模型管理
│   │       ├── 📁 database/        # 数据库模型
│   │       │   ├── 📁 dao/         # 数据访问层
│   │       │   └── 📁 models/      # 数据模型
│   │       ├── 📁 services/        # 业务服务
│   │       │   ├── 📁 rag/         # RAG检索服务
│   │       │   ├── 📁 mars/        # Mars智能体服务
│   │       │   └── 📁 mcp/         # MCP服务器
│   │       ├── 📁 tools/           # 工具集成
│   │       │   ├── 📁 arxiv/       # ArXiv工具
│   │       │   ├── 📁 delivery/    # 快递查询工具
│   │       │   └── 📁 web_search/  # 网络搜索工具
│   │       ├── 📁 mcp_servers/     # MCP服务器
│   │       ├── 📁 prompts/         # 提示词模板
│   │       └── 📁 utils/           # 工具函数
│   └── 📁 frontend/                # 前端代码
│       └── 📁 src/
│           ├── 📁 pages/           # 页面组件
│           │   ├── 📁 agent/       # Agent管理页面
│           │   ├── 📁 conversation/# 对话页面
│           │   ├── 📁 knowledge/   # 知识库页面
│           │   └── 📁 mars/        # Mars对话页面
│           ├── 📁 components/      # 通用组件
│           ├── 📁 apis/            # API接口
│           ├── 📁 store/           # 状态管理
│           └── 📁 utils/           # 工具函数
├── 📁 docker/                      # Docker配置
├── 📁 docs/                        # 项目文档
├── 📄 pyproject.toml              # Python项目配置
├── 📄 requirements.txt            # Python依赖
└── 📄 README.md                   # 项目说明
```

---

## 🚀 快速开始

### 📋 环境要求

- **Python**: 3.12+
- **Node.js**: 18+
- **MySQL**: 8.0+
- **Redis**: 7.0+
- **Docker**: 20.10+ (可选)

### 🔧 本地开发

#### 1. 克隆项目

```bash
git clone https://github.com/your-username/AgentChat.git
cd AgentChat
```

#### 2. 后端环境配置

```bash
# 安装Poetry（如果未安装）
curl -sSL https://install.python-poetry.org | python3 -

# 安装依赖
cd src/backend
poetry install
# 或使用pip
pip install -r requirements.txt

# 激活虚拟环境（Poetry）
poetry shell
```

#### 3. 配置文件设置

**配置LLM模型**
在 `src/backend/agentchat/config.yaml` 中配置你的API密钥：

```yaml
# AI模型配置
models:
  openai:
    api_key: "your-openai-api-key"
    base_url: "https://api.openai.com/v1"
  anthropic:
    api_key: "your-anthropic-api-key"
  qwen:
    api_key: "your-qwen-api-key"
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 数据库配置
database:
  mysql:
    host: localhost
    port: 3306
    user: root
    password: 123456
    database: agentchat
  redis:
    host: localhost
    port: 6379
```

#### 4. 数据库初始化

```bash
# 启动MySQL和Redis（使用Docker）
cd docker
docker-compose up -d mysql redis

# 或手动启动本地服务
# MySQL: 创建数据库 agentchat
# Redis: 启动Redis服务

# 初始化数据库
cd ../src/backend
python -m agentchat.database.init_data
```

#### 5. 启动后端服务

```bash
cd src/backend
uvicorn agentchat.main:app --port 8000 --host 0.0.0.0 --reload
```

#### 6. 前端环境配置

```bash
# 安装依赖
cd src/frontend
npm install

# 启动开发服务器
npm run dev
```

#### 7. 访问应用

- **前端界面**: http://localhost:8090
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

---

## 📦 部署

### 🐳 Docker部署（推荐）

#### 完整部署

```bash
# 克隆项目
git clone https://github.com/Shy2593666979/AgentChat.git
cd AgentChat

# 配置环境变量
cp src/backend/agentchat/config.yaml.example src/backend/agentchat/config.yaml
# 编辑配置文件，填入你的API密钥

# 构建并启动所有服务
cd docker
docker-compose up --build -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

#### 仅启动数据库服务

```bash
cd docker
docker-compose up -d mysql redis
```



---

## 📖 文档

### 📚 API文档
- [API Documentation v3.0](docs/API_Documentation_v3.0.md) - 最新API文档
- [API Documentation v2.0](docs/API_Documentation_v2.0.md) - v2.0版本文档
- [API Documentation v1.0](docs/API_Documentation_v1.0.md) - v1.0版本文档

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

### ⚠️ 重要提示

由于 `fastapi-jwt-auth` 库使用较旧版本的 Pydantic，而项目中的 LangChain、MCP 等组件需要 Pydantic >= 2，需要手动修改库文件：

找到你的虚拟环境中的文件：
```
/path/to/your/env/lib/python3.x/site-packages/fastapi_jwt_auth/config.py
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
    
    # 其他配置项...
    
    @validator('authjwt_access_token_expires')
    def validate_access_token_expires(cls, v):
        if v is True:
            raise ValueError("The 'authjwt_access_token_expires' only accept value False (bool)")
        return v

    # 其他验证器...
    
    class Config:
        str_min_length = 1
        str_strip_whitespace = True
```

</details>


## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 🐛 报告Bug
1. 在GitHub Issues中搜索是否已存在相同问题
2. 创建新Issue，详细描述问题
3. 提供复现步骤和环境信息

### 💡 提出功能建议
1. 在GitHub Issues中创建Feature Request
2. 详细描述功能需求和使用场景
3. 讨论实现方案


---


## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

---


<div align="center">

**如果这个项目对你有帮助，请给它一个 ⭐️**

*Made with ❤️ by the AgentChat Author MingGuang Tian*

</div>
