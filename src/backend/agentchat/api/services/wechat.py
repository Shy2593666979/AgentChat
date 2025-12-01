import hashlib
import httpx
import asyncio
import time
import requests
from loguru import logger
import xml.etree.ElementTree as ET

from agentchat.api.services.workspace_session import WorkSpaceSessionService
from agentchat.settings import app_settings

class WeChatService:

    @classmethod
    def _get_access_token(cls):
        wechat_conf = app_settings.wechat_config
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={wechat_conf.get("app_id")}&secret={wechat_conf.get("secret")}"
        try:
            with httpx.Client() as client:
                response = client.get(url, timeout=10)
                result = response.json()
                if "access_token" in result:
                    return result["access_token"]
                else:
                    logger.error(f"获取access_token失败: {result}")
                    return None
        except Exception as e:
            logger.error(f"获取access_token异常: {e}")
            return None

    @classmethod
    def send_user_message(cls, to_user, content):
        """仅限于进行微信验证后的企业账号，否则客服消息开不通"""
        access_token = cls._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={access_token}"
        data = {
            "touser": to_user,
            "msgtype": "text",
            "text": {"content": content}
        }
        resp = requests.post(url, json=data)
        return resp.json()

    @classmethod
    def push_user_image(cls, image_path=None):
        """将图片临时推送到微信服务器中，可使用Redis缓存三天 media_id"""
        access_token = cls._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/media/upload?access_token={access_token}&type=image"
        files = {
            "media": open(image_path or "agentchat/config/default.jpg", "rb") # 示例，可放到config.yaml文件
        }
        response = requests.post(url, files=files)
        result = response.json()
        media_id = result.get("media_id")
        return media_id

    @classmethod
    def check_signature(cls, token: str, signature: str, timestamp: str, nonce: str) -> bool:
        tmp_list = sorted([token, timestamp, nonce])
        tmp_str = "".join(tmp_list)
        tmp_str = hashlib.sha1(tmp_str.encode("utf-8")).hexdigest()
        return tmp_str == signature

    @classmethod
    def parse_wechat_xml(cls, xml_data: str):
        """解析微信发来的 XML 消息"""
        root = ET.fromstring(xml_data)
        msg_type = root.find("MsgType").text
        from_user = root.find("FromUserName").text
        to_user = root.find("ToUserName").text
        event = root.find("Event").text if root.find("Event") is not None else ""
        content = root.find("Content").text if root.find("Content") is not None else ""
        return {
            "msg_type": msg_type,
            "from_user": from_user,
            "to_user": to_user,
            "event": event,
            "content": content,
        }

    @classmethod
    async def process_user_keyword(cls, keyword, from_user, to_user):
        match keyword:
            case key if key in ["清空会话", "清空聊天记录", "清除会话", "清除聊天记录"]:
                await WorkSpaceSessionService.clear_workspace_session_contexts(from_user)
                return cls.build_text_reply(to_user, from_user, "聊天记录已清空，有什么新问题再问我的呢~")
            case key if "毕业照" in key: # 示例，发送给用户图片
                media_id = cls.push_user_image()
                return cls.build_image_reply(to_user, from_user, media_id)
            case key if "微信账号" in key:
                return cls.build_text_reply(to_user, from_user, f"您的微信账号为：{from_user}, 可在www.agentchat.cloud网站中使用微信账号注册查看您的聊天记录")
            case _:
                return None

    @classmethod
    def build_text_reply(cls, to_user: str, from_user: str, content: str) -> str:
        """构造回复的 XML（文本消息）
        Attention:
            消息再返回去的时候， from_user 和 to_user反过来!!!
        """
        return f"""
        <xml>
            <ToUserName><![CDATA[{from_user}]]></ToUserName>
            <FromUserName><![CDATA[{to_user}]]></FromUserName>
            <CreateTime>{int(time.time())}</CreateTime>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA[{content}]]></Content>
        </xml>
        """

    @classmethod
    def build_image_reply(cls, to_user: str, from_user: str, media_id: str) -> str:
        return f"""
        <xml>
            <ToUserName><![CDATA[{from_user}]]></ToUserName>
            <FromUserName><![CDATA[{to_user}]]></FromUserName>
            <CreateTime>{int(time.time())}</CreateTime>
            <MsgType><![CDATA[image]]></MsgType>
            <Image>
                <MediaId><![CDATA[{media_id}]]></MediaId>
            </Image>
        </xml>
        """