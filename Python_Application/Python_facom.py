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
import pandas as pd
import xlrd


def facom_api_power_on_off(ip, port=4001, port_num=1, operation_mode="power_on"):
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
        print("===PB IP/PORT configuration ERROR or connection FAILURE===")
    else:
        print("===IP:", ip, "PORT:", port_num, "->", operation_mode)


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


# read data from excel
'''
print("\n(1)全部数据：")
print(df.values)

print("\n(2)第2行第3列的值：")
print(df.values[1,2])

print("\n(3)第3行数据：")
print(df.values[2])

print("\n(4)获取第2、3行数据：")
print(df.values[[1,2]])

print("\n(5)第2列数据：")
print(df.values[:,1])

print("\n(6)第2、3列数据：")
print(df.values[:,[1,2]])

print("\n(7)第2至4行、第3至5列数据：")
print(df.values[1:4,2:5])
'''
# file1 = 'C:/5CG7316JVN-Data/h4zhang/Desktop/testline_info.xls'
# df = pd.read_excel(file1, sheet_name='Sheet1', header=None, skiprows=[0])
#
# if __name__ == "__main__":
#     for i in range(0, len(df.values[:, 0])):
#         facom_api_power_reset(df.values[:, 0][i], 4001, df.values[:, 1][i])
#         print("===PB IP:", df.values[:, 0][i], "PORT:", df.values[:, 1][i], "===\n===reset===")

# read data from ini
file2 = 'C:/5CG7316JVN-Data/h4zhang/Desktop/testline_info.ini'
conf = configparser.ConfigParser()
date = time.strftime("%w", time.localtime())  # 获取当天的星期数(int)

power_off_tl_ip_19 = []
power_off_tl_port_19 = []
power_off_tl_ip_23 = []
power_off_tl_port_23 = []
power_on_tl_ip_08 = []
power_on_tl_port_08 = []


def update_testline_info_to_power_off_on():
    conf.read(file2, encoding="utf-8")
    sections = conf.sections()
    print("\n===", datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S"), "===")
    for i in range(len(sections)):  # len(sections) = total testline num
        items = conf.items(sections[i])
        if int(items[2][1]):  # auto_power_off_on = 1
            if str(date) in items[3][1]:  # 配置的关机星期 包含当天
                print(sections[i], "-- power off time:", items[4][1])
                if items[4][1] == "19:00":  # 19点下电的TL加入列表
                    power_off_tl_ip_19.append(items[0][1])
                    power_off_tl_port_19.append(items[1][1])
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
    # print("# Testline IP/port about to power off/on based on exact time #")
    #     # # power off at 19:00
    #     # print(power_off_tl_ip_19)
    #     # print(power_off_tl_port_19)
    #     # # power off at 23:00
    #     # print(power_off_tl_ip_23)
    #     # print(power_off_tl_port_23)
    #     # # power on at 08:00
    #     # print(power_on_tl_ip_08)
    #     # print(power_on_tl_port_08)


# 19:00 -- TL下电
def power_off_19():
    if len(power_off_tl_ip_19):
        for i in range(len(power_off_tl_ip_19)):
            facom_api_power_on_off(power_off_tl_ip_19[i], port=4001,
                                   port_num=power_off_tl_port_19[i], operation_mode="power_off")
    else:
        print("===no testline need to power off at 19:00===")


# 23:00 -- TL下电
def power_off_23():
    if len(power_off_tl_ip_23):
        for j in range(len(power_off_tl_ip_23)):
            facom_api_power_on_off(power_off_tl_ip_23[j], port=4001,
                                   port_num=power_off_tl_port_23[j], operation_mode="power_off")
    else:
        print("===no testline need to power off at 23:00===")


# # 08:00 -- TL 上电
def power_on_08():
    if len(power_on_tl_ip_08):
        for k in range(len(power_on_tl_ip_08)):
            facom_api_power_on_off(power_on_tl_ip_08[k], port=4001,
                                   port_num=power_on_tl_port_08[k], operation_mode="power_on")
    else:
        print("===no testline need to power on at 08:00===")


# 定时读取配置文件并按照配置上下电
scheduler = BlockingScheduler()
scheduler.add_job(update_testline_info_to_power_off_on, 'cron', day_of_week='1-5', hour='0-23',
                  minute='0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55')
scheduler.add_job(power_off_19, 'cron', day_of_week='1-5', hour='0-23',
                  minute='2, 7, 12, 17, 22, 27, 32, 37, 42, 47, 52, 57')
scheduler.add_job(power_off_23, 'cron', day_of_week='1-5', hour='0-23',
                  minute='3, 8, 13, 18, 23, 28, 33, 38, 43, 48, 53, 58')
scheduler.add_job(power_on_08, 'cron', day_of_week='1-5', hour='0-23',
                  minute='4, 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59')
scheduler.start()


# 确认下电并打印
# 获取IP/port异常并打印 -- done
# 重复下+下/上+上
