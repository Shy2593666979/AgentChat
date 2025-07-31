# 🐍 Python 3.12+ 基础镜像
FROM python:3.12-slim as backend-base

# 📦 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 🔧 设置工作目录
WORKDIR /app

# 📋 复制Python依赖文件
COPY requirements.txt .

# 🚀 安装Python依赖（使用pip镜像源加速）
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/


# ⚠️ 修复 fastapi-jwt-auth 与 Pydantic 2 的兼容性问题
COPY scripts/fix_fastapi_jwt_auth.py /scripts/
RUN python /scripts/fix_fastapi_jwt_auth.py

# 📁 复制后端代码
COPY src/backend/ .

# 🌍 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 🚀 暴露端口
EXPOSE 7860

# 🏃‍♂️ 启动后端服务
CMD ["uvicorn", "agentchat.main:app", "--host", "0.0.0.0", "--port", "7860"]

# ⚠️ 修复 fastapi-jwt-auth 与 Pydantic 2 的兼容性问题
# 创建修复后的配置文件
#RUN cat > /tmp/fastapi_jwt_auth_config.py << 'EOF'
#from datetime import timedelta
#from typing import Optional, Union, Sequence, List
#from pydantic import (
#    BaseModel,
#    validator,
#    StrictBool,
#    StrictInt,
#    StrictStr
#)
#
#class LoadConfig(BaseModel):
#    authjwt_token_location: Optional[List[StrictStr]] = ['headers']
#    authjwt_secret_key: Optional[StrictStr] = None
#    authjwt_public_key: Optional[StrictStr] = None
#    authjwt_private_key: Optional[StrictStr] = None
#    authjwt_algorithm: Optional[StrictStr] = "HS256"
#    authjwt_decode_algorithms: Optional[List[StrictStr]] = None
#    authjwt_decode_leeway: Optional[Union[StrictInt,timedelta]] = 0
#    authjwt_encode_issuer: Optional[StrictStr] = None
#    authjwt_decode_issuer: Optional[StrictStr] = None
#    authjwt_decode_audience: Optional[Union[StrictStr,Sequence[StrictStr]]] = None
#    authjwt_denylist_enabled: Optional[StrictBool] = False
#    authjwt_denylist_token_checks: Optional[List[StrictStr]] = ['access','refresh']
#    authjwt_header_name: Optional[StrictStr] = "Authorization"
#    authjwt_header_type: Optional[StrictStr] = "Bearer"
#    authjwt_access_token_expires: Optional[Union[StrictBool,StrictInt,timedelta]] = timedelta(minutes=15)
#    authjwt_refresh_token_expires: Optional[Union[StrictBool,StrictInt,timedelta]] = timedelta(days=30)
#    # # option for create cookies
#    authjwt_access_cookie_key: Optional[StrictStr] = "access_token_cookie"
#    authjwt_refresh_cookie_key: Optional[StrictStr] = "refresh_token_cookie"
#    authjwt_access_cookie_path: Optional[StrictStr] = "/"
#    authjwt_refresh_cookie_path: Optional[StrictStr] = "/"
#    authjwt_cookie_max_age: Optional[StrictInt] = None
#    authjwt_cookie_domain: Optional[StrictStr] = None
#    authjwt_cookie_secure: Optional[StrictBool] = False
#    authjwt_cookie_samesite: Optional[StrictStr] = None
#    # # option for double submit csrf protection
#    authjwt_cookie_csrf_protect: Optional[StrictBool] = True
#    authjwt_access_csrf_cookie_key: Optional[StrictStr] = "csrf_access_token"
#    authjwt_refresh_csrf_cookie_key: Optional[StrictStr] = "csrf_refresh_token"
#    authjwt_access_csrf_cookie_path: Optional[StrictStr] = "/"
#    authjwt_refresh_csrf_cookie_path: Optional[StrictStr] = "/"
#    authjwt_access_csrf_header_name: Optional[StrictStr] = "X-CSRF-Token"
#    authjwt_refresh_csrf_header_name: Optional[StrictStr] = "X-CSRF-Token"
#    authjwt_csrf_methods: Optional[List[StrictStr]] = ['POST','PUT','PATCH','DELETE']
#
#    @validator('authjwt_access_token_expires')
#    def validate_access_token_expires(cls, v):
#        if v is True:
#            raise ValueError("The 'authjwt_access_token_expires' only accept value False (bool)")
#        return v
#
#    @validator('authjwt_refresh_token_expires')
#    def validate_refresh_token_expires(cls, v):
#        if v is True:
#            raise ValueError("The 'authjwt_refresh_token_expires' only accept value False (bool)")
#        return v
#
#    @validator('authjwt_denylist_token_checks', each_item=True)
#    def validate_denylist_token_checks(cls, v):
#        if v not in ['access','refresh']:
#            raise ValueError("The 'authjwt_denylist_token_checks' must be between 'access' or 'refresh'")
#        return v
#
#    @validator('authjwt_token_location', each_item=True)
#    def validate_token_location(cls, v):
#        if v not in ['headers','cookies']:
#            raise ValueError("The 'authjwt_token_location' must be between 'headers' or 'cookies'")
#        return v
#
#    @validator('authjwt_cookie_samesite')
#    def validate_cookie_samesite(cls, v):
#        if v not in ['strict','lax','none']:
#            raise ValueError("The 'authjwt_cookie_samesite' must be between 'strict', 'lax', 'none'")
#        return v
#
#    @validator('authjwt_csrf_methods', each_item=True)
#    def validate_csrf_methods(cls, v):
#        if v.upper() not in ["GET", "HEAD", "POST", "PUT", "DELETE", "PATCH"]:
#            raise ValueError("The 'authjwt_csrf_methods' must be between http request methods")
#        return v.upper()
#
#    class Config:
#        str_min_length = 1
#        str_strip_whitespace = True
#EOF
#
## 替换原始配置文件 - 通过pydantic路径定位
#RUN SITE_PACKAGES=$(python -c "import pydantic; from pathlib import Path; print(Path(pydantic.__file__).parent.parent)") && \
#    cp /tmp/fastapi_jwt_auth_config.py "$SITE_PACKAGES/fastapi_jwt_auth/config.py" && \
#    rm /tmp/fastapi_jwt_auth_config.py

