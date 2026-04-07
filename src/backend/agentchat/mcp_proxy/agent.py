import json
from pydantic import ValidationError
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import HumanMessage, SystemMessage, AIMessageChunk
from langgraph.config import get_stream_writer
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from agentchat.core.models.manager import ModelManager
from agentchat.prompts.register_mcp import (
    GENERATE_MCP_JSON_PROMPT,
    RESTORE_MCP_JSON_PROMPT,
    REVISE_MCP_JSON_SYSTEM_PROMPT,
    REVISE_MCP_JSON_HUMAN_PROMPT,
    MCP_AGENT_SYSTEM_PROMPT
)
from agentchat.schemas.register_mcp import RegisterMcpServerModel
from agentchat.mcp_proxy.register_mcp import RegisterMcpService
from agentchat.utils.contexts import get_user_id_context

_checkpointer = InMemorySaver()


@tool
def generate_mcp_json(user_query: str, runtime: ToolRuntime) -> str:
    """根据用户描述，提取并生成标准的 MCP Server JSON 配置字符串。
    当用户想要注册一个 MCP Server 时，首先调用此工具生成 JSON。

    Args:
        user_query: 用户原始输入，描述想要注册的 MCP Server 信息
    """
    writer = get_stream_writer()

    writer({
        "title": "提取Query中的Mcp必要信息",
        "status": "START",
        "is_error": False,
        "content": ""
    })

    client = ModelManager.get_conversation_model()

    response = client.invoke(
        input=[HumanMessage(content=GENERATE_MCP_JSON_PROMPT + user_query)],
        config={"callbacks": []}
    )

    mcp_json_str = response.content

    writer({
        "title": "提取Query中的Mcp必要信息",
        "status": "END",
        "is_error": False,
        "content": mcp_json_str
    })

    return mcp_json_str


@tool
def verify_mcp_json(mcp_json_str: str, runtime: ToolRuntime) -> str:
    """校验 MCP JSON 字符串是否合法，包括 JSON 格式和 Pydantic Schema 校验。
    生成 JSON 后必须调用此工具进行校验，根据结果决定下一步。

    Args:
        mcp_json_str: 待校验的 MCP JSON 字符串
    """
    writer = get_stream_writer()

    writer({
        "title": "校验Mcp Json是否合规",
        "status": "START",
        "is_error": False,
        "content": ""
    })

    try:
        if isinstance(mcp_json_str, str):
            data = json.loads(mcp_json_str)
        else:
            data = mcp_json_str
    except Exception as e:
        err = f"JSON解析失败: {e}"
        writer({"title": "校验Mcp Json是否合规", "status": "END", "is_error": True, "content": err})
        return f"VERIFY_FAILED: {err}"

    try:
        RegisterMcpServerModel.model_validate(data)
    except ValidationError as e:
        err = f"Pydantic校验失败: {e}"
        writer({"title": "校验Mcp Json是否合规", "status": "END", "is_error": True, "content": err})
        return f"VERIFY_FAILED: {err}"

    writer({"title": "校验Mcp Json是否合规", "status": "END", "is_error": False, "content": "校验成功"})
    return f"VERIFY_SUCCESS: {json.dumps(data, ensure_ascii=False)}"


@tool
def restore_mcp_json(mcp_json_str: str, error_message: str, runtime: ToolRuntime) -> str:
    """根据校验错误信息，修复不合法的 MCP JSON。
    当 verify_mcp_json 返回 VERIFY_FAILED 时调用此工具，修复后需再次校验。
    最多修复 2 次，超过后应放弃并告知用户。

    Args:
        mcp_json_str: 需要修复的 MCP JSON 字符串
        error_message: verify_mcp_json 返回的错误信息
    """
    writer = get_stream_writer()

    writer({"title": "修复Mcp Json", "status": "START", "is_error": False, "content": ""})

    client = ModelManager.get_conversation_model()

    response = client.invoke([
        SystemMessage(content=RESTORE_MCP_JSON_PROMPT.format(mcp_json=mcp_json_str)),
        HumanMessage(content=error_message)
    ])

    fixed_json = response.content

    writer({"title": "修复Mcp Json", "status": "END", "is_error": False, "content": fixed_json})
    return fixed_json


