from time import time
import traceback
from uuid import uuid4
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from loguru import logger

from agentchat.utils.contexts import set_trace_id_context


class TraceIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        trace_id = request.headers.get("x-b3-traceid", str(uuid4()))
        start_time = time()
        set_trace_id_context(trace_id)

        with logger.contextualize(trace_id=trace_id):
            try:
                response = await call_next(request)
            except Exception:
                logger.error(f"exception_traceback: {traceback.format_exc()}")
                response = JSONResponse(
                    status_code=500,
                    content={"code": -1, "error_msg": "10500: 系统错误，请重试"}
                )

            response.headers["X-Trace-ID"] = trace_id
            logger.info(
                f'{request.method} {request.url.path} {response.status_code} time_cost={(time() - start_time) * 1000:.3f}ms')
            return response
