
from agentchat.database.models.user import UserTable
from typing import List
from sqlmodel import Session, select, func, update
from agentchat.database.session import session_getter

class UserDao:

    @classmethod
    def get_user(cls, user_id: str) -> UserTable | None:
        with session_getter() as session:
            statement = select(UserTable).where(UserTable.user_id == user_id)
            return session.exec(statement).first()

    @classmethod
    def get_user_by_ids(cls, user_ids: List[str]) -> List[UserTable] | None:
        with session_getter() as session:
            statement = select(UserTable).where(UserTable.user_id.in_(user_ids))
            return session.exec(statement).all()

    @classmethod
    def get_user_by_username(cls, user_name: str) -> UserTable | None:
        with session_getter() as session:
            statement = select(UserTable).where(UserTable.user_name == user_name)
            return session.exec(statement).first()

    @classmethod
    def update_user(cls, user_id: str, user_name: str, user_email: str, user_password: str) :
        with session_getter() as session:
            session.add(UserTable(user_id=user_id, user_email=user_email,
                                  user_name=user_name, user_password=user_password))
            session.commit()

    @classmethod
    def filter_users(cls, user_ids: List[str], keyword: str = None, page: int = 0, limit: int = 0) -> (List[UserTable], int):
        statement = select(UserTable)
        count_statement = select(func.count(UserTable.user_id))
        if user_ids:
            statement = statement.where(UserTable.user_id.in_(user_ids))
            count_statement = count_statement.where(UserTable.user_id.in_(user_ids))
        if keyword:
            statement = statement.where(UserTable.user_name.like(f'%{keyword}%'))
            count_statement = count_statement.where(UserTable.user_name.like(f'%{keyword}%'))
        if page and limit:
            statement = statement.offset((page - 1) * limit).limit(limit)
        statement = statement.order_by(UserTable.user_id.desc())
        with session_getter() as session:
            return session.exec(statement).all(), session.scalar(count_statement)

    @classmethod
    def get_unique_user_by_name(cls, user_name: str) -> UserTable | None:
        with session_getter() as session:
            statement = select(UserTable).where(UserTable.user_name == user_name)
            return session.exec(statement).first()

    @classmethod
    def create_user(cls, user_id: str, user_name: str, user_email: str, user_password: str):
        with session_getter() as session:
            session.add(UserTable(user_id=user_id, user_name=user_name,
                                  user_email=user_email, user_password=user_password))
            session.commit()

    @classmethod
    def add_user_and_default_role(cls, user_name: str, user_email: str, user_password: str, user_avatar: str):
        """
        新增用户，并添加默认角色
        用户的ID以此递增
        """
        user_number = len(cls.get_user_number()) + 1
        with session_getter() as session:
            session.add(UserTable(user_id=str(user_number), user_name=user_name, user_avatar=user_avatar,
                                  user_email=user_email, user_password=user_password))
            session.commit()

    @classmethod
    def add_user_and_admin_role(cls, user_id: str, user_name: str,
                                user_email: str, user_password: str, user_avatar: str):
        """
        新增用户，并添加超级管理员角色
        """
        with session_getter() as session:
            session.add(UserTable(user_email=user_email, user_id=user_id, user_avatar=user_avatar,
                                  user_name=user_name, user_password=user_password))
            session.commit()

    @classmethod
    def get_all_users(cls, page: int = 0, limit: int = 0) -> List[UserTable]:
        """
        分页获取所有用户
        """
        statement = select(UserTable)
        if page and limit:
            statement = statement.offset((page - 1) * limit).limit(limit)
        with session_getter() as session:
            return session.exec(statement).all()

    @classmethod
    def get_visible_users(cls):
        with session_getter() as session:
            statement = select(UserTable).where(UserTable.delete == False)
            return session.exec(statement).all()

    @classmethod
    def get_user_number(cls) -> int:
        with session_getter() as session:
            statement = select(UserTable)
            return session.exec(statement).all()

    @classmethod
    def update_user_info(cls, user_id, user_avatar, user_description):
        with session_getter() as session:
            update_values = {}
            if user_avatar:
                update_values["user_avatar"] = user_avatar
            if user_description:
                update_values["user_description"] = user_description
            statement = update(UserTable).where(UserTable.user_id == user_id).values(**update_values)
            session.exec(statement)
            session.commit()