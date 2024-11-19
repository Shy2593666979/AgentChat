from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi_jwt_auth import AuthJWT

from cache.redis import redis_client
from database.models.user import UserCreate, UserLogin, UserRead
from database.dao.user import UserDao
from config.user_config import userConfig
from errcode.user import UserPasswordExpireError, UserValidateError
from type.schemas import resp_200
from utils.JWT import ACCESS_TOKEN_EXPIRE_TIME
from utils.captcha import verify_captcha
from service.user import  UserService
from database.models.user import User
from type.schemas import UnifiedResponseModel
from loguru import logger
from service.user import get_user_jwt
from utils.constants import USER_CURRENT_SESSION

router = APIRouter()

@router.post('/user/regist', response_model=UnifiedResponseModel)
async def regist(*, user: UserCreate):
    # 验证码校验
    # if userConfig.USE_CAPTCHA:
    #     if not user.captcha_key or not await verify_captcha(user.captcha, user.captcha_key):
    #         raise HTTPException(status_code=500, detail='验证码错误')

    db_user = User.model_validate(user)

    exist_user = UserDao.get_user_by_username(db_user.user_name)
    if exist_user:
        raise HTTPException(status_code=500, detail='用户名重复')
    if len(db_user.user_name) > 20:
        raise HTTPException(status_code=500, detail='用户名长度不应该超过20')
    try:
        db_user.password = UserService.encrypt_sha256_password(user.password)
        admin = UserDao.get_user(1)
        if admin:
            UserDao.add_user_and_default_role(db_user)
        else:
            db_user.user_id = 1
            UserDao.add_user_and_admin_role(db_user)
    except Exception as e:
        logger.error(f'register user is appear error: {e}')
        raise HTTPException(status_code=500, detail=f'register user is appear error: {e}')
    return resp_200(data=db_user)

@router.post('/user/login', response_model=UnifiedResponseModel)
async def login(*, request: Request, user: UserLogin, Authorize: AuthJWT = Depends()):
    # 验证码校验
    # if userConfig.USE_CAPTCHA:
    #     if not user.captcha_key or not await verify_captcha(user.captcha, user.captcha_key):
    #         raise HTTPException(status_code=500, detail='验证码错误')

    db_user = UserDao.get_user_by_username(user.user_name)
    # 检查密码
    if not db_user or not UserService.verify_password(user.password, db_user.password):
        return UserValidateError.return_resp()

    if 1 == db_user.delete:
        raise HTTPException(status_code=500, detail='该账号已被禁用，请联系管理员')

    access_token, refresh_token, role = get_user_jwt(db_user)

    # Set the JWT cookies in the response
    Authorize.set_access_cookies(access_token)
    Authorize.set_refresh_cookies(refresh_token)

    # 设置登录用户当前的cookie, 比jwt有效期多一个小时
    redis_client.set(USER_CURRENT_SESSION.format(db_user.user_id), access_token, ACCESS_TOKEN_EXPIRE_TIME + 3600)

    return resp_200(UserRead(role=str(role), access_token=access_token, **db_user.__dict__))
