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
import ET_Feature_Report
from flask import Flask, render_template, request
import logging
import re
from flask import redirect, url_for


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


# no need to convert after parameter change -- 230926
def convert_data(string):  # 转换格式 xxh转换为数字
    if string is None:
        return 0
    elif isinstance(string, str):  # 检查string是否为字符串类型
        return float(string.replace(',', '').replace('h', ''))
    else:
        return string  # 如果不是字符串，直接返回


def get_data(issues):  # 处理数据
    team, end_fb, remaining_effort, remaining_effort_percentage, original_effort = [], [], [], [], []
    feature_blues, feature_jazz, feature_rock, feature_shield = [], [], [], []
    remaining_effort_blues, remaining_effort_jazz, remaining_effort_rock, remaining_effort_shield = [], [], [], []
    end_fb_blues, end_fb_jazz, end_fb_rock, end_fb_shield = [], [], [], []
    squad_jazz_hc = 6
    squad_blues_hc = 7
    squad_rock_hc = 6
    squad_shield_hc = 6
    squad_c_hc = 8
    squad_jazz_cap = squad_jazz_hc * 60 - 20 - 15 - 15
    squad_blues_cap = squad_blues_hc * 60 - 20 - 15 - 15
    squad_rock_cap = squad_rock_hc * 60 - 20 - 15 - 15
    squad_shield_cap = squad_shield_hc * 60 - 20 - 15
    squad_c_cap = squad_c_hc * 60 - 20 - 15

    squad_name = ["Jazz", "Blues", "Rock", "Shield", "HZ64_SG2"]
    squad_hc = [squad_jazz_hc, squad_blues_hc, squad_rock_hc, squad_shield_hc, squad_c_hc]
    squad_cap = [squad_jazz_cap, squad_blues_cap, squad_rock_cap, squad_shield_cap, squad_c_cap]

    for issue in issues:
        end_fb.append(issue.fields.customfield_38693)
        data_remain = issue.fields.customfield_43291    # from time remaining[39192] change to time remaining(h)[43291] -- 230926
        remaining_effort.append(data_remain)
        data_origin = issue.fields.customfield_43292    # from original esitimate[39191] change to original esitimate(h)[43292] -- 230926
        original_effort.append(data_origin)

        # get team info should use: issue.fields.customfield_29790.name -- 23/10/08

        if issue.fields.customfield_29790.name == 'L3_5GL3ET_HZH_Jazz':
            team.append('L3_5GL3ET_HZH_Jazz')
            remaining_effort_percentage.append(data_remain / squad_jazz_cap)
            feature_jazz.append(issue.fields.customfield_37381)
            remaining_effort_jazz.append(data_remain)
            end_fb_jazz.append(issue.fields.customfield_38693)
        elif issue.fields.customfield_29790.name == 'L3_5GL3ET_HZH_Blues':
            team.append('L3_5GL3ET_HZH_Blues')
            remaining_effort_percentage.append(data_remain / squad_blues_cap)
            feature_blues.append(issue.fields.customfield_37381)
            remaining_effort_blues.append(data_remain)
            end_fb_blues.append(issue.fields.customfield_38693)
        elif issue.fields.customfield_29790.name == 'L3_5GL3ET_HZH_Rock':
            team.append('L3_5GL3ET_HZH_Rock')
            remaining_effort_percentage.append(data_remain / squad_rock_cap)
            feature_rock.append(issue.fields.customfield_37381)
            remaining_effort_rock.append(data_remain)
            end_fb_rock.append(issue.fields.customfield_38693)
        elif issue.fields.customfield_29790.name == 'L3_5GL3ET_HZH_SHIELD':
            team.append('L3_5GL3ET_HZH_SHIELD')
            remaining_effort_percentage.append(data_remain / squad_shield_cap)
            feature_shield.append(issue.fields.customfield_37381)
            remaining_effort_shield.append(data_remain)
            end_fb_shield.append(issue.fields.customfield_38693)
        elif issue.fields.customfield_29790.name == 'L3_5G L3 ET_HZ64_SG2':
            team.append('L3_5G L3 ET_HZ64_SG2')
            remaining_effort_percentage.append(data_remain / squad_c_cap)

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
def feature_info_default():
    return render_template("et_rep_jira.html")


