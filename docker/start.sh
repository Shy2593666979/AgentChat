#!/bin/bash

# 🚀 AgentChat Docker 启动脚本
# 快速启动所有服务

set -e

echo "🐳 启动 AgentChat Docker 服务..."

# 检查环境变量配置文件
if [ ! -f "docker.env" ]; then
    echo "⚠️  环境变量文件不存在，正在创建..."
    cp docker.env.example docker.env
    echo "📝 请编辑 docker/docker.env 文件，填入你的API密钥"
    echo "然后重新运行此脚本"
    exit 1
fi

# 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p ../data
mkdir -p ../logs
mkdir -p ./mysql/init

# 构建并启动服务
echo "🔨 构建并启动所有服务..."
docker-compose --env-file docker.env up --build -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

echo ""
echo "✅ AgentChat 启动完成！"
echo ""
echo "🌐 访问地址："
echo "  前端界面: http://localhost:8090"
echo "  后端API:  http://localhost:7860"
echo "  API文档:  http://localhost:7860/docs"
echo ""
echo "🔍 查看日志："
echo "  所有服务: docker-compose logs -f"
echo "  后端日志: docker-compose logs -f backend"
echo "  前端日志: docker-compose logs -f frontend"
echo ""
echo "🛑 停止服务："
echo "  docker-compose down"
echo ""