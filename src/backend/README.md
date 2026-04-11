# AgentChat 后端技术文档

## 技术架构

AgentChat 后端采用 FastAPI 异步框架构建，基于 Python 3.12+，支持多 Agent 协作、知识库检索（RAG）、工具调用和 MCP 协议集成。

### 核心技术栈

| 层次 | 技术 |
|------|------|
| Web 框架 | FastAPI (async) |
| ORM | SQLModel (SQLAlchemy + Pydantic) |
| 数据库 | MySQL 8.0 (pymysql + aiomysql) |
| 缓存 | Redis 7.0 (aioredis) |
| 向量数据库 | Milvus / ChromaDB |
| 全文检索 | Elasticsearch (IK 分词) |
| 对象存储 | MinIO / 阿里云 OSS |
| AI 框架 | LangChain 1.0+ |
| 认证 | JWT (fastapi-jwt-auth) |
| 日志 | Loguru |

---

## 项目结构

```
agentchat/
├── main.py              # FastAPI 应用入口
├── settings.py          # 配置加载（YAML → Pydantic）
├── config.yaml          # 统一配置文件
├── api/
│   ├── router.py        # 顶层路由聚合
│   ├── v1/              # REST API 端点（20+ 模块）
│   ├── services/        # 业务逻辑服务层
│   ├── mcp_proxy/       # MCP 协议代理路由
│   ├── responses/       # 统一响应构建器
│   └── errcode/         # 错误码定义
├── auth/                # JWT 认证模块
├── core/
│   └── agents/          # Agent 实现（React/CodeAct/MCP/Plan 等）
├── database/
│   ├── models/          # 23 张数据表模型
│   └── dao/             # 数据访问对象层
├── services/
│   ├── rag/             # RAG 检索增强生成
│   ├── mcp/             # MCP 多服务器客户端管理
│   ├── storage/         # 存储抽象（OSS/MinIO）
│   └── rewrite/         # 查询改写
├── middleware/          # TraceID / 白名单中间件
├── schemas/             # Pydantic 数据模型
├── prompts/             # Prompt 模板
└── tools/               # 内置工具集成
```

---

## API 层设计

所有业务接口统一挂载在 `/api/v1`，按领域拆分路由模块：

- `completion` — 对话补全（流式 SSE）
- `agent` — Agent CRUD 管理
- `dialog / history / message` — 会话与消息管理
- `knowledge / knowledge_file` — 知识库与文件管理
- `mcp_server / mcp_user_config` — MCP 服务器配置
- `llm / tool` — 模型与工具管理
- `user / workspace` — 用户与工作空间
- `usage_stats` — 用量统计
- `register_mcp / register_task` — MCP 注册与任务调度

MCP 代理路由独立挂载，支持 SSE 和 HTTP Streaming 两种传输协议。

---

## Agent 系统

支持多种 Agent 类型，按任务复杂度选用：

| Agent 类型 | 适用场景 |
|-----------|---------|
| ReactAgent | 通用工具调用推理 |
| CodeActAgent | 代码生成与执行 |
| MCPAgent | MCP 工具集成 |
| SkillAgent | 技能组合调用 |
| PlanExecuteAgent | 复杂多步骤规划 |
| StructuredResponseAgent | 结构化输出 |

---

## RAG 知识库检索

```
用户查询
  → 查询改写（多路 Query）
  → 混合检索（Milvus 向量 + ES 全文）
  → 去重 & 排序
  → Rerank 重排序
  → 注入 Prompt → LLM 生成
```

支持按 `min_score` 和 `top_k` 过滤，ES 可通过配置开关启用。

---

## 多模型配置

通过 `config.yaml` 统一配置，支持按用途分配不同模型：

- `conversation_model` — 对话（Qwen-Plus）
- `tool_call_model` — 工具调用
- `reasoning_model` — 深度推理（DeepSeek-Reasoner）
- `text2image` — 文生图（Wanx）
- `qwen_vl` — 多模态视觉
- `embedding` — 向量化（text-embedding-v4）
- `rerank` — 重排序（gte-rerank-v2）

---

## 认证与权限

- JWT Token 支持 Header 和 Cookie 两种传输方式
- 角色分为：`AdminUser`（超级管理员）、`SystemUser`、普通用户
- 白名单中间件控制免鉴权路径
- Token 吊销列表支持登出场景

---

## 外部集成

| 类型 | 集成方 |
|------|--------|
| LLM | 阿里云 Qwen、DeepSeek、OpenAI 兼容接口 |
| 搜索 | Tavily、Google Search、BoCha |
| 存储 | MinIO（本地）/ 阿里云 OSS（云端） |
| 工具 | 高德天气、快递查询、ArXiv 论文 |
| MCP | 动态加载，支持 SSE/HTTP 双协议 |

---

## 数据库模型

系统包含 23 张数据表，核心表包括：

- `AgentTable` — Agent 配置
- `DialogTable` — 对话会话
- `HistoryTable` — 对话历史
- `MessageTable` — 消息记录
- `KnowledgeTable` — 知识库
- `KnowledgeFileTable` — 知识库文件
- `ToolTable` — 工具配置
- `LLMTable` — 模型配置
- `MCPServerTable` — MCP 服务器
- `MCPUserConfigTable` — MCP 用户配置
- `WorkSpaceSession` — 工作空间会话
- `UsageStats` — 用量统计
- `AgentSkill` — Agent 技能
- `RegisterMcpServer` — 注册 MCP 服务器
- `RegisterMcpTask` — 注册 MCP 任务

