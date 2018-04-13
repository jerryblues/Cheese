# coding=utf-8
"""
@file: Python_math.py.py
@time: 2017/11/1 16:42
@author: h4zhang
"""

import math

while True:
    ori = float(raw_input('original acccount = '))
    now = float(raw_input('now account = '))
    yea = float(raw_input('year = '))
    # now = ori * (1 + rate%) ^ yea

    print 'rate = %.2f' % (100 * (math.pow(now / ori, 1.0 / yea) - 1)) + '%\n'

    goon = raw_input("go on? 1 for go, other for no: ")
    if goon != '1':
        break
print 'exit'
