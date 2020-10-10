# coding=utf-8
"""
@file: Python_math.py.py
@time: 2017/11/1 16:42
@author: h4zhang
"""
import math
from pip._vendor.distlib.compat import raw_input

while True:
    ori = float(raw_input('original acccount = '))
    now = float(raw_input('now account = '))
    yea = float(raw_input('year = '))
    # now = ori * (1 + rate%) ^ yea
    print('rate = %.2f' % (100 * (math.pow(now / ori, 1.0 / yea) - 1)) + '%\n')
    goon = raw_input("go on? 1 for go, other for no: ")
    if goon != '1':
        break
print('exit')

# ori_amount = 10000
# ori_rate = 0.0001
# all_rating = 0
#
# for i in range(101):
#     left_amount = ori_amount - 100 * i
#     print 'left_amount: %.2f' % left_amount
#
#     rating = left_amount * ori_rate
#     print 'rating: %.2f' % rating
#
#     all_rating = all_rating + rating
#     print 'all_rating: %.2f' % all_rating
#
#     new_amount = left_amount + all_rating
#     print 'new_amount: %.2f' % new_amount
#     print '==='
#
# new_rate = all_rating / ori_amount / i
# print 'for %s days' % i
# print 'new_rate: %f' % new_rate
