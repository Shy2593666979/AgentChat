# AgentChat API文档

本文档总结了Agentchat API（V2025.630版本），该文档为管理对话，代理，工具，大语言模型（LLMS），知识库和MCP服务器提供了端点。所有端点返回JSON的回复，成功的回复（200）通常遵循`UnifiedResponseModel`模式和验证错误（422）返回`HTTPValidationError`.

---

## 聊天端点

### 聊天
- **POST/API/V1/CHAT **
  - **摘要**：启动对话。
  - **描述**：发送用户输入以开始或继续对话ID确定的对话。
  - **请求身体**：`ConversationReq`
    - `user_input`（字符串，必需）：用户查询。
    - `dialog_id`（字符串，必需）：对话框ID。
    - `file_url`（字符串，可选）：上传文件的URL。
  - **响应**：
    - 200：成功的回应。
    - 422：验证错误。

### MCP聊天
- **POST /api/v1/mcp_chat **
  - **摘要**：与MCP代理进行对话。
  - **描述**：发送用户输入与对话框ID标识的MCP代理进行交互。
  - **请求身体**：`Body_chat_api_v1_mcp_chat_post`
    - `user_input`（字符串，必需）：用户查询。
    - `dialog_id`（字符串，必需）：对话框ID。
  - **响应**：
    - 200：成功的回应。
    - 422：验证错误。

---

## 对话管理

### 获取对话列表
- **GET /api/v1/dialog/list **
  - **摘要**：检索对话列表。
  - **响应**：
    - 200：回报`UnifiedResponseModel`带有对话列表。
    - 422：验证错误。

### 创建对话框
- **POST /api/v1/对话框**
  - **摘要**：创建一个新的对话框。
  - **请求身体**：`DialogCreateRequest`
    - `name`（字符串，必需）：对话名称。
    - `agent_id`（字符串，必需）：代理ID。
    - `agent_type`（字符串，默认值：“代理”）：代理类型（“ McPagent”或“ Agent”）。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 删除对话框
- **删除/api/v1/对话框**
  - **摘要**：删除对话框。
  - **请求身体**：`Body_delete_dialog_api_v1_dialog_delete`
    - `dialog_id`（字符串，必需）：对话框ID。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 获取对话历史记录
- **POST /api/v1/历史**
  - **摘要**：检索对话的对话历史记录。
  - **请求身体**：`Body_get_dialog_history_api_v1_history_post`
    - `dialog_id`（字符串，必需）：对话框ID。
  - **响应**：
    - 200：回报`UnifiedResponseModel`与历史。
    - 422：验证错误。

---

## 代理管理

### 获取代理
- **GET /api/v1/agent **
  - **摘要**：检索代理详细信息。
  - **响应**：
    - 200：回报`UnifiedResponseModel`使用代理数据。
    - 422：验证错误。

### 创建代理
- **POST/API/V1/AGENT **
  - **摘要**：创建一个新代理。
  - **请求身体**：`CreateAgentRequest`
    - `name`（字符串，必需）：代理名称。
    - `description`（字符串，必需）：代理说明。
    - `tool_ids`（字符串数组，默认值：[]）：工具ID。
    - `llm_id`（字符串，可选）：LLM ID。
    - `mcp_ids`（字符串数组，默认值：[]）：MCP服务器ID。
    - `knowledge_ids`（字符串数组，默认值：[]）：知识基础ID。
    - `use_embedding`（布尔值，默认值：true）：使用嵌入。
    - `system_prompt`（字符串，必需）：系统提示。
    - `logo_url`（字符串，必需）：徽标URL。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 更新代理
- **PUT /api/v1/agent **
  - **摘要**：更新现有代理。
  - **请求身体**：`UpdateAgentRequest`
    - `agent_id`（字符串，必需）：代理ID。
    - `name`, `description`, `tool_ids`, `knowledge_ids`, `mcp_ids`, `llm_id`, `use_embedding`, `logo_url`, `system_prompt`（可选）：更新的字段。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 删除代理
