# _*_ coding: utf-8 _*_
# @Date    : 2017/11/20
# @Author  : lxie

import os

# try:
#     f = open('myfile.txt')
#     print "in try f.read():", f.read(2)
#     f.seek(-5, os.SEEK_SET)
# except IOError, e:
#     print "catch IOError:", e
# except ValueError, e:
#     print "catch ValueError", e
# finally:
#     f.close()
# print "try-finally:", f.closed

# with open('myfile.txt') as f1:
#     print "in with f1.read():", f1.read(2)
#     f1.seek(-5, os.SEEK_SET)
# print "with:", f1.closed

try:
    with open('testfile.txt') as f1:
        print "read 6 characters in the file:", f1.read(6)
        f1.seek(-5, os.SEEK_SET)  # os.SEEK_SET:相对文件起始位置-5
except IOError, e:
    print "Error info:", e
    print "file closed:", f1.closed

'''
read 6 characters in the file: 100aaa
Error info: [Errno 22] Invalid argument
file closed: True
'''