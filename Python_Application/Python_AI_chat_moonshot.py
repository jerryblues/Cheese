import os
import sys
from openai import OpenAI

# 初始化客户端
client = OpenAI(
    api_key="sk-ZxVLt1FBAC8GtJVYSALCuu5xPFeW7PNt8ZSg0Qwuv8n0HMbs",
    base_url="https://api.moonshot.cn/v1",
)

while True:
    user_input = input("请输入您的问题（输入Q退出）: ")
    if user_input.strip().upper() == 'Q':  # 检查是否退出
        print("对话结束。")
        break

    # 动态构建messages列表
    messages = [
        {
            "role": "system",
            "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。",
        },
        {"role": "user", "content": user_input},
    ]

    response = client.chat.completions.create(
        model="moonshot-v1-8k",  # moonshot-v1-8k,moonshot-v1-32k,moonshot-v1-128k 其一
        messages=messages,
        temperature=0.3,
        stream=True,  # 流式返回
    )

    collected_messages = []
    for idx, chunk in enumerate(response):
        chunk_message = chunk.choices[0].delta
        if not chunk_message.content:
            continue
        collected_messages.append(chunk_message)  # 保存消息
        # 立即在同一行输出接收到的每个消息块的内容，并使用sys.stdout.flush()确保即时显示
        print(f"{chunk_message.content}", end="")
        sys.stdout.flush()
    # 每次回答后换行，以便下一次输入
    print("\n")
