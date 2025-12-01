# 数据库表结构技术文档

## 概述

本文档详细描述了 AgentChat 系统的数据库表结构设计。系统采用 MySQL 数据库，使用 SQLModel 作为 ORM 框架，支持用户管理、智能体配置、对话管理、知识库管理等核心功能。

## 数据库配置

- **数据库名称**: `agentchat`
- **默认用户**: `agentchat_user`
- **连接地址**: `mysql://agentchat_user:123456@mysql:3306/agentchat`

## 表结构详细说明

### 1. 用户管理相关表

#### 1.1 用户表 (user)

存储系统用户的基本信息。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| user_id | VARCHAR | PRIMARY KEY | 用户唯一标识 |
| user_name | VARCHAR | UNIQUE, INDEX | 用户名 |
| user_email | VARCHAR | | 用户邮箱 |
| user_avatar | VARCHAR | | 用户头像URL |
| user_description | VARCHAR | DEFAULT: "该用户很懒，没有留下一片云彩" | 用户描述 |
| user_password | VARCHAR | | 加密后的用户密码 |
| delete | BOOLEAN | DEFAULT: FALSE | 是否删除标记 |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**特殊用户类型**:
- SystemUser = '0' (系统用户)
- AdminUser = '1' (管理员用户)

#### 1.2 角色表 (role)

定义系统中的用户角色。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 角色ID |
| role_name | VARCHAR | UNIQUE | 角色名称 |
| remark | VARCHAR | | 角色备注 |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**预定义角色**:
- SystemRole = '0' (系统管理员)
- AdminRole = '1' (超级管理员)
- DefaultRole = '2' (普通用户)

#### 1.3 用户角色关联表 (user_role)

管理用户与角色的多对多关系。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | VARCHAR | PRIMARY KEY | 关联记录ID |
| user_id | VARCHAR | INDEX | 用户ID |
| role_id | VARCHAR | INDEX | 角色ID |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

### 2. 智能体管理相关表

#### 2.1 智能体表 (agent)

存储智能体的配置信息。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | VARCHAR | PRIMARY KEY | 智能体ID (UUID) |
| name | VARCHAR | | 智能体名称 |
| description | VARCHAR | | 智能体描述 |
| logo_url | VARCHAR | | 智能体Logo URL |
| user_id | VARCHAR | INDEX | 创建用户ID |
| is_custom | BOOLEAN | DEFAULT: TRUE | 是否为用户自定义 |
| system_prompt | TEXT | | 系统提示词 |
| llm_id | VARCHAR | | 绑定的LLM模型ID |
| enable_memory | BOOLEAN | DEFAULT: TRUE | 是否开启记忆功能 |
| mcp_ids | JSON | | 绑定的MCP Server ID列表 |
| tool_ids | JSON | | 绑定的工具ID列表 |
| knowledge_ids | JSON | | 绑定的知识库ID列表 |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

#### 2.2 MCP智能体表 (mcp_agent)

专门用于MCP (Model Context Protocol) 智能体的配置。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| mcp_agent_id | VARCHAR | PRIMARY KEY | MCP智能体ID |
| mcp_server_id | JSON | | 绑定的MCP Server ID |
| name | VARCHAR | | MCP智能体名称 |
| description | VARCHAR | | 描述信息 |
| logo_url | VARCHAR | DEFAULT: 'img/mcp_openai/mcp_agent.png' | Logo URL |
| user_id | VARCHAR | INDEX | 创建用户ID |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

### 3. 对话管理相关表

#### 3.1 对话表 (dialog)

存储用户与智能体的对话会话信息。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| dialog_id | VARCHAR | PRIMARY KEY | 对话ID (UUID) |
| name | VARCHAR | | 对话名称 |
| agent_id | VARCHAR | | 绑定的智能体ID |
| agent_type | VARCHAR | DEFAULT: "Agent" | 智能体类型 (Agent/MCPAgent) |
| user_id | VARCHAR | | 用户ID |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

