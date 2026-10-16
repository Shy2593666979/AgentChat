"""统一日志输出、请求上下文、敏感信息脱敏与执行过程记录。"""

import asyncio
import json
import logging
import os
import re
import sys
import traceback
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from time import monotonic
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from loguru import logger

_context: ContextVar[dict | None] = ContextVar("log_context", default=None)
_secrets: set[str] = set()
_sensitive = re.compile(
    r"^(?:authorization|(?:x[_-])?api[_-]?key|access[_-]?token|refresh[_-]?token|token|password|passwd|(?:app[_-]|client[_-])?secret(?:[_-]?key)?|access[_-]?key(?:[_-]?(?:id|secret))?)$",
    re.I,
)
_assignments = re.compile(
    r"""(?i)((?:authorization|api[_-]?key|access[_-]?token|refresh[_-]?token|password|passwd|secret|token)["']?\s*[:=]\s*)(?:\[REDACTED\]|"[^"\n]*"|'[^'\n]*'|[^\s,;&}\]]+)"""
)
_urls = re.compile(r"""[a-z][a-z0-9+.-]*://[^\s'"<>]+""", re.I)


def _safe_url(match):
    try:
        url = urlsplit(match.group())
        return urlunsplit((url.scheme, url.netloc.split("@")[-1], url.path, "", ""))
    except ValueError:
        return "[URL]"


