# coding=utf-8
from jira import JIRA
import pandas as pd
from datetime import datetime
import pytz
from collections import Counter
import datetime
import configparser
from taf.pdu import pdu
import time
import socket
import ET_ReP_Jira
from flask import Flask, render_template, request
import logging

'''
# lib to install
pip3 install jira
pip3 install pandas
pip3 install flask
pip3 install apscheduler
pip3 install flask_sslify
pip3 install pyopenssl
'''
token = "first token is invalid"

# account = input('>>>>>:').strip()    # 本地调试时注释掉
# password = input('>>>>>:').strip()   # 本地调试时注释掉

jira_server = 'https://jiradc.ext.net.nokia.com'  # jira地址
jira_username = 'h4zhang'  # 用户名，本地调试时，可用明文代替
jira_password = 'Holmes-09'  # 密码，本地调试时，可用明文代替

# jira = JIRA(basic_auth=(jira_username, jira_password), options={'server': jira_server})
jira_filter_ET = '''
    project = FCA_5G_L2L3 AND issuetype in (epic) AND resolution = Unresolved AND status not in (Done, obsolete) AND cf[29790] in (5253, 5254, 5255, 5351, 6261) ORDER BY cf[38693] ASC, key ASC
'''

jira_filter_ET_Jazz = '''project = FCA_5G_L2L3 AND issuetype in (epic) AND resolution = Unresolved AND status not in (Done, obsolete) AND cf[29790] in (5253) ORDER BY cf[38693] ASC, key ASC'''
jira_filter_ET_Blues = '''project = FCA_5G_L2L3 AND issuetype in (epic) AND resolution = Unresolved AND status not in (Done, obsolete) AND cf[29790] in (5254) ORDER BY cf[38693] ASC, key ASC'''
jira_filter_ET_Rock = '''project = FCA_5G_L2L3 AND issuetype in (epic) AND resolution = Unresolved AND status not in (Done, obsolete) AND cf[29790] in (5351) ORDER BY cf[38693] ASC, key ASC'''
jira_filter_ET_Shield = '''project = FCA_5G_L2L3 AND issuetype in (epic) AND resolution = Unresolved AND status not in (Done, obsolete) AND cf[29790] in (6261) ORDER BY cf[38693] ASC, key ASC'''

jira_filter_issues_all = '''project = 68296 AND reporter in (membersOf(I_MN_RAN_L3_SW_1_CN_ET)) AND created > startOfYear() and issuetype = Bug AND status != CNN ORDER BY key DESC'''
jira_filter_issues_this_year = '''project = 68296 AND reporter in (membersOf(I_MN_RAN_L3_SW_1_CN_ET)) AND created > startOfYear() and issuetype = Bug AND status != CNN ORDER BY key DESC'''
jira_filter_issues_this_month = '''project = 68296 AND reporter in (membersOf(I_MN_RAN_L3_SW_1_CN_ET)) AND created >= startOfMonth() and issuetype = Bug AND status != CNN ORDER BY key DESC'''

jira_filter_long_open_issue = '''project = 68296 AND reporter in (membersOf(I_MN_RAN_L3_SW_1_CN_ET)) AND status not in (Done, CNN, FNR, "Transferred out") ORDER BY created ASC, key DESC'''


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


def convert_data(string):  # 转换格式 xxh转换为数字
    if string is None:
        return 0
    else:
        return float(string.replace(',', '').replace('h', ''))


