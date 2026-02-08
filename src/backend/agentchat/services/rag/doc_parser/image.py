import os
import base64
import tempfile
from agentchat.core.models.manager import ModelManager


def image_to_txt(image_path: str):
    vl_model = ModelManager.get_qwen_vl_model()
    # 将本地图片转成 base64进行解析描述
    image_type = image_path.split('.')[-1]
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    response = vl_model.invoke(
        input=[
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a helpful assistant."}]},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/{image_type};base64,{base64_image}"},
                    },
                    {"type": "text", "text": "图中描绘的是什么景象? 要求：1.字数不超过300字。2.直接输出图片描述文本"},
                ],
            }
        ],
    )

    fd, txt_path = tempfile.mkstemp(suffix=".txt")
    os.close(fd)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(response.content.strip())

    return txt_path
