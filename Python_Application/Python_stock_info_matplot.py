import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta
import requests


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

    print("A.50 Current Price:" + str(current_sh50_price))
    print("A.50 Current Avg:" + str(last_sh50_avg))
    print("A.50 Yesterday Price:" + str(yesterday_sh50_price))
    print("A.50 Yesterday Avg:" + str(yesterday_sh50_avg))

    print("A.1000 Current Price:" + str(current_zz1000_price))
    print("A.1000 Current Avg:" + str(last_zz1000_avg))
    print("A.1000 Yesterday Price:" + str(yesterday_zz1000_price))
    print("A.1000 Yesterday Avg:" + str(yesterday_zz1000_avg))


    # if current_sh50_price > last_sh50_avg:
    #     message = f"Current [{current_sh50_price}] > Avg [{last_sh50_avg}]"
    #     if yesterday_sh50_price < yesterday_sh50_avg:
    #         message += f" | Yesterday [{yesterday_sh50_price}] < Avg [{yesterday_sh50_avg}] | Trend changed. Buy!"
    #     else:
    #         message += f" | Yesterday [{yesterday_sh50_price}] > Avg [{yesterday_sh50_avg}] | Trend unchanged"
    #     send_notification("A.50", message)
    # elif current_sh50_price < last_sh50_avg:
    #     message = f"Current [{current_sh50_price}] < Avg [{last_sh50_avg}]"
    #     if yesterday_sh50_price < yesterday_sh50_avg:
    #         message += f" | Yesterday [{yesterday_sh50_price}] < Avg [{yesterday_sh50_avg}] | Trend unchanged"
    #     else:
    #         message += f" | Yesterday [{yesterday_sh50_price}] > Avg [{yesterday_sh50_avg}] | Trend changed. Sell!"
    #     send_notification("A.50", message)
    #
    # if current_zz1000_price > last_zz1000_avg:
    #     message = f"Current [{current_zz1000_price}] > Avg [{last_zz1000_avg}]"
    #     if yesterday_zz1000_price < yesterday_zz1000_avg:
    #         message += f" | Yesterday [{yesterday_zz1000_price}] < Avg [{yesterday_zz1000_avg}] | Trend changed. Buy!"
    #     else:
    #         message += f" | Yesterday [{yesterday_zz1000_price}] > Avg [{yesterday_zz1000_avg}] | Trend unchanged"
    #     send_notification("A.1000", message)
    # elif current_zz1000_price < last_zz1000_avg:
    #     message = f"Current [{current_zz1000_price}] < Avg [{last_zz1000_avg}]"
    #     if yesterday_zz1000_price < yesterday_zz1000_avg:
    #         message += f" | Yesterday [{yesterday_zz1000_price}] < Avg [{yesterday_zz1000_avg}] | Trend unchanged"
    #     else:
    #         message += f" | Yesterday [{yesterday_zz1000_price}] > Avg [{yesterday_zz1000_avg}] | Trend changed. Sell!"
    #     send_notification("A.1000", message)


    # Plot only the last 20 days of data
    plt.figure(figsize=(14, 7))

    # Filter for the last 20 days
    plt.plot(sh50_data.index[-20:], sh50_data['Close'][-20:], label='A.50 ETF Close Price', color='blue')
    plt.plot(sh50_data.index[-20:], sh50_avg[-20:], label='A.50 ETF 20-Day Average', color='green')

    plt.plot(zz1000_data.index[-20:], zz1000_data['Close'][-20:], label='A.1000 ETF Close Price', color='red')
    plt.plot(zz1000_data.index[-20:], zz1000_avg[-20:], label='A.1000 ETF 20-Day Average', color='orange')

    # Add title and labels
    plt.title('A.50 ETF and A.1000 ETF Price Trends for the Last 20 Days')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid()

    # Show the plot
    plt.tight_layout()
    plt.show()