#### 3.2 历史消息表 (history)

存储对话中的具体消息内容。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | VARCHAR | PRIMARY KEY | 消息ID (UUID) |
| content | TEXT | | 消息内容 |
| dialog_id | VARCHAR | | 所属对话ID |
| role | VARCHAR | | 消息角色 (assistant/system/user) |
| events | JSON | | AI回复事件信息 |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

#### 3.3 工作台会话表 (workspace_session)

管理工作台的会话信息。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| session_id | VARCHAR | PRIMARY KEY | 会话ID (UUID) |
| title | VARCHAR | | 会话标题 |
| agent | VARCHAR | | 使用的智能体 |
| user_id | VARCHAR | | 用户ID |
| contexts | JSON | | 结构化对话上下文 |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

### 4. 消息反馈相关表

#### 4.1 消息点赞表 (message_like)

存储用户对消息的点赞记录。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | VARCHAR | PRIMARY KEY | 记录ID (UUID) |
| user_input | TEXT | | 用户输入内容 |
| agent_output | TEXT | | 智能体输出内容 |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

#### 4.2 消息踩表 (message_down)

存储用户对消息的踩记录。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | VARCHAR | PRIMARY KEY | 记录ID (UUID) |
| user_input | TEXT | | 用户输入内容 |
| agent_output | TEXT | | 智能体输出内容 |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

### 5. 知识库管理相关表

#### 5.1 知识库表 (knowledge)

存储知识库的基本信息。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | VARCHAR | PRIMARY KEY | 知识库ID (格式: t_xxxxxxxxxxxxxxxx) |
| name | VARCHAR(128) | UNIQUE, INDEX | 知识库名称 |
| description | VARCHAR(1024) | | 知识库描述 |
| user_id | VARCHAR(128) | INDEX | 创建用户ID |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

#### 5.2 知识库文件表 (knowledge_file)

存储知识库中的文件信息。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | VARCHAR | PRIMARY KEY | 文件ID (UUID) |
| file_name | VARCHAR | INDEX | 文件名称 |
| knowledge_id | VARCHAR | INDEX | 所属知识库ID |
| status | VARCHAR | DEFAULT: "success" | 文件解析状态 (fail/process/success) |
| user_id | VARCHAR | INDEX | 用户ID |
| oss_url | VARCHAR | | OSS存储路径 |
| file_size | INT | DEFAULT: 0 | 文件大小(字节) |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

### 6. 模型管理相关表

#### 6.1 大语言模型表 (llm)

存储大语言模型的配置信息。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| llm_id | VARCHAR | PRIMARY KEY | 模型ID (UUID) |
| llm_type | VARCHAR | DEFAULT: 'LLM' | 模型类型 (LLM/Embedding/Rerank) |
| model | VARCHAR | | 模型名称 |
| base_url | VARCHAR | | 模型API地址 |
| api_key | VARCHAR | | API密钥 |
| provider | VARCHAR | | 模型提供商 |
| user_id | VARCHAR | | 创建用户ID |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

### 7. 工具管理相关表

#### 7.1 工具表 (tool)

存储系统中可用的工具信息。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| tool_id | VARCHAR | PRIMARY KEY | 工具ID (UUID) |
| zh_name | VARCHAR | | 工具中文名称 |
| en_name | VARCHAR | | 工具英文名称 |
| user_id | VARCHAR | | 创建用户ID |
| logo_url | VARCHAR | | 工具Logo URL |
| description | TEXT | | 工具描述 |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

### 8. MCP服务器管理相关表

#### 8.1 MCP服务器表 (mcp_server)

