from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import pandas as pd
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
import json
import requests
from datetime import datetime, timedelta
import pytz
import re
import holidays


headers = {
    'Authorization': 'Token d8c42b66120fdbec8fdf6fe7c27c849e045970c1'}


def ask_question(question):
    # API URL
    url = "https://burn.hair/v1/chat/completions"

    headers = {
        "Authorization": "Bearer sk-ySOZXKC68tIwP6e8Bb3689Cb914044Bc90B51c8a321e6c15"
    }

    # 构造请求体
    data = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "system",
                "content": "You are a software development expert, a testing expert, adept at analyzing log files. After I provide you with the {log content}, tell me in one sentence where the main error lies.",
            },
            {
                "role": "user",
                "content": question
            }
        ],
        "temperature": 0.7
    }

    # 发送POST请求
    response = requests.post(url, headers=headers, json=data)

    # 检查响应状态码
    if response.status_code == 200:
        # 解析响应内容
        response_data = response.json()
        # 假设API响应的结构包含回复内容
        return response_data.get("choices", [{}])[0].get("message", {}).get("content", "无法获取回复。")
    else:
        return f"请求失败，状态码：{response.status_code}"


def get_log_content():
    # 创建一个Session对象
    session = requests.Session()
    # 登录URL
    login_url = 'https://cloud.ute.nsn-rdnet.net/user/login?'
    # 获取登录页面，确保Cookies被设置
    session.get(login_url)
    # 从Cookies中获取CSRF令牌
    csrf_token = session.cookies.get('csrftoken')
    # 登录信息，包括用户名、密码和CSRF令牌
    login_data = {
        'username': 'xxx',
        'password': 'xxx',
        'csrfmiddlewaretoken': csrf_token  # 添加CSRF令牌到请求数据中
    }
    print(f"[1.0] <-- CSRF token: [{csrf_token}] -->")

    # 发送登录请求
    response = session.post(login_url, data=login_data)
    # print(response.text)

    url_log = "http://logs.ute.nsn-rdnet.net/cloud/execution/16923459/execution_for_preparation_69ad99e5-00a1-4d73-9893-9ccef605c1f5/test_results/log.html"
    # url_log2 = "http://logs.ute.nsn-rdnet.net/cloud/execution/16923458/execution_for_preparation_43aaf284-e62d-417b-b9a3-8ab362bb1fbc/test_results/log.html"
    # 使用 session 获取 response
    response = session.get(url_log, headers=headers)
    # print(response.text)  # 打印响应文本

    # soup = BeautifulSoup(response.text, 'lxml')
    # print(soup)

    # find the error log
    pattern = r'"ERR/:\s*([^"]*)"'
    matches = re.findall(pattern, response.text)
    error_log = ', '.join(matches)
    return error_log


if __name__ == "__main__":
    err_log_content = get_log_content()
    print(f'error log:\n{err_log_content}')
    reply = ask_question(err_log_content)
    print(f'log analyze result:\n{reply}')
