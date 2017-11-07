# coding=utf-8
'''
@file: Class_WithAs.py
@time: 2017/11/3 17:49
@author: h4zhang
'''


class Sample(object):
    def __enter__(self):
        print ('this is enter')
        return self

    def __exit__(self, type, value, trace):
        print 'this is exit'
        print 'type:', type
        print 'value:', value
        print 'trace:', trace

    def do_something(self):
        bar = 5 / 0
        return bar + 10


with Sample() as sample:  # instance Sample and begin with enter method, end with exit method
    print(sample.do_something())

'''
this is enter
Traceback (most recent call last):
this is exit
  File "D:/code/Cheese/Python_Examples/Class_WithAs.py", line 26, in <module>
type: <type 'exceptions.ZeroDivisionError'>
    print(sample.do_something())
value: integer division or modulo by zero
trace: <traceback object at 0x02793C88>
  File "D:/code/Cheese/Python_Examples/Class_WithAs.py", line 21, in do_something
    bar = 5 / 0
ZeroDivisionError: integer division or modulo by zero
'''