存储MCP服务器的配置信息。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| mcp_server_id | VARCHAR | PRIMARY KEY | MCP服务器ID (UUID) |
| server_name | VARCHAR | | 服务器名称 |
| user_id | VARCHAR | | 创建用户ID |
| user_name | VARCHAR | | 创建用户名称 |
| description | VARCHAR | | 服务器描述 |
| mcp_as_tool_name | VARCHAR | | 作为工具时的名称 |
| url | VARCHAR | | 连接地址 |
| type | VARCHAR(255) | | 连接类型 (sse/websocket/stdio) |
| logo_url | VARCHAR | | Logo URL |
| config | JSON | | 配置信息 |
| tools | JSON | | 工具列表 |
| params | JSON | | 输入参数 |
| config_enabled | BOOLEAN | DEFAULT: FALSE | 是否需要用户配置 |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

#### 8.2 MCP Stdio服务器表 (mcp_stdio_server)

存储MCP Stdio服务器的特殊配置。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| mcp_server_id | VARCHAR | PRIMARY KEY | 服务器ID (UUID) |
| mcp_server_path | VARCHAR | | 脚本路径 |
| mcp_server_command | VARCHAR | | 执行命令 |
| mcp_server_env | VARCHAR | | 环境变量 |
| user_id | VARCHAR | | 创建用户ID |
| name | VARCHAR | DEFAULT: "MCP Server" | 服务器名称 |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |

#### 8.3 MCP用户配置表 (mcp_user_config)

存储用户与MCP服务器的绑定配置。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | VARCHAR | PRIMARY KEY | 配置ID (UUID) |
| mcp_server_id | VARCHAR | | MCP服务器ID |
| user_id | VARCHAR | | 用户ID |
| config | JSON | | 鉴权配置信息 |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |
| update_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

### 9. 统计和记录相关表

#### 9.1 使用统计表 (usage_stats)

记录智能体和模型的使用统计信息。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | VARCHAR | PRIMARY KEY | 统计记录ID (UUID) |
| agent | VARCHAR | | 智能体名称 |
| model | VARCHAR | | 模型名称 |
| user_id | VARCHAR | | 用户ID |
| input_tokens | INT | DEFAULT: 0 | 输入Token数量 |
| output_tokens | INT | DEFAULT: 0 | 输出Token数量 |
| create_time | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |

#### 9.2 记忆历史表 (memory_history)

记录智能体记忆的变更历史。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | VARCHAR | PRIMARY KEY | 记录ID (UUID) |
| memory_id | VARCHAR | | 记忆ID |
| old_memory | TEXT | | 旧记忆内容 |
| new_memory | TEXT | | 新记忆内容 |
| event | VARCHAR | | 事件类型 |
| actor_id | VARCHAR | | 操作者ID |
| role | VARCHAR | | 角色 |
| is_deleted | BOOLEAN | DEFAULT: FALSE | 是否删除 |
| created_at | DATETIME | DEFAULT: CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT: CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

## 数据库设计特点

### 1. 统一的基础模型
所有表都继承自 `SQLModelSerializable` 基类，提供统一的序列化和时间戳管理功能。

### 2. UUID主键策略
大部分表使用UUID作为主键，确保分布式环境下的唯一性。

### 3. 软删除支持
部分表支持软删除机制，通过 `delete` 或 `is_deleted` 字段标记。

### 4. JSON字段使用
广泛使用JSON字段存储复杂的配置信息和列表数据，提高灵活性。

### 5. 时间戳自动管理
所有表都包含 `create_time` 和 `update_time` 字段，由数据库自动维护。

## 索引策略

- 用户相关字段 (`user_id`) 建立索引
- 关联字段 (`dialog_id`, `knowledge_id` 等) 建立索引
- 唯一性约束字段 (`user_name`, `knowledge.name`) 建立唯一索引

## 数据完整性

- 外键关系通过应用层维护
- 必填字段使用 NOT NULL 约束
- 枚举值通过应用层验证
- 字符串长度限制防止数据溢出

---

*文档版本: 1.0*  
*最后更新: 2024年11月*  
*维护者: AgentChat 开发团队*