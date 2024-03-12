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
from datetime import datetime, timedelta
import pytz
import re
import holidays


def get_token():
    # 定义请求的URL
    url = 'https://rep-portal.wroclaw.nsn-rdnet.net/jwt/obtain/'
    # 定义POST请求的数据（字典形式）
    data = {
        "username": "h4zhang",
        "password": "Holmes=-0"
    }
    # send POST request
    response = requests.post(url, json=data)
    # Convert the JSON string to a Python dictionary
    result = json.loads(response.text)
    # Get the value of the "token" key
    t = result["token"]
    # 输出 'token'
    # print("=== token ===\n", t)
    return t


def validate_token(t):
    global count
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
        print(f"=== [{count}] token is valid ===")
        count += 1
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


# 用 get_latest_build 获取昨天的 CIT build，用 get_no_run_case_list_on_cit_build 获取这个包上 no run case list
def get_latest_build(url, t, yesterday_date_yy_mm_dd):
    i = 0
    build = ""
    builds = []
    # query source data from rep
    query_rep_result = query_rep(url, t)
    if len(query_rep_result['data']):
        logging.debug("<--get result from rep done-->")
    while i < len(query_rep_result['data']):
        builds.append(query_rep_result['data'][i]['Builds'][:29])
        i += 1

    for element in builds:
        if yesterday_date_yy_mm_dd in element:
            build = element
            break
    # 输出结果
    if build:
        # print(f"CIT build: [{build}]")
        return build
    else:
        # print(f"CIT build not found")
        return None


def get_no_run_case_list_on_cit_build(url, t):
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
        case_name.append(re.sub(r'^[^a-zA-Z]*(?=[a-zA-Z])', '', query_rep_result['results'][i]['name']))  # 去掉第一个英文字母前的字符
        qc_status.append(query_rep_result['results'][i]['wall_status']['status'])
        test_entity.append(query_rep_result['results'][i]['test_entity'])
        case_owner.append(re.sub(r'\(\w+\)', '', query_rep_result['results'][i]['res_tester']))  # 去掉()及()内字符
        last_qc_run.append(query_rep_result['results'][i]['last_testrun']['timestamp'][:10])
        i += 1
    return case_name, qc_status, test_entity, case_owner, last_qc_run


# 用 get_result_not_analyzed 获取 not analyzed case list, 包括 CRT/CIT
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
        case_owner.append(re.sub(r'\(\w+\)', '', query_rep_result['results'][i]['qc_test_instance']['res_tester']))  # 去掉()及()内字符
        last_qc_run.append(query_rep_result['results'][i]['end'][:10])
        i += 1
    return case_name, qc_status, test_entity, case_owner, last_qc_run


# 用 get_result_retest 获取需要重跑的 case list，一般是有PR关了
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
        case_name.append(re.sub(r'^[^a-zA-Z]*(?=[a-zA-Z])', '', query_rep_result['results'][i]['name']))  # 去掉第一个英文字母前的字符
        qc_status.append(query_rep_result['results'][i]['status'])
        test_entity.append(query_rep_result['results'][i]['test_entity'])
        # case_owner.append(query_rep_result['results'][i]['res_tester'])
        case_owner.append(re.sub(r'\(\w+\)', '', query_rep_result['results'][i]['res_tester']))  # 去掉()及()内字符
        last_qc_run.append(query_rep_result['results'][i]['last_testrun']['timestamp'][:10])
        ready_for_retest.append(query_rep_result['results'][i]['ready_for_retest'])
        i += 1
    return case_name, qc_status, test_entity, case_owner, last_qc_run, ready_for_retest