@tool
def revise_mcp_json(mcp_json_str: str, user_feedback: str, runtime: ToolRuntime) -> str:
    """根据用户的自然语言反馈，对已有 MCP JSON 进行修改和优化。
    当用户在确认环节选择"修改"并提供反馈意见后，调用此工具。
    调用完成后必须再次调用 verify_mcp_json 进行校验。

    Args:
        mcp_json_str: 当前的 MCP JSON 字符串
        user_feedback: 用户的自然语言修改意见
    """
    writer = get_stream_writer()

    writer({
        "title": "根据用户反馈优化Mcp配置",
        "status": "START",
        "is_error": False,
        "content": user_feedback
    })

    client = ModelManager.get_conversation_model()
    response = client.invoke(
        input=[
            SystemMessage(content=REVISE_MCP_JSON_SYSTEM_PROMPT.format(mcp_json_str=mcp_json_str)),
            HumanMessage(content=REVISE_MCP_JSON_HUMAN_PROMPT.format(user_feedback=user_feedback))
        ],
        config={"callbacks": []}
    )

    new_json = response.content.strip()
    
    # 清理可能的 markdown 代码块
    if new_json.startswith("```"):
        lines = new_json.split("\n")
        new_json = "\n".join(lines[1:-1])

    writer({
        "title": "根据用户反馈优化Mcp配置",
        "status": "END",
        "is_error": False,
        "content": new_json
    })

    return new_json


@tool
async def register_mcp_server(mcp_json_str: str, runtime: ToolRuntime) -> str:
    """将已通过校验的 MCP JSON 注册为 MCP Server。
    只有在 verify_mcp_json 返回 VERIFY_SUCCESS 后才调用此工具。
    此工具会触发人机确认，等待用户 approve / reject。

    Args:
        mcp_json_str: 已通过校验的 MCP JSON 字符串（VERIFY_SUCCESS 后的数据部分）
    """
    user_id = get_user_id_context()

    writer = get_stream_writer()
    writer({"title": "开始创建Mcp Server", "status": "START", "is_error": False, "content": ""})

    async def _register():
        try:
            json_str = mcp_json_str
            if json_str.startswith("VERIFY_SUCCESS:"):
                json_str = json_str[len("VERIFY_SUCCESS:"):].strip()

            data = json.loads(json_str) if isinstance(json_str, str) else json_str
            mcp_server = RegisterMcpServerModel.model_validate(data)
            result = await RegisterMcpService.register_mcp_by_completion(mcp_server, user_id=user_id)
            result_dict = result.model_dump() if hasattr(result, "model_dump") else result
            return True, result_dict
        except Exception as e:
            return False, str(e)

    ok, result = await _register()

    if not ok:
        writer({"title": "开始创建Mcp Server", "status": "END", "is_error": True, "content": result})
        return f"REGISTER_FAILED: {result}"

    writer({"title": "开始创建Mcp Server", "status": "END", "is_error": False, "content": "注册成功"})
    return f"REGISTER_SUCCESS: {json.dumps(result, ensure_ascii=False)}"


