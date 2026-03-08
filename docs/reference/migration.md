# AgentChat v2.2.0 迁移指南

> **从 LangChain 0.x 升级到 LangChain 1.0+ 的完整迁移指南**

## 📋 概述

AgentChat v2.2.0 是一个重大版本更新，主要变更是将 LangChain 从 0.x 版本升级到 1.0+ 版本。LangChain 1.0 引入了**革命性的架构变更**：

- 🔄 **全新的 Agent 系统**: 从 `initialize_agent` 完全迁移到 `create_agent`
- 🛠️ **工具系统重构**: 使用 `@tool` 装饰器和新的工具定义方式
- 🎯 **中间件架构**: 全新的中间件系统替代旧的回调机制
- 📊 **状态管理**: 基于 TypedDict 的状态系统
- 🌊 **流式处理**: 原生支持流式响应和实时交互

## 🚨 重要提醒

- **完全重写**: 这不是简单的版本升级，而是架构的完全重写
- **备份数据**: 升级前请务必备份您的数据库和配置文件
- **测试环境**: 强烈建议先在测试环境中进行完整验证
- **依赖冲突**: LangChain 1.0 对依赖包有严格要求
- **学习成本**: 新架构需要重新学习 Agent 开发模式

---

## 📦 版本对比

| 组件 |     v2.1.x 及以下     |    v2.2.0+     | 说明 |
|:---:|:------------------:|:--------------:|:---|
| **LangChain** |        0.x         |     1.0.3+     | 核心框架完全重写 |
| **LangChain Community** |        0.x         |     0.4.1+     | 社区组件包 |
| **LangChain OpenAI** |        0.x         |     1.0.2+     | OpenAI 集成包 |
| **LangGraph** |         -          |     1.0.2+     | 图形化 Agent 编排（核心） |
| **Agent 架构** | `initialize_agent` | `create_agent` | 完全不同的实现方式 |

---

## 🔄 主要变更内容

### 1. **包结构重组**

#### 变更前 (LangChain 0.x)
```python
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from langchain.callbacks.base import BaseCallbackHandler
```

#### 变更后 (LangChain 1.0+)
```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.tools import BaseTool, tool
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.callbacks import BaseCallbackHandler
from langchain.agents import create_agent  # 新的核心函数
from langchain.agents.middleware import wrap_tool_call, after_model
```

### 2. **Agent 架构革命性变更 - 从 initialize_agent 到 create_agent**

#### 变更前 (LangChain 0.x)
```python
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

# 旧的 Agent 初始化方式
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory,
    verbose=True
)

# 运行 Agent
result = agent.run("Hello, what can you do?")
```

#### 变更后 (LangChain 1.0+ 官方推荐)
```python
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

# 方式1: 使用模型标识符字符串 (最简单)
agent = create_agent("gpt-4o", tools=tools)

# 方式2: 使用模型实例 (更多控制)
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-4o", temperature=0.1, max_tokens=1000)
agent = create_agent(model, tools=tools)

# 方式3: 添加系统提示
agent = create_agent(
    model="gpt-4o",
    tools=tools,
    system_prompt="You are a helpful assistant. Be concise and accurate."
)

# 运行 Agent (新的调用方式)
result = agent.invoke({
    "messages": [{"role": "user", "content": "Hello, what can you do?"}]
})

# 流式调用
for chunk in agent.stream({
    "messages": [{"role": "user", "content": "Search for AI news"}]
}):
    print(chunk)
```

### 3. **工具系统完全重构**

#### 变更前 (LangChain 0.x)
```python
from langchain.tools import Tool

def search_function(query: str) -> str:
    return f"Search results for: {query}"

# 简单工具定义
tool = Tool(
    name="Search",
    description="Search for information",
    func=search_function
)

# 使用工具
tools = [tool]
agent = initialize_agent(tools=tools, llm=llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION)
```

#### 变更后 (LangChain 1.0+ 官方推荐)
```python
from langchain_core.tools import tool
from typing import Annotated

# 方式1: 使用 @tool 装饰器 (官方推荐)
@tool
def search(query: Annotated[str, "The search query"]) -> str:
    """Search for information on the internet."""
    return f"Search results for: {query}"

@tool
def get_weather(location: Annotated[str, "The location to get weather for"]) -> str:
    """Get weather information for a location."""
    return f"Weather in {location}: Sunny, 72°F"

# 使用工具 - 新的 create_agent 方式
from langchain.agents import create_agent

agent = create_agent("gpt-4o", tools=[search, get_weather])

# 方式2: 继承 BaseTool (高级用法)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(description="The search query")

class SearchTool(BaseTool):
    name: str = "search"
    description: str = "Search for information"
    args_schema: type[BaseModel] = SearchInput

    def _run(self, query: str) -> str:
        return f"Search results for: {query}"

    async def _arun(self, query: str) -> str:
        return f"Async search results for: {query}"
```

