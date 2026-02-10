import json
import os
import re
import requests
from loguru import  logger
from pydantic import BaseModel, Field

from agentchat.settings import app_settings
from datetime import datetime, timedelta, timezone

class ImportedConfigInfo(BaseModel):
    name: str
    url: str
    type: str = "sse"
    headers: dict | None = None

def parse_imported_config(imported_config):
    name, info = next(iter(imported_config.get("mcpServers", {}).items()))

    return ImportedConfigInfo(
        name=name,
        url=info.get("url"),
        type=info.get("type"),
        headers=info.get("headers")
    )


def build_completion_system_prompt(system_prompt, history):
    if "{history}" in system_prompt:
        system_prompt = system_prompt.format(
            history=f"<chat_history>\n{history}\n</chat_history>"
        )
    else:
        system_prompt += f"""
        📜 对话历史
        - {history}
        """
    return system_prompt


def build_completion_history_messages(history_messages):
    """
    examples:
        <chat_history>
        role: user, content: 你好啊！
        role: ai, content: 你好啊，我可以帮助你什么？
        <chat_history>
        ......
    """
    if len(history_messages) % 2 == 1:
        history_messages = history_messages[:len(history_messages)-1]

    history_content = ""
    for idx in range(0, len(history_messages), 2):
        user_msg = history_messages[idx]
        ai_msg = history_messages[idx+1]
        history_content += f"<chat_history_{idx // 2 + 1}>\n"
        history_content += f"role: {user_msg.type}, content: {user_msg.content}\n"
        history_content += f"role: {ai_msg.type}, content: {ai_msg.content}\n"
        history_content += f"</chat_history_{idx // 2 + 1}>\n"

    return history_content


def fix_json_text(text: str):
    """
    Json字符串不允许出现 ' 单引号
    修复Json字符串"""
    return text.replace("'", '"')

def get_cache_key(client_id, chat_id):
    return f'{client_id}_{chat_id}'

def check_or_create(path):
    if os.path.exists(path):
        pass
    else:
        os.makedirs(path)

def build_completion_user_input(user_input, file_url):
    if file_url:
        return f"{user_input}, 上传的文件链接：{file_url}"
    else:
        return user_input

