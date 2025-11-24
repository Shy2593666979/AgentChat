# 🚀 AgentChat 快速启动指南

本指南将帮助你使用自动化脚本一键启动 AgentChat 的前后端服务。

## 📋 前置要求

在运行脚本之前，请确保你的电脑上已经安装并配置好了以下环境：

1.  **Python** (建议 3.12+)
2.  **Node.js & npm** (用于运行前端)
3.  **虚拟环境** (推荐): 建议在 Conda 或 Python venv 虚拟环境中运行。

## 📂 目录结构检查

为了确保脚本能正常工作，请确认你的项目目录结构如下所示：

```text
AgentChat/             (项目根目录)
├── requestment.txt    <-- Python依赖文件 (跟 src 并列)
├── scripts/
│   └── start.py       <-- 启动脚本在这里
└── src/
    ├── backend/       <-- 后端代码目录 (包含 agentchat/main.py)
    └── frontend/      <-- 前端代码目录 (包含 package.json)

## ⚡️ 如何运行

### 1. 激活环境
在终端（VS Code, PowerShell, 或 CMD）中，先激活你的 Python 虚拟环境。
*(如果你已经在 `(py-langchain1.0)` 这种环境下，请跳过此步)*

### 2. 执行启动脚本
确保你当前处于项目根目录（例如 `AgentChat`），然后运行以下命令：

```bash
python scripts/start.py
```

### 3. 脚本运行流程
脚本会自动执行以下操作：
1.  **自动定位**：识别项目根目录和 `/src` 目录。
2.  **安装依赖**：自动在根目录下查找 `requestment.txt` (或 `request*.txt`) 并执行安装。
3.  **启动后端**：进入 `src/backend`，在端口 `7860` 启动 Uvicorn 服务。
4.  **启动前端**：进入 `src/frontend`，执行 `npm run dev` 启动前端页面。
5.  **日志展示**：前后端的日志会实时打印在同一个终端窗口中。

## 🛑 如何停止

*   在终端窗口中按下 **`Ctrl + C`**。
*   脚本会自动清理并关闭后台运行的前端和后端进程。

---

## ❓ 常见问题

**Q: 提示 `npm` 不是内部或外部命令？**
A: 请检查是否安装了 Node.js，并将其添加到了系统环境变量中。

**Q: 依赖安装失败？**
A: 请检查根目录下是否存在 `requestment.txt` 文件，且内容格式正确。