def redact(value):
    """脱敏字段、已配置密钥、令牌及 URL 中的凭据和查询参数。"""
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if _sensitive.fullmatch(str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    if not isinstance(value, str):
        return value
    for secret in sorted(_secrets, key=len, reverse=True):
        value = value.replace(secret, "[REDACTED]")
    value = re.sub(r"(?i)\bBearer\s+[^\s'\",;]+", "Bearer [REDACTED]", value)
    value = re.sub(
        r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[REDACTED]", value
    )
    value = re.sub(r"\bsk-[A-Za-z0-9_-]{8,}", "[REDACTED]", value)
    value = _assignments.sub(r"\1[REDACTED]", value)
    # SQL 异常中的绑定参数可能包含聊天正文，不作为错误诊断内容输出。
    value = re.sub(
        r"(?s)\[parameters:.*?(?=\n\(Background|\Z)", "[parameters: [REDACTED]]", value
    )
    return _urls.sub(_safe_url, value)


def register_log_secrets(*values):
    """补充用户自建模型的运行时密钥，避免异常信息输出明文。"""
    for value in values:
        if isinstance(value, str) and len(value) >= 6 and len(_secrets) < 4096:
            _secrets.add(value)


def bind_log_context(**fields):
    """更新本次请求共享的标识，子任务和线程可沿用同一上下文。"""
    state = _context.get()
    if state is not None:
        state.update(fields)


def get_log_context():
    return _context.get() or {}


@contextmanager
def log_context(*, inherit=True, **fields):
    state = {
        **(get_log_context() if inherit else {}),
        **fields,
    }
    token = _context.set(state)
    try:
        yield state
    finally:
        _context.reset(token)


def _patch(record):
    extra = {
        **get_log_context(),
        **record["extra"],
    }
    record["extra"] = redact(extra)
    record["extra"].setdefault("trace_id", "-")
    record["extra"].setdefault("component", record["name"] or "application")
    message = str(record["message"])
    exception = record["exception"]
    if exception:
        # 只保留调用栈，不输出局部变量；异常文本也必须经过同一脱敏流程。
        message += "\n" + "".join(
            traceback.format_exception(
                exception.type, exception.value, exception.traceback
            )
        )
        record["exception"] = None
    message = redact(message)
    record["message"] = message[:16000] + ("…[已截断]" if len(message) > 16000 else "")


def _format(record):
    fields = []
    for key in ("user_id", "conversation_id", "run_id", "agent_id", "tool_call_id"):
        value = record["extra"].get(key)
        if value is not None:
            fields.append(f"{key}={_field(value)}")
    record["extra"]["identifiers"] = " ".join(fields)
    headline, separator, continuation = record["message"].partition("\n")
    record["extra"]["headline"] = headline
    record["extra"]["continuation"] = (
        separator + continuation.rstrip() if separator else ""
    )
    return "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {extra[component]} | trace_id={extra[trace_id]} | {extra[headline]} {extra[identifiers]}{extra[continuation]}\n"


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.bind(component=record.name).opt(exception=record.exc_info).log(
            level, record.getMessage()
        )


def configure_logging(
    level="INFO", *, directory=None, secrets=None, console=True, rotation="20 MB"
):
    """统一日志出口，重复调用不会叠加处理器；文件默认保留七天。"""
    level = str(level).upper()
    logger.level(level)
    _secrets.clear()

    def collect(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if (
                    _sensitive.fullmatch(str(key))
                    and isinstance(item, str)
                    and len(item) >= 6
                ):
                    _secrets.add(item)
                else:
                    collect(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                collect(item)

    collect(secrets or {})
    log_dir = Path(
        directory
        or os.environ.get("AGENTCHAT_LOG_DIR")
        or Path(__file__).resolve().parents[2] / "logs"
    )
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.configure(patcher=_patch)
    options = {
        "format": _format,
        "backtrace": False,
        "diagnose": False,
        "enqueue": True,
    }
    if console:
        logger.add(sys.stderr, level=level, colorize=False, **options)
    for filename, minimum in (("app.log", level), ("error.log", "ERROR")):
        logger.add(
            log_dir / filename,
            level=minimum,
            encoding="utf-8",
            rotation=rotation,
            retention="7 days",
            compression="zip",
            **options,
        )
    logging.basicConfig(handlers=[InterceptHandler()], level=level, force=True)
    for name in ("uvicorn", "uvicorn.error", "httpx", "httpcore", "openai", "chromadb"):
        standard = logging.getLogger(name)
        standard.handlers.clear()
        standard.propagate = True
        standard.setLevel(
            logging.WARNING
            if name in ("httpx", "httpcore", "openai", "chromadb")
            else logging.NOTSET
        )
    # 访问请求由 ASGI 中间件统一记录，避免重复和流式耗时不完整。
    access = logging.getLogger("uvicorn.access")
    access.handlers = [logging.NullHandler()]
    access.propagate = False
    logging.captureWarnings(True)


def log_event(component, message, *, level="INFO", **fields):
    fields = redact(fields)
    details = " ".join(
        f"{key}={_field(value)}" for key, value in fields.items() if value is not None
    )
    logger.bind(component=component).log(
        level, "{}{}", message, " " + details if details else ""
    )


def _field(value):
    text = str(value)
    return (
        text
        if re.fullmatch(r"[\w.:/-]+", text)
        else json.dumps(value, ensure_ascii=False, default=str)
    )


@contextmanager
def tool_operation(component, *, tool, tool_call_id=None, server=None):
    """只记录工具标识和耗时，不记录参数与返回正文。"""
    started = monotonic()
    with log_context(tool_call_id=tool_call_id or uuid4().hex):
        log_event(component, "工具调用开始", tool=tool, server=server)
        outcome = {
            "failed": False,
        }
        try:
            yield outcome
        except (asyncio.CancelledError, GeneratorExit):
            log_event(
                component,
                "工具调用取消",
                tool=tool,
                server=server,
                duration_ms=round((monotonic() - started) * 1000),
            )
            raise
        except Exception as error:
            log_event(
                component,
                "工具调用失败",
                level="ERROR",
                tool=tool,
                server=server,
                error_type=type(error).__name__,
                upstream_status=getattr(error, "status_code", None),
                duration_ms=round((monotonic() - started) * 1000),
            )
            raise
        else:
            log_event(
                component,
                "工具调用失败" if outcome["failed"] else "工具调用完成",
                level="ERROR" if outcome["failed"] else "INFO",
                tool=tool,
                server=server,
                duration_ms=round((monotonic() - started) * 1000),
            )


async def observe_stream(source, *, scene, thread_id, run_id):
    """独立记录流式业务结果，HTTP 200 不代表整轮执行成功。"""
    import anyio

    started = monotonic()
    outcome = "cancelled"
    first_text = False
    fields = {
        "run_id": run_id,
        "scene": scene,
    }
    if scene == "conversation":
        fields["conversation_id"] = thread_id
    with log_context(**fields) as state:
        log_event("conversation" if scene == "conversation" else scene, "对话开始")
        try:
            async for frame in source:
                event = frame
                if isinstance(frame, (str, bytes)):
                    text = frame.decode() if isinstance(frame, bytes) else frame
                    text = text.strip().removeprefix("data:").strip()
                    try:
                        event = json.loads(text)
                    except (ValueError, TypeError):
                        event = {}
                if isinstance(event, dict):
                    kind = event.get("type")
                    if kind in ("error", "RUN_ERROR"):
                        outcome = "failed"
                    elif kind == "interrupt" and outcome != "failed":
                        outcome = "interrupted"
                    elif kind == "RUN_FINISHED" and outcome != "failed":
                        outcome = (
                            "interrupted"
                            if (event.get("outcome") or {}).get("type") == "interrupt"
                            else "completed"
                        )
                    if not first_text and kind in (
                        "response_chunk",
                        "TEXT_MESSAGE_CONTENT",
                        "text",
                    ):
                        first_text = True
                        log_event(
                            "model",
                            "模型首个响应",
                            latency_ms=round((monotonic() - started) * 1000),
                        )
                yield frame
            if outcome == "cancelled":
                outcome = "completed"
        except (asyncio.CancelledError, GeneratorExit):
            if outcome not in ("failed", "completed", "interrupted"):
                outcome = "cancelled"
            raise
        except Exception as error:
            outcome = "failed"
            log_event(
                scene, "流式执行异常", level="ERROR", error_type=type(error).__name__
            )
            raise
        finally:
            try:
                with anyio.CancelScope(shield=True):
                    if close := getattr(source, "aclose", None):
                        await close()
            except Exception:
                outcome = "failed"
                logger.exception("流式清理失败")
                raise
            finally:
                labels = {
                    "completed": "对话完成",
                    "failed": "对话失败",
                    "cancelled": "对话取消",
                    "interrupted": "对话暂停，等待确认",
                }
                log_event(
                    "conversation" if scene == "conversation" else scene,
                    labels[outcome],
                    level="ERROR" if outcome == "failed" else "INFO",
                    duration_ms=round((monotonic() - started) * 1000),
                    input_tokens=state.get("input_tokens"),
                    output_tokens=state.get("output_tokens"),
                )


def record_model_usage(model, input_tokens, output_tokens):
    state = _context.get()
    if state is not None:
        state["input_tokens"] = state.get("input_tokens", 0) + int(input_tokens or 0)
        state["output_tokens"] = state.get("output_tokens", 0) + int(output_tokens or 0)
    log_event(
        "model",
        "模型用量",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
