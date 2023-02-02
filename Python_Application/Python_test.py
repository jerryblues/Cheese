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
import smtplib
import datetime
from email.header import Header
from email.mime.text import MIMEText
import urllib.request
import ssl
import time
import socket
from taf.pdu import pdu


from telnetlib import Telnet
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import optparse
import os
import logging
import sys


ssl._create_default_https_context = ssl._create_unverified_context


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
            if self.is_relay_connectable(relay):
                return relay
        raise AssertionError(
            'not find the nokia mail relay from {} '
            'with port {}'.format(
                self.nokia_relays,
                self.relay_port))

    def send_mail(self, receiver, subject, content, format='plain', attachFileList=None):
        receiver = receiver.replace(',', ';')
        sender = self.sender
        message = MIMEMultipart()
        message['From'] = self.sender
        message['To'] = receiver
        subject = subject
        message['Subject'] = Header(subject, 'utf-8')

        message.attach(MIMEText(content, format, 'utf-8'))
        if attachFileList:
            for file in attachFileList:
                att1 = MIMEText(open(file, 'rb').read(), 'base64', 'utf-8')
                att1["Content-Type"] = 'application/octet-stream'
                att1["Content-Disposition"] = 'attachment; filename={}'.format(file)
                message.attach(att1)

        relay = self.choose_nokia_relay()
        smtp = smtplib.SMTP(relay, self.relay_port)
        smtp.sendmail(sender, receiver, message.as_string())
        smtp.quit()
        print('send mail to {} succeed'.format(receiver))


def mail():
    content = urllib.request.urlopen("https://10.57.195.35:8080/TL_status", timeout=500).read()
    MailSender().send_mail(
        receiver='hao.6.zhang@nokia-sbell.com',
        subject='RAN_L3_SW_1_CN_ET - Testline Power Off/On Status',
        content=content, format='html')


# mail()

import random
from retrying import retry
@retry
def random_with_retry():
    if random.randint(0, 10) > 2:
        print("大于2，重试...")
        raise Exception("大于2")
    print("小于2，成功！")


@retry
def retry_ute():
    x = random.randint(0, 3)
    if x == 0:
        print("can not be 0")
        raise Exception("=0")
    print(12 / x)


retry_ute()