@app.route('/feature_info', methods=['POST'])
def feature_info():
    feature = request.form.get("feature_id").strip()  # 从网页输入获得feature，并去掉前后的空格
    if feature:
        return redirect(url_for('feature_info_with_id', feature_name=feature))  # 将feature作为参数传给feature_report_with_id，可以做为url的一部分
    else:
        logging.info("[1.0] <--query feature id is [null]-->")
        return render_template("et_rep_jira.html")


@app.route('/feature_info/<feature_name>', methods=['GET'])
def feature_info_with_id(feature_name):  # feature_name 可以来自手动输入的url，也可以来自网页上输入的 feature id
    global token
    if ET_ReP_Jira.validate_token(token):
        logging.info("[0.1] <--token is valid-->")
    else:  # 如果token失效，就重新获取
        token = ET_ReP_Jira.get_token()
        logging.info("[0.1] <--get new token-->")
    logging.info("[0.2] <--token validated-->")
    feature = feature_name.strip()
    if feature:
        logging.info(f"[1.0] <--query [{feature}] start-->")
    else:
        logging.info("[1.0] <--query feature id is [null]-->")
    url_case_info = "https://rep-portal.ext.net.nokia.com/api/qc-beta/instances/report/?fields=id%2Cm_path%2Ctest_set__name%2Cbacklog_id%2Cname%2Curl%2Cstatus%2Cstatus_color%2Cfault_report_id_link%2Ccomment%2Csw_build%2Cres_tester%2Ctest_entity%2Cfunction_area%2Cca%2Corganization%2Crelease%2Cfeature%2Crequirement%2Clast_testrun__timestamp&limit=200&m_path__pos_neg=New_Features%5CRAN_L3_SW_CN_1&ordering=name&test_set__name__pos_neg_empty_str="
    url_case_info_feature = url_case_info + feature
    source_data = ET_ReP_Jira.get_result(url_case_info_feature, token)
    logging.info(f"[2.0] <--query [{feature}] case status done-->")
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
    # 按 QC status 统计case个数，除去 N/A case 个数
    total_case = sum(1 for item in source_data[4] if item != "N/A")
    # print("total case", total_case)
    df = pd.DataFrame(data)
    # 表格数据由df传入，数值则直接传入html
    return render_template('et_rep_jira.html', data=df.to_dict('records'), total_label=total_label, total_case=total_case)


@app.route("/Feature_Report")
def feature_report_default():
    return render_template("et_feature_report.html")


@app.route('/Feature_Report', methods=['POST'])
def feature_report():
    feature = request.form.get("feature_id").strip()  # 从网页输入获得feature，并去掉前后的空格
    if feature:
        return redirect(url_for('feature_report_with_id', feature_name=feature))  # 将feature作为参数传给feature_report_with_id，可以做为url的一部分
    else:
        logging.info("[1.0] <--query feature id is [null]-->")
        return render_template("et_feature_report.html")


