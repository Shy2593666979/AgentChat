import json

from openai import OpenAI

client = OpenAI(api_key="sk-3e4b76be9af842ab81ca2a4ca1c16bdd", base_url="https://api.deepseek.com")

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather of an location, the user shoud supply a location first",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    }
                },
                "required": ["location"]
            },
        }
    },
]

def send_messages(messages):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools
    )
    return response.choices[0].message

messages = [{"role": "user", "content": "How's the weather in Hangzhou?"}]
message = send_messages(messages)
print(f"User>\t {messages[0]['content']}")

tool = message.tool_calls[0]
for tool in message.tool_calls:
    print(tool.function.name)
messages.append(message)


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
#             'type': 'object',
#             'properties': {
#                 'location': {
#                     'type': 'string',
#                     'description': 'The city and state, e.g. San Francisco, CA',
#                 },
#                 'unit': {
#                     'type': 'string',
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

