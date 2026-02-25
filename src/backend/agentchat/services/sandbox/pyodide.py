"""Python wrapper that calls pyodide & deno for code execution."""

import asyncio
import dataclasses
import json
import logging
import subprocess
import time
from typing import Annotated, Any, Literal

from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, InjectedToolCallId
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

Status = Literal["success", "error"]


@dataclasses.dataclass(kw_only=True)
class CodeExecutionResult:
    """代码执行结果的容器。"""

    result: Any = None
    stdout: str | None = None
    stderr: str | None = None
    status: Status
    execution_time: float
    session_metadata: dict | None = None
    session_bytes: bytes | None = None


# 发布的包名
PKG_NAME = "jsr:@langchain/pyodide-sandbox@0.0.4"


def build_permission_flag(
    flag: str,
    *,
    value: bool | list[str],
) -> str | None:
    """根据提供的设置构建权限标志字符串。

    参数：
        flag: 基础权限标志（例如，“--allow-read”）。
        value: 布尔值（True 表示无限制访问，False 表示没有访问权限）或允许的项目列表。

    返回：
        带有权限标志和项目的字符串，或者如果不应添加权限，则为 None。
    """
    if value is True:
        return flag
    if isinstance(value, list) and value:
        return f"{flag}={','.join(value)}"
    return None


