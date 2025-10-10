from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, select, Session, delete
from agentchat.database.session import session_getter
from agentchat.database.models.role import AdminRole
from agentchat.database.models.user_role import UserRoleBase, UserRole


class UserRoleDao(UserRoleBase):

    @classmethod
    def get_user_roles(cls, user_id: str) -> List[UserRole]:
        with session_getter() as session:
            return session.exec(select(UserRole).where(UserRole.user_id == user_id)).all()

    @classmethod
    def get_roles_user(cls, role_ids: List[str], page: int = 0, limit: int = 0) -> List[UserRole]:
        """
        获取角色对应的用户
        """
        with session_getter() as session:
            statement = select(UserRole).where(UserRole.role_id.in_(role_ids))
            if page and limit:
                statement = statement.offset((page - 1) * limit).limit(limit)
            return session.exec(statement).all()

    @classmethod
    def get_admins_user(cls) -> List[UserRole]:
        """
        获取所有超级管理的账号
        """
        with session_getter() as session:
            statement = select(UserRole).where(UserRole.role_id == AdminRole)
            return session.exec(statement).all()

    @classmethod
    def set_admin_user(cls, user_id: str) -> UserRole:
        """
        设置用户为超级管理员
        """
        with session_getter() as session:
            user_role = UserRole(user_id=user_id, role_id=AdminRole)
            session.add(user_role)
            session.commit()
            session.refresh(user_role)
            return user_role

    @classmethod
    def add_user_roles(cls, user_id: str, role_ids: List[str]) -> List[UserRole]:
        """
        给用户批量添加角色
        """
        with session_getter() as session:
            user_roles = [UserRole(user_id=user_id, role_id=role_id) for role_id in role_ids]
            session.add_all(user_roles)
            session.commit()
            return user_roles

    @classmethod
    def delete_user_roles(cls, user_id: str, role_ids: List[str]) -> None:
        """
        将用户从某些角色中移除
        """
        with session_getter() as session:
            statement = delete(UserRole).where(UserRole.user_id == user_id).where(UserRole.role_id.in_(role_ids))
            session.exec(statement)
            session.commit()
