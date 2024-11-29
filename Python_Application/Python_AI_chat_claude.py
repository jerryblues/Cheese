import requests

# 设置请求的 URL 和头部
url = "https://api.burn.hair/v1/chat/completions"
headers = {
    "Authorization": "sk-KAmlnm4JxJAZFC98C1hB3AbEMsm3quoFK6Bjy4PNhCHpLfav",  # 替换为你的令牌
    "Content-Type": "application/json"
}

# 设置请求体
data = {
    "model": "claude-3-haiku-20240307",
    "max_tokens": 1024,
    "messages": [
        {
            "role": "user",
            "content": "Hello, world"
        }
    ]
}

# 发送 POST 请求
response = requests.post(url, headers=headers, json=data)

# 输出响应内容
if response.status_code == 200:
    print("响应内容:", response.json())
else:
    print("请求失败，状态码:", response.status_code, "响应内容:", response.text)
