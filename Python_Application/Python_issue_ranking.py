# coding=utf-8
from jira import JIRA
import pandas as pd
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


# jira_filter = '''project = 68296 AND reporter in (membersOf(I_MN_RAN_L3_SW_1_CN_ET)) AND created >= startOfMonth() ORDER BY key DESC'''
# issues = searchIssues(jira_filter)
#
# team_shield = ['Lei, Damon', 'Zhang, Jun 15.', 'Cao, Jiangping', 'Liu, Qiuqi', 'Yan, Susana', 'Wang, Alex 2.', 'Ye, Jun 3.']
# team_jazz = ['Chen, Dandan', 'Tong, Doris', 'Li, Delun', 'Zhou, Lingyan', 'Tang, Zheng', 'Jia, Lijun J.', 'Yang, Chunjian']
# team_blues = ['Ge, Nanxiao', 'Zhang, Sherry', 'Zhang, Yige G.', 'Zhu, Ruifang', 'Zhang, Hao 6.', 'Zheng, Ha', 'Xu, Xiaowen', ]
# team_rock = ['Fan, Jolin', 'Zhuo, Lena', 'Wu, Jiadan', 'Chen, Christine', 'Wang, Zora', 'Fang, Liupei', 'Ye, Jing']
# counter_shield = 0
# counter_jazz = 0
# counter_blues = 0
# counter_rock = 0
# team = []
# month = []
# counter = []
#
# for issue in issues:
#     # print(issue.fields.created[0:7], str(issue.fields.reporter)[:-20])
#     month.append(issue.fields.created[0:7])
#     if str(issue.fields.reporter)[:-20] in team_shield:
#         counter_shield = counter_shield + 1
#         team.append('Shield')
#         counter.append(1)
#     elif str(issue.fields.reporter)[:-20] in team_jazz:
#         counter_jazz = counter_jazz + 1
#         team.append('Jazz')
#         counter.append(1)
#     elif str(issue.fields.reporter)[:-20] in team_blues:
#         counter_blues = counter_blues + 1
#         team.append('Blues')
#         counter.append(1)
#     elif str(issue.fields.reporter)[:-20] in team_rock:
#         counter_rock = counter_rock + 1
#         team.append('Rock')
#         counter.append(1)
# # print(counter_shield, counter_jazz, counter_blues, counter_rock)
#
# pd.set_option(
#     'precision', 1,
#     'display.max_rows', 500,
#     'display.max_columns', 500,
#     'display.width', 1000)
# # 设置参数：精度，最大行，最大列，最大显示宽度
# data = (list(zip(team, month, counter)))
# current_month = month[0]
# df = pd.DataFrame(data)
# df.columns = ['Team', 'Month', 'Counter']
# # df.sort_values('Month')
# # print(df, '\n')
# pivoted_df = pd.pivot_table(df,
#                             index='Team',
#                             columns='Month',
#                             values=['Counter'],
#                             aggfunc='sum',
#                             fill_value=0)
# pivoted_df = pivoted_df.sort_values(('Counter', current_month), ascending=False)
# print(pivoted_df)


def issue_hunter_star(issues):
    star = []
    month = []
    for issue in issues:
        month.append(issue.fields.created[0:7])
        star.append(str(issue.fields.reporter)[:-20])
    return star, month


jira_filter_issues_this_year = '''project = 68296 AND reporter in (membersOf(I_MN_RAN_L3_SW_1_CN_ET)) AND created > startOfYear() ORDER BY key DESC'''
month = []

jira_list_year = search_data(jira_filter_issues_this_year)
jira_list_year_ = issue_hunter_star(jira_list_year)
last_month = jira_list_year_[1][0]
counter = Counter(jira_list_year_[0]).most_common(5)
print(counter)
first, second = zip(*counter)
print(first)
print(second)

for i in range(0, len(first)):
    month.append(last_month)
print(month)
