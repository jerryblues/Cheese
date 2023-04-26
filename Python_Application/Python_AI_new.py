from bs4 import BeautifulSoup
import requests

# 获取网页源码
# url = 'https://rep-portal.ext.net.nokia.com/reports/qc/?backlog_id=FCA_5G_L2L3-121521&columns=%3Ahash%3A69f2f4be3a1c4957a207ee2a19a875a4&limit=200&ordering=name&path=%3Ahash%3A60211b33616c0de620e99b4f4bbb439f&test_set__name=8311'
url = 'https://codedamn-classrooms.github.io/webscraper-python-codedamn-classroom-website/'
response = requests.get(url)

# 解析HTML文档
soup = BeautifulSoup(response.text, 'html.parser')

# 查找所有的tr标签，并存储它们的第二个td子标签的文本到一个列表中
second_column = []
for row in soup.find_all('tr'):
  cells = row.find_all('td')
  if len(cells) > 1:
    second_column.append(cells[1].text)

# 打印列表
print(second_column)
