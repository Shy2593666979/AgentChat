# AG-UI 流式事件适配

后端使用 `ag-ui-protocol==1.0.0` 的事件模型和 `EventEncoder`；前端使用 `@ag-ui/core==1.0.0` 的 `EventSchema` 校验接收的 JSON。

## 目录

```text
agentchat/protocols/ag_ui/
├── __init__.py
├── streaming.py
├── conversation.py
├── mars.py
├── workspace.py
└── mcp.py
```

`streaming.py` 管理每次请求独立的运行状态、消息 ID、工具调用 ID、SSE 编码和生成器关闭；四个场景文件负责业务事件映射。鉴权、模型配置、历史保存及 Token 入库仍由原接口和模型回调负责，没有新增数据库表。

## 协议选择

保持原接口地址和请求体，添加请求头：

```http
X-AgentChat-Protocol: ag-ui/1.0
```

未添加请求头时继续输出旧协议。新版页面的公共 `postEventStream` 已添加该请求头；旧版 API 辅助函数仍可按原格式使用。

本阶段适配的是 **AG-UI 输出事件**。请求体仍为项目原来的 `CompletionReq` 等结构，MCP 同意、拒绝仍走原有接口，不是可以直接传入 `RunAgentInput` 的通用 AG-UI Agent 服务。后续若接入通用 `HttpAgent`，需要再增加标准输入到现有请求模型的转换，不应绕过原有权限校验。

## 事件与状态

- 每次请求发送 `RUN_STARTED`，正常完成发送 `RUN_FINISHED`；执行异常发送 `RUN_ERROR`，不伪装为成功回复。
- `threadId` 在普通会话中对应 `conversation_id`，MCP 中对应 `task_id`；未提供持久会话标识的独立任务使用临时线程 ID。每次请求生成独立 `runId`。
- 正文使用 `TEXT_MESSAGE_START/CONTENT/END`，分片只发送增量，不重复携带累计正文。
- 工具使用 `TOOL_CALL_START/ARGS/END/RESULT`，按真实调用 ID 匹配。`TOOL_CALL_END` 表示参数发送结束，执行结束通过 `TOOL_CALL_RESULT` 表示。工具结果元数据的 `status` 为 `END` 或 `ERROR`，单个工具失败不必终止整轮。
- Mars 的可见分析内容使用 `REASONING_*`；工具输出元数据保留 `tool_id/source/result_key`，维持报告重置、不同工具结果分组的现有行为。
- 工作区任务图通过 `STATE_SNAPSHOT` 返回；步骤开始、结束使用 `STEP_STARTED/FINISHED`。
- 自定义事件只允许固定名称：`agentchat.agent`、`agentchat.knowledge`、`agentchat.notice`、`agentchat.mars.progress`、`agentchat.mars.result_start`、`agentchat.workspace.step_result`、`agentchat.mcp.progress`。每个名称的构造代码决定其数据结构，未知业务事件直接报错，不使用 RAW 静默透传。

MCP 中断通过 `RUN_FINISHED.outcome.type=interrupt` 返回，携带 `interrupts` 及审批元数据。审批请求继续使用现有接口，可附带 `interrupt_id` 校验当前审批。新页面会提交该 ID；过期或重复确认被拒绝。拒绝后修改意见的业务逻辑及模型绑定继续沿用原有实现。

客户端用 `AgUiStreamReader` 集中消费线上协议，再生成现有组件的展示事件。运行未发送终止事件就断开时提示异常，不再把连接关闭直接当成成功。用户主动停止仍由 AbortController 标记，保留页面已接收内容。

关闭协议生成器会关闭上游生成器。普通会话及 MCP 在取消时使用屏蔽取消的数据库清理区保存已收到内容；普通会话取消后不继续执行摘要或长期记忆写入。没有加入自动重试、事件重放或断线续传。

## 历史与统计

数据库继续保存原有正文和业务事件，新工具事件增加调用 ID，实时展示和历史恢复都优先按 ID 匹配，旧记录仍按原规则读取。未将每个文字分片重复写入数据库，也没有通过协议事件再次累计 Token。

AG-UI 不负责持久化 LangGraph 检查点；现有 MCP 检查点仍位于进程内存，重启后的审批恢复不属于本次变更。

## 验证

在 `src/backend` 执行：

```powershell
.venv\Scripts\python.exe -m pytest tests/test_ag_ui.py tests/test_flexible_conversations.py tests/test_simple_config.py tests/test_mcp_model_selection.py -q
```

测试包含 SDK 结构校验、同名工具并发、运行标识隔离、错误和停止清理，以及 Python 实际输出到 TypeScript 消费器的跨语言检查。临时 SQLite 上的 HTTP 集成检查覆盖四类接口、登录权限、消息保存、Token 统计和 MCP 审批；模型输出使用模拟实现，不调用真实模型。

前端独立检查：`node --test tests/ag-ui-stream.cjs`。跨语言用例由后端测试提供实际编码样本；单独执行 Node 时该用例跳过。

参考：[服务端接入](https://docs.ag-ui.com/quickstart/server)、[事件定义](https://docs.ag-ui.com/concepts/events)、[审批中断](https://docs.ag-ui.com/concepts/interrupts)。
