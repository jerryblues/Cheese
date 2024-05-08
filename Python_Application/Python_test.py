import requests
import logging


proxies = {
    "http": "http://10.144.1.10:8080",
    "https": "http://10.144.1.10:8080",
}


def ute_login():
    session = requests.Session()
    login_url = 'https://cloud.ute.nsn-rdnet.net/api/v1/auth/login'
    login_data = {'username': 'h4zhang', 'password': 'Holmes=-0'}
    try:
        response = session.post(login_url, json=login_data, proxies=proxies)
        response.raise_for_status()
        logging.info(f"<-- [response]: {response.json()} -->\n")
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


def fetch_csrf_token(session):
    profile_url = 'https://cloud.ute.nsn-rdnet.net/cm/user/settings/profile'
    try:
        # 访问个人资料页面以获取 CSRF token
        response = session.get(profile_url)
        response.raise_for_status()
        # 从 cookies 中提取 CSRF token
        csrftoken = session.cookies.get('csrftoken')
        if csrftoken:
            print(f"Retrieved csrftoken: {csrftoken}")
        else:
            print("csrftoken not found in cookies")
    except requests.exceptions.RequestException as err:
        print(f"Error fetching profile page: {err}")
        return None
    return csrftoken


# 主逻辑
session = ute_login()
if session:
    csrftoken = fetch_csrf_token(session)

