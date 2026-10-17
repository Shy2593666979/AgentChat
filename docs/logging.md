# 后端日志

统一入口是 `agentchat/utils/logging.py`，业务继续使用 Loguru；标准 `logging`、Uvicorn 和第三方库通过同一出口输出。默认级别为 INFO，可在配置文件中设置 `log_level: DEBUG`，省略时使用默认值。非法级别会在启动时报错。

日志默认保存在 `src/backend/logs/`，不依赖启动工作目录：

- `app.log`：当前级别及以上的全部日志。
- `error.log`：ERROR 及以上的错误日志。
- 单个文件达到 20 MB 时轮转，归档为 ZIP，保留 7 天；多进程部署应为每个进程指定独立目录，或输出到各自的容器控制台统一收集。

可通过环境变量 `AGENTCHAT_LOG_DIR` 指定目录。控制台使用同样格式，文件为 UTF-8，不包含颜色控制码。

```text
2026-10-15 22:36:15.120 | INFO | api.request | trace_id=a82f19c3 | 请求开始 method=POST path=/api/v1/completion run_id=r901
2026-10-15 22:36:15.132 | INFO | conversation | trace_id=a82f19c3 | 对话开始 user_id=3 conversation_id=c102 run_id=r901 agent_id=a12
2026-10-15 22:36:15.850 | INFO | model | trace_id=a82f19c3 | 模型首个响应 latency_ms=718 user_id=3 conversation_id=c102 run_id=r901 agent_id=a12
2026-10-15 22:36:18.420 | INFO | conversation | trace_id=a82f19c3 | 对话完成 duration_ms=3288 input_tokens=120 output_tokens=85 user_id=3 conversation_id=c102 run_id=r901 agent_id=a12
```

请求 Trace ID 优先读取 `X-Trace-ID`，其次读取 `x-b3-traceid`；不符合字符及长度限制时重新生成。响应始终返回 `X-Trace-ID`。每个请求的日志上下文独立，后台子任务和线程继承当前标识。AG-UI 的 `runId` 与流式日志中的 `run_id` 一致。

纯 ASGI 请求中间件在整个响应结束后记录总耗时，并区分完成、失败和取消；Uvicorn 自带访问日志关闭，避免重复。HTTP 状态与业务结果分别记录：HTTP 已经发送 200 后仍可能出现“对话失败”。流式业务另记录首个文本输出、完成、失败、取消及等待人工确认，关闭时仍执行原有上游清理和历史保存逻辑。

MCP 工具、普通智能体工具和 Mars 工具记录调用开始、完成、失败或取消，包含工具名、调用 ID 和耗时；不记录调用参数和返回正文。模型用量日志沿用真实用量回调，记录已获取的输入和输出 Token；流式完成日志只汇总本轮上下文中已经记录的用量，不估算供应方未返回的消耗。

已配置及运行时注册的模型密钥、Bearer/JWT、常见敏感字段与 URL 凭据、查询参数统一脱敏。异常保留调用栈，禁用局部变量转储并截断过长文本。正常级别不记录完整查询、聊天正文、工具结果；部分历史调试明细改为 DEBUG，主动开启 DEBUG 时仍须按业务数据管理日志访问权限。

`tests/test_logging.py` 覆盖脱敏、标准日志接管、异常安全输出、轮转与重复初始化、并发上下文、完整流式耗时、AG-UI 运行标识、失败与取消、工具错误结果。全新应用的 HTTP 测试使用临时日志目录。
