# 会话内切换智能体

会话业务统一使用 `conversation` 命名：表名为 `conversation`，关联字段为 `conversation_id`，管理接口为 `/api/v1/conversation`。前端路由参数、历史查询和 Token 统计同步使用该字段，不提供旧命名兼容接口。AG-UI 中仍按协议使用 `threadId`，其值对应业务会话 ID。

会话 ID、标题、摘要和历史记录独立于当前智能体。`conversation.agent_id` 保存最近选择的智能体；`POST /completion` 可通过 `agent_id` 指定本次回复使用的智能体，省略时兼容原客户端。

`PUT /conversation` 接受 `conversation_id` 与 `agent_id`，在原会话内保存选择。切换不创建新会话，也不清空草稿、附件或历史。正在生成的回复使用请求开始时的智能体；生成中可以选择下一轮智能体。

每条新回复通过已有消息 `events` 字段保存 `type=agent` 的身份快照，页面显示实际回复者。旧会话首次切换时，为缺少身份信息的历史回复补齐原智能体身份。删除智能体只清空会话当前选择，保留会话和历史；用户可选择其他智能体继续。

第一条用户消息落库时设置 2—10 字符备用标题，并在当前进程内异步调用模型生成话题标题。后续消息与智能体切换不再次生成标题。标题失败、超时或进程中断时保留备用标题，不阻塞回复。`GET /conversation/list` 返回 `title_pending`，前端短暂轮询更新标题。标题更新不会改变会话的活动时间或排序。

异步标题任务的提交、生成、状态查询和关闭清理统一由 `api/services/conversation.py` 的 `ConversationService` 类管理，任务集合与并发限制保存在类中。纯文本标题整理保留在 `utils/conversation_title.py`，供历史保存与标题生成共用。会话读取、智能体切换和消息发送均核对用户访问权限。
