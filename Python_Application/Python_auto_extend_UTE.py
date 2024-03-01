# coding=utf-8
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import pytz
import re
from retrying import retry
import datetime
import chinese_calendar as calendar


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
        return True
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


@retry
def get_link(link):
    tl_link = []

    for tl in link:
        chrome_options = Options()
        # run chrome in background
        chrome_options.add_argument('--headless')
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(60)
        driver.get(tl)
        driver.switch_to.window(driver.current_window_handle)
        driver.find_element_by_name("username").clear()
        driver.find_element_by_name("username").send_keys(account)
        driver.find_element_by_name("password").clear()
        driver.find_element_by_name("password").send_keys(password)
        driver.find_element_by_id("id_login_btn").click()
        # wait until all the link updated in the page
        time.sleep(10)
        # find all link in the page
        find_href = driver.find_elements_by_tag_name('a')
        # save the link that contain "show" in all the link
        for link in find_href:
            href = link.get_attribute("href")
            if href is not None and "show" in href:
                tl_link.append(href)
        driver.quit()
        # print("Link:", link)
        return tl_link


@retry
def extend_ute(link):
    for tl in link:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver = webdriver.Chrome(options=chrome_options)

        driver.get(tl)
        print(tl)

        driver.switch_to.window(driver.current_window_handle)
        driver.find_element_by_name("username").clear()
        driver.find_element_by_name("username").send_keys(account)
        driver.find_element_by_name("password").clear()
        driver.find_element_by_name("password").send_keys(password)
        driver.find_element_by_id("id_login_btn").click()

        requested_testline_type = driver.find_element_by_xpath(
            '//*[@id="topology"]').text
        print("Requested testline type:\n %s" % requested_testline_type)

        screen_text = driver.find_elements_by_xpath("/*")
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
                driver.find_element_by_id("extend-button").click()
                # reservation_end = driver.find_element_by_xpath(
                #     '//*[@id="reservation_show_details"]/div[2]/table/tbody/tr[18]/td[2]').text
                # print("Current Reservation End Time:\n %s" % reservation_end)
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
