
function_call_template = """
请你根据user input 、 history 和 recall_knowledge_data 来进行本次的function call
# 用户问题：
    user: {input}
# 历史记录：
    history: {history}
# 知识库召回的数据:
    recall_knowledge_data: {recall_knowledge_data}
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

llm_chat_template = """
请根据用户问题以及聊天记录回答用户：
# 用户问题
    {user_input}
# 聊天记录
    {history}
"""

update_user_config_error = "请检查您输入的信息或者格式是否正确"

get_user_config_error = "获取用户配置信息有误"

code_template = """def custom_function(text: str):
    ""This is a default python function, Please do not change the function name""
    
    return text
"""

parameter_template = """{
    "name": "WeatherAgent",
    "description": "获得指定位置的实时天气以及预报天气信息",
    "parameters": {
        "schema": "object",
        "properties": {
            "location": {
                "schema": "string",
                "description": "用户提到的位置"
            }
        },
        "required": ["location"]
    }
}
"""
