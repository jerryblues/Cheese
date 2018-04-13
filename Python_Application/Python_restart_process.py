# coding=utf-8
"""
@file: Python_restart_process.py
@time: 2018/4/13 14:06
@author: h4zhang
"""

import os
import time

command_stop = 'taskkill /f /im CiscoJabber.exe'
time.sleep(1)
command_start = 'start C:\Progra~2\CiscoS~1\CiscoJ~1\CiscoJabber.exe'
# 采用8个字符缩写，即头6个字母（略去空格），另加波浪号和数字，首字母不足6个字母，用第二个词的字母，凑成6个

os.system(command_stop)
os.system(command_start)
