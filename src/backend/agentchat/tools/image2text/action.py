import base64
from typing import Type

from langchain.tools import BaseTool
from openai import OpenAI
from pydantic import BaseModel, Field
from agentchat.settings import app_settings


class Image2TextInput(BaseModel):
    file_url: str = Field(description='用户上传的文件URL路径')


class Image2TextTool(BaseTool):
    name: str = "image_to_text"
    description: str = '将用户上传的图片转成图片文本'
    args_schema: Type[BaseModel] = Image2TextInput

    def _run(self, file_url):
        return image_to_text(file_url)


def image_to_text(image_path):
    def encode_image():
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    client = OpenAI(api_key=app_settings.multi_models.qwen_vl.api_key,
                    base_url=app_settings.multi_models.qwen_vl.base_url)
    image_type = image_path.split('.')[-1]
    base64_image = encode_image()
    completion = client.chat.completions.create(
        model=app_settings.multi_models.qwen_vl.model_name,
        messages=[
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a helpful assistant."}]},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        # 需要注意，传入BASE64，图像格式（即image/{format}）需要与支持的图片列表中的Content Type保持一致。"f"是字符串格式化的方法。
                        # PNG图像：  f"data:image/png;base64,{base64_image}"
                        # JPEG图像： f"data:image/jpeg;base64,{base64_image}"
                        # WEBP图像： f"data:image/webp;base64,{base64_image}"
                        "image_url": {"url": f"data:image/{image_type};base64,{base64_image}"},
                    },
                    {"type": "text", "text": "图中描绘的是什么景象?"},
                ],
            }
        ],
    )
    return completion.choices[0].message.content