- **删除/api/v1/agent **
  - **摘要**：删除代理。
  - **请求身体**：`Body_delete_agent_api_v1_agent_delete`
    - `agent_id`（字符串，必需）：代理ID。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 搜索代理
- **POST /api/v1/agent/搜索**
  - **摘要**：按名称搜索代理。
  - **请求身体**：`Body_search_agent_api_v1_agent_search_post`
    - `name`（字符串，必需）：要搜索的代理名称。
  - **响应**：
    - 200：回报`UnifiedResponseModel`与匹配代理。
    - 422：验证错误。

---

## MCP代理管理

### 获取MCP代理
- **GET /api/v1/mcp_agent **
  - **摘要**：检索MCP代理详细信息。
  - **响应**：
    - 200：回报`UnifiedResponseModel`使用MCP代理数据。
    - 422：验证错误。

### 创建MCP代理
- **POST /api/v1/mcp_agent **
  - **摘要**：创建一个新的MCP代理。
  - **请求身体**：`Body_create_mcp_agent_api_v1_mcp_agent_post`
    - `name`（字符串，必需）：代理名称。
    - `description`（字符串，必需）：代理说明。
    - `mcp_servers_id`（字符串数组，默认值：[]）：MCP服务器ID。
    - `llm_id`（字符串）：LLM ID。
    - `knowledges_id`（字符串数组，默认值：[]）：知识基础ID。
    - `use_embedding`（布尔值，默认值：true）：使用嵌入。
    - `logoFile`（二进制，可选）：徽标文件。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 更新MCP代理
- **PUT /api/v1/mcp_agent **
  - **摘要**：更新现有的MCP代理。
  - **请求身体**：`Body_update_mcp_agent_api_v1_mcp_agent_put`
    - `agent_id`（字符串，必需）：代理ID。
    - `name`, `description`, `mcp_servers_id`, `knowledges_id`, `llm_id`, `use_embedding`, `logoFile`（可选）：更新的字段。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 删除MCP代理
- **删除/api/v1/mcp_agent **
  - **摘要**：删除MCP代理。
  - **请求身体**：`Body_delete_mcp_agent_api_v1_mcp_agent_delete`
    - `agent_id`（字符串，必需）：代理ID。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 搜索MCP代理
- **POST /api/v1/mcp_agent/search**
  - **摘要**：按名称搜索MCP代理。
  - **请求身体**：`Body_search_mcp_agent_api_v1_mcp_agent_search_post`
    - `name`（字符串，必需）：要搜索的代理名称。
  - **响应**：
    - 200：回报`UnifiedResponseModel`与匹配的MCP代理商。
    - 422：验证错误。

---

## 工具管理

### 创建工具
- **POST/API/V1/tool/create**
  - **摘要**：创建一个新工具。
  - **请求身体**：`ToolCreateRequest`
    - `zh_name`（弦，必需，2-10个字符）：中文名称。
    - `en_name`（字符串，必需，2-10个字符）：英文名称。
    - `description`（字符串，必需，最大300个字符）：工具说明。
    - `logo_url`（字符串，必需）：徽标URL。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 获取所有工具
- **GET /api/v1/tool/all**
  - **摘要**：检索所有工具。
  - **响应**：
    - 200：回报`UnifiedResponseModel`使用工具列表。
    - 422：验证错误。

### 获取个人工具
- **POST /api/v1/tool/own**
  - **摘要**：检索用户拥有的工具。
  - **响应**：
    - 200：回报`UnifiedResponseModel`使用个人工具。
    - 422：验证错误。

### 获取可见工具
- **POST/API/V1/tool/visible**
  - **摘要**：检索用户可见的工具。
  - **响应**：
    - 200：回报`UnifiedResponseModel`使用可见工具。
    - 422：验证错误。

