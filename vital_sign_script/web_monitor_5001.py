import os
import re
import json
import time
import statistics
import paramiko
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from threading import Thread, Event
from io import StringIO
from typing import Union

app = Flask(__name__)

# 全局变量用于存储统计数据
pose_counters = {
    'others_pose': 0,
    'bending_over': 0,
    'hand_on_chest': 0,
    'convulsion': 0,
    'fall_down': 0,
    'rush_wall': 0
}
bpm_values = []
manual_bpm_values = []  # 存储手动输入的心率数据

# 监控状态和控制
monitoring_status = {
    'pose': False,
    'bpm': False
}
stop_events = {
    'pose': Event(),
    'bpm': Event()
}

# SSH连接信息
ssh_clients = {}

def get_remote_file_content(hostname, username, password, remote_path, last_position=0):
    """通过SFTP获取远程文件内容"""
    try:
        # 检查是否已有连接
        if hostname not in ssh_clients:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname, username=username, password=password)
            ssh_clients[hostname] = ssh
        else:
            ssh = ssh_clients[hostname]

        sftp = ssh.open_sftp()
        with sftp.file(remote_path, 'r') as remote_file:
            remote_file.seek(last_position)
            content = remote_file.read().decode('utf-8')
            new_position = remote_file.tell()
            return content, new_position
    except Exception as e:
        print(f"Error reading remote file: {str(e)}")
        return '', last_position

def monitor_pose_log(log_file, ssh_config=None):
    print(f"Starting pose monitoring for file: {log_file}")
    if ssh_config:
        print(f"Using SSH connection to {ssh_config['hostname']}")
    
    try:
        # 检查文件是否存在
        if not ssh_config:
            if not os.path.exists(log_file):
                error_msg = f"Error: Log file '{log_file}' not found"
                print(error_msg)
                return error_msg
            print("Local file exists, starting monitoring...")
            # 获取文件初始大小
            last_position = os.path.getsize(log_file)
        else:
            print("Remote file monitoring starting...")
            # 获取远程文件初始大小
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ssh_config['hostname'], username=ssh_config['username'], password=ssh_config['password'])
                stdin, stdout, stderr = ssh.exec_command(f'stat -c%s {log_file}')
                file_size = int(stdout.read().decode().strip())
                last_position = file_size
                ssh.close()
                print(f"Remote file size: {file_size} bytes")
            except Exception as e:
                print(f"Error getting remote file size: {str(e)}")
                last_position = 0
    except Exception as e:
        print(f"Error initializing monitoring: {str(e)}")
        last_position = 0

    print(f"开始监控动作识别日志: {log_file}")

    while not stop_events['pose'].is_set():
        try:
            new_lines = []
            
            if ssh_config:
                # 远程文件监控
                content, new_position = get_remote_file_content(
                    ssh_config['hostname'],
                    ssh_config['username'],
                    ssh_config['password'],
                    log_file,
                    last_position
                )
                
                if content and new_position > last_position:
                    new_lines = content.splitlines(keepends=True)
                    last_position = new_position
                elif new_position < last_position:
                    # 文件被截断或轮转，重置位置
                    last_position = 0
                    continue
            else:
                # 本地文件监控
                try:
                    current_size = os.path.getsize(log_file)
                    if current_size > last_position:
                        # 文件有新内容
                        with open(log_file, 'r', encoding='utf-8') as f:
                            f.seek(last_position)
                            new_content = f.read()
                            new_lines = new_content.splitlines(keepends=True)
                            last_position = current_size
                    elif current_size < last_position:
                        # 文件被截断或轮转，重置位置
                        last_position = 0
                        continue
                except FileNotFoundError:
                    time.sleep(1)
                    continue
                except Exception:
                    time.sleep(1)
                    continue
            
            if not new_lines:
                time.sleep(0.1)  # 减少等待时间，更快响应停止信号
                continue
            
            for line in new_lines:
                if stop_events['pose'].is_set():
                    print("检测到停止信号，正在终止动作识别监控...")
                    break
                    
                line = line.strip()
                if not line:
                    continue
                if 'Sending behavior message:' in line:
                    print("\nDetected new behavior message - processing...")
                    match = re.search(r'Sending behavior message: (\{.*\})', line)
                    if match:
                        json_str = match.group(1)
                        print(f"Original JSON string: {json_str}")
                        
                        json_str = json_str.replace("'", '"').replace("True", "true").replace("False", "false")
                        print(f"Cleaned JSON string: {json_str}")
                        
                        try:
                            log_data = json.loads(json_str)
                            if 'results' in log_data and isinstance(log_data['results'], list):
                                for result in log_data['results']:
                                    if stop_events['pose'].is_set():
                                        break
                                    for key in pose_counters:
                                        if key in result and result[key] is True:
                                            pose_counters[key] += 1
                                            print(f"Incremented {key} to {pose_counters[key]}")
                            else:
                                print("No valid 'results' field in JSON")
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {str(e)}")
                            print(f"Failed to parse: {json_str}")
                            continue
                    else:
                        print("Could not extract JSON from line")
                
                # 显示当前统计结果（仅在有更新时）
                if 'Sending behavior message:' in line and not stop_events['pose'].is_set():
                    print("\nCurrent statistics (new entries only):")
                    for key, value in pose_counters.items():
                        print(f"{key}: {value}")
                    print("\nMonitoring continues...")
                    print("----------------------------------------")
                    
        except Exception as e:
            if stop_events['pose'].is_set():
                print("动作识别监控已停止")
                break
            print(f"Error monitoring pose log: {str(e)}")
            time.sleep(1)
    
    print("动作识别监控线程已完全退出")

