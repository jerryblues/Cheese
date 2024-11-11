import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import os
import json
from datetime import datetime
import pytz


# 配置起始 URL 和前缀
dedao_url = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91%2F01-%E6%9B%B4%E6%96%B0%E4%B8%AD%E7%9A%84%E8%AF%BE%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89&tag=65&ts=65&recursion=2"
start_with = "http://120.24.70.100/?dir=%2F01%E3%80%90%E5%BE%97Dao+APP%E3%80%91%2F01-%E6%9B%B4%E6%96%B0%E4%B8%AD%E7%9A%84%E8%AF%BE%EF%BC%88%E6%9B%B4%E6%96%B0%E4%B8%AD%EF%BC%89%"
current_texts = set()


def fetch_page(url):
    """获取网页内容并返回解析后的 BeautifulSoup 对象"""
    try:
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return None


def find_subdirectories(url, prefix):
    """查找指定 URL 下的所有下一级目录，且仅返回以指定前缀开头的链接"""
    soup = fetch_page(url)
    if soup:
        subdirectories = []
        # 查找所有链接
        for a_tag in soup.find_all('a', href=True):
            full_url = urljoin(url, a_tag['href'])
            # 检查链接是否为目录且以指定前缀开头
            if is_directory(full_url) and full_url.startswith(prefix):
                subdirectories.append(full_url)
        return subdirectories
    return []


def is_directory(url):
    """判断链接是否为目录（可以根据实际情况调整）"""
    # 这里假设以斜杠结尾的链接为目录
    return url.endswith('/') or 'dir=' in url


if __name__ == "__main__":
    start_url = dedao_url
    prefix = start_with
    subdirs = find_subdirectories(start_url, prefix)

    print("下一级目录:")
    for index, subdir in enumerate(subdirs, start=1):
        print(f"{index}. {subdir}")
