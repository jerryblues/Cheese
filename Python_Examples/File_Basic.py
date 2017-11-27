# _*_ coding: utf-8 _*_
# @Date    : 2017/11/21
# @Author  : lxie

f = open('testfile.txt', 'w+')
f.write('100')
f.write('aaa')
f.write('bbb')
print "文件名:", f.name
print "文件是否已关闭:", f.closed
print "访问模式:", f.mode
print "文件末尾是否强制加空格:", f.softspace
f.close()
print "文件是否已关闭:", f.closed

f = open('testfile.txt')
print '\n'
print f.read(3)
print f.read(3)
f.seek(1, 0)  # == f.seek(1, os.SEEK_SET) back to the 1st character
'''
os.SEEK_SET:相对文件起始位置，可用0表示
os.SEEK_CUR:相对文件当前位置，可用1表示
os.SEEK_END:相对文件结尾位置，可用2表示
'''
print f.read(2)
print f.readline(1)
print f.readline(40)
print len(f.readlines(1))
f.close()

'''
文件名: testfile.txt
文件是否已关闭: False
访问模式: w+
文件末尾是否强制加空格: 0
文件是否已关闭: True

100
aaa
00
a
aabbb
0
'''
