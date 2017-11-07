# coding=utf-8
'''
@file: Class_Restricting.py
@time: 2017/11/3 16:29
@author: h4zhang
'''


class Student(object):
    def __init__(self, name, score, age):
        self.__name = name  # name attribute is private, can't call directly
        self._score = score  # score attribute is protected, should not call usually
        self.__age = age  # age attribute is private, can't call directly

    def print_score(self):
        print ('%s:%s:%s' % (self.__name, self._score, self.__age))

    def get_name(self):  # private attribute can be called by using this method
        return self.__name

    def set_age(self, age):  # private attribute can be called by using this method
        self.__age = age


jame = Student('Jame simpson', 80, 30)
# print jame.__name  # can't call __name, 'Student' object has no attribute '__name'
jame.print_score()
print jame._score
# print jame.__age  # can't call __age, 'Student' object has no attribute '__age'
print jame._Student__name  # private attribute can be called by using in this way
print jame.get_name()  # private attribute can be called by using in this way
jame.set_age(20)
jame.print_score()

'''
Jame simpson:80:30
80
Jame simpson
Jame simpson
Jame simpson:80:20
'''
