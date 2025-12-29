import re
import json
import sys
import os
import time

def count_poses(log_file):
    # 初始化计数器
    counters = {
        'others_pose': 0,
        'bending_over': 0,
        'hand_on_chest': 0,
        'convulsion': 0,
        'fall_down': 0,
        'rush_wall': 0
    }
    
    print("Starting monitoring (only new log entries will be processed)...")
    print(f"Monitoring log file: {log_file}")
    
    # 获取文件当前大小，从文件末尾开始监控新内容
    try:
        file_size = os.path.getsize(log_file)
    except FileNotFoundError:
        print(f"Error: Log file '{log_file}' not found")
        sys.exit(1)
    
    with open(log_file, 'r') as f:
        # 移动到文件末尾
        f.seek(file_size)
        
        while True:
            # 读取新内容
            line = f.readline()
            if not line:
                # 没有新内容时短暂等待
                time.sleep(0.1)
                continue
            
            try:
                # 检查是否为目标行为日志
                if 'Sending behavior message:' in line:
                    print("\nDetected new behavior message - processing...")
                    
                    # 提取完整的JSON部分（从{开始到最后一个}结束）
                    # 针对你的日志格式专门优化的正则表达式
                    match = re.search(r'Sending behavior message: (\{.*\})', line)
                    if match:
                        json_str = match.group(1)
                        print(f"Original JSON string: {json_str}")
                        
                        # 仅进行必要的JSON格式转换
                        json_str = json_str.replace("'", "\"")  # 单引号转双引号
                        json_str = json_str.replace("True", "true")  # 布尔值小写
                        json_str = json_str.replace("False", "false")
                        
                        print(f"Cleaned JSON string: {json_str}")
                        
                        try:
                            # 解析JSON
                            log_data = json.loads(json_str)
                            
                            # 提取results并统计
                            if 'results' in log_data and isinstance(log_data['results'], list):
                                for result in log_data['results']:
                                    for key in counters:
                                        if key in result and result[key] is True:
                                            counters[key] += 1
                                            print(f"Incremented {key} to {counters[key]}")
                            else:
                                print("No valid 'results' field in JSON")
                                
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {str(e)}")
                            print(f"Failed to parse: {json_str}")
                    else:
                        print("Could not extract JSON from line")
                
                # 显示当前统计结果（仅在有更新时）
                if 'Sending behavior message:' in line:
                    print("\nCurrent statistics (new entries only):")
                    for key, value in counters.items():
                        print(f"{key}: {value}")
                    print("\nPress Ctrl+C to exit")
                    print("----------------------------------------")
            
            except Exception as e:
                print(f"Error processing line: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python log_statistic.py <log_file_path>")
        sys.exit(1)
    
    log_file = sys.argv[1]
    try:
        count_poses(log_file)
    except KeyboardInterrupt:
        print("\nProgram exited")

