from agentchat.utils.logging import log_event


async def search_optional_memory(client, *, query: str, run_id: str | None = None, user_id: str | None = None):
    """长期记忆是辅助能力，服务异常时继续使用当前会话上下文。"""
    try:
        scope = {
            key: value
            for key, value in {
                "run_id": run_id,
                "user_id": user_id,
            }.items()
            if value is not None
        }
        memories = await client.search(query=query, **scope)
        return '\n'.join(item.get('memory', '') for item in memories.get('results', [])), True
    except Exception as error:
        log_event("memory", "记忆检索失败，跳过本轮记忆", level="WARNING",
                  error_type=type(error).__name__, upstream_status=getattr(error, "status_code", None))
        return None, False


async def store_optional_memory(client, *, messages: list, run_id: str | None = None, user_id: str | None = None):
    """记忆写入失败不应影响回答及聊天记录的保存。"""
    try:
        scope = {
            key: value
            for key, value in {
                "run_id": run_id,
                "user_id": user_id,
            }.items()
            if value is not None
        }
        await client.add(messages=messages, **scope)
        return True
    except Exception as error:
        log_event("memory", "记忆写入失败，保留当前回答", level="WARNING",
                  error_type=type(error).__name__, upstream_status=getattr(error, "status_code", None))
        return False
