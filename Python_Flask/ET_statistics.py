# coding=utf-8
from jira import JIRA
import pandas as pd
from flask import Flask, render_template
from datetime import datetime
import pytz
import logging
from collections import Counter

'''
# lib to install
pip3 install jira
pip3 install pandas
pip3 install flask
pip3 install apscheduler
'''
# account = input('>>>>>:').strip()    # 本地调试时注释掉
# password = input('>>>>>:').strip()   # 本地调试时注释掉

jira_server = 'https://jiradc.ext.net.nokia.com'  # jira地址
jira_username = 'h4zhang'  # 用户名，本地调试时，可用明文代替
jira_password = 'Holmes0-0'  # 密码，本地调试时，可用明文代替

# jira = JIRA(basic_auth=(jira_username, jira_password), options={'server': jira_server})
jira_filter_ET = '''
    project = FCA_5G_L2L3 AND issuetype in (epic) AND resolution = Unresolved AND status not in (Done, obsolete) AND cf[29790] in (5253, 5254, 5255, 5351, 6261) ORDER BY cf[38693] ASC, key ASC
'''

jira_filter_ET_Jazz = '''project = FCA_5G_L2L3 AND issuetype in (epic) AND resolution = Unresolved AND status not in (Done, obsolete) AND cf[29790] in (5253) ORDER BY cf[38693] ASC, key ASC'''
jira_filter_ET_Blues ='''project = FCA_5G_L2L3 AND issuetype in (epic) AND resolution = Unresolved AND status not in (Done, obsolete) AND cf[29790] in (5254) ORDER BY cf[38693] ASC, key ASC'''
jira_filter_ET_Rock = '''project = FCA_5G_L2L3 AND issuetype in (epic) AND resolution = Unresolved AND status not in (Done, obsolete) AND cf[29790] in (5351) ORDER BY cf[38693] ASC, key ASC'''
jira_filter_ET_Shield = '''project = FCA_5G_L2L3 AND issuetype in (epic) AND resolution = Unresolved AND status not in (Done, obsolete) AND cf[29790] in (6261) ORDER BY cf[38693] ASC, key ASC'''

jira_filter_issues_all = '''project = 68296 AND reporter in (membersOf(I_MN_RAN_L3_SW_1_CN_ET)) and issuetype = Bug AND status != CNN ORDER BY key DESC'''
jira_filter_issues_this_year = '''project = 68296 AND reporter in (membersOf(I_MN_RAN_L3_SW_1_CN_ET)) AND created > startOfYear() and issuetype = Bug AND status != CNN ORDER BY key DESC'''
jira_filter_issues_this_month = '''project = 68296 AND reporter in (membersOf(I_MN_RAN_L3_SW_1_CN_ET)) AND created >= startOfMonth() and issuetype = Bug AND status != CNN ORDER BY key DESC'''


def search_data(jql, max_results=10000):  # 抓取数据
    """
    Search issues
    @param jql: JQL, str
    @param max_results: max results, int, default 1000
    @return issues: result, list
    """
    jira = JIRA(basic_auth=(jira_username, jira_password), options={'server': jira_server})
    try:
        issues = jira.search_issues(jql, maxResults=max_results)
        return issues
    except Exception as e:
        print(e)


def convert_data(string):  # 转换格式
    if string is None:
        return 0
    else:
        return float(string.replace(',', '').replace('h', ''))


def get_data(issues):  # 处理数据
    team, end_fb, time_remaining, time_remaining_percentage, feature = [], [], [], [], []
    squad_jazz_hc = 7
    squad_blues_hc = 7
    squad_rock_hc = 7
    squad_shield_hc = 6
    squad_c_hc = 8
    squad_jazz_cap = squad_jazz_hc * 120 - 40
    squad_blues_cap = squad_blues_hc * 120 - 40
    squad_rock_cap = squad_rock_hc * 120 - 40
    squad_shield_cap = squad_shield_hc * 120 - 40
    squad_c_cap = squad_c_hc * 120 - 40

    for issue in issues:
        end_fb.append(issue.fields.customfield_38693)
        feature.append(issue.fields.customfield_37381)
        time_remaining.append(convert_data(issue.fields.customfield_39192))
        if issue.fields.customfield_29790 == '5253':
            team.append('5G_SW_HZH_Jazz')
            time_remaining_percentage.append(convert_data(issue.fields.customfield_39192) / squad_jazz_cap)
        elif issue.fields.customfield_29790 == '5254':
            team.append('5G_SW_HZH_Blues')
            time_remaining_percentage.append(convert_data(issue.fields.customfield_39192) / squad_blues_cap)
        elif issue.fields.customfield_29790 == '5351':
            team.append('5G_SW_HZH_Rock')
            time_remaining_percentage.append(convert_data(issue.fields.customfield_39192) / squad_rock_cap)
        elif issue.fields.customfield_29790 == '6261':
            team.append('5G_SW_HZH_Shield')
            time_remaining_percentage.append(convert_data(issue.fields.customfield_39192) / squad_shield_cap)
        elif issue.fields.customfield_29790 == '5255':
            team.append('5G_SW_HZH_Squad C')
            time_remaining_percentage.append(convert_data(issue.fields.customfield_39192) / squad_c_cap)
    return team, end_fb, time_remaining, time_remaining_percentage, feature


