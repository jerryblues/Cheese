import tushare as ts
from datetime import datetime, timedelta

# 初始化 tushare
ts.set_token('d9539dfdc1e347c3895a14a8c62e2d7aef74a765372dba921bbb27bb')  # 需要替换为你自己的 token
pro = ts.pro_api()

# 输入你想查询的股票代码，例如 '600519' 表示贵州茅台
stock_code = '600519.SH'

# 获取最近的交易日
trade_cal = pro.trade_cal(start_date='20240101', end_date=datetime.now().strftime('%Y%m%d'))
if trade_cal.empty:
    print("无法获取交易日历数据。")
else:
    # 获取最近的交易日期
    recent_trade_date = trade_cal[trade_cal['is_open'] == 1].iloc[-1]['cal_date']

    # 获取前一天的股价
    stock_data = pro.daily(ts_code=stock_code, trade_date=recent_trade_date)

    if stock_data.empty:
        print(f"无法获取股票 {stock_code} 在 {recent_trade_date} 的股价数据。请检查股票代码和日期是否正确。")
    else:
        current_price = stock_data['close'].values[0]
        print(f"前一天 ({recent_trade_date}) 的股价: {current_price}")

        # 获取最近的财务数据
        financial_data = pro.fina_indicator(ts_code=stock_code, limit=1)  # 获取最新一条财务数据

        if financial_data.empty:
            print(f"无法获取股票 {stock_code} 的财务数据。")
        else:
            # 打印财务数据的列名，检查可用的列
            print("财务数据的列名:", financial_data.columns.tolist())

            # 获取财务指标
            gross_margin = financial_data['grossprofit_margin'].values[0] / 100  # 毛利率
            net_profit_margin = financial_data['netprofit_margin'].values[0] / 100  # 净利润率

            # 检查 'profit_growth' 是否存在
            if 'profit_growth' in financial_data.columns:
                profit_growth = financial_data['profit_growth'].values[0]  # 利润同比增长
            else:
                profit_growth = None
                print("财务数据中没有 'profit_growth' 列。")

            # 获取市盈率
            stock_basic = pro.stock_basic(ts_code=stock_code)
            if stock_basic.empty:
                print(f"无法获取股票 {stock_code} 的基本信息。")
            else:
                pe_ratio = stock_basic['pe'].values[0]

                # 输出结果
                print(f"当前市盈率: {pe_ratio}")
                print(f"毛利率: {gross_margin * 100:.2f}%")
                print(f"净利润率: {net_profit_margin * 100:.2f}%")

                if profit_growth is not None:
                    print(f"利润同比增长: {profit_growth * 100:.2f}%")
                else:
                    print("无法提供利润同比增长数据。")
