# coding=utf-8
"""
@file: Python_test.py.py
@time: 2022/3/24 16:43
@author: h4zhang
"""

from facom_cmd import *
import configparser
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import pytz
from git.repo import Repo


# def facom_api_power_on_off_origin(ip, port=4001, port_num=1, operation_mode="power_on"):
#     """
#     this API is PowerON or PowerOFF the facom equipment
#     | Input Parameters | Man | Description |
#     | ip | Yes | Ip of facom equipment |
#     | port| Yes | Connection port of facom server,1~6 are allowed |
#     | port_num | Yes | The power output port number |
#     | operation_mode | Man | 'power_on' or 'power_off' |
#
#     example:
#     facom_api_power_on_off('10.69.6.32','4001','6','power_off')
#     """
#     fb_obj = OperationOfFacom(ip, port)
#     if operation_mode in ['power_on', 'power_off', 'qurery_status']:
#         eval('fb_obj.%s("%s")' % (operation_mode, port_num))
#     # else:
#     #     raise LrcValidateException('operation_mode = %s is not support, \
#     #     it must be power_on or power_off' % operation_mode)


def facom_api_power_on_off_origin(ip, port=4001, port_num=1, operation_mode="power_on"):
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
        if operation_mode in ['power_on', 'power_off', 'qurery_status']:
            return eval('fb_obj.%s("%s")' % (operation_mode, port_num))
        # else:
        #     raise LrcValidateException('operation_mode = %s is not support, \
        #     it must be power_on or power_off' % operation_mode)
    except:
        return "status unkown"


file = 'C:/Holmes/code/autopoweroffon/testline_info.ini'
conf = configparser.ConfigParser()
tl_ip = []
tl_port = []
tl_power_off_on_flag = []
tl_power_off_date = []
tl_power_off_time = []
tl_power_on_time = []
tl_owner = []
tl_power_off_on_status = []


def get_testline_info():
    conf.read(file, encoding="utf-8")
    sections = conf.sections()
    for i in range(len(sections)):  # len(sections) = total testline num
        items = conf.items(sections[i])
        tl_ip.append(items[0][1])
        tl_port.append(items[1][1])
        tl_power_off_on_flag.append(items[2][1])
        tl_power_off_date.append(items[3][1])
        tl_power_off_time.append(items[4][1])
        tl_power_on_time.append(items[5][1])
        tl_owner.append(items[6][1])
        tl_power_off_on_status.append(facom_api_power_on_off_origin(
            tl_ip[i], port=4001, port_num=tl_port[i], operation_mode="qurery_status"))
    print(tl_ip, tl_port, tl_power_off_on_status)
    return tl_ip, tl_port, tl_power_off_on_flag, tl_power_off_date, tl_power_off_time, tl_power_on_time, tl_owner, tl_power_off_on_status


get_testline_info()
