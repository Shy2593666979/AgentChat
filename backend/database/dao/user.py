from database.models.user import UserBase, User
from database.models.role import DefaultRole, AdminRole
from database.models.user_role import UserRole
from typing import List
from sqlalchemy import select, func
from sqlmodel import Session
from database import engine

class UserDao(UserBase):

    @classmethod
    def get_user(cls, user_id: int) -> User | None:
        with Session(engine) as session:
            statement = select(User).where(User.user_id == user_id)
            return session.exec(statement).first()

    @classmethod
    def get_user_by_ids(cls, user_ids: List[int]) -> List[User] | None:
        with Session(engine) as session:
            statement = select(User).where(User.user_id.in_(user_ids))
            return session.exec(statement).all()

    @classmethod
    def get_user_by_username(cls, username: str) -> User | None:
        with Session(engine) as session:
            statement = select(User).where(User.user_name == username)
            return session.exec(statement).first()

    @classmethod
    def update_user(cls, user: User) -> User:
        with Session(engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    @classmethod
    def filter_users(cls, user_ids: List[int], keyword: str = None, page: int = 0, limit: int = 0) -> (List[User], int):
        statement = select(User)
        count_statement = select(func.count(User.user_id))
        if user_ids:
            statement = statement.where(User.user_id.in_(user_ids))
            count_statement = count_statement.where(User.user_id.in_(user_ids))
        if keyword:
            statement = statement.where(User.user_name.like(f'%{keyword}%'))
            count_statement = count_statement.where(User.user_name.like(f'%{keyword}%'))
        if page and limit:
            statement = statement.offset((page - 1) * limit).limit(limit)
        statement = statement.order_by(User.user_id.desc())
        with Session(engine) as session:
            return session.exec(statement).all(), session.scalar(count_statement)

    @classmethod
    def get_unique_user_by_name(cls, user_name: str) -> User | None:
        with Session(engine) as session:
            statement = select(User).where(User.user_name == user_name)
            return session.exec(statement).first()

    @classmethod
    def create_user(cls, db_user: User) -> User:
        with Session(engine) as session:
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            return db_user

    @classmethod
    def add_user_and_default_role(cls, user: User) -> User:
        """
        新增用户，并添加默认角色
        """
        with Session(engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            db_user_role = UserRole(user_id=user.user_id, role_id=DefaultRole)
            session.add(db_user_role)
            session.commit()
            session.refresh(user)
            return user

    @classmethod
    def add_user_and_admin_role(cls, user: User) -> User:
        """
        新增用户，并添加超级管理员角色
        """
        with Session(engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            db_user_role = UserRole(user_id=user.user_id, role_id=AdminRole)
            session.add(db_user_role)
            session.commit()
            session.refresh(user)
            return user

    @classmethod
    def get_all_users(cls, page: int = 0, limit: int = 0) -> List[User]:
        """
        分页获取所有用户
        """
        statement = select(User)
        if page and limit:
            statement = statement.offset((page - 1) * limit).limit(limit)
        with Session(engine) as session:
            return session.exec(statement).all()
