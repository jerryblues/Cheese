# coding=utf-8
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import pandas as pd
import requests
import json
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
import json
import requests
from datetime import datetime
import pytz
import re


def get_token():
    # 定义请求的URL
    url = 'https://rep-portal.wroclaw.nsn-rdnet.net/jwt/obtain/'
    # 定义POST请求的数据（字典形式）
    data = {
        "username": "h4zhang",
        "password": "Holmes=-0"
    }
    # 发送POST请求
    response = requests.post(url, json=data)
    # 打印响应结果
    # print(response.text)
    # 找到第一个双引号的索引位置
    first_quote_index = response.text.find('"')
    # 找到第二个双引号的索引位置，从第一个双引号索引位置开始搜索
    second_quote_index = response.text.find('"', first_quote_index + 1)
    # 再次使用 find() 方法找到第三个双引号的索引位置，从第二个双引号索引位置开始搜索
    third_quote_index = response.text.find('"', second_quote_index + 1)
    # 再次使用 find() 方法找到第四个双引号的索引位置，从第三个双引号索引位置开始搜索
    fourth_quote_index = response.text.find('"', third_quote_index + 1)
    # 利用切片获取第三个和第四个双引号之间的内容
    t = response.text[third_quote_index + 1:fourth_quote_index]
    # 输出 'token'
    print("=== token ===\n", t)
    return t


def validate_token(t):
    # 定义请求的URL
    url = 'https://rep-portal.wroclaw.nsn-rdnet.net/jwt/verify/ '
    # 定义POST请求的数据（字典形式）
    data = {
        "pk": 1606902367,
        "token": t}
    # 发送POST请求
    res = requests.post(url, json=data)
    # If the token is invalid, the server will respond with status 400 and JSON object that contains further details of the error.
    # print(type(res))
    # print(res.status_code)
    if res.status_code == 201:
        print("=== token is valid ===")
        return True
    else:
        print("=== response ===\n", res)
        return False


def query_rep(url, t):
    # headers format is "JWT token" in type of string
    headers = {"Authorization": "JWT " + t}
    # url 获取方式：edge打开rep，输入feature ID，打开F12，刷新页面，在网络页签中，获取请求url(最长的那个)，然后去掉feature ID
    logging.debug(f"<--{url}-->")
    response = requests.get(url, headers=headers)
    logging.debug(f"<--response status: {response.status_code}-->")
    # print("status:", response.status_code)
    # print("headers:", response.headers)
    logging.debug(f"<--response text: {response.text}-->")
    # print("text:", response.text)
    return json.loads(response.text)


def get_result_retest(url, t):
    i = 0
    case_name = []
    qc_status = []
    test_entity = []
    case_owner = []
    last_qc_run = []
    ready_for_retest = []

    # query source data from rep
    query_rep_result = query_rep(url, t)
    if len(query_rep_result['results']):
        logging.debug("<--get result from rep done-->")
        '''
        data format
        print(data)
        print(data['results'][0]['backlog_id'])  # list
        print(data['results'][0]['backlog_id'][0])  # dic
        print(data['results'][0]['backlog_id'][0]['id'])  # value
        print(type(data), type(data['results']), type(data['results'][1]))
        print(len(data['results']))
        '''
    while i < len(query_rep_result['results']):
        case_name.append(query_rep_result['results'][i]['name'])
        qc_status.append(query_rep_result['results'][i]['status'])
        test_entity.append(query_rep_result['results'][i]['test_entity'])
        # case_owner.append(query_rep_result['results'][i]['res_tester'])
        case_owner.append(re.sub(r'\(\w+\)', '', query_rep_result['results'][i]['res_tester']))  # 去掉()及()内字符
        last_qc_run.append(query_rep_result['results'][i]['last_testrun']['timestamp'][:10])
        ready_for_retest.append(query_rep_result['results'][i]['ready_for_retest'])
        i += 1
    return case_name, qc_status, test_entity, case_owner, last_qc_run, ready_for_retest


def get_result_not_analyzed(url, t):
    i = 0
    case_name = []
    qc_status = []
    test_entity = []
    case_owner = []
    last_qc_run = []

    # query source data from rep
    query_rep_result = query_rep(url, t)
    # print(query_rep_result)
    if len(query_rep_result['results']):
        logging.debug("<--get result from rep done-->")
    while i < len(query_rep_result['results']):
        case_name.append(query_rep_result['results'][i]['test_case']['name'])
        qc_status.append(query_rep_result['results'][i]['result'])
        test_entity.append(query_rep_result['results'][i]['qc_test_instance']['test_entity'])
        # case_owner.append(query_rep_result['results'][i]['qc_test_instance']['res_tester'])
        case_owner.append(re.sub(r'\(\w+\)', '', query_rep_result['results'][i]['qc_test_instance']['res_tester']))    # 去掉()及()内字符
        last_qc_run.append(query_rep_result['results'][i]['end'][:10])
        i += 1
    return case_name, qc_status, test_entity, case_owner, last_qc_run


