# coding=utf-8
from jira import JIRA
from flask import Flask, render_template
import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import logging


'''
# lib to install
pip3 install jira
pip3 install pandas
pip3 install flask
pip3 install apscheduler
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


def searchIssues(jql, max_results=1000):
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


jira_filter = '''
    project = FCA_5G_L2L3 AND issuetype in (epic) AND resolution = Unresolved AND status not in (Done, obsolete) AND cf[29790] in (5253, 5254, 5255, 5351, 6261) ORDER BY cf[38693] ASC, key ASC
'''
# issues = searchIssues(jira_filter)


def job():
    print("====== current time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "======")
    issues = searchIssues(jira_filter)
    # print(issues)

    # 2.处理数据
    team = []
    end_fb = []
    # original_estimate = []
    time_remaining = []
    time_remaining_percentage = []
    squad_a_cap = 9.6
    squad_b_cap = 9.6
    squad_rock_cap = 9.6
    squad_shield_cap = 8.4
    squad_c_cap = 9.6
    # Cap means Capacity percentage constant = headcount * 120 / 100

    for issue in issues:
        end_fb.append(issue.fields.customfield_38693)
        # original_estimate.append(issue.fields.customfield_39191)
        time_remaining.append(
            int(''.join(list(filter(str.isdigit, issue.fields.customfield_39192)))))
        if issue.fields.customfield_29790 == '5253':
            team.append('5G_SW_HZH_Squad A')
            time_remaining_percentage.append(int(''.join(
                list(filter(str.isdigit, issue.fields.customfield_39192)))) / squad_a_cap)
        elif issue.fields.customfield_29790 == '5254':
            team.append('5G_SW_HZH_Squad B')
            time_remaining_percentage.append(int(''.join(
                list(filter(str.isdigit, issue.fields.customfield_39192)))) / squad_b_cap)
        elif issue.fields.customfield_29790 == '5351':
            team.append('5G_SW_HZH_Rock')
            time_remaining_percentage.append(int(''.join(
                list(filter(str.isdigit, issue.fields.customfield_39192)))) / squad_rock_cap)
        elif issue.fields.customfield_29790 == '5255':
            team.append('5G_SW_HZH_Squad C')
            time_remaining_percentage.append(int(''.join(
                list(filter(str.isdigit, issue.fields.customfield_39192)))) / squad_c_cap)
        elif issue.fields.customfield_29790 == '6261':
            team.append('5G_SW_HZH_Shield')
            time_remaining_percentage.append(int(''.join(
                list(filter(str.isdigit, issue.fields.customfield_39192)))) / squad_shield_cap)

    '''
    # change string to number then append to new list:
    new_time_remaining = []
    for i in time_remaining:
        new_time_remaining.append(int(''.join(list(filter(str.isdigit, i)))))
    # print(new_time_remaining, type(new_time_remaining[1]))
    # print(team, end_fb, new_time_remaining)

    # change total effort to effort percentage
    new_time_remaining_pec = []
    for k in new_time_remaining:
        new_time_remaining_pec.append(k / 9.6)
    # print(new_time_remaining_pec)
    '''

    # 3.展示数据
    pd.set_option(
        'precision', 1,
        'display.max_rows', 500,
        'display.max_columns', 500,
        'display.width', 1000)
    # 设置参数：精度，最大行，最大列，最大显示宽度
    data = (list(zip(team, end_fb, time_remaining)))
    df = pd.DataFrame(data)
    df.columns = ['Team', 'FB', 'Remaining EE']
    # print(df)
    pivoted_df = pd.pivot_table(df[['Team',
                                    'FB',
                                    'Remaining EE']],
                                values='Remaining EE',
                                index=['Team'],
                                columns=['FB'],
                                aggfunc='sum',
                                fill_value=0)
    # print(pivoted_df, '\n')

    data1 = (list(zip(team, end_fb, time_remaining_percentage)))
    df1 = pd.DataFrame(data1)
    df1.columns = ['Team', 'FB', 'Percentage']
    # print(df1)
    pivoted_df1 = pd.pivot_table(df1[['Team', 'FB', 'Percentage']], values='Percentage', index=[
        'Team'], columns=['FB'], aggfunc='sum', fill_value=0)
    # print(pivoted_df1, '\n')

    # 4.美化数据
    app = Flask(__name__)
    # 打印log到文件
    logging.basicConfig(level=logging.DEBUG,
                        filename='FB_effort.log',
                        filemode='a',
                        format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                        )

    @app.route('/')
    def show_in_web():
        return render_template(
            "template.html",
            total=pivoted_df.to_html(classes="total", header="true", table_id="table"),
            percentage=pivoted_df1.to_html(classes="percentage", header="true", table_id="table")
        )

    if __name__ == '__main__':
        app.run()
        # app.run(host='10.57.209.188')


# 定时任务：每周一到周五 每天8点到20点 每整点0分 运行一次
scheduler = BlockingScheduler()
scheduler.add_job(job, 'cron', max_instances=65535, day_of_week='1-5', hour='8-20', minute='0')
scheduler.start()
