import pandas as pd
import numpy as np
from openpyxl.utils import get_column_letter

# 读取file1中的数据
file1_path = 'C:\\N-20W1PF3T3YXB-Data\\h4zhang\\Downloads\\export_my_reserved_hao.6.zhang - copy.xlsx'  # 修改为你的file1文件路径
# file1_path = 'C:\\N-20W1PF3T3YXB-Data\\h4zhang\\Downloads\\export_my_owned_hao.6.zhang - copy.xlsx'  # 修改为你的file1文件路径

sheet1_df = pd.read_excel(file1_path, sheet_name='Export')

# 读取file2中的所有sheets
file2_path = 'C:\\Users\\h4zhang\\Nokia\\5GSC SW Eng CN ET - Documents\\5GSC SW ENG CN2 ET Management\\CN2 lab management\\TestLine detail info.xlsx'
xls = pd.ExcelFile(file2_path)
# 获取所有工作表的名称
sheet_names = xls.sheet_names

# 打印所有工作表的名称
print("Sheet names in file2.xlsx:")
for name in sheet_names:
    print(name)

# 定义你想要搜索的工作表名称列表
sheets_to_search = ['SHIELD', 'CRT', 'jazz mobility', 'L2L3 int', 'Blues', 'ROCK operability', 'VRF3_6', 'AiC', 'key HW', 'HW_PLANNING', 'CD testline', 'prism UE']

# 读取指定的sheets
dfs = {sheet_name: xls.parse(sheet_name) for sheet_name in sheets_to_search if sheet_name in xls.sheet_names}

results = []

# 遍历file1中'sn'列的每个值
for value in sheet1_df['sn']:
    found = False  # 用来标记是否找到值
    for sheet_name, df in dfs.items():
        # 使用np.where来查找值在DataFrame中的位置
        result = np.where(df.values == value)

        # 如果找到，result将是一个包含行索引和列索引的元组
        if len(result[0]) > 0:  # 检查是否找到了至少一个匹配
            first_match_row = result[0][0] + 1  # +1 使行号从1开始，符合Excel的行号
            first_match_col = result[1][0] + 1  # +1 使列号从1开始，符合Excel的列号
            # 记录找到的信息
            cell_ref = get_column_letter(first_match_col) + str(first_match_row)  # 转换列索引为字母
            results.append(f"Yes, Sheet: {sheet_name}, Cell: {cell_ref}")
            found = True
            break  # 如果找到了匹配，就不需要继续搜索其他sheets

    if not found:
        results.append("No")

# 将结果添加到sheet1_df的新列中
sheet1_df['check'] = results

# 保存处理后的数据到新的Excel文件
output_file_path = 'modified_my_reserved.xlsx'
sheet1_df.to_excel(output_file_path, sheet_name='Export', index=False)
