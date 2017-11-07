import pytest


@pytest.mark.testmark
def test_1():
    print 'case1'
    assert False


def test_2():
    print 'case2'
    assert False


if __name__ == '__main__':
    pytest.main('test_mark.py -m testmark')


'''
case1
F
'''