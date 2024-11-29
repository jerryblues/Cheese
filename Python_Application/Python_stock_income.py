import yfinance as yf
import pandas as pd

# 获取数据
sh50_data = yf.download("510050.SS", start="2019-01-01", end="2024-01-01")
zz1000_data = yf.download("560010.SS", start="2019-01-01", end="2024-01-01")

# 计算20日均线
sh50_data['20_MA'] = sh50_data['Close'].rolling(window=20).mean()
zz1000_data['20_MA'] = zz1000_data['Close'].rolling(window=20).mean()

# 合并数据
merged_data = pd.merge(
    sh50_data[['Close', '20_MA']],
    zz1000_data[['Close', '20_MA']],
    left_index=True,
    right_index=True,
    suffixes=('_SH50', '_ZZ1000')
)

# 初始化参数
initial_capital = 20000
sh50_position = 0
zz1000_position = 0
capital = initial_capital

# 遍历合并后的数据
for date, row in merged_data.iterrows():
    current_sh50_price = row['Close_SH50']
    current_sh50_ma = row['20_MA_SH50']

    current_zz1000_price = row['Close_ZZ1000']
    current_zz1000_ma = row['20_MA_ZZ1000']

    # 上证50策略
    if current_sh50_price > current_sh50_ma and capital > 0:
        # 买入半仓
        sh50_position = (capital / 2) / current_sh50_price
        capital -= (capital / 2)  # 更新资本
    elif current_sh50_price < current_sh50_ma and sh50_position > 0:
        # 卖出
        capital += sh50_position * current_sh50_price
        sh50_position = 0  # 清空持仓

    # 中证1000策略
    if current_zz1000_price > current_zz1000_ma and capital > 0:
        # 买入半仓
        zz1000_position = (capital / 2) / current_zz1000_price
        capital -= (capital / 2)  # 更新资本
    elif current_zz1000_price < current_zz1000_ma and zz1000_position > 0:
        # 卖出
        capital += zz1000_position * current_zz1000_price
        zz1000_position = 0  # 清空持仓

# 计算最终资本
final_capital = capital + (sh50_position * current_sh50_price) + (zz1000_position * current_zz1000_price)

# 输出结果
print(f"初始资本: {initial_capital}")
print(f"最终资本: {final_capital}")
print(f"收益率: {(final_capital - initial_capital) / initial_capital * 100:.2f}%")
