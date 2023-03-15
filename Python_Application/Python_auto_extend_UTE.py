# coding=utf-8
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import time
import pytz
import re
from retrying import retry

# account = input('>>>>>:').strip()    # 本地调试时注释掉
# password = input('>>>>>:').strip()   # 本地调试时注释掉

account = "h4zhang"
password = "Holmes-09"

my_reservations = ['https://cloud.ute.nsn-rdnet.net/user/reservations?status=1',
                   'https://cloud.ute.nsn-rdnet.net/user/reservations?status=2',
                   'https://cloud.ute.nsn-rdnet.net/user/reservations?status=3']
#  default link: https://cloud.ute.nsn-rdnet.net/reservation/current
#  pending, assigned, confirmed


@retry
def get_link(link):
    all_link = []
    tmp = []
    my_link = []

    for link in link:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(60)
        driver.get(link)
        driver.switch_to.window(driver.current_window_handle)
        driver.find_element_by_name("username").clear()
        driver.find_element_by_name("username").send_keys(account)
        driver.find_element_by_name("password").clear()
        driver.find_element_by_name("password").send_keys(password)

        driver.find_element_by_id("id_login_btn").click()
        time.sleep(1)

        find_href = driver.find_elements_by_tag_name('a')
        for link in find_href:
            all_link.append(link.get_attribute("href"))
        driver.quit()

    for i in all_link:
        if i != None:
            tmp.append(i)
    str = 'show'
    for j in tmp:
        if str in j:
            my_link.append(j)
    return my_link


@retry
def extend_ute(link):
    for link in link:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver = webdriver.Chrome(options=chrome_options)

        driver.get(link)
        print(link)

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
        for list in screen_text:
            s = list.text
            if "Reservation status Pending for testline" in list.text:
                print("*Testline is pending* ...")
            elif "Reservation status Canceled" in list.text:
                print("*Testline is canceled* -_-")
            elif "Reservation status Testline assigned" in list.text:
                print("*Testline is assigned* `-`")
            elif "Reservation status Finished" in list.text:
                print("*Testline is finished* '-'")
            elif "Reservation status Confirmed" in list.text:
                print("*Testline is confirmed* ^-^")
                driver.find_element_by_id("extend-button").click()
                # reservation_end = driver.find_element_by_xpath(
                #     '//*[@id="reservation_show_details"]/div[2]/table/tbody/tr[18]/td[2]').text
                # print("Current Reservation End Time:\n %s" % reservation_end)
            else:
                print("Testline status not available")
        for line in s.split('\n'):
            if re.match(r'Reservation end (.*)', line, re.M | re.I):
                print("Reservation End Time:\n", line[15:])
            if re.match(r'Reservation owner (.*)', line, re.M | re.I):
                print("Reservation Owner:\n", line[17:])
        print("Current Time:\n", datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S"))
        driver.quit()


script_count = 1
extend_count = 1
while script_count < 9999:
    link = get_link(my_reservations)
    if link:
        extend_ute(link)
        print("***UTE extended for %s time***" % extend_count)
        print("***Script Running for %s time***\n" % script_count)
        extend_count = extend_count + 1
        script_count = script_count + 1
        time.sleep(2400)
    else:
        print("***UTE not reserved***")
        print("***Script Running for %s time***\n" % script_count)
        script_count = script_count + 1
        time.sleep(2400)

'''
count = 1
while count < 9999:
    try:
        link = get_link(my_reservations)
    except:
        link = get_link(my_reservations)
    else:
        if link:
            try:
                extend_ute(link)
            except:
                extend_ute(link)
            else:
                print("***Script Running for %s time***\n" % count)
                count = count + 1
                time.sleep(2400)
        else:
            print("***Testline has not been reserved***")
            count = count + 1
            time.sleep(2400)
'''