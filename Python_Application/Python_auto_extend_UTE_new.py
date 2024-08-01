import requests
import json
import logging
import time
import pytz
import re
import datetime as dt
import chinese_calendar as calendar
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta


logging.basicConfig(level=logging.INFO,
                    filename='auto_extend_ute.log',
                    filemode='a',
                    format='%(asctime)s - %(levelname)s: %(message)s'
                    )

proxies = {
    "http": "http://10.144.1.10:8080",
    "https": "http://10.144.1.10:8080",
}

# 全局变量存储上次的数据
last_tl_ids = []
last_end_times = []


# 获取今天日期
def today_date():
    t = dt.date.today()
    year = t.year
    month = t.month
    day = t.day
    logging.info(f"<-- [today] is [{year}][{month}][{day}] -->")
    return year, month, day


def is_holiday(d):
    """
    判断日期是否是休息日
    """
    if calendar.is_holiday(d):
        # print("Holiday")
        return True  # True = not extend in weekend
    else:
        # print("Working Day")
        return False


def ute_login():
    session = requests.Session()
    login_url = 'https://cloud.ute.nsn-rdnet.net/api/v1/auth/login'
    login_data = {'username': 'xxx', 'password': 'xxx'}
    try:
        response = session.post(login_url, json=login_data, proxies=proxies)
        response.raise_for_status()
        logging.info(f"<-- [response]: {response.json()} -->")
        # print("session.cookies:", session.cookies)
    except requests.exceptions.HTTPError as errh:
        logging.info(f"<-- http rrror: {errh} -->")
    except requests.exceptions.ConnectionError as errc:
        logging.info(f"<-- error connecting: {errc} -->")
    except requests.exceptions.Timeout as errt:
        logging.info(f"<-- timeout error: {errt} -->")
    except requests.exceptions.RequestException as err:
        logging.info(f"<-- [oops]: something else {err} -->")
    return session


def get_csrf_token(session):
    profile_url = 'https://cloud.ute.nsn-rdnet.net/cm/user/settings/profile'
    try:
        # 访问个人资料页面以获取 CSRF token
        response = session.get(profile_url, proxies=proxies)
        response.raise_for_status()
        # 从 cookies 中提取 CSRF token
        csrf_token = session.cookies.get('csrftoken')
        if csrf_token:
            logging.info(f"<-- [csrftoken]: {csrf_token} -->\n")
        else:
            logging.info("<-- csrftoken not found in cookies -->")
    except requests.exceptions.RequestException as err:
        logging.info(f"<-- error get profile page: {err} -->")
        return None
    return csrf_token


def ute_extend(session, ute_testline_id, token):
    token_backup = 'JHa92uY9xCpXdvoITxHziNvdE3Ih0w596bVgtA9V2dfpdEw0BT20nq2yueKmDDwS'
    if token:
        session.cookies.set('csrftoken', token, domain='cloud.ute.nsn-rdnet.net')
    else:
        session.cookies.set('csrftoken', token_backup, domain='cloud.ute.nsn-rdnet.net')
    # url should contain /extend
    url = 'https://cloud.ute.nsn-rdnet.net/reservation/' + ute_testline_id + '/extend'
    testline_url = 'https://cloud.ute.nsn-rdnet.net/reservation/' + ute_testline_id + '/show'
    logging.info(f"<-- [testline_url]: {testline_url} -->")
    headers = {
        'X-CSRFToken': token
    }
    request_data = {
        "duration": 60
    }
    try:
        response = session.post(url, headers=headers, data=request_data, proxies=proxies)
        logging.info(f"<-- [status_code]: {response.status_code} -->")  # 打印状态码
        # print("Response Text:", response.text)  # 打印响应文本内容
        response.raise_for_status()
        if response.text:  # 检查响应是否为空
            logging.info(f"<-- response: {response.json()} -->")
        else:
            logging.info(f"<-- empty response -->")
    except requests.exceptions.HTTPError as errh:
        logging.info(f"<-- http error: {errh} -->")
    except requests.exceptions.ConnectionError as errc:
        logging.info(f"<-- error connecting: {errc} -->")
    except requests.exceptions.Timeout as errt:
        logging.info(f"<-- timeout error: {errt} -->")
    except requests.exceptions.RequestException as err:
        logging.info(f"<-- [oops]: something else {err} -->")


