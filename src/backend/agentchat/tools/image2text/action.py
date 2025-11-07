import base64
from langchain.tools import tool

from agentchat.core.models.manager import ModelManager

@tool(parse_docstring=True)
def image_to_text(image_path: str):
    """
    根据用户提供的图片路径描述图片内容。

    Args:
        image_path (str): 用户提供的图片路径。

    Returns:
        str: 描述图片内容的结果。
    """
    return _image_to_text(image_path)

def _image_to_text(image_path):
    def encode_image():
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    client = ModelManager.get_qwen_vl_model()

    image_type = image_path.split('.')[-1]
    base64_image = encode_image()

    response = client.invoke(
        [
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
    return response.content
