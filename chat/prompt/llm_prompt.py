
function_call_prompt = """
请你判断user_input 是否应该需要function call
# 要求
用户和历史记录没提到的参数全部置空，但是一定返回
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
Thought:{agent_scratchpad}
"""
