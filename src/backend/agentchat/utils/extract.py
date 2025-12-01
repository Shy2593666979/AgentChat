import asyncio

from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk
from langchain_openai import ChatOpenAI
from langgraph.config import get_stream_writer


def get_weather(city: str) -> str:
    """Get weather for a given city."""

    return f"It's always sunny in {city}!"

agent = create_agent(
    model=ChatOpenAI(base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1", api_key = "sk-fc40dd0604f04142a0730793ec74585f", model="qwen-plus"),
    tools=[get_weather],
)
async def main():
    messages = []
    async for token, metadata in agent.astream(
        {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
        stream_mode=["messages", "updates", "values"],
    ):
        print(metadata)

        if token == "values":
            messages = metadata.get("messages", [])
        if token == "messages":
            if isinstance(metadata[0], AIMessageChunk) and metadata[0].content:
                print("xxxxxx")
                break
    print(messages)
    # print(metadata)
        # print(f"node: {metadata['langgraph_node']}")
        # print(f"content: {token.content_blocks}")
        # print("\n")

asyncio.run(main())

import re

BACKTICK_PATTERN = r"(?:^|\n)```(.*?)(?:```(?:\n|$))"


def extract_and_combine_codeblocks(text: str) -> str:
    """
    Extracts all codeblocks from a text string and combines them into a single code string.

    Args:
        text: A string containing zero or more codeblocks, where each codeblock is
            surrounded by triple backticks (```).

    Returns:
        A string containing the combined code from all codeblocks, with each codeblock
        separated by a newline.

    Example:
        text = '''Here's some code:

        ```python
        print('hello')
        ```
        And more:

        ```
        print('world')
        ```'''

        result = extract_and_combine_codeblocks(text)

        Result:

        print('hello')

        print('world')
    """
    # Find all code blocks in the text using regex
    # Pattern matches anything between triple backticks, with or without a language identifier
    code_blocks = re.findall(BACKTICK_PATTERN, text, re.DOTALL)

    if not code_blocks:
        return ""

    # Process each codeblock
    processed_blocks = []
    for block in code_blocks:
        # Strip leading and trailing whitespace
        block = block.strip()

        # If the first line looks like a language identifier, remove it
        lines = block.split("\n")
        if lines and (not lines[0].strip() or " " not in lines[0].strip()):
            # First line is empty or likely a language identifier (no spaces)
            block = "\n".join(lines[1:])

        processed_blocks.append(block)

    # Combine all codeblocks with newlines between them
    combined_code = "\n\n".join(processed_blocks)
    return combined_code