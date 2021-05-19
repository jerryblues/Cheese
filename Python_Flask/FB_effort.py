# coding=utf-8
from jira import JIRA
import pandas as pd
from flask import Flask, render_template
from datetime import datetime
import pytz
import logging

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


def search_data(jql, max_results=1000):  # 抓取数据
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
    team, end_fb, time_remaining, time_remaining_percentage = [], [], [], []
    squad_jazz_hc = 8
    squad_blues_hc = 7
    squad_rock_hc = 7
    squad_shield_hc = 7
    squad_c_hc = 8
    squad_jazz_cap = squad_jazz_hc * 120
    squad_blues_cap = squad_blues_hc * 120
    squad_rock_cap = squad_rock_hc * 120
    squad_shield_cap = squad_shield_hc * 120
    squad_c_cap = squad_c_hc * 120

    for issue in issues:
        end_fb.append(issue.fields.customfield_38693)
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
    return team, end_fb, time_remaining, time_remaining_percentage


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
    # print(pivoted_fb_effort_percentage, '\n')
    return pivoted_fb_effort, pivoted_fb_effort_percentage


logging.basicConfig(level=logging.DEBUG,
                    filename='FB_effort.log',
                    filemode='a',
                    format='%(asctime)s - %(levelname)s: %(message)s'
                    )

app = Flask(__name__)


@app.route('/ET', methods=['GET'])
def web_server():
    print("=== current time:", datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S"), "===")
    data = get_data(search_data(jira_filter_ET))
    table = pivot_data(data[0], data[1], data[2], data[3])
    return render_template(
        "ET_template.html",
        total=table[0].to_html(classes="total", header="true", table_id="table"),
        percentage=table[1].to_html(classes="percentage", header="true", table_id="table")
    )


if __name__ == '__main__':
    app.run(host='127.0.0.1', port='80')
    # app.run(host='10.57.209.188')
