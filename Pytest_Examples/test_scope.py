import pytest


@pytest.fixture(scope='function')
def fix_func(request):
    print '\nfixture_function setup ==='

    def teardown():
        print '\nfixture_function teardown ==='

    request.addfinalizer(teardown)  # scope=function, after the test function is over, call def teardown
    return 12


def test_fix_func1(fix_func):
    print 'test_case_func1'
    assert 12 == fix_func


def test_fix_func2(fix_func):
    print 'test_case_func2'
    assert 12 == fix_func


@pytest.fixture(scope='class')
def fix_class(request):
    print '\nfixture_class setup ==='

    def teardown():
        print '\nfixture_class teardown ==='

    request.addfinalizer(teardown)  # scope=class, after the test class is ove, call def teardown
    return 12


class TestFixClass:
    def test_fix_class1(self, fix_class):
        print 'test_case_class1'
        assert 12 == fix_class

    def test_fix_class2(self, fix_class):
        print '\ntest_case_class2'
        assert 12 == fix_class


if __name__ == '__main__':
    pytest.main("test_scope.py")


'''
fixture_function setup ===
test_case_func1
.
fixture_function teardown ===

fixture_function setup ===
test_case_func2
.
fixture_function teardown ===

fixture_class setup ===
test_case_class1
.
test_case_class2
.
fixture_class teardown ===
'''