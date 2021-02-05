# coding=utf-8
"""
@file: Python_factorization.py
@time: 2019/4/2 12:53
@author: h4zhang
"""

# 因式分解
# 7140229933
# 6541367***

i = 2
a = 34
r = list()

while i <= a - 1:
    if (a % i == 0):
        r.append(i)
        print('%s ' % i),
    i = i + 1
print('\n')

if len(r):
    print(r)
else:
    print('no result')