def get_data(issues):  # 处理数据
    team, end_fb, remaining_effort, remaining_effort_percentage, original_effort = [], [], [], [], []
    feature_blues, feature_jazz, feature_rock, feature_shield = [], [], [], []
    remaining_effort_blues, remaining_effort_jazz, remaining_effort_rock, remaining_effort_shield = [], [], [], []
    end_fb_blues, end_fb_jazz, end_fb_rock, end_fb_shield = [], [], [], []
    squad_jazz_hc = 7
    squad_blues_hc = 7
    squad_rock_hc = 7
    squad_shield_hc = 7
    squad_c_hc = 8
    squad_jazz_cap = squad_jazz_hc * 60 - 20 - 15 - 15
    squad_blues_cap = squad_blues_hc * 60 - 20 - 15 - 15
    squad_rock_cap = squad_rock_hc * 60 - 20 - 15 - 15
    squad_shield_cap = squad_shield_hc * 60 - 20 - 15
    squad_c_cap = squad_c_hc * 60 - 20 - 15

    squad_name = ["Jazz", "Blues", "Rock", "Shield", "Squad C"]
    squad_hc = [squad_jazz_hc, squad_blues_hc, squad_rock_hc, squad_shield_hc, squad_c_hc]
    squad_cap = [squad_jazz_cap, squad_blues_cap, squad_rock_cap, squad_shield_cap, squad_c_cap]

    for issue in issues:
        end_fb.append(issue.fields.customfield_38693)
        converted_data_remain = convert_data(issue.fields.customfield_39192)
        remaining_effort.append(converted_data_remain)
        converted_data_origin = convert_data(issue.fields.customfield_39191)
        original_effort.append(converted_data_origin)
        if issue.fields.customfield_29790 == '5253':
            team.append('L3_5GL3ET_HZH_Jazz')
            remaining_effort_percentage.append(converted_data_remain / squad_jazz_cap)
            feature_jazz.append(issue.fields.customfield_37381)
            remaining_effort_jazz.append(converted_data_remain)
            end_fb_jazz.append(issue.fields.customfield_38693)
        elif issue.fields.customfield_29790 == '5254':
            team.append('L3_5GL3ET_HZH_Blues')
            remaining_effort_percentage.append(converted_data_remain / squad_blues_cap)
            feature_blues.append(issue.fields.customfield_37381)
            remaining_effort_blues.append(converted_data_remain)
            end_fb_blues.append(issue.fields.customfield_38693)
        elif issue.fields.customfield_29790 == '5351':
            team.append('L3_5GL3ET_HZH_Rock')
            remaining_effort_percentage.append(converted_data_remain / squad_rock_cap)
            feature_rock.append(issue.fields.customfield_37381)
            remaining_effort_rock.append(converted_data_remain)
            end_fb_rock.append(issue.fields.customfield_38693)
        elif issue.fields.customfield_29790 == '6261':
            team.append('L3_5GL3ET_HZH_SHIELD')
            remaining_effort_percentage.append(converted_data_remain / squad_shield_cap)
            feature_shield.append(issue.fields.customfield_37381)
            remaining_effort_shield.append(converted_data_remain)
            end_fb_shield.append(issue.fields.customfield_38693)
        elif issue.fields.customfield_29790 == '5255':
            team.append('L3_5GL3ET_HZH_Squad C')
            remaining_effort_percentage.append(converted_data_remain / squad_c_cap)
    return team, end_fb, remaining_effort, remaining_effort_percentage, original_effort, \
           feature_blues, feature_jazz, feature_rock, feature_shield, \
           remaining_effort_blues, remaining_effort_jazz, remaining_effort_rock, remaining_effort_shield, \
           end_fb_blues, end_fb_jazz, end_fb_rock, end_fb_shield, squad_name, squad_hc, squad_cap


def pivot_data_sum(team, end_fb, remaining_effort):  # 汇总数据
    pd.set_option(  # 设置参数：精度，最大行，最大列，最大显示宽度
        'precision', 1,
        'display.max_rows', 500,
        'display.max_columns', 500,
        'display.width', 1000)
    df0 = pd.DataFrame((list(zip(team, end_fb, remaining_effort))))
    df0.columns = ['Team', 'FB', 'Remaining EE']
    pivoted_fb_effort = pd.pivot_table(df0[['Team', 'FB', 'Remaining EE']], values='Remaining EE',
                                       index=['Team'], columns=['FB'], aggfunc='sum', fill_value=0)
    return pivoted_fb_effort


def pivot_data_percentage(team, end_fb, remaining_effort_percentage):  # 汇总数据
    pd.set_option(  # 设置参数：精度，最大行，最大列，最大显示宽度
        'precision', 1,
        'display.max_rows', 500,
        'display.max_columns', 500,
        'display.width', 1000)
    df = pd.DataFrame((list(zip(team, end_fb, remaining_effort_percentage))))
    df.columns = ['Team', 'FB', 'Percentage']
    pivoted_fb_effort_percentage = pd.pivot_table(df[['Team', 'FB', 'Percentage']], values='Percentage',
                                                  index=['Team'], columns=['FB'], aggfunc='sum', fill_value=0) \
        .applymap(lambda x: "{0:.1f}%".format(100 * x))  # show as percentage
    return pivoted_fb_effort_percentage


