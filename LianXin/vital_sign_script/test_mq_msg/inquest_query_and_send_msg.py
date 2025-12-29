import json
import time
import requests
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# RocketMQ 配置
ROCKETMQ_DASHBOARD_URL = "http://10.1.120.27:8080"
TOPIC = "physiology-Topic"
KEY = "key"
TAG = "tag"

# 消息内容配置
MESSAGE_TEMPLATE = {
    "bpm": 39,  # 手动配置需要发送的心跳数值
    "person_id": "1",
    "breathe": 19,  # 手动配置需要发送的呼吸数值
    "hrv": None,
    "timestamp": int(time.time() * 1000),  # 当前时间戳（毫秒）
    "trial_id": "22025073118495400685"   # 审讯ID默认值
}


# 是否自动获取 trial_id（审讯ID）
AUTO_GET_TRIAL_ID = True  # 设为False则使用上面配置的默认值，True则通过 get_trial_id 获取最新一条id

# 发送间隔（秒）
SEND_INTERVAL = 1

# 发送次数配置（设为 None 表示无限发送）
MAX_SEND_COUNT = 2


def send_message_to_rocketmq(topic, key, tag, message_body, trace_enabled=False):
    url = f"{ROCKETMQ_DASHBOARD_URL}/topic/sendTopicMessage.do"
    
    # 将消息内容转换为JSON字符串
    message_body_str = json.dumps(message_body)
    
    payload = {
        "topic": topic,
        "key": key,
        "tag": tag,
        "messageBody": message_body_str,
        "traceEnabled": trace_enabled
    }
    
    try:
        print(f"访问URL: {url}")
        print(f"请求参数: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(url, json=payload, timeout=10)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == 0:
                print(f"消息发送成功: {result}")
                return True
            else:
                print(f"消息发送失败: {result}")
                return False
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            return False
    except Exception as e:
        print(f"发送消息时发生错误: {e}")
        return False


def generate_message(template):
    """
    生成消息，更新时间戳和trial_id
    Args:
        template (dict): 消息模板
    Returns:
        dict: 更新后的消息
    """
    message = template.copy()
    message["timestamp"] = int(time.time() * 1000)  # 更新时间戳为当前时间（毫秒）
    
    if AUTO_GET_TRIAL_ID:
        message["trial_id"] = get_trial_id()  # 自动获取最新一条审讯ID
    # 如果AUTO_GET_TRIAL_ID为False，则使用配置中的默认值
    
    return message


def start_sending_messages():
    """
    开始循环定时发送消息
    """
    print(f"开始发送消息到 {TOPIC}，间隔 {SEND_INTERVAL} 秒")
    
    if MAX_SEND_COUNT is not None:
        print(f"将发送 {MAX_SEND_COUNT} 次后自动停止")
    else:
        print(f"无限发送模式，按 Ctrl+C 停止发送")
    
    try:
        sent_count = 0
        while MAX_SEND_COUNT is None or sent_count < MAX_SEND_COUNT:
            # 生成消息
            message = generate_message(MESSAGE_TEMPLATE)
            
            # 发送消息
            success = send_message_to_rocketmq(
                topic=TOPIC,
                key=KEY,
                tag=TAG,
                message_body=message,
                trace_enabled=False
            )
            
            # 更新发送计数
            if success:
                sent_count += 1
                if MAX_SEND_COUNT is not None:
                    print(f"已发送 {sent_count}/{MAX_SEND_COUNT} 条消息")
                else:
                    print(f"已发送 {sent_count} 条消息")
            
            # 检查是否达到最大发送次数
            if MAX_SEND_COUNT is not None and sent_count >= MAX_SEND_COUNT:
                print(f"\n已达到最大发送次数 {MAX_SEND_COUNT}，停止发送")
                break
            
            # 等待指定的间隔时间
            time.sleep(SEND_INTERVAL)
    except KeyboardInterrupt:
        print(f"\n已发送 {sent_count} 条消息，手动停止发送")


def get_trial_id():
    query_url = "https://pip-test.shangjin618.com/api/lianxin-sis/policeTrial/queryTrialPage"
    
    headers = {
        'Authorization': 'eyJhbGciOiJIUzUxMiJ9.eyJhY2NvdW50X2lkIjpudWxsLCJhdXRob3JpemVfaWQiOm51bGwsInVzZXJfaWQiOiIxIiwicGxpbmsiOm51bGwsInRoaXJkX3VzZXJfaWQiOm51bGwsInVzZXJfa2V5IjoiMzJhYmNiYjQtZDNjNy00ZDRlLThlZWYtY2IwYjI3ZmQwMGM4IiwiZGVwdF9pZF9saXN0IjpudWxsLCJkZXB0X2lkIjpudWxsLCJhcHBfaWQiOm51bGwsInBsaW5rX2xpc3QiOm51bGwsInVzZXJuYW1lIjoiYWRtaW4iLCJ0ZW5hbnRfY29kZSI6IkxYX1NYIn0.BSfDQX62tdJTvwNNQnC0ATX_650UdbCTbxjM9xkkaqA4ZEywkqmjIlf7X37MIRnKicrgwfxzDVFSG3-FGJm4cw',
   }
    
    # 请求消息体
    payload = {
        "id": "",
        "idCard": "",
        "caseNumber": "",
        "gender": "",
        "userName": "",
        "caseHandlingPolice": "",
        "occurDate": "",
        "deviceCode": "",
        "inquiryDate": "",
        "inquestAddress": "",
        "channel": "LX",
        "trialType": "",
        "page": 1,
        "pageSize": 10,
        "status": 1
    }
    
    try:
        response = requests.post(
            query_url, 
            headers=headers, 
            json=payload, 
            verify=False, 
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查返回的数据结构
            if data.get("code") == "200" and data.get("data") and data.get("data").get("list"):
                first_record = data["data"]["list"][0]
                trial_id = first_record.get("id")
                if trial_id:
                    print(f"✅ 成功获取trial_id: {trial_id}")
                    return trial_id
                else:
                    print("⚠️ 返回数据中未找到id字段")
                    return MESSAGE_TEMPLATE["trial_id"]
            else:
                print("⚠️ API返回数据格式不正确或无数据")
                print(f"返回数据: {data}")
                return MESSAGE_TEMPLATE["trial_id"]
        else:
            print(f"❌ 查询失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return MESSAGE_TEMPLATE["trial_id"]
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时，使用默认trial_id")
        return MESSAGE_TEMPLATE["trial_id"]
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，使用默认trial_id")
        return MESSAGE_TEMPLATE["trial_id"]
    except Exception as e:
        print(f"❌ 获取trial_id时出错: {str(e)}，使用默认trial_id")
        return MESSAGE_TEMPLATE["trial_id"]


def test_connection():
    """
    测试RocketMQ Dashboard连接
    """
    print("测试RocketMQ Dashboard连接...")
    try:
        response = requests.get(f"{ROCKETMQ_DASHBOARD_URL}/", timeout=5)
        print(f"Dashboard响应状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ RocketMQ Dashboard连接成功")
            return True
        else:
            print(f"❌ Dashboard连接失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到RocketMQ Dashboard: {e}")
        return False

if __name__ == "__main__":
    # 配置说明：
    # 1. AUTO_GET_TRIAL_ID=True: 自动从审讯系统获取trial_id
    #    - 使用POST方法和Authorization认证
    #    - 如果获取失败，会使用MESSAGE_TEMPLATE中的trial_id值
    # 2. AUTO_GET_TRIAL_ID=False: 使用MESSAGE_TEMPLATE中配置的固定值
    
    print("=== query trial id and send mq message ===")
    
    # 开始发送消息
    if test_connection():
        start_sending_messages()
