from datetime import datetime

from agentchat.api.services.agent import AgentService
from agentchat.core.models.manager import ModelManager
from agentchat.database.dao.dialog import DialogDao
from agentchat.database.dao.history import HistoryDao
from agentchat.database.models.user import AdminUser
from agentchat.prompts.completion import GENERATE_CHAT_SUMMARY


class DialogService:

    @classmethod
    async def create_dialog(cls, name: str, agent_id: str, agent_type: str, user_id: str):
        """Create a new dialog"""
        try:
            dialog = await DialogDao.create_dialog(
                name=name,
                agent_id=agent_id,
                agent_type=agent_type,
                user_id=user_id
            )
            return dialog.to_dict()
        except Exception as err:
            raise ValueError(f"Add Dialog Appear Error: {err}")

    @classmethod
    async def select_dialog(cls, dialog_id: str):
        """Select dialog by dialog_id"""
        try:
            results = await DialogDao.select_dialog_by_id(dialog_id=dialog_id)
            return [res.to_dict() for res in results]
        except Exception as err:
            raise ValueError(f"Select Dialog Appear Error: {err}")

    @classmethod
    async def get_list_dialog(cls, user_id: str):
        """Get all dialogs for a user"""
        try:
            results = await DialogDao.get_dialog_by_user(user_id=user_id)
            return [res.to_dict() for res in results]
        except Exception as err:
            raise ValueError(f"Get List Dialog Appear Error: {err}")

    @classmethod
    async def get_agent_by_dialog_id(cls, dialog_id: str):
        """Get agent information by dialog_id"""
        try:
            dialog = await DialogDao.get_agent_by_dialog_id(dialog_id=dialog_id)
            return await AgentService.select_agent_by_id(dialog.agent_id)
        except Exception as err:
            raise ValueError(f"Select Dialog Appear Error: {err}")

    @classmethod
    async def update_dialog_time(cls, dialog_id: str):
        """Update dialog's create time"""
        try:
            await DialogDao.update_dialog_time(dialog_id=dialog_id)
        except Exception as err:
            raise ValueError(f"Update Dialog Create Time Appear Error: {err}")

    @classmethod
    async def delete_dialog(cls, dialog_id: str):
        """Delete dialog and its history"""
        try:
            await DialogDao.delete_dialog_by_id(dialog_id=dialog_id)
            await HistoryDao.delete_history_by_dialog_id(dialog_id=dialog_id)
        except Exception as err:
            raise ValueError(f"Delete Dialog Appear Error: {err}")

    @classmethod
    async def verify_user_permission(cls, dialog_id: str, user_id: str):
        """Verify user has permission to access dialog"""
        dialog = await DialogDao.get_agent_by_dialog_id(dialog_id=dialog_id)
        if user_id not in (AdminUser, dialog.user_id):
            raise ValueError(f"没有权限访问")

    @classmethod
    async def get_dialog_history_summary(cls, dialog_id):
        dialog = await DialogDao.select_dialog_by_id(dialog_id)
        return dialog.summary

    @classmethod
    async def update_dialog_summary(cls, dialog_id: str, user_id: str, cutoff_tokens: int=5000):
        messages = await HistoryDao.select_history_from_time(
            dialog_id=dialog_id,
            k=10000
        )
        dialog = await DialogDao.select_dialog_by_id(dialog_id)

        if dialog.user_id != user_id:
            raise ValueError(f"无权限访问 {dialog_id} 数据")
        current_summary = dialog.summary
        summary_last_time = dialog.summary_last_time

        if not messages:
            return None
        if summary_last_time:
            incremental_messages = [
                m for m in messages if m.create_time and m.create_time > summary_last_time
            ]
        else:
            incremental_messages = messages

        if not incremental_messages:
            return None

        # 两两分组
        pairs = []
        i = 0
        while i < len(incremental_messages) - 1:
            if incremental_messages[i].role == "user" and incremental_messages[i + 1].role == "assistant":
                pairs.append((incremental_messages[i], incremental_messages[i + 1]))
                i += 2
            else:
                i += 1

        if not pairs:
            return None

        # 至少保留一对
        # 如果只有一对，并且 token 超过 cutoff → 不总结
        if len(pairs) == 1:
            pair_tokens = sum((m.token_usage or len(m.content) // 4) for m in pairs[0])
            if pair_tokens > cutoff_tokens:
                return None

        # 从后往前截断 token
        total_tokens = 0
        kept_pairs = []

        for pair in reversed(pairs):
            pair_tokens = sum((m.token_usage or len(m.content) // 4) for m in pair)

            if total_tokens + pair_tokens > cutoff_tokens:
                break

            kept_pairs.append(pair)
            total_tokens += pair_tokens

        kept_pairs = list(reversed(kept_pairs))

        # 切分messages
        cutoff_index = len(pairs) - len(kept_pairs)
        old_pairs = pairs[:cutoff_index]

        # 保证 new 至少有一对
        if not kept_pairs:
            # 把最后一对强行放入 new
            kept_pairs = [pairs[-1]]
            old_pairs = pairs[:-1]

        if not old_pairs:
            return None

        # 构造 summary 输入
        def format_messages(msgs):
            texts = []
            for m in msgs:
                role = "User" if m.role == "user" else "Assistant"
                texts.append(f"{role}: {m.content}")
            return "\n".join(texts)

        old_messages = [m for pair in old_pairs for m in pair]

        summary_input = f"""
        【已有总结】
        {current_summary or "（暂无）"}

        【新增需要总结的对话】
        {format_messages(old_messages)}
        """

        # 调用模型
        messages_prompt = GENERATE_CHAT_SUMMARY.format(summary_input=summary_input)
        summary = await cls._generate_messages_summary(messages_prompt)

        # 更新 summary_last_time
        # 用“最后一个参与总结的消息时间”
        last_time = max(
            (m.create_time for m in old_messages if m.create_time),
            default=None
        )

        await DialogDao.update_dialog_summary(dialog_id, summary, last_time)
        return None

    @classmethod
    async def _generate_messages_summary(cls, messages_prompt):
        conversation_model = ModelManager.get_conversation_model()
        response = await conversation_model.ainvoke(
            messages_prompt
        )
        return response.content


    @classmethod
    def split_messages_by_token(cls, messages, cutoff_tokens: int):
        if not messages or cutoff_tokens <= 0:
            return [], []

        # user、assistant两两分组
        pairs = []
        i = 0
        while i < len(messages) - 1:
            if messages[i].role == "user" and messages[i + 1].role == "assistant":
                pairs.append((messages[i], messages[i + 1]))
                i += 2
            else:
                i += 1

        if not pairs:
            return [], []

        # 从后往前累计 token
        total_tokens = 0
        kept_pairs = []

        for pair in reversed(pairs):
            pair_tokens = sum((m.token_usage or len(m.content) // 4) for m in pair)

            if total_tokens + pair_tokens > cutoff_tokens:
                break

            kept_pairs.append(pair)
            total_tokens += pair_tokens

        kept_pairs = list(reversed(kept_pairs))

        # 切分
        cutoff_index = len(pairs) - len(kept_pairs)
        old_pairs = pairs[:cutoff_index]

        if not old_pairs or not kept_pairs:
            return [], []

        # 展平成 messages
        old_messages = [m for pair in old_pairs for m in pair]
        new_messages = [m for pair in kept_pairs for m in pair]

        return old_messages, new_messages



