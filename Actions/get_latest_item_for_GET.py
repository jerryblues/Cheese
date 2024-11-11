from base64 import urlsafe_b64decode

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import pytz
import json
import os

# 监控的网页 URL 列表
url_ai = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91%2F07-%E3%80%8AAI%E5%AD%A6%E4%B9%A0%E5%9C%88%E3%80%8B399%E5%85%83%2F01%E4%B8%A8%E5%BF%AB%E5%88%80%E5%B9%BF%E6%92%AD%E7%AB%99%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89&tag=65&ts=65&recursion=2"
url_zhichang = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91%2F08-%E3%80%8A%E8%81%8C%E5%9C%BA%E5%AD%A6%E4%B9%A0%E5%9C%88%E3%80%8B399%E5%85%83%2F%EF%BC%8800%E4%B8%A8%E8%8A%B1%E5%A7%90%E4%BF%A1%E7%AE%B1%EF%BC%89&tag=65&ts=65&recursion=2"
url_xinli = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91%2F09-%E3%80%8A%E5%BF%83%E7%90%86%E6%88%90%E9%95%BF%E5%9C%88%E3%80%8B%EF%BF%A5399%E5%85%83%2F%EF%BC%8800%E4%B8%A8%E6%AF%8F%E5%A4%A9%E6%87%82%E7%82%B9%E5%BF%83%E7%90%86%E5%AD%A6%E4%B8%A8%E6%97%A5%E6%9B%B4%E5%A4%B4%E6%9D%A1%EF%BC%89&tag=65&ts=65&recursion=2"
url_tingshu = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91%2F06-%E6%AF%8F%E5%A4%A9%E5%90%AC%E4%B9%A6%EF%BC%88VIP%EF%BC%89365%E5%85%83%2F2024%E5%B9%B4&tag=65&ts=65&recursion=2"

url_wangweigang = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91%2F01-%E6%9B%B4%E6%96%B0%E4%B8%AD%E7%9A%84%E8%AF%BE%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89%2F%EF%BF%A5299%E5%85%83-%E4%B8%87%E7%BB%B4%E9%92%A2%C2%B7%E3%80%8A%E7%B2%BE%E8%8B%B1%E6%97%A5%E8%AF%BE%C2%B7%E7%AC%AC%E5%85%AD%E5%AD%A3%E3%80%8B%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89&tag=65&ts=65&recursion=2"
url_wujun = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91%2F01-%E6%9B%B4%E6%96%B0%E4%B8%AD%E7%9A%84%E8%AF%BE%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89%2F%EF%BF%A5299%E5%85%83-%E5%90%B4%E5%86%9B%C2%B7%E3%80%8A%E5%90%B4%E5%86%9B%E6%9D%A5%E4%BF%A12%E3%80%8B%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89&tag=65&ts=65&recursion=2"
url_zhuoke = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91%2F01-%E6%9B%B4%E6%96%B0%E4%B8%AD%E7%9A%84%E8%AF%BE%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89%2F%EF%BF%A5299%E5%85%83-%E5%8D%93%E5%85%8B%C2%B7%E3%80%8A%E7%A7%91%E6%8A%80%E5%8F%82%E8%80%834%E3%80%8B%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89&tag=65&ts=65&recursion=2"
url_hegang = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91%2F01-%E6%9B%B4%E6%96%B0%E4%B8%AD%E7%9A%84%E8%AF%BE%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89%2F%EF%BF%A5399%E5%85%83-%E4%BD%95%E5%88%9A%C2%B7%E3%80%8A%E6%8A%95%E8%B5%84%E5%8F%82%E8%80%832024-2025%E3%80%8B%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89&tag=65&ts=65&recursion=2"
url_xiongtaihang = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91%2F01-%E6%9B%B4%E6%96%B0%E4%B8%AD%E7%9A%84%E8%AF%BE%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89%2F%EF%BF%A5299%E5%85%83-%E7%86%8A%E5%A4%AA%E8%A1%8C%C2%B7%E3%80%8A%E5%85%B3%E7%B3%BB%E6%94%BB%E7%95%A52%E3%80%8B%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89&tag=65&ts=65&recursion=2"