# 用 get_case_planned_in_this_fb 获取这个 FB 需要执行的 case
def get_case_planned_in_this_fb(url, t):
    i = 0
    case_name = []
    qc_status = []
    feature = []
    case_owner = []
    plan_to_run = []
    fault_id = []
    # get last_day_of_fb
    today = datetime.today()
    result = get_today_detail(today)
    last_day_of_fb = result[3]
    # query source data from rep
    query_rep_result = query_rep(url, t)
    # print(query_rep_result)
    if len(query_rep_result['results']):
        logging.debug("<--get result from rep done-->")
    while i < len(query_rep_result['results']):
        if datetime.strptime(query_rep_result['results'][i]['planned_test_set_ends'], "%Y-%m-%d") <= datetime.strptime(last_day_of_fb, "%Y-%m-%d"):
            case_name.append(re.sub(r'^[^a-zA-Z]*(?=[a-zA-Z])', '', query_rep_result['results'][i]['name']))
            qc_status.append(query_rep_result['results'][i]['status'])
            feature.append(query_rep_result['results'][i]['feature'])
            case_owner.append(re.sub(r'\(\w+\)', '', query_rep_result['results'][i]['res_tester']))  # 去掉()及()内字符
            plan_to_run.append(query_rep_result['results'][i]['planned_test_set_ends'])
            fault_id.append(query_rep_result['results'][i]['fault_report_id_link'][0]['id'])
        else:
            break
        i += 1
    return case_name, qc_status, feature, case_owner, plan_to_run, fault_id


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

# global parameter
count = 1

case_not_analyzed = "https://rep-portal.ext.net.nokia.com/reports/test-runs/?end_ft=2024-02-28%2000%3A00%3A00%2Cnow&limit=200&org=RAN_L3_SW_CN_1_TA&path=%3Ahash%3A403a03937f5a2c9f3463d990ab3498df&result=not%20analyzed"
case_not_analyzed_f12 = "https://rep-portal.ext.net.nokia.com/api/automatic-test/runs/report/?end__ft=2024-02-28%2000%3A00%3A00%2Cnow&fields=id%2Cqc_test_instance__m_path%2Cqc_test_set%2Ctest_case__name%2Curl%2Cresult%2Cresult_color%2Corigin_result%2Cbuilds%2Cqc_test_instance__test_entity%2Cqc_test_instance__res_tester%2Chyperlink_set%2Cend%2Cpronto%2Ccomment%2Ctest_col__testline_type%2Cqc_test_instance__organization&limit=200&qc_test_instance__m_path__pos_neg_empty_str=%3Ahash%3A403a03937f5a2c9f3463d990ab3498df&qc_test_instance__organization__pos_neg=RAN_L3_SW_CN_1_TA&result__name__pos_neg=not%20analyzed"
crt_cit_retest = "https://rep-portal.ext.net.nokia.com/reports/qc/?columns=%3Ahash%3A61bc3fcc83f04ab0b3589c26b9744c7b&limit=200&ordering=name&organization=RAN_L3_SW_CN_1_TA&path=k%5CRAN_L3_SW_CN_1&ready_for_retest=true&status=-N%2FA"
crt_cit_retest_f12 = "https://rep-portal.ext.net.nokia.com/api/qc-beta/instances/report/?fields=id%2Cm_path%2Ctest_set__name%2Cbacklog_id%2Cname%2Curl%2Cstatus%2Cstatus_color%2Cfault_report_id_link%2Ccomment%2Csw_build%2Cplanned_test_set_ends%2Cdet_auto_lvl%2Ctest_entity%2Cres_tester%2Crequirement%2Cpi_id%2Ctest_subarea%2Ctest_lvl_area%2Cfunction_area%2Cca%2Corganization%2Crelease%2Cready_for_retest%2Cfeature%2Clast_testrun__timestamp%2Cautomation_options&limit=200&m_path__pos_neg=k%5CRAN_L3_SW_CN_1&ordering=name&organization__pos_neg=RAN_L3_SW_CN_1_TA&ready_for_retest=true&status__pos_neg=-N%2FA"

link_text_not_analyzed = "Test Run Link"
test_run_url = "https://rep-portal.ext.net.nokia.com/reports/test-runs/?end_ft=2024-02-28%2000%3A00%3A00%2Cnow&limit=200&org=RAN_L3_SW_CN_1_TA&path=%3Ahash%3A403a03937f5a2c9f3463d990ab3498df&result=not%20analyzed"
additional_text_not_analyzed = f"<span style='font-family: 微软雅黑;'>[CIT/CRT] Not analyzed case list: </span> <a href='{test_run_url}' class='link'>{link_text_not_analyzed}</a>"
additional_html_not_analyzed = f"<p>{additional_text_not_analyzed}</p>"

