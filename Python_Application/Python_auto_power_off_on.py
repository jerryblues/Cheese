# coding=utf-8
"""
@file: Python_facom.py
@time: 2018/9/5 13:36
@author: h4zhang
"""
# pip3 install gitpython
# pip3 install PyEmail
from facom_cmd import *
import configparser
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import pytz
from git import Repo
import smtplib
import datetime
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.request
import ssl
import time
import socket
from taf.pdu import pdu
import chinese_calendar as calendar


ssl._create_default_https_context = ssl._create_unverified_context


# 获取今天日期
def today_date():
    t = datetime.date.today()
    year = t.year
    month = t.month
    day = t.day
    print(f"=== Today is [{year}],[{month}],[{day}] ===")
    return year, month, day


def is_holiday(d):
    """
    判断日期是否是休息日
    """
    if calendar.is_holiday(d):
        # print("Holiday")
        return True
    else:
        # print("Working Day")
        return False


def turn_on_pdu(pdu_ip, pdu_port, port_num, planned_time, pdu_alias='power_on'):
    ppdu = pdu()
    if pdu_port == 5000:
        pdu_type = 'HBTE'
    elif pdu_port == 4001:
        pdu_type = 'FACOM'
    elif pdu_port == 3000:
        pdu_type = 'TOPYOUNG'
    else:
        pdu_type = 'Unknown'
    try:
        ppdu.setup_pdu(model=pdu_type, host=pdu_ip, port=pdu_port, alias=pdu_alias)
        ppdu.power_on(port=port_num, pdu_device=pdu_alias)
    except Exception as e:
        print('ERROR:', e)
    else:
        print("=== planned power off/on time [", planned_time, "] ===")
        print("===", current_date_time()[1], "IP:", pdu_ip, "PORT:", pdu_port, "PORT_NUM:", port_num, "->", pdu_alias, "===")


def turn_off_pdu(pdu_ip, pdu_port, port_num, planned_time, pdu_alias='power_off'):
    ppdu = pdu()
    if pdu_port == 5000:
        pdu_type = 'HBTE'
    elif pdu_port == 4001:
        pdu_type = 'FACOM'
    elif pdu_port == 3000:
        pdu_type = 'TOPYOUNG'
    else:
        pdu_type = 'Unknown'
    try:
        ppdu.setup_pdu(model=pdu_type, host=pdu_ip, port=pdu_port, alias=pdu_alias)
        ppdu.power_off(port=port_num, pdu_device=pdu_alias)
    except Exception as e:
        print('ERROR:', e)
    else:
        print("=== planned power off/on time [", planned_time, "] ===")
        print("===", current_date_time()[1], "IP:", pdu_ip, "PORT:", pdu_port, "PORT_NUM:", port_num, "->", pdu_alias, "===")


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


# read data from ini
r = Repo("/home/ute/zhanghao/autopoweroffon")
# file = 'testline_info.ini'
# conf = configparser.ConfigParser()
power_off_tl_ip_20 = []
power_off_tl_port_20 = []
power_off_tl_port_num_20 = []
power_off_tl_ip_23 = []
power_off_tl_port_23 = []
power_off_tl_port_num_23 = []
power_on_tl_ip_08 = []
power_on_tl_port_08 = []
power_on_tl_port_num_08 = []


def current_date_time():
    current_date = time.strftime("%w", time.localtime())  # 获取当天的星期数(int)
    current_time = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
    return current_date, current_time


