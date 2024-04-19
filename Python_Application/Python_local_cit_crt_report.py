from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import pandas as pd
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
import json
import requests
from datetime import datetime, timedelta
import pytz
import re
import holidays

# mail receiver
mail_receiver = ['hao.6.zhang@nokia-sbell.com']
# mail_receiver = ['i_nsb_mn_ran_rd_vrf_haz3_06@internal.nsn.com', 'hao.6.zhang@nokia-sbell.com']

logging.basicConfig(level=logging.INFO,
                    filename='local_cit_crt_report.log',
                    filemode='a',
                    format='%(asctime)s - %(levelname)s: %(message)s'
                    )

headers_backup = {
    'Authorization': 'Token d8c42b66120fdbec8fdf6fe7c27c849e045970c1',
    'Cookie': 'sessionid=.eJxVjEEOwiAQRe_C2lRKW1vd1ejOhYkHmAzMRFAKicBG492tSTfd_vff-wh6YLhHyG7idwwsDmJMDrc3O88WndgIwJItlMQvsJjs_NBKm34va-o63SMpUqyYB922rZKKmqanWuKuWcsazZMDzX7JDMbHQmDiNMUAJTtfLbw6k8uoPV9O4_W4OKuQ-ze6QUrx_QGCn0Dr:1rsfDi:C-i6svehz4_oleQw_CvG24SIRUk; csrftoken=tXyBtgrohUnouAoMBJpDC7UtSrosMd9bItbqYbFDevcr8BipY6aFRUBVk8Peo6Sh',
    # Cookie 格式
}

headers = {
    'Authorization': 'Token d8c42b66120fdbec8fdf6fe7c27c849e045970c1'}

proxies = {
    "http": "http://10.144.1.10:8080",
    "https": "http://10.144.1.10:8080",
}

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
    if val == "Passed":
        color = '#1EC21E'
    elif val == "Failed":
        color = 'red'
    else:  # 默认情况，不设置特殊颜色
        color = 'none'
    return f'background-color: {color}'


def format_df(df):
    # 设置索引从1开始
    df.index = range(1, len(df) + 1)
    # 将索引转换为列，并设置列名为"No."
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'No.'}, inplace=True)
    # 将"序号"列移动到DataFrame的第一列位置
    columns = ['No.'] + [col for col in df.columns if col != 'No.']
    formatted_df = df[columns]
    return formatted_df


def get_single_run_id(session):
    # 获取昨天的日期
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_yyyy_mm_dd = yesterday.strftime('%Y-%m-%d')

    # 获取昨天16点之后的 single run，换算过来就是当天凌晨开始的 single run
    url_single_run_filter = "https://cloud.ute.nsn-rdnet.net/execution/search/ajax?format=json&test_path=testsuite%2FHangzhou%2FRRM%2FRAN_L3_SW_CN_HZ%2Ftrunk_sbts%2FCRT%2FCN1%2F&topology=&status=&queue=&user=&start_date__gte=&start_date__lte=&end_date__gte=&end_date__lte=&add_date__gte=" + yesterday_yyyy_mm_dd + "+16%3A00&add_date__lte=&execution_count=&test_repository_revision=&skiprun=&state=&additional_parameters=&ordering=-id&limit=50&offset=0&no_cache=9761"
    url_single_run_for_web = "https://cloud.ute.nsn-rdnet.net/execution/search/?test_path=testsuite%2FHangzhou%2FRRM%2FRAN_L3_SW_CN_HZ%2Ftrunk_sbts%2FCRT%2FCN1%2F&topology=&status=&queue=&user=&start_date__gte=&start_date__lte=&end_date__gte=&end_date__lte=&add_date__gte=" + yesterday_yyyy_mm_dd + "+16%3A00&add_date__lte=&execution_count=&test_repository_revision=&skiprun=&state=&additional_parameters="

    # 使用 session 获取 response
    response = session.get(url_single_run_filter, headers=headers, proxies=proxies)
    # 或者使用 request get 获取 response，但需要在 header 中配置 cookies
    # response = requests.get(url_single_run_filter, headers=headers)

    # print(response.text)  # 打印响应文本

    # 将JSON字符串解析为Python对象
    data = json.loads(response.text)
    # 遍历列表，提取每个字典中的id字段
    ids = [item['id'] for item in data['rows']]
    # times = len(ids)  # 调了几次 single run

    # print(ids)
    # print(f'Total Single Run: [{times}] Times')
    return ids, url_single_run_for_web


