import json
import time
import requests

"""
支持以下消息：
1. 检测到有人消息
2. 检测到血液消息
3. 检测到动作消息（2组动作）
4. 检测到心率/呼吸消息
支持通过全局开关控制是否发送对应消息
"""

# ================ 功能开关 ==================
ENABLE_PERSON_DETECT = 1      # 是否发送检测到有人
ENABLE_BLOOD_DETECT  = 1      # 是否发送血液检测
ENABLE_ACTION_DETECT = 1      # 是否发送动作检测
ENABLE_HR_BR         = 0      # 是否发送心率/呼吸

# ================ 动作检测配置 ===============
# 两组动作组合
ACTIVE_ACTIONS_1 = {
    "fall_down": False,
    "hand_on_chest": False,
    "others_pose": False,
    "bending_over": False,
    "convulsion": False,
    "rush_wall": False
}

ACTIVE_ACTIONS_2 = {
    "fall_down": False,
    "hand_on_chest": False,
    "others_pose": False,
    "bending_over": False,
    "convulsion": False,
    "rush_wall": True
}

# ================= 全局配置 =================
# 接口与人员信息
PERSON_ID = 10086
TASK_ID = "53@53"                # 动作/血液检测统一 task_id，53@53对应房间：模拟20
HR_BR_TASK_ID = "53"        # 心率消息独立 task_id
POST_URL = "http://10.1.120.27:8120/vital-sign/vital/signs/sendMq"
# 图片地址（检测到有人、血液）
BODY_URL = "https://file.shangjinuu.com/images/trial/%E5%B9%B3%E9%9D%99.png"
IMG_URL = "https://file.shangjinuu.com/images/trial/%E5%B9%B3%E9%9D%99.png"
# 心率/呼吸默认值与频率配置
HEART_RATE = 39               # 默认心率
BREATHE = 10                  # 默认呼吸
HEART_RATE_SEND_COUNT = 15    # 心率消息发送次数
HEART_RATE_SEND_INTERVAL = 2  # 心率消息发送间隔（秒）
# 血液检测循环发送配置
BLOOD_SEND_COUNT = 5          # 血液检测发送次数
BLOOD_SEND_INTERVAL = 1       # 血液检测发送间隔（秒）


# ==================== 发送函数 ====================

def send_post(url: str, payload: dict, desc: str) -> bool:
    """公共请求封装，打印日志并返回是否成功"""
    try:
        print(desc)
        print(f"请求URL: {url}")
        print(f"请求参数: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        response = requests.post(url, json=payload)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        if response.status_code == 200:
            print(f"✅ {desc} 发送成功")
            return True
        else:
            print(f"❌ {desc} 发送失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {desc} 发送异常: {e}")
        return False

def send_person_detect():
    ts = int(time.time() * 1000)
    payload = {
        "message_type": 3,
        "results": [{
            "person_id": PERSON_ID,
            "body_url": BODY_URL,
            "body_still": False
        }],
        "timestamp": ts,
        "task_id": TASK_ID
    }
    return send_post(POST_URL, payload, "检测到有人消息")

def send_vital_sign_blood():
    ts = int(time.time() * 1000)
    payload = {
        "message_type": 5,
        "results": [{
            "blood": True,
            "img_url": IMG_URL
        }],
        "timestamp": ts,
        "task_id": TASK_ID
    }
    return send_post(POST_URL, payload, "检测到血液消息")

def send_vital_sign_action():
    ts = int(time.time() * 1000)
    # 构造两条 result
    result1 = {**ACTIVE_ACTIONS_1, "person_id": PERSON_ID}
    result2 = {**ACTIVE_ACTIONS_2, "person_id": PERSON_ID}

    # 第一条
    payload1 = {
        "message_type": 4,
        "results": [result1],
        "timestamp": ts,
        "task_id": TASK_ID
    }
    ok1 = send_post(POST_URL, payload1, "动作检测消息-1")

    # 第二条（时间戳 +1s）
    payload2 = {
        "message_type": 4,
        "results": [result2],
        "timestamp": ts + 1000,
        "task_id": TASK_ID
    }
    ok2 = send_post(POST_URL, payload2, "动作检测消息-2")
    return ok1 and ok2

def send_hr_br():
    print(f"=== 开始发送心率消息，共 {HEART_RATE_SEND_COUNT} 次，间隔 {HEART_RATE_SEND_INTERVAL} 秒 ===")
    for i in range(HEART_RATE_SEND_COUNT):
        ts = int(time.time() * 1000) + i * HEART_RATE_SEND_INTERVAL * 1000
        payload = {
            "message_type": 1,
            "task_id": HR_BR_TASK_ID,
            "hkData": 1,
            "timestamp": ts,
            "results": [{
                "bpm": HEART_RATE,
                "person_id": PERSON_ID,
                "breathe": BREATHE
            }]
        }
        if not send_post(POST_URL, payload, f"心率消息第 {i+1}/{HEART_RATE_SEND_COUNT}"):
            return False
        if i < HEART_RATE_SEND_COUNT - 1:
            time.sleep(HEART_RATE_SEND_INTERVAL)
    print("=== 心率消息发送完成 ===")
    return True

# ==================== 主流程 ====================
if __name__ == "__main__":
    if ENABLE_PERSON_DETECT:
        print("\n=== 发送检测到有人消息 ===")
        send_person_detect()

    if ENABLE_BLOOD_DETECT:
        print("\n=== 循环发送血液检测消息 ===")
        sent = 0
        try:
            while sent < BLOOD_SEND_COUNT:
                if send_vital_sign_blood():
                    sent += 1
                    print(f"已发送 {sent}/{BLOOD_SEND_COUNT} 条血液检测消息")
                if sent < BLOOD_SEND_COUNT:
                    time.sleep(BLOOD_SEND_INTERVAL)
        except KeyboardInterrupt:
            print("⚠️ 手动停止血液检测消息发送")

    if ENABLE_ACTION_DETECT:
        print("\n=== 发送动作检测消息 ===")
        send_vital_sign_action()

    if ENABLE_HR_BR:
        print("\n=== 发送心率/呼吸消息 ===")
        send_hr_br()