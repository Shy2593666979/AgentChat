# MCP 服务器集合

本目录包含了多个 MCP（Model Context Protocol）服务器实现，这些服务器仅作为参考示例放置在本项目中，可以独立启动和运行。

## 📁 目录结构

```
mcp_servers/
├── lark_mcp/          # 飞书 MCP 服务器
├── weather/           # 天气查询 MCP 服务器  
├── arxiv/             # arXiv 论文搜索 MCP 服务器
└── README.md          # 本文件
```

## 🚀 服务器说明

### 1. Lark MCP 服务器 (lark_mcp/)

提供完整的飞书 API 集成功能，包括：

- **日历管理** - 创建、删除、更新日历，预定会议
- **日历事件** - 管理日历事件和参会人员
- **聊天管理** - 群聊成员管理
- **文档操作** - 创建和获取文档数据
- **文件夹管理** - 创建文件夹，列出文件
- **消息发送** - 发送消息到群聊或个人
- **用户信息** - 获取用户详细信息

**启动方式：**
```bash
# 方式1：使用 uvicorn 启动 (推荐)
cd src/backend/agentchat/mcp_servers
uvicorn lark_mcp.main:app --host 0.0.0.0 --port 8000

# 方式2：直接运行（stdio 模式）
cd src/backend/agentchat/mcp_servers/lark_mcp
python main.py --transport stdio

# 方式3：SSE 模式
cd src/backend/agentchat/mcp_servers/lark_mcp
python main.py --transport sse
```

### 2. Weather MCP 服务器 (weather/)

提供天气查询功能。

**功能特性：**
- 根据地理位置查询当前天气
- 支持全球主要城市天气查询

**环境配置：**
需要在 `.env` 文件中配置：
```env
weather_api_key=your_weather_api_key
weather_endpoint=your_weather_api_endpoint
```

**启动方式：**
```bash
cd src/backend/agentchat/mcp_servers/weather
python mcp_weather.py
```

### 3. arXiv MCP 服务器 (arxiv/)

提供 arXiv 学术论文搜索功能。

**功能特性：**
- 搜索 arXiv 数据库中的学术论文
- 返回相关论文的详细信息

**启动方式：**
```bash
cd src/backend/agentchat/mcp_servers/arxiv
python mcp_arxiv.py
```

## 📋 使用说明

### 前置依赖

确保已安装以下 Python 包：
```bash
pip install fastmcp
pip install starlette
pip install langchain-community
pip install python-dotenv
pip install requests
```

### 启动流程

1. **进入服务器目录**
   ```bash
   cd src/backend/agentchat/mcp_servers
   ```

2. **选择要启动的服务器**
   - 对于 Lark MCP：`uvicorn lark_mcp.main:app --host 0.0.0.0 --port 8000`
   - 对于 Weather MCP：`python weather/mcp_weather.py`
   - 对于 arXiv MCP：`python arxiv/mcp_arxiv.py`

3. **配置环境变量**（如果需要）
   - Weather 服务器需要配置天气 API 密钥
   - Lark 服务器需要配置飞书应用密钥

### 健康检查

Lark MCP 服务器提供健康检查端点：
```bash
curl http://localhost:8000/health
```

## ⚠️ 注意事项

1. **独立运行** - 这些 MCP 服务器是独立的应用程序，不依赖主项目运行
2. **端口配置** - 确保启动端口没有被其他服务占用
3. **API 密钥** - 某些服务器需要配置第三方 API 密钥才能正常工作
4. **网络连接** - Weather 和 arXiv 服务器需要互联网连接

## 🔧 开发说明

这些 MCP 服务器基于 FastMCP 框架开发，支持多种传输协议：
- **stdio** - 标准输入输出模式
- **sse** - Server-Sent Events 模式  
- **streamable-http** - HTTP 流模式

可以根据具体的集成需求选择合适的传输方式。

## 📖 更多信息

- [MCP 协议文档](https://modelcontextprotocol.io/)
- [FastMCP 框架](https://github.com/jlowin/fastmcp)
- 各服务器的详细 API 文档请参考对应目录下的文档文件
