# coding=utf-8
from jira import JIRA
import pandas as pd
import time
import datetime
from collections import Counter


'''
# lib to install
pip3 install pandas
pip3 install jira
'''
# 1.抓取数据
# account = input('>>>>>:').strip()    # 本地调试时注释掉
# password = input('>>>>>:').strip()   # 本地调试时注释掉

jira_server = 'https://jiradc.ext.net.nokia.com'  # jira地址
jira_username = 'h4zhang'  # 用户名，本地调试时，可用明文代替
jira_password = 'Holmes0-0'  # 密码，本地调试时，可用明文代替

jira = JIRA(
    basic_auth=(
        jira_username,
        jira_password),
    options={
        'server': jira_server})


def search_data(jql, max_results=1000):
    """
    Search issues
    @param jql: JQL, str
    @param max_results: max results, int, default 1000
    @return issues: result, list
    """
    try:
        issues = jira.search_issues(jql, maxResults=max_results)
        return issues
    except Exception as e:
        print(e)


jira_filter_long_open_issue = '''project = 68296 AND reporter in (membersOf(I_MN_RAN_L3_SW_1_CN_ET)) AND status not in (Done, CNN, FNR, "Transferred out") ORDER BY created ASC, key DESC'''


def find_long_open_issue(issues):
    feature = []
    fault_id = []
    reporter = []
    created_date = []
    status = []
    open_day = []
    current_day = datetime.datetime.now()

    for issue in issues:
        feature.append(issue.fields.customfield_37381)
        fault_id.append(issue.fields.key)
        reporter.append(str(issue.fields.reporter)[:-20])
        created_date.append(issue.fields.created[:-18])
        status.append(issue.fields.status)

    return feature, reporter, created_date, status, fault_id


def pivot_long_open_issue(feature, reporter, created_date, status, fault_id):
    pd.set_option(  # 设置参数：精度，最大行，最大列，最大显示宽度
        'precision', 1,
        'display.max_rows', 500,
        'display.max_columns', 500,
        'display.width', 1000)
    df = pd.DataFrame((list(zip(feature, reporter, created_date, status, fault_id))))
    df.columns = ["Feature", "Reporter", "Created Date", "Status"]
    df.index = df.index + 1
    # print("print_df", '\n', df)
    # print(df.dtypes)
    return df


jira_long_open_issue = search_data(jira_filter_long_open_issue)
data = find_long_open_issue(jira_long_open_issue)
table = pivot_long_open_issue(data[0], data[1], data[2], data[3], data[4])
print(table)
