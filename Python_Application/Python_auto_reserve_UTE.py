# coding=utf-8

from selenium import webdriver
import time

#to be done

account = "h4zhang"
password = "Holmes--0"
testline_type = "CLOUD_5G_KL_AP_SA_L1B_CMWV"


def extend_ute():
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get("https://cloud.ute.nsn-rdnet.net/reservation/create")

    url = driver.current_window_handle
    driver.switch_to.window(url)

    driver.find_element_by_name("username").clear()
    driver.find_element_by_name("username").send_keys(account)
    time.sleep(0.5)
    driver.find_element_by_name("password").clear()
    driver.find_element_by_name("password").send_keys(password)
    driver.find_element_by_id("id_login_btn").click()

    time.sleep(0.5)
    driver.find_element_by_xpath(
        '//*[@id="mat-tab-label-0-1"]/div').click()
    time.sleep(1)
    driver.find_element_by_xpath(
        '//*[@id="mat-select-2"]/div/div[1]/span/span').click()



    time.sleep(1)
    driver.quit()

extend_ute()

# count = 1
# while count < 9:
#     extend_ute()
#     print("UTE Extended for %s time" % count)
#     count = count + 1
#     time.sleep(3000)
# else:
#     print("UTE Extended End")
