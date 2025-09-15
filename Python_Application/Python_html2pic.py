import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# 配置HTML文件路径（在这里修改要转换的HTML文件路径）
HTML_FILE_PATH = r"C:/Users/howar/Downloads/tension-relaxation-webpage.html"

def html_to_image(html_path):
    """将HTML文件转换为PNG图片，保存在HTML文件同目录下"""
    # 检查HTML文件是否存在
    if not os.path.exists(html_path):
        print(f"错误: HTML文件 '{html_path}' 不存在")
        return None
    
    # 设置输出路径为HTML文件同目录下的同名PNG图片
    output_path = os.path.splitext(html_path)[0] + ".png"
    
    # 设置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        # 初始化WebDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 加载HTML文件
        html_absolute_path = os.path.abspath(html_path)
        driver.get(f"file:///{html_absolute_path}")
        
        # 等待页面初始加载
        time.sleep(2)
        
        # 滚动到页面底部并等待动态内容加载
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            # 滚动到底部
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # 等待新内容加载
            
            # 计算新的滚动高度并比较
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break  # 如果高度不再增加，说明已经到底部
            last_height = new_height
        
        # 滚动回顶部
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)  # 等待滚动完成
        
        # 获取页面实际尺寸
        width = driver.execute_script("return Math.max(document.body.scrollWidth, document.body.offsetWidth, document.documentElement.clientWidth, document.documentElement.scrollWidth, document.documentElement.offsetWidth);")
        height = driver.execute_script("return Math.max(document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);")
        
        # 设置窗口大小为页面实际大小
        driver.set_window_size(width + 100, height + 100)  # 添加一些边距
        
        # 再次等待以确保页面完全渲染
        time.sleep(1)
        
        # 截图
        driver.save_screenshot(output_path)
        print(f"成功将HTML转换为PNG图片: {output_path}")
        
        # 关闭WebDriver
        driver.quit()
        
        return output_path
    
    except Exception as e:
        print(f"转换过程中出错: {str(e)}")
        return None

if __name__ == "__main__":
    result = html_to_image(HTML_FILE_PATH)
    if result is None:
        sys.exit(1)
    else:
        sys.exit(0)