### 更新工具
- **PUT /api/v1/tool/update**
  - **摘要**：更新现有工具。
  - **请求身体**：`ToolUpdateRequest`
    - `tool_id`（字符串，必需）：工具ID。
    - `zh_name`, `en_name`, `description`, `logo_url`（可选）：更新的字段。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 删除工具
- **DELETE /api/v1/tool/delete**
  - **摘要**：删除工具。
  - **请求身体**：`Body_delete_tool_api_v1_tool_delete_delete`
    - `tool_id`（字符串，必需）：工具ID。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

---

## LLM管理

### 创建LLM
- **POST /api/v1/llm/create**
  - **摘要**：创建新的大型语言模型配置。
  - **请求身体**：`CreateLLMRequest`
    - `model`（字符串，必需）：模型名称。
    - `api_key`（字符串，必需）：API键。
    - `base_url`（字符串，必需）：模型服务的基本URL。
    - `llm_type`（字符串，必需）：模型类型（例如LLM，嵌入）。
    - `provider`（字符串，必需）：提供者（例如Openai，人类）。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 更新LLM
- **PUT /api/v1/llm/update**
  - **摘要**：更新现有的LLM配置。
  - **请求身体**：`UpdateLLMRequest`
    - `llm_id`（字符串，必需）：LLM ID。
    - `model`, `api_key`, `base_url`, `llm_type`, `provider`（必需）：要更新的字段。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 删除LLM
- **DELETE /api/v1/llm/delete**
  - **摘要**：删除LLM配置。
  - **请求身体**：`Body_delete_llm_api_v1_llm_delete_delete`
    - `llm_id`（字符串，必需）：LLM ID。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 获取所有LLM
- **GET /api/v1/llm/all**
  - **摘要**：检索所有LLM配置。
  - **响应**：
    - 200：回报`UnifiedResponseModel`使用LLM列表。
    - 422：验证错误。

### 获取个人LLM
- **POST/API/V1/LLM/个人**
  - **摘要**：检索用户拥有的LLM。
  - **响应**：
    - 200：回报`UnifiedResponseModel`与个人LLM。
    - 422：验证错误。

### 获得可见的LLM
- **POST/API/V1/LLM/可见**
  - **摘要**：检索用户可见的LLMS。
  - **响应**：
    - 200：回报`UnifiedResponseModel`具有可见的LLM。
    - 422：验证错误。

### 获取LLM类型
- **GET /api/v1llm/架构**
  - **摘要**：检索LLM类型模式。
  - **响应**：
    - 200：回报`UnifiedResponseModel`使用模式。
    - 422：验证错误。

---

## 知识库管理

### 创建知识库
- **POST/API/V1/知识/创建**
  - **摘要**：创建一个新的知识库。
  - **请求身体**：`KnowledgeCreateRequest`
    - `knowledge_name`（字符串，必需，2-10个字符）：知识库名称。
    - `knowledge_desc`（字符串，必需，2-200个字符）：知识库描述。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 更新知识库
- **PUT /api/v1/知识/更新**
  - **摘要**：更新现有的知识库。
  - **请求身体**：`KnowledgeUpdateRequest`
    - `knowledge_id`（字符串，必需）：知识库ID。
    - `knowledge_name`（字符串，必需，2-10个字符）：更新的名称。
    - `knowledge_desc`（字符串，必需，2-200个字符）：更新的描述。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 删除知识库
- **DELETE/API/V1/知识/DELETE **
  - **摘要**：删除知识库。
  - **请求身体**：`Body_delete_knowledge_api_v1_knowledge_delete_delete`
    - `knowledge_id`（字符串，必需）：知识库ID。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 选择知识库
- **GET /api/v1/知识/选择**
  - **摘要**：检索知识基础。
  - **响应**：
    - 200：回报`UnifiedResponseModel`具有知识库列表。
    - 422：验证错误。

---

## 知识文件管理

