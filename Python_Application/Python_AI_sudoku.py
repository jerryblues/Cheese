# coding=utf-8
"""
@file: Python_AI_shudu.py.py
@time: 2024/4/23 17:01
@author: h4zhang
"""


def solve_sudoku(board):
    empty = find_empty_location(board)
    if not empty:
        return True  # 没有空位时，解决成功
    row, col = empty

    for num in range(1, 10):
        if is_safe(board, row, col, num):
            board[row][col] = num
            if solve_sudoku(board):
                return True
            board[row][col] = 0  # 回溯

    return False


def find_empty_location(board):
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0:
                return (i, j)
    return None


def is_safe(board, row, col, num):
    # 检查行
    for x in range(9):
        if board[row][x] == num:
            return False
    # 检查列
    for x in range(9):
        if board[x][col] == num:
            return False
    # 检查3x3宫
    start_row = row - row % 3
    start_col = col - col % 3
    for i in range(3):
        for j in range(3):
            if board[i + start_row][j + start_col] == num:
                return False
    return True


# 使用0表示空格
sudoku_board = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 7, 2, 0, 0, 9, 0, 4, 0],
    [1, 0, 0, 7, 0, 4, 5, 0, 9],
    [0, 0, 7, 0, 0, 5, 0, 0, 8],
    [0, 3, 0, 0, 7, 0, 0, 2, 0],
    [4, 0, 0, 1, 0, 0, 7, 0, 0],
    [7, 0, 8, 4, 0, 2, 0, 0, 3],
    [0, 4, 0, 6, 0, 0, 1, 7, 0],
    [2, 5, 0, 3, 0, 0, 0, 0, 4]
]

if solve_sudoku(sudoku_board):
    for row in sudoku_board:
        print(row)
else:
    print("No solution exists")
