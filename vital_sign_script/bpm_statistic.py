import re
import json
import sys
import os
import time
import statistics

def analyze_bpm(log_file):
    # 存储所有提取的bpm数值
    bpm_values = []
    
    print("Starting BPM monitoring (only new log entries will be processed)...")
    print(f"Monitoring log file: {log_file}")
    print("----------------------------------------")
    
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
                # 检查是否为心率消息日志
                # if 'Sending heart message:' in line:
                if 'heart message:' in line:
                    print("\nDetected new heart message - processing...")
                    
                    # 提取完整的JSON部分
                    # match = re.search(r'Sending heart message: (\{.*\})', line)
                    match = re.search(r'heart message: (\{.*\})', line)
                    if match:
                        json_str = match.group(1)
                        # 转换为标准JSON格式
                        json_str = json_str.replace("'", "\"")
                        json_str = json_str.replace("None", "null")
                        
                        try:
                            # 解析JSON数据
                            log_data = json.loads(json_str)
                            
                            # 提取results中的bpm数值
                            if 'results' in log_data and isinstance(log_data['results'], list):
                                for result in log_data['results']:
                                    if 'bpm' in result and result['bpm'] is not None:
                                        bpm = result['bpm']
                                        # 确保bpm是数值类型
                                        if isinstance(bpm, (int, float)):
                                            bpm_values.append(bpm)
                                            print(f"Added BPM value: {bpm}")
                                            print(f"All BPM values so far: {', '.join(map(str, bpm_values))}")
                                            
                                            # 计算并显示统计信息
                                            if len(bpm_values) >= 1:
                                                average = sum(bpm_values) / len(bpm_values)
                                                print(f"Average BPM: {average:.2f}")
                                                
                                            if len(bpm_values) >= 2:
                                                median = statistics.median(bpm_values)
                                                print(f"Median BPM: {median}")
                                        else:
                                            print(f"Invalid BPM value (not a number): {result['bpm']}")
                            else:
                                print("No valid 'results' field in JSON")
                                
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {str(e)}")
                    else:
                        print("Could not extract JSON from line")
                
                # 显示分隔线，区分不同日志条目
                # if 'Sending heart message:' in line:
                if 'heart message:' in line:
                    print("\n----------------------------------------")
                    print("Waiting for new entries... (Press Ctrl+C to exit)")
            
            except Exception as e:
                print(f"Error processing line: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python bpm_analyzer.py <log_file_path>")
        sys.exit(1)
    
    log_file = sys.argv[1]
    try:
        analyze_bpm(log_file)
    except KeyboardInterrupt:
        print("\nProgram exited")

