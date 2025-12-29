# coding=utf-8
"""
@file: ET_ReP_Jira.py.py
@time: 2023/4/26 11:01
@author: h4zhang
"""
import requests
import json
import pandas as pd
from flask import Flask, render_template, request
from jira import JIRA
from flask import Flask, jsonify, render_template
import re
import logging

# token = "first token is invalid"

logging.basicConfig(level=logging.INFO,
                    filename='ET_statistics.log',
                    filemode='a',
                    format='%(asctime)s - %(levelname)s: %(message)s'
                    )

# Jira configuration
jira_server = 'https://jiradc.ext.net.nokia.com'  # jira地址
jira_username = 'xxx'  # 用户名，本地调试时，可用明文代替
jira_password = 'xxx'  # 密码，本地调试时，可用明文代替


def get_token():
    # 定义请求的URL
    url = 'https://rep-portal.wroclaw.nsn-rdnet.net/jwt/obtain/'
    # 定义POST请求的数据（字典形式）
    data = {
        "username": "xxx",
        "password": "xxx"
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
    print("===token===\n", t)
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
        print("===token is valid===")
        return True
    else:
        print("===response===\n", res)
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


def query_jira(link):
    key = []
    end_fb = []
    label = []
    jira_dict = {}
    try:
        jira = JIRA(basic_auth=(jira_username, jira_password), options={'server': jira_server})
        issues = jira.search_issues(link, maxResults=1000)
    except Exception as e:
        logging.info(f"[Error] {e}")
        return None
    else:
        for issue in issues:
            key.append(issue.key)  # get backlog_id
            end_fb.append(issue.fields.customfield_38693)
            label.append(issue.fields.labels)
            jira_dict = dict(zip(key, zip(end_fb, label)))  # save 3 list into dict
        return jira_dict


def get_result(url, t):
    i = 0
    backlog_id = []
    case_name = []
    qc_status = []
    end_fb = []
    label = []

    # query backlog ID and case name from reporting portal, 'feature' is from input on web
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
        # 查询jira前，先登录和鉴权
        # jira_login_auth = JIRA(basic_auth=(jira_username, jira_password), options={'server': jira_server})
        while i < len(query_rep_result['results']):
            if query_rep_result['results'][i]['backlog_id']:
                backlog_id.append(query_rep_result['results'][i]['backlog_id'][0]['id'])
            else:
                backlog_id.append('FPB-484682')  # 这里 backlog id 给了一个默认值，如果给0的话，下面无法批量查询

            # 完整的case name
            fullname = query_rep_result['results'][i]['name']
            # 如果截取fullname中第一个英文字符开始的100个字符
            case_name.append(fullname[re.search('[a-zA-Z]', fullname).start():120] + '...')

            qc_status.append(query_rep_result['results'][i]['status'])
            i += 1
        logging.debug(f"[{i}] <--get backlog_id from query_rep_result-->")
        logging.debug(f"[{i}] <--get case_name from query_rep_result-->")
        logging.debug(f"[{i}] <--get qc_status from query_rep_result-->")

        # query end FB and label from Jira, according to backlog_id
        # 将获取到的 backlog_id 组装成 jira 查询链接，供批量查询
        query_link = "key in ({})".format(', '.join("{}".format(item) for item in backlog_id))
        logging.debug(f"{query_link}")
        query_jira_result = query_jira(query_link)
        if query_jira_result:  # 如果query_jira_result有值
            logging.debug(f"{query_jira_result}")
            for element in backlog_id:
                value1, value2 = query_jira_result[element]
                logging.debug(f"{value1}")
                logging.debug(f"{value2}")
                end_fb.append(value1)
                tc_tag = [s for s in value2 if s.startswith('TC')]
                logging.debug(f"{tc_tag}")
                if tc_tag:
                    case_number = int(re.findall(r'\d+', tc_tag[0])[0])
                else:
                    case_number = 0
                logging.debug(f"{case_number}")
                label.append(case_number)
            logging.debug(f"<--end_fb: {end_fb}-->")
            logging.debug(f"[{len(end_fb)}] <--get end_fb from query_jira_result-->")
            logging.debug(f"<--label: {label}-->")
            logging.debug(f"[{len(label)}] <--get case_label from query_jira_result-->")
            return backlog_id, end_fb, label, case_name, qc_status
        else:  # 如果query_jira_result为空，比如jira server挂了
            for id in backlog_id:
                end_fb.append('0')
                label.append(0)
            return backlog_id, end_fb, label, case_name, qc_status
    else:
        logging.debug("<--get result[null] from rep done-->")
        return backlog_id, end_fb, label, case_name, qc_status


# 取出唯一的backlog ID，并把对应的label个数累加
def summary(lst1, lst2):
    logging.debug(f"<--backlog_id: {lst1}-->")
    logging.debug(f"<--label: {lst2}-->")
    distinct_indexes = []
    seen = set()
    for i, x in enumerate(lst1):
        if x not in seen:
            seen.add(x)
            distinct_indexes.append(i)
    # print(distinct_indexes)
    total = 0
    for i in distinct_indexes:
        total = total + lst2[i]
    # print(total)
    return total

# app = Flask(__name__)
#
#
# @app.route("/feature_info")
# def index():
#     return render_template("et_rep_jira.html")
#
#
# @app.route("/feature_info", methods=["POST"])
# def process_input():
#     global token
#     if not validate_token(token):  # 如果token失效，就重新获取
#         token = get_token()
#     feature = request.form.get("feature_id")  # get input from web
#     url_case_info = "https://rep-portal.ext.net.nokia.com/api/qc-beta/instances/report/?fields=id%2Cm_path%2Ctest_set__name%2Cbacklog_id%2Cname%2Curl%2Cstatus%2Cstatus_color%2Cfault_report_id_link%2Ccomment%2Csw_build%2Cres_tester%2Ctest_entity%2Cfunction_area%2Cca%2Corganization%2Crelease%2Cfeature%2Crequirement%2Clast_testrun__timestamp&limit=200&m_path__pos_neg=New_Features%5CRAN_L3_SW_CN_1&ordering=name&test_set__name__pos_neg_empty_str="
#     url_case_info_feature = url_case_info + feature
#     source_data = get_result(url_case_info_feature, token)
#     data = {
#         'backlog_id': source_data[0],
#         'end_fb': source_data[1],
#         'case_name': source_data[2],
#         'label': source_data[3],
#         'qc_status': source_data[4]
#     }
#     total_label = summary(source_data[0], source_data[3])
#     # print("total label", total_label)
#     total_case = len(source_data[2])
#     # print("total case", total_case)
#     df = pd.DataFrame(data)
#     # 表格数据由df传入，数值则直接传入html
#     return render_template('et_rep_jira.html', data=df.to_dict('records'), total_label=total_label, total_case=total_case)
#
#
# if __name__ == '__main__':
#     app.run(debug=True, host='127.0.0.1', port=8080)
