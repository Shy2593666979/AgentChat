import logging
import threading
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from agentchat.database.models.memory_history import MemoryHistoryTable
from sqlmodel import Session, select, delete
from agentchat.database.session import session_getter

logger = logging.getLogger(__name__)


class MemoryHistoryDao:
    """Memory History 数据访问对象类 - MySQL版本"""
    
    _lock = threading.Lock()

    @classmethod
    def add_history(
        cls,
        memory_id: str,
        old_memory: Optional[str],
        new_memory: Optional[str],
        event: str,
        *,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        is_deleted: bool = False,
        actor_id: Optional[str] = None,
        role: Optional[str] = None,
    ) -> None:
        """添加记忆历史记录"""
        with cls._lock:
            try:
                with session_getter() as session:
                    history_record = MemoryHistoryTable(
                        id=str(uuid.uuid4()),
                        memory_id=memory_id,
                        old_memory=old_memory,
                        new_memory=new_memory,
                        event=event,
                        created_at=created_at,
                        updated_at=updated_at,
                        is_deleted=is_deleted,
                        actor_id=actor_id,
                        role=role,
                    )
                    session.add(history_record)
                    session.commit()
                    logger.info(f"Successfully added memory history record for memory_id: {memory_id}")
            except Exception as e:
                logger.error(f"Failed to add history record: {e}")
                raise

    @classmethod
    def get_history(cls, memory_id: str) -> List[Dict[str, Any]]:
        """获取指定memory_id的历史记录"""
        with cls._lock:
            try:
                with session_getter() as session:
                    sql = select(MemoryHistoryTable).where(
                        MemoryHistoryTable.memory_id == memory_id
                    ).order_by(
                        MemoryHistoryTable.created_at.asc(),
                        MemoryHistoryTable.updated_at.asc()
                    )
                    result = session.exec(sql).all()
                    
                    return [
                        {
                            "id": record.id,
                            "memory_id": record.memory_id,
                            "old_memory": record.old_memory,
                            "new_memory": record.new_memory,
                            "event": record.event,
                            "created_at": record.created_at.isoformat() if record.created_at else None,
                            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
                            "is_deleted": record.is_deleted,
                            "actor_id": record.actor_id,
                            "role": record.role,
                        }
                        for record in result
                    ]
            except Exception as e:
                logger.error(f"Failed to get history for memory_id {memory_id}: {e}")
                raise

    @classmethod
    def get_all_history(cls) -> List[Dict[str, Any]]:
        """获取所有历史记录"""
        with cls._lock:
            try:
                with session_getter() as session:
                    sql = select(MemoryHistoryTable).order_by(
                        MemoryHistoryTable.created_at.asc()
                    )
                    result = session.exec(sql).all()
                    
                    return [record.to_dict() for record in result]
            except Exception as e:
                logger.error(f"Failed to get all history: {e}")
                raise

    @classmethod
    def delete_history_by_memory_id(cls, memory_id: str) -> None:
        """删除指定memory_id的所有历史记录"""
        with cls._lock:
            try:
                with session_getter() as session:
                    sql = delete(MemoryHistoryTable).where(
                        MemoryHistoryTable.memory_id == memory_id
                    )
                    session.exec(sql)
                    session.commit()
                    logger.info(f"Successfully deleted history records for memory_id: {memory_id}")
            except Exception as e:
                logger.error(f"Failed to delete history for memory_id {memory_id}: {e}")
                raise

    @classmethod
    def delete_history_by_id(cls, history_id: str) -> None:
        """删除指定ID的历史记录"""
        with cls._lock:
            try:
                with session_getter() as session:
                    sql = delete(MemoryHistoryTable).where(
                        MemoryHistoryTable.id == history_id
                    )
                    session.exec(sql)
                    session.commit()
                    logger.info(f"Successfully deleted history record with id: {history_id}")
            except Exception as e:
                logger.error(f"Failed to delete history record with id {history_id}: {e}")
                raise

    @classmethod
    def reset(cls) -> None:
        """重置表（删除所有记录）"""
        with cls._lock:
            try:
                with session_getter() as session:
                    sql = delete(MemoryHistoryTable)
                    session.exec(sql)
                    session.commit()
                    logger.info("Successfully reset memory_history table")
            except Exception as e:
                logger.error(f"Failed to reset memory_history table: {e}")
                raise

    @classmethod
    def update_history_record(
        cls,
        history_id: str,
        **kwargs
    ) -> None:
        """更新历史记录"""
        with cls._lock:
            try:
                with session_getter() as session:
                    sql = select(MemoryHistoryTable).where(
                        MemoryHistoryTable.id == history_id
                    )
                    record = session.exec(sql).first()
                    
                    if not record:
                        raise ValueError(f"History record with id {history_id} not found")
                    
                    # 更新字段
                    for key, value in kwargs.items():
                        if hasattr(record, key):
                            setattr(record, key, value)
                    
                    # 自动更新 updated_at
                    record.updated_at = datetime.now()
                    
                    session.add(record)
                    session.commit()
                    logger.info(f"Successfully updated history record with id: {history_id}")
            except Exception as e:
                logger.error(f"Failed to update history record with id {history_id}: {e}")
                raise

    @classmethod
    def mark_as_deleted(cls, history_id: str) -> None:
        """标记历史记录为已删除"""
        cls.update_history_record(history_id, is_deleted=True)

    @classmethod
    def get_history_by_event(cls, event: str) -> List[Dict[str, Any]]:
        """根据事件类型获取历史记录"""
        with cls._lock:
            try:
                with session_getter() as session:
                    sql = select(MemoryHistoryTable).where(
                        MemoryHistoryTable.event == event
                    ).order_by(MemoryHistoryTable.created_at.asc())
                    result = session.exec(sql).all()
                    
                    return [record.to_dict() for record in result]
            except Exception as e:
                logger.error(f"Failed to get history by event {event}: {e}")
                raise

    @classmethod
    def get_history_by_actor(cls, actor_id: str) -> List[Dict[str, Any]]:
        """根据操作者ID获取历史记录"""
        with cls._lock:
            try:
                with session_getter() as session:
                    sql = select(MemoryHistoryTable).where(
                        MemoryHistoryTable.actor_id == actor_id
                    ).order_by(MemoryHistoryTable.created_at.asc())
                    result = session.exec(sql).all()
                    
                    return [record.to_dict() for record in result]
            except Exception as e:
                logger.error(f"Failed to get history by actor_id {actor_id}: {e}")
                raise

