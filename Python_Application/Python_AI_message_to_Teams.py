import pandas as pd
import json
import requests


def df_to_text(df):
    text_list = []  # 初始化一个空列表来存储每行的文本
    for index, row in df.iterrows():
        # 将每行数据转换为纯文本格式
        text_row = ' | '.join(str(cell) for cell in row)
        text_list.append(text_row)  # 将文本行添加到列表中
    return "\n\n".join(text_list)  # 返回所有文本行，每行后都有换行符，需要两个\n才能在 teams 中显示出换行


def send_to_teams(df1, df2):
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
        "summary": "Some Summary",
        "sections": [{
            "activityTitle": "Test",
            "text": f"{message_text1}\n\n{message_text2}\n\n{hyperlink_text}",  # 合并两个DataFrame的文本和超链接文本
            "markdown": True
        }]
    }

    print(message)

    # Webhook URL
    webhook_url = 'https://nokia.webhook.office.com/webhookb2/8a514e5f-105f-44eb-8695-74950f6c2862@5d471751-9675-428d-917b-70f44f9630b0/IncomingWebhook/c0dcfecb0dce46e28a30a11d9fa998d3/24b4cd6e-4864-4fba-b2d1-92fea3819e65'

    # 发送POST请求到Webhook URL
    headers = {'Content-Type': 'application/json'}
    response = requests.post(webhook_url, data=json.dumps(message), headers=headers)

    # 检查请求是否成功
    if response.status_code == 200:
        print('=== Teams message sent successfully ===')
    else:
        print('=== Teams message sent failed, error code: ===', response.status_code)


# 示例用法
link_text = "Test Run Link"
url = "https://rep-portal.ext.net.nokia.com/reports/test-runs/?end_ft=2024-01-01%2000%3A00%3A00%2Cnow&limit=200&path=%3Ahash%3A403a03937f5a2c9f3463d990ab3498df"

df1 = pd.DataFrame({'Name': ['Alice', 'Bob'], 'Status': ['OK', 'Fail']})
df2 = pd.DataFrame({'Test': ['Math', 'Science'], 'Score': [95, 88]})
send_to_teams(df1, df2)
