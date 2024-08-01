# coding=utf-8
"""
@file: Python_check_port.py.py
@time: 2024/3/24 17:19
@author: h4zhang
"""

import socket


def scan_port(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)  # Timeout to make the scanning faster
        result = sock.connect_ex((ip, port))
        if result == 0:
            print(f"Port {port} is open")
            return port
        else:
            print(f"Port {port} is closed")
        sock.close()
    except Exception as e:
        print(f"Error scanning port {port}: {str(e)}")


def main(target_ip, start_port, end_port):
    port_list = []
    for port in range(start_port, end_port + 1):
        open_port = scan_port(target_ip, port)
        if open_port:
            port_list.append(open_port)
    print(f"Open port: {port_list}")


if __name__ == "__main__":
    target = "10.57.195.35"  # Example IP address
    startPort = 1
    endPort = 65535
    # open port for 10.57.195.35
    # 22, 2000, 5060, 8080, 10001
    #

    main(target, startPort, endPort)
