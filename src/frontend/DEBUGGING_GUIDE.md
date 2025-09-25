# 智能体API调试指南

## 问题描述
GET `/api/v1/agent` 接口无法获取到智能体数据

## 调试步骤

### 1. 检查后端服务
```bash
# 确保后端服务正在运行
cd src/backend
python -m agentchat.main
# 或者根据你的启动方式
```

后端应该运行在 `http://localhost:7860`

### 2. 检查前端开发服务器
```bash
cd src/frontend
npm run dev
```

前端应该运行在 `http://127.0.0.1:8090`

### 3. 检查代理配置
在 `vite.config.ts` 中确认代理设置：
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:7860/',
    changeOrigin: true,
  }
}
```

### 4. 检查认证状态
打开浏览器开发者工具，检查：
- localStorage中是否有 `token`
- 如果没有token，需要先登录

### 5. 手动测试API
使用curl或Postman测试：
```bash
# 不带认证的测试
curl -X GET http://localhost:7860/api/v1/agent

# 带认证的测试（替换YOUR_TOKEN）
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:7860/api/v1/agent
```

### 6. 检查数据库
确保数据库中有智能体数据：
- 检查 `agent` 表是否存在
- 检查是否有数据记录

### 7. 查看后端日志
检查后端控制台输出，查看是否有错误信息

## 常见错误及解决方案

### 401 Unauthorized
- 原因：token无效或未提供
- 解决：重新登录获取有效token

### 404 Not Found
- 原因：API路径错误或后端服务未启动
- 解决：检查后端服务和路由配置

### CORS错误
- 原因：跨域请求被阻止
- 解决：检查后端CORS配置

### 500 Internal Server Error
- 原因：后端代码错误或数据库问题
- 解决：查看后端日志，检查数据库连接

## 调试工具

1. 使用创建的 `AgentDebug.vue` 页面进行测试
2. 浏览器开发者工具 -> Network 标签查看请求
3. 浏览器开发者工具 -> Console 查看前端错误

## API响应格式
正常响应应该是：
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "agent_id": "xxx",
      "name": "智能体名称",
      "description": "描述",
      "logo_url": "图标URL",
      "tool_ids": [],
      "llm_id": "模型ID",
      "mcp_ids": [],
      "system_prompt": "系统提示词",
      "knowledge_ids": [],
      "enable_memory": false
    }
  ]
}
``` 