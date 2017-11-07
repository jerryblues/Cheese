import pytest


@pytest.mark.skipif("True")  # The test case will skip if condition is True
def test_skipif_1():
    print 'case1'
    assert False


@pytest.mark.skipif("False")
def test_skipif_2():
    print '\ncase2'
    assert False


if __name__ == '__main__':
    pytest.main("test_skipif.py")


'''
s
case2
F
'''