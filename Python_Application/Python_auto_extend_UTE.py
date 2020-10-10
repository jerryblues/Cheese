# coding=utf-8
from typing import List, Any, Union

from selenium import webdriver
import time

account = "h4zhang"
password = "Holmes--0"


def extend_ute():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get("https://cloud.ute.nsn-rdnet.net/reservation/current")

    url = driver.current_window_handle
    driver.switch_to.window(url)

    driver.find_element_by_name("username").clear()
    driver.find_element_by_name("username").send_keys(account)
    driver.find_element_by_name("password").clear()
    driver.find_element_by_name("password").send_keys(password)
    driver.find_element_by_id("id_login_btn").click()

    time.sleep(1)
    driver.find_element_by_id("extend-button").click()

    reservation_end = driver.find_element_by_xpath(
        '//*[@id="reservation_show_details"]/div[2]/table/tbody/tr[18]/td[2]').text
    print("Current Reservation End Time:\n %s" % reservation_end)

    time.sleep(1)
    driver.quit()


count = 1
while count < 10:
    extend_ute()
    print("*UTE Extended for %s time*" % count)
    count = count + 1
    time.sleep(3000)
else:
    print("***UTE Extended End***")
