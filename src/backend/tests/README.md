# 后端测试

在 `src/backend` 目录运行自动化测试：

```powershell
uv sync --locked --group dev
uv run --locked pytest tests -q
```

GitHub Actions 的 `CI` 工作流会在推送 `main`、提交 PR 或手动触发时运行后端测试和前端类型检查、构建。后端使用临时 SQLite、占位模型 Key 与本地存储，无需配置 Secrets；同时安装前端依赖，执行 Python 与前端之间的协议测试。

根目录保存可自动收集的回归测试。原 `agentchat/test` 中的 Parallel MCP、Lark 参数测试已移至这里，并更新配置和模块路径。

Lark 参数测试依赖飞书 MCP 的独立依赖 `lark_oapi`，未安装时跳过。

`manual/` 保存原目录中的调试脚本、MCP 辅助模块和 A2A 示例。它们可能需要外部服务、额外依赖、凭据或本地文件，部分脚本导入即执行，因此默认 pytest 不收集该目录。运行前检查脚本配置，例如：

```powershell
.venv\Scripts\python.exe -m tests.manual.test_a2a.main
```

本次仅整理目录和更新相关路径，未逐一修复历史调试脚本的旧接口或依赖。
