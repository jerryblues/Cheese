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
                    filename='django_local_cit_report.log',
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


def get_single_run_id(session, date):
    # 获取昨天的日期
    # yesterday = datetime.now() - timedelta(days=1)
    yesterday = date - timedelta(days=1)
    yesterday_yyyy_mm_dd = yesterday.strftime('%Y-%m-%d')

    # 获取昨天16点之后的 single run，换算过来就是当天00:00开始到7：59结束的，且phase=SingleRun (排除Reported Single run) 的 single run
    url_single_run_filter = "https://cloud.ute.nsn-rdnet.net/execution/search/ajax?format=json&test_path=testsuite%2FHangzhou%2FRRM%2FRAN_L3_SW_CN_HZ%2Ftrunk_sbts%2FCRT%2FCN1%2F&topology=&status=&queue=&phase__in=SingleRun&user=&start_date__gte=&start_date__lte=&end_date__gte=&end_date__lte=&add_date__gte=" + yesterday_yyyy_mm_dd + "+16%3A00&add_date__lte=" + yesterday_yyyy_mm_dd + "+23%3A59&execution_count=&test_repository_revision=&skiprun=&state=&additional_parameters=&ordering=-id&limit=50&offset=0&no_cache=9761"
    url_single_run_for_web = "https://cloud.ute.nsn-rdnet.net/execution/search/?test_path=testsuite%2FHangzhou%2FRRM%2FRAN_L3_SW_CN_HZ%2Ftrunk_sbts%2FCRT%2FCN1%2F&topology=&status=&queue=&phase__in=SingleRun&user=&start_date__gte=&start_date__lte=&end_date__gte=&end_date__lte=&add_date__gte=" + yesterday_yyyy_mm_dd + "+16%3A00&add_date__lte=" + yesterday_yyyy_mm_dd + "+23%3A59&execution_count=&test_repository_revision=&skiprun=&state=&additional_parameters="

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


def get_single_run_result(session, date):
    case_result = []
    case_name = []
    log_links = []
    single_run_links = []
    owner_name = []
    pass_case_num, fail_case_num, running_case_num, total_case_num = 0, 0, 0, 0
    ids, url_single_run_for_web = get_single_run_id(session, date)

    for single_run_id in ids:
        url_single_run = "https://cloud.ute.nsn-rdnet.net/cm/execution/" + str(single_run_id) + "/show"
        # print(url_single_run)

        response = session.get(url_single_run, headers=headers, proxies=proxies)

        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(response.text, 'lxml')  # 或者使用 'html.parser' 作为解析器
        # print("soup:", soup)
        # print("url_single_run:", url_single_run)

        # 提取状态和描述
        status_elements = soup.select('td.status')

        # 遍历匹配到的元素
        for status in status_elements:
            # 打印状态
            # print("status:", status.text.strip())
            case_result.append(status.text.strip())
            # 打印描述（状态的下一个兄弟节点）
            # print("case:", status.find_next_sibling('td').text.strip())
            case_name.append(status.find_next_sibling('td').text.strip()[:80])

            # 提取链接和链接文本
            # execution_log_link = soup.find('a', string='Execution logs')
            # if execution_log_link:
            #     # print("link:", execution_log_link['href'])  # 打印链接
            #     # print("text:", execution_log_link.text)  # 打印链接文本
            #     log_links.append(execution_log_link['href'])

            # 获取 single run links
            single_run_links.append(url_single_run)

            # 提取 owner name
            owner_td = soup.find('td', string='Owner')
            next_td = owner_td.find_next_sibling('td')
            owner_name.append(next_td.text.strip())

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

    return case_result, case_name, owner_name, single_run_links, url_single_run_for_web, pass_case_num, fail_case_num, running_case_num, total_case_num


def data_summary(session, date):
    case_result, case_name, owner_name, single_run_links, url_single_run_for_web, pass_case_num, fail_case_num, running_case_num, total_case_num = get_single_run_result(session, date)
    result_summary = {
        'Case_Name': case_name,
        'Triggered_By': owner_name,
        'Test_Result': case_result,
        'Log_Link': single_run_links,
    }

    df_result_summary = pd.DataFrame(result_summary)
    return df_result_summary