class BasePyodideSandbox:
    """PyodideSandbox 实现的基类。

    此类提供同步和异步 PyodideSandbox 实现的公共初始化和配置逻辑。

    沙箱利用 Deno 的安全模型创建一个安全的运行时，用于执行不受信任的 Python 代码。它通过生成一个加载 Pyodide（编译为 WebAssembly 的 Python）并在隔离环境中执行提供的代码的 Deno 子进程来工作。

    安全特性：
    - 可配置的文件系统、网络和环境访问权限
    - 支持执行超时，以防止无限循环
    - 内存使用监控
    - 通过 Deno 的安全沙箱实现进程隔离

    沙箱通过其初始化程序支持细粒度权限控制：
    - 限制网络访问到特定域
    - 限制文件系统访问到特定目录
    - 控制环境变量访问
    - 防止子进程执行和 FFI
    """

    def __init__(
        self,
        *,
        stateful: bool = False,
        allow_env: list[str] | bool = False,
        allow_read: list[str] | bool = False,
        allow_write: list[str] | bool = False,
        allow_net: list[str] | bool = False,
        allow_run: list[str] | bool = False,
        allow_ffi: list[str] | bool = False,
        node_modules_dir: str = "auto",
        skip_deno_check: bool = False,
    ) -> None:
        """使用特定的 Deno 权限初始化沙箱。

        此方法配置将执行 Python 代码的 Deno 子进程的安全权限。默认情况下，所有权限均禁用（False），以确保最大安全性。权限可以根据执行代码的需求选择性启用。

        参数：
            stateful: 是否使用状态保持会话。如果为 True，则 `sandbox.execute`
                将包括会话元数据和包含会话状态（变量、导入等）的会话字节。这样可以在执行之间保存和重用会话状态。

            allow_env: 环境变量访问配置：
                - False: 不允许环境访问（默认，最安全）
                - True: 允许访问所有环境变量
                - List[str]: 限制为特定环境变量的访问，例如
                  ["PATH", "PYTHONPATH"]

            allow_read: 文件系统读取访问配置：
                - False: 不允许文件系统读取访问（默认，最安全）
                - True: 允许无限制读取文件系统
                - List[str]: 限制为特定路径的读取访问，例如
                  ["/tmp/sandbox", "./data"]

                  默认允许从 node_modules 读取

            allow_write: 文件系统写入访问配置：
                - False: 不允许文件系统写入访问（默认，最安全）
                - True: 允许无限制写入文件系统
                - List[str]: 限制为特定路径的写入访问，例如
                  ["/tmp/sandbox/output"]

                  默认允许写入 node_modules

            allow_net: 网络访问配置：
                - False: 不允许网络访问（默认，最安全）
                - True: 允许无限制的网络访问
                - List[str]: 限制为特定域/IP 的网络访问，例如
                  ["api.example.com", "data.example.org:8080"]

            allow_run: 子进程执行配置：
                - False: 不允许子进程执行（默认，最安全）
                - True: 允许无限制的子进程执行
                - List[str]: 限制为特定命令的子进程执行，例如
                  ["python", "git"]

            allow_ffi: 外部函数接口访问配置：
                - False: 不允许 FFI 访问（默认，最安全）
                - True: 允许无限制的 FFI 访问
                - List[str]: 限制为特定库的 FFI 访问，例如
                  ["/usr/lib/libm.so"]

            node_modules_dir: Node.js 模块的目录。设置为 "auto" 以使用 Deno 模块的默认目录。
            skip_deno_check: 如果为 True，则跳过 Deno 安装检查。
        """
        self.stateful = stateful
        # 配置权限
        self.permissions = []

        if not skip_deno_check:
            # 检查 Deno 是否已安装
            try:
                subprocess.run(["deno", "--version"], check=True, capture_output=True)  # noqa: S607, S603
            except subprocess.CalledProcessError as e:
                msg = "Deno 已安装，但运行它失败。"
                raise RuntimeError(msg) from e
            except FileNotFoundError as e:
                msg = "Deno 没有安装或不在 PATH 中。"
                raise RuntimeError(msg) from e

        # 定义权限配置：
        # 每个元组包含 (flag, setting, defaults)
        perm_defs = [
            ("--allow-env", allow_env, None),
            # 对于文件系统权限，如果没有指定权限，
            # 强制使用 node_modules
            ("--allow-read", allow_read, ["node_modules"]),
            ("--allow-write", allow_write, ["node_modules"]),
            ("--allow-net", allow_net, None),
            ("--allow-run", allow_run, None),
            ("--allow-ffi", allow_ffi, None),
        ]

        self.permissions = []
        for flag, value, defaults in perm_defs:
            perm = build_permission_flag(flag, value=value)
            if perm is None and defaults is not None:
                default_value = ",".join(defaults)
                perm = f"{flag}={default_value}"
            if perm:
                self.permissions.append(perm)

        self.permissions.append(f"--node-modules-dir={node_modules_dir}")

    def _build_command(
        self,
        code: str,
        *,
        session_bytes: bytes | None = None,
        session_metadata: dict | None = None,
        memory_limit_mb: int | None = None,
    ) -> list[str]:
        """构建带有所有必要参数的 Deno 命令。

        参数：
            code: 要执行的 Python 代码
            session_bytes: 可选的会话状态字节
            session_metadata: 可选的会话元数据
            memory_limit_mb: 可选的内存限制（以 MB 为单位）

        返回：
            子进程执行的命令参数列表
        """
        cmd = [
            "deno",
            "run",
        ]

        # 应用权限
        cmd.extend(self.permissions)

        # Deno 使用 V8 标志 --max-old-space-size 限制内存使用（以 MB 为单位）
        if memory_limit_mb is not None and memory_limit_mb > 0:
            cmd.append(f"--v8-flags=--max-old-space-size={memory_limit_mb}")

        # 添加 JavaScript 包装脚本的路径
        cmd.append(PKG_NAME)

        # 添加脚本路径和代码
        cmd.extend(["-c", code])

        if self.stateful:
            cmd.extend(["-s"])

        if session_bytes:
            # 将字节转换为整数列表再转为 JSON 字符串
            bytes_array = list(session_bytes)
            cmd.extend(["-b", json.dumps(bytes_array)])

        if session_metadata:
            cmd.extend(["-m", json.dumps(session_metadata)])

        return cmd