url_xiangshuai = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91%2F01-%E6%9B%B4%E6%96%B0%E4%B8%AD%E7%9A%84%E8%AF%BE%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89%2F%EF%BF%A599%E5%85%83-%E9%A6%99%E5%B8%85%C2%B7%E3%80%8A2025%E5%B9%B4%E5%BA%A6%E5%BE%97%E5%88%B0%C2%B7%E9%A6%99%E5%B8%85%E4%B8%AD%E5%9B%BD%E8%B4%A2%E5%AF%8C%E6%8A%A5%E5%91%8A%E3%80%8B%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89&tag=65&ts=65&recursion=2"
url_hefan = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91%2F01-%E6%9B%B4%E6%96%B0%E4%B8%AD%E7%9A%84%E8%AF%BE%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89%2F%EF%BF%A599%E5%85%83-%E4%BD%95%E5%B8%86%C2%B7%E3%80%8A2025%E5%B9%B4%E5%BA%A6%E5%BE%97%E5%88%B0%C2%B7%E4%BD%95%E5%B8%86%E4%B8%AD%E5%9B%BD%E7%BB%8F%E6%B5%8E%E6%8A%A5%E5%91%8A%E3%80%8B%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89&tag=65&ts=65&recursion=2"
url_laoyu = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91%2F01-%E6%9B%B4%E6%96%B0%E4%B8%AD%E7%9A%84%E8%AF%BE%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89%2F%EF%BF%A5229%E5%85%83-%E8%80%81%E5%96%BB%C2%B7%E3%80%8A%E5%86%B3%E7%AD%96%E7%AE%97%E6%B3%95100%E8%AE%B2%E3%80%8B%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89&tag=65&ts=65&recursion=2"
url_liuyi = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91%2F01-%E6%9B%B4%E6%96%B0%E4%B8%AD%E7%9A%84%E8%AF%BE%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89%2F%EF%BF%A5299%E5%85%83-%E5%88%98%E6%80%A1%C2%B7%E3%80%8A%E5%85%A8%E7%90%83%E5%A4%A7%E4%BA%8B%E6%8A%A5%E5%91%8A%E3%80%8B%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89&tag=65&ts=65&recursion=2"

url_gengxinzhong = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91%2F01-%E6%9B%B4%E6%96%B0%E4%B8%AD%E7%9A%84%E8%AF%BE%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89&tag=65&ts=65&recursion=2"

urls = [url_ai, url_zhichang, url_xinli, url_tingshu, url_wangweigang, url_wujun, url_zhuoke, url_hegang, url_xiongtaihang, url_xiangshuai, url_hefan, url_laoyu, url_liuyi, url_gengxinzhong]

def get_current_time():
    china_tz = pytz.timezone('Asia/Shanghai')  # 设置中国时区
    return datetime.now(china_tz).strftime("%Y-%m-%d %H:%M:%S")  # 获取当前时间

def fetch_content():
    all_current_files = set()  # 用于存储所有 URL 的文件名

    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()  # 检查请求是否成功
            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取所有包含文件名的 span 标签
            current_content = soup.find_all('span', class_='lineText')

            # 提取文本内容
            current_texts = [item.get_text(strip=True) for item in current_content]
            # print(current_content)

            # 正则表达式模式
            # pattern = r'(\d{4}丨[^/]+\.mp3)'
            pattern_mp3 = r'([^/]+\.mp3)'  # 只匹配后缀是mp3的文件
            pattern_text = r'(￥.*)'


            # 使用正则表达式筛选出符合格式的文件名
            for text in current_texts:
                if url != url_gengxinzhong:
                    match = re.search(pattern_mp3, text)
                    if match:
                        all_current_files.add(match.group(1))
                else:
                    match = re.search(pattern_text, text)
                    if match:
                        all_current_files.add(match.group(1))

        except Exception as e:
            print(f"Error fetching from {url}: {e}")

    # 排序并打印当前文件集合
    print("[Current files]:")
    for file in sorted(all_current_files):
        print(file)

    # 读取上次的结果
    previous_files = load_previous_result()

    # 比较新旧文件
    new_files = all_current_files - previous_files
    if new_files:
        current_time = get_current_time()  # 获取当前时间
        message_today = f"[{current_time}] - New updates:\n" + "\n".join(f"- {item}" for item in sorted(new_files))
        print(f"[{current_time}] - New updates:\n" + "\n".join(f"- {item}" for item in sorted(new_files)))
        send_notification_to_feishu(message_today)
    else:
        print(f"[{get_current_time()}] - [no new updates]")

    # 保存当前结果
    save_current_result(all_current_files)

def load_previous_result():
    if os.path.exists("previous_result.json"):
        with open("previous_result.json", "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_current_result(current_files):
    with open("previous_result.json", "w", encoding="utf-8") as f:
        json.dump(list(sorted(current_files)), f, ensure_ascii=False)  # 确保中文字符以可读形式保存，并且按字符排序，如果没有变化，就不会触发新的commit

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
