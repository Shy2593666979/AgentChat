import logging

from contextlib import contextmanager
from typing import Iterator

from sqlmodel import Session
from agentchat.database import engine

logger = logging.getLogger(__name__)

@contextmanager
def session_getter() -> Iterator[Session]:
    session = Session(engine)

    try:
        yield session
    except Exception as e:
        logger.info('Session rollback because of exception:{}', e)
        session.rollback()
        raise
    finally:
        session.close()