class PyodideSandbox(BasePyodideSandbox):
    """在沙箱 Deno 环境中异步执行 Python 代码的实现。"""

    async def execute(
        self,
        code: str,
        *,
        session_bytes: bytes | None = None,
        session_metadata: dict | None = None,
        timeout_seconds: float | None = None,
        memory_limit_mb: int | None = None,
    ) -> CodeExecutionResult:
        """异步在沙箱 Deno 子进程中执行 Python 代码。

        此方法生成一个 Deno 子进程，该进程加载 Pyodide（编译为 WebAssembly 的 Python），
        并在沙箱环境中执行提供的代码。执行受初始化中配置的沙箱权限和作为参数提供的资源限制的约束。

        参数：
            code: 在沙箱中执行的 Python 代码
            session_bytes: 可选的会话状态字节
            session_metadata: 可选的会话元数据
            timeout_seconds: 最大执行时间（以秒为单位）
            memory_limit_mb: 最大内存使用量（以 MB 为单位）

        返回：
            包含执行结果和元数据的 CodeExecutionResult
        """
        start_time = time.time()
        stdout = ""
        stderr = ""
        result = None
        status: Literal["success", "error"] = "success"

        cmd = self._build_command(
            code,
            session_bytes=session_bytes,
            session_metadata=session_metadata,
            memory_limit_mb=memory_limit_mb,
        )

        # 创建并运行子进程
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            # 等待进程与超时
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds,
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace")

            if stdout:
                # stdout 编码了来自沙箱的完整结果。
                # 包括 stdout、stderr 和 json 结果。
                full_result = json.loads(stdout)
                stdout = full_result.get("stdout", None)
                stderr = full_result.get("stderr", None)
                result = full_result.get("result", None)
                status = "success" if full_result.get("success", False) else "error"
                session_metadata = full_result.get("sessionMetadata", None)
                # 将 Uint8Array 转换为 Python 字节
                session_bytes_array = full_result.get("sessionBytes", None)
                session_bytes = (
                    bytes(session_bytes_array) if session_bytes_array else None
                )
            else:
                stderr = stderr_bytes.decode("utf-8", errors="replace")
                status = "error"
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            status = "error"
            stderr = f"执行超时，超过 {timeout_seconds} 秒"
        except asyncio.CancelledError:
            # 可选：如果需要，记录取消
            pass
        end_time = time.time()

        return CodeExecutionResult(
            status=status,
            execution_time=end_time - start_time,
            stdout=stdout or None,
            stderr=stderr or None,
            result=result,
            session_metadata=session_metadata,
            session_bytes=session_bytes,
        )


class SyncPyodideSandbox(BasePyodideSandbox):
    """提供 PyodideSandbox 功能的同步接口。"""

    def execute(
        self,
        code: str,
        *,
        session_bytes: bytes | None = None,
        session_metadata: dict | None = None,
        timeout_seconds: float | None = None,
        memory_limit_mb: int | None = None,
    ) -> CodeExecutionResult:
        """在沙箱 Deno 子进程中同步执行 Python 代码。

        此方法提供与 PyodideSandbox.execute() 相同的功能，但以同步/阻塞方式。

        参数：
            code: 在沙箱中执行的 Python 代码
            session_bytes: 可选的会话状态字节
            session_metadata: 可选的会话元数据
            timeout_seconds: 最大执行时间（以秒为单位）
            memory_limit_mb: 最大内存使用量（以 MB 为单位）

        返回：
            包含执行结果和元数据的 CodeExecutionResult
        """
        start_time = time.time()
        stdout = ""
        result = None
        stderr: str
        status: Literal["success", "error"]

        cmd = self._build_command(
            code,
            session_bytes=session_bytes,
            session_metadata=session_metadata,
            memory_limit_mb=memory_limit_mb,
        )

        try:
            # 运行子进程与超时
            # 因为 cmd 是安全地构建的，所以忽略 S603。
            # 不受信的输入来自 `code` 参数，应该正确转义，因为我们并没有使用 shell=True。
            process = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=False,  # 保持为字节以进行正确解码
                timeout=timeout_seconds,
                check=False,  # 不在非零退出时引发
            )

            stdout_bytes = process.stdout
            stderr_bytes = process.stderr

            stdout = stdout_bytes.decode("utf-8", errors="replace")

            if stdout:
                # stdout 编码了来自沙箱的完整结果
                # 包括 stdout、stderr 和 json 结果
                full_result = json.loads(stdout)
                stdout = full_result.get("stdout", None)
                stderr = full_result.get("stderr", None)
                result = full_result.get("result", None)
                status = "success" if full_result.get("success", False) else "error"
                session_metadata = full_result.get("sessionMetadata", None)
                # 将 Uint8Array 转换为 Python 字节
                session_bytes_array = full_result.get("sessionBytes", None)
                session_bytes = (
                    bytes(session_bytes_array) if session_bytes_array else None
                )
            else:
                stderr = stderr_bytes.decode("utf-8", errors="replace")
                status = "error"

        except subprocess.TimeoutExpired:
            status = "error"
            stderr = f"执行超时，超过 {timeout_seconds} 秒"

        end_time = time.time()

        return CodeExecutionResult(
            status=status,
            execution_time=end_time - start_time,
            stdout=stdout or None,
            stderr=stderr or None,
            result=result,
            session_metadata=session_metadata,
            session_bytes=session_bytes,
        )


