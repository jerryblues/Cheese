# coding=utf-8
'''
@file: Function_Arguments.py
@time: 2017/11/2 18:00
@author: h4zhang
'''


def newfoo(arg1, arg2='defaultC', *nkw, **kw):
    print'arg1 is:', arg1
    print'arg2 is:', arg2
    for eachNKW in nkw:
        print 'additional non-key arg:', eachNKW
    for eachkw in kw.keys():
        print "additional keyword age '%s':%s" % (eachkw, str(kw[eachkw]))


newfoo('one', 3, 'abc', 'zzsd', c=123, b='xyz', z=45.68, )

print '\n'


def dictVarAgs(arg1, arg2='defaultC', **theRest):
    print'formal arg1:', arg1
    print'formal arg2:', arg2
    for eachXtrArg in theRest.keys():
        print'Xtra arg %s:%s' % (eachXtrArg, str(theRest[eachXtrArg]))


dictVarAgs('one', c=123, b='xyz', z=45.68)


'''
===result===
arg1 is: one
arg2 is: 3
additional non-key arg: abc
additional non-key arg: zzsd
additional keyword age 'c':123
additional keyword age 'b':xyz
additional keyword age 'z':45.68


formal arg1: one
formal arg2: defaultC
Xtra arg c:123
Xtra arg b:xyz
Xtra arg z:45.68
'''
