import smtplib
from typing import Type
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from langchain.tools import BaseTool
from pydantic import Field, BaseModel
from loguru import logger

class EmailInput(BaseModel):
    sender: str = Field(description='邮件的发送人邮箱')
    receiver: str = Field(description='邮件的收件人邮箱')
    email_message: str = Field(description='邮件的具体内容')
    password: str = Field(description='发送人邮箱的授权码')

class SendEmailTool(BaseTool):
    name = 'send_email'
    description = '帮助用户发送邮件'
    args_schema: Type[BaseModel] = EmailInput

    def _run(self, sender: str, receiver: str, email_message: str, password: str):
            return send_email(sender, receiver, email_message, password)


def send_email(sender: str, receiver: str, email_message: str, password: str):
    """帮助用户发送邮件"""

    # 构建邮件内容
    message = MIMEMultipart()
    message["From"] = Header('AI <%s>' % sender)
    message["To"] = receiver
    message["Subject"] = "我是您的AI助理，您有一封邮件请查看"
    try:
        body = email_message
        message.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 发件人邮箱中的SMTP服务器，端口是465
        server.login(sender, password)  # 括号中对应的是发件人邮箱账号、邮箱密码
        server.sendmail(sender, receiver, message.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接

        logger.info(f"sender: {sender}, receiver: {receiver}, emailMessage: {email_message}, password: {password}")
        return "send email successful, please check receiver`s email"

    except Exception as err:
        logger.error(f"send email appear error : {err}")
        return "send email is error"
