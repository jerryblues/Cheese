import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta

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

    # Get current and yesterday price and avg
    current_sh50_price = round(sh50_data['Close'].iloc[-1].item(), 3)
    last_sh50_avg = round(sh50_avg.iloc[-1].item(), 3)
    yesterday_sh50_price = round(sh50_data['Close'].iloc[-2].item(), 3)
    yesterday_sh50_avg = round(sh50_avg.iloc[-2].item(), 3)

    current_zz1000_price = round(zz1000_data['Close'].iloc[-1].item(), 3)
    last_zz1000_avg = round(zz1000_avg.iloc[-1].item(), 3)
    yesterday_zz1000_price = round(zz1000_data['Close'].iloc[-2].item(), 3)
    yesterday_zz1000_avg = round(zz1000_avg.iloc[-2].item(), 3)

    # Get dates
    current_date_sh50 = sh50_data.index[-1].strftime('%Y-%m-%d')
    yesterday_date_sh50 = sh50_data.index[-2].strftime('%Y-%m-%d')
    current_date_zz1000 = zz1000_data.index[-1].strftime('%Y-%m-%d')
    yesterday_date_zz1000 = zz1000_data.index[-2].strftime('%Y-%m-%d')

    # Print current and yesterday prices and averages
    print(f"A.50 [{current_date_sh50}] Current Price:" + str(current_sh50_price))
    print(f"A.50 [{current_date_sh50}] Current Avg:" + str(last_sh50_avg))
    print(f"A.50 [{yesterday_date_sh50}] Yesterday Price:" + str(yesterday_sh50_price))
    print(f"A.50 [{yesterday_date_sh50}] Yesterday Avg:" + str(yesterday_sh50_avg))

    print(f"A.1000 [{current_date_zz1000}] Current Price:" + str(current_zz1000_price))
    print(f"A.1000 [{current_date_zz1000}] Current Avg:" + str(last_zz1000_avg))
    print(f"A.1000 [{yesterday_date_zz1000}] Yesterday Price:" + str(yesterday_zz1000_price))
    print(f"A.1000 [{yesterday_date_zz1000}] Yesterday Avg:" + str(yesterday_zz1000_avg))

    # Plot only the last 20 days of data
    plt.figure(figsize=(14, 7))

    # Filter for the last 20 days
    plt.plot(sh50_data.index[-20:], sh50_data['Close'][-20:], label='A.50 ETF Close Price', color='blue')
    plt.plot(sh50_data.index[-20:], sh50_avg[-20:], label='A.50 ETF 20-Day Average', color='skyblue')

    plt.plot(zz1000_data.index[-20:], zz1000_data['Close'][-20:], label='A.1000 ETF Close Price', color='red')
    plt.plot(zz1000_data.index[-20:], zz1000_avg[-20:], label='A.1000 ETF 20-Day Average', color='lightcoral')

    # Add title and labels
    plt.title('A.50 ETF and A.1000 ETF Price Trends for the Last 20 Days')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid()

    # Annotate each data point with its value
    for i in range(20):
        plt.text(sh50_data.index[-20:][i], sh50_data['Close'].iloc[-20 + i],
                 f"{sh50_data['Close'].iloc[-20 + i].item():.2f}", fontsize=8, color='blue', ha='center', va='bottom')

    for i in range(20):
        plt.text(zz1000_data.index[-20:][i], zz1000_data['Close'].iloc[-20 + i],
                 f"{zz1000_data['Close'].iloc[-20 + i].item():.2f}", fontsize=8, color='red', ha='center', va='bottom')

    # Show the plot
    plt.tight_layout()
    plt.show()
