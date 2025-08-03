#!/bin/bash

# 🛑 AgentChat Docker 停止脚本
# 停止并清理所有服务

set -e

echo "🛑 停止 AgentChat Docker 服务..."

# 停止所有服务
echo "🔻 停止所有容器..."
docker-compose down

# 询问是否删除数据
read -p "🗑️  是否删除所有数据（包括数据库）？[y/N]: " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 清理数据卷..."
    docker-compose down -v
    
    echo "🗑️  删除构建缓存..."
    docker system prune -f
    
    echo "✅ 数据已清理完成"
else
    echo "💾 数据已保留"
fi

echo ""
echo "✅ AgentChat 已停止！"
echo ""
echo "🔄 重新启动："
echo "  ./start.sh"
echo ""