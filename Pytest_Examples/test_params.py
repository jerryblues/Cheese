import pytest


@pytest.fixture(params=[1, 2])  # define fixture params, only can use params and param
def fix_func(request):
    return request.param  # to get a value from fixture params parameter


def test_params(fix_func):  # call test case twice
    print '\n1 == %s?' %fix_func
    assert 1 == fix_func


if __name__ == '__main__':
    pytest.main("test_params.py")


'''
1 == 1?
.
1 == 2?
F
'''