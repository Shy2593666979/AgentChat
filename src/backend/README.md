# agentchat 后端

后端使用 Python、FastAPI、LangChain 和 SQLModel，提供智能体会话、Mars 任务、知识库、工具与 MCP 管理等接口。

首次运行使用 [根目录快速开始](../../README.md#快速开始) 或 [简易配置指南](../../docs/simple-config.md)。默认本地方案使用 SQLite、内存缓存、文件目录和 Chroma，不要求额外启动 MySQL、Redis、MinIO 或 Milvus。

## 本地启动

准备 Python 3.12 和 uv，在 `src/backend` 目录执行：

```bash
uv sync --locked --python 3.12
```

复制 `agentchat/config.simple.yaml` 为 `agentchat/config.local.simple.yaml`。以 [DeepSeek Flash](https://api-docs.deepseek.com/zh-cn/) 为例，修改以下字段并保留模板其他设置：

```yaml
multi_models:
  chat_model:
    api_key: "填写你的 DeepSeek API Key"
    base_url: "https://api.deepseek.com"
    model_name: "deepseek-flash"
```

Windows PowerShell：

```powershell
$env:AGENTCHAT_CONFIG = "agentchat/config.local.simple.yaml"
uv run --locked uvicorn agentchat.main:app --host 127.0.0.1 --port 7860
```

Linux / macOS：

```bash
export AGENTCHAT_CONFIG=agentchat/config.local.simple.yaml
uv run --locked uvicorn agentchat.main:app --host 127.0.0.1 --port 7860
```

- 健康检查：`GET http://127.0.0.1:7860/health`，返回 `{"status":"OK"}`。
- API 文档：[Swagger UI](http://127.0.0.1:7860/docs)。
- 前端启动与代理设置见 [根目录 README](../../README.md#快速开始)。

JWT 实现位于 `agentchat/auth/`，当前启动流程无需执行旧的 `fix_fastapi_jwt_auth.py` 修补脚本。

## 配置与数据目录

配置优先级：显式传入 `init_app_settings` 的路径 → `AGENTCHAT_CONFIG` → `agentchat/config.local.yaml` → `agentchat/config.yaml`。环境变量中的相对路径以启动命令的工作目录为基准。`config.local.simple.yaml` 不会被自动选择，需要显式指定。

`simple_mode: true` 启用默认值补齐，并让工具调用、推理等模型复用对话配置。完整配置模式不自动复用这些模型，按需填写各项。配置修改后需要重启后端。

| 数据 | 本地方案位置 | 说明 |
| --- | --- | --- |
| 业务数据库 | `data/agentchat.db` | 相对 SQLite 路径固定以 `src/backend` 为基准 |
| 上传文件 | `data/uploads/` | 相对存储路径固定以 `src/backend` 为基准，通过 `/uploads/` 访问 |
| 知识库向量 | `vector_db/` | 相对启动工作目录 |
| 长期记忆向量 | `memory_db/` | 相对启动工作目录 |
| 应用日志 | `logs/app.log`、`logs/error.log` | 默认位于 `src/backend`，可用 `AGENTCHAT_LOG_DIR` 覆盖 |
| 内存缓存 | 当前进程 | 重启后清空；多进程应配置 Redis |

因此建议始终从 `src/backend` 启动。数据库、文件和向量目录分别保存不同数据，需要持久化或备份时一起考虑。本地上传链接是直接访问地址，不是临时签名链接。

### 数据库与缓存

```yaml
database:
  url: "sqlite:///data/agentchat.db"
redis:
  endpoint: null
```

切换 MySQL 时，将 `database.url` 改为 `mysql+pymysql://用户名:密码@127.0.0.1:3306/agentchat`；需要 Redis 时填写 `redis://127.0.0.1:6379`。密码中的 URL 特殊字符需要编码。

数据库同步与异步连接由同一 URL 派生，不需要分别维护两个地址。切换 URL 不会自动搬迁旧数据库的数据。SQLite 文件会启用外键检查、繁忙等待和 WAL；`sqlite:///:memory:` 用于临时运行，进程退出后不保留数据。

### 模型与知识库

| 配置项 | 用途 |
| --- | --- |
| `multi_models.chat_model` | 系统默认对话、会话标题等 |
| `multi_models.tool_call_model` | 工具调用模型 |
| `multi_models.reasoning_model` | 推理模型 |
| `multi_models.embedding` | 知识库与长期记忆向量化 |
| `multi_models.rerank` | 知识库检索重排 |
| `multi_models.qwen_vl` | 视觉处理 |
| `multi_models.qwen3_coder` | 代码场景 |
| `multi_models.text2image` | 文生图工具 |

前端模型服务页中的自定义模型供智能体等场景选择；它不会替换配置文件中的向量与重排模型。`show_model` 是展示名称，`model` 是服务商实际请求标识。

本文示例使用 DeepSeek Flash 对话模型。加载器的向量、视觉和重排默认项仍是通义模型，需要单独配置相应的 Key、模型和接口，不能复用 DeepSeek Key；重排接口并非普通聊天接口。知识库默认使用 Chroma，可通过 `rag.vector_db.mode` 选择其他实现；全文检索由 `rag.enable_elasticsearch` 控制。完整示例见 [简易配置指南](../../docs/simple-config.md#模型继承与能力边界)。

## 代码结构

```text
src/backend/
├── agentchat/
│   ├── main.py                 # FastAPI 入口与生命周期
│   ├── settings.py             # 配置加载与默认值
│   ├── config.simple.yaml      # 简易配置模板
│   ├── config/                 # 默认工具、MCP、智能体和 Skill 模板
│   ├── api/v1/                 # HTTP 与流式接口
│   ├── api/services/           # 业务服务，包含 ConversationService
│   ├── auth/                   # JWT 实现
│   ├── core/                   # 智能体、模型封装与用量回调
│   ├── database/
│   │   ├── connection.py       # 数据库 URL、驱动与连接
│   │   ├── init_data.py        # 系统模板初始化
│   │   ├── models/             # 数据表定义
│   │   └── dao/                # 数据访问与新用户资源复制
│   ├── protocols/ag_ui/        # SSE 编码与场景适配
│   ├── mcp_proxy/              # MCP 代理与会话管理
│   ├── services/               # RAG、记忆、MCP、存储与任务服务
│   ├── tools/                  # 内置工具
│   ├── middleware/             # 请求追踪与白名单
│   └── utils/                  # 日志、上下文等公共辅助模块
└── tests/
    ├── test_*.py               # 自动化测试
    └── manual/                 # 需要显式运行的手动脚本
```

## 接口与流式事件

业务路由以 `/api/v1` 为前缀，准确请求结构以运行中的 Swagger 文档为准。

| 接口或模块 | 作用 |
| --- | --- |
| `/conversation`、`/conversation/list` | 会话创建、编辑、删除与列表；字段使用 `conversation_id` |
| `/completion` | 智能体流式对话 |
| `/mars/chat` | Mars 任务流式对话 |
| `history` | 历史消息与反馈 |
| `agent`、`tool`、`agent_skill` | 智能体、工具和技能管理 |
| `knowledge`、`knowledge_file` | 知识库与文件处理 |
| `mcp_server`、`mcp_user_config` | MCP 服务与连接配置 |
| `register_mcp`、`register_task` | MCP 创建与任务记录 |
| `llm`、`usage_stats` | 模型配置与调用统计 |
| `workspace`、`user` | 工作区与用户相关接口 |

同一会话可以切换智能体。首条用户消息保存后异步生成标题，不阻塞主回复；服务层保留会话归属、资源权限和历史保存校验。

AG-UI 通过请求头 `X-AgentChat-Protocol: ag-ui/1.0` 协商，响应仍是 SSE。适配器负责事件转换与 SDK 编码，权限、历史保存和 Token 统计保留在业务层。没有该请求头时保留原事件格式，详情见 [协议说明](../../docs/ag-ui.md)。

## 初始化与用户资源

启动时按顺序准备数据库表、系统模型、工具、Skill、MCP 和默认智能体。模板位于 `agentchat/config/`，初始化不会下载默认头像、联网探测 MCP 或调用模型生成 MCP 名称。

新账号与其默认资源在同一事务中创建。智能体、工具、Skill 和 MCP 使用独立 ID，绑定也指向当前用户副本；知识库由用户自行创建。系统默认模型与用户自定义模型分别管理，不应将所有系统配置理解成用户副本。

新增 MCP 的名称和描述由当前进程的异步任务补齐，不建立任务表。页面工具列表的默认快照不能保证远端服务始终可用，实际连接仍取决于远端状态。模板修改也不会自动覆盖用户已经编辑的副本。

当前初始化按新表结构创建数据，不提供旧 `dialog` 数据库结构的自动迁移。更新已有部署时，需要单独处理数据库结构与数据。

## Token 统计与日志

模型回调记录服务商返回的输入、输出用量，并通过请求上下文关联用户、智能体和会话。供应商没有返回 usage 时，不应把估算值当作实际用量。详见 [统计说明](../../docs/conversation-token-usage.md)。

日志输出到终端与文件，默认级别 `INFO`；文件按 20 MB 轮转、保留 7 天。请求日志包含 trace ID，任务和工具日志按场景补充会话、运行与调用 ID。常见凭据会被脱敏，正文类日志主要位于 `DEBUG`。详见 [日志说明](../../docs/logging.md)。

## 开发与测试

在 `src/backend` 执行：

```bash
uv sync --locked --group dev
uv run --locked pytest tests -q
```

跨语言协议测试需要 Node.js 和前端依赖，先在 `src/frontend` 执行 `npm ci`。`tests/manual/` 默认不收集，其中部分脚本依赖额外库、文件或外部服务。详见 [测试说明](tests/README.md)。

新增接口时，在 `api/v1/` 定义路由、在 `api/services/` 放业务逻辑，并在路由聚合文件注册。新增数据表需在数据库模块导入；自动建表不能代替已有表的结构迁移。

## 故障排查与部署

| 现象 | 检查方向 |
| --- | --- |
| 启动仍连接 Redis 或对象存储 | 确认 `AGENTCHAT_CONFIG` 指向简易配置；配置加载日志会显示所选文件名 |
| 简易模式启动失败 | 检查 YAML 格式及非空的 `multi_models.chat_model.api_key` |
| 健康检查正常但聊天失败 | 检查模型 Key、模型标识、地址与服务权限；健康检查不调用模型 |
| 聊天可用但知识库失败 | 检查 embedding、rerank 配置及向量目录权限 |
| 出现记忆检索失败日志 | 检查向量模型；辅助记忆异常会跳过本轮记忆，不代表记忆服务已经恢复 |
| MCP 工具调用失败 | 检查服务连接、认证与远端状态，确认智能体已绑定该 MCP |
| 上传链接打不开 | 检查 `storage.local.base_url`、后端实际地址及反向代理的 `/uploads/` 转发 |
| 前端请求失败或端口被占用 | 检查后端监听端口、前端代理与实际启动地址 |

FastAPI 是 ASGI 应用，可通过 Uvicorn 运行。对外部署时配置反向代理、SSE 转发与持久化目录；多进程需要共享缓存和文件存储。现有 [Docker 文件](../../docker/) 保留开发部署组合，本轮没有验证完整容器启动流程。

本项目采用 [MIT License](../../LICENSE)。
