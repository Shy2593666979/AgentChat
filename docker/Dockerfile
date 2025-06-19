# 使用官方运行时作为镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# requirements.txt 复制到工作目录
COPY ../requirement.txt .

# 安装python 依赖
RUN pip install -r requirement.txt

COPY ../src/backend .

# 运行 
CMD [ "python", "main.py"]