class MailSender:
    def __init__(self):
        self.relay_host = '10.130.128.21'
        self.relay_port = 25
        self.sender = 'hao.6.zhang@nokia-sbell.com'

    def send_mail(self, receiver, subject, content, attachFileList=None, is_html=False):
        message_to = "; ".join(receiver)
        sender = self.sender
        message = MIMEMultipart()
        message['From'] = self.sender
        message['To'] = message_to
        message['Subject'] = subject

        # 如果内容是HTML，则以HTML格式添加
        if is_html:
            part = MIMEText(content, 'html')
        else:
            part = MIMEText(content, 'plain')
        message.attach(part)

        if attachFileList:
            for file in attachFileList:
                with open(file, 'rb') as f:
                    attachment = MIMEImage(f.read())
                    attachment.add_header('Content-Disposition', 'attachment', filename=file)
                    message.attach(attachment)

        smtp = smtplib.SMTP(self.relay_host, self.relay_port)
        smtp.sendmail(sender, receiver, message.as_string())
        smtp.quit()
        print(f"=== Send Email to {receiver} successfully ===")


# 自定义函数，为单元格设置条件格式
def highlight(val):
    # 根据val的值设置不同的颜色
    if val == "CIT":
        color = 'yellow'
    elif val == "Failed":
        color = 'red'
    elif val == "Passed":
        color = 'green'
    else:  # 默认情况，不设置特殊颜色
        color = 'none'
    return f'background-color: {color}'


# CSS样式
css_style = """
<style type="text/css">
table {
    font-family: '微软雅黑', sans-serif; /* 设置字体为微软雅黑 */
    color: #333; /* 字体颜色 */
    border-collapse: collapse; /* 边框合并 */
    width: 100%;
}
td, th {
    border: 1px solid #CCC; /* 单元格边框 */
    height: 24px; /* 单元格高度 */
    transition: all 0.3s;  /* 过渡动画 */
    font-size: 14px; /* 设置表头字体大小为 14px */
}
th {
    background: #025cb4; /* 表头背景色设置为深蓝色 */
    color: #FFF; /* 表头文字颜色设置为白色 */
    font-weight: bold; /* 表头字体加粗 */
    text-align: left; /* 表头文字左对齐 */
}
tr:nth-child(even) td {
    background: #5fbdfd !important; /* 偶数行单元格背景色设置为淡蓝色 */
}
tr:nth-child(odd) td {
    background: #c0bebe !important; /* 奇数行单元格背景色设置为浅灰色 */
}
td {
    text-align: left; /* 文字居中 */
    font-size: 12px; /* 设置表格内容字体大小为 12px */
}
a {
    font-family: 微软雅黑, sans-serif; /* 设置链接字体为微软雅黑 */
}
</style>
"""

logging.basicConfig(level=logging.INFO,
                    filename='crt_cit_report.log',
                    filemode='a',
                    format='%(asctime)s - %(levelname)s: %(message)s'
                    )

