# 简易配置

`src/backend/agentchat/config.simple.yaml` 沿用完整配置的结构，保留服务地址、数据库、缓存、模型、文件存储和向量库这些常用设置。填好 `multi_models.chat_model.api_key` 后可以直接使用模板里的本地默认方案，不需要逐项配置外部服务。

`simple_mode: true` 启用简易模式。未填写的细节由加载器补齐：工具调用、推理默认复用对话模型，向量模型默认复用对话模型的 Key 和地址。也可以单独覆盖任意模型配置。默认对话模型为 `qwen-plus`，向量模型为 `text-embedding-v4`，是否有权限和费用以模型服务商为准。

在 `src/backend` 目录的 PowerShell 中启动：

```powershell
$env:AGENTCHAT_CONFIG = "agentchat/config.simple.yaml"
.venv\Scripts\python.exe -m uvicorn agentchat.main:app --host 127.0.0.1 --port 7860
```

若虚拟环境位于项目根目录，请将 Python 路径改为 `..\..\.venv\Scripts\python.exe`。

也可以复制为已被 Git 忽略的 `agentchat/config.local.simple.yaml`，填写真实 Key 后将环境变量指向该文件。

加载优先级：显式传入的配置路径 → `AGENTCHAT_CONFIG` → `config.local.yaml` → `config.yaml`。不会自动切换当前完整配置。简易模式不会读取完整配置中的凭据。

省略字段的默认行为：

- SQLite：`src/backend/data/agentchat.db`，自动创建目录和表，会话及配置保留在本地。
- 缓存：不连接 Redis，使用有容量限制、支持过期的单进程内存缓存；重启后临时缓存和 MCP 代理会话清空。多进程部署请使用 Redis。
- 文件：保存至 `src/backend/data/uploads`，通过后端 `/uploads/` 路径访问，重启后保留。访问方式与现有公共对象存储 URL 一致。
- 向量库：本地 Chroma，不依赖 Milvus 或 Elasticsearch。
- 默认 MCP 和 Skill：沿用现有本地配置加载流程。
- 可选服务：不要求配置 OSS、MinIO、微信或 Langfuse；所有模式均不下载或上传预置用户头像，默认头像由前端显示。

简易配置支持按需添加高级字段，并逐层覆盖默认值。例如更换模型或部署地址：

```yaml
simple_mode: true
multi_models:
  chat_model:
    api_key: "你的 Key"
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model_name: "qwen-plus"
storage:
  mode: "local"
  local:
    base_url: "https://你的后端域名/uploads/"
```

其他服务商的聊天 Key 不一定支持上述向量、视觉或重排模型，请通过 `multi_models` 分别覆盖。文生图没有默认凭据，不属于基础聊天能力。

天气、Tavily 等原有第三方工具尚未替换为免 Key 实现。本次仅将它们从启动必填配置中移除，并延迟创建搜索客户端；调用这些工具仍需要对应服务可用。不要把省略配置理解为所有第三方工具均已免费接入。

未使用的外部工具凭据、OSS/MinIO 凭据、微信和追踪配置不放在简易模板中；需要时可从完整配置复制对应部分。此前 `model.api_key` 的单模型简写仍然兼容。

配置格式错误、简易模式 Key 为空时直接阻止启动；不会输出配置内容或 Key。
