# coding=utf-8
'''
@file: Class_Classmethod_Property.py
@time: 2017/11/3 17:09
@author: h4zhang
'''


class Student(object):
    hobby = "Hello python"

    def __init__(self, name, age, weight):
        self.name = name
        self._age = age
        self.__weight = weight

    @classmethod
    def get_hobby(cls):
        return cls.hobby

    @property  # turn get_weight to an attribute of the instance class
    def get_weight(self):
        return self.__weight

    def self_introduction(self):
        print('My name is %s, I am %s years old\n' % (self.name, self._age))


if __name__ == '__main__':  # entrance of this program
    a_student = Student('jake', 28, 80)
    print Student.get_hobby()  # no need to create an instance by using classmethod
    print a_student.get_weight  # get_weight is an attribute of the instance class
    a_student.self_introduction()

'''
Hello python
80
My name is jake, I am 28 years old
'''
