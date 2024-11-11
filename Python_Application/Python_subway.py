import math

ticket_cost = 7.0  # 单程票价


def method1(total_days):
    total_cost = 0.0  # 初始化为浮点数
    total_rides = total_days * 2.0  # 每天往返，乘车次数为浮点数

    for ride in range(math.ceil(total_rides)):  # 使用 math.ceil() 进行向上取整
        one_way_cost = ticket_cost * 0.9  # 单程来回费用
        # 在每次乘车前检查当前的总费用
        if total_cost >= 100:
            one_way_cost = ticket_cost * 0.5  # 100元后打5折
        elif total_cost >= 50:
            one_way_cost = ticket_cost * 0.7  # 50元后打7折

        total_cost += one_way_cost  # 更新总费用

        # 计算当前天数（每2次乘车为1天）
        current_day = ride // 2  # 向下取整
        print(f"day: {current_day + 1}, one_way_cost: {one_way_cost:.2f}, total_cost: {total_cost:.2f}")

    return total_cost


def method2(total_days):
    one_way_cost = ticket_cost  # 单程来回费用
    total_cost = (one_way_cost - 2.0) * (total_days * 2.0)  # 每天优惠4元，计算往返的总费用
    return total_cost


def compare_methods():
    total_days = 22  # 示例浮点数，工作日天数
    cost_method1 = method1(total_days)
    cost_method2 = method2(total_days)

    print(f"method1 cost: {cost_method1:.2f}")
    print(f"method2 cost: {cost_method2:.2f}")

    if cost_method1 < cost_method2:
        print("-> method1 better")
    elif cost_method1 > cost_method2:
        print("-> method2 better")
    else:
        print("-> the same cost")


if __name__ == "__main__":
    compare_methods()
