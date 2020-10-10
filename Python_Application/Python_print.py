# coding=utf-8
"""
@file: Python_print.py
@time: 2019/4/2 13:08
@author: h4zhang
"""

print('%f' % 1.11)  # 默认保留6位小数

print('%.1f' % 1.11)  # 取1位小数

print('%e' % 1.11)  # 默认6位小数，用科学计数法

print('%.3e' % 1.11)  # 取3位小数，用科学计数法

print('%g' % 1111.1111)  # 默认6位有效数字

print('%.2g' % 1111.1111)  # 取2位有效数字，自动转换为科学计数法

print('\n' * 3)  # n为行数，换3行

print("account/pwd:\nadmin/123")

for i in range(10):
    print('%s ' % i),  # 不换行打印
