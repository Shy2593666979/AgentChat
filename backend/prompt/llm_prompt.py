function_call_prompt = """
基于用户输入 [user_input]，结合工具结果 [tools_result] 和历史记录 [history]，请生成一个综合性的响应或建议。

1. **用户输入**: {input}
2. **历史记录**: {history}
3. **工具结果**: {tools_result}

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
Thought:{agent_scratchpad}
"""

agent_guide_word = "我现在知道你想要创建一个Agent帮你解决一些事情，那么我们开始吧"

auto_build_ask_prompt = """
目前缺少的参数是：{para_type}
用户输入：{user_input}

请你使用温柔的语气去诱导用户补充这个参数
"""

auto_build_abstract_prompt = """
请根据用户输入的问题和聊天记录来提取用户参数：
user input: {input}
history: {history}

output schemas: {format_instructions}
"""
