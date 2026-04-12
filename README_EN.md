<div align='center'>
    <img src="https://github.com/user-attachments/assets/eb9b3b09-e2bf-4c9d-95a0-5c2d9712723d" alt="alt text" width="70%">
</div>

<div align="center">

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/vue-3.4+-4FC08D.svg?style=for-the-badge&logo=vue.js&logoColor=white" alt="Vue Version" />
  <img src="https://img.shields.io/badge/fastapi-0.115+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge" alt="License" />
</p>

<p align="center">
  <b>A Modern Intelligent Conversation System Based on Large Language Models</b>
</p>

<p align="center">
  <a href="https://shy2593666979.github.io/agentchat-docs/%E5%BF%AB%E9%80%9F%E5%85%A5%E9%97%A8.html">Quick Start</a> •
  <a href="https://shy2593666979.github.io/agentchat-docs/%E5%BC%80%E5%8F%91%E6%8C%87%E5%8D%97/%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA.html">Deployment Guide</a> •
  <a href="https://shy2593666979.github.io/agentchat-docs/">Documentation</a> •
  <a href="https://agentchat.cloud">Live Demo</a> •
  <a href="https://github.com/Shy2593666979/agentchat-docs/blob/main/images/README.md">Join WeChat Group</a>
</p>

</div>

---

## Latest Changelog (2026-4-12)

### 1. HITL-based Conversational MCP Server Generation from OpenAPI

- Supports conversational MCP Server generation from OpenAPI specs using a Human-In-The-Loop mechanism.
- Key decision nodes during MCP Server generation support human intervention and confirmation, enabling dynamic configuration and real-time interaction.
- Improves server generation flexibility and system controllability, allowing users to retain full initiative within automated workflows.

### 2. Optimized Conversation Context Management
Refactored the context management strategy, upgrading from a simple "last 5 turns" approach to an intelligent three-layer memory architecture:
- Short-Term Memory: retains conversation content within the most recent 3000 tokens to ensure immediate context continuity
- History Summarization: automatically summarizes historical conversations exceeding 3000 tokens and extracts key information
- Long-Term Memory: persistently records user preferences, habits, and important information for a personalized conversation experience

### 3. Dependency Conflict Fixes
Resolved multiple dependency version conflicts, particularly compatibility issues among core libraries such as Pydantic, LangChain, and FastAPI, improving system stability.

### 4. Improved First-Launch Experience
Fixed errors caused by missing model configuration on first launch. Added configuration validation and friendly prompts to guide users through initial setup, lowering the barrier to entry.

---

<details>
<summary><b>Previous Changelog (2026-3-8)</b></summary>

### 1. MinIO Local Object Storage Support
Now supports both OSS and MinIO as object storage options. Reference: [Install MinIO on Windows](docs/development/install_minio_win.md). Thanks to the contributors who raised Issues:
- @xiaoyan011016
- @shenmi888

### 2. Optimized Docker Deployment
(1) Fixed the network connectivity issue where agentchat-frontend could not reach agentchat-backend in previous Docker deployments.
(2) Added a one-click deployment script for Windows (start_win.bat).

### 3. Custom Tool Support
Previously clicking custom tools had no effect. Now you can build your own tools by uploading a Swagger/OpenAPI spec.

### 4. Skill Support
Now supports creating Skills bound to agents, using progressive Prompt loading to teach the model how to perform tasks.

### 5. UI Style Improvements
The system settings page was blank in previous versions. This has been fixed.

</details>

---

## Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. Feature Showcase](#2-feature-showcase)
- [3. Important Version Notes](#3-important-version-notes)
- [4. Features](#4-features)
- [5. Tech Stack](#5-tech-stack)
- [6. Quick Start](#6-quick-start)
- [7. Advanced Deployment Guide](#7-advanced-deployment-guide)
- [8. Documentation](#8-documentation)
- [9. License](#9-license)

---

## 1. Project Overview

AgentChat is a modern intelligent conversation system built on large language models, offering rich AI conversation capabilities. The system adopts a frontend-backend separated architecture and supports multiple AI models, knowledge base retrieval, tool calling, MCP server integration, and other advanced features.

<div align="center">
<img width="800" height="400" src="https://github.com/user-attachments/assets/f35e8a9a-0905-46a2-a167-a3c8e876760a" />
</div>

### 1. Core Highlights

- Intelligent Agent: Supports Sub-Agents collaboration with reasoning and decision-making capabilities
- Knowledge Base Retrieval: RAG technology for accurate knowledge retrieval and Q&A
- Tool Ecosystem: Built-in practical tools with support for custom extensions
- MCP Integration: Supports Model Context Protocol servers
- Modern UI: Beautiful interface based on Vue 3 and Element Plus
- Three-Layer Memory: Short-term context retention, automatic history summarization, long-term user preference recording
- HITL Generation: Conversational MCP Server generation based on HITL, with human intervention at key nodes

---

## 2. Feature Showcase

<div align="center">

### 1. Human-In-The-Loop (HITL)
Conversational MCP Server generation from API information using the Human-In-The-Loop mechanism
<img width="800" height="450" src="https://github.com/user-attachments/assets/cabb59d8-0e14-432a-9aee-aa9115e266cd" />

### 2. New Workspace
Added workspace feature; users can freely switch between workspace and app center
<img width="800" height="450" src="https://github.com/user-attachments/assets/766c7628-2256-4c8b-a838-c400eaa78d6b" />

### 3. LingXun Task Planning
Real-time task flowchart for a more intuitive experience
<img width="800" height="450" src="https://github.com/user-attachments/assets/53f7fe9f-d70d-4cc2-bf7e-b47a712a6d7a" />

### 4. Data Dashboard
Filter call counts and token usage by Agent, model, and time range
<img width="800" height="450" src="https://github.com/user-attachments/assets/b0cb4ccf-b868-4f1b-9b26-8a882d8130da" />

### 5. Platform Homepage
Clean and modern main interface with intuitive navigation
<img width="800" height="450" src="https://github.com/user-attachments/assets/dc626494-4797-4a86-b350-3a0759d52d64" />

</div>

### 6. Intelligent Agent Demo

<table>
<tr>
<td width="50%">

#### Weather Query Agent
Real-time weather information query and forecast
<img width="400" height="240" src="https://github.com/user-attachments/assets/91a95c2b-f194-4c25-ba0f-f8cb393cba50" />

</td>
<td width="50%">

#### Text-to-Image Agent
AI-driven image generation service
<img width="400" height="240" src="https://github.com/user-attachments/assets/58194798-5c3e-4d7d-895c-944b6665e5a6" />

</td>
</tr>
</table>

### 7. Multi-turn Tool Calling

The platform supports multi-turn tool calling for agents (Tool C depends on the result of Tool B, which depends on the result of Tool A, so the calling order is A --> B --> C)
<div align="center">
<img width="800" height="450" src="https://github.com/user-attachments/assets/029c70ce-e5fa-4f2c-926a-a5dfd719e237" />
</div>

---

## 3. Important Version Notes

Starting from AgentChat v2.2.0, LangChain has been upgraded to version 1.0.

<div align="center">

| Version | LangChain Version | Compatibility | Notes |
|:---:|:---:|:---:|:---|
| v2.1.x and below | 0.x | Legacy | Uses old LangChain API |
| v2.2.0+ | 1.0+ | Latest | Major update, significant API changes |

</div>

1. LangChain 1.0 introduces breaking API changes.
2. Some tool and Agent configuration methods have been updated.
3. It is recommended to review the migration guide for detailed changes.

---

## 4. Features

### 1. Core Modules

- AI Conversation Engine: Multi-model ecosystem, streaming responses, context memory, reasoning visualization.
- Intelligent Agent System: Multi-agent collaboration, task automation, workflow orchestration, goal-oriented execution.
- Knowledge Base System: Multi-format support, semantic chunking, vector retrieval, RAG-based Q&A.
- Tool Ecosystem: 10+ built-in tools, supports custom upload and extension.

### 2. Advanced Features

- MCP Server: Full protocol support, dynamic loading at runtime.
- User Management: Secure authentication, fine-grained permission control, personalized configuration.
- System Architecture: Frontend-backend separation, Docker deployment, async high-performance processing.

---

## 5. Tech Stack

- Backend: FastAPI, Python 3.12+, LangChain, MySQL, Redis, ChromaDB.
- Frontend: Vue 3.4+, Element Plus, Pinia, Vite 5, TypeScript.
- Deployment: Docker, Docker Compose, Poetry, npm.

---

## 6. Quick Start

### 1. System Requirements

- Python 3.12+
- Node.js 18+
- MySQL 8.0+, Redis 7.0+
- Docker 20.10+

### 2. Docker One-Click Deployment

```bash
# 1. Clone the project
git clone https://github.com/Shy2593666979/AgentChat.git
cd AgentChat

# 2. Edit the configuration file
vim docker/docker_config.yaml

# 3. Start
cd docker
docker-compose up --build -d
```

### 3. Local Deployment

Clone the project
```bash
git clone https://github.com/Shy2593666979/AgentChat.git

cd AgentChat
```

Start the backend service
```bash
cd src/backend

# Install dependencies
1. pip install -r requirements.txt

# Or use uv (recommended)
1. pip install uv
2. uv sync
```

Start the frontend service
```bash
cd src/frontend

# Install dependencies
npm install
npm run dev
```

---

## 7. Advanced Deployment Guide

The system supports configuration of multiple vector databases (Milvus/ChromaDB) and search engines (Elasticsearch). Please refer to the deployment documentation for details.

---

## 8. Documentation

- API Documentation: [AgentChat Document](docs/reference/agentchat.md)
- Development Guide: Start the backend and visit /docs to view the Swagger documentation.

---

## 9. License

This project is licensed under the **[MIT License](LICENSE)**

*This means you are free to use, modify, and distribute this project*

---

## 10. Thank You for Supporting AgentChat

<div align="center">

## Thank You for Supporting AgentChat!

### If this project has been helpful to you, please give us a Star

*Help more people discover this project and build the future of AI together!*

*Made with love by the AgentChat Author MingGuang Tian*

<picture>
  <source
    media="(prefers-color-scheme: dark)"
    srcset="
      https://api.star-history.com/svg?repos=Shy2593666979/AgentChat&type=Date&theme=dark
    "
  />
  <source
    media="(prefers-color-scheme: light)"
    srcset="
      https://api.star-history.com/svg?repos=Shy2593666979/AgentChat&type=Date
    "
  />
  <img
    alt="Star History Chart"
    src="https://api.star-history.com/svg?repos=Shy2593666979/AgentChat&type=Date"
  />
</picture>

</div>
