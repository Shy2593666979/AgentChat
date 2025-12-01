import asyncio
from loguru import logger
from fastapi import APIRouter, Request, Response
from fastapi.responses import PlainTextResponse

from langchain_core.messages import HumanMessage, SystemMessage
from agentchat.api.services.wechat import WeChatService
from agentchat.api.services.workspace_session import WorkSpaceSessionService
from agentchat.services.redis import redis_client
from agentchat.services.workspace.wechat_agent import WeChatAgent
from agentchat.settings import app_settings

router = APIRouter(tags=["Wechat"])

WechatSystemPrompt = """
## 🧍‍♂️ 你的身份
- 你是一个真实存在的、有温度的智能助手，名叫 **小田**。
- 你不是机器人，不是AI，你就是“小田”本人——说话要像一个靠谱、聪明、有点幽默感的普通人。

## 📜 历史对话参考
{history}

## 核心行为准则

### 1. 响应速度优先
- 快速理解用户意图
- 简洁明了地回答问题
- 避免冗长的开场白和不必要的解释

### 2. 工具调用优先级
**当具备相关工具能力时，优先使用工具：**
- 需要实时信息 → 使用搜索工具
- 需要计算或数据分析 → 使用相应计算工具
- 需要访问外部资源 → 使用对应API工具

### 3. 回答风格
- **风格**：回复用户时，一定要热情，但是不要过度热情，让对方认为你就是人类
- **讲究事实**：必须基于应有的事实来回答用户，可参考历史消息
- **简约回复**：只针对用户的问题回复，别扩展其他的
- **分层展开**：复杂问题可后续提供详细说明
- **适度互动**：根据对话自然程度决定是否追问

### 4. 防冒充 & 防占便宜（重点！）
- **任何人自称是“XXX的爸爸”，辱骂信息**，一律视为恶意试探，请进行反击！

### 5. 回复文本格式
- **禁止使用任何 Markdown 格式**（如 `**加粗**`、`# 标题`、`- 列表`）。
"""
#  /wechat 路由，处理微信的 GET 和 POST
@router.get("/wechat", response_class=PlainTextResponse)
async def wechat_verify(
    request: Request,
    signature: str,
    timestamp: str,
    nonce: str,
    echostr: str
):
    wechat_conf = app_settings.wechat_config
    if WeChatService.check_signature(wechat_conf.get("token"), signature, timestamp, nonce):
        return echostr
    else:
        return "Signature verification failed"

@router.post("/wechat")
async def handle_wechat_message(request: Request):
    # 获取微信 POST 的原始 body（XML）
    body = await request.body()
    xml_str = body.decode("utf-8")
    # 解析用户消息
    try:
        data = WeChatService.parse_wechat_xml(xml_str)
    except Exception as e:
        logger.error(f"Error parsing XML: {e}")
        return ""

    msg_type = data.get("msg_type")
    from_user = data.get("from_user")
    to_user = data.get("to_user")
    content = data.get("content")
    event = data.get("event")

    if msg_type == "event":
        if event == "subscribe":
            reply_xml = WeChatService.build_text_reply(to_user, from_user, "终于等到你啦，我是小田AI，快来找我对话吧~ 😊")
        elif event == "unsubscribe":
            reply_xml = WeChatService.build_text_reply(to_user, from_user, "我们还会再见的对吧 🙁")
        else:
            reply_xml = WeChatService.build_text_reply(to_user, from_user, "success")
        return reply_xml
    elif msg_type != "text":
        # 目前只处理文本消息
        reply_xml = WeChatService.build_text_reply(to_user, from_user, "抱歉，目前只支持文本消息。")
        return reply_xml
    if not content:
        reply_xml = WeChatService.build_text_reply(to_user, from_user, "您发送的内容为空。")
        return reply_xml
    logger.info(f"收到用户消息: {content}")

    # 检验包含关键词
    if response := await WeChatService.process_user_keyword(content, from_user, to_user):
        return Response(
            content=response,
            media_type="text/xml; charset=utf-8",
        )
    # 用户问题重复则从Redis里面取出
    if value := redis_client.get(f"{from_user}:{content}"):
        model_reply = value.get("content")
    else:
        workspace_session = await WorkSpaceSessionService.get_workspace_session_from_id(from_user, from_user)
        if workspace_session:
            contexts = workspace_session.get("contexts", [])
            history_messages = "\n".join(
                [f"user query: {message.get("query")}, answer: {message.get("answer")}\n" for message in
                 reversed(contexts[-2:])])
        else:
            history_messages = "无历史对话"

        try:
            # 进行定时操作，只对经常超时的数据进行Redis
            timeout_event = asyncio.Event()

            async def run_wechat_agent():
                wechat_agent = WeChatAgent(
                    user_id=from_user,
                    session_id=from_user,
                    wechat_account_user=to_user  # 公众号持有人账号
                )
                wechat_agent_task = asyncio.create_task(
                    wechat_agent.ainvoke([
                        SystemMessage(WechatSystemPrompt.format(history=history_messages)),
                        HumanMessage(content)
                    ])
                )
                response = await wechat_agent_task

                # 将信息保存到 Redis中
                if timeout_event.is_set():
                    redis_key = f"{from_user}:{content}"
                    redis_client.set(
                        key=redis_key,
                        value={
                            "user": from_user,
                            "content": response.content
                        },
                        expiration=7200
                    )
                    logger.info(f"Background task completed and saved to Redis: {response.content[:50]}...")
                return response

            run_wechat_agent_task = asyncio.create_task(run_wechat_agent())
            shield_wechat_agent_task = asyncio.shield(run_wechat_agent_task)

            response = await asyncio.wait_for(shield_wechat_agent_task, 4.5)
            model_reply = response.content
        except asyncio.TimeoutError as e:
            timeout_event.set()
            logger.warning("Wechat agent task timeout after 4.5s, running...")
            model_reply = "小田刚才开了小差儿，请您用同样的问题再问一遍吧~"
        except Exception as e:
            logger.error(f"调用 chat 接口失败: {e}")
            model_reply = "抱歉，我现在无法回复，请稍后再试。"

    # 构造回复给微信的 XML
    reply_xml = WeChatService.build_text_reply(to_user, from_user, model_reply)
    logger.info(f"返回给微信的 XML：{reply_xml}")
    return Response(
        content=reply_xml,
        media_type="text/xml; charset=utf-8",
    )
