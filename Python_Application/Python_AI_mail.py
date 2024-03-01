import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


class MailSender:
    def __init__(self):
        self.relay_host = '10.130.128.21'
        self.relay_port = 25
        self.sender = 'hao.6.zhang@nokia-sbell.com'

    def send_mail(self, receiver, subject, content, attachFileList=None, is_html=False):
        message_to = "; ".join(receiver)
        sender = self.sender
        message = MIMEMultipart()
        message['From'] = self.sender
        message['To'] = message_to
        message['Subject'] = subject

        # 如果内容是HTML，则以HTML格式添加
        if is_html:
            part = MIMEText(content, 'html')
        else:
            part = MIMEText(content, 'plain')
        message.attach(part)

        if attachFileList:
            for file in attachFileList:
                with open(file, 'rb') as f:
                    attachment = MIMEImage(f.read())
                    attachment.add_header('Content-Disposition', 'attachment', filename=file)
                    message.attach(attachment)

        smtp = smtplib.SMTP(self.relay_host, self.relay_port)
        smtp.sendmail(sender, receiver, message.as_string())
        smtp.quit()
        print(f"<--send mail to {receiver} succeed-->")


# CSS样式
css_style = """
<style type="text/css">
table {
    font-family: '微软雅黑', sans-serif; /* 设置字体为微软雅黑 */
    color: #333; /* 字体颜色 */
    border-collapse: collapse; /* 边框合并 */
    width: 100%;
}
td, th {
    border: 1px solid #CCC; /* 单元格边框 */
    height: 30px; /* 单元格高度 */
    transition: all 0.3s;  /* 过渡动画 */
}
th {
    background: #025cb4; /* 表头背景色设置为深蓝色 */
    color: #FFF; /* 表头文字颜色设置为白色 */
    font-weight: bold; /* 表头字体加粗 */
}
tr:nth-child(even) td {
    background: #5fbdfd; /* 偶数行单元格背景色设置为淡蓝色 */
}
tr:nth-child(odd) td {
    background: #c0bebe; /* 奇数行单元格背景色设置为浅灰色 */
}
td {
    text-align: center; /* 文字居中 */
}
</style>
"""

# 示例：将Pandas DataFrame转换为HTML并发送邮件
df = pd.DataFrame({'Name': ['Alice', 'Bob'], 'Age': [24, 30]})  # 示例DataFrame
html_content = css_style + df.to_html(index=False)  # 将DataFrame转换为HTML
mail_sender = MailSender()
receiver = ['hao.6.zhang@nokia-sbell.com']  # 接收者列表
subject = 'CRT/CIT Retest Report'  # 邮件主题
content = html_content  # 邮件内容

# 发送邮件，is_html设置为True
mail_sender.send_mail(receiver, subject, content, is_html=True)
