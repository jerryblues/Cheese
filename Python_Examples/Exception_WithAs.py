# _*_ coding: utf-8 _*_
# @Date    : 2017/11/20
# @Author  : lxie


class Mycontext(object):
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        print "__enter__"
        return self

    def do_self(self):
        print "do_self"

    def __exit__(self, exc_type, exc_value, traceback):
        print "__exit__"
        print "Error:", exc_type, "Info:", exc_value


with Mycontext('test context') as f:
    print f.name
    f.do_self()

ff = Mycontext('\n1111')  # will not from enter and end with exit
print ff.name

'''
__enter__
test context
do_self
__exit__
Error: None Info: None

1111
'''
