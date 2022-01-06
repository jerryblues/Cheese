# coding=utf-8
'''
@file: Function_Decorator.py
@time: 2017/11/3 15:40
@author: h4zhang
'''


def dec(func):
    def in_dec(*arg):
        if len(arg) == 0:  # whether arg is null
            return 'none'
        for val in arg:  # whether arg is int
            if not isinstance(val, int):
                return 'not int'
        return func(*arg) + 1

    return in_dec


@dec
def mysum(*arg):
    return sum(arg)


# same as: mysum=dec(mysum) and should write it here.

print(mysum(1, 2, 3))
# 1.parameter send to *arg 2. run mysum=dec(mysum) 3.send mysum to fuc, and the new mysum refer to the return of dec,which is in_dec
print(mysum())
print(mysum(1, 2, 3, '6'))

'''
===result===
7
none
not int
'''
