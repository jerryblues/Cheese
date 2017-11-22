import pytest


@pytest.mark.parametrize('aaa', ('111','222','333'))  # define test case params
def test_parametrize(aaa):
    print '\n222 == %s?' %aaa
    assert '222' == aaa


if __name__ == '__main__':
    pytest.main("test_parametrize.py")


'''
222 == 111?
F
222 == 222?
.
222 == 333?
F
'''