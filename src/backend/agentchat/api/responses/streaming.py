from collections.abc import Callable

import anyio
from fastapi.responses import StreamingResponse
from loguru import logger
from starlette.types import Receive


class WatchedStreamingResponse(StreamingResponse):
    """
    重写 StreamingResponse类 保证流式输出的时候可随时暂停
    """
    def __init__(
        self,
        content,
        callback: Callable | None = None,
        status_code: int = 200,
        headers = None,
        media_type: str | None = None,
        background = None,
    ):
        super().__init__(content, status_code, headers, media_type, background)

        self.callback = callback

    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        except BaseException:
            if self.callback:
                self.callback()
            raise
        finally:
            # 新版 ASGI 在发送失败时不一定调用断开监听，仍需关闭业务生成器。
            with anyio.CancelScope(shield=True):
                if close := getattr(self.body_iterator, "aclose", None):
                    await close()

    async def listen_for_disconnect(self, receive: Receive) -> None:
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                logger.info("http.disconnect. stop task and streaming")

                if self.callback:
                    self.callback()

                break
