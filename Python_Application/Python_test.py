# coding=utf-8
"""
@file: Python_test.py.py
@time: 2022/3/24 16:43
@author: h4zhang
"""

import time
from datetime import datetime
import pytz


def current_date_time():
    current_date = time.strftime("%w", time.localtime())  # 获取当天的星期数(int)
    current_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
    return current_date, current_time


print("\n===", current_date_time()[1], "===")
