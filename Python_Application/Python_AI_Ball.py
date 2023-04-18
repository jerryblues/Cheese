import pygame
import random

# 初始化 Pygame
pygame.init()

# 定义屏幕大小
screen_width = 600
screen_height = 800
screen = pygame.display.set_mode((screen_width, screen_height))

# 设置游戏标题
pygame.display.set_caption("接球游戏")

# 定义颜色
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (20, 255, 140)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# 定义小球类
class Ball:
    def __init__(self, x):
        self.x = x
        self.y = 0
        self.color = random.choice([BLUE, GREEN, RED])
        self.radius = random.randint(10, 20)
        self.speed = 5
        self.acceleration = 0.1

    def move(self):
        self.y += self.speed
        self.speed += self.acceleration

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

# 定义筐子类
class Basket:
    def __init__(self, x):
        self.x = x
        self.y = screen_height - 50
        self.width = 120
        self.height = 20
        self.speed = 20
        self.move_left_flag = False
        self.move_right_flag = False

    def move_left(self):
        self.move_left_flag = True

    def move_right(self):
        self.move_right_flag = True

    def stop(self):
        self.move_left_flag = False
        self.move_right_flag = False

    def update(self):
        if self.move_left_flag:
            self.x -= self.speed
            if self.x < 0:
                self.x = 0
        elif self.move_right_flag:
            self.x += self.speed
            if self.x > screen_width - self.width:
                self.x = screen_width - self.width

    def draw(self):
        pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height))

# 初始化球和筐子
balls = []
basket = Basket(screen_width//2)

# 定义字体
font = pygame.font.SysFont(None, 36)

# 游戏循环
clock = pygame.time.Clock()
game_over = False
score = 0
missed_balls = 0
while not game_over:

    # 控制帧率
    clock.tick(60)

    # 处理事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_over = True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                basket.move_left()
            elif event.key == pygame.K_RIGHT:
                basket.move_right()
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                basket.stop()

    # 添加新的球
    if random.randint(0, 59) == 0:
        ball = Ball(random.randint(20, screen_width-20))
        balls.append(ball)

    # 移动球
    for ball in balls:
        ball.move()

    # 碰撞检测
    for ball in balls:
        if abs(ball.y - basket.y) <= ball.radius and \
                basket.x - ball.radius <= ball.x <= basket.x + basket.width + ball.radius:
            balls.remove(ball)
            score += 1
            missed_balls = max(missed_balls-1, 0)
        elif ball.y > screen_height + ball.radius:
            balls.remove(ball)
            missed_balls += 1

    # 判断是否游戏结束
    if missed_balls >= 15:
        game_over = True

    # 删除离开屏幕的球
    balls = [ball for ball in balls if ball.y < screen_height+50]

    # 更新筐子位置
    basket.update()

    # 绘制背景、球和筐子，并在屏幕上显示当前得分和漏掉的球数
    screen.fill(BLACK)
    for ball in balls:
        ball.draw()
    basket.draw()
    text_score = font.render(f"Score: {score}", True, WHITE)
    text_missed_balls = font.render(f"Missed balls: {missed_balls}/15", True, WHITE)
    screen.blit(text_score, (10, 10))
    screen.blit(text_missed_balls, (10, 50))

    # 更新屏幕
    pygame.display.update()

# 显示最终得分并退出 Pygame
final_text = font.render(f"Game Over! Your final score is {score}", True, WHITE)
screen.blit(final_text, (screen_width//2 - final_text.get_width()//2, screen_height//2))
pygame.display.update()
pygame.time.delay(3000)
pygame.quit()
