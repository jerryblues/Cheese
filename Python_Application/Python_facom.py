# coding=utf-8
"""
@file: Python_facom.py
@time: 2018/9/5 13:36
@author: h4zhang
"""

from facom_cmd import *
import logging

# from lrclib.base.errors import *

__all__ = ['facom_api_power_on_off', 'facom_api_power_reset']


def facom_api_power_on_off(ip, port, port_num, operation_mode):
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
    fb_obj = OperationOfFacom(ip, port)
    if operation_mode in ['power_on', 'power_off']:
        eval('fb_obj.%s("%s")' % (operation_mode, port_num))
        # else:
        #     raise LrcValidateException('operation_mode = %s is not support, \
        #         it must be power_on or power_off' % operation_mode)


def facom_api_power_reset(ip, port, port_num):
    """
    this API is used to reset the facom equipment
    | Input Parameters | Man | Description |
    | ip | Yes | Ip of facom equipment |
    | port| Yes | Connection port of facom server,1~6 are allowed |
    | port_num | Yes | The power output port number |

    example:
    facom_api_power_rest('10.69.6.32','4001','6')
    """
    log = logging.getLogger(__name__)
    log.info('{},{},{}'.format(ip, port, port_num))
    facom_api_power_on_off(ip, port, port_num, 'power_off')
    import time
    time.sleep(15)
    facom_api_power_on_off(ip, port, port_num, 'power_on')


# TL1009-PB:10.57.247.203 port 2/3, AP IP:10.57.146.136 port 2, DU IP:10.57.146.137 port 3
# TL265 -PB:10.57.242.41  port 2  , DU IP:10.57.233.131
if __name__ == "__main__":
    # facom_api_power_reset("10.57.247.204", 4001, 3)
    # facom_api_power_reset("10.57.247.204", 4001, 2)
    # facom_api_power_on_off("10.57.247.203", 4001, 3, 'power_off')
    # facom_api_power_on_off("10.57.247.203", 4001, 2, 'power_off')
    # facom_api_power_reset("10.57.242.41", 4001, 2)
    facom_api_power_on_off("10.57.247.219", 4001, 1, 'power_on')
    facom_api_power_on_off("10.57.247.218", 4001, 5, 'power_on')
