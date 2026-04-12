from typing import Optional
from sqlalchemy.orm import selectinload
from sqlmodel import select, delete

from agentchat.database.models.register_mcp_tool import RegisterMcpTool
from agentchat.database.models.register_mcp import RegisterMcpServer
from agentchat.database.session import async_session_getter

class RegisterMcpDao:

    @classmethod
    async def get_by_id(cls, mcp_id: str) -> Optional[RegisterMcpServer]:
        async with async_session_getter() as session:
            return await session.get(RegisterMcpServer, mcp_id)

    @classmethod
    async def get_all(cls, user_id) -> list[RegisterMcpServer]:
        async with async_session_getter() as session:
            result = await session.exec(
                select(RegisterMcpServer).where(
                    RegisterMcpServer.user_id == user_id
                ).options(
                    selectinload(RegisterMcpServer.mcp_tools)
                )
            )
            return result.all()

    @classmethod
    async def save(cls, mcp: RegisterMcpServer) -> RegisterMcpServer:
        async with async_session_getter() as session:
            session.add(mcp)
            await session.commit()
            await session.refresh(mcp)
            return mcp

    @classmethod
    async def delete(cls, mcp_id: str) -> None:
        async with async_session_getter() as session:
            await session.exec(delete(RegisterMcpServer).where(RegisterMcpServer.id == mcp_id))
            await session.commit()

    @classmethod
    async def get_tools_by_mcp_id(cls, mcp_id: str) -> list[RegisterMcpTool]:
        async with async_session_getter() as session:
            result = await session.exec(select(RegisterMcpTool).where(RegisterMcpTool.register_mcp_id == mcp_id))
            return result.all()

    @classmethod
    async def get_tool_by_name(cls, mcp_id: str, tool_name: str) -> Optional[RegisterMcpTool]:
        async with async_session_getter() as session:
            result = await session.exec(
                select(RegisterMcpTool).where(RegisterMcpTool.register_mcp_id == mcp_id, RegisterMcpTool.name == tool_name)
            )
            return result.first()

    @classmethod
    async def save_tool(cls, tool: RegisterMcpTool) -> RegisterMcpTool:
        async with async_session_getter() as session:
            session.add(tool)
            await session.commit()
            await session.refresh(tool)
            return tool

    @classmethod
    async def save_mcp_with_tools(cls, mcp: RegisterMcpServer, tools: list[RegisterMcpTool]) -> RegisterMcpServer:
        async with async_session_getter() as session:
            session.add(mcp)
            for tool in tools:
                session.add(tool)
            await session.commit()
            await session.refresh(mcp)
            return mcp