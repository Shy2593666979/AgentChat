<div align='center'>
    <img src="docs/media/cover.jpg" alt="agentchat: connecting models, knowledge, and tools" width="100%">
</div>

<div align="center">

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/vue-3.4+-4FC08D.svg?style=for-the-badge&logo=vue.js&logoColor=white" alt="Vue Version" />
  <img src="https://img.shields.io/badge/fastapi-0.121+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge" alt="License" />
</p>

<p align="center">
  <b>An agent platform connecting models, knowledge, and tools</b>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#advanced-configuration">Deployment Guide</a> •
  <a href="https://shy2593666979.github.io/agentchat-docs/">Documentation</a> •
  <a href="https://agentchat.cloud">Live Demo</a> •
  <a href="https://github.com/Shy2593666979/agentchat-docs/blob/main/images/README.md">Join WeChat Group</a>
</p>

</div>

---

[简体中文](README.md) · [Changelog](docs/CHANGELOG.md)

## Overview

agentchat is an agent application platform with a Vue frontend and a FastAPI backend. Connect a model service, give agents access to tools, Skills, MCP servers, and knowledge bases, then use those capabilities in conversations. Mars provides a task interface for search, research, and report generation with execution details.

The local setup uses SQLite, an in-process cache, local file storage, and Chroma. Separate MySQL, Redis, MinIO, and Milvus services are optional.

## Capabilities

![agentchat technical architecture](docs/media/architecture.png)

| Capability | What it does |
| --- | --- |
| Flexible conversations | Switch agents within a conversation; asynchronously generate a topic title of 2–10 Chinese characters from the first message |
| Agents | Select a model, edit instructions, and bind tools, MCP servers, Skills, and knowledge bases |
| Mars tasks | Start a task from Explore and inspect tool execution and the resulting Markdown report |
| Tools and MCP | Use built-in tools, import OpenAPI specs, or connect SSE / Streamable HTTP MCP servers; create MCP servers through conversation with human confirmation |
| Skills | Load six templates at startup for research reports, data analysis, product documents, code review, email writing, and knowledge organization |
| Knowledge bases | Upload and index documents for retrieval and reranking, with optional full-text search |
| Resource isolation | New users receive separate copies of default agents, tools, Skills, and MCP servers; edits do not affect other users |
| Usage and logs | Track provider-reported token usage and inspect request, run, and tool logs |
| Streaming | Adapt conversation and task events through the shared AG-UI layer |

Basic chat needs a working chat model. Knowledge retrieval needs suitable embedding and reranking services, and some external tools require separate credentials. A single chat API key does not automatically enable every capability.

This update covers the interface and brand, conversations, user resource isolation, AG-UI, token usage, unified logging, and GitHub CI. See the [changelog](docs/CHANGELOG.md) for details.

## Contents

