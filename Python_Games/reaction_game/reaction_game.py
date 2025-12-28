import pygame
import sys
import random
import time
import json
import os
from typing import List, Dict, Optional

# 游戏配置
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 马里奥游戏配色方案（柔和版）
COLORS = {
    "background": (173, 216, 230),   # 更柔和的天蓝色背景
    "primary": (220, 80, 80),        # 柔和的红色
    "secondary": (50, 50, 50),       # 深灰色文字
    "text": (50, 50, 50),            # 深灰色文字
    "button": (220, 80, 80),         # 柔和的红色按钮
    "button_hover": (180, 60, 60),   # 柔和的深红色悬停
    "square_normal": (255, 180, 0),  # 马里奥橙色方块
    "square_react": (220, 80, 80),   # 柔和的红色反应方块
    "success": (100, 200, 100),      # 柔和的绿色成功
    "warning": (50, 50, 50),         # 深灰色警告
    "danger": (220, 80, 80),        # 柔和的红色危险
    "square_invalid": (255, 180, 0),  # 马里奥橙色无效方块
    "danger": (180, 60, 60)          # 柔和的深红色危险
}

class ReactionGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("反应时间测试")
        self.clock = pygame.time.Clock()
        # 使用支持中文的字体
        self.font_large = pygame.font.SysFont("Microsoft YaHei", 72)
        self.font_medium = pygame.font.SysFont("Microsoft YaHei", 36)
        self.font_small = pygame.font.SysFont("Microsoft YaHei", 24)
        
        # 游戏状态
        self.state = "start"  # start, waiting, reacting, result, invalid
        self.reaction_time = 0
        self.start_time = 0
        self.color_change_time = 0
        self.history = self.load_history()
        self.invalid_attempt = False  # 是否提前按键
        
        # 方块属性
        self.square_size = 200
        self.square_color = COLORS["square_normal"]
        self.square_rect = pygame.Rect(
            (SCREEN_WIDTH - self.square_size) // 2,
            (SCREEN_HEIGHT - self.square_size) // 2,
            self.square_size,
            self.square_size
        )
        
        # 按钮
        self.start_button = pygame.Rect(SCREEN_WIDTH//2 - 100, 350, 200, 60)
        self.clear_button = pygame.Rect(SCREEN_WIDTH//2 - 100, 430, 200, 50)
        self.retry_button = pygame.Rect(SCREEN_WIDTH//2 - 150, 450, 140, 50)
        self.menu_button = pygame.Rect(SCREEN_WIDTH//2 + 10, 450, 140, 50)
        
        # 按钮字体
        self.font_button = pygame.font.SysFont("Microsoft YaHei", 28)
        self.font_clear = pygame.font.SysFont("Microsoft YaHei", 22)

    def load_history(self) -> List[float]:
        """加载历史记录"""
        try:
            history_path = os.path.join(os.path.dirname(__file__), "reaction_history.json")
            if os.path.exists(history_path):
                with open(history_path, "r") as f:
                    return json.load(f)
        except:
            pass
        return []

    def save_history(self):
        """保存历史记录"""
        try:
            # 只保存最好的3次记录
            best_records = sorted(self.history)[:3]
            history_path = os.path.join(os.path.dirname(__file__), "reaction_history.json")
            with open(history_path, "w") as f:
                json.dump(best_records, f)
        except:
            pass

    def draw_text(self, text: str, font, color: tuple, x: int, y: int, centered: bool = True):
        """绘制文本"""
        text_surface = font.render(text, True, color)
        if centered:
            text_rect = text_surface.get_rect(center=(x, y))
        else:
            text_rect = text_surface.get_rect(topleft=(x, y))
        self.screen.blit(text_surface, text_rect)

    def draw_button(self, rect: pygame.Rect, text: str, hover: bool = False):
        """绘制按钮"""
        color = COLORS["button_hover"] if hover else COLORS["button"]
        pygame.draw.rect(self.screen, color, rect, border_radius=15)
        pygame.draw.rect(self.screen, COLORS["primary"], rect, 3, border_radius=15)
        self.draw_text(text, self.font_button, COLORS["text"], rect.centerx, rect.centery)

    def clear_history(self):
        """清空历史记录"""
        self.history = []
        try:
            history_path = os.path.join(os.path.dirname(__file__), "reaction_history.json")
            if os.path.exists(history_path):
                os.remove(history_path)
        except:
            pass

    def start_screen(self):
        """开始界面"""
        self.screen.fill(COLORS["background"])
        
        # 标题
        self.draw_text("反应时间测试", self.font_large, COLORS["primary"], SCREEN_WIDTH//2, 120)
        
        # 说明
        self.draw_text("当屏幕变色时，立即按下空格键", self.font_medium, COLORS["text"], SCREEN_WIDTH//2, 200)
        self.draw_text("测试你的反应速度", self.font_medium, COLORS["text"], SCREEN_WIDTH//2, 250)
        
        # 开始按钮
        mouse_pos = pygame.mouse.get_pos()
        start_hover = self.start_button.collidepoint(mouse_pos)
        clear_hover = self.clear_button.collidepoint(mouse_pos)
        
        self.draw_button(self.start_button, "开始游戏", start_hover)
        
        # 清空历史按钮
        pygame.draw.rect(self.screen, COLORS["button_hover"] if clear_hover else COLORS["button"], 
                        self.clear_button, border_radius=10)
        pygame.draw.rect(self.screen, COLORS["primary"], self.clear_button, 2, border_radius=10)
        self.draw_text("清空历史记录", self.font_clear, COLORS["text"], self.clear_button.centerx, self.clear_button.centery)
        
        # 历史统计
        if self.history:
            avg_time = sum(self.history) / len(self.history)
            best_time = min(self.history)
            self.draw_text(f"平均: {avg_time:.0f}ms  最佳: {best_time:.0f}ms", 
                          self.font_small, COLORS["secondary"], SCREEN_WIDTH//2, 500)

    def game_screen(self):
        """游戏界面"""
        # 整个屏幕变色
        if self.state == "reacting":
            self.screen.fill(COLORS["square_react"])
        else:
            self.screen.fill(COLORS["background"])
        
        # 状态提示
        if self.state == "waiting":
            self.draw_text("等待变色...", self.font_medium, COLORS["text"], SCREEN_WIDTH//2, SCREEN_HEIGHT - 50)
        elif self.state == "reacting":
            self.draw_text("快按空格！", self.font_medium, COLORS["text"], SCREEN_WIDTH//2, SCREEN_HEIGHT - 50)
        elif self.state == "invalid":
            self.draw_text("请等待屏幕变色后再按空格！", self.font_medium, COLORS["danger"], SCREEN_WIDTH//2, SCREEN_HEIGHT - 50)
            self.draw_text("本轮已无效，请重新开始", self.font_small, COLORS["warning"], SCREEN_WIDTH//2, SCREEN_HEIGHT - 20)

    def result_screen(self):
        """结果界面"""
        self.screen.fill(COLORS["background"])
        
        if self.invalid_attempt:
            # 显示无效尝试
            self.draw_text("本轮无效", self.font_large, COLORS["danger"], SCREEN_WIDTH//2, 150)
            self.draw_text("请等待屏幕变色后再按空格键", self.font_medium, COLORS["text"], SCREEN_WIDTH//2, 220)
            self.draw_text("下次要耐心等待哦！", self.font_small, COLORS["secondary"], SCREEN_WIDTH//2, 260)
        else:
            # 本次成绩
            self.draw_text(f"反应时间: {self.reaction_time:.0f}ms", self.font_large, COLORS["primary"], SCREEN_WIDTH//2, 150)
            
            # 评价
            if self.reaction_time < 200:
                evaluation = "超凡反应！"
                color = COLORS["success"]
            elif self.reaction_time < 300:
                evaluation = "非常优秀"
                color = COLORS["success"]
            elif self.reaction_time < 400:
                evaluation = "良好表现"
                color = COLORS["warning"]
            else:
                evaluation = "继续努力"
                color = COLORS["danger"]
            
            self.draw_text(evaluation, self.font_medium, color, SCREEN_WIDTH//2, 220)
        
        # 历史记录 - 显示最好的3次记录
        best_records = sorted(self.history)[:3]
        if best_records:
            self.draw_text("最佳记录:", self.font_medium, COLORS["text"], SCREEN_WIDTH//2, 300)
            for i, time_val in enumerate(best_records, 1):
                self.draw_text(f"{i}. {time_val:.0f}ms", self.font_small, COLORS["text"], SCREEN_WIDTH//2, 330 + i * 30)
        
        # 按钮 - 在结果界面和无效状态都显示按钮
        mouse_pos = pygame.mouse.get_pos()
        retry_hover = self.retry_button.collidepoint(mouse_pos)
        menu_hover = self.menu_button.collidepoint(mouse_pos)
        
        self.draw_button(self.retry_button, "再试一次", retry_hover)
        self.draw_button(self.menu_button, "返回首页", menu_hover)

    def start_game(self):
        """开始新游戏"""
        self.state = "waiting"
        self.square_color = COLORS["square_normal"]
        self.start_time = time.time()
        self.color_change_time = self.start_time + random.uniform(1.0, 3.0)
        self.invalid_attempt = False

    def check_color_change(self):
        """检查是否需要变色"""
        current_time = time.time()
        if current_time >= self.color_change_time and self.state == "waiting":
            self.state = "reacting"
            self.square_color = COLORS["square_react"]
            self.color_change_time = current_time

    def handle_reaction(self):
        """处理反应"""
        current_time = time.time()
        self.reaction_time = (current_time - self.color_change_time) * 1000  # 转换为毫秒
        self.history.append(self.reaction_time)
        self.save_history()
        self.state = "result"

    def run(self):
        """主游戏循环"""
        running = True
        
        while running:
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "start":
                        if self.start_button.collidepoint(mouse_pos):
                            self.start_game()
                        elif self.clear_button.collidepoint(mouse_pos):
                            self.clear_history()
                    elif self.state == "result" or self.state == "invalid":
                        if self.retry_button.collidepoint(mouse_pos):
                            self.start_game()
                        elif self.menu_button.collidepoint(mouse_pos):
                            self.state = "start"
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if self.state == "reacting":
                            self.handle_reaction()
                        elif self.state == "waiting" and not self.invalid_attempt:
                            # 提前按键，本轮无效
                            self.state = "result"
                            self.invalid_attempt = True
                    elif event.key == pygame.K_ESCAPE:
                        if self.state == "start":
                            running = False
                        else:
                            self.state = "start"
            
            # 游戏逻辑更新
            if self.state == "waiting":
                self.check_color_change()
            
            # 绘制界面
            if self.state == "start":
                self.start_screen()
            elif self.state in ["waiting", "reacting"]:
                self.game_screen()
            elif self.state == "result":
                self.result_screen()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = ReactionGame()
    game.run()