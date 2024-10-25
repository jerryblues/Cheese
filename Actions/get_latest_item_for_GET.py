import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import pytz

# 监控的网页URL
url = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91%2F06-%E6%AF%8F%E5%A4%A9%E5%90%AC%E4%B9%A6%EF%BC%88VIP%EF%BC%89365%E5%85%83%2F2024%E5%B9%B4&tag=65&ts=65&recursion=2"

def get_current_time():
    china_tz = pytz.timezone('Asia/Shanghai')  # 设置中国时区
    return datetime.now(china_tz).strftime("%Y-%m-%d %H:%M:%S")  # 获取当前时间

def fetch_content():
    try:
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功
        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取所有包含文件名的 span 标签
        current_content = soup.find_all('span', class_='lineText')

        # 提取文本内容
        current_texts = [item.get_text(strip=True) for item in current_content]

        # 正则表达式模式
        pattern = r'(\d{2}\.\d{4}丨[^/]+\.mp3)'

        # 使用正则表达式筛选出符合格式的文件名
        current_files = set()
        for text in current_texts:
            match = re.search(pattern, text)
            if match:
                current_files.add(match.group(1))

        # 排序并打印当前文件集合
        print("[Current files]:")
        for file in sorted(current_files):
            print(file)

        # 获取当前和前一天的日期
        today = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%m%d")  # 格式为 MMDD
        yesterday = (datetime.now(pytz.timezone('Asia/Shanghai')) - timedelta(days=1)).strftime("%m%d")
        message_content_today, message_content_yesterday = [], []

        # 检查文件名中是否包含当天和昨天的日期
        for file in current_files:
            if today in file:
                message_content_today.append(file)
            if yesterday in file:
                message_content_yesterday.append(file)

        # 发送通知
        if message_content_today:
            current_time = get_current_time()  # 获取当前时间
            message_today = f"[{current_time}] - Today's update:\n" + "\n".join(f"- {item}" for item in message_content_today)
            print(f"[{current_time}] - Today's update:\n" + "\n".join(f"- {item}" for item in message_content_today))
            send_notification_to_feishu(message_today)
        else:
            print(f"[{get_current_time()}] - [no update for today]")

        if message_content_yesterday:
            current_time = get_current_time()  # 获取当前时间
            message_yesterday = f"[{current_time}] - Yesterday's update:\n" + "\n".join(f"- {item}" for item in message_content_yesterday)
            print(f"[{current_time}] - Yesterday's update:\n" + "\n".join(f"- {item}" for item in message_content_yesterday))
        else:
            print(f"[{get_current_time()}] - [no update for yesterday]")

    except Exception as e:
        print(f"err: {e}")

def send_notification_to_feishu(message):
    webhook_url = 'https://open.feishu.cn/open-apis/bot/v2/hook/8b2f29c3-1ef2-4c61-8996-e9a98dc0e92e'  # 替换为你的 Webhook URL
    headers = {'Content-Type': 'application/json'}

    # 构建消息体
    payload = {
        "msg_type": "text",
        "content": {
            "text": message
        }
    }

    # 发送 POST 请求
    response = requests.post(webhook_url, headers=headers, json=payload)

    # 检查响应
    if response.status_code == 200:
        print("Notification sent successfully!")
    else:
        print(f"Failed to send notification: {response.status_code}, {response.text}")

if __name__ == "__main__":
    fetch_content()
