import tkinter as tk
from tkinter import ttk
import datetime
import time

class DesktopClock:
    def __init__(self, root):
        self.root = root
        self.root.title("桌面时钟")
        
        # 设置窗口属性
        self.root.overrideredirect(True)  # 无边框窗口
        self.root.attributes('-alpha', 0.9)  # 透明度
        self.root.attributes('-topmost', True)  # 默认置顶
        self.root.configure(bg='white')  # 设置窗口背景为白色
        
        # 设置窗口可拖动
        self.root.bind('<Button-1>', self.start_drag)
        self.root.bind('<B1-Motion>', self.on_drag)
        
        # 创建一个frame来组织日期和时间标签
        self.content_frame = tk.Frame(root, bg='white')
        self.content_frame.pack(padx=10, pady=5)
        
        # 创建日期标签（左侧）
        self.date_label = tk.Label(
            self.content_frame,
            font=('JetBrains Mono', 16, 'bold'),
            bg='white',
            fg='#666666',
            bd=0,
            padx=5
        )
        self.date_label.pack(side=tk.LEFT)
        
        # 创建时间标签（右侧）
        self.time_label = tk.Label(
            self.content_frame,
            font=('JetBrains Mono', 16, 'bold'),
            bg='white',
            fg='#666666',
            bd=0,
            padx=5
        )
        self.time_label.pack(side=tk.LEFT)
        
        # 创建右键菜单
        self.create_menu()
        self.root.bind('<Button-3>', self.show_menu)
        
        # 更新时间
        self.update_time()
        
    def create_menu(self):
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="取消置顶", command=self.toggle_topmost)
        self.menu.add_separator()
        self.menu.add_command(label="退出", command=self.root.quit)
        
        # 存储当前置顶状态（与窗口实际状态一致）
        self.is_topmost = True
        
    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)
        
    def toggle_topmost(self):
        self.is_topmost = not self.is_topmost
        self.root.attributes('-topmost', self.is_topmost)
        # 根据当前状态更新菜单项文本
        self.menu.entryconfig(0, label="取消置顶" if self.is_topmost else "置顶")
        
    def start_drag(self, event):
        self.x = event.x
        self.y = event.y
        
    def on_drag(self, event):
        # 获取当前窗口的尺寸
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 计算新的位置
        new_x = self.root.winfo_x() + event.x - self.x
        new_y = self.root.winfo_y() + event.y - self.y
        
        # 确保窗口不会超出屏幕边界
        new_x = max(0, min(new_x, screen_width - window_width))
        new_y = max(0, min(new_y, screen_height - window_height))
        
        # 应用新位置
        self.root.geometry(f"+{new_x}+{new_y}")
        
    def update_time(self):
        # 获取当前完整时间，包括秒
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")
        current_date = now.strftime("%m-%d")
        
        # 检查是否需要更新时间：
        # 1. 如果是首次运行
        # 2. 如果分钟已变化
        # 3. 如果当前秒数接近0（确保与系统时间同步）
        if not hasattr(self, 'last_time') or self.last_time != current_time or (now.second == 0 and hasattr(self, 'last_second') and self.last_second != 0):
            self.time_label.config(text=current_time)
            self.last_time = current_time
        
        # 检查是否需要更新日期
        if not hasattr(self, 'last_date') or self.last_date != current_date:
            self.date_label.config(text=current_date)
            self.last_date = current_date
        
        # 记录当前秒数用于下次比较
        self.last_second = now.second
        
        # 每500毫秒检查一次，提高同步精度
        self.root.after(500, self.update_time)

if __name__ == "__main__":
    root = tk.Tk()
    app = DesktopClock(root)
    root.mainloop()