crt_cit_retest = "https://rep-portal.ext.net.nokia.com/reports/qc/?columns=%3Ahash%3A61bc3fcc83f04ab0b3589c26b9744c7b&limit=200&ordering=name&organization=RAN_L3_SW_CN_1_TA&path=k%5CRAN_L3_SW_CN_1&ready_for_retest=true&status=-N%2FA"
crt_cit_retest_f12 = "https://rep-portal.ext.net.nokia.com/api/qc-beta/instances/report/?fields=id%2Cm_path%2Ctest_set__name%2Cbacklog_id%2Cname%2Curl%2Cstatus%2Cstatus_color%2Cfault_report_id_link%2Ccomment%2Csw_build%2Cplanned_test_set_ends%2Cdet_auto_lvl%2Ctest_entity%2Cres_tester%2Crequirement%2Cpi_id%2Ctest_subarea%2Ctest_lvl_area%2Cfunction_area%2Cca%2Corganization%2Crelease%2Cready_for_retest%2Cfeature%2Clast_testrun__timestamp%2Cautomation_options&limit=200&m_path__pos_neg=k%5CRAN_L3_SW_CN_1&ordering=name&organization__pos_neg=RAN_L3_SW_CN_1_TA&ready_for_retest=true&status__pos_neg=-N%2FA"
case_not_analyzed = "https://rep-portal.ext.net.nokia.com/reports/test-runs/?end_ft=2024-02-28%2000%3A00%3A00%2Cnow&limit=200&org=RAN_L3_SW_CN_1_TA&path=%3Ahash%3A403a03937f5a2c9f3463d990ab3498df&result=not%20analyzed"
case_not_analyzed_f12 = "https://rep-portal.ext.net.nokia.com/api/automatic-test/runs/report/?end__ft=2024-02-28%2000%3A00%3A00%2Cnow&fields=id%2Cqc_test_instance__m_path%2Cqc_test_set%2Ctest_case__name%2Curl%2Cresult%2Cresult_color%2Corigin_result%2Cbuilds%2Cqc_test_instance__test_entity%2Cqc_test_instance__res_tester%2Chyperlink_set%2Cend%2Cpronto%2Ccomment%2Ctest_col__testline_type%2Cqc_test_instance__organization&limit=200&qc_test_instance__m_path__pos_neg_empty_str=%3Ahash%3A403a03937f5a2c9f3463d990ab3498df&qc_test_instance__organization__pos_neg=RAN_L3_SW_CN_1_TA&result__name__pos_neg=not%20analyzed"

link_text = "Test Run Link"
url = "https://rep-portal.ext.net.nokia.com/reports/test-runs/?end_ft=2024-02-28%2000%3A00%3A00%2Cnow&limit=200&org=RAN_L3_SW_CN_1_TA&path=%3Ahash%3A403a03937f5a2c9f3463d990ab3498df&result=not%20analyzed"
additional_text = f"<span style='font-family: 微软雅黑;'>For Detailed Info:</span> <a href='{url}' class='link'>{link_text}</a>"
additional_html = f"<p>{additional_text}</p>"

# mail receiver
mail_receiver = ['hao.6.zhang@nokia-sbell.com']

# Webhook URL
webhook_url = 'https://nokia.webhook.office.com/webhookb2/8a514e5f-105f-44eb-8695-74950f6c2862@5d471751-9675-428d-917b-70f44f9630b0/IncomingWebhook/c0dcfecb0dce46e28a30a11d9fa998d3/24b4cd6e-4864-4fba-b2d1-92fea3819e65'


def df_to_text(df):
    text_list = []  # 初始化一个空列表来存储每行的文本
    for index, row in df.iterrows():
        # 将每行数据转换为纯文本格式
        text_row = ' | '.join(str(cell) for cell in row)
        text_list.append(text_row)  # 将文本行添加到列表中
    return "\n\n".join(text_list)  # 返回所有文本行，每行后都有换行符，需要两个换行符才能在 Teams 中显示出换行符


def send_to_teams(df1, df2):
    # 将DataFrame转换为字符串格式以在Teams中显示
    # 对于第一个DataFrame
    if df1.empty:
        message_text1 = "1.Not Analyzed Case List: None"
    else:
        # 将每行数据连接成字符串，并在每行末尾添加换行符
        df_string1 = df_to_text(df1)
        message_text1 = f"1.Not Analyzed Case List:\n\n{df_string1}"

    # 对于第二个DataFrame
    if df2.empty:
        message_text2 = "2.CRT/CIT Retest Case List(due to PR closed): None"
    else:
        # 将每行数据连接成字符串，并在每行末尾添加换行符
        df_string2 = df_to_text(df2)
        message_text2 = f"2.CRT/CIT Retest Case List:\n\n{df_string2}"

    # 创建消息内容，合并两个消息文本
    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": "Summary",
        "sections": [{
            "activityTitle": "Summary",
            "text": f"{message_text1}\n\n{message_text2}\n\n{additional_text}",  # 合并两个DataFrame的文本+超链接文本
            "markdown": True
        }]
    }

    # 发送POST请求到Webhook URL
    headers = {'Content-Type': 'application/json'}
    response = requests.post(webhook_url, data=json.dumps(message), headers=headers)

    # 检查请求是否成功
    if response.status_code == 200:
        print('=== Send message to Teams successfully ===')
    else:
        print('=== Send message to Teams failed, error code: ===', response.status_code)


