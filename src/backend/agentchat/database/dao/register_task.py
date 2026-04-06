from typing import List

from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import delete, select
from agentchat.database.session import async_session_getter
from agentchat.database.models.register_task import RegisterMcpTask


class RegisterMcpTaskDao:

    @classmethod
    async def create_task(cls, task: RegisterMcpTask) -> RegisterMcpTask:
        async with async_session_getter() as session:
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task

    @classmethod
    async def delete_task(cls, task_id: str):
        async with async_session_getter() as session:
            statement = delete(RegisterMcpTask).where(
                RegisterMcpTask.id == task_id
            )

            result = await session.exec(statement)
            await session.commit()

    @classmethod
    async def add_task_message(cls, task_id: str, message: dict):
        async with async_session_getter() as session:
            task = await session.get(RegisterMcpTask, task_id)

            if not task:
                raise ValueError(f"Task {task_id} not found")

            task.messages = (task.messages or []) + [message]
            await session.commit()
            return task

    @classmethod
    async def extend_previous_content_messages(cls, task_id, content_messages):
        async with async_session_getter() as session:
            task = await session.get(RegisterMcpTask, task_id)

            copy_messages = list(task.messages)
            copy_messages[-1]["content"] = copy_messages[-1]["content"] + content_messages

            task.messages = copy_messages
            flag_modified(task, "messages")
            await session.commit()

    @classmethod
    async def update_message_interrupt_status(cls, task_id: str):
        async with async_session_getter() as session:
            task = await session.get(RegisterMcpTask, task_id)
            if not task or not task.messages:
                return

            content_list = task.messages[-1].get("content", [])

            if not content_list:
                return

            is_modified = False
            for msg in reversed(content_list):
                if msg.get("type") == "interrupt":
                    if not msg["data"].get("status"):
                        msg["data"]["status"] = True
                        is_modified = True
                    break

            if is_modified:
                flag_modified(task, "messages")
                await session.commit()

    @classmethod
    async def get_task(cls, task_id: str) -> RegisterMcpTask:
        async with async_session_getter() as session:
            task = await session.get(RegisterMcpTask, task_id)
            return task

    @classmethod
    async def get_all_tasks(cls, user_id) -> List[RegisterMcpTask]:
        async with async_session_getter() as session:
            statement = select(RegisterMcpTask).where(
                RegisterMcpTask.user_id == user_id
            )
            results = await session.exec(statement)
            return results.all()


    @classmethod
    async def create_task_if_not_exists(cls, task_id: str, user_id: str):
        async with async_session_getter() as session:
            task = await session.get(RegisterMcpTask, task_id)

            if not task:
                task = RegisterMcpTask(
                    id=task_id,
                    user_id=user_id
                )
                session.add(task)
                await session.commit()
                await session.refresh(task)
            return task