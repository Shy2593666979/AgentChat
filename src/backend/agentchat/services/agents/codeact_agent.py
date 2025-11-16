import inspect
from typing import List
from typing import Any, Awaitable, Callable, Optional, Sequence, Type, TypeVar, Union
from langgraph.types import Command
from langchain_core.messages import BaseMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import StructuredTool
from langchain_core.tools import tool as create_tool
from langgraph.graph import END, START, MessagesState, StateGraph

from agentchat.core.models.manager import ModelManager
from agentchat.services.sandbox import PyodideSandbox
from agentchat.utils.extract import extract_and_combine_codeblocks

EvalFunction = Callable[[str, dict[str, Any]], tuple[str, dict[str, Any]]]
EvalCoroutine = Callable[[str, dict[str, Any]], Awaitable[tuple[str, dict[str, Any]]]]

class CodeActState(MessagesState):
    """State for CodeAct agent."""

    script: Optional[str]
    """The Python code script to be executed."""
    context: dict[str, Any]
    """Dictionary containing the execution context with available tools and variables."""


StateSchema = TypeVar("StateSchema", bound=CodeActState)
StateSchemaType = Type[StateSchema]


def create_default_prompt(tools: list[StructuredTool], base_prompt: Optional[str] = None):
    """Create default prompt for the CodeAct agent."""
    tools = [t if isinstance(t, StructuredTool) else create_tool(t) for t in tools]
    prompt = f"{base_prompt}\n\n" if base_prompt else ""
    prompt += """You will be given a task to perform. You should output either
- a Python code snippet that provides the solution to the task, or a step towards the solution. Any output you want to extract from the code should be printed to the console. Code should be output in a fenced code block.
- text to be shown directly to the user, if you want to ask for more information or provide the final answer.

In addition to the Python Standard Library, you can use the following functions:
"""

    for tool in tools:
        prompt += f'''
def {tool.name}{str(inspect.signature(tool.func))}:
    """{tool.description}"""
    ...
'''

    prompt += """

Variables defined at the top level of previous code snippets can be referenced in your code.

Reminder: use Python code snippets to call tools"""
    return prompt


class CodeActAgent:

    def __init__(self, tools, user_id):
        self.tools = tools
        self.user_id = user_id
        self.coder_model = ModelManager.get_conversation_model()

        self.setup_codeact_agent()


    def setup_codeact_agent(self):
        sandbox = PyodideSandbox(allow_net=True)
        eval_fn = self.create_pyodide_eval_fn(sandbox)
        self.codeact_agent = self.create_codeact_agent(self.coder_model, self.tools, eval_fn)


    async def astream(self, messages: List[BaseMessage]):

        async for typ, chunk in self.codeact_agent.astream(
                {"messages": messages},
                stream_mode=["values", "messages"],
        ):
            if typ == "messages":
                yield chunk[0].content
            elif typ == "values":
                yield chunk

    async def ainvoke(self, messages: List[BaseMessage]):
        pass

    def create_pyodide_eval_fn(self, sandbox: PyodideSandbox) -> EvalCoroutine:
        """Create an eval_fn that uses PyodideSandbox.
        """

        async def async_eval_fn(
                code: str, _locals: dict[str, Any]
        ) -> tuple[str, dict[str, Any]]:
            # Create a wrapper function that will execute the code and return locals
            wrapper_code = f"""
def execute():
    try:
        # Execute the provided code
{"\n".join(" " * 8 + line for line in code.strip().split("\n"))}
        return locals()
    except Exception as e:
        return {{"error": str(e)}}

execute()
    """
            # Convert functions in _locals to their string representation
            context_setup = ""
            for key, value in _locals.items():
                if callable(value):
                    # Get the function's source code
                    src = inspect.getsource(value)
                    context_setup += f"\n{src}"
                else:
                    context_setup += f"\n{key} = {repr(value)}"

            try:
                # Execute the code and get the result
                response = await sandbox.execute(
                    code=context_setup + "\n\n" + wrapper_code,
                )
                # Check if execution was successful
                if response.stderr:
                    return f"Error during execution: {response.stderr}", {}

                # Get the output from stdout
                output = (
                    response.stdout
                    if response.stdout
                    else "<Code ran, no output printed to stdout>"
                )
                result = response.result

                # If there was an error in the result, return it
                if isinstance(result, dict) and "error" in result:
                    return f"Error during execution: {result['error']}", {}

                # Get the new variables by comparing with original locals
                new_vars = {
                    k: v
                    for k, v in result.items()
                    if k not in _locals and not k.startswith("_")
                }
                return output, new_vars

            except Exception as e:
                return f"Error during PyodideSandbox execution: {repr(e)}", {}

        return async_eval_fn


    def create_codeact_agent(
        self,
        model: BaseChatModel,
        tools: Sequence[Union[StructuredTool, Callable]],
        eval_fn: Union[EvalFunction, EvalCoroutine],
        *,
        prompt: Optional[str] = None,
        state_schema: StateSchemaType = CodeActState,
    ) -> StateGraph:
        """Create a CodeAct agent.

        Args:
            model: The language model to use for generating code
            tools: List of tools available to the agent. Can be passed as python functions or StructuredTool instances.
            eval_fn: Function or coroutine that executes code in a sandbox. Takes code string and locals dict,
                returns a tuple of (stdout output, new variables dict)
            prompt: Optional custom system prompt. If None, uses default prompt.
                To customize default prompt you can use `create_default_prompt` helper:
                `create_default_prompt(tools, "You are a helpful assistant.")`
            state_schema: The state schema to use for the agent.

        Returns:
            A StateGraph implementing the CodeAct architecture
        """
        tools = [t if isinstance(t, StructuredTool) else create_tool(t) for t in tools]

        if prompt is None:
            prompt = create_default_prompt(tools)

        # Make tools available to the code sandbox
        tools_context = {tool.name: tool.func for tool in tools}

        def call_model(state: StateSchema) -> Command:
            messages = [{"role": "system", "content": prompt}] + state["messages"]
            response = model.invoke(messages)
            # Extract and combine all code blocks
            code = extract_and_combine_codeblocks(response.content)
            if code:
                return Command(goto="sandbox", update={"messages": [response], "script": code})
            else:
                # no code block, end the loop and respond to the user
                return Command(update={"messages": [response], "script": None})

        # If eval_fn is a async, we define async node function.
        if inspect.iscoroutinefunction(eval_fn):

            async def sandbox(state: StateSchema):
                existing_context = state.get("context", {})
                context = {**existing_context, **tools_context}
                # Execute the script in the sandbox
                output, new_vars = await eval_fn(state["script"], context)
                new_context = {**existing_context, **new_vars}
                return {
                    "messages": [{"role": "user", "content": output}],
                    "context": new_context,
                }
        else:

            def sandbox(state: StateSchema):
                existing_context = state.get("context", {})
                context = {**existing_context, **tools_context}
                # Execute the script in the sandbox
                output, new_vars = eval_fn(state["script"], context)
                new_context = {**existing_context, **new_vars}
                return {
                    "messages": [{"role": "user", "content": output}],
                    "context": new_context,
                }

        agent = StateGraph(state_schema)
        agent.add_node(call_model, destinations=(END, "sandbox"))
        agent.add_node(sandbox)
        agent.add_edge(START, "call_model")
        agent.add_edge("sandbox", "call_model")
        return agent.compile()
