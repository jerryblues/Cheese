# coding=utf-8
'''
@file: Class_Inheritance_Override.py
@time: 2017/11/3 16:47
@author: h4zhang
'''


class Student(object):
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def self_introduction(self):
        print ('my name is %s, I am %s years old' % (self.name, self.age))


class SubStudent(Student):
    def __init__(self, name, age, weight):  # add attribute weight
        super(SubStudent, self).__init__(name, age)  # inheritance attribute name and age
        self.weight = weight

    def self_introduction(self):  # override method
        print('my name is %s, my age is %s, my weight is %s' % (self.name, self.age, self.weight))


class NotStudent(object):
    def __init__(self, number, color):
        self.number = number
        self.color = color


def introduce(student):
    if isinstance(student, Student):  # whether student is subclass of Student
        student.self_introduction()
    else:
        print 'not a student'


a_student = Student('Jerry', 25)
a_student.self_introduction()
b_student = SubStudent('Tom', 30, 80)
b_student.self_introduction()
introduce(b_student)
c_student = NotStudent(10, 'red')
introduce(c_student)

'''
my name is Jerry, I am 25 years old
my name is Tom, my age is 30, my weight is 80
my name is Tom, my age is 30, my weight is 80
not a student
'''
