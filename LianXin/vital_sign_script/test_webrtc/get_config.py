import json

# 读取你的 streams.txt
with open("streams.txt", "r") as f:
    urls = [line.strip() for line in f if line.strip()]

config = {"urls": {}}
for i, url in enumerate(urls):
    # i+1 是当前的序号
    # 使用 :02d 强制两位数字补零，如 cam01, cam02... cam10
    cam_name = f"cam{(i+1):02d}" 
    config["urls"][cam_name] = {"video": url}

with open("config.json", "w") as jf:
    json.dump(config, jf, indent=4)

print(f"成功生成 config.json，共 {len(urls)} 路。")
