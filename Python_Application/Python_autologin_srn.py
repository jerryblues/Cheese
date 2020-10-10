# coding=utf-8
"""
@file: Python_autologin_srn.py
@time: 2018/4/13 13:19
@author: h4zhang
"""

from selenium import webdriver
import time

drive = webdriver.Chrome()
# drive = webdriver.Firefox()

drive.get("http://authresponse.srnhz.nsn-rdnet.net/")
# aa = drive.get_cookies()
# print('aa=', aa)

url = drive.current_window_handle
drive.switch_to.window(url)

drive.find_element_by_name("username").clear()
drive.find_element_by_name("username").send_keys("h4zhang@nsn-intra")
drive.find_element_by_name("password").clear()
drive.find_element_by_name("password").send_keys("Holmes-0")

time.sleep(0.5)
drive.find_element_by_id("btnSubmit_6").click()

# bb = drive.get_cookies()
# print('bb=', bb)

# drive.quit()