### 4. **中间件系统 - 全新的扩展机制**

#### 新增功能 (LangChain 1.0+)
LangChain 1.0 引入了强大的中间件系统，替代了旧的回调机制：

```python
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call, after_model, wrap_model_call
from langchain_core.messages import ToolMessage

# 工具调用中间件 - 处理工具执行
@wrap_tool_call
def handle_tool_errors(request, handler):
    """处理工具执行错误"""
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Tool error: {str(e)}",
            tool_call_id=request.tool_call["id"]
        )

# 模型后处理中间件
@after_model
def log_model_response(state, runtime):
    """记录模型响应"""
    last_message = state["messages"][-1]
    print(f"Model response: {last_message.content}")
    return None

# 动态模型选择中间件
@wrap_model_call
def dynamic_model_selection(request, handler):
    """基于对话复杂度选择模型"""
    message_count = len(request.state["messages"])
    if message_count > 10:
        # 长对话使用高级模型
        from langchain_openai import ChatOpenAI
        advanced_model = ChatOpenAI(model="gpt-4o")
        return handler(request.override(model=advanced_model))
    return handler(request)

# 创建带中间件的 Agent
agent = create_agent(
    model="gpt-4o-mini",
    tools=[search, get_weather],
    middleware=[handle_tool_errors, log_model_response, dynamic_model_selection]
)
```

### 5. **结构化输出 - 新的响应格式控制**

#### 新增功能 (LangChain 1.0+)
```python
from pydantic import BaseModel
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy, ProviderStrategy

class ContactInfo(BaseModel):
    name: str
    email: str
    phone: str

# 方式1: 使用 ToolStrategy (兼容所有支持工具调用的模型)
agent = create_agent(
    model="gpt-4o-mini",
    tools=[search_tool],
    response_format=ToolStrategy(ContactInfo)
)

# 方式2: 使用 ProviderStrategy (仅支持原生结构化输出的模型)
agent = create_agent(
    model="gpt-4o",
    response_format=ProviderStrategy(ContactInfo)
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Extract contact info from: John Doe, john@example.com, (555) 123-4567"}]
})

# 访问结构化响应
contact = result["structured_response"]
# ContactInfo(name='John Doe', email='john@example.com', phone='(555) 123-4567')
```

### 6. **自定义状态管理 - 扩展 Agent 记忆**

#### 变更前 (LangChain 0.x)
```python
from langchain.memory import ConversationBufferMemory

# 简单的内存管理
memory = ConversationBufferMemory(return_messages=True)
```

#### 变更后 (LangChain 1.0+)
```python
from langchain.agents import AgentState, create_agent
from typing import TypedDict

# 自定义状态 - 必须继承 AgentState 并使用 TypedDict
class CustomState(AgentState):
    user_preferences: dict
    conversation_context: str
    tool_usage_count: int

# 方式1: 通过 state_schema 参数
agent = create_agent(
    model="gpt-4o",
    tools=[search, get_weather],
    state_schema=CustomState
)

# 调用时传入自定义状态
result = agent.invoke({
    "messages": [{"role": "user", "content": "I prefer technical explanations"}],
    "user_preferences": {"style": "technical", "verbosity": "detailed"},
    "conversation_context": "software development discussion",
    "tool_usage_count": 0
})

# 方式2: 通过中间件定义状态 (推荐)
from langchain.agents.middleware import AgentMiddleware

class CustomMiddleware(AgentMiddleware):
    state_schema = CustomState
    
    def before_model(self, state: CustomState, runtime):
        # 在模型调用前处理状态
        state["tool_usage_count"] += 1
        return None

agent = create_agent(
    model="gpt-4o",
    tools=[search, get_weather],
    middleware=[CustomMiddleware()]
)
```

### 7. **流式处理增强**

#### 变更前 (LangChain 0.x)
```python
# 简单的同步调用
result = agent.run("What's the weather like?")
print(result)
```

#### 变更后 (LangChain 1.0+)
```python
# 流式处理 - 显示中间步骤
for chunk in agent.stream({
    "messages": [{"role": "user", "content": "Search for AI news and summarize"}]
}, stream_mode="values"):
    # 每个 chunk 包含该时刻的完整状态
    latest_message = chunk["messages"][-1]
    if latest_message.content:
        print(f"Agent: {latest_message.content}")
    elif latest_message.tool_calls:
        print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")
```

---

## 🛠️ AgentChat 特定变更

### 1. **MCP 集成更新**

#### 文件位置
- `src/backend/agentchat/services/mcp_openai/mcp_langchain.py`

