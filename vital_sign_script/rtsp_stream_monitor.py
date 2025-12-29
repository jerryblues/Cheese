#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RTSP 流地址监控工具
通过 ps -ef | grep ffmpeg 获取本地服务器上的 RTSP 流地址，并在网页上展示
"""

import re
import subprocess
import platform
from flask import Flask, render_template, jsonify
from datetime import datetime

app = Flask(__name__)


def get_rtsp_streams():
    """
    通过 ps -ef | grep ffmpeg 获取 RTSP 流地址
    返回 RTSP 地址列表
    """
    rtsp_streams = []
    
    try:
        # 根据操作系统选择不同的命令
        if platform.system() == "Windows":
            # Windows 系统：尝试使用 wmic 获取进程命令行
            try:
                # 使用 wmic 获取 ffmpeg 进程的命令行
                cmd = ['wmic', 'process', 'where', "name='ffmpeg.exe'", 'get', 'ProcessId,CommandLine', '/format:list']
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=5)
                
                if result.returncode == 0 and result.stdout:
                    # 解析 wmic 输出
                    current_pid = None
                    current_cmd = None
                    rtsp_pattern = re.compile(r'rtsp://[^\s"\'<>]+')
                    
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if line.startswith('ProcessId='):
                            current_pid = line.split('=', 1)[1].strip()
                        elif line.startswith('CommandLine='):
                            current_cmd = line.split('=', 1)[1].strip()
                            if current_cmd and current_pid:
                                matches = rtsp_pattern.findall(current_cmd)
                                for rtsp_url in matches:
                                    rtsp_streams.append({
                                        'url': rtsp_url,
                                        'pid': current_pid,
                                        'command': current_cmd[:300] if len(current_cmd) > 300 else current_cmd,
                                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    })
                                current_pid = None
                                current_cmd = None
            except Exception as e:
                print(f"Windows 系统获取进程信息失败: {str(e)}")
        else:
            # Linux/Unix 系统：使用 ps -ef | grep ffmpeg
            try:
                # 直接执行 ps -ef | grep ffmpeg
                ps_cmd = subprocess.Popen(['ps', '-ef'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                grep_cmd = subprocess.Popen(['grep', 'ffmpeg'], stdin=ps_cmd.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                ps_cmd.stdout.close()
                result = grep_cmd.communicate(timeout=5)
                
                if result[0]:
                    output = result[0].decode('utf-8', errors='ignore')
                    lines = output.split('\n')
                    
                    # 过滤掉 grep 进程本身
                    ffmpeg_lines = [line for line in lines if 'ffmpeg' in line.lower() and 'grep' not in line.lower()]
                    
                    # RTSP 地址正则表达式（匹配更完整）
                    rtsp_pattern = re.compile(r'rtsp://[^\s"\'<>]+')
                    
                    for line in ffmpeg_lines:
                        if not line.strip():
                            continue
                        
                        # 提取 RTSP 地址
                        matches = rtsp_pattern.findall(line)
                        if matches:
                            # 解析进程信息（ps -ef 格式：UID PID PPID C STIME TTY TIME CMD）
                            parts = line.split()
                            if len(parts) >= 2:
                                pid = parts[1]
                                # 获取完整的命令行（从第 8 个字段开始）
                                cmdline = ' '.join(parts[7:]) if len(parts) > 7 else line
                                
                                for rtsp_url in matches:
                                    rtsp_streams.append({
                                        'url': rtsp_url,
                                        'pid': pid,
                                        'command': cmdline[:300] if len(cmdline) > 300 else cmdline,
                                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    })
            except subprocess.TimeoutExpired:
                print("获取进程信息超时")
            except Exception as e:
                print(f"Linux 系统获取进程信息失败: {str(e)}")
                # 降级方案：直接使用 ps -ef
                try:
                    cmd = ['ps', '-ef']
                    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=5)
                    
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        ffmpeg_lines = [line for line in lines if 'ffmpeg' in line.lower() and 'grep' not in line.lower()]
                        rtsp_pattern = re.compile(r'rtsp://[^\s"\'<>]+')
                        
                        for line in ffmpeg_lines:
                            matches = rtsp_pattern.findall(line)
                            if matches:
                                parts = line.split()
                                if len(parts) >= 2:
                                    pid = parts[1]
                                    cmdline = ' '.join(parts[7:]) if len(parts) > 7 else line
                                    
                                    for rtsp_url in matches:
                                        rtsp_streams.append({
                                            'url': rtsp_url,
                                            'pid': pid,
                                            'command': cmdline[:300] if len(cmdline) > 300 else cmdline,
                                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        })
                except Exception as e2:
                    print(f"降级方案也失败: {str(e2)}")
        
        # 去重（基于 URL）
        seen_urls = set()
        unique_streams = []
        for stream in rtsp_streams:
            if isinstance(stream, dict):
                url = stream['url']
            else:
                url = stream
                stream = {
                    'url': url,
                    'pid': 'N/A',
                    'command': 'N/A',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            
            if url not in seen_urls:
                seen_urls.add(url)
                unique_streams.append(stream)
        
        return unique_streams
        
    except Exception as e:
        print(f"获取 RTSP 流地址时出错: {str(e)}")
        return []


@app.route('/')
def index():
    """主页面"""
    return render_template('rtsp_monitor.html')


@app.route('/api/streams')
def get_streams():
    """API 接口：获取 RTSP 流地址列表"""
    streams = get_rtsp_streams()
    return jsonify({
        'success': True,
        'count': len(streams),
        'streams': streams,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


if __name__ == '__main__':
    print("=" * 60)
    print("RTSP 流地址监控工具")
    print("=" * 60)
    print("访问地址: http://localhost:5001")
    print("API 接口: http://localhost:5001/api/streams")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5002)

