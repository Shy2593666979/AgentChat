from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Depends, Body
from fastapi_jwt_auth import AuthJWT

from cache.redis import redis_client
from database.dao.user import UserDao
from errcode.user import UserPasswordExpireError, UserValidateError
from type.schemas import resp_200
from utils.JWT import ACCESS_TOKEN_EXPIRE_TIME
from service.user import  UserService
from database.models.user import UserTable, AdminUser
from type.schemas import UnifiedResponseModel
from loguru import logger
from service.user import get_user_jwt
from utils.constants import USER_CURRENT_SESSION

router = APIRouter()

@router.post('/user/register', response_model=UnifiedResponseModel)
async def register(user_name: str = Body(description='用户名'),
                   user_email: Optional[str] = Body(description='用户邮箱'),
                   user_password: str = Body(description='用户密码')):
    # 验证码校验
    # if userConfig.USE_CAPTCHA:
    #     if not user.captcha_key or not await verify_captcha(user.captcha, user.captcha_key):
    #         raise HTTPException(status_code=500, detail='验证码错误')


    exist_user = UserDao.get_user_by_username(user_name)
    if exist_user:
        raise HTTPException(status_code=500, detail='用户名重复')
    if len(user_name) > 20:
        raise HTTPException(status_code=500, detail='用户名长度不应该超过20')
    try:
        user_password = UserService.encrypt_sha256_password(user_password)
        admin = UserDao.get_user(AdminUser)
        if admin:
            UserDao.add_user_and_default_role(user_name, user_email, user_password)
        else:
            user_id = AdminUser
            UserDao.add_user_and_admin_role(user_id, user_name, user_email, user_password)
    except Exception as e:
        logger.error(f'register user is appear error: {e}')
        raise HTTPException(status_code=500, detail=f'register user is appear error: {e}')
    return resp_200()

@router.post('/user/login', response_model=UnifiedResponseModel)
async def login(user_name: str = Body(description='用户名'),
                user_password: str = Body(description='用户密码'),
                Authorize: AuthJWT = Depends()):
    # 验证码校验
    # if userConfig.USE_CAPTCHA:
    #     if not user.captcha_key or not await verify_captcha(user.captcha, user.captcha_key):
    #         raise HTTPException(status_code=500, detail='验证码错误')

    db_user = UserDao.get_user_by_username(user_name)[0]
    # 检查密码
    if not db_user or not UserService.verify_password(user_password, db_user.user_password):
        return UserValidateError.return_resp()

    if db_user.delete:
        raise HTTPException(status_code=500, detail='该账号已被禁用，请联系管理员')

    access_token, refresh_token, role = get_user_jwt(db_user)

    # Set the JWT cookies in the response
    Authorize.set_access_cookies(access_token)
    Authorize.set_refresh_cookies(refresh_token)

    # 设置登录用户当前的cookie, 比jwt有效期多一个小时
    redis_client.set(USER_CURRENT_SESSION.format(db_user.user_id), access_token, ACCESS_TOKEN_EXPIRE_TIME + 3600)

    return resp_200(data={'user_id': db_user.user_id, 'access_token': access_token})
