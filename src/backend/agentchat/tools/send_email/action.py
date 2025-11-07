import smtplib
from loguru import logger
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

from langchain.tools import tool

@tool(parse_docstring=True)
def send_email(sender: str, receiver: str, email_message: str, password: str):
    """
    向指定用户发送邮件信息。

    Args:
        sender (str): 发件人的邮箱地址。
        receiver (str): 收件人的邮箱地址。
        email_message (str): 发件人发送的邮件内容。
        password (str): 发件人的邮箱密码或授权码。

    Returns:
        str: 发送邮件的结果信息。
    """
    return _send_email(sender, receiver, email_message, password)




def _send_email(sender: str, receiver: str, email_message: str, password: str):
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
