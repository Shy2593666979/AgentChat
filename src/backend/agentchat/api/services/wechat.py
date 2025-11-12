import hashlib
import httpx
import asyncio
import time
from loguru import logger
import xml.etree.ElementTree as ET
from agentchat.settings import app_settings

class WeChatService:
    @classmethod
    def _get_access_token(cls):
        wechat_conf = app_settings.wechat_conf

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
    def check_signature(cls, token: str, signature: str, timestamp: str, nonce: str) -> bool:
        tmp_list = sorted([token, timestamp, nonce])
        tmp_str = "".join(tmp_list)
        tmp_str = hashlib.sha1(tmp_str.encode("utf-8")).hexdigest()
        return tmp_str == signature

    # 解析微信发来的 XML 消息
    @classmethod
    def parse_wechat_xml(cls, xml_data: str):
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

    # 构造回复的 XML（文本消息）
    @classmethod
    def build_text_reply(cls, to_user: str, from_user: str, content: str) -> str:
        # 消息再返回去的时候， from_user 和 to_user反过来!!!
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