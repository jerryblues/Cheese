import socket
import json
import struct
import time
import logging
import traceback
import requests
import socket
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置选项
CONFIG = {
    "retry_count": 5,  # 请求失败重试次数
    "retry_interval": 2,  # 重试间隔(秒)
    "connection_timeout": 15,  # 连接超时时间(秒)
    "response_timeout": 30  # 响应超时时间(秒)
}

# 清澜云系统的TCP服务器配置
TCP_SERVER_CONFIG = {
    "host": "qinglanst.com",
    "port": 7260,
    "buffer_size": 4096,
    "timeout": CONFIG["connection_timeout"]  # 使用配置的连接超时时间
}

def check_network_connection(host: str, port: int) -> bool:
    """
    检查网络连接和DNS解析
    :param host: 主机名或IP地址
    :param port: 端口号
    :return: 连接是否正常
    """
    logger.info("开始网络连接诊断...")
    
    # 检查DNS解析
    try:
        ip_addresses = socket.gethostbyname_ex(host)
        logger.info(f"DNS解析成功，主机 {host} 的IP地址: {ip_addresses}")
    except socket.gaierror as e:
        logger.error(f"DNS解析失败: {str(e)}")
        logger.error("可能的原因: 域名不存在、DNS服务器问题或网络连接问题")
        return False
    
    # 尝试连接测试
    for ip in ip_addresses[2]:
        logger.info(f"尝试连接到IP地址: {ip}:{port}")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_sock:
                # 设置超时时间为连接超时的2倍，提高成功率
                test_sock.settimeout(CONFIG["connection_timeout"] * 2)
                start_time = time.time()
                
                # 使用connect而非connect_ex，以便更好地处理连接异常
                try:
                    test_sock.connect((ip, port))
                    end_time = time.time()
                    logger.info(f"成功连接到 {ip}:{port}，响应时间: {end_time - start_time:.2f}秒")
                    return True
                except socket.timeout:
                    logger.warning(f"连接到 {ip}:{port} 超时")
                except ConnectionRefusedError:
                    logger.warning(f"连接到 {ip}:{port} 被拒绝")
                except Exception as e:
                    logger.warning(f"连接测试发生错误: {str(e)}")
        except Exception as e:
            logger.warning(f"创建套接字时发生错误: {str(e)}")
    
    logger.error("网络连接诊断失败，无法连接到服务器")
    logger.error("可能的原因: 服务器端口未开放、防火墙阻止、网络限制等")
    return False

