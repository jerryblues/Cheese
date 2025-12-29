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
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ET_ReP_Jira


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


class MailSender:
    def __init__(self):
        self.nokia_relays = [
            '10.130.128.21',
            '10.130.128.30',
            '135.239.3.80',
            '135.239.3.83']
        self.relay_port = 25
        self.sender = 'hao.6.zhang@nokia-sbell.com'

    def send_mail(self, receiver, subject, content, attachFileList=None):
        message_to = "; ".join(receiver)  # change list to string
        sender = self.sender
        message = MIMEText(content, 'html', 'utf-8')
        message['From'] = self.sender
        message['To'] = message_to  # should be string
        message['Subject'] = Header(subject, 'utf-8')

        if attachFileList:
            for file in attachFileList:
                att1 = MIMEText(open(file, 'rb').read(), 'base64', 'utf-8')
                att1["Content-Type"] = 'application/octet-stream'
                att1["Content-Disposition"] = 'attachment; filename={}'.format(file)
                message.attach(att1)

        smtp = smtplib.SMTP('10.130.128.21', self.relay_port)
        smtp.sendmail(sender, receiver, message.as_string())  # should keep receiver as list
        smtp.quit()
        logging.debug(f"<--send mail to {receiver} succeed'-->")
        # print('send mail to {} succeed'.format(receiver))


def query_jira_issue(jql, max_results=10000):
    try:
        jira = JIRA(basic_auth=(jira_username, jira_password), options={'server': jira_server})
        issues = jira.search_issues(jql, maxResults=max_results)
    except Exception as e:
        logging.info(f"[Error] {e}")
        return None
    else:
        return issues


def filter_string(feature, test_set):
    # feature 需要转为大写，否则小写输入的feature会匹配不到ReP中大写的original_test_set
    # 第一个if，过滤掉 CNI-xxx 开头的test set，比如输入CB008140，会过滤掉CNI-72007-C_CB008140-
    if test_set.startswith(feature.upper() + '-') or test_set.startswith(feature.upper() + ' '):
        parts = test_set.split('-', maxsplit=2)
        filtered = (parts[0] + '-' + parts[1])
        return filtered
    # 在第一个if中，输入的feature与test set完全一样的也会被过滤掉，这里用这个elif，获取这些应该显示的值
    elif feature.upper() == test_set:
        return feature.upper()
    else:
        # 不满足上述条件，返回none，用于调用这个函数时进行判断
        return None


def get_case_info_from_rep(feature, url, t):
    i = 0
    backlog_id = []
    case_name = []
    qc_status = []
    sub_feature = []
    # query backlog ID and case name from reporting portal, 'feature' is from input on web
    query_rep_result = ET_ReP_Jira.query_rep(url, t)

    if len(query_rep_result['results']):  # 查询Rep得到结果
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

        while i < len(query_rep_result['results']):
            test_set = query_rep_result['results'][i]['test_set']['name']
            # 获取sub-feature, 且对非法值处理，比如'CNI-72007-C_CB008290-A-1'
            match = filter_string(feature, test_set)
            if match:
                # 如果能正常匹配，才把sub_feature，backlog_id 这些进行append
                sub_feature.append(match)
                # 对 backlog 空值的处理
                if query_rep_result['results'][i]['backlog_id']:
                    backlog_id.append(query_rep_result['results'][i]['backlog_id'][0]['id'])
                else:
                    backlog_id.append(0)
                # 完整的case name
                fullname = query_rep_result['results'][i]['name']
                # 截取fullname中第一个英文字符开始的100个字符
                case_name.append(fullname[re.search('[a-zA-Z]', fullname).start():100] + '...')
                qc_status.append(query_rep_result['results'][i]['status'])
                i = i + 1
            else:
                # 如果test set匹配不到，则不统计这项，比如 'CNI-72007-C_CB008290-A-1' 会被过滤掉
                logging.info(f"[test set not matched]: {test_set}")
                i = i + 1

        logging.debug(f"[{i}] <--get sub_feature from query_rep_result-->")
        logging.debug(f"[{i}] <--get backlog_id from query_rep_result-->")
        logging.debug(f"[{i}] <--get case_name from query_rep_result-->")
        logging.debug(f"[{i}] <--get qc_status from query_rep_result-->")
        return backlog_id, sub_feature, case_name, qc_status

    else:  # 查询ReP结果为空
        logging.debug("<--get result[null] from rep-->")
        return backlog_id, sub_feature, case_name, qc_status