link_text_retest = "Retest Case List"
qc_instance_url = "https://rep-portal.ext.net.nokia.com/reports/qc/?columns=%3Ahash%3A61bc3fcc83f04ab0b3589c26b9744c7b&limit=200&ordering=name&organization=RAN_L3_SW_CN_1_TA&path=k%5CRAN_L3_SW_CN_1&ready_for_retest=true&status=-N%2FA"
additional_text_retest = f"<span style='font-family: 微软雅黑;'>[CIT/CRT] Retest case list: </span> <a href='{qc_instance_url}' class='link'>{link_text_retest}</a>"
additional_html_retest = f"<p>{additional_text_retest}</p>"

link_text_case_planned_in_this_fb = "FB Planned Case List"
case_planned_in_this_fb = "https://rep-portal.ext.net.nokia.com/reports/qc/?columns=%3Ahash%3A840c26f65271ed10e1f00e7daf59a916&limit=200&ordering=planned_test_set_ends&organization=RAN_L3_SW_CN_1_TA&path=s%5CRAN_L3_SW_CN_1&status=-N%2FA%2C%20-Passed"
case_planned_in_this_fb_f12 = "https://rep-portal.ext.net.nokia.com/api/qc-beta/instances/report/?fields=id%2Cm_path%2Ctest_set__name%2Cbacklog_id%2Cname%2Curl%2Cstatus%2Cstatus_color%2Cfault_report_id_link%2Ccomment%2Csw_build%2Cplanned_test_set_ends%2Cdet_auto_lvl%2Ctest_entity%2Cres_tester%2Crequirement%2Cpi_id%2Ctest_subarea%2Ctest_lvl_area%2Cfunction_area%2Cca%2Corganization%2Crelease%2Cfeature%2Clast_testrun__timestamp%2Cautomation_options&limit=200&m_path__pos_neg=s%5CRAN_L3_SW_CN_1&ordering=planned_test_set_ends&organization__pos_neg=RAN_L3_SW_CN_1_TA&status__pos_neg=-N%2FA%2C%20-Passed"
additional_text_case_planned_in_this_fb = f"<span style='font-family: 微软雅黑;'>FB Planned Case List: </span> <a href='{case_planned_in_this_fb}' class='link'>{link_text_case_planned_in_this_fb}</a>"
additional_html_case_planned_in_this_fb = f"<p>{additional_text_case_planned_in_this_fb}</p>"

# mail receiver
mail_receiver = ['hao.6.zhang@nokia-sbell.com']
# mail_receiver = ['i_nsb_mn_ran_rd_vrf_haz3_06@internal.nsn.com', 'hao.6.zhang@nokia-sbell.com']

# Webhook URL
# link only to me
webhook_url = 'https://nokia.webhook.office.com/webhookb2/8a514e5f-105f-44eb-8695-74950f6c2862@5d471751-9675-428d-917b-70f44f9630b0/IncomingWebhook/57929b2325b04cc195e8cb121016422a/24b4cd6e-4864-4fba-b2d1-92fea3819e65'
# link to VRF306
# webhook_url = 'https://nokia.webhook.office.com/webhookb2/479b1e71-9c4d-4554-bff0-5d55b77c538b@5d471751-9675-428d-917b-70f44f9630b0/IncomingWebhook/f2f88b8e5bcd45bb9a718716bbdaf95f/24b4cd6e-4864-4fba-b2d1-92fea3819e65'

token = get_token()


def short_case_name(lst, length):
    shortened_list = [item[:length] for item in lst]
    return shortened_list


