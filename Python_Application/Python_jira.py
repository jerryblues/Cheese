# coding=utf-8
"""
@file: Python_test2.py.py
@time: 2023/10/8 15:53
@author: h4zhang
"""

from jira import JIRA

# 连接到 JIRA 服务器
jira = JIRA(server='https://jiradc.ext.net.nokia.com', basic_auth=('h4zhang', 'Holmes-09'))

# 获取特定的 Issue
issues = jira.issue('FCA_5G_L2L3-171921')

# 遍历并打印 Issue 的所有属性
for field_name, field_value in issues.fields.__dict__.items():
    if field_name == "customfield_29790":
        print(f"{field_name}: {field_value}")
        # print(dir(field_value))
        print("id:", field_value.id)
        print("name:", field_value.name)
