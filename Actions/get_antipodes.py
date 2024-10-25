import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


# 使用 Nominatim 获取城市名称，尝试获取更大范围内的地区名
def get_city_name(lat, lon):
    geolocator = Nominatim(user_agent="city_locator")
    try:
        location = geolocator.reverse((lat, lon), timeout=10)
        if location:
            city = location.raw['address'].get('city')
            town = location.raw['address'].get('town')
            village = location.raw['address'].get('village')

            if city:
                return city
            elif town:
                return town
            elif village:
                return village
            else:
                state = location.raw['address'].get('state')
                country = location.raw['address'].get('country')
                return f"{state}, {country}" if state else country
    except (GeocoderTimedOut, GeocoderServiceError):
        print("地理编码服务超时或不可用，请稍后重试。")

    return None


# 计算对跖点的经纬度
def get_antipodal_point(lat, lon):
    antipodal_lat = -lat
    antipodal_lon = lon + 180 if lon < 0 else lon - 180
    return antipodal_lat, antipodal_lon


# 获取输入城市的经纬度
def get_coordinates(city_name):
    geolocator = Nominatim(user_agent="city_locator")
    retries = 3
    for attempt in range(retries):
        try:
            location = geolocator.geocode(city_name, timeout=10)
            if location:
                return location.latitude, location.longitude
        except (GeocoderTimedOut, GeocoderServiceError):
            print("地理编码服务超时，正在重试...")
            time.sleep(1)  # 等待 1 秒后重试
    return None


def main():
    city_name = input("请输入中国城市名（如：北京、上海等）：")
    coordinates = get_coordinates(city_name)

    if coordinates:
        lat, lon = coordinates
        print(f"{city_name} 的经纬度为：{lat}, {lon}")

        # 获取对跖点的坐标
        antipodal_point = get_antipodal_point(lat, lon)
        print(f"{city_name} 的对跖点坐标为：{antipodal_point}")

        # 获取对跖点的城市名称
        antipodal_city_name = get_city_name(*antipodal_point)

        if antipodal_city_name:
            print(f"对跖点的城市名称为：{antipodal_city_name}")
        else:
            print("未找到对跖点的城市名称。")
    else:
        print("未找到该城市，请检查输入。")


if __name__ == "__main__":
    main()
