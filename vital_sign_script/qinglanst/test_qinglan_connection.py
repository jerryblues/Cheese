import socket
import struct
import time
import sys

"""
qinglan.com TCP连接测试工具
用于测试与qinglanst.com 7260端口的TCP连接可用性
"""

# 服务器配置
SERVER_HOST = "qinglanst.com"
SERVER_PORT = 7260
TIMEOUT = 15  # 连接超时时间(秒)，与原始脚本保持一致


def test_tcp_connection(host, port, timeout=TIMEOUT):
    """
    测试TCP连接是否可用
    :param host: 主机名或IP地址
    :param port: 端口号
    :param timeout: 超时时间(秒)
    :return: 连接是否成功
    """
    print(f"\n=== TCP连接测试开始 ===")
    print(f"目标服务器: {host}:{port}")
    print(f"超时时间: {timeout}秒")
    
    # 检查DNS解析
    try:
        print("\n正在进行DNS解析...")
        start_time = time.time()
        # 使用gethostbyname_ex获取所有IP地址，与原始脚本行为一致
        ip_addresses = socket.gethostbyname_ex(host)
        resolve_time = time.time() - start_time
        print(f"DNS解析成功! 主机 {host} 的IP地址列表: {ip_addresses[2]}")
        print(f"DNS解析耗时: {resolve_time:.3f}秒")
    except socket.gaierror as e:
        print(f"❌ DNS解析失败: {str(e)}")
        print("可能的原因: 域名不存在、DNS服务器问题或网络连接问题")
        return False
    
    # 测试TCP连接，尝试连接所有解析到的IP地址
    success = False
    for ip in ip_addresses[2]:
        print(f"\n正在尝试连接到IP地址: {ip}:{port}")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                # 设置超时时间，与原始脚本保持一致
                sock.settimeout(timeout)
                start_time = time.time()
                
                try:
                    # 尝试连接
                    sock.connect((ip, port))
                    end_time = time.time()
                    print(f"✅ 成功连接到 {ip}:{port}，响应时间: {end_time - start_time:.2f}秒")
                    success = True
                    
                    # 尝试发送测试数据包（可选）
                    try:
                        print("\n尝试发送测试数据包...")
                        # 准备一个简单的测试消息，遵循4字节长度+报文格式
                        test_message = "{\"cmd\":\"TEST\"}"
                        # 计算消息长度（包括4字节本身）
                        message_length = len(test_message.encode('utf-8')) + 4
                        # 构建4字节长度前缀（大端序）
                        length_prefix = struct.pack('>I', message_length)
                        # 组合完整消息
                        full_message = length_prefix + test_message.encode('utf-8')
                        
                        # 发送消息
                        sock.sendall(full_message)
                        print(f"测试数据包发送成功")
                        print(f"发送的数据包长度: {len(full_message)}字节")
                        print(f"其中长度前缀: 4字节 ({message_length})")
                        print(f"测试消息内容: {test_message}")
                    except Exception as e:
                        print(f"⚠️ 发送测试数据包时发生错误: {str(e)}")
                        # 发送失败不影响连接成功的状态
                    
                    break  # 只要有一个IP连接成功就停止尝试
                except socket.timeout:
                    print(f"❌ 连接到 {ip}:{port} 超时")
                except ConnectionRefusedError:
                    print(f"❌ 连接到 {ip}:{port} 被拒绝")
                except Exception as e:
                    print(f"❌ 连接测试发生错误: {str(e)}")
        except Exception as e:
            print(f"❌ 创建套接字时发生错误: {str(e)}")
    
    if not success:
        print("\n连接测试失败。请检查以下几点:")
        print("1. 网络连接是否正常")
        print("2. 防火墙是否允许访问该端口")
        print("3. 服务器地址和端口是否正确")
        print("4. 服务器是否正在运行并监听该端口")
        return False
    
    return True


def main():
    """
    主函数
    """
    print("=========================")
    print(" qinglan.com TCP连接测试工具 ")
    print("=========================")
    
    # 执行连接测试
    success = test_tcp_connection(SERVER_HOST, SERVER_PORT)
    
    # 多次测试选项
    try:
        print("\n是否进行多次连接测试? (y/n): ")
        choice = input().strip().lower()
        if choice == 'y':
            print("输入测试次数: ")
            count = int(input().strip())
            print(f"\n开始执行{count}次连接测试...")
            
            success_count = 0
            for i in range(1, count + 1):
                print(f"\n--- 测试 #{i} ---")
                if test_tcp_connection(SERVER_HOST, SERVER_PORT):
                    success_count += 1
                
                # 两次测试之间的间隔
                if i < count:
                    wait_time = 2
                    print(f"\n等待{wait_time}秒后进行下一次测试...")
                    time.sleep(wait_time)
            
            print(f"\n=== 测试统计 ===")
            print(f"总测试次数: {count}")
            print(f"成功次数: {success_count}")
            print(f"成功率: {success_count/count*100:.1f}%")
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
    
    print("\n=== 测试结束 ===")


if __name__ == "__main__":
    main()