def monitor_bpm_log(log_file: str, ssh_config: dict = None) -> Union[str, None]:
    print(f"Starting heart rate monitoring for file: {log_file}")
    if ssh_config:
        print(f"Using SSH connection to {ssh_config['hostname']}")
    
    try:
        # 检查文件是否存在
        if not ssh_config:
            if not os.path.exists(log_file):
                error_msg = f"Error: Log file '{log_file}' not found"
                print(error_msg)
                return error_msg
            print("Local file exists, starting monitoring...")
            # 获取文件初始大小
            last_position = os.path.getsize(log_file)
        else:
            print("Remote file monitoring starting...")
            # 获取远程文件初始大小
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ssh_config['hostname'], username=ssh_config['username'], password=ssh_config['password'])
                stdin, stdout, stderr = ssh.exec_command(f'stat -c%s {log_file}')
                file_size = int(stdout.read().decode().strip())
                last_position = file_size
                ssh.close()
                print(f"Remote file size: {file_size} bytes")
            except Exception as e:
                print(f"Error getting remote file size: {str(e)}")
                last_position = 0
    except Exception as e:
        print(f"Error initializing monitoring: {str(e)}")
        last_position = 0

    print(f"开始监控心率日志: {log_file}")

    while not stop_events['bpm'].is_set():
        try:
            new_lines = []
            
            if ssh_config:
                # 远程文件监控
                content, new_position = get_remote_file_content(
                    ssh_config['hostname'],
                    ssh_config['username'],
                    ssh_config['password'],
                    log_file,
                    last_position
                )
                
                if content and new_position > last_position:
                    new_lines = content.splitlines(keepends=True)
                    last_position = new_position
                elif new_position < last_position:
                    # 文件被截断或轮转，重置位置
                    last_position = 0
                    continue
            else:
                # 本地文件监控
                try:
                    current_size = os.path.getsize(log_file)
                    if current_size > last_position:
                        # 文件有新内容
                        with open(log_file, 'r', encoding='utf-8') as f:
                            f.seek(last_position)
                            new_content = f.read()
                            new_lines = new_content.splitlines(keepends=True)
                            last_position = current_size
                    elif current_size < last_position:
                        # 文件被截断或轮转，重置位置
                        last_position = 0
                        continue
                except FileNotFoundError:
                    time.sleep(1)
                    continue
                except Exception:
                    time.sleep(1)
                    continue
            
            if not new_lines:
                time.sleep(0.1)  # 减少等待时间，更快响应停止信号
                continue
            
            for line in new_lines:
                if stop_events['bpm'].is_set():
                    print("检测到停止信号，正在终止心率监控...")
                    break
                    
                line = line.strip()
                if not line:
                    continue
                if 'heart message:' in line:
                    print("\nDetected new heart rate message - processing...")
                    match = re.search(r'heart message: (\{.*\})', line)
                    if match:
                        json_str = match.group(1)
                        print(f"Original JSON string: {json_str}")
                        
                        json_str = json_str.replace("'", '"').replace("None", "null")
                        print(f"Cleaned JSON string: {json_str}")
                        
                        try:
                            log_data = json.loads(json_str)
                            if 'results' in log_data and isinstance(log_data['results'], list):
                                for result in log_data['results']:
                                    if stop_events['bpm'].is_set():
                                        break
                                    if 'bpm' in result and result['bpm'] is not None:
                                        bpm = result['bpm']
                                        if isinstance(bpm, (int, float)):
                                            timestamp = datetime.now().strftime('%H:%M:%S')
                                            bpm_values.append({
                                                'value': bpm,
                                                'timestamp': timestamp
                                            })
                                            print(f"Added BPM value: {bpm} at {timestamp}")
                            else:
                                print("No valid 'results' field in JSON")
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {str(e)}")
                            print(f"Failed to parse: {json_str}")
                            continue
                    else:
                        print("Could not extract JSON from line")
                
                # 显示当前统计结果（仅在有更新时）
                if 'heart message:' in line and bpm_values and not stop_events['bpm'].is_set():
                    values = [v['value'] for v in bpm_values]
                    print("\nCurrent statistics:")
                    print(f"Total readings: {len(values)}")
                    print(f"Average BPM: {sum(values) / len(values):.2f}")
                    if len(values) >= 2:
                        print(f"Median BPM: {statistics.median(values):.2f}")
                    print("\nMonitoring continues...")
                    print("----------------------------------------")
        except Exception as e:
            if stop_events['bpm'].is_set():
                print("心率监控已停止")
                break
            print(f"Error monitoring bpm log: {str(e)}")
            time.sleep(1)
    
    print("心率监控线程已完全退出")

