import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import os
import json
from datetime import datetime
import pytz

# 配置起始 URL 和前缀
start_url = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91"
prefix = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91"
current_texts = set()

def get_current_time():
    china_tz = pytz.timezone('Asia/Shanghai')  # 设置中国时区
    return datetime.now(china_tz).strftime("%Y-%m-%d %H:%M:%S")  # 获取当前时间

def is_valid_url(url):
    """检查 URL 是否有效且以指定前缀开头"""
    return url.startswith(prefix)

def fetch_page(url):
    """获取网页内容并返回解析后的 BeautifulSoup 对象"""
    try:
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return None

def find_links(soup):
    """从 BeautifulSoup 对象中提取所有链接"""
    links = []
    for a_tag in soup.find_all('a', href=True):
        full_url = urljoin(start_url, a_tag['href'])
        if is_valid_url(full_url):
            links.append(full_url)
    return links

def fetch_content(urls):
    global current_texts
    all_current_files = set()  # 用于存储所有 URL 的文件名

    for url in urls:
        try:
            soup = fetch_page(url)
            if soup:
                # 提取所有包含文件名的 span 标签
                current_content = soup.find_all('span', class_='lineText')

                # 提取文本内容
                current_texts = [item.get_text(strip=True) for item in current_content]

                # # 正则表达式模式
                # pattern = r'(\d{4}丨[^/]+\.mp3)'
                #
                # # 根据 URL 判断是否需要使用正则表达式
                # if url != url_gengxinzhong:
                #     # 使用正则表达式筛选出符合格式的文件名
                #     for text in current_texts:
                #         match = re.search(pattern, text)
                #         if match:
                #             all_current_files.add(match.group(1))
                # else:
                #     # 对于不需要正则处理的 URL，直接添加所有文本内容
                #     all_current_files.update(current_texts)

        except Exception as e:
            print(f"Error fetching from {url}: {e}")

    # 排序并打印当前文件集合
    print("[Current texts]:")
    for file in sorted(current_texts):
        print(file)

    # 读取上次的结果
    previous_files = load_previous_result()

    # 比较新旧文件
    new_files = all_current_files - previous_files
    if new_files:
        current_time = get_current_time()  # 获取当前时间
        message_today = f"[{current_time}] - New updates:\n" + "\n".join(f"- {item}" for item in sorted(new_files))
        print(f"[{current_time}] - New updates:\n" + "\n".join(f"- {item}" for item in sorted(new_files)))

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
        json.dump(list(sorted(current_files)), f, ensure_ascii=False)

def crawl_and_fetch_content(start_url):
    visited_urls = set()
    to_visit_urls = [start_url]

    while to_visit_urls:
        current_url = to_visit_urls.pop()
        if current_url not in visited_urls:
            visited_urls.add(current_url)
            print(f"访问: {current_url}")
            soup = fetch_page(current_url)
            if soup:
                links = find_links(soup)
                to_visit_urls.extend(links)

    fetch_content(visited_urls)

if __name__ == "__main__":
    crawl_and_fetch_content(start_url)
