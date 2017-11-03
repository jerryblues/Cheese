# coding=utf-8
'''
@file: Function_Closures.py
@time: 2017/11/3 15:18
@author: h4zhang
'''

# function's scope
# LEGB: L>E>G>B
# L:local E:enclosing G:global B:build-in

passline = 110


def set_passline(passline):
    def cmp(val):
        if val >= passline:
            print'pass'
        else:
            print'failed'

    return cmp


f_100 = set_passline(60)  # 1、set passline=60, 2、set f_100 refer to cmp
f_150 = set_passline(90)
f_100(89)  # set 89=val，compare with passline
f_150(89)

'''
===result===
pass
failed
'''
