# coding=utf-8
'''
@file: Class_MagicMethod.py
@time: 2017/11/3 17:42
@author: h4zhang
'''


class Student(object):
    def __init__(self, name, age):
        self.name = name
        if isinstance(age, int):
            self.age = age
        else:
            raise Exception('age must be int')

    def __str__(self):  # override str method
        return '%s is %s yesars old' % (self.name, self.age)

    def __add__(self, other):  # override add method
        if isinstance(other, Student):
            return self.age + other.age
        else:
            raise Exception ('the type of object must be Student')


if __name__ == '__main__':
    p1 = Student('jame', 23)
    p2 = Student('tony', 28)
    # p3=Student('tom',23.9)
    print p1 + p2
    print p1

'''
51
jame is 23 yesars old
'''