def pivot_data(team, end_fb, time_remaining, time_remaining_percentage):  # 汇总数据
    pd.set_option(  # 设置参数：精度，最大行，最大列，最大显示宽度
        'precision', 1,
        'display.max_rows', 500,
        'display.max_columns', 500,
        'display.width', 1000)
    df0 = pd.DataFrame((list(zip(team, end_fb, time_remaining))))
    df0.columns = ['Team', 'FB', 'Remaining EE']
    pivoted_fb_effort = pd.pivot_table(df0[['Team', 'FB', 'Remaining EE']], values='Remaining EE',
                                       index=['Team'], columns=['FB'], aggfunc='sum', fill_value=0)
    # print(pivoted_fb_effort, '\n')
    df1 = pd.DataFrame((list(zip(team, end_fb, time_remaining_percentage))))
    df1.columns = ['Team', 'FB', 'Percentage']
    pivoted_fb_effort_percentage = pd.pivot_table(df1[['Team', 'FB', 'Percentage']], values='Percentage',
                                                  index=['Team'], columns=['FB'], aggfunc='sum', fill_value=0)\
        .applymap(lambda x: "{0:.1f}%".format(100*x))    # show as percentage
    return pivoted_fb_effort, pivoted_fb_effort_percentage


def pivot_data_team(feature, end_fb, time_remaining):
    pd.set_option(  # 设置参数：精度，最大行，最大列，最大显示宽度
        'precision', 1,
        'display.max_rows', 500,
        'display.max_columns', 500,
        'display.width', 1000)
    df0 = pd.DataFrame((list(zip(feature, end_fb, time_remaining))))
    df0.columns = ['Feature', 'FB', 'Remaining EE']
    pivoted_fb_effort_team = pd.pivot_table(df0[['Feature', 'FB', 'Remaining EE']], values='Remaining EE',
                                       index=['Feature'], columns=['FB'], aggfunc='sum', fill_value=0, margins=True)
    return pivoted_fb_effort_team


def filter_issues(issues):
    team_shield = ['Lei, Damon', 'Zhang, Jun 15.', 'Cao, Jiangping', 'Liu, Qiuqi', 'Yan, Susana', 'Wang, Alex 2.', 'Ye, Jun 3.']
    team_jazz = ['Chen, Dandan', 'Tong, Doris', 'Li, Delun', 'Zhou, Lingyan', 'Tang, Zheng', 'Jia, Lijun J.', 'Yang, Chunjian']
    team_blues = ['Ge, Nanxiao', 'Zhang, Sherry', 'Zhang, Yige G.', 'Zhu, Ruifang', 'Zhang, Hao 6.', 'Zheng, Ha', 'Xu, Xiaowen', ]
    team_rock = ['Fan, Jolin', 'Zhuo, Lena', 'Wu, Jiadan', 'Chen, Christine', 'Wang, Zora', 'Fang, Liupei', 'Ye, Jing']
    counter_shield = 0
    counter_jazz = 0
    counter_blues = 0
    counter_rock = 0
    counter_other = 0
    team = []
    month = []
    counter = []

    for issue in issues:
        month.append(issue.fields.created[0:7])
        if str(issue.fields.reporter)[:-20] in team_shield:
            counter_shield = counter_shield + 1
            team.append('Shield')
            counter.append(1)
        elif str(issue.fields.reporter)[:-20] in team_jazz:
            counter_jazz = counter_jazz + 1
            team.append('Jazz')
            counter.append(1)
        elif str(issue.fields.reporter)[:-20] in team_blues:
            counter_blues = counter_blues + 1
            team.append('Blues')
            counter.append(1)
        elif str(issue.fields.reporter)[:-20] in team_rock:
            counter_rock = counter_rock + 1
            team.append('Rock')
            counter.append(1)
        else:
            counter_other = counter_other + 1
            team.append('Ungrouped')
            counter.append(1)
    return team, month, counter


def pivot_issues(team, month, counter):
    pd.set_option(  # 设置参数：精度，最大行，最大列，最大显示宽度
        'precision', 1,
        'display.max_rows', 500,
        'display.max_columns', 500,
        'display.width', 1000)
    df0 = pd.DataFrame((list(zip(team, month, counter))))
    df0.columns = ['Team', 'Month', 'Counter']
    pivoted_issue = pd.pivot_table(df0[['Team', 'Month', 'Counter']], values='Counter', index=['Team'], columns=['Month'],
                                   aggfunc='sum', fill_value=0, margins=True)
    return pivoted_issue


