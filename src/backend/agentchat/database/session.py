import logging
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncIterator, Iterator

from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

from agentchat.database import async_engine, engine

logger = logging.getLogger(__name__)

@contextmanager
def session_getter() -> Iterator[Session]:
    session = Session(engine)

    try:
        yield session
    except Exception as e:
        logger.warning("数据库会话回滚 error_type=%s", type(e).__name__)
        session.rollback()
        raise
    finally:
        session.close()

@asynccontextmanager
async def async_session_getter() -> AsyncIterator[AsyncSession]:
    session = AsyncSession(async_engine)  # 使用异步引擎创建会话

    try:
        yield session
    except Exception as e:
        logger.warning("数据库会话回滚 error_type=%s", type(e).__name__)
        await session.rollback()  # 异步回滚
        raise
    finally:
        await session.close()  # 异步关闭会话
