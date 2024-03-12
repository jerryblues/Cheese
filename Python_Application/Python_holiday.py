import datetime
import holidays


def get_country_holidays(country_code):
    # 创建对应国家的节假日对象
    if country_code == 'FR':
        return holidays.FRA(), 'France'
    elif country_code == 'DE':
        return holidays.DE(), 'Germany'
    elif country_code == 'PL':
        return holidays.PL(), 'Poland'
    elif country_code == 'IN':
        return holidays.IN(), 'India'
    elif country_code == 'FI':
        return holidays.FI(), 'Finland'
    elif country_code == 'CN':
        return holidays.CN(), 'China'
    else:
        return None, None  # 如果国家代码无效，则返回 None


def main():
    # 获取今天的日期
    # today = datetime.date.today()
    # print(today)

    # for test
    today = '2024-04-01'

    # 获取所有国家的节假日信息
    all_countries = ['CN', 'IN', 'DE', 'PL', 'FR', 'FI']
    holiday_info = []  # 创建一个空列表来收集节假日信息
    for country_code in all_countries:
        # 获取指定国家的节假日信息
        country_holidays, country_name = get_country_holidays(country_code)

        if country_holidays is not None:
            # 检查今天是否是指定国家的节假日
            if today in country_holidays:
                # 将节假日信息添加到列表中
                holiday_info.append(f"{country_name}: {country_holidays.get(today)}\n")

    # 打印节假日信息
    if holiday_info:
        print(f"Today is {today}, it's a holiday in\n", ' '.join(holiday_info))
    else:
        print(f"Today is {today}.")


if __name__ == "__main__":
    main()
