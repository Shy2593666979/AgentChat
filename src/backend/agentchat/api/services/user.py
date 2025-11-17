import json
import random

import rsa
import hashlib
from fastapi_jwt_auth import AuthJWT

from agentchat.services.aliyun_oss import aliyun_oss
from agentchat.services.redis import redis_client
from agentchat.database.dao.user_role import UserRoleDao
from agentchat.database.models.role import AdminRole
from agentchat.api.errcode.user import UserNameAlreadyExistError
from agentchat.settings import app_settings
from agentchat.utils.hash import md5_hash
from base64 import b64decode
from fastapi import Request, Depends, HTTPException
from agentchat.database.models.user import UserTable
from agentchat.database.dao.user import UserDao
from agentchat.utils.constants import RSA_KEY
from agentchat.schema.schemas import CreateUserReq
from agentchat.utils.JWT import ACCESS_TOKEN_EXPIRE_TIME

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

    @classmethod
    def get_random_user_avatar(cls):
        files_url = aliyun_oss.list_files_in_folder("icons/user")
        avatars_url = []
        for file_url in files_url:
            avatars_url.append(f"{app_settings.aliyun_oss['base_url']}/{file_url}")
        return random.choice(avatars_url) if avatars_url else ""

    @classmethod
    def get_available_avatars(cls):
        files_url = aliyun_oss.list_files_in_folder("icons/user")
        avatars_url = []
        for file_url in files_url:
            avatars_url.append(f"{app_settings.aliyun_oss['base_url']}/{file_url}")
        return avatars_url

    @classmethod
    def get_user_info_by_id(cls, user_id):
        user_info = UserDao.get_user(user_id)
        return user_info.to_dict()

    @classmethod
    def update_user_info(cls, user_id, user_avatar, user_description):
        UserDao.update_user_info(user_id, user_avatar, user_description)

    @classmethod
    def get_user_id_by_name(cls, user_name):
        user = UserDao.get_user_by_username(user_name)
        return user.user_id

async def get_login_user(request: Request, authorize: AuthJWT = Depends()) -> UserPayload:
    """
    获取当前登录的用户
    """
    if request.state.is_whitelisted:
        # 白名单路径：直接返回Admin
        return UserPayload(user_id="1", user_name="Admin")

    # 非白名单路径：执行 JWT 验证
    try:
        authorize.jwt_required()
        current_user = json.loads(authorize.get_jwt_subject())
        return UserPayload(**current_user)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

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