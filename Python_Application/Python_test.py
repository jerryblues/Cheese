import datetime
import chinese_calendar as calendar


def is_workday(date):
    """
    判断日期是否是工作日
    """
    if calendar.is_holiday(date):
        return "Holiday"
    else:
        return "Working Day"


# 测试代码
if __name__ == '__main__':
    date = datetime.date(2023, 4, 23)
    print(is_workday(date))
