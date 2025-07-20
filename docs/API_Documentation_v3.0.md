

# AgentChat API 文档 v1.0

本文档整理了 AgentChat 系统 v1 版本的所有 API 接口，包含接口 URL、请求方法、请求参数和返回参数。

## 目录
- [对话相关 API](#对话相关-api)
- [知识库文件 API](#知识库文件-api)
- [MCP 服务器 API](#mcp-服务器-api)
- [用户 API](#用户-api)
- [工具 API](#工具-api)
- [大模型 API](#大模型-api)
- [知识库 API](#知识库-api)
- [对话框 API](#对话框-api)
- [智能体 API](#智能体-api)
- [MCP 用户配置 API](#mcp-用户配置-api)
- [历史记录 API](#历史记录-api)
- [消息 API](#消息-api)

---

## 对话相关 API

### 1. 对话接口
- **接口 URL**: `/api/v1/chat`
- **请求方法**: `POST`
- **请求参数**:
  ```json
  {
    "dialog_id": "string",        // 对话ID
    "user_input": "string",       // 用户输入内容
    "file_url": "string"          // 可选，文件URL
  }
  ```
- **返回参数**: Server-Sent Events (SSE) 流式响应
  ```json
  {
    "chunk": "string",            // 响应片段
    "type": "response_chunk"      // 事件类型
  }
  ```

### 2. 文件上传接口
- **接口 URL**: `/api/v1/upload`
- **请求方法**: `POST`
- **请求参数**: 
  - `file`: 上传的文件（支持 PDF、DOCX、TXT、JPG 等格式）
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "string",          // 文件访问URL
    "data": null
  }
  ```

### 3. 知识库检索接口
- **接口 URL**: `/api/v1/knowledge/retrieval`
- **请求方法**: `POST`
- **请求参数**:
  ```json
  {
    "query": "string",            // 用户问题
    "knowledge_id": "string|array" // 知识库ID，可以是单个或数组
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": "string"              // 检索到的内容
  }
  ```

---

## 知识库文件 API

### 1. 创建知识库文件
- **接口 URL**: `/api/v1/knowledge_file/create`
- **请求方法**: `POST`
- **请求参数**:
  ```json
  {
    "knowledge_id": "string",     // 知识库ID
    "file_url": "string"          // 文件上传后返回的URL
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 2. 查询知识库文件
- **接口 URL**: `/api/v1/knowledge_file/select`
- **请求方法**: `GET`
- **请求参数**:
  - `knowledge_id`: 知识库ID (Query参数)
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "file_id": "string",
        "file_name": "string",
        "file_url": "string",
        "upload_time": "string"
      }
    ]
  }
  ```

### 3. 删除知识库文件
- **接口 URL**: `/api/v1/knowledge_file/delete`
- **请求方法**: `DELETE`
- **请求参数**:
  ```json
  {
    "knowledge_file_id": "string" // 知识库文件ID
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

---

## MCP 服务器 API

### 1. 创建 MCP 服务器
- **接口 URL**: `/api/v1/mcp_server`
- **请求方法**: `POST`
- **请求参数**:
  
  ```json
  {
    "server_name": "string",      // MCP Server名称
    "url": "string",              // MCP Server URL
    "type": "string",             // 连接方式（SSE、Websocket）
    "config": {}                  // 可选，MCP Server配置信息
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 2. 获取 MCP 服务器列表
- **接口 URL**: `/api/v1/mcp_server`
- **请求方法**: `GET`
- **请求参数**: 无
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "server_id": "string",
        "server_name": "string",
        "url": "string",
        "type": "string",
        "config": {},
        "tools": ["string"]
      }
    ]
  }
  ```

### 3. 删除 MCP 服务器
- **接口 URL**: `/api/v1/mcp_server`
- **请求方法**: `DELETE`
- **请求参数**:
  ```json
  {
    "server_id": "string"         // MCP Server ID
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 4. 获取 MCP 工具信息
- **接口 URL**: `/api/v1/mcp_tools`
- **请求方法**: `GET`
- **请求参数**:
  ```json
  {
    "server_id": "string"         // MCP Server ID
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "tools": [
        {
          "name": "string",
          "description": "string",
          "parameters": {}
        }
      ]
    }
  }
  ```

### 5. 更新 MCP 服务器
- **接口 URL**: `/api/v1/mcp_server`
- **请求方法**: `PUT`
- **请求参数**:
  ```json
  {
    "server_id": "string",        // MCP Server ID
    "server_name": "string",      // 可选，MCP Server名称
    "url": "string",              // 可选，MCP Server URL
    "type": "string",             // 可选，连接方式
    "config": {}                  // 可选，MCP Server配置信息
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

---

## 用户 API

### 1. 用户注册
- **接口 URL**: `/api/v1/user/register`
- **请求方法**: `POST`
- **请求参数**:
  
  ```json
  {
    "user_name": "string",        // 用户名
    "user_email": "string",       // 可选，用户邮箱
    "user_password": "string"     // 用户密码
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 2. 用户登录
- **接口 URL**: `/api/v1/user/login`
- **请求方法**: `POST`
- **请求参数**:
  ```json
  {
    "user_name": "string",        // 用户名
    "user_password": "string"     // 用户密码
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "user_id": "string",
      "access_token": "string"
    }
  }
  ```

### 3. 更新用户信息
- **接口 URL**: `/api/v1/user/login`
- **请求方法**: `POST`
- **请求参数**:
  ```json
  {
    "user_avatar": "string",        // 用户上传头像或选择头像的链接
    "user_description": "string"    // 用户的描述，默认就是：该用户很懒，没有留下一片云彩
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      
    }
  }

### 4. 用户头像选择
- **接口 URL**: `/api/v1/user/icons`
- **请求方法**: `GET`
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": ["http://........", "https://........."]
  }



---

## 工具 API

### 1. 创建工具
- **接口 URL**: `/api/v1/tool/create`
- **请求方法**: `POST`
- **请求参数**:
  ```json
  {
    "zh_name": "string",          // 工具中文名称
    "en_name": "string",          // 工具英文名称
    "description": "string",      // 工具描述
    "logo_url": "string"          // 工具图标URL
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "tool_id": "string"
    }
  }
  ```

### 2. 获取所有工具
- **接口 URL**: `/api/v1/tool/all`
- **请求方法**: `GET`
- **请求参数**: 无
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "tool_id": "string",
        "zh_name": "string",
        "en_name": "string",
        "description": "string",
        "logo_url": "string"
      }
    ]
  }
  ```

### 3. 获取个人工具
- **接口 URL**: `/api/v1/tool/own`
- **请求方法**: `POST`
- **请求参数**: 无
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "tool_id": "string",
        "zh_name": "string",
        "en_name": "string",
        "description": "string",
        "logo_url": "string"
      }
    ]
  }
  ```

### 4. 获取可见工具
- **接口 URL**: `/api/v1/tool/visible`
- **请求方法**: `POST`
- **请求参数**: 无
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "tool_id": "string",
        "zh_name": "string",
        "en_name": "string",
        "description": "string",
        "logo_url": "string"
      }
    ]
  }
  ```

### 5. 删除工具
- **接口 URL**: `/api/v1/tool/delete`
- **请求方法**: `DELETE`
- **请求参数**:
  ```json
  {
    "tool_id": "string"           // 工具ID
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 6. 更新工具
- **接口 URL**: `/api/v1/tool/update`
- **请求方法**: `PUT`
- **请求参数**:
  ```json
  {
    "tool_id": "string",          // 工具ID
    "zh_name": "string",          // 可选，工具中文名称
    "en_name": "string",          // 可选，工具英文名称
    "description": "string",      // 可选，工具描述
    "logo_url": "string"          // 可选，工具图标URL
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

---

## 大模型 API

### 1. 创建大模型
- **接口 URL**: `/api/v1/llm/create`
- **请求方法**: `POST`
- **请求参数**:
  ```json
  {
    "model": "string",            // 大模型名称
    "api_key": "string",          // API密钥
    "base_url": "string",         // 基础URL
    "provider": "string",         // 提供商
    "llm_type": "string"          // 模型类型
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 2. 删除大模型
- **接口 URL**: `/api/v1/llm/delete`
- **请求方法**: `DELETE`
- **请求参数**:
  ```json
  {
    "llm_id": "string"            // 大模型ID
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 3. 更新大模型
- **接口 URL**: `/api/v1/llm/update`
- **请求方法**: `PUT`
- **请求参数**:
  ```json
  {
    "llm_id": "string",           // 大模型ID
    "model": "string",            // 可选，大模型名称
    "api_key": "string",          // 可选，API密钥
    "base_url": "string",         // 可选，基础URL
    "provider": "string",         // 可选，提供商
    "llm_type": "string"          // 可选，模型类型
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 4. 获取所有大模型
- **接口 URL**: `/api/v1/llm/all`
- **请求方法**: `GET`
- **请求参数**: 无
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "llm_id": "string",
        "model": "string",
        "provider": "string",
        "llm_type": "string"
      }
    ]
  }
  ```

### 5. 获取个人大模型
- **接口 URL**: `/api/v1/llm/personal`
- **请求方法**: `POST`
- **请求参数**: 无
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "llm_id": "string",
        "model": "string",
        "provider": "string",
        "llm_type": "string"
      }
    ]
  }
  ```

### 6. 获取可见大模型
- **接口 URL**: `/api/v1/llm/visible`
- **请求方法**: `POST`
- **请求参数**: 无
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "llm_id": "string",
        "model": "string",
        "provider": "string",
        "llm_type": "string"
      }
    ]
  }
  ```

### 7. 获取大模型类型
- **接口 URL**: `/api/v1/llm/schema`
- **请求方法**: `GET`
- **请求参数**: 无
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": ["LLM", "Embedding"]
  }
  ```

