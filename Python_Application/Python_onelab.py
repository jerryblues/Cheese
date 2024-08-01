# coding=utf-8
"""
@file: Python_onelab.py
@time: 2018/9/4 15:56
@author: h4zhang
"""

from selenium import webdriver
import time

drive = webdriver.Chrome()
# drive = webdriver.Firefox()

drive.get("https://onelab.eecloud.dynamic.nsn-net.net/onelab/index.php?m=public&a=login")

url = drive.current_window_handle
drive.switch_to.window(url)

# login
drive.find_element_by_name("account").clear()
drive.find_element_by_name("account").send_keys("xxx")
drive.find_element_by_name("password").clear()
drive.find_element_by_name("password").send_keys("xxx")
drive.find_element_by_id("login_btn").click()
time.sleep(5)

# enter service
drive.find_element_by_id("stage_Asset_1").click()
time.sleep(1)

# enter reserve
drive.find_element_by_class_name("img-rounded").click()
time.sleep(1)

# search ABIL A101
drive.find_element_by_id("searchBox").clear()
drive.find_element_by_id("searchBox").send_keys("474020A.10")
drive.find_element_by_id("own_button").click()
