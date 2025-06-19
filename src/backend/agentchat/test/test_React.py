import json

from langchain_core.output_parsers import JsonOutputParser
from openai import OpenAI
from langchain_openai import ChatOpenAI

# client = ChatOpenAI(api_key="sk-ChtJNYJD1sm5FqwA7bE8EfFa3eE847Fa9758E5626d64Cc9a", base_url="http://70.182.56.16:11000/v1/", model="Qwen2-72B-Instruct")

client = OpenAI(base_url='http://70.182.56.16:11000/v1/', api_key='sk-ChtJNYJD1sm5FqwA7bE8EfFa3eE847Fa9758E5626d64Cc9a')
tools = [
    {
        "schema": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather of an location, the user shoud supply a location first",
            "parameters": {
                "schema": "object",
                "properties": {
                    "location": {
                        "schema": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    }
                },
                "required": ["location"]
            },
        }
    },
]

def send_messages(messages):
    # client = OpenAI()
    response = client.chat.completions.create(
        model="Qwen2-72B-Instruct",
        messages=messages,
        tools=tools,
    )
    return response.choices[0].message
#
messages = [{"role": "user", "content": "How's the weather in Hangzhou?"}]
# message = send_messages(messages)
# print(f"User>\t {messages[0]['content']}")
#
# tool = message.tool_calls[0]
# for tool in message.tool_calls:
#     print(tool.function.name)
# messages.append(message)

PROMPT_REACT = """Answer the following questions as best you can. You have access to the following APIs:

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


prompt = PROMPT_REACT.format(tools_text=tools, tools_name_text='get_weather', query='北京的天气如何啊？')

def parse_latest_plugin_call(text):
    plugin_name, plugin_args = '', ''
    i = text.rfind('\nAction:')
    j = text.rfind('\nAction Input:')
    k = text.rfind('\nObservation:')
    if 0 <= i < j:  # If the text has `Action` and `Action input`,
        if k < j:  # but does not contain `Observation`,
            # then it is likely that `Observation` is ommited by the LLM,
            # because the output text may have discarded the stop word.
            text = text.rstrip() + '\nObservation:'  # Add it back.
        k = text.rfind('\nObservation:')
        plugin_name = text[i + len('\nAction:') : j].strip()
        plugin_args = text[j + len('\nAction Input:') : k].strip()
        text = text[:k]
    return plugin_name, plugin_args, text


res = send_messages(messages)



# res = client.invoke(input=prompts).content
#
# resp = parse_latest_plugin_call(res)
#
# print(resp)
# def get_current_weather(location, unit='fahrenheit'):
#     """Get the current weather in a given location"""
#     if 'tokyo' in location.lower():
#         return json.dumps({'location': 'Tokyo', 'temperature': '10', 'unit': 'celsius'})
#     elif 'san francisco' in location.lower():
#         return json.dumps({'location': 'San Francisco', 'temperature': '72', 'unit': 'fahrenheit'})
#     elif 'paris' in location.lower():
#         return json.dumps({'location': 'Paris', 'temperature': '22', 'unit': 'celsius'})
#     else:
#         return json.dumps({'location': location, 'temperature': 'unknown'})
#
#
# functions = [{
#         'name': 'get_current_weather',
#         'description': 'Get the current weather in a given location',
#         'parameters': {
#             'schema': 'object',
#             'properties': {
#                 'location': {
#                     'schema': 'string',
#                     'description': 'The city and state, e.g. San Francisco, CA',
#                 },
#                 'unit': {
#                     'schema': 'string',
#                     'enum': ['celsius', 'fahrenheit']
#                 },
#             },
#             'required': ['location'],
#         },
#     }]


# user_input = "What's the weather like in San Francisco?"
# # messages = [{'role': 'user', 'content': "What's the weather like in San Francisco?"}]
#
# if responses.get('function_call', None):
#     # Step 3: call the function
#     # Note: the JSON response may not always be valid; be sure to handle errors
#     available_functions = {
#         'get_current_weather': get_current_weather,
#     }  # only one function in this example, but you can have multiple
#     function_name = responses['function_call']['name']
#     function_to_call = available_functions[function_name]
#     function_args = json.loads(responses['function_call']['arguments'])
#     function_response = function_to_call(
#         location=function_args.get('location'),
#         unit=function_args.get('unit'),
#     )
#     print('# Function Response:')
#     print(function_response)

