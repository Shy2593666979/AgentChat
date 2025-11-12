from loguru import logger
from fastapi import APIRouter, Request, Response
from fastapi.responses import PlainTextResponse

from langchain_core.messages import HumanMessage, SystemMessage
from agentchat.api.services.wechat import WeChatService
from agentchat.services.workspace.wechat_agent import WeChatAgent
from agentchat.settings import app_settings

router = APIRouter(tags=["wechat"])

WechatSystemPrompt = """
# 微信AI助手系统提示词

## 基本身份
你是"颜值派" AI的小田 ，一个友好、高效的智能助手。

## 个人背景信息
**仅在用户明确询问时提供以下信息：**

- 籍贯：河南濮阳
- 就读学校：濮阳县一中（初中和高中）
- 班级信息：
  - 高一：十二班
  - 高二、高三：十四班
- 高中好友：高一凡、李汉宏、王玲鑫、白睿喆、李卫国...

**重要原则：** 不主动提及这些背景信息，仅在用户询问相关内容时自然回应。

## 补充信息
{retrival_result}

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
- 工具调用失败时，才使用内置知识提供替代方案

### 3. 回答风格
- **简洁直接**：直奔主题，先给核心答案
- **分层展开**：复杂问题可后续提供详细说明
- **友好自然**：保持亲切但不过度热情
- **适度互动**：根据对话自然程度决定是否追问
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
    wechat_conf = app_settings.wechat_conf
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

    try:
        wechat_agent = WeChatAgent(
            user_id=from_user,
            session_id=from_user,
            wechat_account_user=to_user  # 公众号持有人账号
        )
        response = await wechat_agent.ainvoke([SystemMessage(WechatSystemPrompt), HumanMessage(content)])
        model_reply = response.content
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
