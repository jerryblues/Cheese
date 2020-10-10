# coding=utf-8
"""
@file: Python_math.py.py
@time: 2017/11/1 16:42
@author: h4zhang
"""
import random

center = ['a', 'b']
forward = ['d', 'e', 'f', 'g', 'h', 'i', 'c']
guard = ['j', 'k', 'l', 'm', 'n', 'o']
j = 0
for i in range(3):
    if len(center) != 0:
        member1 = random.choice(center)
        center.remove(member1)
    else:
        member1 = random.choice(forward)
        forward.remove(member1)
    member2 = random.choice(forward)
    forward.remove(member2)
    member3 = random.choice(forward)
    forward.remove(member3)
    member4 = random.choice(guard)
    guard.remove(member4)
    member5 = random.choice(guard)
    guard.remove(member5)
    j += 1
    print('team%s: %s,%s,%s,%s,%s' % (j, member1, member2, member3, member4, member5))
