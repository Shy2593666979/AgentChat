
function_call_template = """
请你根据user input 和 history 来进行本次的function call
# 用户问题：
    user: {user_input}
# 历史记录：
    history: {history}
"""

ask_user_template = """
目前还缺少参数，你需要根据以下信息引导用户将这些缺少的参数补充完整

# 用户问题：
    user：{user_input}
# 当前场景：
    {function_name}
# 目前已有的参数：
    {have_parameters}
# 缺少的参数
    {lack_parameters}
"""

action_template = """
现在已经执行完action，根据以下信息进行回答用户

# 用户问题：
    user: {user_input}
# 当前场景:
    {function_name}
# action信息：
    {action_result}
"""

code_template = """def custom_function(text: str):
    ""This is a default python function, Please do not change the function name""
    
    return text
"""

parameter_template = """{
    "name": "WeatherAgent",
    "description": "获得指定位置的实时天气以及预报天气信息",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "用户提到的位置"
            }
        },
        "required": ["location"]
    }
}
"""