@app.route('/Feature_Report/<feature_name>', methods=['GET'])
def feature_report_with_id(feature_name):  # feature_name 可以来自手动输入的url，也可以来自网页上输入的 feature id
    global token
    if ET_ReP_Jira.validate_token(token):
        logging.info("[0.1] <--token is valid-->")
    else:  # 如果token失效，就重新获取
        token = ET_ReP_Jira.get_token()
        logging.info("[0.1] <--get new token-->")
    logging.info("[0.2] <--token validated-->")
    feature = feature_name.strip()
    # 判断输入的值 非空和非空格时的处理
    if feature:
        logging.info(f"[1.0] <--query [{feature}] start-->")
        url_case = "https://rep-portal.ext.net.nokia.com/api/qc-beta/instances/report/?fields=id%2Cm_path%2Ctest_set__name%2Cbacklog_id%2Cname%2Curl%2Cstatus%2Cstatus_color%2Cfault_report_id_link%2Ccomment%2Csw_build%2Cres_tester%2Ctest_entity%2Cfunction_area%2Cca%2Corganization%2Crelease%2Cfeature%2Crequirement%2Clast_testrun__timestamp&limit=200&m_path__pos_neg=New_Features%5CRAN_L3_SW_CN_1&ordering=name&test_set__name__pos_neg_empty_str="
        url_case_feature = url_case + feature
        url_pr = "https://rep-portal.ext.net.nokia.com/api/pronto/report/?fields=pronto_id,pronto_tool_url,title,rd_info,state,author,author_group,group_in_charge_name,fault_analysis_responsible_person,reported_date&limit=200&ordering=-reported_date&feature__pos_neg="
        url_pr_feature = url_pr + feature
        jql = 'project = 68296 AND type = Bug AND "Feature ID" ~ "{}*" ORDER BY key DESC'.format(feature)

        # 第一个表格中的数据，case result统计
        case_data = ET_Feature_Report.get_case_info_from_rep(feature, url_case_feature, token)
        # return backlog_id, sub_feature, case_name, qc_status and as input to pivot_feature_report_qc_status(sub_feature, qc_status, case)
        case_status = ET_Feature_Report.pivot_feature_report_qc_status(case_data[1], case_data[3], case_data[2])
        logging.info(f"[2.0] <--query [{feature}] case status done-->")

        # 第二个表格中的数据，pr 统计
        pr_data = ET_Feature_Report.get_pr_info_from_rep(url_pr_feature, token)
            # pr_id, pr_link, gic, fault_analysis_person, author, author_group, state, title, reported_date, rd_info
        data_for_pr = {
            'pr_id': pr_data[0],
            'pr_link': pr_data[1],
            'gic': pr_data[2],
            'fault_analysis_person': pr_data[3],
            'author': pr_data[4],
            'author_group': pr_data[5],
            'state': pr_data[6],
            'title': pr_data[7],
            'reported_date': pr_data[8],
            'rd_info': pr_data[9]
            }
        df_pr = pd.DataFrame(data_for_pr)
        logging.info(f"[3.0] <--query [{feature}] pr status done-->")

        # 第三个表格中的数据，jira 统计
        jira_data = ET_Feature_Report.get_jira_issue_from_jira(jql)
            # jira_id, feature_id, title, assignee, reporter, created, status, comment
        data_for_jira = {
            'jira_id': jira_data[0],
            'feature_id': jira_data[1],
            'title': jira_data[2],
            'assignee': jira_data[3],
            'reporter': jira_data[4],
            'created': jira_data[5],
            'status': jira_data[6],
            'comment': jira_data[7],
            'jira_link': jira_data[8]
             }
        df_jira = pd.DataFrame(data_for_jira)
        logging.info(f"[4.0] <--query [{feature}] jira status done-->")

        if not case_status.empty:  # 输入非空，且查询结果也非空时，正常返回所有表格数据
            return render_template(
                "et_feature_report.html",
                table_qc_status=case_status.to_html(classes="total", header="true", table_id="table"),
                data_pr=df_pr.to_dict('records'),
                data_jira=df_jira.to_dict('records'),
                feature_id=feature)
        else:  # 输入非空，但case_status查询结果为空时，table_qc_status无返回值
            # logging.info("[5.0] <--query case status is [null]-->")
            return render_template(
                "et_feature_report.html",
                # table_qc_status=case_status.to_html(classes="total", header="true", table_id="table"),
                data_pr=df_pr.to_dict('records'),
                data_jira=df_jira.to_dict('records'),
                feature_id=feature)
    else:  # 输入为空或空格时，返回默认表格
        logging.info("[1.0] <--query feature id is [null]-->")
        return render_template("et_feature_report.html")


@app.route('/send_content', methods=['POST'])
def send_content():
    mail_sender = ET_Feature_Report.MailSender()
    try:
        # 获取 HTML 内容
        data = request.get_json()
        html_content = data['htmlContent']

        # 设置收件人、主题和 HTML 内容
        receiver = ['hao.6.zhang@nokia-sbell.com']
        subject = 'HTML Email'
        content = html_content

        mail_sender.send_mail(receiver, subject, content)

        return '', 200
    except Exception as e:
        logging.info(f"ERROR: {e}")
        # print('ERROR:', e)
        return '', 500


if __name__ == '__main__':
    '''http'''
    app.run(debug=True, host='127.0.0.1', port=8080)
    # need to update in home_template.html

    '''https -- private key'''
    # sslify = SSLify(app)
    # app.run(host='10.57.195.35', port=8443, debug=True, ssl_context=('./SSL/ca/ca.crt', './SSL/ca/ca.key'))

    '''https -- default key'''
    # app.run(host='10.57.195.35', port=8080, debug=True, ssl_context='adhoc')
