import re
import os
import base64
import asyncio
from loguru import logger
from urllib.parse import urljoin

from agentchat.core.models.manager import ModelManager
from agentchat.settings import app_settings


class MarkdownRewrite:
    def __init__(self, **kwargs):

        # LLM 的配置可以放到配置文件config中
        self.client = ModelManager.get_qwen_vl_model()

    async def _get_image_dict(self, markdown_path):
        # 获取Md文件的上层目录路径
        parent_dir = os.path.dirname(markdown_path)

        images_dir = os.path.join(parent_dir, "images")
        # 将文件名与具体路径一一对应
        image_path_dict = {}
        if os.path.exists(images_dir):
            for path in os.listdir(images_dir):
                image_path_dict[path] = os.path.join(images_dir, path)
        return image_path_dict

    async def _read_markdown(self, markdown_path):
        if not os.path.exists(markdown_path):
            raise FileNotFoundError(f'Markdown 文件未找到: {markdown_path}')
        with open(markdown_path, 'r', encoding='utf-8') as file:
            return file.read()

    async def request_vl(self, image_path):
        # 将本地图片转成 base64进行解析描述
        image_type = image_path.split('.')[-1]
        base64_image = await MarkdownRewrite.encode_image(image_path)
        response = await self.client.ainvoke(
            input=[
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
                        {"type": "text", "text": "图中描绘的是什么景象? 要求：1.字数不超过100字。2.直接输出图片描述文本"},
                    ],
                }
            ],
        )
        logger.debug(f"{image_path} 中的描述信息为 {response.content}")
        return response.content

    async def async_request_vl(self, image, image_path):
        result = await self.request_vl(image_path)
        return image, result

    async def get_image_description(self, image_path_dict):
        # 创建信号量，限制并发数为3
        semaphore = asyncio.Semaphore(3)

        async def limited_request(image, image_path):
            async with semaphore:  # 使用信号量控制并发
                return await self.async_request_vl(image, image_path)

        # 创建任务列表
        tasks = [limited_request(image, image_path)
                 for image, image_path in image_path_dict.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 获得每张图片的描述信息
        # 采用的是异步调用，只需要一次请求模型的时间
        # tasks = [self.async_request_vl(image, image_path) for image, image_path in image_path_dict.items()]
        # results = await asyncio.gather(*tasks, return_exceptions=True)

        image_desc_dict = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f'图片描述信息出现错误: {result}')
                continue

            image, desc = result
            image_desc_dict[image] = desc
        return image_desc_dict

    async def process_markdown(self, markdown_text, image_oss_dict, image_desc_dict):
        # 正则表达式匹配Markdown中的图片链接格式
        pattern = r"!\[.*?\]\((.*?)\)"

        # 替换函数，在每个匹配的图片链接前加上提示文字
        def replace_image(match):
            alt_text = match.group(0)  # 提取图片的alt文本
            image_url = match.group(1)  # 提取图片的URL
            image_oss_object_name = image_oss_dict.get(os.path.basename(image_url))
            image_desc = image_desc_dict.get(os.path.basename(image_url))

            return f'![{image_desc}]({urljoin(app_settings.aliyun_oss.get("base_url"), image_oss_object_name)})'

        # 使用re.sub进行替换
        result = re.sub(pattern, replace_image, markdown_text)

        return result

    async def run_rewrite(self, markdown_path, image_oss_dict):
        markdown_text = await self._read_markdown(markdown_path)

        image_path_dict = await self._get_image_dict(markdown_path)

        # 首先获取Image中的描述信息
        image_desc_dict = await self.get_image_description(image_path_dict)

        new_markdown_text = await self.process_markdown(markdown_text, image_oss_dict, image_desc_dict)

        with open(markdown_path, 'w', encoding='utf-8') as file:
            file.write(new_markdown_text)
        logger.info(f'Markdown 文档已经重写完成 !')

    @staticmethod
    async def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")


markdown_rewriter = MarkdownRewrite()