def ute_get_reservations(session):
    # get below url from https://cloud.ute.nsn-rdnet.net/cm/user/reservations?status=3 with "cm"
    url = 'https://cloud.ute.nsn-rdnet.net/user/reservations/ajax?limit=30&offset=0&ordering=-add_date&status=3'
    try:
        response = session.get(url, proxies=proxies)
        response.raise_for_status()  # 检查响应状态码，如果是 4XX 或 5XX 将抛出异常
        return response.text  # 返回网页内容
    except requests.exceptions.HTTPError as errh:
        logging.info(f"<-- http error: {errh} -->")
    except requests.exceptions.ConnectionError as errc:
        logging.info(f"<-- error connecting: {errc} -->")
    except requests.exceptions.Timeout as errt:
        logging.info(f"<-- timeout error: {errt} -->")
    except requests.exceptions.RequestException as err:
        logging.info(f"<-- [oops]: something else {err} -->")


def time_zone_switch(time_str, hours=8):
    # 定义日期时间的格式
    date_format = "%b %d, %Y, %I:%M %p"
    # 解析日期时间字符串
    dt = datetime.strptime(time_str, date_format)
    # 添加指定的小时数
    new_dt = dt + timedelta(hours=hours)
    # 返回新的时间字符串
    return new_dt.strftime(date_format)


def ute_get_tl_detail(response_data):
    global last_tl_ids, last_end_times
    uuids = []
    end_dates = []
    topology_names = []
    usernames = []
    statuses = []
    extended_results = []
    if response_data is not None:
        # 将 JSON 字符串解析为 Python 字典
        data = json.loads(response_data)

        # 遍历结果列表，提取每个项的相关字段
        for item in data['results']:
            uuids.append(item['uuid'])
            end_dates.append(time_zone_switch(item['end_date']))
            topology_names.append(item['topology_name'])
            usernames.append(item['username'])
            if item['status'] == 3:
                statuses.append('confirmed')
            else:
                statuses.append(item['status'])

        # 进行数据比较
        extended_results = is_extended(last_tl_ids, last_end_times, uuids, end_dates)
        # print("Results:", len(extended_results), extended_results)
        # 更新存储的上次数据
        last_tl_ids, last_end_times = uuids, end_dates

    else:
        logging.info(f"<-- error: get response_data={response_data} -->")
    return uuids, end_dates, topology_names, usernames, statuses, extended_results


def is_extended(old_tl_ids, old_end_times, new_tl_ids, new_end_times):
    is_extended_results = []
    old_data = dict(zip(old_tl_ids, old_end_times))
    for new_id, new_end_time in zip(new_tl_ids, new_end_times):
        if new_id in old_data:
            if old_data[new_id] != new_end_time:
                is_extended_results.append('extended')
            else:
                is_extended_results.append('not extended')
        else:
            is_extended_results.append('new testline')
    return is_extended_results


def start_extend():
    today = today_date()
    date = dt.date(today[0], today[1], today[2])
    if is_holiday(date):
        logging.info(f"<-- [today] is holiday -->")
    else:
        logging.info(f"<-- [today] is working day -->")
        ute_session = ute_login()
        page_content = ute_get_reservations(ute_session)
        ute_tl_ids, end_date, topology_name, username, status, extended_result = ute_get_tl_detail(page_content)
        # get csrf_token
        csrf_token = get_csrf_token(ute_session)
        for ute_tl_id, e_date, t_name, u_name, stats, result in zip(ute_tl_ids, end_date, topology_name, username, status, extended_result):
            ute_extend(ute_session, ute_tl_id, csrf_token)
            logging.info(f"<-- [testline_id]: {ute_tl_id} -->")
            logging.info(f"<-- [end_time]: {e_date} -->")
            logging.info(f"<-- [topology]: {t_name} -->")
            logging.info(f"<-- [username]: {u_name} -->")
            logging.info(f"<-- [status]: {stats} -->")
            logging.info(f"<-- [result]: {result} -->\n")
        total_testline = len(extended_result)
        extended_count = extended_result.count('extended')
        logging.info(f"<-- [{total_testline}] testline in total, [{extended_count}] extended -->\n")


start_extend()

# scheduler = BlockingScheduler()
# # scheduler.add_job(start_extend, 'cron', day_of_week='0-6', minute='0', timezone="Asia/Shanghai")
# scheduler.add_job(start_extend, 'interval', minutes=50)
# scheduler.start()