---

## 知识库 API

### 1. 创建知识库
- **接口 URL**: `/api/v1/knowledge/create`
- **请求方法**: `POST`
- **请求参数**:
  ```json
  {
    "knowledge_name": "string",   // 知识库名称
    "knowledge_desc": "string"    // 知识库描述
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 2. 查询知识库
- **接口 URL**: `/api/v1/knowledge/select`
- **请求方法**: `GET`
- **请求参数**: 无
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "knowledge_id": "string",
        "knowledge_name": "string",
        "knowledge_desc": "string",
        "create_time": "string"
      }
    ]
  }
  ```

### 3. 更新知识库
- **接口 URL**: `/api/v1/knowledge/update`
- **请求方法**: `PUT`
- **请求参数**:
  ```json
  {
    "knowledge_id": "string",     // 知识库ID
    "knowledge_name": "string",   // 可选，知识库名称
    "knowledge_desc": "string"    // 可选，知识库描述
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 4. 删除知识库
- **接口 URL**: `/api/v1/knowledge/delete`
- **请求方法**: `DELETE`
- **请求参数**:
  ```json
  {
    "knowledge_id": "string"      // 知识库ID
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

---

## 对话框 API

### 1. 获取对话列表
- **接口 URL**: `/api/v1/dialog/list`
- **请求方法**: `GET`
- **请求参数**: 无
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "dialog_id": "string",
        "name": "string",
        "agent_id": "string",
        "agent_type": "string",
        "create_time": "string"
      }
    ]
  }
  ```

### 2. 创建对话
- **接口 URL**: `/api/v1/dialog`
- **请求方法**: `POST`
- **请求参数**:
  ```json
  {
    "name": "string",             // 对话名称
    "agent_id": "string",         // 智能体ID
    "agent_type": "string"        // 智能体类型
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 3. 删除对话
- **接口 URL**: `/api/v1/dialog`
- **请求方法**: `DELETE`
- **请求参数**:
  ```json
  {
    "dialog_id": "string"         // 对话ID
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

---

## 智能体 API

### 1. 创建智能体
- **接口 URL**: `/api/v1/agent`
- **请求方法**: `POST`
- **请求参数**:
  ```json
  {
    "name": "string",             // 智能体名称
    "description": "string",      // 智能体描述
    "logo_url": "string",         // 智能体图标URL
    "tool_ids": ["string"],       // 工具ID列表
    "llm_id": "string",           // 大模型ID
    "mcp_ids": ["string"],        // MCP服务器ID列表
    "system_prompt": "string",    // 系统提示词
    "knowledge_ids": ["string"],  // 知识库ID列表
    "use_embedding": boolean      // 是否使用嵌入
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 2. 获取智能体
- **接口 URL**: `/api/v1/agent`
- **请求方法**: `GET`
- **请求参数**: 无
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "agent_id": "string",
        "name": "string",
        "description": "string",
        "logo_url": "string",
        "tool_ids": ["string"],
        "llm_id": "string",
        "mcp_ids": ["string"],
        "system_prompt": "string",
        "knowledge_ids": ["string"],
        "use_embedding": boolean
      }
    ]
  }
  ```

### 3. 删除智能体
- **接口 URL**: `/api/v1/agent`
- **请求方法**: `DELETE`
- **请求参数**:
  ```json
  {
    "agent_id": "string"          // 智能体ID
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 4. 更新智能体
- **接口 URL**: `/api/v1/agent`
- **请求方法**: `PUT`
- **请求参数**:
  ```json
  {
    "agent_id": "string",         // 智能体ID
    "name": "string",             // 可选，智能体名称
    "description": "string",      // 可选，智能体描述
    "logo_url": "string",         // 可选，智能体图标URL
    "tool_ids": ["string"],       // 可选，工具ID列表
    "llm_id": "string",           // 可选，大模型ID
    "mcp_ids": ["string"],        // 可选，MCP服务器ID列表
    "system_prompt": "string",    // 可选，系统提示词
    "knowledge_ids": ["string"],  // 可选，知识库ID列表
    "use_embedding": boolean      // 可选，是否使用嵌入
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 5. 搜索智能体
- **接口 URL**: `/api/v1/agent/search`
- **请求方法**: `POST`
- **请求参数**:
  ```json
  {
    "name": "string"              // 搜索的智能体名称
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "agent_id": "string",
        "name": "string",
        "description": "string",
        "logo_url": "string"
      }
    ]
  }
  ```

---

## MCP 用户配置 API

### 1. 创建 MCP 用户配置
- **接口 URL**: `/api/v1/mcp_user_config/create`
- **请求方法**: `POST`
- **请求参数**:
  ```json
  {
    "mcp_server_id": "string",    // MCP服务器ID
    "config": {}                  // 配置信息
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "config_id": "string"
    }
  }
  ```

### 2. 根据ID获取 MCP 用户配置
- **接口 URL**: `/api/v1/mcp_user_config/{config_id}`
- **请求方法**: `GET`
- **请求参数**: 
  - `config_id`: 配置ID (路径参数)
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "config_id": "string",
      "mcp_server_id": "string",
      "config": {}
    }
  }
  ```

