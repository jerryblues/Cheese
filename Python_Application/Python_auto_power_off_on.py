# coding=utf-8
"""
@file: Python_facom.py
@time: 2018/9/5 13:36
@author: h4zhang
"""

from facom_cmd import *
import configparser
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import pytz
from git.repo import Repo


def facom_api_power_on_off(ip, port=4001, port_num=1, operation_mode="power_on", planned_time="00:00"):
    """
    this API is PowerON or PowerOFF the facom equipment
    | Input Parameters | Man | Description |
    | ip | Yes | Ip of facom equipment |
    | port| Yes | Connection port of facom server,1~6 are allowed |
    | port_num | Yes | The power output port number |
    | operation_mode | Man | 'power_on' or 'power_off' |

    example:
    facom_api_power_on_off('10.69.6.32','4001','6','power_off')
    """
    try:
        fb_obj = OperationOfFacom(ip, port)
        if operation_mode in ['power_on', 'power_off']:
            eval('fb_obj.%s("%s")' % (operation_mode, port_num))
        # else:
        #     raise LrcValidateException('operation_mode = %s is not support, \
        #     it must be power_on or power_off' % operation_mode)
    except:
        print("=== planned power off/on time [", planned_time, "] ===")
        print("===", current_date_time()[1], "IP:", ip, "PORT:", port_num, "-> Configuration ERROR or Connection FAILURE ===")
    else:
        print("=== planned power off/on time [", planned_time, "] ===")
        print("===", current_date_time()[1], "IP:", ip, "PORT:", port_num, "->", operation_mode, "===")


def facom_api_power_reset(ip, port=4001, port_num=1):
    """
    this API is used to reset the facom equipment
    | Input Parameters | Man | Description |
    | ip | Yes | Ip of facom equipment |
    | port| Yes | Connection port of facom server,1~6 are allowed |
    | port_num | Yes | The power output port number |

    example:
    facom_api_power_rest('10.69.6.32','4001','6')
    """
    facom_api_power_on_off(ip, port, port_num, 'power_off')
    import time
    time.sleep(10)
    facom_api_power_on_off(ip, port, port_num, 'power_on')


# read data from ini
r = Repo("C:/Holmes/code/autopoweroffon")
file = 'C:/Holmes/code/autopoweroffon/testline_info.ini'
conf = configparser.ConfigParser()
power_off_tl_ip_20 = []
power_off_tl_port_20 = []
power_off_tl_ip_23 = []
power_off_tl_port_23 = []
power_on_tl_ip_08 = []
power_on_tl_port_08 = []


def current_date_time():
    current_date = time.strftime("%w", time.localtime())  # 获取当天的星期数(int)
    current_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
    return current_date, current_time


def update_testline_info_to_power_off_on():
    r.remote().pull()  # 重新git pull 获取最新配置
    power_off_tl_ip_20.clear()  # 清空testline信息 重新读取配置
    power_off_tl_port_20.clear()
    power_off_tl_ip_23.clear()
    power_off_tl_port_23.clear()
    power_on_tl_ip_08.clear()
    power_on_tl_port_08.clear()
    conf.read(file, encoding="utf-8")
    sections = conf.sections()
    print("\n===", current_date_time()[1], "===")
    for i in range(len(sections)):  # len(sections) = total testline num
        items = conf.items(sections[i])
        if int(items[2][1]):  # auto_power_off_on = 1
            if str(current_date_time()[0]) in items[3][1]:  # 配置的关机星期 包含当天
                print(sections[i], "-- power off time:", items[4][1])
                if items[4][1] == "20:00":  # 20点下电的TL加入列表
                    power_off_tl_ip_20.append(items[0][1])
                    power_off_tl_port_20.append(items[1][1])
                else:  # 23点下电的TL加入列表
                    power_off_tl_ip_23.append(items[0][1])
                    power_off_tl_port_23.append(items[1][1])
                print(sections[i], "-- power on  time:", items[5][1])
                power_on_tl_ip_08.append(items[0][1])  # 08点开机的TL加入列表
                power_on_tl_port_08.append(items[1][1])
            else:  # 配置的关机星期 未包含当天
                print(sections[i], "-- not power off today")
        else:  # auto_power_off_on = 0
            print(sections[i], "-- not open power off flag")
    print("===========================")
    print("# Testline IP/port about to power off/on based on exact time #")
    # power off at 20:00
    print(power_off_tl_ip_20)
    print(power_off_tl_port_20)
    # power off at 23:00
    print(power_off_tl_ip_23)
    print(power_off_tl_port_23)
    # power on at 08:00
    print(power_on_tl_ip_08)
    print(power_on_tl_port_08)


# 20:00 -- TL下电
def power_off_20():
    if len(power_off_tl_ip_20):
        for i in range(len(power_off_tl_ip_20)):
            facom_api_power_on_off(power_off_tl_ip_20[i], port=4001,
                                   port_num=power_off_tl_port_20[i], operation_mode="power_off", planned_time="20:00")
    else:
        print("===No testline need to power off at 20:00===")


# 23:00 -- TL下电
def power_off_23():
    if len(power_off_tl_ip_23):
        for j in range(len(power_off_tl_ip_23)):
            facom_api_power_on_off(power_off_tl_ip_23[j], port=4001,
                                   port_num=power_off_tl_port_23[j], operation_mode="power_off", planned_time="23:00")
    else:
        print("===No testline need to power off at 23:00===")


# # 08:00 -- TL 上电
def power_on_08():
    if len(power_on_tl_ip_08):
        for k in range(len(power_on_tl_ip_08)):
            facom_api_power_on_off(power_on_tl_ip_08[k], port=4001,
                                   port_num=power_on_tl_port_08[k], operation_mode="power_on", planned_time="08:00")
    else:
        print("===No testline need to power on at 08:00===")


# 定时读取配置文件并按照配置上下电
scheduler = BlockingScheduler()
scheduler.add_job(update_testline_info_to_power_off_on, 'cron', day_of_week='0-6', hour='0-23', minute='0',
                  timezone="Asia/Shanghai")
scheduler.add_job(power_off_20, 'cron', day_of_week='0-4', hour='20', minute='5', timezone="Asia/Shanghai")
scheduler.add_job(power_off_23, 'cron', day_of_week='0-4', hour='23', minute='5', timezone="Asia/Shanghai")
scheduler.add_job(power_on_08, 'cron', day_of_week='0-4', hour='8', minute='5', timezone="Asia/Shanghai")
scheduler.start()

'''
# future function:
  下电时长统计
  TL power off/on plan show on web
  邮件通知
'''
