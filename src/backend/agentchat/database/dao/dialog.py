from agentchat.database.models.dialog import DialogTable
from sqlmodel import Session, select, update, desc, delete
from agentchat.database.session import async_session_getter
from datetime import datetime

class DialogDao:

    @classmethod
    async def create_dialog(cls, name: str, agent_id: str, agent_type: str, user_id: str):
        """Create a new dialog with named parameters"""
        dialog = DialogTable(
            name=name,
            agent_id=agent_id,
            agent_type=agent_type,
            user_id=user_id
        )
        async with async_session_getter() as session:
            session.add(dialog)
            await session.commit()
            await session.refresh(dialog)  # 确保获取数据库生成的字段
            return dialog

    @classmethod
    async def select_dialog_by_id(cls, dialog_id: str) -> DialogTable:
        """Select dialog by dialog_id"""
        async with async_session_getter() as session:
            statement = select(DialogTable).where(DialogTable.dialog_id == dialog_id)
            result = await session.exec(statement)
            return result.first()

    @classmethod
    async def get_dialog_by_user(cls, user_id: str):
        """Get all dialogs for a user ordered by create time"""
        async with async_session_getter() as session:
            statement = select(DialogTable).where(
                DialogTable.user_id == user_id
            ).order_by(desc(DialogTable.create_time))
            result = await session.exec(statement)
            return result.all()

    @classmethod
    async def get_agent_by_dialog_id(cls, dialog_id: str):
        """Get agent information by dialog_id"""
        async with async_session_getter() as session:
            statement = select(DialogTable).where(DialogTable.dialog_id == dialog_id)
            result = await session.exec(statement)
            return result.first()

    @classmethod
    async def update_dialog_time(cls, dialog_id: str):
        """Update dialog's create_time to current time"""
        async with async_session_getter() as session:
            statement = update(DialogTable).where(
                DialogTable.dialog_id == dialog_id
            ).values(create_time=datetime.utcnow())
            await session.exec(statement)
            await session.commit()

    @classmethod
    async def delete_dialog_by_id(cls, dialog_id: str):
        """Delete dialog by dialog_id"""
        async with async_session_getter() as session:
            statement = delete(DialogTable).where(DialogTable.dialog_id == dialog_id)
            await session.exec(statement)
            await session.commit()

    @classmethod
    async def check_dialog_iscustom(cls, dialog_id: str):
        """Check if dialog is custom by dialog_id"""
        async with async_session_getter() as session:
            statement = select(DialogTable).where(DialogTable.dialog_id == dialog_id)
            result = await session.exec(statement)
            return result.first()

    @classmethod
    async def delete_from_agent_id(cls, agent_id: str):
        """Delete all dialogs associated with an agent_id"""
        async with async_session_getter() as session:
            statement = delete(DialogTable).where(DialogTable.agent_id == agent_id)
            await session.exec(statement)
            await session.commit()

    @classmethod
    async def update_dialog_summary(cls, dialog_id, summary, summary_last_time):
        """Update dialog summary"""
        async with async_session_getter() as session:
            db_dialog = await session.get(DialogTable, dialog_id)

            if summary:
                db_dialog.summary = summary
            if summary_last_time:
                db_dialog.summary_last_time = summary_last_time

            await session.commit()
            await session.refresh(db_dialog)