# Agent 定义
class AbstractMcpAgent:
    def __init__(self):
        self.model = ModelManager.get_conversation_model()

        self.tools = [
            generate_mcp_json,
            verify_mcp_json,
            restore_mcp_json,
            revise_mcp_json,
            register_mcp_server,
        ]

        # LangChain 1.0+ create_agent，加入 HITL middleware 和 checkpointer
        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=MCP_AGENT_SYSTEM_PROMPT,
            middleware=[
                HumanInTheLoopMiddleware(
                    interrupt_on={
                        # register_mcp_server 被拦截，允许 approve / reject
                        # edit 不开放：用户要改内容走 reject + message -> revise 循环
                        "register_mcp_server": {
                            "allowed_decisions": ["approve", "reject"],
                            "description": (
                                "请确认是否注册此 MCP Server：\n"
                                "- Approve — 确认注册\n"
                                "- Reject  — 取消注册\n"
                                "- Edit    — 修改信息 (点击取消会弹出修改框，自动优化后将重新提交)"
                            ),
                        },
                    },
                    description_prefix="MCP Server 注册确认",
                ),
            ],
            # HITL 必须配置 checkpointer 来保存中断状态
            checkpointer=_checkpointer,
        )

    # 初次调用：启动流

    async def astream(self, messages, thread_id: str):
        """
        流式执行 Agent（初次对话）。
        yield 三种类型：
          {"type": "text",      "content": "...", "event": {}}       # LLM 文本
          {"type": "event",     "content": "",    "event": {...}}    # 工具进度
          {"type": "interrupt", "content": "",    "event": {...}}    # HITL 中断
        """
        config = {"configurable": {"thread_id": thread_id}}

        async for mode, chunk in self.agent.astream(
            input={"messages": messages},
            config=config,
            stream_mode=["messages", "updates", "custom"],
        ):
            async for item in self._process_chunk(mode, chunk):
                yield item

    # resume：处理用户 HITL 决策后继续流
    async def astream_resume(self, command: Command, thread_id: str):
        """
        在用户做出 HITL 决策后，resume Agent 继续执行。
        command 由接口层构建后传入。
        """
        config = {"configurable": {"thread_id": thread_id}}

        async for mode, chunk in self.agent.astream(
            command,
            config=config,
            stream_mode=["messages", "updates", "custom"]
        ):
            async for item in self._process_chunk(mode, chunk):
                yield item

    # 内部统一 chunk 处理
    async def _process_chunk(self, mode, chunk):
        # 处理 LLM token
        if mode == "messages":
            msg, metadata = chunk
            if msg.content and isinstance(msg, AIMessageChunk):
                yield {"type": "text", "content": msg.content, "event": {}}

        # 处理图节点更新（包含 HITL interrupt）
        elif mode == "updates":
            for node_name, node_update in chunk.items():
                if node_name == "__interrupt__":
                    interrupts = node_update if isinstance(node_update, tuple) else [node_update[0]]
                    for interrupt in interrupts:
                        interrupt_value = interrupt.value if hasattr(interrupt, "value") else interrupt
                        
                        # 解析 mcp_json_str 供前端预览表格
                        action_requests = interrupt_value.get("action_requests", [])
                        review_configs = interrupt_value.get("review_configs", [])
                        preview = _parse_mcp_preview(action_requests)
                        
                        yield {
                            "type": "interrupt",
                            "content": "",
                            "event": {
                                "status": False,  # 用户是否决定
                                "action_requests": action_requests,
                                "review_configs": interrupt_value.get("review_configs", []),
                                "preview": preview,
                                "allowed_decisions": review_configs[0].get("allowed_decisions", [])
                            },
                        }

        # 处理工具内部流式进度
        elif mode == "custom":
            yield {"type": "event", "content": "", "event": chunk}


def _parse_mcp_preview(action_requests: list) -> list:
    """从 action_requests 里解析出 mcp_json，供前端渲染表格预览"""
    result = []
    for action in action_requests:
        args = action.get("arguments", {})
        mcp_str = args.get("mcp_json_str", "")
        
        # 兼容 VERIFY_SUCCESS: {...} 前缀
        if mcp_str.startswith("VERIFY_SUCCESS:"):
            mcp_str = mcp_str[len("VERIFY_SUCCESS:"):].strip()
            
        parsed = {}
        try:
            parsed = json.loads(mcp_str)
        except Exception:
            pass
            
        result.append({
            "tool_name": action.get("name"),
            "mcp_json_str": mcp_str,
            "mcp_preview": parsed,
        })
    return result


abstract_mcp_agent = AbstractMcpAgent()