#### 变更前
```python
from langchain.tools import Tool
from pydantic import BaseModel, Field, create_model

def convert_base_tool(tool_name, tool_description, schema: Dict[str, Any]):
    schema_model = create_model_from_schema(tool_name, schema)
    return Tool(
        name=tool_name,
        description=tool_description,
        func=lambda **kwargs: call_mcp_tool(kwargs),
        args_schema=schema_model
    )
```

#### 变更后
```python
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field, create_model
from typing import Any, Dict, Type

@tool
async def mcp_tool_wrapper(tool_name: str, **kwargs) -> str:
    """MCP工具包装器，支持异步调用"""
    return await call_mcp_tools([{
        "server_name": kwargs.get("server_name"),
        "url": kwargs.get("url"),
        "type": kwargs.get("type"),
        "tool_name": tool_name,
        "tool_args": kwargs
    }])

class MCPTool(BaseTool):
    name: str
    description: str
    server_config: Dict[str, Any]
    
    def _run(self, **kwargs) -> str:
        # 同步工具执行
        return asyncio.run(self._arun(**kwargs))
    
    async def _arun(self, **kwargs) -> str:
        # 异步工具执行
        mcp_args = [{
            "server_name": self.server_config["name"],
            "url": self.server_config["url"],
            "type": self.server_config["type"],
            "tool_name": self.name,
            "tool_args": kwargs
        }]
        return await call_mcp_tools(mcp_args)
```

### 2. **Mars Agent 更新**

#### 文件位置
- `src/backend/agentchat/services/mars/mars_agent.py`

#### 变更前
```python
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

class MarsAgent:
    def __init__(self, mars_config: MarsConfig):
        self.mars_tools = None
        self.mars_config = mars_config
        
    def setup_agent(self):
        memory = ConversationBufferMemory(return_messages=True)
        return initialize_agent(
            tools=self.mars_tools,
            llm=self.conversation_model,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            memory=memory,
            verbose=True
        )
```

#### 变更后
```python
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call, after_model
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage

class MarsAgent:
    def __init__(self, mars_config: MarsConfig):
        self.mars_tools = None
        self.mars_config = mars_config
        self.mars_output_queue = None
        self.reasoning_interrupt = None

    async def init_mars_agent(self):
        self.mars_tools = await self.setup_mars_tools()
        await self.setup_language_model()
        self.middlewares = await self.setup_middlewares()
        self.react_agent = self.setup_react_agent()

    def setup_react_agent(self):
        return create_agent(
            model=self.conversation_model,
            tools=self.mars_tools,
            middleware=self.middlewares,
            system_prompt="You are a helpful Mars assistant"
        )

    async def setup_middlewares(self):
        @after_model
        async def handler_after_model(state, runtime):
            last_message = state["messages"][-1]
            if not last_message.tool_calls:
                await self.mars_output_queue.put(None)
            return None

        @wrap_tool_call
        async def handler_tool_call(request, handler):
            request.tool_call["args"].update({"user_id": self.mars_config.user_id})
            tool_result = await handler(request)
            return ToolMessage(content=tool_result, tool_call_id=request.tool_call["id"])

        return [handler_after_model, handler_tool_call]

    async def ainvoke_stream(self, messages: List[BaseMessage]):
        """流式调用Mars Agent"""
        self.reasoning_interrupt = asyncio.Event()
        self.mars_output_queue = asyncio.Queue()
        
        callback = UsageMetadataCallbackHandler()
        
        async for chunk in self.react_agent.astream(
            input={"messages": messages},
            config={"callbacks": [callback]},
            stream_mode=["custom"]
        ):
            await self.mars_output_queue.put(chunk)
        
        await self.mars_output_queue.put(None)
```

### 3. **RAG 系统更新**

#### 文件位置
- `src/backend/agentchat/services/rag/`

#### 变更前
```python
from langchain.vectorstores import Chroma, Milvus
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
```

#### 变更后
```python
from langchain_community.vectorstores import Chroma, Milvus
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
```

### 4. **工具系统统一更新**

#### 文件位置
- `src/backend/agentchat/tools/`

#### 变更前
```python
from langchain.tools import Tool

def create_weather_tool():
    return Tool(
        name="get_weather",
        description="Get weather information",
        func=get_weather_data
    )
```

#### 变更后
```python
from langchain_core.tools import tool
from typing import Annotated

@tool
def get_weather(
    location: Annotated[str, "The location to get weather for"],
    unit: Annotated[str, "Temperature unit (celsius/fahrenheit)"] = "celsius"
) -> str:
    """Get current weather information for a specific location."""
    return get_weather_data(location, unit)

# 或者使用类定义
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

class WeatherInput(BaseModel):
    location: str = Field(description="The location to get weather for")
    unit: str = Field(default="celsius", description="Temperature unit")

class WeatherTool(BaseTool):
    name: str = "get_weather"
    description: str = "Get current weather information"
    args_schema: type[BaseModel] = WeatherInput

    def _run(self, location: str, unit: str = "celsius") -> str:
        return get_weather_data(location, unit)

    async def _arun(self, location: str, unit: str = "celsius") -> str:
        return await get_weather_data_async(location, unit)
```

