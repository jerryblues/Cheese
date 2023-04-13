import datetime
import chinese_calendar as calendar


def is_workday(date):
    """
    判断日期是否是工作日
    """
    # 判断是否是周六周日
    if date.weekday() >= 5:
        return False
    # 判断是否是节假日
    return not calendar.is_holiday(date)


# 测试代码
if __name__ == '__main__':
    date = datetime.date(2023, 4, 5)
    print(is_workday(date))