def pivot_squad(name, hc, cap):
    pd.set_option(  # 设置参数：精度，最大行，最大列，最大显示宽度
        'precision', 1,
        'display.max_rows', 500,
        'display.max_columns', 500,
        'display.width', 1000)
    df = pd.DataFrame((list(zip(name, hc, cap))))
    df.columns = ["Team Name", "Team HC", "Team Capacity"]
    df.index = df.index + 1
    return df


def pivot_data_team(feature, end_fb, remaining_effort):
    pd.set_option(  # 设置参数：精度，最大行，最大列，最大显示宽度
        'precision', 1,
        'display.max_rows', 500,
        'display.max_columns', 500,
        'display.width', 1000)
    df0 = pd.DataFrame((list(zip(feature, end_fb, remaining_effort))))
    df0.columns = ['Feature', 'FB', 'Remaining EE']
    pivoted_fb_effort_team = pd.pivot_table(df0[['Feature', 'FB', 'Remaining EE']], values='Remaining EE',
                                            index=['Feature'], columns=['FB'], aggfunc='sum', fill_value=0,
                                            margins=True)
    return pivoted_fb_effort_team


def filter_issues(issues):
    team_shield = ['Damon Lei', 'Jun 15. Zhang', 'Jiangping Cao', 'Ping 3. Li', 'Susana Yan', 'Alex 2. Wang',
                   'Jun 3. Ye']
    team_jazz = ['Jolin Fan', 'Dandan Chen', 'Delun Li', 'Lingyan Zhou', 'Zheng Tang', 'Lijun J. Jia',
                 'Chunjian Yang', 'Jean Jing']
    team_blues = ['Nanxiao Ge', 'Sherry Zhang', 'Yige G. Zhang', 'Ruifang Zhu', 'Hao 6. Zhang', 'Ha Zheng',
                  'Zora Wang', 'Tingjian Mao']
    team_rock = ['Lena Zhuo', 'Jiadan Wu', 'Christine Chen', 'Xiaowen Xu', 'Liupei Fang',
                 'Jing Ye', 'Jia Pan']
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
        if str(issue.fields.reporter)[:-6] in team_shield:
            counter_shield = counter_shield + 1
            team.append('Shield')
            counter.append(1)
        elif str(issue.fields.reporter)[:-6] in team_jazz:
            counter_jazz = counter_jazz + 1
            team.append('Jazz')
            counter.append(1)
        elif str(issue.fields.reporter)[:-6] in team_blues:
            counter_blues = counter_blues + 1
            team.append('Blues')
            counter.append(1)
        elif str(issue.fields.reporter)[:-6] in team_rock:
            counter_rock = counter_rock + 1
            team.append('Rock')
            counter.append(1)
        else:
            # print("Ungrouped list:", str(issue.fields.reporter)[:-6])
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
    pivoted_issue = pd.pivot_table(df0[['Team', 'Month', 'Counter']], values='Counter', index=['Team'],
                                   columns=['Month'],
                                   aggfunc='sum', fill_value=0, margins=True)
    return pivoted_issue


def issue_hunter_star(issues):
    star = []
    month = []
    for issue in issues:
        month.append(issue.fields.created[0:7])
        star.append(str(issue.fields.reporter)[:-6])
    return star, month


def pivot_issues_star(star, month, counter):
    pd.set_option(  # 设置参数：精度，最大行，最大列，最大显示宽度
        'precision', 1,
        'display.max_rows', 500,
        'display.max_columns', 500,
        'display.width', 1000)
    if len(month) == 0:  # 如果当月没有Jira时的处理
        # current_month = datetime.datetime.now().strftime("%Y-%m")  # 配置为显示成当前月份会报错
        current_month = 0
        star_result = [0]
        month_result = [0]
        counter_result = [0]
    else:
        current_month = month[0]
        star_result = star
        month_result = month
        counter_result = counter
    print("current_month", current_month, type(current_month))
    df = pd.DataFrame((list(zip(star_result, month_result, counter_result))))
    df.columns = ['Star', 'Month', 'Counter']
    pivoted_issue_star = pd.pivot_table(df, values=['Counter'], index=['Star'], columns=['Month'], fill_value=0)
    # print(pivoted_issue_star, '\n')
    pivoted_issue_star = pivoted_issue_star.sort_values(('Counter', current_month), ascending=False)  # 按Counter排序
    # print(pivoted_issue_star, '\n')
    return pivoted_issue_star


