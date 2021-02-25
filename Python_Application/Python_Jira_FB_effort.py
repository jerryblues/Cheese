# coding=utf-8
from jira import JIRA
import pandas as pd
import logging


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
issues = searchIssues(jira_filter)
# print(issues)

# 2.处理数据
team = []
end_FB = []
# original_estimate = []
time_remaining = []
time_remaining_percentage = []
Squad_A_Cap = 9.6
Squad_B_Cap = 9.6
Squad_Rock_Cap = 9.6
Squad_Shield_Cap = 8.4
Squad_C_Cap = 9.6
# Cap means Capacity percentage constant = headcount * 120 / 100

for issue in issues:
    end_FB.append(issue.fields.customfield_38693)
    # original_estimate.append(issue.fields.customfield_39191)
    time_remaining.append(
        int(''.join(list(filter(str.isdigit, issue.fields.customfield_39192)))))
    if issue.fields.customfield_29790 == '5253':
        team.append('5G_SW_HZH_Squad A')
        time_remaining_percentage.append(int(''.join(
            list(filter(str.isdigit, issue.fields.customfield_39192)))) / Squad_A_Cap)
    elif issue.fields.customfield_29790 == '5254':
        team.append('5G_SW_HZH_Squad B')
        time_remaining_percentage.append(int(''.join(
            list(filter(str.isdigit, issue.fields.customfield_39192)))) / Squad_B_Cap)
    elif issue.fields.customfield_29790 == '5351':
        team.append('5G_SW_HZH_Rock')
        time_remaining_percentage.append(int(''.join(
            list(filter(str.isdigit, issue.fields.customfield_39192)))) / Squad_Rock_Cap)
    elif issue.fields.customfield_29790 == '5255':
        team.append('5G_SW_HZH_Squad C')
        time_remaining_percentage.append(int(''.join(
            list(filter(str.isdigit, issue.fields.customfield_39192)))) / Squad_C_Cap)
    elif issue.fields.customfield_29790 == '6261':
        team.append('5G_SW_HZH_Shield')
        time_remaining_percentage.append(int(''.join(
            list(filter(str.isdigit, issue.fields.customfield_39192)))) / Squad_Shield_Cap)


'''
# change string to number then append to new list:
new_time_remaining = []
for i in time_remaining:
    new_time_remaining.append(int(''.join(list(filter(str.isdigit, i)))))
# print(new_time_remaining, type(new_time_remaining[1]))
# print(team, end_FB, new_time_remaining)

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
data = (list(zip(team, end_FB, time_remaining)))
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
print(pivoted_df, '\n')

data1 = (list(zip(team, end_FB, time_remaining_percentage)))
df1 = pd.DataFrame(data1)
df1.columns = ['Team', 'FB', 'Percentage']
# print(df1)
pivoted_df1 = pd.pivot_table(df1[['Team', 'FB', 'Percentage']], values='Percentage', index=[
                             'Team'], columns=['FB'], aggfunc='sum', fill_value=0)
print(pivoted_df1, '\n')

# 4.美化数据
# Implemented in Python_Flask

# 打印log到文件
logging.basicConfig(level=logging.DEBUG,  # 控制台打印的日志级别
                    filename='FB_effort.log',
                    filemode='a',
                    # 模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                    # a是追加模式，默认如果不写的话，就是追加模式
                    format=
                    '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                    # 日志格式
                    )


'''
1.抓取数据
2.处理数据
3.展示数据
4.美化数据
'''

'''
# 方案三
def team_effort_per_fb(team_name):
    new_list1 = []
    new_list2 = []
    data = ()
    for j in range(0, len(team)):
        if team[j] == team_name:
            new_list1.append(end_FB[j])
            new_list2.append(new_time_remaining[j])
            data = (list(zip(new_list1, new_list2)))
    df = pd.DataFrame(data).groupby([0]).aggregate(sum)
    df.columns = ['Remaining EE']
    # df.index = [team_name]
    return df


print('5G_SW_HZH_Squad A effort per FB:\n', team_effort_per_fb('5G_SW_HZH_Squad A'), '\n================\n')
print('5G_SW_HZH_Squad B effort per FB:\n', team_effort_per_fb('5G_SW_HZH_Squad B'), '\n================\n')
print('5G_SW_HZH_Rock effort per FB:\n', team_effort_per_fb('5G_SW_HZH_Rock'), '\n================\n')
'''

'''
# 方案二
df = pd.DataFrame([
    ['2016-10-20 00:00:00', 6, 17],
    ['2016-10-20 00:00:00', 0, 21],
    ['2017-09-11 00:00:00', 7, 22],
    ['2017-09-11 00:00:00', 5, 30],
    ['2017-09-11 00:00:00', 2, 40]
])

print(df.groupby([0]).aggregate(sum))
'''

'''
# 方案一
Squad_A_FB = []
Squad_A_effort = []
Squad_A_FB_new = []
Squad_A_effort_new = []

for i in range(0, len(team)):
    if team[i] == '5G_SW_HZH_Squad A':
        # print('5G_SW_HZH_Squad A,', end_FB[i], new_time_remaining[i])
        Squad_A_FB.append(end_FB[i])
        Squad_A_effort.append(new_time_remaining[i])
# print(Squad_A_FB, Squad_A_effort)

Squad_A_FB_new.append(Squad_A_FB[0])
Squad_A_effort_new.append(Squad_A_effort[0])


for j in range(1, len(Squad_A_FB)):
    if Squad_A_FB[j] != Squad_A_FB[j-1]:
        Squad_A_FB_new.append(Squad_A_FB[j])
        Squad_A_effort_new.append(Squad_A_effort[j])
    elif Squad_A_FB[j] == Squad_A_FB[j-1]:
        Squad_A_effort_new[j] = Squad_A_effort_new[j] + Squad_A_effort[j-1]
print(Squad_A_FB_new, Squad_A_effort_new)

    elif team[i] == '5G_SW_HZH_Squad B':
        print('5G_SW_HZH_Squad B,', end_FB[i], new_time_remaining[i])
    elif team[i] == '5G_SW_HZH_Rock':
        print('5G_SW_HZH_Rock,', end_FB[i], new_time_remaining[i])
'''
