import pytest


@pytest.mark.xfail("False")
def test_xfail_1():
    print 'case1'
    assert False


@pytest.mark.xfail("True")  # The failure test case will not be treated as a failure case if condition is True
def test_xfail_2():
    print '\ncase2'
    assert False


if __name__ == '__main__':
    pytest.main("test_xfail.py")


'''
case1
F
case2
x
'''