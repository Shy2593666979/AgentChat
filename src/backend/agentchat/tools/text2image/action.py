import requests
from loguru import logger
from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath

from dashscope import ImageSynthesis
from langchain.tools import tool

from agentchat.settings import app_settings
from agentchat.services.aliyun_oss import aliyun_oss

@tool(parse_docstring=True)
def text_to_image(user_prompt: str):
    """
    根据用户提供的提示词产生图片。

    Args:
        user_prompt (str): 用户的图片提示词。

    Returns:
        str: 生成的图片链接。
    """
    return _text_to_image(user_prompt)


def _text_to_image(user_prompt):
    """给用户的图片描述生成一张照片"""
    rsp = ImageSynthesis.call(api_key=app_settings.multi_models.text2image.api_key,
                              model=app_settings.multi_models.text2image.model_name,
                              prompt=user_prompt,
                              n=1,
                              size='1024*1024')
    if rsp.status_code == HTTPStatus.OK:
        # 上传图片到OSS
        for result in rsp.output.results:
            try:
                # 解析文件名
                url_path = urlparse(result.url).path
                unquoted_path = unquote(url_path)
                file_name = PurePosixPath(unquoted_path).parts[-1]

                # 可选：添加存储前缀，方便管理OSS文件
                oss_object_name = f"text_to_image/{file_name}"  # 例如存到images目录下

                # 直接获取图片内容并上传到OSS
                response = requests.get(result.url)
                if response.status_code == 200:
                    aliyun_oss.upload_file(oss_object_name, response.content)
                    logger.info(f"图片 {file_name} 已成功上传到OSS")
                    return f"您的图片已经生成完毕，图片链接为：![图片]({app_settings.aliyun_oss["base_url"]}/{oss_object_name})"
                else:
                    logger.error(f"获取图片 {result.url} 失败，状态码: {response.status_code}")
                    raise ValueError(f"获取图片 {result.url} 失败，状态码: {response.status_code}")

            except Exception as e:
                logger.error(f"处理图片 {result.url} 时出错: {str(e)}")
                raise ValueError(f"处理图片 {result.url} 时出错: {str(e)}")
    else:
        return 'sync_call Failed, status_code: %s, code: %s, message: %s' % (rsp.status_code, rsp.code, rsp.message)