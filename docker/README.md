# 🐳 AgentChat Docker 部署指南

> 🚀 **一键部署 AgentChat** - 完整的容器化解决方案

## 📋 目录

- [🎯 快速开始](#🎯-快速开始)
- [🔧 配置说明](#🔧-配置说明)
- [🏗️ 服务架构](#🏗️-服务架构)
- [📊 服务管理](#📊-服务管理)
- [🐛 故障排除](#🐛-故障排除)
- [📈 性能优化](#📈-性能优化)

---

## 🎯 快速开始

### 📋 系统要求

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **内存**: 最少4GB，推荐8GB+
- **磁盘**: 最少10GB可用空间

### 🚀 一键启动

```bash
# 0️⃣ 配置应用（必须先完成！）
vim src/backend/agentchat/config.yaml
# 修改数据库连接、API密钥等配置

# 1️⃣ 进入docker目录
cd docker

# 2️⃣ 设置执行权限
chmod +x start.sh stop.sh

# 3️⃣ 启动所有服务
./start.sh
```

### 🌐 访问地址

| 🎯 **服务** | 🔗 **地址** | 📝 **说明** |
|:---:|:---:|:---|
| **前端界面** | [localhost:8090](http://localhost:8090) | Vue3 开发服务器 |
| **后端API** | [localhost:7860](http://localhost:7860) | FastAPI 应用服务 |
| **API文档** | [localhost:7860/docs](http://localhost:7860/docs) | Swagger 在线文档 |
| **MySQL** | `localhost:3306` | 数据库服务 |
| **Redis** | `localhost:6379` | 缓存服务 |

---

## 🔧 配置说明

### ⚠️ 重要提示

**AgentChat 使用 `config.yaml` 文件进行配置，而不是环境变量！**

在启动 Docker 容器之前，您必须先修改配置文件：

```bash
# 编辑配置文件（必须在启动前完成）
vim ../src/backend/agentchat/config.yaml
```

### 🤖 必要配置项

打开 `src/backend/agentchat/config.yaml` 并修改以下配置：

#### 1️⃣ 数据库配置（必填）

```yaml
mysql:
  endpoint: "mysql+pymysql://root:your-password@mysql:3306/agentchat"
  async_endpoint: "mysql+aiomysql://root:your-password@mysql:3306/agentchat"

redis:
  endpoint: "redis://redis:6379"
```

> � **注意**：Docker 环境中，主机名使用服务名（`mysql`、`redis`），而不是 `localhost`

#### 2️⃣ AI 模型配置（必填）

```yaml
multi_models:
  # 对话模型
  conversation_model:
    api_key: "your-api-key"
    base_url: "https://api.openai.com/v1"
    model_name: "gpt-4"
  
  # 工具调用模型
  tool_call_model:
    api_key: "your-api-key"
    base_url: "https://api.openai.com/v1"
    model_name: "gpt-4"
  
  # Embedding 模型
  embedding:
    api_key: "your-api-key"
    base_url: "https://api.openai.com/v1"
    model_name: "text-embedding-3-small"
```

#### 3️⃣ 可选配置

```yaml
# RAG 向量数据库（如需使用知识库功能）
rag:
  vector_db:
    host: "your-milvus-host"
    port: "19530"
    mode: "chroma"

# 对象存储（如需文件上传功能）
aliyun_oss:
  access_key_id: "your-access-key"
  access_key_secret: "your-secret"
  endpoint: "oss-cn-beijing.aliyuncs.com"
  bucket_name: "your-bucket"
```

### 🔐 Docker 环境配置注意事项

在 Docker 环境中，请确保：

1. **数据库主机名**：使用 `mysql` 而不是 `localhost`
2. **Redis 主机名**：使用 `redis` 而不是 `localhost`
3. **服务端口**：保持 `config.yaml` 中的端口配置为 `7860`
4. **API 密钥**：填写真实有效的 API 密钥

---

## 🏗️ 服务架构

```mermaid
graph TB
    A[前端 Frontend :8090] --> B[后端 Backend :7860]
    B --> C[MySQL :3306]
    B --> D[Redis :6379]
    
    style A fill:#4FC08D
    style B fill:#009688
    style C fill:#4479A1
    style D fill:#DC382D
```

### 📦 服务详情

| 🏷️ **服务名** | 🐳 **镜像** | 📝 **说明** |
|:---:|:---|:---|
| **frontend** | node:18-alpine | Vue3 + Vite 开发服务器 |
| **backend** | python:3.12-slim | FastAPI + uvicorn 应用 |
| **mysql** | mysql:8.0 | 主数据库 |
| **redis** | redis:7.0-alpine | 缓存和会话存储 |

---

## 📊 服务管理

### 🔍 查看服务状态

```bash
# 查看所有服务状态
docker-compose ps

# 查看服务详细信息
docker-compose ps --format table
```

### 📋 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mysql
docker-compose logs -f redis

# 查看最近100行日志
docker-compose logs --tail=100 backend
```

### 🔄 服务操作

```bash
# 重启特定服务
docker-compose restart backend

# 重新构建并启动
docker-compose up --build -d

# 仅启动数据库服务
docker-compose up -d mysql redis

# 停止所有服务
./stop.sh
```

### 📊 资源监控

```bash
# 查看容器资源使用情况
docker stats

# 查看特定容器统计
docker stats agentchat-backend agentchat-frontend
```

---

## 🐛 故障排除

### ❓ 常见问题

<details>
<summary><b>🔧 服务启动失败</b></summary>

```bash
# 检查日志
docker-compose logs backend

# 检查配置文件
cat docker.env

# 重新构建容器
docker-compose build --no-cache backend
```

</details>

<details>
<summary><b>🔌 端口被占用</b></summary>

```bash
# 查看端口占用
lsof -i :7860
lsof -i :8090

# 修改docker-compose.yml中的端口映射
ports:
  - "17860:7860"  # 改为其他端口
```

</details>

<details>
<summary><b>💾 数据库连接失败</b></summary>

```bash
# 检查MySQL容器状态
docker-compose ps mysql

# 进入MySQL容器
docker-compose exec mysql mysql -u root -p

# 重置数据库
docker-compose down mysql
docker volume rm docker_mysql_data
docker-compose up -d mysql
```

</details>

<details>
<summary><b>🚀 API密钥错误</b></summary>

```bash
# 检查配置文件
cat ../src/backend/agentchat/config.yaml

# 修改配置文件
vim ../src/backend/agentchat/config.yaml

# 重启后端服务使配置生效
docker-compose restart backend
```

</details>

### 🧹 清理和重置

```bash
# 完全清理（包括数据）
./stop.sh  # 选择删除数据

# 仅清理容器和镜像
docker-compose down --rmi all
docker system prune -a

# 重新开始
./start.sh
```

---

## 📈 性能优化

### 🚀 开发环境优化

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  backend:
    volumes:
      - ../src/backend:/app:cached  # 使用cached模式
    environment:
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1

  frontend:
    volumes:
      - ../src/frontend:/app:cached
    command: npm run dev -- --host 0.0.0.0 --port 8090
```

### 🏭 生产环境配置

```bash
# 使用生产配置
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 📊 监控和指标

```bash
# 启用容器监控
docker run -d \
  --name cadvisor \
  -p 8080:8080 \
  -v /:/rootfs:ro \
  -v /var/run:/var/run:ro \
  -v /sys:/sys:ro \
  -v /var/lib/docker/:/var/lib/docker:ro \
  gcr.io/cadvisor/cadvisor:latest
```

---

## 🔧 高级配置

### 🌐 Nginx反向代理

```nginx
# nginx.conf
upstream backend {
    server localhost:7860;
}

upstream frontend {
    server localhost:8090;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 🔒 SSL/TLS配置

```bash
# 使用Let's Encrypt
docker run -it --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/lib/letsencrypt:/var/lib/letsencrypt \
  certbot/certbot certonly --standalone -d your-domain.com
```

---

## 📞 获取帮助

如果遇到问题，请：

1. 🔍 检查 [故障排除](#🐛-故障排除) 部分
2. 📋 查看容器日志：`docker-compose logs -f`
3. 🐛 在GitHub提交Issue
4. 💬 加入我们的社区讨论

---

<div align="center">

**🐳 愉快地使用 Docker 部署 AgentChat！**

*如有问题，请查看日志或联系维护者*

</div>