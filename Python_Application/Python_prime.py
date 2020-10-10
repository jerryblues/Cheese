# coding=utf-8
"""
@file: Python_prime.py
@time: 2019/4/2 10:39
@author: h4zhang
"""

# 找质数

import time

start = time.clock()

# i = input('please enter  an integer:')
i = 100

# 创建一个空list
r = list()

# 添加元素2
r.append(2)

# 从3开始挨个筛选
a = 3
while a <= i:
    b = False
    a = a + 1
    # 用a除以小于a的质数b
    for b in r:
        if a % b == 0:
            c = False
            break
        else:
            c = True
    if c is True:
        r.append(a)
        print(b, end=' ')
print('\n')
print(r)
print('\n')
t = (time.clock() - start)
print('time cost: %.6f' % t)