def find_long_open_issue(issues):
    feature, split_feature = [], []
    reporter, split_reporter = [], []
    created_date, split_created_date = [], []
    status, split_status = [], []
    open_day, split_open_day = [], []
    current_day = datetime.datetime.now()

    for issue in issues:
        feature.append(issue.fields.customfield_37381)
        reporter.append(str(issue.fields.reporter)[:-6])
        created_date.append(issue.fields.created[:-18])
        status.append(issue.fields.status)

    for day in created_date:
        year_month_date = day.split('-')
        # print(year_month_date)
        report_day = datetime.datetime(int(year_month_date[0]), int(year_month_date[1]), int(year_month_date[2]))
        # print(report_day)
        duration = (current_day - report_day).days
        # print(duration)
        if duration >= 7:
            open_day.append(duration)

    for i in range(0, len(open_day)):
        split_feature.append(feature[i])
        split_reporter.append(reporter[i])
        split_created_date.append(created_date[i])
        split_status.append(status[i])
        split_open_day.append(open_day[i])
    return split_feature, split_reporter, split_status, split_created_date, split_open_day


def pivot_long_open_issue(feature, reporter, status, created_date, open_day):
    pd.set_option(  # 设置参数：精度，最大行，最大列，最大显示宽度
        'precision', 1,
        'display.max_rows', 500,
        'display.max_columns', 500,
        'display.width', 1000)
    df = pd.DataFrame((list(zip(feature, reporter, status, created_date, open_day))))
    df.columns = ["Feature", "Reporter", "Status", "Created Date", "Open Day"]
    df.index = df.index + 1
    # print("print_df", '\n', df)
    # print(df.dtypes)
    return df


def pivot_tl_status(tl_info, tl_ip, tl_port, tl_port_num, tl_power_off_on_flag, tl_power_off_date, tl_power_off_time, tl_power_on_time, tl_owner,
                    tl_power_off_on_status):
    pd.set_option(  # 设置参数：精度，最大行，最大列，最大显示宽度
        'precision', 1,
        'display.max_rows', 500,
        'display.max_columns', 500,
        'display.width', 1000)
    df = pd.DataFrame((list(zip(tl_info, tl_ip, tl_port, tl_port_num, tl_power_off_on_flag, tl_power_off_date, tl_power_off_time, tl_power_on_time, tl_owner,
                                tl_power_off_on_status))))
    df.columns = ["TL Info", "PB IP", "PB PORT", "PB PORT NUM", "Power Off/On Flag", "Power Off/On Date", "Power Off Time", "Power On Time", "TL Owner",
                  "Power Off/On Status"]
    df.index = df.index + 1
    # print("print_df", '\n', df)
    # print(df.dtypes)
    return df


tl_info = []
tl_ip = []
tl_port = []
tl_port_num = []
tl_power_off_on_flag = []
tl_power_off_date = []
tl_power_off_time = []
tl_power_on_time = []
tl_owner = []
tl_power_off_on_status = []


def query_pdu(pdu_ip, pdu_port, port_num, pdu_alias='query'):
    ppdu = pdu()
    if pdu_port == 5000:
        pdu_type = 'HBTE'
    elif pdu_port == 4001:
        pdu_type = 'FACOM'
    elif pdu_port == 3000:
        pdu_type = 'TOPYOUNG'
    else:
        power_status = 'ERROR PORT'
        return power_status
    if port_num not in ['1', '2', '3', '4', '5', '6', '7', '8']:
        power_status = 'ERROR PORT NUM'
        return power_status
    # print(pdu_ip, pdu_type)
    try:
        ppdu.setup_pdu(model=pdu_type, host=pdu_ip, port=pdu_port, alias=pdu_alias)
        power_status = ppdu.get_port_status(port=port_num, pdu_device=pdu_alias)
    except socket.timeout:
        power_status = 'Timeout'
        return power_status
    except Exception as e:
        # print('ERROR:', e)
        power_status = e
        return power_status
    else:
        return power_status


