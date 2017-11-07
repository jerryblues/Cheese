import src  # import ut code
import pytest


def test_add():
    for i in range(3):
        for j in range(5):
            print i, j, src.add(i, j)  # use ut code
            assert i + j == src.add(i, j)


if __name__ == '__main__':
    pytest.main("test_ut.py")


'''
0 0 0
0 1 1
0 2 2
0 3 3
0 4 4
1 0 1
1 1 2
1 2 3
1 3 4
1 4 5
2 0 2
2 1 3
2 2 4
2 3 5
2 4 6
.
'''