def update_testline_info_to_power_off_on():
    r.remote().pull()  # 重新git pull 获取最新配置
    power_off_tl_ip_20.clear()  # 清空testline信息 重新读取配置
    power_off_tl_port_20.clear()
    power_off_tl_port_num_20.clear()
    power_off_tl_ip_23.clear()
    power_off_tl_port_23.clear()
    power_off_tl_port_num_23.clear()
    power_on_tl_ip_08.clear()
    power_on_tl_port_08.clear()
    power_on_tl_port_num_08.clear()
    file = 'testline_info.ini'
    conf = configparser.ConfigParser()
    conf.read(file, encoding="utf-8")
    sections = conf.sections()
    print("\n===", current_date_time()[1], "===")
    for i in range(len(sections)):  # len(sections) = total testline num
        items = conf.items(sections[i])
        if int(items[3][1]):  # auto_power_off_on = 1
            if str(current_date_time()[0]) in items[4][1]:  # 配置的关机星期 包含当天
            # if 1:  # 不判断配置的关机星期 由scheduler控制
                print(sections[i], "-- power off time:", items[5][1])
                if items[5][1] == "20:00":  # 20点下电的TL加入列表
                    power_off_tl_ip_20.append(items[0][1])
                    power_off_tl_port_20.append(int(items[1][1]))
                    power_off_tl_port_num_20.append(items[2][1])
                else:  # 23点下电的TL加入列表
                    power_off_tl_ip_23.append(items[0][1])
                    power_off_tl_port_23.append(int(items[1][1]))
                    power_off_tl_port_num_23.append(items[2][1])
                print(sections[i], "-- power on  time:", items[6][1])
                power_on_tl_ip_08.append(items[0][1])  # 08点开机的TL加入列表
                power_on_tl_port_08.append(int(items[1][1]))
                power_on_tl_port_num_08.append(items[2][1])
            else:  # 配置的关机星期 未包含当天
                print(sections[i], "-- not power off today")
        else:  # auto_power_off_on = 0
            print(sections[i], "-- not open power off flag")
    print("===========================")


# 20:00 -- TL下电
def power_off_20():
    today = today_date()
    date = datetime.date(today[0], today[1], today[2])
    if is_holiday(date):
        print("=== Disable power off as today is holiday ===")
        pass
    else:
        if len(power_off_tl_ip_20):
            for i in range(len(power_off_tl_ip_20)):
                turn_off_pdu(power_off_tl_ip_20[i], power_off_tl_port_20[i], power_off_tl_port_num_20[i], planned_time="20:00")
                time.sleep(2)
        else:
            print("=== No testline need to power off at 20:00 ===")


# 23:00 -- TL下电
def power_off_23():
    today = today_date()
    date = datetime.date(today[0], today[1], today[2])
    if is_holiday(date):
        print("=== Disable power off as today is holiday ===")
        pass
    else:
        if len(power_off_tl_ip_23):
            for j in range(len(power_off_tl_ip_23)):
                turn_off_pdu(power_off_tl_ip_23[j], power_off_tl_port_23[j], power_off_tl_port_num_23[j], planned_time="23:00")
                time.sleep(2)
        else:
            print("=== No testline need to power off at 23:00 ===")


# # 08:00 -- TL 上电
def power_on_08():
    today = today_date()
    date = datetime.date(today[0], today[1], today[2])
    if is_holiday(date):
        print("=== Disable power on as today is holiday ===")
        pass
    else:
        if len(power_on_tl_ip_08):
            for k in range(len(power_on_tl_ip_08)):
                turn_on_pdu(power_on_tl_ip_08[k], power_on_tl_port_08[k], power_on_tl_port_num_08[k], planned_time="08:00")
                time.sleep(10)
        else:
            print("=== No testline need to power on at 08:00 ===")


'''
def send_report_content(subject, sender, receivers_to, receivers_cc, html):
    message = MIMEText(html, 'html', 'utf-8')
    message['From'] = Header(sender.split('@')[0], 'utf-8')
    message['Cc'] = receivers_cc
    message['To'] = receivers_to
    message['Subject'] = Header(subject, 'utf-8')
    server = smtplib.SMTP('172.24.146.155')
    server.sendmail(sender, receivers_to.split(','), message.as_string())


sender_email = r"hao.6.zhang@nokia-sbell.com"
receiver_email = r"hao.6.zhang@nokia-sbell.com, youyong.zheng@nokia-sbell.com, ella.shi@nokia-sbell.com"
receiver_cc_email = r"hao.6.zhang@nokia-sbell.com"
# today = str(datetime.date.today())
subject = f'RAN_L3_SW_1_CN_ET - Testline Power Off/On Status'


def send_mail():
    tic = time.perf_counter()
    try:
        html = urllib.request.urlopen("https://10.57.195.35:8080/TL_status", timeout=500).read()
    except Exception as e:
        html = '<font size="4">' \
               '<strong><br/>' \
               'Not able to get TL status now!<br/>' \
               'Check this link first:<br/>' \
               'https://10.57.195.35:8080/TL_status</strong>'
        print("=== get TL status failed ===", e)
        toc = time.perf_counter()
        print(f"time cost: {toc - tic:0.2f} seconds")
    else:
        print("=== send mail done ===")
        toc = time.perf_counter()
        print(f"time cost: {toc - tic:0.2f} seconds")
    # print(html)
    send_report_content(subject=subject, sender=sender_email, receivers_to=receiver_email, receivers_cc=receiver_cc_email, html=html)
'''


