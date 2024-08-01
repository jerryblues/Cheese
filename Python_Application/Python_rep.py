# coding=utf-8
import logging
import json
import requests
import re
from datetime import datetime, timedelta


def get_token():
    # 定义请求的URL
    url = 'https://rep-portal.wroclaw.nsn-rdnet.net/jwt/obtain/'
    # 定义POST请求的数据（字典形式）
    data = {
        "username": "xxx",
        "password": "xxx"
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


# 获取昨天的日期
yesterday = datetime.now() - timedelta(days=1)
yesterday_yy_mm_dd = yesterday.strftime('%y%m%d')
yesterday_yyyy_mm_dd = yesterday.strftime('%Y-%m-%d')

build_f12 = "https://rep-portal.ext.net.nokia.com/api/charts/build_progress/?branch__pos_neg=SBTS00&chart_creator=amcharts&date__ft=" + yesterday_yyyy_mm_dd + "%2Ctoday&show_empty=true&test_instance__ca__pos_neg=%22RAN_L3_SW_CN_1%22&test_instance__organization__pos_neg=RAN_L3_SW_CN_1_TA&test_type=cit"

token = get_token()
latest_build = get_latest_build(build_f12, token, yesterday_yy_mm_dd)
print(f"CIT build: [{latest_build}]")

not_cit_result_url_f12 = "https://rep-portal.ext.net.nokia.com/api/qc-beta/instances/report/?ca__pos_neg=%22RAN_L3_SW_CN_1%22&daily_build=" + latest_build + "&daily_status=not%20analyzed&daily_test_type=CIT&fields=id%2Cm_path%2Ctest_set__name%2Cbacklog_id%2Cname%2Curl%2Cstatus%2Cstatus_color%2Cfault_report_id_link%2Ccomment%2Csw_build%2Cplanned_test_set_ends%2Cdet_auto_lvl%2Ctest_entity%2Cres_tester%2Crequirement%2Cpi_id%2Ctest_subarea%2Ctest_lvl_area%2Cfunction_area%2Cca%2Corganization%2Crelease%2Cfeature%2Clast_testrun__timestamp%2Cwall_status&limit=25&ordering=name&organization__pos_neg=RAN_L3_SW_CN_1_TA"
case_planned_in_this_fb_f12 = "https://rep-portal.ext.net.nokia.com/api/qc-beta/instances/report/?fields=id%2Cm_path%2Ctest_set__name%2Cbacklog_id%2Cname%2Curl%2Cstatus%2Cstatus_color%2Cfault_report_id_link%2Ccomment%2Csw_build%2Cplanned_test_set_ends%2Cdet_auto_lvl%2Ctest_entity%2Cres_tester%2Crequirement%2Cpi_id%2Ctest_subarea%2Ctest_lvl_area%2Cfunction_area%2Cca%2Corganization%2Crelease%2Cfeature%2Clast_testrun__timestamp%2Cautomation_options&limit=200&m_path__pos_neg=s%5CRAN_L3_SW_CN_1&ordering=planned_test_set_ends&organization__pos_neg=RAN_L3_SW_CN_1_TA&status__pos_neg=-N%2FA%2C%20-Passed"


def get_case_list(url, t):
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
        case_name.append(re.sub(r'^[^a-zA-Z]*(?=[a-zA-Z])', '', query_rep_result['results'][i]['name'][:100]))  # 去掉第一个英文字母前的字符
        qc_status.append(query_rep_result['results'][i]['wall_status']['status'])
        test_entity.append(query_rep_result['results'][i]['test_entity'])
        case_owner.append(re.sub(r'\(\w+\)', '', query_rep_result['results'][i]['res_tester']))  # 去掉()及()内字符
        last_qc_run.append(query_rep_result['results'][i]['last_testrun']['timestamp'][:10])
        i += 1
    # print(case_name, qc_status, test_entity, case_owner, last_qc_run)
    return case_name, qc_status, test_entity, case_owner, last_qc_run


def get_case_planned_this_fb(url, t):
    i = 0
    case_name = []
    qc_status = []
    feature = []
    case_owner = []
    plan_to_run = []
    fault_id = []

    # query source data from rep
    query_rep_result = query_rep(url, t)
    # print(query_rep_result)
    if len(query_rep_result['results']):
        logging.debug("<--get result from rep done-->")
    while i < len(query_rep_result['results']):
        if datetime.strptime(query_rep_result['results'][i]['planned_test_set_ends'], "%Y-%m-%d") <= datetime.strptime("2024-03-12", "%Y-%m-%d"):
            case_name.append(re.sub(r'^[^a-zA-Z]*(?=[a-zA-Z])', '', query_rep_result['results'][i]['name']))
            qc_status.append(query_rep_result['results'][i]['status'])
            feature.append(query_rep_result['results'][i]['feature'])
            case_owner.append(re.sub(r'\(\w+\)', '', query_rep_result['results'][i]['res_tester']))  # 去掉()及()内字符
            plan_to_run.append(query_rep_result['results'][i]['planned_test_set_ends'])
            fault_id.append(query_rep_result['results'][i]['fault_report_id_link'][0]['id'])
        else:
            break
        i += 1
    print(case_name, qc_status, feature, case_owner, plan_to_run, fault_id)
    return case_name, qc_status, feature, case_owner, plan_to_run, fault_id


result = get_case_list(not_cit_result_url_f12, token)
print(result[0], result[3])

get_case_planned_this_fb(case_planned_in_this_fb_f12, token)
