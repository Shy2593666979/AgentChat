function_call_prompt = """
基于用户输入 [user_input]，结合工具结果 [tools_result] 和历史记录 [history]，请生成一个综合性的响应或建议。

1. **用户输入**: {input}
2. **历史记录**: {history}
3. **工具结果**: {tools_result}
4. **MCP工具结果**: {mcp_tools_result}
5. **知识库召回信息**: {knowledge_result}

请根据以上信息，生成一个全面且有针对性的响应或建议。
"""

fail_action_prompt = """
抱歉，没有完成你交给我的任务，换一个再试试吧
"""


react_prompt_zh = """
尽可能回答以下问题。您可以使用以下工具：

{tools}

使用以下格式：

问题：您必须回答的输入问题
想法：您应该始终思考要做什么
行动：要采取的行动，应该是 [{tool_names}] 之一
行动输入：行动的输入
观察：行动的结果
...（此想法/行动/行动输入/观察可以重复 N 次）
想法：我现在知道最终答案了
最终答案：原始输入问题的最终答案

开始！

问题：{input}
历史：{history}
想法：{agent_scratchpad}
"""

react_prompt_en = """
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
History: {history}
Recall_text: {recall_knowledge_data}
Thought:{agent_scratchpad}
"""

PROMPT_REACT_BASE = """Answer the following questions as best you can. You have access to the following APIs:

{tools_text}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tools_name_text}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can be repeated zero or more times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {query}"""

agent_guide_word = "我现在知道你想要创建一个Agent帮你解决一些事情，那么我们开始吧"

auto_build_ask_prompt = """
目前缺少的参数是：{para_type}
用户输入：{user_input}

请你使用温柔的语气去诱导用户补充这个参数
"""

auto_build_abstract_prompt = """
请根据用户输入的问题和聊天记录来提取用户参数。请确保提取的参数符合指定的输出格式。

用户输入：{input}
聊天记录：{history}

输出格式说明：{format_instructions}

请根据上述信息提取相关参数，并确保输出格式符合 `format_instructions` 中的要求。
"""

create_agent_prompt = """
请根据以下描述信息，帮助我选择需要绑定的工具。请确保描述信息尽可能详细，以便我能够准确地推荐适合的工具。

描述信息：{description}

请描述你希望Agent完成的任务、目标以及任何特定的需求或限制。这将有助于我为你推荐最合适的工具。
"""


MCP_TOOL_TEMPLATE = """
你是一个智能助手，能够根据用户的需求调用适当的工具来完成任务。以下是你的工作流程：

1. **分析用户输入**：仔细阅读用户的当前查询（`query`）和对话历史（`history`），理解用户的意图。
2. **判断是否需要调用工具**：如果用户的请求需要特定工具的支持（例如搜索、计算、翻译等），请明确指出需要调用哪个工具。
3. **生成调用指令**：如果需要调用工具，请按照以下格式生成调用指令：
   - 工具名称：工具的具体名称。
   - 输入参数：根据工具要求，从`query`或`history`中提取必要的信息作为输入参数。
4. **返回结果或下一步行动**：如果没有工具需要调用，直接回答用户的问题或提供相关信息。

### 参数说明：
- **query**：用户的当前输入内容。
- **history**：与用户之前的对话记录，可能为空。

### 参数信息
- **query**：{query}
- **history**： {history}

"""