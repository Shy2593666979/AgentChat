# Parallel Search MCP

[Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp) 提供
`web_search` 和 `web_fetch` 两个工具。它已登记在
`src/backend/agentchat/config/mcp_server.json`，服务启动时由
`init_agentchat_system()` 自动加载，无需额外脚本或手动导入。

```json
{
  "server_name": "Parallel 搜索",
  "url": "https://search.parallel.ai/mcp",
  "type": "streamable_http",
  "config": {},
  "params": {},
  "config_enabled": false,
  "logo_url": "https://agentchat.oss-cn-beijing.aliyuncs.com/icons/mcp/mcp.png"
}
```

说明：

- `type` 为 `streamable_http`，由 `convert_mcp_config()` 转成
  `MCPStreamableHttpConfig`，再经 `MCPManager` / `MultiServerMCPClient` 连接。
- 匿名端点免费且无需 API Key，所以 `config` 为空、`config_enabled` 为 `false`
  （用户无需单独配置参数）。匿名访问有速率限制，适合探索和轻量使用；需要更高
  配额时可自行在 `config` 中加入 Parallel API Key 字段并置 `config_enabled`
  为 `true`。
- 登记不等于启用：与其他内置 MCP 服务一样，需要在 Agent 中显式绑定该服务，
  它才会参与对话。不想要它时，从 `mcp_server.json` 删除该条目即可。

## 测试

离线测试用模拟 HTTP MCP 服务校验条目格式与加载流程，不访问网络：

```bash
cd src/backend
python -m unittest agentchat.test.test_parallel_search_mcp
```
