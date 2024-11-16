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
from loguru import logger
from service.user import get_user_jwt
from utils.constants import USER_CURRENT_SESSION

router = APIRouter()

@router.post('/user/regist', description='注册用户')
async def regist(*, user: UserCreate):
    if userConfig.USE_CAPTCHA:
        if not user.captcha_key or not await verify_captcha(user.captcha, user.captcha_key):
            raise HTTPException(status_code=500, detail='验证码错误')

    db_user = User.model_validate(user)

    exist_user = UserDao.get_user_by_username(db_user.user_name)
    if exist_user:
        raise HTTPException(status_code=500, detail='用户名重复')
    if len(db_user.user_name) > 20:
        raise HTTPException(status_code=500, detail='用户名长度不应该超过20')
    try:
        db_user.password = UserService.decrypt_md5_password(user.password)
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

@router.post('/user/login', description='用户登录')
async def login(*, request: Request, user: UserLogin, Authorize: AuthJWT = Depends()):
    # 验证码校验
    if userConfig.USE_CAPTCHA:
        if not user.captcha_key or not await verify_captcha(user.captcha, user.captcha_key):
            raise HTTPException(status_code=500, detail='验证码错误')

    password = UserService.decrypt_md5_password(user.password)

    db_user = UserDao.get_user_by_username(user.user_name)
    # 检查密码
    if not db_user or not db_user.password:
        return UserValidateError.return_resp()

    if 1 == db_user.delete:
        raise HTTPException(status_code=500, detail='该账号已被禁用，请联系管理员')

    # if db_user.password and db_user.password != password:
    #     # 判断是否需要记录错误次数
    #     if not password_conf.login_error_time_window or not password_conf.max_error_times:
    #         return UserValidateError.return_resp()
    #     # 错误次数加1
    #     error_key = get_error_password_key(user.user_name)
    #     error_num = redis_client.incr(error_key)
    #     if error_num == 1:
    #         # 首次设置key的过期时间
    #         redis_client.expire_key(error_key, password_conf.login_error_time_window * 60)
    #     if error_num and int(error_num) >= password_conf.max_error_times:
    #         # 错误次数到达上限，封禁账号
    #         db_user.delete = 1
    #         UserDao.update_user(db_user)
    #         raise HTTPException(status_code=500, detail='由于登录失败次数过多，该账号被自动禁用，请联系管理员处理')
    #     return UserValidateError.return_resp()

    # 判断下密码是否长期未修改
    # if db_user.password and password_conf.password_valid_period and password_conf.password_valid_period > 0:
    #     if (datetime.now() - db_user.password_update_time).days >= password_conf.password_valid_period:
    #         return UserPasswordExpireError.return_resp()

    access_token, refresh_token, role, web_menu = get_user_jwt(db_user)

    # Set the JWT cookies in the response
    Authorize.set_access_cookies(access_token)
    Authorize.set_refresh_cookies(refresh_token)

    # 设置登录用户当前的cookie, 比jwt有效期多一个小时
    redis_client.set(USER_CURRENT_SESSION.format(db_user.user_id), access_token, ACCESS_TOKEN_EXPIRE_TIME + 3600)

    return resp_200(UserRead(role=str(role), web_menu=web_menu, access_token=access_token, **db_user.__dict__))
