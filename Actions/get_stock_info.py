import yfinance as yf
from datetime import datetime, timedelta
import requests
import pytz
from datetime import datetime


# 设置时区为中国时区
china_tz = pytz.timezone('Asia/Shanghai')

# 获取当前时间并转换为中国时区
current_time = datetime.now(china_tz)
print("Current Time[CN]:", current_time.strftime('%Y-%m-%d %H:%M:%S'))


# Notification function
def send_notification(etf_name, messages):
    webhook_url = 'https://open.feishu.cn/open-apis/bot/v2/hook/8b2f29c3-1ef2-4c61-8996-e9a98dc0e92e'  # 替换为你的 Webhook URL
    headers = {'Content-Type': 'application/json'}

    notification = f"{etf_name}: {messages}"

    # 构建消息体
    payload = {
        "msg_type": "text",
        "content": {
            "text": notification
        }
    }

    # 发送 POST 请求
    response = requests.post(webhook_url, headers=headers, json=payload)

    # 检查响应
    if response.status_code == 200:
        print("Notification sent successfully!")
    else:
        print(f"Failed to send notification: {response.status_code}, {response.text}")


# Set the end date to today and start date to 40 days ago
end_date = datetime.today()
start_date = end_date - timedelta(days=60)  # Get data for the last 40 days

# Download historical data for the ETFs
sh50_data = yf.download('510050.SS', start=start_date, end=end_date)
zz1000_data = yf.download('560010.SS', start=start_date, end=end_date)

# Print downloaded data for debugging
print("A.50 Data:")
print(sh50_data, "\n")
print("A.1000 Data:")
print(zz1000_data, "\n")

# Check if data was successfully retrieved
if sh50_data.empty or zz1000_data.empty:
    print("Failed to download data, please check ETF codes or network connection.")
else:
    # Calculate the average price over the last 20 days
    sh50_avg = sh50_data['Close'].rolling(window=20).mean()
    zz1000_avg = zz1000_data['Close'].rolling(window=20).mean()

    # Print the moving averages for debugging
    print("A.50 Last 20-Day Average:")
    print(sh50_avg, "\n")
    print("A.1000 Last 20-Day Average:")
    print(zz1000_avg, "\n")

    # get current and yesterday price and avg
    current_sh50_price = round(sh50_data['Close'].iloc[-1].item(), 3)
    last_sh50_avg = round(sh50_avg.iloc[-1].item(), 3)
    yesterday_sh50_price = round(sh50_data['Close'].iloc[-2].item(), 3)
    yesterday_sh50_avg = round(sh50_avg.iloc[-2].item(), 3)

    current_zz1000_price = round(zz1000_data['Close'].iloc[-1].item(), 3)
    last_zz1000_avg = round(zz1000_avg.iloc[-1].item(), 3)
    yesterday_zz1000_price = round(zz1000_data['Close'].iloc[-2].item(), 3)
    yesterday_zz1000_avg = round(zz1000_avg.iloc[-2].item(), 3)

    # 获取日期
    current_date = sh50_data.index[-1].strftime('%Y-%m-%d')
    yesterday_date = sh50_data.index[-2].strftime('%Y-%m-%d')

    print("A.50 Current Price:" + str(current_sh50_price))
    print("A.50 Current Avg:" + str(last_sh50_avg))
    print("A.50 Yesterday Price:" + str(yesterday_sh50_price))
    print("A.50 Yesterday Avg:" + str(yesterday_sh50_avg))

    print("A.1000 Current Price:" + str(current_zz1000_price))
    print("A.1000 Current Avg:" + str(last_zz1000_avg))
    print("A.1000 Yesterday Price:" + str(yesterday_zz1000_price))
    print("A.1000 Yesterday Avg:" + str(yesterday_zz1000_avg))

    # A.50 Notifications
    if current_sh50_price > last_sh50_avg:
        message = f"{current_date} [{current_sh50_price}] > Avg [{last_sh50_avg}]"
        if yesterday_sh50_price < yesterday_sh50_avg:
            message += f" | {yesterday_date} [{yesterday_sh50_price}] < Avg [{yesterday_sh50_avg}] | Trend changed. Buy!"
        else:
            message += f" | {yesterday_date} [{yesterday_sh50_price}] > Avg [{yesterday_sh50_avg}] | Trend unchanged"
        send_notification("A.50", message)
    elif current_sh50_price < last_sh50_avg:
        message = f"{current_date} [{current_sh50_price}] < Avg [{last_sh50_avg}]"
        if yesterday_sh50_price < yesterday_sh50_avg:
            message += f" | {yesterday_date} [{yesterday_sh50_price}] < Avg [{yesterday_sh50_avg}] | Trend unchanged"
        else:
            message += f" | {yesterday_date} [{yesterday_sh50_price}] > Avg [{yesterday_sh50_avg}] | Trend changed. Sell!"
        send_notification("A.50", message)

    # A.1000 Notifications
    if current_zz1000_price > last_zz1000_avg:
        message = f"{current_date} [{current_zz1000_price}] > Avg [{last_zz1000_avg}]"
        if yesterday_zz1000_price < yesterday_zz1000_avg:
            message += f" | {yesterday_date} [{yesterday_zz1000_price}] < Avg [{yesterday_zz1000_avg}] | Trend changed. Buy!"
        else:
            message += f" | {yesterday_date} [{yesterday_zz1000_price}] > Avg [{yesterday_zz1000_avg}] | Trend unchanged"
        send_notification("A.1000", message)
    elif current_zz1000_price < last_zz1000_avg:
        message = f"{current_date} [{current_zz1000_price}] < Avg [{last_zz1000_avg}]"
        if yesterday_zz1000_price < yesterday_zz1000_avg:
            message += f" | {yesterday_date} [{yesterday_zz1000_price}] < Avg [{yesterday_zz1000_avg}] | Trend unchanged"
        else:
            message += f" | {yesterday_date} [{yesterday_zz1000_price}] > Avg [{yesterday_zz1000_avg}] | Trend changed. Sell!"
        send_notification("A.1000", message)