class MailSender:
    def __init__(self):
        self.nokia_relays = [
            '10.130.128.21',
            '10.130.128.30',
            '135.239.3.80',
            '135.239.3.83']
        self.relay_port = 25
        self.sender = 'hao.6.zhang@nokia-sbell.com'

    def is_relay_connectable(self, relay):
        try:
            con = Telnet(relay, self.relay_port, timeout=5)
            is_connectable = True
            con.close()
        except Exception:
            print('connet to {} failed'.format(relay))
            is_connectable = False
        return is_connectable

    def choose_nokia_relay(self):
        for relay in self.nokia_relays:
            print("try:", relay)
            if self.is_relay_connectable(relay):
                print(relay)
                return relay
        raise AssertionError(
            'not find the nokia mail relay from {} '
            'with port {}'.format(
                self.nokia_relays,
                self.relay_port))

    def send_mail(self, receiver, subject, content, format='plain', attachFileList=None):
        message_to = "; ".join(receiver)  # change list to string
        sender = self.sender
        message = MIMEMultipart()
        message['From'] = self.sender
        message['To'] = message_to  # should be string
        subject = subject
        message['Subject'] = Header(subject, 'utf-8')

        message.attach(MIMEText(content, format, 'utf-8'))
        if attachFileList:
            for file in attachFileList:
                att1 = MIMEText(open(file, 'rb').read(), 'base64', 'utf-8')
                att1["Content-Type"] = 'application/octet-stream'
                att1["Content-Disposition"] = 'attachment; filename={}'.format(file)
                message.attach(att1)

        # relay = self.choose_nokia_relay()
        smtp = smtplib.SMTP('10.130.128.21', self.relay_port)
        smtp.sendmail(sender, receiver, message.as_string())  # should keep receiver as list
        smtp.quit()
        print('send mail to {} succeed'.format(receiver))


def mail():
    today = today_date()
    date = datetime.date(today[0], today[1], today[2])
    if is_holiday(date):
        print("=== Disable send mail as today is holiday ===")
        pass
    else:
        content = urllib.request.urlopen("https://10.57.195.35:8080/TL_status", timeout=500).read()
        MailSender().send_mail(
            receiver=['hao.6.zhang@nokia-sbell.com', 'youyong.zheng@nokia-sbell.com', 'ella.shi@nokia-sbell.com'],  # should be list
            subject='RAN_L3_SW_1_CN_ET - Testline Power Off/On Status',
            content=content, format='html')


update_testline_info_to_power_off_on()

# 定时读取配置文件并按照配置上下电
scheduler = BlockingScheduler()
scheduler.add_job(update_testline_info_to_power_off_on, 'cron', day_of_week='0-6', hour='0-23', minute='0',
                  timezone="Asia/Shanghai")
scheduler.add_job(power_off_20, 'cron', day_of_week='0-6', hour='20', minute='5', timezone="Asia/Shanghai")
scheduler.add_job(power_off_23, 'cron', day_of_week='0-6', hour='23', minute='5', timezone="Asia/Shanghai")
scheduler.add_job(mail, 'cron', day_of_week='0-6', hour='23', minute='30', timezone="Asia/Shanghai")
scheduler.add_job(power_on_08, 'cron', day_of_week='0-6', hour='7', minute='30', timezone="Asia/Shanghai")
scheduler.add_job(mail, 'cron', day_of_week='0-6', hour='8', minute='5', timezone="Asia/Shanghai")
scheduler.start()
