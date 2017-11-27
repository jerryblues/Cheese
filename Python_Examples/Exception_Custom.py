# _*_ coding: utf-8 _*_
# @Date    : 2017/11/20
# @Author  : lxie


class CustomError(Exception):  # inherit exception
    def __init__(self, info):
        Exception.__init__(self)
        self.errorinfo = info
        print id(self)  # print the id of it

    def __str__(self):  # override
        return "CustomError:%s" % self.errorinfo


try:
    raise CustomError("test CustomError")
except CustomError, e:
    print "ErrorInfo:%d,%s" % (id(e), e)

'''
42675216
ErrorInfo:42675216,CustomError:test CustomError
'''