def get_access_token(username: str, password: str) -> Optional[str]:
    """
    从登录接口获取access_token
    :param username: 用户名
    :param password: 密码
    :return: access_token，如果获取失败则返回None
    """
    login_url = "https://qinglanst.com/prod-api/login"
    payload = {
        "username": username,
        "password": password,
        "pattern": "monitor",
        "grantType": "password"
    }
    
    logger.info(f"尝试从 {login_url} 获取access_token")
    
    try:
        response = requests.post(login_url, json=payload, timeout=CONFIG["connection_timeout"])
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("code") == 200 and "data" in data:
                    access_token = data["data"].get("access_token")
                    logger.info(f"成功获取access_token: {access_token}")
                    return access_token
                else:
                    logger.error(f"登录接口返回非成功状态: {data}")
                    return None
            except json.JSONDecodeError:
                logger.error(f"登录接口返回的不是有效JSON: {response.text}")
                return None
        else:
            logger.error(f"登录请求失败，状态码: {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            return None
    except requests.RequestException as e:
        logger.error(f"登录请求发生异常: {str(e)}")
        traceback.print_exc()
        return None

def create_subscribe_message(uid: str, second: int, token: Optional[str] = None, user_name: Optional[str] = None) -> bytes:
    """
    创建订阅消息
    :param uid: 设备UID
    :param second: 订阅时长(秒)
    :param token: 可选的授权token
    :param user_name: 可选的用户名
    :return: 格式化的消息字节
    """
    # 构建消息体
    message_body = {
        "cmd": "DEVICE_DATA",
        "uid": uid,
        "second": second
    }
    
    # 添加可选字段
    if token:
        message_body["token"] = token
    if user_name:
        message_body["userName"] = user_name
    
    # 转换为JSON字符串
    json_str = json.dumps(message_body)
    logger.debug(f"创建的消息体: {json_str}")
    
    # 将JSON字符串转换为字节
    json_bytes = json_str.encode('utf-8')
    
    # 计算消息总长度(4字节长度前缀 + JSON字节长度)
    total_length = len(json_bytes) + 4
    
    # 创建4字节的长度前缀(大端字节序)
    length_prefix = struct.pack('>I', total_length)
    
    # 组合长度前缀和消息体
    final_message = length_prefix + json_bytes
    
    return final_message

def subscribe_device_data(uid: str, second: int, token: Optional[str] = None, user_name: Optional[str] = None) -> Optional[str]:
    """
    订阅设备数据
    :param uid: 设备UID
    :param second: 订阅时长(秒)
    :param token: 可选的授权token
    :param user_name: 可选的用户名
    :return: 服务器响应数据，如果失败则返回None
    """
    # 检查订阅时长是否符合要求
    if second >= 120:
        logger.error(f"订阅时长 {second} 秒不符合要求，必须小于120秒")
        return None
    
    # 创建订阅消息
    message = create_subscribe_message(uid, second, token, user_name)
    
    # 尝试发送请求并接收响应
    for retry in range(CONFIG["retry_count"]):
        try:
            # 创建TCP套接字
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                # 设置超时时间
                sock.settimeout(CONFIG["connection_timeout"] * 2)  # 增加超时时间以提高成功率
                
                # 连接服务器
                logger.info(f"尝试连接到 {TCP_SERVER_CONFIG['host']}:{TCP_SERVER_CONFIG['port']}")
                sock.connect((TCP_SERVER_CONFIG['host'], TCP_SERVER_CONFIG['port']))
                logger.info("连接成功")
                
                # 发送消息
                logger.info(f"发送订阅请求，设备UID: {uid}，订阅时长: {second}秒")
                sent_bytes = sock.sendall(message)
                if sent_bytes is None:  # sendall返回None表示成功
                    logger.info("消息发送成功")
                else:
                    logger.warning(f"消息发送不完整，仅发送了 {sent_bytes} 字节")
                
                # 设置接收超时
                sock.settimeout(CONFIG["response_timeout"])
                
                # 接收数据
                logger.info("等待接收响应...")
                response_data = b''
                
                # 首先接收4字节的长度前缀
                length_prefix = sock.recv(4)
                if not length_prefix:
                    logger.warning("未接收到长度前缀，尝试直接读取响应数据")
                    # 尝试直接读取可能的响应数据
                    try:
                        response_data = sock.recv(TCP_SERVER_CONFIG['buffer_size'])
                        if response_data:
                            response_str = response_data.decode('utf-8', errors='ignore')
                            logger.info(f"成功接收响应数据: {response_str}")
                            return response_str
                    except Exception as e:
                        logger.warning(f"尝试直接读取响应数据失败: {str(e)}")
                    continue  # 重试下一次连接
                
                # 解析长度前缀
                try:
                    message_length = struct.unpack('>I', length_prefix)[0]
                    logger.info(f"接收到的消息总长度: {message_length}字节")
                except struct.error as e:
                    logger.error(f"解析长度前缀失败: {str(e)}")
                    logger.info(f"原始长度前缀数据: {length_prefix}")
                    # 尝试将长度前缀作为响应数据的一部分处理
                    response_data = length_prefix
                    try:
                        response_data += sock.recv(TCP_SERVER_CONFIG['buffer_size'])
                        response_str = response_data.decode('utf-8', errors='ignore')
                        logger.info(f"尝试解析为响应数据: {response_str}")
                        return response_str
                    except Exception as ex:
                        logger.error(f"解析响应数据失败: {str(ex)}")
                    continue  # 重试下一次连接
                
                # 接收剩余的数据
                remaining_bytes = message_length - 4  # 减去已接收的4字节长度前缀
                received_all = True
                
                # 在接收数据时添加更多的错误处理
                while remaining_bytes > 0:
                    try:
                        chunk = sock.recv(min(remaining_bytes, TCP_SERVER_CONFIG['buffer_size']))
                        if not chunk:
                            logger.warning("连接被意外关闭，尝试继续处理已接收的数据")
                            received_all = False
                            break
                        response_data += chunk
                        remaining_bytes -= len(chunk)
                        logger.debug(f"已接收 {len(chunk)} 字节，还剩 {remaining_bytes} 字节")
                    except socket.timeout:
                        logger.warning("接收数据超时，尝试继续处理已接收的数据")
                        received_all = False
                        break
                    except Exception as e:
                        logger.warning(f"接收数据时发生错误: {str(e)}，尝试继续处理已接收的数据")
                        received_all = False
                        break
                
                # 转换响应数据为字符串
                try:
                    response_str = response_data.decode('utf-8', errors='ignore')
                    if received_all:
                        logger.info(f"成功接收完整响应数据")
                    else:
                        logger.info(f"部分接收响应数据，继续尝试处理")
                    return response_str
                except Exception as e:
                    logger.error(f"解码响应数据失败: {str(e)}")
                    logger.info(f"原始响应数据: {response_data}")
                
        except socket.timeout:
            logger.warning(f"连接或接收超时，这可能是由于网络延迟或服务器响应慢")
        except ConnectionRefusedError:
            logger.error(f"连接被拒绝，服务器可能未在 {TCP_SERVER_CONFIG['host']}:{TCP_SERVER_CONFIG['port']} 监听")
        except ConnectionAbortedError:
            logger.error("连接被中止，可能是由于网络问题或服务器主动关闭连接")
        except ConnectionResetError:
            logger.error("连接被重置，服务器可能意外关闭")
        except OSError as e:
            # 特殊处理Windows上的WSAEWOULDBLOCK错误(10035)
            if hasattr(e, 'winerror') and e.winerror == 10035:
                logger.warning(f"操作系统返回非阻塞错误(10035)，这在某些环境下可能是正常的")
                # 尝试继续处理，因为这可能只是表示操作会阻塞，而非真正的错误
                continue
            else:
                logger.error(f"发生操作系统错误: {str(e)}")
        except Exception as e:
            logger.error(f"订阅过程中发生错误: {str(e)}")
            traceback.print_exc()
        
        # 如果不是最后一次重试，则等待一段时间后重试
        if retry < CONFIG["retry_count"] - 1:
            wait_time = CONFIG["retry_interval"] * (retry + 1)  # 指数退避策略
            logger.info(f"第 {retry + 1} 次尝试失败，将在 {wait_time} 秒后重试...")
            time.sleep(wait_time)
        else:
            logger.error(f"已尝试 {CONFIG['retry_count']} 次，订阅失败")
            logger.error("可能的解决方法:")
            logger.error("1. 检查网络连接和防火墙设置")
            logger.error("2. 确认服务器地址和端口是否正确")
            logger.error("3. 确认token是否有效")
            logger.error("4. 检查设备UID是否正确")
            logger.error("5. 如需持续订阅，确保在订阅结束前再次发送请求")
    
    return None

def continuous_subscription(uid: str, token: Optional[str] = None, user_name: Optional[str] = None, interval: int = 60):
    """
    持续订阅设备数据
    :param uid: 设备UID
    :param token: 可选的授权token
    :param user_name: 可选的用户名
    :param interval: 订阅间隔(秒)，建议小于120秒
    """
    try:
        logger.info(f"开始持续订阅设备 {uid} 的数据，订阅间隔: {interval}秒")
        
        while True:
            # 发送订阅请求
            response = subscribe_device_data(uid, interval, token, user_name)
            
            if response:
                try:
                    # 尝试解析JSON响应
                    response_json = json.loads(response)
                    logger.info(f"订阅成功，响应数据: {response_json}")
                except json.JSONDecodeError:
                    logger.info(f"订阅成功，原始响应: {response}")
            else:
                logger.error("订阅失败")
            
            # 等待一段时间后再次订阅(防老化机制)
            # 为了确保不间断数据，在订阅结束前几秒再次发送订阅
            wait_time = max(1, interval - 5)  # 提前5秒再次订阅
            logger.info(f"等待 {wait_time} 秒后再次订阅...")
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        logger.info("持续订阅已停止")

if __name__ == "__main__":
    """
    主程序入口
    使用说明:
    1. 请替换以下参数为实际值
    2. 可以选择单次订阅或持续订阅
    """
    # 配置参数
    device_uid = "AD8B5AB06A37"
    auth_token = "b3eb39a6-ad8d-49a3-b888-f746d80cce1f"  # 从登录接口获取的token
    user_name = "18958134531"  # 用户名
    subscription_second = 60  # 订阅时长(秒)，必须小于120秒
    skip_network_check = True  # 设置为True可跳过网络连接检查
    
    # 可选：从登录接口获取token
    get_auth_token = False
    if get_auth_token:
        login_username = "18958134531"
        login_password = "Ql123456"
        auth_token = get_access_token(login_username, login_password)
        print(f"获取到的token: {auth_token}")
    
    # 检查网络连接
    if not skip_network_check:
        if not check_network_connection(TCP_SERVER_CONFIG['host'], TCP_SERVER_CONFIG['port']):
            logger.error("网络连接检查失败")
            # 询问是否继续（仅在命令行环境下有效）
            try:
                user_input = input("是否继续尝试订阅? (y/n): ").strip().lower()
                if user_input != 'y':
                    logger.info("程序已退出")
                    exit(1)
                else:
                    logger.info("将尝试继续进行数据订阅")
            except EOFError:
                # 如果无法获取用户输入（非交互式环境），则直接退出
                logger.error("程序退出")
                exit(1)
    else:
        logger.info("已跳过网络连接检查")
    
    # 单次订阅示例
    logger.info(f"执行单次订阅，设备UID: {device_uid}")
    response = subscribe_device_data(device_uid, subscription_second, auth_token, user_name)
    
    if response:
        logger.info(f"单次订阅结果: {response}")
    else:
        logger.error("单次订阅失败")
    
    # 启动持续订阅模式
    logger.info(f"\n启动持续订阅模式")
    continuous_subscription(device_uid, auth_token, user_name, interval=subscription_second)
    
    # 提示信息
    logger.info("\n使用提示:")
    logger.info("1. 请确保替换 device_uid 为实际的设备UID")
    logger.info("2. 如果是首次订阅，请提供有效的token")
    logger.info("3. 订阅时间(second)必须小于120秒")
    logger.info("4. 如需持续监控，程序已默认启用持续订阅")
    logger.info("5. 最多支持5台设备并发订阅，超过需要联系清澜添加白名单")