### 3. 更新 MCP 用户配置
- **接口 URL**: `/api/v1/mcp_user_config/update`
- **请求方法**: `PUT`
- **请求参数**:
  ```json
  {
    "config_id": "string",        // 配置ID
    "mcp_server_id": "string",    // 可选，MCP服务器ID
    "config": {}                  // 可选，配置信息
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 4. 删除 MCP 用户配置
- **接口 URL**: `/api/v1/mcp_user_config/delete`
- **请求方法**: `DELETE`
- **请求参数**:
  ```json
  {
    "config_id": "string"         // 配置ID
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 5. 获取 MCP 用户配置
- **接口 URL**: `/api/v1/mcp_user_config`
- **请求方法**: `GET`
- **请求参数**:
  - `mcp_server_id`: MCP服务器ID (Query参数)
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "config_id": "string",
      "mcp_server_id": "string",
      "config": {}
    }
  }
  ```

---

## 历史记录 API

### 1. 获取对话历史
- **接口 URL**: `/api/v1/history`
- **请求方法**: `POST`
- **请求参数**:
  ```json
  {
    "dialog_id": "string"         // 对话ID
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "message_id": "string",
        "role": "string",
        "content": "string",
        "timestamp": "string"
      }
    ]
  }
  ```

---

## 消息 API

### 1. 消息点赞
- **接口 URL**: `/api/v1/message/like`
- **请求方法**: `POST`
- **请求参数**:
  
  ```json
  {
    "user_input": "string",       // 用户输入
    "agent_output": "string"      // 智能体输出
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 2. 消息踩
- **接口 URL**: `/api/v1/message/down`
- **请求方法**: `POST`
- **请求参数**:
  ```json
  {
    "user_input": "string",       // 用户输入
    "agent_output": "string"      // 智能体输出
  }
  ```
- **返回参数**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

---

## 通用返回格式

所有接口的返回格式都遵循统一的响应模型：

```json
{
  "code": 200,                    // 状态码，200表示成功，500表示失败
  "message": "string",            // 返回消息
  "data": "any"                   // 返回数据，根据具体接口而定
}
```

## 认证说明

除了用户注册和登录接口外，所有接口都需要用户登录认证。认证方式为 JWT Token，需要在请求头中携带 Token 或通过 Cookie 传递。

## 错误处理

当接口调用失败时，会返回相应的错误信息：

```json
{
  "code": 500,
  "message": "具体的错误信息",
  "data": null
}
```

常见错误码：
- `400`: 请求参数错误
- `401`: 未认证或认证失败
- `403`: 权限不足
- `404`: 资源不存在
- `500`: 服务器内部错误 