---

## 📋 迁移步骤

### 步骤 1: 环境准备

```bash
# 1. 备份当前环境
cp requirements.txt requirements.txt.backup
cp pyproject.toml pyproject.toml.backup

# 2. 创建新的虚拟环境
python -m venv venv_v2.2.0
source venv_v2.2.0/bin/activate  # Linux/Mac
# 或
venv_v2.2.0\Scripts\activate  # Windows

# 3. 安装新版本依赖
pip install -r requirements.txt
```

### 步骤 2: 代码更新

#### 2.1 更新导入语句
```bash
# 使用脚本批量替换导入语句
python scripts/update_imports.py
```

#### 2.2 更新 Agent 定义
- 将所有 `initialize_agent` 替换为 `create_agent`
- 更新工具定义方式
- 修改 Agent 调用逻辑

#### 2.3 更新回调处理器
- 将回调处理器迁移到中间件系统
- 更新使用统计相关代码

### 步骤 3: 配置更新

#### 3.1 更新 config.yaml
```yaml
# 新增 LangChain 1.0 相关配置
langchain:
  version: "1.0.3"
  enable_tracing: true
  
# 更新模型配置
models:
  default_model: "gpt-4o"
  temperature: 0.7
```

### 步骤 4: 测试验证

#### 4.1 单元测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行特定模块测试
python -m pytest tests/test_agents.py
python -m pytest tests/test_tools.py
```

#### 4.2 集成测试
```bash
# 启动服务
cd src/backend
uvicorn agentchat.main:app --port 7860

# 测试 API 接口
curl -X POST "http://localhost:7860/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"dialog_id": "test", "user_input": "Hello"}'
```

---

## 🐛 常见问题与解决方案

### 问题 1: 导入错误

**错误信息:**
```
ImportError: cannot import name 'initialize_agent' from 'langchain.agents'
```

**解决方案:**
```python
# 替换旧的导入
# from langchain.agents import initialize_agent

# 使用新的导入
from langchain.agents import create_agent
```

### 问题 2: 工具定义错误

**错误信息:**
```
TypeError: Tool() missing required argument: 'args_schema'
```

**解决方案:**
```python
from langchain_core.tools import tool
from typing import Annotated

@tool
def my_tool(query: Annotated[str, "Input query"]) -> str:
    """Tool description"""
    return f"Result for {query}"
```

### 问题 3: Agent 调用方式错误

**错误信息:**
```
AttributeError: 'CompiledGraph' object has no attribute 'run'
```

**解决方案:**
```python
# 旧的调用方式
# result = agent.run("Hello")

# 新的调用方式
result = agent.invoke({
    "messages": [{"role": "user", "content": "Hello"}]
})
```


## 📚 参考资源

### 官方文档
- [LangChain 1.0 Agents 文档](https://docs.langchain.com/oss/python/langchain/agents)
- [LangChain 1.0 迁移指南](https://python.langchain.com/docs/versions/migrating_to_langchain_1_0)
- [LangChain 工具文档](https://docs.langchain.com/oss/python/langchain/tools)
- [LangChain 中间件文档](https://docs.langchain.com/oss/python/langchain/middleware)

### 社区资源
- [LangChain GitHub Issues](https://github.com/langchain-ai/langchain/issues)
- [LangChain Discord 社区](https://discord.gg/langchain)

### AgentChat 相关
- [AgentChat 技术文档](agentchat.md)
- [API 文档](api.md)
- [核心功能文档](core.md)

---

## 🆘 获取帮助

如果在迁移过程中遇到问题，可以通过以下方式获取帮助：

1. **查看日志**: 检查应用日志中的错误信息
2. **运行测试**: 使用测试套件验证功能
3. **提交 Issue**: 在 GitHub 仓库中提交问题
4. **社区讨论**: 参与社区讨论获取帮助

---

## ✅ 迁移检查清单

- [ ] 备份数据和配置文件
- [ ] 更新 Python 版本到 3.12+
- [ ] 安装新版本依赖包
- [ ] 运行导入更新脚本
- [ ] 运行 Pydantic 兼容性修复脚本
- [ ] 将 `initialize_agent` 替换为 `create_agent`
- [ ] 更新工具定义为 `@tool` 装饰器
- [ ] 将回调处理器迁移到中间件
- [ ] 更新 Agent 调用方式 (`run` → `invoke`)
- [ ] 运行单元测试
- [ ] 运行集成测试
- [ ] 验证 API 接口功能
- [ ] 验证前端界面功能
- [ ] 部署到生产环境

---

*最后更新时间: 2025年10月*
*基于 LangChain 1.0 官方文档编写*