def issue_hunter_star(issues):
    star = []
    month = []
    for issue in issues:
        month.append(issue.fields.created[0:7])
        star.append(str(issue.fields.reporter)[:-20])
    return star, month


def pivot_issues_star(star, month, counter):
    pd.set_option(  # 设置参数：精度，最大行，最大列，最大显示宽度
        'precision', 1,
        'display.max_rows', 500,
        'display.max_columns', 500,
        'display.width', 1000)
    current_month = month[0]
    df = pd.DataFrame((list(zip(star, month, counter))))
    df.columns = ['Star', 'Month', 'Counter']
    pivoted_issue_star = pd.pivot_table(df, values=['Counter'], index=['Star'], columns=['Month'], fill_value=0)
    # print(pivoted_issue_star, '\n')
    pivoted_issue_star = pivoted_issue_star.sort_values(('Counter', current_month), ascending=False)  # 按Counter排序
    # print(pivoted_issue_star, '\n')
    return pivoted_issue_star


# logging.basicConfig(level=logging.DEBUG,
#                     filename='ET_statistics.log',
#                     filemode='a',
#                     format='%(asctime)s - %(levelname)s: %(message)s'
#                     )

app = Flask(__name__)


@app.route('/', methods=['GET'])
def web_server():
    return render_template(
        "home_template.html",
    )


@app.route('/FB_Effort', methods=['GET'])
def web_server_effort():
    print("=== current time:", datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S"), "===")
    data = get_data(search_data(jira_filter_ET))
    table = pivot_data(data[0], data[1], data[2], data[3])

    data_jazz = get_data(search_data(jira_filter_ET_Jazz))
    table_jazz = pivot_data_team(data_jazz[4], data_jazz[1], data_jazz[2])

    data_blues = get_data(search_data(jira_filter_ET_Blues))
    table_blues = pivot_data_team(data_blues[4], data_blues[1], data_blues[2])

    data_rock = get_data(search_data(jira_filter_ET_Rock))
    table_rock = pivot_data_team(data_rock[4], data_rock[1], data_rock[2])

    data_shield = get_data(search_data(jira_filter_ET_Shield))
    table_shield = pivot_data_team(data_shield[4], data_shield[1], data_shield[2])

    return render_template(
        "et_template.html",
        total=table[0].to_html(classes="total", header="true", table_id="table"),
        percentage=table[1].to_html(classes="percentage", header="true", table_id="table"),
        total_jazz=table_jazz.to_html(classes="team", header="true", table_id="table"),
        total_blues=table_blues.to_html(classes="team", header="true", table_id="table"),
        total_rock=table_rock.to_html(classes="team", header="true", table_id="table"),
        total_shield=table_shield.to_html(classes="team", header="true", table_id="table")
    )


@app.route('/Issue_Hunter', methods=['GET'])
def web_server_issue():
    print("=== current time:", datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S"), "===")
    jira_list_month = search_data(jira_filter_issues_this_month)
    jira_list_year = search_data(jira_filter_issues_this_year)
    jira_list_all = search_data(jira_filter_issues_all)

    data_year = filter_issues(jira_list_year)
    table_year = pivot_issues(data_year[0], data_year[1], data_year[2])

    date_all = filter_issues(jira_list_all)
    table_all = pivot_issues(date_all[0], date_all[1], date_all[2])

    jira_list_month_ = issue_hunter_star(jira_list_month)
    jira_list_year_ = issue_hunter_star(jira_list_year)

    person_month, counter_month = zip(*Counter(jira_list_month_[0]).most_common(5))
    month_of_current_month = []
    last_month = jira_list_month_[1][0]
    for i in range(0, len(person_month)):
        month_of_current_month.append(last_month)
    # 用Counter函数统计当月提交Jira数量最多的前5名 获取名单、个数和当前月份

    person_year, counter_year = zip(*Counter(jira_list_year_[0]).most_common(5))
    month_of_current_year = []
    last_month_year = jira_list_year_[1][0]
    for i in range(0, len(person_year)):
        month_of_current_year.append(last_month_year)
    # 用Counter函数统计当年提交Jira数量最多的前5名 获取名单、个数和最新月份
    table_star_month = pivot_issues_star(person_month, month_of_current_month, counter_month)
    table_star_year = pivot_issues_star(person_year, month_of_current_year, counter_year)

    return render_template(
        "issues_template.html",
        total_year=table_year.to_html(classes="total", header="true", table_id="table"),
        total_all=table_all.to_html(classes="total", header="true", table_id="table"),
        star_month=table_star_month.to_html(classes="star", header="true", table_id="table"),
        star_year=table_star_year.to_html(classes="star", header="true", table_id="table")
    )


if __name__ == '__main__':
    app.run(host='127.0.0.1', port='80')
    # app.run(host='10.57.209.188')