def send_to_mail(df1, df2):
    # 将DataFrame转换为复杂格式以在Email中显示
    # 设置索引从1开始
    df1.index = range(1, len(df1) + 1)
    # 将索引转换为列，并设置列名为"No."
    df1.reset_index(inplace=True)
    df1.rename(columns={'index': 'No.'}, inplace=True)
    # 将"序号"列移动到DataFrame的第一列位置
    columns = ['No.'] + [col for col in df1.columns if col != 'No.']
    df_1 = df1[columns]

    df2.index = range(1, len(df2) + 1)
    # 将索引转换为列，并设置列名为"No."
    df2.reset_index(inplace=True)
    df2.rename(columns={'index': 'No.'}, inplace=True)
    # 将"序号"列移动到DataFrame的第一列位置
    columns = ['No.'] + [col for col in df2.columns if col != 'No.']
    df_2 = df2[columns]

    styled_html_1 = df_1.style.applymap(highlight).hide_index().render()    # 应用高亮格式并转换为HTML，且隐藏默认索引
    styled_html_2 = df_2.style.applymap(highlight).hide_index().render()
    # 应用css格式 + 自定义文本 + 高亮格式1&2
    html_content = (
            css_style +
            additional_html +
            "<h4 style='font-family:微软雅黑;'>Not Analyzed Case List</h4>" +
            styled_html_1 +
            "<h4 style='font-family:微软雅黑;'>CRT/CIT Retest Case List</h4>" +
            styled_html_2
    )

    # Create an instance of the MailSender class
    mail_sender = MailSender()

    # Define the email parameters
    receiver = mail_receiver  # Receiver list
    subject = 'Not Analyzed Case List & CRT/CIT Retest Case List'  # Email subject
    content = html_content  # Email content

    # Send the email with HTML content
    mail_sender.send_mail(receiver, subject, content, is_html=True)


def short_case_name(lst, length):
    shortened_list = [item[:length] for item in lst]
    return shortened_list


def data_summary():
    token = get_token()
    if not validate_token(token):  # 如果token失效，就重新获取
        token = get_token()
    # get case list: not_analyzed
    source_data_not_analyzed = get_result_not_analyzed(case_not_analyzed_f12, token)
    data_not_analyzed_for_mail = {
        'Case Name': short_case_name(source_data_not_analyzed[0], 100),
        'QC Status': source_data_not_analyzed[1],
        'Test Entity': source_data_not_analyzed[2],
        'Case Owner': source_data_not_analyzed[3],
        'Last QC Run': source_data_not_analyzed[4],
    }
    data_not_analyzed_for_teams = {
        'Case Name': short_case_name(source_data_not_analyzed[0], 17),
        'QC Status': source_data_not_analyzed[1],
        'Test Entity': source_data_not_analyzed[2],
        'Last QC Run': source_data_not_analyzed[4],
        'Case Owner': source_data_not_analyzed[3],
    }
    # get case list: need_retest
    source_data_retest = get_result_retest(crt_cit_retest_f12, token)
    data_retest_for_mail = {
        'Case Name': short_case_name(source_data_retest[0], 100),
        'QC Status': source_data_retest[1],
        'Test Entity': source_data_retest[2],
        'Case Owner': source_data_retest[3],
        'Last QC Run': source_data_retest[4],
        # 'Ready for Retest': source_data_retest[5]
    }
    data_retest_for_teams = {
        'Case Name': short_case_name(source_data_retest[0], 17),
        'QC Status': source_data_retest[1],
        'Test Entity': source_data_retest[2],
        'Last QC Run': source_data_retest[4],
        'Case Owner': source_data_retest[3],
        # 'Ready for Retest': source_data_retest[5]
    }

    df_not_analyzed_for_mail = pd.DataFrame(data_not_analyzed_for_mail)
    df_not_analyzed_for_teams = pd.DataFrame(data_not_analyzed_for_teams)
    df_retest_for_mail = pd.DataFrame(data_retest_for_mail)
    df_retest_for_teams = pd.DataFrame(data_retest_for_teams)
    return df_not_analyzed_for_mail, df_retest_for_mail, df_not_analyzed_for_teams, df_retest_for_teams


def trigger_send_to_mail():
    result = data_summary()
    send_to_mail(result[0], result[1])
    print("=== Current time:", datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S"), "===")


def trigger_send_to_teams():
    result = data_summary()
    send_to_teams(result[2], result[3])
    print("=== Current time:", datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S"), "===")


# test in local
trigger_send_to_mail()
trigger_send_to_teams()

# 定时收数据并发邮件
# scheduler = BlockingScheduler()
# scheduler.add_job(trigger_send_to_mail, 'cron', day_of_week='0-6', hour='8', minute='5', timezone="Asia/Shanghai")
# scheduler.add_job(trigger_send_to_teams, 'cron', day_of_week='0-6', hour='14', minute='5', timezone="Asia/Shanghai")
# scheduler.start()
