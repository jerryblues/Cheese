# coding=utf-8
"""
@file: Python_test.py.py
@time: 2022/3/24 16:43
@author: h4zhang
"""

import smtplib
import datetime
from email.header import Header
from email.mime.text import MIMEText
import urllib.request
import re

str = """Details
ID 5faa1b36-c278-4fa8-aa3e-fe77e70cfb41
Reservation owner Nan Xiao Ge
Shared with Hao Zhang
Reservation status Confirmed
Testline user ute
Testline password Nokia_123456
Requested topology CLOUD_5G_I_BLLL_AP_KLLL_SANSA_L1B_ECPRI_CMWV_TDD
Tags CLOUD_5G_I_BLLL_AP_KLLL_SANSA_L1B_ECPRI_CMWV_TDD, 5G_RAN
Requested duration 1h
Requested build SBTS00_ENB_9999_220514_000022
Requested sysimage utevm_debian10_64bit_202109211335.qcow2.tar.gz
Requested ute-4g 2219.02.00
Requested airphone 5G_4.0.20845
Requested test repository revision 0f82c7c5d00741df21b69b4ddb139834a5ff1118
Requested BTS state configured
Postpone to 17 May 2022, 6:00 a.m.
Waiting time 04h 03m 37s
Reservation start 17 May 2022, 10:03 a.m.
Reservation end 17 May 2022, 7:03 p.m."""

for line in str.split('\n'):
    if re.match(r'Reservation end [0-9]{2}(.*)', line, re.M | re.I):
        print("Current Reservation End Time:\n", line[16:])



# if re.match(r'Reservation end [0-9]{2}(.*)', str, re.M | re.I):
#     print("yes")
# else:
#     print("no")

# def send_reportContent(subject, sender, receivers_to, receivers_cc, html):
#     message = MIMEText(html, 'html', 'utf-8')
#     message['From'] = Header(sender.split('@')[0], 'utf-8')
#     message['Cc'] = receivers_cc
#     message['To'] = receivers_to
#     message['Subject'] = Header(subject, 'utf-8')
#     server = smtplib.SMTP('172.24.146.151')
#     server.sendmail(sender, receivers_to.split(','), message.as_string())
#
#
# def getHtml(url):
#     html = urllib.request.urlopen(url).read()
#     return html
#
#
# sender_email = r"hao.6.zhang@nokia-sbell.com"
# receiver_email = r"hao.6.zhang@nokia-sbell.com, youyong.zheng@nokia-sbell.com"
# receiver_cc_email = r"hao.6.zhang@nokia-sbell.com"
# today = str(datetime.date.today())
# subject = f'ET team - Testline Power Off/On status - {today}'
#
# html = getHtml("http://10.57.209.188:5000/TL_status")
#
# send_reportContent(subject=subject, sender=sender_email, receivers_to=receiver_email, receivers_cc=receiver_cc_email,
#                    html=html)
