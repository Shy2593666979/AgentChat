# 🐍 Python 3.12+ 基础镜像
FROM python:3.12-slim as backend-base

# 📦 安装系统依赖
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    wget \
    unzip \
    pandoc \
    texlive-xetex \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libnss3 \
    libxss1 \
    libgbm1 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libdrm2 \
    libxdamage1 \
    libxrandr2 \
    libxcomposite1 \
    libxcursor1 \
    libxi6 \
    libxtst6 \
    libglib2.0-0 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*


# -----------------------------
# 安装 Chrome
# -----------------------------
RUN wget https://storage.googleapis.com/chrome-for-testing-public/138.0.7204.183/linux64/chrome-linux64.zip \
    && unzip chrome-linux64.zip \
    && mv chrome-linux64 /opt/chrome \
    && ln -s /opt/chrome/chrome /usr/bin/google-chrome \
    && rm chrome-linux64.zip


# -----------------------------
# 安装 ChromeDriver
# -----------------------------
RUN wget https://storage.googleapis.com/chrome-for-testing-public/138.0.7204.183/linux64/chromedriver-linux64.zip \
    && unzip chromedriver-linux64.zip \
    && mv chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm -rf chromedriver-linux64*

# 🔧 设置工作目录
WORKDIR /app

# 📋 复制Python依赖文件
COPY requirements.txt .

# 🚀 安装Python依赖（使用pip镜像源加速）
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/



# 📁 复制后端代码
COPY src/backend/ .

# 📄 用 docker 配置覆盖默认配置
COPY docker/docker_config.yaml /app/agentchat/config.yaml

# 🌍 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 🚀 暴露端口
EXPOSE 7860

# 🏃‍♂️ 启动后端服务
CMD ["uvicorn", "agentchat.main:app", "--host", "0.0.0.0", "--port", "7860"]
