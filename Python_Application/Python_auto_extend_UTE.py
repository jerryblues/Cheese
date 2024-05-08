# coding=utf-8
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
import time
import pytz
import re
from retrying import retry
import datetime
import chinese_calendar as calendar


proxies = {
    "http": "http://10.144.1.10:8080",
    "https": "http://10.144.1.10:8080",
}


# 获取今天日期
def today_date():
    t = datetime.date.today()
    year = t.year
    month = t.month
    day = t.day
    print(f"***Today is [{year}],[{month}],[{day}]***")
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

# account = input('>>>>>:').strip()    # 本地调试时注释掉
# password = input('>>>>>:').strip()   # 本地调试时注释掉


account = "h4zhang"
password = "Holmes=-0"

my_reservations = ['https://cloud.ute.nsn-rdnet.net/user/reservations?status=3']
# pending, assigned, confirmed link = [
#                    'https://cloud.ute.nsn-rdnet.net/user/reservations?status=1',
#                    'https://cloud.ute.nsn-rdnet.net/user/reservations?status=2',
#                    'https://cloud.ute.nsn-rdnet.net/user/reservations?status=3'
#                    ]
#  default link: https://cloud.ute.nsn-rdnet.net/reservation/current


# @retry
def get_link(link):
    tl_link = []

    for tl in link:
        chrome_options = ChromeOptions()
        # run chrome in background
        chrome_options.add_argument('--headless')
        # Add the proxy settings to ChromeOptions
        chrome_options.add_argument(f'--proxy-server={proxies}')
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(60)
        driver.get(tl)
        driver.switch_to.window(driver.current_window_handle)
        # driver.find_element(By.label, "Username").clear()
        # driver.find_element(By.label, "Username").send_keys(account)
        # driver.find_element(By.label, "Password").clear()
        # driver.find_element(By.label, "Password").send_keys(password)

        # 定位用户名输入框并输入用户名
        username_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Username']")
        username_input.clear()
        username_input.send_keys("account")

        # 定位密码输入框并输入密码
        password_input = driver.find_element(By.By.CSS_SELECTOR, "input[placeholder='Password']")
        password_input.clear()
        password_input.send_keys("password")

        driver.find_element(By.ID, "id_login_btn").click()
        # wait until all the link updated in the page
        time.sleep(10)
        # find all link in the page
        find_href = driver.find_elements(By.TAG_NAME, 'a')
        # save the link that contain "show" in all the link
        for link in find_href:
            href = link.get_attribute("href")
            if href is not None and "show" in href:
                tl_link.append(href)
        driver.quit()
        # print("Link:", link)
        return tl_link


# @retry
def extend_ute(link):
    for tl in link:
        chrome_options = ChromeOptions()
        chrome_options.add_argument('--headless')
        # Add the proxy settings to ChromeOptions
        chrome_options.add_argument(f'--proxy-server={proxies}')
        driver = webdriver.Chrome(options=chrome_options)

        driver.get(tl)
        print(tl)

        driver.switch_to.window(driver.current_window_handle)
        driver.find_element(By.NAME, "username").clear()
        driver.find_element(By.NAME, "username").send_keys(account)
        driver.find_element(By.NAME, "password").clear()
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.ID, "id_login_btn").click()

        requested_testline_type = driver.find_element(By.XPATH, '//*[@id="topology"]').text
        print("Requested testline type:\n %s" % requested_testline_type)

        screen_text = driver.find_elements(By.XPATH, "/*")
        for lst in screen_text:
            string = lst.text
            if "Reservation status Pending for testline" in lst.text:
                print("*Testline is pending* ...")
            elif "Reservation status Canceled" in lst.text:
                print("*Testline is canceled* -_-")
            elif "Reservation status Testline assigned" in lst.text:
                print("*Testline is assigned* `-`")
            elif "Reservation status Finished" in lst.text:
                print("*Testline is finished* '-'")
            elif "Reservation status Confirmed" in lst.text:
                print("*Testline is confirmed* ^-^")
                driver.find_element(By.ID, "extend-button").click()
            else:
                print("Testline status not available")
        for line in string.split('\n'):
            if re.match(r'Reservation end (.*)', line, re.M | re.I):
                print("Reservation End Time:\n", line[15:])
            if re.match(r'Reservation owner (.*)', line, re.M | re.I):
                print("Reservation Owner:\n", line[17:])
        print("Current Time:\n", datetime.datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S"))
        driver.quit()


script_count = 1
extend_count = 1

while script_count < 9999:
    my_link = get_link(my_reservations)
    print(my_link)
    today = today_date()
    date = datetime.date(today[0], today[1], today[2])
    if is_holiday(date):
        print("***Today is Holiday***")
        print("***Script Running for %s time***\n" % script_count)
        script_count = script_count + 1
        time.sleep(10800)  # sleep 3 hour
    else:
        print("***Today is Working Day***")
        if my_link:
            count = len(my_link)
            print(f"***[{count}] TL reserved***")
            extend_ute(my_link)
            print(f"***UTE extended for [{extend_count}] time***")
            print(f"***Script Running for [{script_count}] time***\n")
            extend_count = extend_count + 1
            script_count = script_count + 1
            time.sleep(2400)
        else:
            print("Link:", my_link)
            print("***UTE not reserved***")
            print(f"***Script Running for [{script_count}] time***\n")
            script_count = script_count + 1
            time.sleep(2400)
