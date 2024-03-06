import pandas as pd
import json
import requests
import holidays
from datetime import datetime, timedelta


def find_first_wednesday(year):
    # January 1st of the given year
    date = datetime(year, 1, 1)
    # Find the first Wednesday of the year
    while date.weekday() != 2:  # In Python's datetime, Monday is 0 and Sunday is 6. So, Wednesday is 2.
        date += timedelta(days=1)
    return date


def get_today_detail(date):
    year = date.year
    first_wednesday = find_first_wednesday(year)
    if date < first_wednesday:
        year -= 1
        first_wednesday = find_first_wednesday(year)
    # Calculate the difference in days
    delta_days = (date - first_wednesday).days
    # Calculate the FB number
    fb = f"{year % 100}{delta_days // 14 + 1:02d}"
    # Calculate the week number within the FB
    week_num = delta_days % 14 // 7 + 1
    week_in_fb = "1st week" if week_num == 1 else "2nd week"
    # Calculate the weekday (Python's weekday function returns 0 for Monday and 6 for Sunday)
    week_day = date.strftime('%A')
    # Calculate the last day of the FB
    last_day_of_fb = (first_wednesday + timedelta(days=14 * (delta_days // 14 + 1) - 1)).strftime('%Y-%m-%d')
    return fb, week_in_fb, week_day, last_day_of_fb


def get_country_holidays(country_code):
    # 创建对应国家的节假日对象
    if country_code == 'FR':
        return holidays.FRA(), 'France'
    elif country_code == 'DE':
        return holidays.DE(), 'Germany'
    elif country_code == 'PL':
        return holidays.PL(), 'Poland'
    elif country_code == 'IN':
        return holidays.IN(), 'India'
    elif country_code == 'FI':
        return holidays.FI(), 'Finland'
    elif country_code == 'CN':
        return holidays.CN(), 'China'
    else:
        return None, None  # 如果国家代码无效，则返回 None


def is_today_holiday(day):
    # 获取所有国家的节假日信息
    all_countries = ['CN', 'IN', 'DE', 'PL', 'FR', 'FI']
    holiday_info = []  # 创建一个空列表来收集节假日信息
    for country_code in all_countries:
        # 获取指定国家的节假日信息
        country_holidays, country_name = get_country_holidays(country_code)

        if country_holidays is not None:
            # 检查今天是否是指定国家的节假日
            if day in country_holidays:
                # 将节假日信息添加到列表中
                holiday_info.append(f"{country_name}: {country_holidays.get(day)}")
    return holiday_info


def df_to_text(df):
    text_list = []  # 初始化一个空列表来存储每行的文本
    for index, row in df.iterrows():
        # 将每行数据转换为纯文本格式
        text_row = ' | '.join(str(cell) for cell in row)
        text_list.append(text_row)  # 将文本行添加到列表中
    return "\n\n".join(text_list)  # 返回所有文本行，每行后都有换行符，需要两个\n才能在 teams 中显示出换行


def send_to_teams(df1, df2, msg1, msg2):
    # send hello message
    msg0 = "Hi there! Good day!"
    msg3 = "Here is daily news for you:"
    message_text0 = f"{msg0}\n\n{msg1}\n\n{msg2}\n\n{msg3}\n\n"

    # 对于第一个DataFrame
    if df1.empty:
        message_text1 = "No case need to retest from DF1"
    else:
        df_string1 = df1.to_string(index=False)  # 将DataFrame转换为字符串
        message_text1 = f"DF1:\n```\n{df_string1}\n```"  # 使用Markdown代码块格式化文本

    # 对于第二个DataFrame
    if df2.empty:
        message_text2 = "No case need to retest from DF2"
    else:
        df_string2 = df_to_text(df2)  # 将DataFrame转换为带两个换行符的纯文本
        message_text2 = f"DF2:\n\n{df_string2}"  # 使用普通模式格式化文本

    # 包含超链接的文本
    hyperlink_text = f"For Detailed Info: <a href='{url}'>{link_text}</a>"

    # 创建消息内容，合并两个消息文本
    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": "Summary",
        "sections": [{
            "activityTitle": "Test",
            "text": f"{message_text0}\n\n{message_text1}\n\n{message_text2}\n\n{hyperlink_text}",  # 合并两个DataFrame的文本和超链接文本
            "markdown": True
        }]
    }

    print(f"message body: {message}\n")

    # Webhook URL
    webhook_url = 'https://nokia.webhook.office.com/webhookb2/8a514e5f-105f-44eb-8695-74950f6c2862@5d471751-9675-428d-917b-70f44f9630b0/IncomingWebhook/57929b2325b04cc195e8cb121016422a/24b4cd6e-4864-4fba-b2d1-92fea3819e65'

    # 发送POST请求到Webhook URL
    headers = {'Content-Type': 'application/json'}
    response = requests.post(webhook_url, data=json.dumps(message), headers=headers)

    # 检查请求是否成功
    if response.status_code == 200:
        print('=== Teams message sent successfully ===')
    else:
        print('=== Teams message sent failed, error code: ===', response.status_code)


def today_detail_info():
    # today = datetime.today()
    today = datetime(2024, 5, 1)  # Test the function
    # 获取当前所属的 FB 和处于 FB 的第几周以及今天是星期几
    current_fb, week_number, weekday, last_day_of_this_fb = get_today_detail(today)
    msg1 = f"Today is {today.strftime('%Y-%m-%d')}, {weekday}, {week_number} of FB{current_fb}, this FB end at {last_day_of_this_fb}.\n"
    # print(msg1)
    # 获取节假日信息
    holiday = is_today_holiday(today)
    if holiday:
        msg2 = f"Today is holiday in " + ', '.join(holiday)
        # print(msg2)
    else:
        msg2 = f"No holiday today."
        # print(msg2)
    return msg1, msg2


# test get_today_detail function
# current_fb, week_in_this_fb, weekday, last_day_of_this_fb = get_today_detail(today)
# print("Current FB:", current_fb)
# print("Week of this FB:", week_in_this_fb)
# print("Weekday:", weekday)
# print("Last day of this FB:", last_day_of_this_fb)
# msg_day_info, msg_holiday_info = today_detail_info()
# print(msg_holiday_info)

# main()
link_text = "Test Run Link"
url = "https://rep-portal.ext.net.nokia.com/reports/test-runs/?end_ft=2024-01-01%2000%3A00%3A00%2Cnow&limit=200&path=%3Ahash%3A403a03937f5a2c9f3463d990ab3498df"

df_example_1 = pd.DataFrame({'Name': ['Alice', 'Bob'], 'Status': ['OK', 'Fail']})
df_example_2 = pd.DataFrame({'Test': ['Math', 'Science'], 'Score': [95, 88]})

msg_day_info, msg_holiday_info = today_detail_info()
send_to_teams(df_example_1, df_example_2, msg_day_info, msg_holiday_info)
