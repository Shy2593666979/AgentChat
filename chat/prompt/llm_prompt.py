
function_call_prompt = """
请你判断user_input 是否应该需要function call
# 要求
用户和历史记录没提到的参数全部置空，但是一定返回
"""

fail_action_prompt = """
抱歉，没有完成你交给我的任务，换一个再试试吧
"""