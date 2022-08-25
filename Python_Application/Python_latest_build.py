# coding=utf-8
"""
@file: Python_spider.py.py
@time: 2022/4/14 16:44
@author: h4zhang
"""

import re
import requests

url = 'http://files.ute.nsn-rdnet.net/builds/enb/base/'
response = requests.get(url)
data = response.text
# print(data)

string = r'SBTS00_ENB_9999_22[0-9]{4}_[0-9]{6}'
build = re.findall(string, data, re.M | re.I)
print(build[-1])

# print(re.findall(r'SBTS00_ENB_9999_22[0-9]{4}_[0-9]{6}', requests.get('http://files.ute.nsn-rdnet.net/builds/enb/base/').text)[-1])
