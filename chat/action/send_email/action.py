import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from loguru import logger


def send_email_action(sender: str, receiver: str, emailMessage: str, password: str):
    
    # 构建邮件内容
    message = MIMEMultipart()
    message["From"] = Header('AI <%s>' % sender)
    message["To"] = receiver
    message["Subject"] = "我是您的AI助理，您有一封邮件请查看"
    try:
        body = emailMessage
        message.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 发件人邮箱中的SMTP服务器，端口是465
        server.login(sender, password)  # 括号中对应的是发件人邮箱账号、邮箱密码
        server.sendmail(sender, receiver, message.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
        
        logger.info(f"sender: {sender}, receiver: {receiver}, emailMessage: {emailMessage}, password: {password}")
        return "send email successful, please check receiver`s email"
    
    except Exception as err :
        logger.error(f"send email appear error : {err}")
        return "send email is error"
