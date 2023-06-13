import asyncio
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from PIL import Image
from io import BytesIO
from pyppeteer import launch

class MailSender:
    def __init__(self):
        self.relay_host = '10.130.128.21'
        self.relay_port = 25
        self.sender = 'hao.6.zhang@nokia-sbell.com'

    def send_mail(self, receiver, subject, content, attachFileList=None):
        message_to = "; ".join(receiver)
        sender = self.sender
        message = MIMEMultipart()
        message['From'] = self.sender
        message['To'] = message_to
        message['Subject'] = Header(subject, 'utf-8')

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

async def capture_screenshot(url):
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url)
    screenshot = await page.screenshot()
    await browser.close()
    return screenshot

def send_mail_with_screenshot(url, receiver, subject, content):
    mail_sender = MailSender()
    screenshot = asyncio.get_event_loop().run_until_complete(capture_screenshot(url))
    screenshot_image = Image.open(BytesIO(screenshot))
    screenshot_path = 'screenshot.png'
    screenshot_image.save(screenshot_path)
    mail_sender.send_mail(receiver, subject, content, attachFileList=[screenshot_path])
    print('Email sent successfully.')

def main():
    url = 'https://www.baidu.com'  # 要截图的网页 URL
    receiver = ['hao.6.zhang@nokia-sbell.com']  # 收件人邮箱
    subject = 'Screenshot of Baidu Homepage'  # 邮件主题
    content = '<h1>Baidu Homepage</h1>'  # 邮件正文

    # 发送邮件
    send_mail_with_screenshot(url, receiver, subject, content)

if __name__ == '__main__':
    main()
