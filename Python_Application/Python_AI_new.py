import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from selenium import webdriver
from PIL import Image


class MailSender:
    def __init__(self):
        self.relay_host = '10.130.128.21'  # 10.130.128.21
        self.relay_port = 25
        self.sender = 'hao.6.zhang@nokia-sbell.com'  # hao.6.zhang@nokia-sbell.com

    def send_mail(self, receiver, subject, content, attachFileList=None):
        message_to = "; ".join(receiver)
        sender = self.sender
        message = MIMEMultipart()
        message['From'] = self.sender
        message['To'] = message_to
        message['Subject'] = subject

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

def capture_element_screenshot(url, selector, screenshot_path):
    # 使用Selenium启动浏览器
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 无头模式，不打开浏览器窗口
    driver = webdriver.Chrome(options=options)

    # 访问网页
    driver.get(url)

    # 定位要截图的元素
    element = driver.find_element_by_css_selector(selector)

    # 获取元素在页面上的位置和大小
    location = element.location
    size = element.size

    # 截取整个网页的截图
    driver.save_screenshot(screenshot_path)

    # 使用PIL库打开截图
    image = Image.open(screenshot_path)

    # 根据元素位置和大小，截取元素的截图
    left = location['x']
    top = location['y']
    right = location['x'] + size['width']
    bottom = location['y'] + size['height']
    element_screenshot = image.crop((left, top, right, bottom))

    # 保存元素截图
    element_screenshot.save(screenshot_path)

    # 关闭浏览器
    driver.quit()

def send_mail_with_screenshot(url, selector, receiver, subject):
    # 发送邮件实例化
    mail_sender = MailSender()

    # 设置截图保存路径
    screenshot_path = 'screenshot.png'

    # 获取元素截图
    capture_element_screenshot(url, selector, screenshot_path)

    # 创建邮件
    msg = MIMEMultipart()
    msg['From'] = mail_sender.sender
    msg['To'] = ", ".join(receiver)
    msg['Subject'] = subject

    # 添加邮件正文
    content = '<h1>Homepage with Element Screenshot</h1>'
    html_part = MIMEText(content, 'html')
    msg.attach(html_part)

    # 添加元素截图附件
    with open(screenshot_path, 'rb') as f:
        attachment = MIMEImage(f.read())
        attachment.add_header('Content-Disposition', 'attachment', filename='screenshot.png')
        msg.attach(attachment)

    # 发送邮件
    mail_sender.send_mail(receiver, subject, content, attachFileList=[screenshot_path])
    print("<--send mail with screenshot succeed-->")

def main():
    url = 'https://confluence.ext.net.nokia.com/display/5GHAN/FB2311+-+Blues'  # 要截图的网页 URL
    selector = '#main-content > div:nth-child(3) > table'  # 要截图的表格节点选择器
    receiver = ['hao.6.zhang@nokia-sbell.com']  # 收件人邮箱
    subject = 'Screenshot of Table'  # 邮件主题

    # 发送邮件并附带元素截图
    send_mail_with_screenshot(url, selector, receiver, subject)

if __name__ == '__main__':
    main()
