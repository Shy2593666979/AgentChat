# 简易配置与本地运行

简易模式保留常用 YAML 配置项，将数据库、缓存和文件存储默认设置为本地方案。你可以先填写一个对话模型开始聊天，再为知识库、搜索或其他工具补充需要的服务。

完整的前后端安装步骤见 [快速开始](../README.md#快速开始)。本页命令均在 `src/backend` 目录执行。

## 创建本地配置

先安装 Python 3.12、uv，再安装依赖：

```bash
uv sync --locked --python 3.12
```

Windows PowerShell：

```powershell
Copy-Item agentchat/config.simple.yaml agentchat/config.local.simple.yaml
```

Linux / macOS：

```bash
cp agentchat/config.simple.yaml agentchat/config.local.simple.yaml
```

编辑复制后的文件，保留模板其他内容，填写：

```yaml
multi_models:
  chat_model:
    api_key: "填写你的 DeepSeek API Key"
    base_url: "https://api.deepseek.com"
    model_name: "deepseek-flash"
```

本示例使用 [DeepSeek Flash](https://api-docs.deepseek.com/zh-cn/)。复制模板后，将上述三个字段一起修改。本地配置文件匹配 `.gitignore` 中的 `config.local*.yaml`。

## 指定配置并启动

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

环境变量只在当前终端及其子进程中生效。新开终端启动后端时，需要重新设置；路径相对于启动工作目录解析。

加载优先级为：显式传给 `init_app_settings` 的配置路径 → `AGENTCHAT_CONFIG` → `agentchat/config.local.yaml` → `agentchat/config.yaml`。不会自动选择 `config.local.simple.yaml`，也不会在简易模式中读取完整配置的凭据。加载失败会阻止启动。

访问 [健康检查](http://127.0.0.1:7860/health)，确认返回 `{"status":"OK"}`。前端在另一个终端启动，默认访问 `8090`，步骤见 [根目录说明](../README.md#快速开始)。模型调用需要另外发送消息验证。

## 省略参数时使用什么

| 配置 | 简易模式默认值 | 数据是否保留 |
| --- | --- | --- |
| `database.url` | `sqlite:///data/agentchat.db` | 文件保留；目录与表自动创建 |
| `redis.endpoint` | `null`，使用单进程内存缓存 | 重启清空临时缓存和内存 MCP 代理会话 |
| `storage.mode` | `local` | 上传文件保留在本地目录 |
| `storage.local.path` | `data/uploads` | 相对 `src/backend` |
| `rag.vector_db.mode` | `chroma` | 知识库向量保留在启动目录的 `vector_db/` |
| `rag.enable_elasticsearch` | `false` | 不连接 Elasticsearch |
| `log_level` | `INFO` | 文件默认写入 `src/backend/logs/` |

数据库与本地上传的相对路径固定以 `src/backend` 为基准；知识库 `vector_db/` 和长期记忆 `memory_db/` 则相对启动工作目录。建议始终从 `src/backend` 启动，避免产生多份向量目录。

系统默认 MCP 和 Skill 从 `agentchat/config/` 加载。初始化不下载默认头像，也不联网探测 MCP 或生成工具名称；用户注册时复制自己的默认资源。

## 模型继承与能力边界

`simple_mode: true` 会先生成模型默认值，再逐层应用文件中的显式配置：

- `tool_call_model`、`reasoning_model`、`qwen3_coder` 默认复用 `chat_model` 的 Key、地址和模型标识。
- `embedding` 默认复用同一 Key 和地址，模型名为 `text-embedding-v4`。
- `qwen_vl` 默认复用同一 Key 和地址，模型名为 `qwen-vl-plus`。
- `rerank` 默认复用同一 Key，使用 `gte-rerank-v2` 和通义重排接口。
- 文生图没有默认凭据，需要另外配置。

加载器中的向量、视觉和重排默认模型仍按通义服务设置。上面的 DeepSeek 示例用于对话，不能直接用 DeepSeek Key 调用这些通义模型。使用知识库前需要分别配置 embedding 与 rerank；通用聊天接口不能直接代替重排接口。

例如，DeepSeek Flash 用于聊天，通义服务用于知识库向量化与重排：

```yaml
simple_mode: true
multi_models:
  chat_model:
    api_key: "填写你的 DeepSeek API Key"
    base_url: "https://api.deepseek.com"
    model_name: "deepseek-flash"
  embedding:
    api_key: "通义服务 Key"
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model_name: "text-embedding-v4"
  rerank:
    api_key: "通义服务 Key"
    base_url: "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"
    model_name: "gte-rerank-v2"
```

天气、Tavily、邮件等工具仍遵循各自的服务配置要求。它们不再是基础启动的必填项，不代表全部工具都已免 Key。默认 MCP 也需要远端端点可访问，并绑定到智能体后才会用于该智能体的对话。

## 修改端口或部署地址

例如，将后端端口改为 `7861`：

```yaml
server:
  host: "127.0.0.1"
  port: 7861
storage:
  mode: "local"
  local:
    path: "data/uploads"
    base_url: "http://127.0.0.1:7861/uploads/"
```

同时把启动命令中的 `--port` 改为 `7861`，并在 `src/frontend/.env.local` 中填写：

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:7861
```

重启前后端后生效。Uvicorn 的监听参数由启动命令决定；只修改 YAML 中的端口不会改变命令行指定的监听端口。未显式填写 `storage.local.base_url` 时，加载器会按 YAML 中的服务地址生成访问链接。

对外部署时，`storage.local.base_url` 应是浏览器实际可访问的后端地址，反向代理同时转发 `/api/` 和 `/uploads/`。内存缓存适用于本地单进程，多进程应配置 Redis。

## 使用完整配置

需要更多选项时，可以在简易文件中添加与完整配置相同的字段，继续使用默认值补齐；也可以复制 `agentchat/config.yaml` 为本地文件并显式指定路径。后者没有启用 `simple_mode`，需要分别核对模型、缓存、对象存储等配置，不会自动继承简易模板的模型配置。

修改配置后重启后端。切换数据库连接、存储方式或向量库不会自动搬迁已有数据。更多内容见 [后端文档](../src/backend/README.md)。
