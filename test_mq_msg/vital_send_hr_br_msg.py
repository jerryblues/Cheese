import json
import time
import requests

# 全局配置变量
PERSON_ID = 10086
TASK_ID = "53@53"
HEART_RATE_TASK_ID = "53"
HEART_RATE = 39
BREATHE = 10
HEART_RATE_SEND_COUNT = 15      # 发送次数
HEART_RATE_SEND_INTERVAL = 2   # 发送间隔（秒）
BODY_URL = "https://file.shangjinuu.com/images/trial/%E5%B9%B3%E9%9D%99.png"
IMG_URL = "https://file.shangjinuu.com/images/trial/%E5%B9%B3%E9%9D%99.png"
POST_URL = "http://10.1.120.27:8120/vital-sign/vital/signs/sendMq"

# 动作配置 - 两组不同的动作组合
ACTIVE_ACTIONS_1 = {
    "fall_down": False,      # 摔倒
    "hand_on_chest": False,  # 手捂胸口
    "others_pose": False,   # 其他姿势
    "bending_over": False,  # 弯腰
    "convulsion": False,    # 抽搐
    "rush_wall": False      # 撞墙
}

ACTIVE_ACTIONS_2 = {
    "fall_down": False,     # 摔倒
    "hand_on_chest": False,  # 捂胸口
    "others_pose": False,   # 其他姿势
    "bending_over": False,  # 弯腰
    "convulsion": False,    # 抽搐
    "rush_wall": False      # 撞墙
}


def send_person_enter():
    # 获取当前时间戳（毫秒）
    timestamp = int(time.time() * 1000)
    
    # 构造检测到有人消息
    payload = {
        "message_type": 3,
        "results": [
            {
                "person_id": PERSON_ID,
                "body_url": BODY_URL,
                "body_still": False
            }
        ],
        "timestamp": timestamp,
        "task_id": TASK_ID
    }
    
    # 发送POST请求
    url = POST_URL
    
    try:
        print("正在发送检测到有人消息...")
        print(f"请求URL: {url}")
        print(f"请求参数: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(url, json=payload)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 检测到人员消息发送成功")
            return True
        else:
            print(f"❌ 检测到人员消息发送失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 发送检测到人员消息时出错: {str(e)}")
        return False


def send_vital_sign_action():
    # 获取当前时间戳（毫秒）
    timestamp = int(time.time() * 1000)
    
    # 构造第一个动作检测消息
    result1 = {
        "others_pose": ACTIVE_ACTIONS_1.get("others_pose", False),
        "bending_over": ACTIVE_ACTIONS_1.get("bending_over", False),
        "hand_on_chest": ACTIVE_ACTIONS_1.get("hand_on_chest", False),
        "convulsion": ACTIVE_ACTIONS_1.get("convulsion", False),
        "fall_down": ACTIVE_ACTIONS_1.get("fall_down", False),
        "rush_wall": ACTIVE_ACTIONS_1.get("rush_wall", False),
        "person_id": PERSON_ID
    }
    
    # 构造第二个动作检测消息
    result2 = {
        "others_pose": ACTIVE_ACTIONS_2.get("others_pose", False),
        "bending_over": ACTIVE_ACTIONS_2.get("bending_over", False),
        "hand_on_chest": ACTIVE_ACTIONS_2.get("hand_on_chest", False),
        "convulsion": ACTIVE_ACTIONS_2.get("convulsion", False),
        "fall_down": ACTIVE_ACTIONS_2.get("fall_down", False),
        "rush_wall": ACTIVE_ACTIONS_2.get("rush_wall", False),
        "person_id": PERSON_ID
    }
    
    url = POST_URL
    
    try:
        # 发送第一个动作检测消息
        payload1 = {
            "message_type": 4,
            "results": [result1],
            "timestamp": timestamp,
            "task_id": TASK_ID
        }
        
        active_actions1 = [k for k, v in ACTIVE_ACTIONS_1.items() if v]
        print(f"正在发送第一个动作检测消息，激活的动作: {active_actions1}")
        print(f"请求URL: {url}")
        print(f"请求参数: {json.dumps(payload1, indent=2, ensure_ascii=False)}")
        
        response1 = requests.post(url, json=payload1)
        print(f"响应状态码: {response1.status_code}")
        print(f"响应内容: {response1.text}")
        
        if response1.status_code != 200:
            print(f"❌ 第一个动作检测消息发送失败，状态码: {response1.status_code}")
            return False
        
        # 发送第二个动作检测消息
        payload2 = {
            "message_type": 4,
            "results": [result2],
            "timestamp": timestamp + 1000,  # 加1秒，模拟时间差异
            "task_id": TASK_ID
        }
        
        active_actions2 = [k for k, v in ACTIVE_ACTIONS_2.items() if v]
        print(f"\n正在发送第二个动作检测消息，激活的动作: {active_actions2}")
        print(f"请求URL: {url}")
        print(f"请求参数: {json.dumps(payload2, indent=2, ensure_ascii=False)}")
        
        response2 = requests.post(url, json=payload2)
        print(f"响应状态码: {response2.status_code}")
        print(f"响应内容: {response2.text}")
        
        if response2.status_code == 200:
            print("✅ 两个动作检测消息都发送成功")
            return True
        else:
            print(f"❌ 第二个动作检测消息发送失败，状态码: {response2.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 发送消息时出错: {str(e)}")
        return False

def send_hr_br():
    """发送心率消息（在30秒内按配置次数和间隔发送）"""
    url = POST_URL
    total_count = HEART_RATE_SEND_COUNT
    interval = HEART_RATE_SEND_INTERVAL
    
    print(f"=== 开始发送心率消息，将在30秒内发送 {total_count} 次，间隔 {interval} 秒 ===")
    
    for i in range(total_count):
        # 动态生成时间戳（当前时间 + 偏移）
        timestamp = int(time.time() * 1000) + (i * interval * 1000)
        
        payload = {
            "message_type": 1,
            "task_id": HEART_RATE_TASK_ID,
            "hkData": 1,
            "timestamp": timestamp,
            "results": [
                {
                    "bpm": HEART_RATE,
                    "person_id": PERSON_ID,
                    "breathe": BREATHE
                }
            ]
        }
        
        try:
            print(f"\n[{i+1}/{total_count}] 正在发送心率消息...")
            print(f"请求URL: {url}")
            print(f"请求参数: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            response = requests.post(url, json=payload)
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                print(f"✅ 第 {i+1} 次心率消息发送成功")
            else:
                print(f"❌ 第 {i+1} 次心率消息发送失败，状态码: {response.status_code}")
            
            # 如果不是最后一次，等待指定间隔
            if i < total_count - 1:
                print(f"等待 {interval} 秒后发送下一次...")
                time.sleep(interval)
                
        except Exception as e:
            print(f"❌ 第 {i+1} 次发送心率消息时出错: {str(e)}")
            return False
    
    print(f"\n=== 心率消息发送完成，共发送 {total_count} 次 ===")
    return True

if __name__ == "__main__":
    print("=== 发送检测到有人消息 ===\n")
    send_person_enter()
    
    print("\n=== 发送动作检测消息 ===\n")
    send_vital_sign_action()
    
    print("\n=== 发送心率消息 ===\n")
    send_hr_br()