def get_testline_info():
    file = "C://Holmes//code//autopoweroffon//testline_info.ini"
    conf = configparser.ConfigParser()
    conf.read(file, encoding="utf-8")
    tl_info.clear()
    tl_ip.clear()
    tl_port.clear()
    tl_port_num.clear()
    tl_power_off_on_flag.clear()
    tl_power_off_date.clear()
    tl_power_off_time.clear()
    tl_power_on_time.clear()
    tl_owner.clear()
    tl_power_off_on_status.clear()
    sections = conf.sections()
    tic = time.perf_counter()
    for i in range(len(sections)):  # len(sections) = total testline num
        items = conf.items(sections[i])
        tl_info.append(sections[i])
        tl_ip.append(items[0][1])
        tl_port.append(int(items[1][1]))
        tl_port_num.append(items[2][1])
        tl_power_off_on_flag.append(items[3][1])
        tl_power_off_date.append(items[4][1])
        tl_power_off_time.append(items[5][1])
        tl_power_on_time.append(items[6][1])
        tl_owner.append(items[7][1])
        tl_power_off_on_status.append(query_pdu(tl_ip[i], tl_port[i], tl_port_num[i]))
    toc = time.perf_counter()
    print(f"time cost: {toc - tic:0.2f} seconds")
    # print(tl_power_off_on_status)
    return tl_info, tl_ip, tl_port, tl_port_num, tl_power_off_on_flag, tl_power_off_date, tl_power_off_time, tl_power_on_time, tl_owner, tl_power_off_on_status


logging.basicConfig(level=logging.INFO,
                    filename='ET_statistics.log',
                    filemode='a',
                    format='%(asctime)s - %(levelname)s: %(message)s'
                    )

app = Flask(__name__)


@app.route('/', methods=['GET'])
def web_server():
    return render_template(
        "home_template.html",
    )


