import requests

'''
https://one.caifree.com/log
url = "https://one.caifree.com/v1/chat/completions"
"Authorization": "Bearer sk-sg9w4LAuHPCm9Fq408F5679d46F44d02A485B96aB5041685"

https://burn.hair/log
url = "https://burn.hair/v1/chat/completions"
"Authorization": "Bearer sk-ySOZXKC68tIwP6e8Bb3689Cb914044Bc90B51c8a321e6c15"
'''


def ask_question(question):
    # API URL
    url = "https://one.caifree.com/v1/chat/completions"

    headers = {
        "Authorization": "Bearer sk-sg9w4LAuHPCm9Fq408F5679d46F44d02A485B96aB5041685"
    }

    # 构造请求体
    data = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": question
            }
        ],
        "temperature": 0.7
    }

    # 发送POST请求
    response = requests.post(url, headers=headers, json=data)

    # 检查响应状态码
    if response.status_code == 200:
        # 解析响应内容
        response_data = response.json()
        # 假设API响应的结构包含回复内容
        return response_data.get("choices", [{}])[0].get("message", {}).get("content", "无法获取回复。")
    else:
        return f"请求失败，状态码：{response.status_code}"


if __name__ == "__main__":
    while True:
        # 提示用户输入问题
        my_question = input("请输入你的问题（输入'Q'结束对话）：")

        # 检查是否退出
        if my_question == "Q":
            print("对话结束。")
            break

        # 调用函数获取回复
        reply = ask_question(my_question)
        print("机器人回复：", reply)
