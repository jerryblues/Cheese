import pytest


@pytest.fixture
def fix_func(request):
    def teardown():
        print '\nteardown...'

    request.addfinalizer(teardown)  # to declare a function which will be invoked when fixture will be destructed
    print 'setup...'
    return 'doing...'


def test_request(fix_func):
    print fix_func


if __name__ == '__main__':
    pytest.main("test_request.py")



'''
setup...
doing...
.
teardown...
'''