import yfinance as yf
from datetime import datetime, timedelta
import requests
import pytz
from datetime import datetime


# 设置时区为中国时区
china_tz = pytz.timezone('Asia/Shanghai')

# 获取当前时间并转换为中国时区
current_time = datetime.now(china_tz)


# Notification function
def send_notification(etf_name, messages):
    webhook_url = 'https://open.feishu.cn/open-apis/bot/v2/hook/9d3a127c-6f0a-45b8-88bb-23a4f7a23e7e'  # 替换为你的 Webhook URL
    headers = {'Content-Type': 'application/json'}

    # check messages contain "buy" or "sell"
    if "buy" in messages.lower() or "sell" in messages.lower():
        notification = (f"{etf_name}:\n"
                        f"{messages}")

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
    else:
        print("No 'buy' or 'sell' detected in messages. Notification not sent.")


# Set the end date to today and start date to 60 days ago
end_date = datetime.today()
start_date = end_date - timedelta(days=60)  # Get data for the last 60 days

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
    current_date_sh50 = sh50_data.index[-1].strftime('%Y-%m-%d')
    yesterday_date_sh50 = sh50_data.index[-2].strftime('%Y-%m-%d')
    current_date_zz1000 = zz1000_data.index[-1].strftime('%Y-%m-%d')
    yesterday_date_zz1000 = zz1000_data.index[-2].strftime('%Y-%m-%d')

    print(f"A.50 [{current_date_sh50}] Current Price:" + str(current_sh50_price))
    print(f"A.50 [{current_date_sh50}] Current Avg:" + str(last_sh50_avg))
    print(f"A.50 [{yesterday_date_sh50}] Yesterday Price:" + str(yesterday_sh50_price))
    print(f"A.50 [{yesterday_date_sh50}] Yesterday Avg:" + str(yesterday_sh50_avg))

    print(f"A.1000 [{current_date_zz1000}] Current Price:" + str(current_zz1000_price))
    print(f"A.1000 [{current_date_zz1000}] Current Avg:" + str(last_zz1000_avg))
    print(f"A.1000 [{yesterday_date_zz1000}] Yesterday Price:" + str(yesterday_zz1000_price))
    print(f"A.1000 [{yesterday_date_zz1000}] Yesterday Avg:" + str(yesterday_zz1000_avg))

    # A.50 Notifications
    if current_sh50_price > last_sh50_avg:
        message = f"{current_date_sh50} | Current [{current_sh50_price}] > Avg [{last_sh50_avg}]\n"
        if yesterday_sh50_price < yesterday_sh50_avg:
            message += (f"{yesterday_date_sh50} | Current [{yesterday_sh50_price}] < Avg [{yesterday_sh50_avg}]\n"
                        f"Trend changed. Buy!")
        else:
            message += (f"{yesterday_date_sh50} | Current [{yesterday_sh50_price}] > Avg [{yesterday_sh50_avg}]\n"
                        f"Trend unchanged")
        print(message)
        send_notification("A.50", message)

    elif current_sh50_price < last_sh50_avg:
        message = f"{current_date_sh50} | Current [{current_sh50_price}] < Avg [{last_sh50_avg}]\n"
        if yesterday_sh50_price < yesterday_sh50_avg:
            message += (f"{yesterday_date_sh50} | Current [{yesterday_sh50_price}] < Avg [{yesterday_sh50_avg}]\n"
                        f"Trend unchanged")
        else:
            message += (f"{yesterday_date_sh50} | Current [{yesterday_sh50_price}] > Avg [{yesterday_sh50_avg}]\n"
                        f"Trend changed. Sell!")
        print(message)
        send_notification("A.50", message)

    # A.1000 Notifications
    if current_zz1000_price > last_zz1000_avg:
        message = f"{current_date_zz1000} | Current [{current_zz1000_price}] > Avg [{last_zz1000_avg}]\n"
        if yesterday_zz1000_price < yesterday_zz1000_avg:
            message += (f"{yesterday_date_zz1000} | Current [{yesterday_zz1000_price}] < Avg [{yesterday_zz1000_avg}]\n"
                        f"Trend changed. Buy!")
        else:
            message += (f"{yesterday_date_zz1000} | Current [{yesterday_zz1000_price}] > Avg [{yesterday_zz1000_avg}]\n"
                        f"Trend unchanged")
        print(message)
        send_notification("A.1000", message)

    elif current_zz1000_price < last_zz1000_avg:
        message = f"{current_date_zz1000} | Current [{current_zz1000_price}] < Avg [{last_zz1000_avg}]\n"
        if yesterday_zz1000_price < yesterday_zz1000_avg:
            message += (f"{yesterday_date_zz1000} | Current [{yesterday_zz1000_price}] < Avg [{yesterday_zz1000_avg}]\n"
                        f"Trend unchanged")
        else:
            message += (f"{yesterday_date_zz1000} | Current [{yesterday_zz1000_price}] > Avg [{yesterday_zz1000_avg}]\n"
                        f"Trend changed. Sell!")
        print(message)
        send_notification("A.1000", message)

    print("Current Time[CN]:", current_time.strftime('%Y-%m-%d %H:%M:%S'))
