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


#⚠️修复 fastapi-jwt-auth 与 Pydantic 2 的兼容性问题
#❗目前文件已重写放到backend文件夹可正常导入
# COPY scripts/fix_fastapi_jwt_auth.py /scripts/
# RUN python /scripts/fix_fastapi_jwt_auth.py

# 📁 复制后端代码
COPY src/backend/ .

# 🌍 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 🚀 暴露端口
EXPOSE 7860

# 🏃‍♂️ 启动后端服务
CMD ["uvicorn", "agentchat.main:app", "--host", "0.0.0.0", "--port", "7860"]
