# coding=utf-8
'''
@file: Function_Lambda.py
@time: 2017/11/3 14:44
@author: h4zhang
'''


def fuc(x, y=2):
    return x + y


# the same as:
# lambda x, y=2 : x + y


print fuc(1, 3)

'''
===result===
4
'''