### 上传知识文件
- **POST /api/v1/knowledge_file/create **
  - **摘要**：将文件上传到知识库。
  - **请求身体**：`Body_upload_file_api_v1_knowledge_file_create_post`
    - `knowledge_id`（字符串，必需）：知识库ID。
    - `file_url`（字符串，必需）：上传文件URL。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 选择知识文件
- **GET /api/v1/knowlace_file/select **
  - **摘要**：在知识库中检索文件。
  - **请求身体**：`Body_select_knowledge_file_api_v1_knowledge_file_select_get`
    - `knowledge_id`（字符串，必需）：知识库ID。
  - **响应**：
    - 200：回报`UnifiedResponseModel`使用文件列表。
    - 422：验证错误。

### 删除知识文件
- **DELETE /api/v1/knowlace_file/delete **
  - **摘要**：从知识库中删除文件。
  - **请求身体**：`Body_delete_knowledge_file_api_v1_knowledge_file_delete_delete`
    - `knowledge_file_id`（字符串，必需）：文件ID。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

---

## 文件上传

### 上传文件
- **POST/API/V1/上传**
  - **摘要**：上传文件。
  - **请求身体**：`Body_upload_file_api_v1_upload_post`
    - `file`（二进制，必需）：文件（支持PDF，DOCX，TXT，JPG等）。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

---

## 消息反馈

### 喜欢消息
- **POST /api/v1/message/like **
  - **摘要**：记录一个消息“喜欢”。
  - **响应**：
    - 200：成功的回应。
    - 422：验证错误。

### 降价消息
- **POST /api/v1/sagess/down **
  - **摘要**：记录消息的“否定投票”。
  - **响应**：
    - 200：成功的回应。
    - 422：验证错误。

---

## 用户管理

### 注册用户
- **POST/API/V1/用户/注册**
  - **摘要**：注册新用户。
  - **请求身体**：`Body_register_api_v1_user_register_post`
    - `user_name`（字符串，必需）：用户名。
    - `user_email`（字符串，可选）：用户电子邮件。
    - `user_password`（字符串，必需）：用户密码。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 登录用户
- **POST/API/V1/用户/登录**
  - **摘要**：对用户进行身份验证。
  - **请求身体**：`Body_login_api_v1_user_login_post`
    - `user_name`（字符串，必需）：用户名。
    - `user_password`（字符串，必需）：密码。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

---

## MCP服务器管理

### 获取MCP服务器
- **GET /api/v1/mcp_server **
  - **摘要**：检索MCP服务器详细信息。
  - **响应**：
    - 200：成功的回应。
    - 422：验证错误。

### 创建MCP服务器
- **POST /api/v1/mcp_server **
  - **摘要**：创建一个新的MCP服务器。
  - **请求身体**：`Body_create_mcp_server_api_v1_mcp_server_post`
    - `server_name`（字符串，必需）：服务器名称。
    - `url`（字符串，必需）：服务器URL。
    - `type`（字符串，必需）：连接类型（SSE或Websocket）。
    - `config`（对象）：服务器配置。
  - **响应**：
    - 200：成功的回应。
    - 422：验证错误。

### 更新MCP服务器
- **PUT /api/v1/mcp_server **
  - **摘要**：更新现有的MCP服务器。
  - **请求身体**：`Body_update_mcp_server_api_v1_mcp_server_put`
    - `server_id`（字符串，必需）：服务器ID。
    - `server_name`, `url`, `type`, `config`（可选）：更新的字段。
  - **响应**：
    - 200：成功的回应。
    - 422：验证错误。

### 删除MCP服务器
- **DELETE /api/v1/mcp_server **
  - **摘要**：删除MCP服务器。
  - **请求身体**：
    - `server_id`（字符串，必需）：服务器ID。
  - **响应**：
    - 200：成功的回应。
    - 422：验证错误。

### 获取MCP STDIO服务器
- **GET /api/v1/mcp_stdio_server **
  - **摘要**：检索MCP STDIO服务器详细信息。
  - **响应**：
    - 200：成功的回应。
    - 422：验证错误。

