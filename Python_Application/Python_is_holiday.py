import datetime
import chinese_calendar as calendar


# 获取今天日期
def today_date():
    t = datetime.date.today()
    year = t.year
    month = t.month
    day = t.day
    print(f"今天是{year}年{month}月{day}日")
    return year, month, day


def is_holiday(d):
    """
    判断日期是否是休息日
    """
    if calendar.is_holiday(d):
        print("Holiday")
        return True
    else:
        print("Working Day")
        return False


today = today_date()
date = datetime.date(today[0], today[1], today[2])
is_holiday(date)
