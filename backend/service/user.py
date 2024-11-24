import json

import rsa
import hashlib
from fastapi_jwt_auth import AuthJWT
from cache.redis import redis_client
from database.dao.user_role import UserRoleDao
from database.models.role import AdminRole
from errcode.user import UserNameAlreadyExistError, UserLoginOfflineError
from utils.hash import md5_hash
from base64 import b64decode
from fastapi import Request, HTTPException, Depends
from database.models.user import UserTable
from database.dao.user import UserDao
from utils.constants import RSA_KEY, USER_CURRENT_SESSION
from type.schemas import CreateUserReq
from utils.JWT import ACCESS_TOKEN_EXPIRE_TIME

class UserPayload:

    def __init__(self, **kwargs):
        self.user_id = kwargs.get('user_id')
        self.user_role = kwargs.get('role')
        if self.user_role != 'admin':  # 非管理员用户，需要获取他的角色列表
            roles = UserRoleDao.get_user_roles(self.user_id)
            self.user_role = [one.role_id for one in roles]
        self.user_name = kwargs.get('user_name')

    def is_admin(self):
        if self.user_role == 'admin':
            return True
        if isinstance(self.user_role, list):
            for one in self.user_role:
                if one == AdminRole:
                    return True
        return False

class UserService:

    # MD5算法加密
    @classmethod
    def decrypt_md5_password(cls, password: str):
        if value := redis_client.get(RSA_KEY):
            private_key = value[1]
            password = md5_hash(rsa.decrypt(b64decode(password), private_key).decode('utf-8'))
        else:
            password = md5_hash(password)
        return password

    # 使用SHA-256算法进行加密
    @classmethod
    def encrypt_sha256_password(cls, password: str):
        sha256 = hashlib.sha256()
        sha256.update(password.encode('utf-8'))
        encrypted_password = sha256.hexdigest()
        return encrypted_password

    # 验证密码是否匹配
    @classmethod
    def verify_password(cls, password: str, encrypted_password: str):
        return cls.encrypt_sha256_password(password) == encrypted_password

    @classmethod
    def create_user(cls, request: Request, login_user: UserPayload, req_data: CreateUserReq):
        """
        创建用户
        """
        exists_user = UserDao.get_user_by_username(req_data.user_name)
        if exists_user:
            # 抛出异常
            raise UserNameAlreadyExistError.http_exception()
        user = UserTable(
            user_name=req_data.user_name,
            user_password=cls.decrypt_md5_password(req_data.password),
        )
        user = UserDao.add_user_and_default_role(user_name=user.user_name,
                                                 user_password=user.user_password)
        return user

async def get_login_user(authorize: AuthJWT = Depends()) -> UserPayload:
    """
    获取当前登录的用户
    """
    # 校验是否过期，过期则直接返回http 状态码的 401
    authorize.jwt_required()

    current_user = json.loads(authorize.get_jwt_subject())
    user = UserPayload(**current_user)

    return user

def get_user_role(db_user: UserTable):
    # 查询用户的角色列表
    db_user_role = UserRoleDao.get_user_roles(db_user.user_id)
    role = ""
    role_ids = []
    for user_role in db_user_role:
        if user_role.role_id == '1':
            # 是管理员，忽略其他的角色
            role = 'admin'
        else:
            role_ids.append(user_role.role_id)
    if role != "admin":
        role = role_ids

    return role

def get_user_jwt(db_user: UserTable):
    # 查询角色
    role = get_user_role(db_user)
    # 生成JWT令牌
    payload = {'user_name': db_user.user_name, 'user_id': db_user.user_id, 'role': role}

    access_token = AuthJWT().create_access_token(subject=json.dumps(payload), expires_time=ACCESS_TOKEN_EXPIRE_TIME)

    refresh_token = AuthJWT().create_refresh_token(subject=db_user.user_name)

    # Set the JWT cookies in the response
    return access_token, refresh_token, role