# coding=utf-8
'''
@file: Class_Basic.py
@time: 2017/11/3 16:25
@author: h4zhang
'''


class Student(object):  # default inheritance from object
    def __init__(self, name, score):
        self.name = name
        self.score = score

    def print_socre(self):
        print '%s:%s' % (self.name, self.score)

    def get_grade(self):
        if self.score >= 90:
            return 'a'
        else:
            return 'b'


bart = Student('Bart simpson', 80)
bart.print_socre()
print (bart.get_grade())
bart.age = 8
print (bart.age)
Student.age = 10
print(Student.age)
print (bart.age)
bart.score = 90
print (bart.get_grade())


'''
Bart simpson:80
b
8
10
8
a
'''
