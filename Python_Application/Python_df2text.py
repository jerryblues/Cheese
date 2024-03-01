# coding=utf-8
"""
@file: Python_df2text.py.py
@time: 2024/3/1 13:30
@author: h4zhang
"""
import pandas as pd


def dataframe_to_text(df):
    """
    将DataFrame中的每一行转换为纯文本格式并返回一个列表
    """
    text_list = []
    for index, row in df.iterrows():
        # 将每行数据转换为纯文本格式
        row_text = ' | '.join(str(cell) for cell in row)
        text_list.append(row_text)
    return text_list


# 使用示例
data = {'Name': ['Alice', 'Bob', 'Charlie'],
        'Age': [25, 30, 35],
        'City': ['New York', 'Los Angeles', 'Chicago']}
df = pd.DataFrame(data)

text_list = dataframe_to_text(df)
for row_text in text_list:
    print(row_text)

print(text_list)
