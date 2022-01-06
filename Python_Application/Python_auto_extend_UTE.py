# coding=utf-8
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# account = input('>>>>>:').strip()    # 本地调试时注释掉
# password = input('>>>>>:').strip()   # 本地调试时注释掉

account = "h4zhang"
password = "Holmes0-0"

my_reservations = ['https://cloud.ute.nsn-rdnet.net/user/reservations?status=1',
                   'https://cloud.ute.nsn-rdnet.net/user/reservations?status=2',
                   'https://cloud.ute.nsn-rdnet.net/user/reservations?status=3']
#  default link: https://cloud.ute.nsn-rdnet.net/reservation/current
#  pending, assigned, confirmed


def get_link(link):
    all_link = []
    tmp = []
    my_link = []
    for link in link:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver = webdriver.Chrome(options=chrome_options)

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
            # print(list.text)
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
                reservation_end = driver.find_element_by_xpath(
                    '//*[@id="reservation_show_details"]/div[2]/table/tbody/tr[18]/td[2]').text
                print("Current Reservation End Time:\n %s" % reservation_end)
            else:
                print("Testline status not available")
        print("Current Time:\n", time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
        driver.quit()


count = 1
link = get_link(my_reservations)
if not link:
    print("*Testline has not been reserved*")
    exit(0)
else:
    while count < 255:
        extend_ute(link)
        print("***Script Running for %s time***\n" % count)
        count = count + 1
        time.sleep(3500)
        link = get_link(my_reservations)
    else:
        print("***Script End***")