@app.route('/')
def index():
    return render_template('monitor.html')

@app.route('/start/<monitor_type>', methods=['POST'])
def start_monitoring(monitor_type):
    if monitor_type not in ['pose', 'bpm']:
        return jsonify({'error': 'Invalid monitor type'})
        
    if monitoring_status[monitor_type]:
        return jsonify({'error': f'{monitor_type} monitoring already running'})
    
    data = request.json
    log_file = data.get('log_file')
    ssh_config = data.get('ssh_config')
    
    if not log_file:
        return jsonify({'error': 'Log file path is required'})
    
    stop_events[monitor_type].clear()
    monitoring_status[monitor_type] = True
    
    if monitor_type == 'pose':
        Thread(target=monitor_pose_log, args=(log_file, ssh_config)).start()
    else:
        Thread(target=monitor_bpm_log, args=(log_file, ssh_config)).start()
    
    return jsonify({'status': 'started'})

@app.route('/stop/<monitor_type>')
def stop_monitoring(monitor_type):
    """停止监控 - 只停止日志监控，不清空统计数据"""
    if monitor_type not in ['pose', 'bpm']:
        return jsonify({'error': 'Invalid monitor type'})
        
    stop_events[monitor_type].set()
    monitoring_status[monitor_type] = False
    
    # 停止监控时不再清空统计数据
    return jsonify({'status': 'stopped', 'cleared': False})

@app.route('/stop_all')
def stop_all_monitoring():
    """完全停止所有监控，相当于点击了所有停止按钮"""
    results = {}
    
    for monitor_type in ['pose', 'bpm']:
        if monitoring_status[monitor_type]:
            stop_events[monitor_type].set()
            monitoring_status[monitor_type] = False
            results[monitor_type] = 'stopped'
        else:
            results[monitor_type] = 'already_stopped'
    
    return jsonify({
        'status': 'success',
        'results': results,
        'message': '所有监控已完全停止'
    })

@app.route('/data')
def get_data():
    bpm_stats = {}
    if bpm_values:
        values = [v['value'] for v in bpm_values]
        bpm_stats = {
            'average': sum(values) / len(values),
            'median': statistics.median(values) if len(values) >= 2 else None,
            'history': bpm_values[-80:] # 最近80个数据点用于图表显示
        }
    
    manual_bpm_stats = {}
    if manual_bpm_values:
        values = [v['value'] for v in manual_bpm_values]
        manual_bpm_stats = {
            'average': sum(values) / len(values),
            'median': statistics.median(values) if len(values) >= 2 else None,
            'history': manual_bpm_values[-80:] # 最近80个数据点用于显示
        }
    
    return jsonify({
        'pose_counters': pose_counters,
        'bpm_stats': bpm_stats,
        'manual_bpm_stats': manual_bpm_stats
    })

