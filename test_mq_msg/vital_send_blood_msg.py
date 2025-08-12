import json
import time
import requests

# 全局配置变量
PERSON_ID = 10086
TASK_ID = "53@53"
BODY_URL = "https://file.shangjinuu.com/images/trial/%E5%B9%B3%E9%9D%99.png"
IMG_URL = "https://file.shangjinuu.com/images/trial/%E5%B9%B3%E9%9D%99.png"
POST_URL = "http://10.1.120.27:8120/vital-sign/vital/signs/sendMq"

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

def send_vital_sign_blood():
    # 获取当前时间戳（毫秒）
    timestamp = int(time.time() * 1000)
    # timestamp = current_time - (1 * 1000)  # 减去1秒
    
    # 构造检测到血液消息
    payload = {
        "message_type": 5,
        "results": [
            {
                "blood": True,
                "img_url": IMG_URL
            }
        ],
        "timestamp": timestamp,
        "task_id": TASK_ID
    }
    
    # 发送POST请求
    url = POST_URL
    
    try:
        print("正在发送生命体征消息...")
        print(f"请求URL: {url}")
        print(f"请求参数: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(url, json=payload)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 消息发送成功")
            return True
        else:
            print(f"❌ 消息发送失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 发送消息时出错: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== 发送检测到有人消息 ===\n")
    send_person_enter()
    
    print("\n=== 开始循环发送生命体征消息 ===")
    
    # 发送次数配置
    total_count = 5
    interval = 1
    
    try:
        sent_count = 0
        while sent_count < total_count:
            # 发送消息
            success = send_vital_sign_blood()
            
            # 更新发送计数
            if success:
                sent_count += 1
                print(f"\n已发送 {sent_count}/{total_count} 条消息")
            
            # 如果还没有发送完成，等待指定的间隔时间
            if sent_count < total_count:
                time.sleep(interval)
        
        print(f"\n✅ 完成发送，共发送 {sent_count} 条消息")
    except KeyboardInterrupt:
        print(f"\n⚠️ 手动停止发送，已发送 {sent_count} 条消息")
    except Exception as e:
        print(f"\n❌ 发送过程出错: {str(e)}")