class PyodideSandboxTool(BaseTool):
    """在 PyodideSandbox 中运行 Python 代码的工具。

    如果使用有状态的沙箱（PyodideSandboxTool(stateful=True)），
    代码执行之间的状态（变量、导入、
    定义等）将使用 LangGraph 选区保存。

    !!! 重要
        当您使用有状态的沙箱时，该工具只能在带有检查点的 LangGraph 图内使用，
        必须与预构建的 `create_react_agent` 或 `ToolNode` 一起使用。

    示例：无状态沙箱的用法

        ```python
        from langgraph.prebuilt import create_react_agent
        from langchain_sandbox import PyodideSandboxTool

        tool = PyodideSandboxTool(allow_net=True)
        agent = create_react_agent(
            "anthropic:claude-3-7-sonnet-latest",
            tools=[tool],
        )
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "what's 5 + 7?"}]},
        )
        ```

    示例：有状态沙箱的用法

        ```python
        from langgraph.prebuilt import create_react_agent
        from langgraph.prebuilt.chat_agent_executor import AgentState
        from langgraph.checkpoint.memory import InMemorySaver
        from langchain_sandbox import PyodideSandboxTool, PyodideSandbox

        class State(AgentState):
            session_bytes: bytes
            session_metadata: dict

        tool = PyodideSandboxTool(stateful=True, allow_net=True)
        agent = create_react_agent(
            "anthropic:claude-3-7-sonnet-latest",
            tools=[tool],
            checkpointer=InMemorySaver(),
            state_schema=State
        )
        result = await agent.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": "what's 5 + 7? save result as 'a'"}
                ],
                "session_bytes": None,
                "session_metadata": None
            },
            config={"configurable": {"thread_id": "123"}},
        )
        second_result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "what's the sine of 'a'?"}]},
            config={"configurable": {"thread_id": "123"}},
        )
        ```
    """

    name: str = "python_code_sandbox"
    description: str = (
        "A secure Python code sandbox. Use this to execute python commands.\n"
        "- Input should be a valid python command.\n"
        "- To return output, you should print it out with `print(...)`.\n"
        "- Don't use f-strings when printing outputs.\n"
        "- If you need to make web requests, use `httpx.AsyncClient`."
    )

    # Mirror the PyodideSandbox constructor arguments
    stateful: bool = False
    allow_env: list[str] | bool = False
    allow_read: list[str] | bool = False
    allow_write: list[str] | bool = False
    allow_net: list[str] | bool = False
    allow_run: list[str] | bool = False
    allow_ffi: list[str] | bool = False
    timeout_seconds: float | None
    """代码执行的超时（以秒为单位）。默认设置为 60 秒。"""
    node_modules_dir: str = "auto"

    _sandbox: PyodideSandbox
    _sync_sandbox: SyncPyodideSandbox


    def __init__(
        self,
        *,
        stateful: bool = False,
        timeout_seconds: float | None = 60,
        allow_net: list[str] | bool = False,
        **kwargs: dict[str, Any],
    ) -> None:
        """初始化工具。

        参数：
            stateful: 是否使用有状态的沙箱。如果为 True，则 `sandbox.execute`
                将包含会话元数据和包含会话状态的会话字节（变量、导入等）。
                这允许在执行之间保存和重用会话状态。
            timeout_seconds: 代码执行的超时（以秒为单位）。
            allow_net: 配置网络访问。如果设置为 True，允许任何网络访问，
                包括您可能不希望暴露给恶意演员的内部网络地址。
                根据您的用例，您可以将网络访问限制为仅需的 URL（例如，设置 micropip / pyodide 所需的）。
                更多详细信息请参阅 pyodide 文档。
            **kwargs: 其他属性将传递给 PyodideSandbox
        """
        super().__init__(
            stateful=stateful,
            timeout_seconds=timeout_seconds,
            allow_net=allow_net,
            **kwargs,
        )

        if self.stateful:
            try:
                from langgraph.prebuilt import InjectedState
            except ImportError as e:
                error_msg = (
                    "使用有状态沙箱时需要 'langgraph' 包。"
                    " 请使用 'pip install langgraph' 安装它。"
                )
                raise ImportError(error_msg) from e

            class PyodideSandboxToolInput(BaseModel):
                """要在沙箱中执行的 Python 代码。"""

                code: str = Field(description="要执行的代码。")
                # 这些字段将在 LLM 处理中被忽略
                # 由 LangGraph 的 ToolNode 自动注入
                state: Annotated[dict[str, Any] | BaseModel, InjectedState]
                tool_call_id: Annotated[str, InjectedToolCallId]

        else:

            class PyodideSandboxToolInput(BaseModel):
                """要在沙箱中执行的 Python 代码。"""

                code: str = Field(description="要执行的代码。")

        self.args_schema: type[BaseModel] = PyodideSandboxToolInput
        self._sandbox = PyodideSandbox(
            stateful=self.stateful,
            allow_env=self.allow_env,
            allow_read=self.allow_read,
            allow_write=self.allow_write,
            allow_net=self.allow_net,
            allow_run=self.allow_run,
            allow_ffi=self.allow_ffi,
            node_modules_dir=self.node_modules_dir,
        )
        # 初始化同步沙箱，跳过 Deno 检查，因为异步沙箱已经检查过了
        self._sync_sandbox = SyncPyodideSandbox(
            stateful=self.stateful,
            allow_env=self.allow_env,
            allow_read=self.allow_read,
            allow_write=self.allow_write,
            allow_net=self.allow_net,
            allow_run=self.allow_run,
            allow_ffi=self.allow_ffi,
            node_modules_dir=self.node_modules_dir,
            skip_deno_check=True,  # 跳过 Deno 检查，因为异步沙箱已经检查过
        )

    def _run(
        self,
        code: str,
        state: dict[str, Any] | BaseModel | None = None,
        tool_call_id: str | None = None,
        config: RunnableConfig | None = None,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> Any:  # noqa: ANN401
        """在同步状态下使用该工具。"""
        if self.stateful:
            required_keys = {"session_bytes", "session_metadata", "messages"}
            actual_keys = set(state) if isinstance(state, dict) else set(state.__dict__)
            if missing_keys := required_keys - actual_keys:
                error_msg = (
                    "输入状态缺少 "
                    f"以下必要键：{missing_keys}"
                )
                raise ValueError(error_msg)

            if isinstance(state, dict):
                session_bytes = state["session_bytes"]
                session_metadata = state["session_metadata"]
            else:
                session_bytes = state.session_bytes
                session_metadata = state.session_metadata

            result = self._sync_sandbox.execute(
                code,
                session_bytes=session_bytes,
                session_metadata=session_metadata,
                timeout_seconds=self.timeout_seconds,
            )
        else:
            result = self._sync_sandbox.execute(
                code, timeout_seconds=self.timeout_seconds
            )

        if result.stderr:
            tool_result = f"执行期间出错：{result.stderr}"
        else:
            tool_result = result.stdout

        if self.stateful:
            from langgraph.types import Command

            # 如果该工具与有状态沙箱一起使用，
            # 我们需要使用新的会话字节和元数据更新图状态
            return Command(
                update={
                    "session_bytes": result.session_bytes,
                    "session_metadata": result.session_metadata,
                    "messages": [
                        ToolMessage(
                            content=tool_result,
                            tool_call_id=tool_call_id,
                        )
                    ],
                }
            )

        return tool_result

    async def _arun(
        self,
        code: str,
        state: dict[str, Any] | BaseModel | None = None,
        tool_call_id: str | None = None,
        config: RunnableConfig | None = None,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ) -> Any:  # noqa: ANN401
        """在异步状态下使用该工具。"""
        if self.stateful:
            required_keys = {"session_bytes", "session_metadata", "messages"}
            actual_keys = set(state) if isinstance(state, dict) else set(state.__dict__)
            if missing_keys := required_keys - actual_keys:
                error_msg = (
                    "输入状态缺少 "
                    f"以下必要键：{missing_keys}"
                )
                raise ValueError(error_msg)

            if isinstance(state, dict):
                session_bytes = state["session_bytes"]
                session_metadata = state["session_metadata"]
            else:
                session_bytes = state.session_bytes
                session_metadata = state.session_metadata

            result = await self._sandbox.execute(
                code,
                session_bytes=session_bytes,
                session_metadata=session_metadata,
                timeout_seconds=self.timeout_seconds,
            )
        else:
            result = await self._sandbox.execute(
                code, timeout_seconds=self.timeout_seconds
            )

        if result.stderr:
            tool_result = f"执行期间出错：{result.stderr}"
        else:
            tool_result = result.stdout

        if self.stateful:
            from langgraph.types import Command

            # 如果该工具与有状态沙箱一起使用，
            # 我们需要使用新的会话字节和元数据更新图状态
            return Command(
                update={
                    "session_bytes": result.session_bytes,
                    "session_metadata": result.session_metadata,
                    "messages": [
                        ToolMessage(
                            content=tool_result,
                            tool_call_id=tool_call_id,
                        )
                    ],
                }
            )

        return tool_result