### 创建MCP STDIO服务器
- **POST /api/v1/mcp_stdio_server **
  - **摘要**：创建一个新的MCP STDIO服务器。
  - **请求身体**：`Body_create_mcp_server_api_v1_mcp_stdio_server_post`
    - `name`（字符串，必需）：服务器名称。
    - `mcp_server_path`（字符串，必需）：服务器路径。
    - `mcp_server_command`（字符串，必需）：服务器命令。
    - `mcp_server_env`（字符串，可选）：服务器环境。
  - **响应**：
    - 200：成功的回应。
    - 422：验证错误。

### 更新MCP STDIO服务器
- **PUT /api/v1/mcp_stdio_server **
  - **摘要**：更新现有的MCP STDIO服务器。
  - **请求身体**：`Body_update_mcp_server_api_v1_mcp_stdio_server_put`
    - `mcp_server_id`（字符串，必需）：服务器ID。
    - `name`, `mcp_server_command`, `mcp_server_path`, `mcp_server_env`（可选）：更新的字段。
  - **响应**：
    - 200：成功的回应。
    - 422：验证错误。

### 删除MCP STDIO服务器
- **DELETE /api/v1/mcp_stdio_server **
  - **摘要**：删除MCP STDIO服务器。
  - **请求身体**：`Body_delete_mcp_server_api_v1_mcp_stdio_server_delete`
    - `mcp_server_id`（字符串，必需）：服务器ID。
  - **响应**：
    - 200：成功的回应。
    - 422：验证错误。

### 获取MCP工具
- **GET /api/v1/mcp_tools **
  - **摘要**：检索与MCP服务器关联的工具。
  - **请求身体**：`Body_get_mcp_tools_api_v1_mcp_tools_get`
    - `server_id`（字符串，必需）：MCP服务器ID。
  - **响应**：
    - 200：成功的回应。
    - 422：验证错误。

---

## MCP用户配置

### 创建MCP用户配置
- **POST /api/v1/mcp_user_config/create **
  - **摘要**：创建新的MCP用户配置。
  - **请求身体**：`MCPUserConfigCreateRequest`
    - `mcp_server_id`（字符串，必需）：MCP服务器ID。
    - `config`（对象，可选）：配置详细信息。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 通过ID获取MCP用户配置
- **GET /api/v1/mcp_user_config/{config_id} **
  - **摘要**：通过ID检索MCP用户配置。
  - **参数**：
    - `config_id`（字符串，路径，必需）：配置ID。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 更新MCP用户配置
- **PUT /api/v1/mcp_user_config/update **
  - **摘要**：更新现有的MCP用户配置。
  - **请求身体**：`MCPUserConfigUpdateRequest`
    - `config_id`（字符串，必需）：配置ID。
    - `mcp_server_id`（字符串，必需）：MCP服务器ID。
    - `config`（对象，可选）：更新的配置。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 删除MCP用户配置
- **DELETE  /api/v1/mcp_user_config/delete **
  - **摘要**：删除MCP用户配置。
  - **请求身体**：`Body_delete_mcp_user_config_api_v1_mcp_user_config_delete_delete`
    - `config_id`（字符串，必需）：配置ID。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

### 获取MCP用户配置
- **GET /api/v1/mcp_user_config **
  - **摘要**：检索服务器的MCP用户配置。
  - **参数**：
    - `mcp_server_id`（字符串，查询，必需）：MCP服务器ID。
  - **响应**：
    - 200：回报`UnifiedResponseModel`.
    - 422：验证错误。

---

## 响应模式

### UnifiedResponsemodel
- **特性**：
  - `status_code`（整数，必需）：响应状态代码。
  - `status_message`（字符串，必需）：状态消息。
  - `data`（任何）：响应数据。
- **描述**：大多数端点的标准响应格式。

### httpvalidationer
- **特性**：
  - `detail`（数组`ValidationError`）：验证错误详细信息。
- **描述**：验证失败时返回422响应。