def data_summary(t):
    if validate_token(t):
        validated_token = t
    else:  # 如果token失效，就重新获取
        validated_token = get_token()

    # 获取昨天的日期
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_yy_mm_dd = yesterday.strftime('%y%m%d')
    yesterday_yyyy_mm_dd = yesterday.strftime('%Y-%m-%d')

    build_progress = "https://rep-portal.ext.net.nokia.com/charts/build-progress/?branch=SBTS00&ca=RAN_L3_SW_CN_1&date_ft=2024-03-02%2Ctoday&organization=RAN_L3_SW_CN_1_TA&show_empty=true&test_type=cit"
    build_progress_f12 = "https://rep-portal.ext.net.nokia.com/api/charts/build_progress/?branch__pos_neg=SBTS00&chart_creator=amcharts&date__ft=" + yesterday_yyyy_mm_dd + "%2Ctoday&show_empty=true&test_instance__ca__pos_neg=RAN_L3_SW_CN_1&test_instance__organization__pos_neg=RAN_L3_SW_CN_1_TA&test_type=cit"

    builds_for_cit_yesterday = get_latest_build(build_progress_f12, validated_token, yesterday_yy_mm_dd)  # 一般不为空
    print(f'=== [{yesterday_yyyy_mm_dd}] CIT build: [{builds_for_cit_yesterday}] ===')
    no_run_cit_url = "https://rep-portal.ext.net.nokia.com/reports/qc/?ca=RAN_L3_SW_CN_1&columns=%3Ahash%3A43209d55dad2c7d1680622cf6b33db36&daily_build=" + builds_for_cit_yesterday + "&st_on_build=-Passed%2C-Failed&daily_test_type=CIT&limit=25&ordering=name&organization=RAN_L3_SW_CN_1_TA"
    # print(f'no_run_cit_url:', no_run_cit_url)
    no_run_cit_url_f12 = "https://rep-portal.ext.net.nokia.com/api/qc-beta/instances/report/?ca__pos_neg=RAN_L3_SW_CN_1&daily_build=" + builds_for_cit_yesterday + "&daily_test_type=CIT&fields=id%2Cm_path%2Ctest_set__name%2Cbacklog_id%2Cname%2Curl%2Cstatus%2Cstatus_color%2Cfault_report_id_link%2Ccomment%2Csw_build%2Cplanned_test_set_ends%2Cdet_auto_lvl%2Ctest_entity%2Cres_tester%2Crequirement%2Cpi_id%2Ctest_subarea%2Ctest_lvl_area%2Cfunction_area%2Cca%2Corganization%2Crelease%2Cfeature%2Clast_testrun__timestamp%2Cwall_status&limit=25&ordering=name&organization__pos_neg=RAN_L3_SW_CN_1_TA&wall_status=-Passed%2C-Failed"
    # print(f'no_run_cit_url_f12', no_run_cit_url_f12)
    additional_text_no_run_case_list_on_cit_build = f"<span style='font-family: 微软雅黑;'>[CIT/CDRT] No run case list on build: </span> <a href='{no_run_cit_url}' class='link'>{builds_for_cit_yesterday}</a>"
    additional_html_no_run_case_list_on_cit_build = f"<p>{additional_text_no_run_case_list_on_cit_build}</p>"

    # get case list: no_run_case_list_on_cit_build
    source_data_no_run_case_list_on_cit_build = get_no_run_case_list_on_cit_build(no_run_cit_url_f12, validated_token)
    no_run_case_list_on_cit_build_for_mail = {
        'Case Name': short_case_name(source_data_no_run_case_list_on_cit_build[0], 100),
        'QC Status': source_data_no_run_case_list_on_cit_build[1],
        'Test Entity': source_data_no_run_case_list_on_cit_build[2],
        'Case Owner': source_data_no_run_case_list_on_cit_build[3],
        'Last QC Run': source_data_no_run_case_list_on_cit_build[4],
    }
    no_run_case_list_on_cit_build_for_teams = {
        'Case Name': short_case_name(source_data_no_run_case_list_on_cit_build[0], 17),
        'QC Status': source_data_no_run_case_list_on_cit_build[1],
        'Test Entity': source_data_no_run_case_list_on_cit_build[2],
        'Last QC Run': source_data_no_run_case_list_on_cit_build[4],
        'Case Owner': source_data_no_run_case_list_on_cit_build[3],
    }
    # get case list: not_analyzed
    source_data_not_analyzed = get_result_not_analyzed(case_not_analyzed_f12, validated_token)
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
    source_data_retest = get_result_retest(crt_cit_retest_f12, validated_token)
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
    # get case list: get_case_planned_in_this_fb
    source_data_case_planned_in_this_fb = get_case_planned_in_this_fb(case_planned_in_this_fb_f12, validated_token)
    data_case_planned_in_this_fb_for_mail = {
        'Case Name': short_case_name(source_data_case_planned_in_this_fb[0], 100),
        'QC Status': source_data_case_planned_in_this_fb[1],
        'PR ID': source_data_case_planned_in_this_fb[5],
        'Case Owner': source_data_case_planned_in_this_fb[3],
        'LE': source_data_case_planned_in_this_fb[4],
    }
    data_case_planned_in_this_fb_for_teams = {
        'Case Name': short_case_name(source_data_case_planned_in_this_fb[0], 17),
        'QC Status': source_data_case_planned_in_this_fb[1],
        'LE': source_data_case_planned_in_this_fb[4],
        'Case Owner': source_data_case_planned_in_this_fb[3],
    }

    df_no_run_case_list_on_cit_build_for_mail = pd.DataFrame(no_run_case_list_on_cit_build_for_mail)
    df_no_run_case_list_on_cit_build_for_teams = pd.DataFrame(no_run_case_list_on_cit_build_for_teams)
    df_not_analyzed_for_mail = pd.DataFrame(data_not_analyzed_for_mail)
    df_not_analyzed_for_teams = pd.DataFrame(data_not_analyzed_for_teams)
    df_retest_for_mail = pd.DataFrame(data_retest_for_mail)
    df_retest_for_teams = pd.DataFrame(data_retest_for_teams)
    df_case_planned_in_this_fb_for_mail = pd.DataFrame(data_case_planned_in_this_fb_for_mail)
    df_case_planned_in_this_fb_for_teams = pd.DataFrame(data_case_planned_in_this_fb_for_teams)

    return df_no_run_case_list_on_cit_build_for_mail, df_not_analyzed_for_mail, df_retest_for_mail, df_case_planned_in_this_fb_for_mail, \
           df_no_run_case_list_on_cit_build_for_teams, df_not_analyzed_for_teams, df_retest_for_teams, df_case_planned_in_this_fb_for_teams, \
           additional_html_no_run_case_list_on_cit_build


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
    return "\n\n".join(text_list)  # 返回所有文本行，每行后都有换行符，需要两个换行符才能在 Teams 中显示出换行符