- [Screenshots and demos](#screenshots-and-demos)
- [Quick start](#quick-start)
- [First use](#first-use)
- [Advanced configuration](#advanced-configuration)
- [Development and checks](#development-and-checks)
- [Documentation](#documentation)
- [License and support](#license-and-support)

## Screenshots and demos

### Explore task demo

Enter a goal on the Explore page to follow task execution and read the full report:

> Compare the influence of China's four great ancient capitals and create a travel guide for these four cities.

https://github.com/user-attachments/assets/640650f3-4134-452a-9d17-6f850dabe95f

Start a task from Explore and follow deep search, source organization, and report generation. The video is edited to show only the application.

### Current interface

#### Dashboard

View model calls, token usage, seven-day trends, and recent activity.

![Dashboard: Mingguang's seven-day demo data](docs/media/dashboard.jpg)

#### Model services

One model from each of six providers illustrates display names, provider icons, and API configuration. The `show_model` display name and the model identifier sent in requests are managed separately.

![Model services: display configurations for six providers](docs/media/models.jpg)

#### Agents and capability management

![Agents: my assistants](docs/media/agents.jpg)

<table>
<tr>
<td width="50%"><b>Tools</b><br>Manage built-in tools and custom capabilities.<br><a href="docs/media/tools.jpg"><img src="docs/media/tools.jpg" alt="Tool management page" width="100%"></a></td>
<td width="50%"><b>Skills</b><br>Organize reusable working knowledge into Skills.<br><a href="docs/media/skills.jpg"><img src="docs/media/skills.jpg" alt="Skill management page" width="100%"></a></td>
</tr>
<tr>
<td width="50%"><b>MCP</b><br>Connect external tools and data services.<br><a href="docs/media/mcp.jpg"><img src="docs/media/mcp.jpg" alt="MCP server management page" width="100%"></a></td>
<td width="50%"><b>Knowledge bases</b><br>Organize knowledge spaces by topic.<br><a href="docs/media/knowledge.jpg"><img src="docs/media/knowledge.jpg" alt="Knowledge base management page" width="100%"></a></td>
</tr>
</table>

<details>
<summary>View the sign-in page</summary>

![agentchat sign-in page](docs/media/login.jpg)

</details>

## Quick start

### 1. Prerequisites

- Git, Python 3.12, and Node.js 22, matching the CI environment.
- [uv](https://docs.astral.sh/uv/getting-started/installation/) for Python environments and locked dependencies.
- A model API key, endpoint, and model identifier. The example below uses [DeepSeek Flash](https://api-docs.deepseek.com/) with the model identifier `deepseek-flash`.

The commands below clone the `main` branch. Confirm that `uv --version` and `node --version` work in your terminal.

### 2. Get the source and install backend dependencies

```bash
git clone --branch main https://github.com/Shy2593666979/AgentChat.git
cd AgentChat/src/backend
uv sync --locked --python 3.12
```

### 3. Create a local configuration

Windows PowerShell:

```powershell
Copy-Item agentchat/config.simple.yaml agentchat/config.local.simple.yaml
```

Linux / macOS:

```bash
cp agentchat/config.simple.yaml agentchat/config.local.simple.yaml
```

Edit the following section in `src/backend/agentchat/config.local.simple.yaml`, retaining the rest of the copied template:

```yaml
multi_models:
  chat_model:
    api_key: "your-deepseek-api-key"
    base_url: "https://api.deepseek.com"
    model_name: "deepseek-flash"
```

Retain the other settings in the copied file. Local files matching `config.local*.yaml` are ignored by Git. This DeepSeek example configures chat; knowledge retrieval requires separately configured embedding and reranking services, rather than reusing the DeepSeek key. See the [model configuration guide](docs/simple-config.md#模型继承与能力边界).

### 4. Run the backend

Keep this terminal in `src/backend` and leave the server running.

Windows PowerShell:

```powershell
$env:AGENTCHAT_CONFIG = "agentchat/config.local.simple.yaml"
uv run --locked uvicorn agentchat.main:app --host 127.0.0.1 --port 7860
```

Linux / macOS:

```bash
export AGENTCHAT_CONFIG=agentchat/config.local.simple.yaml
uv run --locked uvicorn agentchat.main:app --host 127.0.0.1 --port 7860
```

[Health check](http://127.0.0.1:7860/health) should return `{"status":"OK"}`. [Swagger UI](http://127.0.0.1:7860/docs) documents the API. The health check confirms server startup; send a message to verify your model credentials.

### 5. Run the frontend

Open another terminal at the repository root:

```bash
cd src/frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 8090 --strictPort
```

Visit [http://127.0.0.1:8090](http://127.0.0.1:8090). The development server proxies `/api` to the backend on port `7860`.

For a different backend address, set `VITE_API_BASE_URL=http://your-backend:port` in `src/frontend/.env.local` and restart the frontend. Keep backend command-line ports, YAML server settings, and uploaded-file URLs consistent. See the [configuration guide](docs/simple-config.md).

## First use

1. **Register and sign in**: Your account receives its own default agents, tools, Skills, and MCP servers. Create knowledge bases when needed.
2. **Check the model setup**: The YAML `chat_model` configures the system default model. Models added on the model page can be selected by agents. Display names and provider model identifiers are separate fields; use the identifier required by the provider for actual requests.
3. **Start a conversation**: Select an agent and send a message. You can switch agents within the conversation. A topic title is generated in the background and can be renamed manually.
4. **Add capabilities**: Bind tools, Skills, MCP servers, or knowledge bases in the agent editor. A listed MCP server is not automatically bound to the current agent. Confirm external credentials and connectivity before calling it.
5. **Use documents and tasks**: Upload documents and wait for processing before using a knowledge base. Start search and research tasks from Explore. Knowledge retrieval depends on embedding and reranking models; tasks depend on the configuration of the tools they use.
6. **Inspect usage**: View model calls and token usage on the dashboard. Statistics depend on the usage information returned by the provider and may be incomplete when it is missing.

## Advanced configuration

Simple mode uses the same YAML structure as the full configuration, filling omitted settings with defaults.

| Requirement | Setting |
| --- | --- |
| SQLite or MySQL | `database.url`; sync and async drivers are derived automatically |
| Redis | `redis.endpoint`; leave it empty for a local in-process cache |
| Local files, MinIO, or OSS | `storage.mode` and the selected storage configuration |
| Separate models | `multi_models.chat_model`, `tool_call_model`, `reasoning_model`, `embedding`, `rerank`, and other model entries |
| Vector store and full-text search | `rag.vector_db`, `rag.enable_elasticsearch`, and the relevant connection settings |
| Default MCP / Skill templates | `agentchat/config/mcp_server.json`, `agentchat/config/default_skills.json`, and `config/skills/` |
| Logging | `log_level` and the `AGENTCHAT_LOG_DIR` environment variable |

Configuration precedence is: explicit loader path → `AGENTCHAT_CONFIG` → `agentchat/config.local.yaml` → `agentchat/config.yaml`. Select `config.local.simple.yaml` explicitly and restart the backend after changes.

The existing [Docker files](docker/) describe a development stack with MySQL, Redis, MinIO, and the frontend development server. They are separate from this lightweight local setup. Container addresses, configuration, and persistence need to be checked for that stack; a full container startup was not validated as part of this documentation update.

## Development and checks

In `src/backend`:

```bash
uv sync --locked --group dev
uv run --locked pytest tests -q
```

In `src/frontend`:

```bash
npm ci
npm run lint
npm run build
node --test tests/mars-task.test.cjs
```

Install frontend dependencies to enable the backend's cross-language AG-UI checks. Scripts requiring external services remain under `src/backend/tests/manual` and are excluded from default collection.

[GitHub CI](.github/workflows/ci.yml) runs backend tests and frontend type checks and builds on pushes to `main`, pull requests, or manual dispatch. It uses temporary configuration and databases, without real model keys. Building the frontend generates static files; it does not deploy the application.

## Documentation

The detailed guides below are currently in Chinese:

- [Backend architecture and troubleshooting](src/backend/README.md)
- [Simple configuration and local data](docs/simple-config.md)
- [Flexible conversations](docs/flexible-conversations.md)
- [Private user resources](docs/private-resources.md)
- [Default Skills](docs/default-skills.md)
- [Default MCP servers](docs/mcp-defaults.md) · [Parallel Search](docs/reference/parallel_search_mcp.md)
- [AG-UI protocol](docs/ag-ui.md)
- [Conversation token usage](docs/conversation-token-usage.md)
- [Logging](docs/logging.md)
- [Tests](src/backend/tests/README.md)
- [Changelog](docs/CHANGELOG.md)

## License and support

This project is licensed under the [MIT License](LICENSE).

<div align="center">

## Thank You for Supporting AgentChat!

### If this project has been helpful to you, please give us a Star

*Help more people discover this project and build the future of AI together!*

*Made with love by the AgentChat Author MingGuang Tian*

<picture>
  <source
    media="(prefers-color-scheme: dark)"
    srcset="
      https://star-history.dera.page/svg?repos=Shy2593666979/AgentChat&type=Date&theme=dark
    "
  />
  <source
    media="(prefers-color-scheme: light)"
    srcset="
      https://star-history.dera.page/svg?repos=Shy2593666979/AgentChat&type=Date
    "
  />
  <img
    alt="Star History Chart"
    src="https://star-history.dera.page/svg?repos=Shy2593666979/AgentChat&type=Date"
  />
</picture>

</div>
