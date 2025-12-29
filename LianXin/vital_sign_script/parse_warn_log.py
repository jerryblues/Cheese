import re
import csv

# 输入 log 文件路径
LOG_FILE = "C:\\Users\\yuanb\\Downloads\\12.24.log"
OUTPUT_CSV = "C:\\Users\\yuanb\\Downloads\\warning_output-12.24.csv"

# 正则表达式提前编译
time_pattern = re.compile(r"\d{4}-\d{2}-\d{2}\s+(\d{2}:\d{2}:\d{2})")
room_pattern = re.compile(r"roomCode:(\d+)")
bp_pattern = re.compile(r'"bloodPressureHighList":(\[[^\]]*\])')

rows = []

with open(LOG_FILE, "r", encoding="utf-8") as f:
    for line in f:
        if "bloodPressureHighList" not in line:
            continue  # 不是要的 log，跳过

        # 提取预警时间
        time_match = time_pattern.search(line)
        if not time_match:
            continue
        warn_time = time_match.group(1)

        # 提取房间号
        room_match = room_pattern.search(line)
        room_code = room_match.group(1) if room_match else ""

        # 提取实际血压数组
        bp_match = bp_pattern.search(line)
        bp_list = bp_match.group(1) if bp_match else ""

        rows.append([warn_time, room_code, bp_list])

# 写入 CSV 文件
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["预警时间", "房间号", "实际血压"])
    writer.writerows(rows)

print(f"已完成！输出文件：{OUTPUT_CSV}")