def get_single_run_result(session):
    case_result = []
    case_name = []
    log_links = []
    pass_case_num, fail_case_num, running_case_num, total_case_num = 0, 0, 0, 0
    ids, url_single_run_for_web = get_single_run_id(session)

    for single_run_id in ids:
        url_single_run = "https://cloud.ute.nsn-rdnet.net/execution/" + str(single_run_id) + "/show"
        # print(url_single_run)

        response = session.get(url_single_run, headers=headers, proxies=proxies)

        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(response.text, 'lxml')  # 或者使用 'html.parser' 作为解析器
        # 提取状态和描述
        status_elements = soup.select('td.status')

        # 遍历匹配到的元素
        for status in status_elements:
            # 打印状态
            # print("status:", status.text.strip())
            case_result.append(status.text.strip())
            # 打印描述（状态的下一个兄弟节点）
            # print("case:", status.find_next_sibling('td').text.strip())
            case_name.append(status.find_next_sibling('td').text.strip())

            # 提取链接和链接文本
            execution_log_link = soup.find('a', string='Execution logs')
            if execution_log_link:
                # print("link:", execution_log_link['href'])  # 打印链接
                # print("text:", execution_log_link.text)  # 打印链接文本
                log_links.append(execution_log_link['href'])
    # print("\n", case_result, case_name, log_links)
    # print(len(case_result), len(case_name), len(log_links))

    for result in case_result:
        if result == "Passed":
            pass_case_num += 1
        elif result == "Failed":
            fail_case_num += 1
        else:
            running_case_num += 1

    total_case_num = len(case_result)

    return case_result, case_name, log_links, url_single_run_for_web, pass_case_num, fail_case_num, running_case_num, total_case_num


def data_summary(session):
    case_result, case_name, log_links, url_single_run_for_web, pass_case_num, fail_case_num, running_case_num, total_case_num = get_single_run_result(session)
    result_summary = {
        'Case Name': case_name,
        'Test Result': case_result,
        'Log Link': log_links,
    }

    df_result_summary = pd.DataFrame(result_summary)
    return df_result_summary, url_single_run_for_web, pass_case_num, fail_case_num, running_case_num, total_case_num


def send_to_mail(session):
    df_result_summary, url_single_run_for_web, pass_case_num, fail_case_num, running_case_num, total_case_num = data_summary(session)
    text = "UTE Cloud"
    additional_text = f"<span style='font-family: 微软雅黑;'>Hi,<br>Please check the local CIT test result: " \
                      f"{total_case_num} cases triggered, {pass_case_num} cases passed, {fail_case_num} cases failed, {running_case_num} cases running.<br>" \
                      f"Check result in </span> <a href='{url_single_run_for_web}' class='link'>{text}</a>"
    additional_html = f"<p>{additional_text}</p>"

    # 将DataFrame转换格式以在Email中显示
    formatted_df1 = format_df(df_result_summary)

    # 应用高亮格式并转换为HTML，且隐藏默认索引 || due to pandas 2.2.1, hide index and to_html function changed ||
    styled_html_1 = formatted_df1.style.map(highlight).hide().to_html()

    # 应用css格式 + 自定义文本 + 高亮格式1&2
    html_content = (
            css_style + additional_html + styled_html_1
    )

    # Create an instance of the MailSender class
    mail_sender = MailSender()

    # Define the email parameters
    receiver = mail_receiver  # Receiver list
    subject = '[CIT] Local CIT Test Result'  # Email subject
    content = html_content  # Email content

    # Send the email with HTML content
    mail_sender.send_mail(receiver, subject, content, is_html=True)
    print("=== Current time:", datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S"), "===\n")


def trigger_send_to_mail():
    # 创建一个Session对象
    session = requests.Session()
    # 登录URL
    login_url = 'https://cloud.ute.nsn-rdnet.net/user/login?'
    # 获取登录页面，确保Cookies被设置
    session.get(login_url, proxies=proxies)
    # 从Cookies中获取CSRF令牌
    csrf_token = session.cookies.get('csrftoken')
    # 登录信息，包括用户名、密码和CSRF令牌
    login_data = {
        'username': 'h4zhang',
        'password': 'Holmes=-0',
        'csrfmiddlewaretoken': csrf_token  # 添加CSRF令牌到请求数据中
    }
    print(f"[1.0] <-- CSRF token: [{csrf_token}] -->")
    # 发送登录请求
    response = session.post(login_url, data=login_data, proxies=proxies)
    # print(response.text)

    # data_summary(session)
    send_to_mail(session)


trigger_send_to_mail()
