import subprocess
import time
import requests
import logging
import sys

# --- 配置区 ---
SERVER_IP = "10.1.10.147"
SERVER_PORT = "8001"
STREAMER_URL = f"http://{SERVER_IP}:{SERVER_PORT}"
CONTAINER_NAME = "webrtc-stress"
NODE_SCRIPT = "stress.js"
LOG_FILE = "output.log"

# --- 日志配置 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout) # 同时在屏幕打印，方便 tail -f
    ]
)
logger = logging.getLogger("StressTester")

def get_webrtc_connections():
    """获取活跃 WebRTC 连接数"""
    try:
        response = requests.get(f"{STREAMER_URL}/api/getPeerConnectionList", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return len(data) if isinstance(data, list) else 0
    except Exception as e:
        return f"Error: {e}"
    return 0

def get_docker_stats():
    """获取 Docker CPU 和 内存占用"""
    try:
        # --no-stream 模式获取一次性快照
        cmd = f"docker stats {CONTAINER_NAME} --no-stream --format '{{{{.CPUPerc}}}} | {{{{.MemUsage}}}}'"
        result = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        return result
    except Exception as e:
        return f"Stats Error: {e}"

def main():
    logger.info("=== 压测监控主程序启动 ===")
    
    # 1. 启动 Node.js 压测脚本
    logger.info(f"正在启动 Node.js 脚本: {NODE_SCRIPT}")
    
    # 将 Node 的标准输出和错误也重定向到同一个日志文件
    try:
        with open(LOG_FILE, "a") as log_out:
            node_process = subprocess.Popen(
                ["node", NODE_SCRIPT],
                stdout=log_out,
                stderr=log_out,
                bufsize=1,
                universal_newlines=True
            )
        
        logger.info(f"Node.js 进程已启动 (PID: {node_process.pid})")
        logger.info("-" * 50)

        while True:
            # 2. 每 10 秒获取一次数据
            time.sleep(10)
            
            connections = get_webrtc_connections()
            stats = get_docker_stats()
            
            # 3. 使用 logging 输出整合信息
            logger.info(f"STATUS | 活跃连接数: {connections} | Docker 负载: {stats}")
            
            # 检查 Node 进程是否结束
            # if node_process.poll() is not None:
                # logger.warning("Node.js 压测指令发送进程已结束")
                # 这里不退出循环，继续监控服务器状态，直到手动 Ctrl+C
                
    except KeyboardInterrupt:
        logger.info("检测到 Ctrl+C，正在清理进程并退出...")
        node_process.terminate()
        logger.info("已停止 Node.js 进程。")
    except Exception as e:
        logger.error(f"主程序异常: {e}")

if __name__ == "__main__":
    main()