def get_pr_info_from_rep(url, t):
    k = 0
    pr_id, pr_link, gic, fault_analysis_person, author, author_group, state, title, reported_date, rd_info \
        = [], [], [], [], [], [], [], [], [], []
    # query backlog ID and case name from reporting portal, 'feature' is from input on web
    query_rep_result = ET_ReP_Jira.query_rep(url, t)
    if len(query_rep_result['results']):
        logging.debug("<--get result from rep done-->")
        while k < len(query_rep_result['results']):
            pr_id.append(query_rep_result['results'][k]['pronto_id'])
            pr_link.append(query_rep_result['results'][k]['pronto_tool_url'])
            gic.append(query_rep_result['results'][k]['group_in_charge_name'])
            fault_analysis_person.append(query_rep_result['results'][k]['fault_analysis_responsible_person'])
            author.append(query_rep_result['results'][k]['author'])
            author_group.append(query_rep_result['results'][k]['author_group'])
            state.append(query_rep_result['results'][k]['state'])
            title.append(query_rep_result['results'][k]['title'])
            time_str = query_rep_result['results'][k]['reported_date']           # 时间格式转换，去掉T09:45:19.000+0300
            reported_date.append(time_str[:time_str.find("T")])
            # 获取最新的RD info，先将all RD info按\n拆分，再截取其中数字或[数字开头的string
            all_rd_info = query_rep_result['results'][k]['rd_info']
            lines = all_rd_info.split("\n")
            pattern = r"^\d.*|^\[\d.*"
            filtered_text = [line.strip() for line in lines if re.match(pattern, line.strip())]
            if filtered_text:
                rd_info.append(filtered_text[0])
            else:
                rd_info.append("No latest RD info")
            k += 1
        return pr_id, pr_link, gic, fault_analysis_person, author, author_group, state, title, reported_date, rd_info
    else:
        logging.debug("<--get result[null] from rep-->")
        return pr_id, pr_link, gic, fault_analysis_person, author, author_group, state, title, reported_date, rd_info


def get_jira_issue_from_jira(jql):
    jira_id, feature_id, title, assignee, reporter, created, status, comment, jira_link = [], [], [], [], [], [], [], [], []
    query_jira_issue_result = query_jira_issue(jql)
    if query_jira_issue_result:
        logging.debug("<--get result from jira done-->")
        for issue in query_jira_issue_result:
            jira_id.append(issue.key)
            feature_id.append(issue.fields.customfield_37381)
            title.append(issue.fields.summary)
            assignee.append(str(issue.fields.assignee))  # 需要转换为str，否则输出为Jira格式
            reporter.append(str(issue.fields.reporter))  # 需要转换为str，否则输出为Jira格式
            time_str = issue.fields.created              # 时间格式转换，去掉T09:45:19.000+0300
            created.append(time_str[:time_str.find("T")])
            status.append(str(issue.fields.status))      # 需要转换为str，否则输出为Jira格式
            comment.append(issue.fields.customfield_44005)
            jira_link.append("https://jiradc.ext.net.nokia.com/browse/"+issue.key)
        return jira_id, feature_id, title, assignee, reporter, created, status, comment, jira_link
    else:
        logging.debug("<--get result[null] from jira-->")
        return jira_id, feature_id, title, assignee, reporter, created, status, comment, jira_link


def pivot_feature_report_qc_status(sub_feature, qc_status, case):
    pd.set_option(  # 设置参数：精度，最大行，最大列，最大显示宽度
        'precision', 1,
        'display.max_rows', 500,
        'display.max_columns', 500,
        'display.width', 1000)

    if not sub_feature or not qc_status or not case:
        # 当入参为空时，返回none，同时在调用处对none进行判断，html中也需要处理
        logging.debug("<--get result[null] from source data-->")
        return pd.DataFrame({})
    else:
        logging.debug("<--get result done and pivot table start-->")
        df0 = pd.DataFrame({'Test Set': sub_feature, 'QC Status': qc_status, 'Sum': case})
        df0.columns = ['Test Set', 'QC Status', 'Sum']
        pivoted_feature = pd.pivot_table(df0[['Test Set', 'QC Status', 'Sum']], values='Sum', index=['Test Set'],
                                         columns=['QC Status'],
                                         aggfunc='count', fill_value=0, margins=True)
        # 移除索引列的标题，这里的索引是 Test Set
        pivoted_feature.index.name = None
        # 自定义列的排列顺序
        custom_columns = ['Passed', 'Failed', 'Blocked', 'No Run', 'N/A', 'All']
        pivoted_feature = pivoted_feature.reindex(columns=custom_columns)
        # 将空值替换为 0
        pivoted_feature = pivoted_feature.fillna(0).astype(int)
        # 添加空的"Comment"列
        pivoted_feature = pivoted_feature.assign(Comment='')
        return pivoted_feature