@app.route('/clear_stats', methods=['POST'])
def clear_stats():
    """清空统计数据"""
    global pose_counters, bpm_values
    
    # 重置姿态计数器
    pose_counters = {
        'others_pose': 0,
        'bending_over': 0,
        'hand_on_chest': 0,
        'convulsion': 0,
        'fall_down': 0,
        'rush_wall': 0
    }
    
    # 清空心率数据
    bpm_values = []
    
    return jsonify({
        'status': 'success',
        'message': '统计数据已清空'
    })

@app.route('/clear_bpm_stats', methods=['POST'])
def clear_bpm_stats():
    """专门清空心率数据"""
    global bpm_values
    
    # 只清空心率数据，不影响动作识别数据
    bpm_values = []
    
    return jsonify({
        'status': 'success',
        'message': '心率数据已清空'
    })

@app.route('/add_manual_bpm', methods=['POST'])
def add_manual_bpm():
    """添加手动输入的心率数据"""
    global manual_bpm_values
    
    data = request.json
    bpm_value = data.get('bpm')
    
    if bpm_value is None:
        return jsonify({'error': '心率值不能为空'})
    
    try:
        bpm_value = float(bpm_value)
        if bpm_value <= 0 or bpm_value > 300:
            return jsonify({'error': '心率值必须在1-300之间'})
    except ValueError:
        return jsonify({'error': '心率值必须是数字'})
    
    timestamp = datetime.now().strftime('%H:%M:%S')
    manual_bpm_values.append({
        'value': bpm_value,
        'timestamp': timestamp
    })
    
    # 保持最多80个数据点
    if len(manual_bpm_values) > 80:
        manual_bpm_values = manual_bpm_values[-80:]
    
    return jsonify({
        'status': 'success',
        'message': '心率数据已添加',
        'data': {
            'value': bpm_value,
            'timestamp': timestamp
        }
    })

@app.route('/clear_manual_bpm', methods=['POST'])
def clear_manual_bpm():
    """清空手动输入的心率数据"""
    global manual_bpm_values
    
    manual_bpm_values = []
    
    return jsonify({
        'status': 'success',
        'message': '手动输入的心率数据已清空'
    })

@app.route('/test_connection', methods=['POST'])
def test_connection():
    data = request.json
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            data['hostname'],
            username=data['username'],
            password=data['password']
        )
        ssh.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/calculate_deviation_mean')
def calculate_deviation_mean():
    """计算心率检测值与手动输入值的偏差均值"""
    if not manual_bpm_values or not bpm_values:
        return jsonify({'error': '心率数据不足，无法计算偏差均值'})
    
    # 计算心率偏差均值
    manual_values = [v['value'] for v in manual_bpm_values]
    detected_values = [v['value'] for v in bpm_values]
    
    # 使用实际可用的数据对数量（不一定需要80对）
    min_length = min(len(manual_values), len(detected_values))
    if min_length == 0:
        return jsonify({'error': '没有足够的数据对来计算偏差均值'})
    
    total_deviation = 0
    for i in range(min_length):
        # 第i个心率检测值 - 第i个实际心率值，取绝对值
        deviation = abs(detected_values[i] - manual_values[i])
        total_deviation += deviation
    
    # 计算平均值
    deviation_mean = total_deviation / min_length
    
    return jsonify({
        'deviation_mean': round(deviation_mean, 2),
        'data_pairs_used': min_length
    })

@app.route('/delete_last_manual_bpm', methods=['POST'])
def delete_last_manual_bpm():
    """删除最后一个手动输入的心率数据"""
    global manual_bpm_values
    
    if not manual_bpm_values:
        return jsonify({'error': '没有手动输入的心率数据可删除'})
    
    # 删除最后一个数据
    deleted_value = manual_bpm_values.pop()
    
    return jsonify({
        'status': 'success',
        'message': '最后一个心率数据已删除',
        'deleted_value': deleted_value['value']
    })

def cleanup():
    """清理SSH连接"""
    for ssh in ssh_clients.values():
        try:
            ssh.close()
        except:
            pass
    ssh_clients.clear()

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=5001)
    finally:
        cleanup()