def today_detail_info():
    today = datetime.today()
    # today = datetime(2024, 5, 1)  # Test the function
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


def send_to_teams(df1, df2, df3, df4, msg1, msg2):
    # send hello message
    msg0 = "Hi there! Good day!"
    msg3 = "Here is daily news for you:"
    message_text0 = f"{msg0}\n\n{msg1}\n\n{msg2}\n\n{msg3}\n\n------"

    # 对于第一个DataFrame
    if df1.empty:
        message_text1 = f"1.[CIT/CDRT] No run case list for today CIT build: None\n\n------"
    else:
        # 将每行数据连接成字符串，并在每行末尾添加换行符
        df_string1 = df_to_text(df1)
        message_text1 = f"1.[CIT/CDRT] No run case list for today CIT build:\n\n{df_string1}\n\n------"

    # 对于第二个DataFrame
    if df2.empty:
        message_text2 = f"2.[CIT/CRT] Not analyzed case list: None\n\n------"
    else:
        # 将每行数据连接成字符串，并在每行末尾添加换行符
        df_string2 = df_to_text(df2)
        message_text2 = f"2.[CIT/CRT] Not analyzed case list:\n\n{df_string2}\n\n------"

    # 对于第三个DataFrame
    if df3.empty:
        message_text3 = "3.[CIT/CRT] Retest case list: None\n\n------"
    else:
        # 将每行数据连接成字符串，并在每行末尾添加换行符
        df_string3 = df_to_text(df3)
        message_text3 = f"3.[CIT/CRT] Retest case list:\n\n{df_string3}\n\n------"

    # 对于第四个DataFrame
    if df4.empty:
        message_text4 = "4.Case planned in this FB: Done\n\n------"
    else:
        # 将每行数据连接成字符串，并在每行末尾添加换行符
        df_string4 = df_to_text(df4)
        message_text4 = f"4.Case planned in this FB:\n\n{df_string4}\n\n------"

    # 创建消息内容，合并两个消息文本
    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": "Your Assistant",
        "sections": [{
            "activityTitle": "Daily News",
            "text": f"{message_text0}\n\n{message_text1}\n\n{message_text2}\n\n{message_text3}\n\n{message_text4}",  # 合并两个DataFrame的文本+超链接文本
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


def send_to_teams_exception():
    # 创建消息内容
    message_text0 = "ReP data not available"
    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": "Your Assistant",
        "sections": [{
            "activityTitle": "Daily News",
            "text": f"{message_text0}\n\n",
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


def send_to_mail(df1, df2, df3, df4, additional_html_no_run_case_list_on_cit_build):
    # 将DataFrame转换格式以在Email中显示
    formatted_df1 = format_df(df1)
    formatted_df2 = format_df(df2)
    formatted_df3 = format_df(df3)
    formatted_df4 = format_df(df4)

    # 应用高亮格式并转换为HTML，且隐藏默认索引
    styled_html_1 = formatted_df1.style.applymap(highlight).hide_index().render()
    styled_html_2 = formatted_df2.style.applymap(highlight).hide_index().render()
    styled_html_3 = formatted_df3.style.applymap(highlight).hide_index().render()
    styled_html_4 = formatted_df4.style.applymap(highlight).hide_index().render()

    # 应用css格式 + 自定义文本 + 高亮格式1&2
    html_content = (
            css_style +
            additional_html_no_run_case_list_on_cit_build +
            styled_html_1 +
            additional_html_not_analyzed +
            styled_html_2 +
            additional_html_retest +
            styled_html_3 +
            additional_html_case_planned_in_this_fb +
            styled_html_4
    )

    # Create an instance of the MailSender class
    mail_sender = MailSender()

    # Define the email parameters
    receiver = mail_receiver  # Receiver list
    subject = '[CIT/CRT] No Run & Not Analyzed & Retest Case List'  # Email subject
    content = html_content  # Email content

    # Send the email with HTML content
    mail_sender.send_mail(receiver, subject, content, is_html=True)


def trigger_send_to_mail():
    result = data_summary(token)
    # return for data_summary
    # df_no_run_case_list_on_cit_build_for_mail, df_not_analyzed_for_mail, df_retest_for_mail, df_case_planned_in_this_fb_for_mail, \
    # df_no_run_case_list_on_cit_build_for_teams, df_not_analyzed_for_teams, df_retest_for_teams, df_case_planned_in_this_fb_for_teams, \
    # additional_html_no_run_case_list_on_cit_build
    send_to_mail(result[0], result[1], result[2], result[3], result[8])
    print("=== Current time:", datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S"), "===\n")


def trigger_send_to_teams():
    try:
        msg_day_info, msg_holiday_info = today_detail_info()
        result = data_summary(token)
        send_to_teams(result[4], result[5], result[6], result[7], msg_day_info, msg_holiday_info)
        print("=== Current time:", datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S"), "===\n")
    except Exception as e:
        send_to_teams_exception()
        print(e)
        print("=== Current time:", datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S"), "===\n")


# test in local
trigger_send_to_mail()
trigger_send_to_teams()

# 定时收数据并发邮件
# scheduler = BlockingScheduler()
# scheduler.add_job(trigger_send_to_mail, 'cron', day_of_week='0-6', hour='8', minute='5', timezone="Asia/Shanghai")
# scheduler.add_job(trigger_send_to_teams, 'cron', day_of_week='0-6', hour='8, 14', minute='5', timezone="Asia/Shanghai")
# scheduler.start()
