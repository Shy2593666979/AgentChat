
function_call_prompt = """
请你判断user_input 是否应该需要function call
# 需要：
    用户和历史记录没提到的参数全部置空，但是一定返回
# 不需要：
    则进行正常的闲聊
"""
