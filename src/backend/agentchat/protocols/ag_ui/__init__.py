"""AG-UI 1.0 流式协议，业务鉴权和持久化仍由原接口负责。"""

from agentchat.protocols.ag_ui.streaming import protocol_stream

__all__ = ["protocol_stream"]
