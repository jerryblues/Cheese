# _*_ coding: utf-8 _*_
# @Date    : 2017/11/20
# @Author  : lxie

try:
    f = open('testfile.txt')
    print f
    line = f.read(4)  # read the former 4 character in the file
    num = int(line)
    print "read num = %d" % num
except IOError, e:
    print "catch IOError:", e
except ValueError, e:
    print "catch ValueError:", e
else:
    print "no error"
finally:
    try:
        f.close()
        print "file closed"
    except NameError, e:
        print "catch error", e

'''
<open file 'testfile.txt', mode 'r' at 0x01F5A1D8>
catch ValueError: invalid literal for int() with base 10: '100a'
file closed
'''
