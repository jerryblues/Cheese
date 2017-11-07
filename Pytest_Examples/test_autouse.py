import pytest


def test_autouse():  # fixture is autouse, no need to call it in test case
    pass


@pytest.fixture(autouse=True)
def fix_func():
    print 'hello, world'


if __name__ == '__main__':
    pytest.main("test_autouse.py")


'''
hello, world
.
'''