@app.route('/FB_Effort', methods=['GET'])
def web_server_effort():
    print("=== current time:", datetime.datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S"), "===")
    data = get_data(search_data(jira_filter_ET))
    # get_data return:
    # team, end_fb, remaining_effort, remaining_effort_percentage, original_effort, \ 01234
    # feature_blues, feature_jazz, feature_rock, feature_shield, \ 5678
    # remaining_effort_blues, remaining_effort_jazz, remaining_effort_rock, remaining_effort_shield, \ 9 10 11 12
    # end_fb_blues, end_fb_jazz, end_fb_rock, end_fb_shield \ 13 14 15 16
    # squad_name, squad_hc, squad_cap \ 17 18 19
    dic = Counter(data[1])
    length = dic[data[1][0]]  # 计算第一个FB有几个数据
    origin = '0rigin_' + data[1][0]

    # 在原始数据中插入数据用于展示 Origin Effort 插入的个数=第一个FB数据的个数
    new_team = data[0][:length] + data[0]
    new_fb = [origin] * length + data[1]
    new_ee = data[4][:length] + data[2]

    # 总effort 和 effort百分比
    table_sum = pivot_data_sum(new_team, new_fb, new_ee)
    table_percentage = pivot_data_percentage(data[0], data[1], data[3])
    # Team Info
    table_squad = pivot_squad(data[17], data[18], data[19])
    # 每个Team每个FB的feature和effort
    table_blues = pivot_data_team(data[5], data[13], data[9])
    table_jazz = pivot_data_team(data[6], data[14], data[10])
    table_rock = pivot_data_team(data[7], data[15], data[11])
    table_shield = pivot_data_team(data[8], data[16], data[12])

    return render_template(
        "effort_template.html",
        total=table_sum.to_html(classes="total", header="true", table_id="table"),
        percentage=table_percentage.to_html(classes="percentage", header="true", table_id="table"),
        squad=table_squad.to_html(classes="team", header="true", table_id="table"),
        total_jazz=table_jazz.to_html(classes="team", header="true", table_id="table"),
        total_blues=table_blues.to_html(classes="team", header="true", table_id="table"),
        total_rock=table_rock.to_html(classes="team", header="true", table_id="table"),
        total_shield=table_shield.to_html(classes="team", header="true", table_id="table")
    )


@app.route('/Issue_Hunter', methods=['GET'])
def web_server_issue():
    print("=== current time:", datetime.datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S"), "===")
    jira_list_month = search_data(jira_filter_issues_this_month)
    jira_list_year = search_data(jira_filter_issues_this_year)
    jira_list_all = search_data(jira_filter_issues_all)

    data_year = filter_issues(jira_list_year)

    if len(data_year[0]) == 0:
        return render_template("null_template.html")
    else:
        # 今年Jira Issue统计
        table_year = pivot_issues(data_year[0], data_year[1], data_year[2])
        # 所有Jira Issue统计
        date_all = filter_issues(jira_list_all)
        table_all = pivot_issues(date_all[0], date_all[1], date_all[2])
        # 当月Jira Issue Hunting Star
        jira_list_month_result = issue_hunter_star(jira_list_month)
        # 今年Jira Issue Hunting Star
        jira_list_year_result = issue_hunter_star(jira_list_year)

        if Counter(jira_list_month_result[0]):  # 当月统计非0时
            person_month, counter_month = zip(*Counter(jira_list_month_result[0]).most_common(5))  # 取前5
            last_month = jira_list_month_result[1][0]
        else:  # 当月统计为0时
            person_month, counter_month = [], []
            last_month = 0

        result_of_current_month = []
        if len(person_month) == 0:
            result_of_current_month = []
        else:
            for i in range(0, len(person_month)):
                result_of_current_month.append(last_month)
        # 用Counter函数统计当月提交Jira数量最多的前5名 获取名单、个数和当前月份

        person_year, counter_year = zip(*Counter(jira_list_year_result[0]).most_common(5))
        result_of_current_year = []
        last_month_year = jira_list_year_result[1][0]
        for i in range(0, len(person_year)):
            result_of_current_year.append(last_month_year)
        # 用Counter函数统计当年提交Jira数量最多的前5名 获取名单、个数和最新月份

        table_star_month = pivot_issues_star(person_month, result_of_current_month, counter_month)
        table_star_year = pivot_issues_star(person_year, result_of_current_year, counter_year)
        # print("star_of_the_year:", '\n', table_star_year)

        return render_template(
            "issues_template.html",
            total_year=table_year.to_html(classes="total", header="true", table_id="table"),
            total_all=table_all.to_html(classes="total", header="true", table_id="table"),
            star_month=table_star_month.to_html(classes="star", header="true", table_id="table"),
            star_year=table_star_year.to_html(classes="star", header="true", table_id="table")
        )


@app.route('/Long_Open_Issue', methods=['GET'])
def web_server_issue_long_open():
    jira_long_open_issue = search_data(jira_filter_long_open_issue)
    data = find_long_open_issue(jira_long_open_issue)
    table = pivot_long_open_issue(data[0], data[1], data[2], data[3], data[4])
    # print(table.values[0][1])
    return render_template(
        "long_open_issues_template.html",
        total=table.to_html(classes="total", header="true", table_id="table")
    )


@app.route('/TL_status', methods=['GET'])
def web_server_tl_status():
    data = get_testline_info()
    table = pivot_tl_status(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9])
    return render_template(
        "testline_status_template.html",
        total=table.to_html(classes="total", header="true", table_id="table")
    )


@app.route("/feature_info")
def index():
    return render_template("et_rep_jira.html")


@app.route("/feature_info", methods=["POST"])
def process_input():
    global token
    if ET_ReP_Jira.validate_token(token):
        logging.info("<--0.1 token is valid-->")
    else:  # 如果token失效，就重新获取
        token = ET_ReP_Jira.get_token()
        logging.info("<--0.2 get new token-->")
    logging.info("<--1.0 token validated-->")
    feature = request.form.get("feature_id")  # get input from web
    logging.info("<--2.0 get feature id done-->")
    source_data = ET_ReP_Jira.get_result(feature, token)
    logging.info("<--4.O get source data done-->")
    # source data order: backlog_id, end_fb, label, case_name, qc_status
    data = {
        'backlog_id': source_data[0],
        'end_fb': source_data[1],
        'label': source_data[2],
        'case_name': source_data[3],
        'qc_status': source_data[4]
    }
    total_label = ET_ReP_Jira.summary(source_data[0], source_data[2])
    # print("total label", total_label)
    total_case = len(source_data[2])
    # print("total case", total_case)
    df = pd.DataFrame(data)
    # 表格数据由df传入，数值则直接传入html
    return render_template('et_rep_jira.html', data=df.to_dict('records'), total_label=total_label, total_case=total_case)


if __name__ == '__main__':
    '''http'''
    app.run(debug=True, host='127.0.0.1', port=8080)
    # need to update in home_template.html

    '''https -- private key'''
    # sslify = SSLify(app)
    # app.run(host='10.57.195.35', port=8443, debug=True, ssl_context=('./SSL/ca/ca.crt', './SSL/ca/ca.key'))

    '''https -- default key'''
    # app.run(host='10.57.195.35', port=8080, debug=True, ssl_context='adhoc')
