from typing import Any, Awaitable, Callable


class FunctionTool:
    """A tool that wraps a function. In most cases, you should use  the `function_tool` helpers to
    create a FunctionTool, as they let you easily wrap a Python function.
    """
    def __init__(
        self,
        name: str,
        description: str,
        params_json_schema: dict[str, Any],
        on_run_tool: Callable[[str], Awaitable[Any]],
        strict_json_schema: bool = True,
    ):
        self.name = name
        self.description = description
        self.params_json_schema = params_json_schema
        self.on_run_tool = on_run_tool
        self.strict_json_schema = strict_json_schema