# app = Flask(__name__)
#
#
# @app.route("/Feature_Report")
# def index():
#     return render_template("et_feature_report.html")
#
#
# @app.route('/Feature_Report', methods=['POST'])
# def web_server_issue():
#     global token
#     if validate_token(token):
#         print("[0.1] <--token is valid-->")
#     else:  # 如果token失效，就重新获取
#         token = get_token()
#         print("[0.1] <--get new token-->")
#     print("[0.2] <--token validated-->")
#     feature = request.form.get("feature_id")  # get input from web
#     if feature:
#         print(f"[1.1] <--query feature id: [{feature}]-->")
#     else:
#         print("[1.1] <--get feature id failed-->")
#         return render_template("et_feature_report.html")
#     url_case = "https://rep-portal.ext.net.nokia.com/api/qc-beta/instances/report/?fields=id%2Cm_path%2Ctest_set__name%2Cbacklog_id%2Cname%2Curl%2Cstatus%2Cstatus_color%2Cfault_report_id_link%2Ccomment%2Csw_build%2Cres_tester%2Ctest_entity%2Cfunction_area%2Cca%2Corganization%2Crelease%2Cfeature%2Crequirement%2Clast_testrun__timestamp&limit=200&m_path__pos_neg=New_Features%5CRAN_L3_SW_CN_1&ordering=name&test_set__name__pos_neg_empty_str="
#     url_case_feature = url_case + feature
#     url_pr = "https://rep-portal.ext.net.nokia.com/api/pronto/report/?fields=pronto_id,pronto_tool_url,title,rd_info,state,author,author_group,group_in_charge_name,fault_analysis_responsible_person,reported_date&limit=200&ordering=-reported_date&feature__pos_neg="
#     url_pr_feature = url_pr + feature
#     jql = '''project = 68296 AND type = Bug AND "Feature ID" ~ "''' + feature + '''*" ORDER BY key DESC'''
#     print(jql)
#     # 第一个表格中的数据，case result统计
#     case_data = get_case_info_from_rep(feature, url_case_feature, token)
#     # return: backlog_id, end_fb, sub_feature, case_name, qc_status
#     case_status = pivot_feature_report_qc_status(case_data[2], case_data[4], case_data[3])
#
#     # 第二个表格中的数据，pr 统计
#     pr_data = get_pr_info_from_rep(url_pr_feature, token)
#         # pr_id, pr_link, gic, fault_analysis_person, author, author_group, state, title, reported_date, rd_info
#     data_for_pr = {
#         'pr_id': pr_data[0],
#         'pr_link': pr_data[1],
#         'gic': pr_data[2],
#         'fault_analysis_person': pr_data[3],
#         'author': pr_data[4],
#         'author_group': pr_data[5],
#         'state': pr_data[6],
#         'title': pr_data[7],
#         'reported_date': pr_data[8],
#         'rd_info': pr_data[9]
#         }
#     df_pr = pd.DataFrame(data_for_pr)
#
#     # 第三个表格中的数据，jira 统计
#     jira_data = get_jira_issue_from_jira(jql)
#         # jira_id, feature_id, title, assignee, reporter, created, status, comment
#     data_for_jira = {
#         'jira_id': jira_data[0],
#         'feature_id': jira_data[1],
#         'title': jira_data[2],
#         'assignee': jira_data[3],
#         'reporter': jira_data[4],
#         'created': jira_data[5],
#         'status': jira_data[6],
#         'comment': jira_data[7],
#         'jira_link': jira_data[8]
#          }
#     df_jira = pd.DataFrame(data_for_jira)
#
#     return render_template(
#         "et_feature_report.html",
#         table_qc_status=case_status.to_html(classes="total", header="true", table_id="table"),
#         data_pr=df_pr.to_dict('records'),
#         data_jira=df_jira.to_dict('records'),
#         feature_id=feature,
#     )
#
#
# @app.route('/send_content', methods=['POST'])
# def send_content():
#     mail_sender = MailSender()
#     try:
#         # 获取 HTML 内容
#         data = request.get_json()
#         html_content = data['htmlContent']
#
#         # 设置收件人、主题和 HTML 内容
#         receiver = ['hao.6.zhang@nokia-sbell.com']
#         subject = 'HTML Email'
#         content = html_content
#
#         mail_sender.send_mail(receiver, subject, content)
#
#         return '', 200
#     except Exception as e:
#         print('ERROR:', e)
#         return '', 500
#
#
# if __name__ == '__main__':
#     app.run(debug=True, host='127.0.0.1', port=8080)
