# coding=utf-8
'''
@file: Function_Yield.py
@time: 2017/11/3 17:56
@author: h4zhang
'''


def fab(max):
    n, a, b = 0, 0, 1
    while n < max:
        yield b
        # print b
        a, b = b, a + b
        n = n + 1

for n in fab(5):  # use yield in this way
    print n

'''
1
1
2
3
5
'''
