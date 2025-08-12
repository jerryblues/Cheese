import json
import time
import requests
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def stop_trial():
    """
    停止最新一次的审讯
    """
    # 获取审讯ID
    trial_id = get_trial_id()
    
    stop_url = "https://pip-test.shangjin618.com/api/lianxin-sis/policeTrial/stopTrial"
    
    headers = {
        'Authorization': 'eyJhbGciOiJIUzUxMiJ9.eyJhY2NvdW50X2lkIjpudWxsLCJhdXRob3JpemVfaWQiOm51bGwsInVzZXJfaWQiOiIxIiwicGxpbmsiOm51bGwsInRoaXJkX3VzZXJfaWQiOm51bGwsInVzZXJfa2V5IjoiMzJhYmNiYjQtZDNjNy00ZDRlLThlZWYtY2IwYjI3ZmQwMGM4IiwiZGVwdF9pZF9saXN0IjpudWxsLCJkZXB0X2lkIjpudWxsLCJhcHBfaWQiOm51bGwsInBsaW5rX2xpc3QiOm51bGwsInVzZXJuYW1lIjoiYWRtaW4iLCJ0ZW5hbnRfY29kZSI6IkxYX1NYIn0.BSfDQX62tdJTvwNNQnC0ATX_650UdbCTbxjM9xkkaqA4ZEywkqmjIlf7X37MIRnKicrgwfxzDVFSG3-FGJm4cw',
    }
    
    # 请求消息体
    payload = {
        "id": trial_id,
        "userId": "1",
        "deviceCode": "local"
    }
    
    try:
        print(f"停止审讯，trial_id: {trial_id}")
        response = requests.post(
            stop_url, 
            headers=headers, 
            json=payload, 
            verify=False, 
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "200":
                print("✅ 审讯停止成功")
                return True
            else:
                print(f"❌ 审讯停止失败: {data}")
                return False
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败")
        return False
    except Exception as e:
        print(f"❌ 停止审讯时出错: {str(e)}")
        return False


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
                    return "22025073118495400685"
            else:
                print("⚠️ API返回数据格式不正确或无数据")
                print(f"返回数据: {data}")
                return "22025073118495400685"
        else:
            print(f"❌ 查询失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return "22025073118495400685"
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时，使用默认trial_id")
        return "22025073118495400685"
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，使用默认trial_id")
        return "22025073118495400685"
    except Exception as e:
        print(f"❌ 获取trial_id时出错: {str(e)}，使用默认trial_id")
        return "22025073118495400685"


if __name__ == "__main__":
    print("=== stop trial by trial id ===")
    
    # 停止审讯
    stop_trial()
