import pytest


def test_with_exception():  # test case without fixture as param
    with pytest.raises(ZeroDivisionError):  # raises is to check whether it will cause an exception
        1 / 0


def test_without_exception():
    with pytest.raises(RuntimeError):
        1 / 1


if __name__ == '__main__':
    pytest.main("test_raises.py")


'''
.F
------- generated html file: D:\code\Cheese\Pytest_Examples\report.html -------
================================== FAILURES ===================================
___________________________ test_without_exception ____________________________

    def test_without_exception():
        with pytest.raises(RuntimeError):
>           1 / 1
E           Failed: DID NOT RAISE <type 'exceptions.RuntimeError'>

test_raises.py:11: Failed
'''