# coding=utf-8
"""
@file: Python_test.py.py
@time: 2022/3/24 16:43
@author: h4zhang
"""

from jira import JIRA
import pandas as pd
from flask import Flask, render_template
from datetime import datetime
import pytz
import logging
from collections import Counter
import datetime
import configparser
from facom_cmd import *
import urllib.request
import ssl
from taf.pdu import pdu
import time
import socket

file = 'C:/Holmes/code/autopoweroffon/testline_info.ini'
conf = configparser.ConfigParser()
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


def get_testline_info():
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
        tl_port.append(items[1][1])
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
    return tl_info, tl_ip, tl_port, tl_power_off_on_flag, tl_power_off_date, tl_power_off_time, tl_power_on_time, tl_owner, tl_power_off_on_status


def query_pdu(pdu_ip, pdu_port, port_num, pdu_alias='query'):
    ppdu = pdu()
    # pdu_type = 'HBTE'
    if pdu_port == '5000':
        pdu_type = 'HBTE'
    elif pdu_port == '4001':
        pdu_type = 'FACOM'
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


def turn_on_pdu(pdu_ip, pdu_port, port_num, pdu_alias='turnon'):
    ppdu = pdu()
    if pdu_port == '5000':
        pdu_type = 'HBTE'
    elif pdu_port == '4001':
        pdu_type = 'FACOM'
    ppdu.setup_pdu(model=pdu_type, host=pdu_ip, port=pdu_port, alias=pdu_alias)
    ppdu.power_on(port=port_num, pdu_device=pdu_alias)
    time.sleep(2)


def turn_off_pdu(pdu_ip, pdu_port, port_num, pdu_alias='turnoff'):
    ppdu = pdu()
    if pdu_port == '5000':
        pdu_type = 'HBTE'
    elif pdu_port == '4001':
        pdu_type = 'FACOM'
    ppdu.setup_pdu(model=pdu_type, host=pdu_ip, port=pdu_port, alias=pdu_alias)
    ppdu.power_off(port=port_num, pdu_device=pdu_alias)
    time.sleep(2)


# get_testline_info()
# print(query_pdu('10.71.180.173', '4001', '2'))
# turn_off_pdu('10.71.180.173', '4001', '2')
# print(query_pdu('10.71.180.173', '4001', '2'))
# turn_on_pdu('10.71.180.173', '4001', '2')
# print(query_pdu('10.71.180.173', '4001', '2'))
