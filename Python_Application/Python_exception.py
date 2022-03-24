# coding=utf-8
from jira import JIRA
import pandas as pd
from flask import Flask, render_template
from datetime import datetime
import pytz
import logging
from collections import Counter
import datetime

"""
@file: Python_exception.py.py
@time: 2022/1/5 13:29
@author: h4zhang
"""
from facom_cmd import *


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


facom_api_power_on_off("10.71.182.172", port=4001, port_num=3, operation_mode="power_on")