所有模型继承自 `SQLModelSerializable` 基类，支持 JSON 序列化。

---

## 配置文件说明

主配置文件 `config.yaml` 包含以下部分：

### 服务配置
```yaml
server:
  env: "dev"           # prod / test / dev
  host: "127.0.0.1"
  port: 7860
  name: "AgentChat"
  version: "2.5.0"
```

### 数据库配置
```yaml
mysql:
  endpoint: "mysql+pymysql://root:password@localhost:3306/agentchat"
  async_endpoint: "mysql+aiomysql://root:password@localhost:3306/agentchat"

redis:
  endpoint: "redis://localhost:6379"
```

### 多模型配置
```yaml
multi_models:
  conversation_model:
    api_key: "your-api-key"
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model_name: "qwen-plus"
  
  tool_call_model:
    api_key: "your-api-key"
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model_name: "qwen-plus"
  
  reasoning_model:
    api_key: "your-api-key"
    base_url: "https://api.deepseek.com/v1"
    model_name: "deepseek-reasoner"
  
  embedding:
    api_key: "your-api-key"
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model_name: "text-embedding-v4"
  
  rerank:
    api_key: "your-api-key"
    base_url: "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"
    model_name: "gte-rerank-v2"
```

### 存储配置
```yaml
storage:
  mode: "minio"   # 或 "oss"
  minio:
    endpoint: "localhost:9000"
    access_key_id: "minioadmin"
    access_key_secret: "minioadmin"
    bucket_name: "agentchat"
  oss:
    endpoint: "oss-cn-hangzhou.aliyuncs.com"
    access_key_id: "your-access-key"
    access_key_secret: "your-secret-key"
    bucket_name: "agentchat"
```

### 工具配置
```yaml
tools:
  weather:
    api_key: "your-amap-key"
    endpoint: "https://restapi.amap.com/v3/weather/weatherInfo?parameters"
  
  tavily:
    api_key: "your-tavily-key"
  
  google:
    api_key: "your-serpapi-key"
  
  bocha:
    api_key: "your-bocha-key"
    endpoint: "https://api.bochaai.com/v1/web-search"
```

---

## 启动流程

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 修复 fastapi-jwt-auth 兼容性

```bash
python scripts/fix_fastapi_jwt_auth.py
```

### 3. 配置数据库

确保 MySQL 和 Redis 服务已启动，并在 `config.yaml` 中配置正确的连接信息。

### 4. 初始化数据库

首次启动时，系统会自动创建数据库表和初始数据。

### 5. 启动服务

```bash
cd src/backend
uvicorn agentchat.main:app --port 7860 --host 0.0.0.0
```

### 6. 访问 API 文档

浏览器访问 [http://localhost:7860/docs](http://localhost:7860/docs) 查看 Swagger API 文档。

---

## 开发指南

### 添加新的 API 端点

1. 在 `api/v1/` 下创建新的路由模块
2. 在 `api/services/` 下创建对应的服务层
3. 在 `api/v1/router.py` 中注册路由

### 添加新的 Agent 类型

1. 在 `core/agents/` 下创建新的 Agent 类
2. 继承 `BaseAgent` 基类
3. 实现 `run` 方法

### 添加新的工具

1. 在 `tools/` 下创建新的工具目录
2. 实现工具的 `run` 方法
3. 在 `tools/__init__.py` 中注册工具

### 添加新的数据表

1. 在 `database/models/` 下创建新的模型类
2. 继承 `SQLModel` 基类
3. 在 `database/__init__.py` 中导入模型
4. 重启服务，系统会自动创建表

---

## 性能优化

### 数据库连接池

```python
engine = create_engine(
    url=app_settings.mysql.get('endpoint'),
    pool_pre_ping=True,      # 连接前检查有效性
    pool_recycle=3600,       # 每小时重连一次
)
```

### Redis 缓存策略

- 用户会话缓存：30 分钟
- API 响应缓存：5 分钟
- 向量检索缓存：1 小时

### 异步处理

所有 I/O 操作均使用异步方式，提高并发性能：

```python
async def get_agent(agent_id: str):
    async with get_async_session() as session:
        result = await session.execute(
            select(AgentTable).where(AgentTable.id == agent_id)
        )
        return result.scalar_one_or_none()
```

---

## 故障排查

### 常见问题

**1. fastapi-jwt-auth 版本冲突**

运行修复脚本：
```bash
python scripts/fix_fastapi_jwt_auth.py
```

**2. 数据库连接失败**

检查 MySQL 服务是否启动，配置文件中的连接信息是否正确。

**3. Redis 连接失败**

检查 Redis 服务是否启动，端口是否正确。

**4. 向量数据库连接失败**

确保 Milvus 或 ChromaDB 服务已启动，配置文件中的连接信息正确。

**5. 模型 API 调用失败**

检查 API Key 是否正确，网络是否可访问模型服务。

---

## 测试

### 运行单元测试

```bash
pytest test/
```

### API 测试

使用 Swagger UI 进行交互式测试：[http://localhost:7860/docs](http://localhost:7860/docs)

---

## 部署

### Docker 部署

参考项目根目录的 [docker/README.md](../../docker/README.md)

### 生产环境部署

1. 使用 Gunicorn + Uvicorn 作为 WSGI 服务器
2. 配置 Nginx 反向代理
3. 使用 Supervisor 或 systemd 管理进程
4. 配置日志轮转
5. 启用 HTTPS

---

## 许可证

本项目采用 [MIT License](../../LICENSE) 开源许可证。
