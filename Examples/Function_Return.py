# coding=utf-8
'''
@file: Function_Return.py
@time: 2017/11/3 9:49
@author: h4zhang
'''


def foo():
    return ['xyx', 1000, -92]


def bar():
    return 'abc', [12, 'python'], "guide"


alist = foo()
aTuple = bar()
x, y, z = bar()
(a, b, c) = bar()
print (alist)
print (aTuple)
print (x, y, z)
print (a, b, c)