def init_dir(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except Exception as err:
        logger.error(f"create dir appear: {err}")

def get_now_beijing_time(delta: int = 0):

    # 设置北京时间时区（东八区）
    beijing_tz = timezone(timedelta(hours=8 + delta))

    # 获取当前时间
    now = datetime.now(beijing_tz)

    # 格式化输出到分钟
    current_time = now.strftime("%Y-%m-%d %H:%M")

    return current_time


def check_input(user_input):
    # 定义正则表达式，匹配大小写字母、数字
    alphabet_pattern = re.compile(r'^[a-zA-Z0-9]+$')

    # 检查输入是否只包含大小写字母、数字
    if alphabet_pattern.match(user_input):
        return True
    else:
        return False

def delete_img(logo: str):
    try:
        if os.path.exists(logo) and logo != app_settings.default_config.get("agent_logo_url"):
            os.remove(logo)
        else:
            logger.info(f"The logo Path is no exist")
    except Exception as err:
        logger.error(f"delete img appear error: {err}")

def filename_to_classname(filename):
    """
    Convert a snake_case filename to a CamelCase class name.

    Args:
    filename (str): The filename in snake_case, without the .py extension.

    Returns:
    str: The converted CamelCase class name.
    """
    parts = filename.split('_')
    class_name = ''.join(part.capitalize() for part in parts)
    return class_name


def load_scene_templates(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def load_all_scene_configs(chatId):
    # 用于存储所有场景配置的字典
    all_scene_configs = {}

    original_path = "./Agent_data/first_important.json"
    file_path = f"./Agent_data/{chatId}.json"
    if not os.path.exists(file_path):
        # 读取original_path中json的内容
        with open(original_path, 'r', encoding='utf-8') as original_file:
            data = json.load(original_file)

        with open(file_path, 'w',encoding='utf-8') as new_file:
            json.dump(data,new_file,ensure_ascii=False,indent=4)

    current_config = load_scene_templates(file_path)

    for key, value in current_config.items():
        if key not in all_scene_configs:
            all_scene_configs[key] = value

    return all_scene_configs

def send_message(prompt, user_input):
    """
    请求LLM函数
    """
    
    # logger.logger_api.info('prompt输入:' + prompts)
    
    # logger.logger_api.info('用户输入:' + user_input)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "-------------"
    }
    data = {
        "models": "Qwen1.5-72b-chat",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post("models.url", data=json.dumps(data),
                             headers=headers).content
    print(response)

    response_1 = json.loads(response)
    message = response_1["choices"][0]["message"]["content"]
    
    # logger.logger_api.info("大模型输出：" + str(message))
    
    return str(message)


def is_slot_fully_filled(json_data):
    """
    检查槽位是否完整填充
    """
    # 遍历JSON数据中的每个元素
    for item in json_data:
        # 检查value字段是否为空字符串
        if item.get('value') == '' or '未提供' in item.get('value') :
            return False  # 如果发现空字符串，返回False
    return True  # 如果所有value字段都非空，返回True


def get_raw_slot(parameters):
    # 创建新的JSON对象
    output_data = []
    for item in parameters:
        new_item = {"name": item["name"], "desc": item["desc"], "schema": item["schema"], "value": ""}
        output_data.append(new_item)
    return output_data


def get_dynamic_example(scene_config):
    # 创建新的JSON对象
    if 'example' in scene_config:
        return scene_config['example']
    else:
        return '答：{"name":"xx","value":"xx"}'

    
def get_slot_update_json(slot):
    # 创建新的JSON对象
    output_data = []
    for item in slot:
        new_item = {"name": item["name"], "desc": item["desc"], "value": item["value"]}
        output_data.append(new_item)
    return output_data


def get_slot_query_user_json(slot):
    # 创建新的JSON对象
    output_data = []
    for item in slot:
        if not item["value"] or "未提供" in item["value"]:
            new_item = {"name": item["name"], "desc": item["desc"], "value":  item["value"]}
            output_data.append(new_item)
    return output_data


def update_slot(json_data, dict_target):
    """
    更新槽位slot参数
    """
    # 遍历JSON数据中的每个元素
    for item in json_data:
        # 检查value字段是否为空字符串
        if item is not None and 'value' in item and item['value'] != '':
            for target in dict_target:
                if target['name'] == item['name']:
                    target['value'] = item.get('value')
                    break

# 在json文件也及时更新
def update_agent_json(scene_name,slot,chatId):
    file_path = f"./Agent_data/{chatId}.json"
    with open(file_path,'r', encoding='utf-8') as file:
        data = json.load(file)

    for index in range(len(slot)):
        data[scene_name]["parameters"][index]["value"] = slot[index]["value"]
    
    with open(file_path,'w',encoding='utf-8') as file:
        json.dump(data,file,ensure_ascii=False,indent=4)


# 清空对应的json文件
def clear_agent_json(scene_name,chatId):
    file_path = f"./Agent_data/{chatId}.json"
    with open(file_path,'r', encoding='utf-8') as file:
        data = json.load(file)

    for index in range(len(data[scene_name]["parameters"])):
        data[scene_name]["parameters"][index]["value"] = ""
    
    with open(file_path,'w',encoding='utf-8') as file:
        json.dump(data,file,ensure_ascii=False,indent=4)

def clean_slot_json(slot):
    
    return get_raw_slot(slot)


def update_agent_current_scene(current_scene,chatId):
    file_path = f"./Agent_data/current_scene.json"
    with open(file_path,'r',encoding='utf-8') as file:
        data = json.load(file)
    
    data[chatId] = current_scene

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def get_agent_current_scene(chatId):
    file_path = f"./Agent_data/current_scene.json"
    with open(file_path,'r',encoding='utf-8') as file:
        data = json.load(file)
    
    return data.get(chatId,'')

def format_name_value_for_logging(json_data):
    """
    抽取参数名称和value值
    """
    log_strings = []
    for item in json_data:
        name = item.get('name', 'Unknown name')  # 获取name，如果不存在则使用'Unknown name'
        value = item.get('value', 'N/A')  # 获取value，如果不存在则使用'N/A'
        log_string = f"name: {name}, Value: {value}"
        log_strings.append(log_string)
    return '\n'.join(log_strings)


def extract_json_from_string(input_string):
    """
    JSON抽取函数
    返回包含JSON对象的列表
    """
    try:
        # 正则表达式假设JSON对象由花括号括起来
        matches = re.findall(r'\{.*?\}', input_string, re.DOTALL)

        # 验证找到的每个匹配项是否为有效的JSON
        valid_jsons = []
        for match in matches:
            try:
                json_obj = json.loads(match)
                valid_jsons.append(json_obj)
            except json.JSONDecodeError:
                try:
                    valid_jsons.append(fix_json(match))
                except json.JSONDecodeError:
                    continue  # 如果不是有效的JSON，跳过该匹配项
                continue  # 如果不是有效的JSON，跳过该匹配项

        return valid_jsons
    except Exception as e:
        print(f"Error occurred: {e}")
        return []


def fix_json(bad_json):
    # 首先，用双引号替换掉所有的单引号
    fixed_json = bad_json.replace("'", '"')
    try:
        # 然后尝试解析
        return json.loads(fixed_json)
    except json.JSONDecodeError:
        # 如果解析失败，打印错误信息，但不会崩溃
        print("给定的字符串不是有效的 JSON 格式。")


# 打印当前工作目录
# print("Current working directory:", os.getcwd())

def get_function(type: str="openai"):
    if type == "openai":
        return get_function_openai()
    else:
        return get_function_qwen()

def get_function_openai():
    parameter = AgentService.select_agent_by_type(type="openai")
    result = []
    for data in parameter:

        para = json.loads(data.parameter)
        result.append(para)
    return result

def get_function_qwen():
    parameter = AgentService.select_agent_by_type(type="qwen")
    result = []
    for data in parameter:
        para = json.loads(data.parameter)
        result.append(para)
    return result

def get_function_by_name_type(function_name: str, type: str="openai"):
    parameter = AgentService.get_agent_by_name_type(name=function_name, type=type)

    for data in parameter:
        para = json.loads(data.parameter)
        return para
    logger.info(f"get function by name schema appear no data")
