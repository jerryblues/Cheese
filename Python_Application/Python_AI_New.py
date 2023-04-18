import pygame
import random

# 初始化 Pygame
pygame.init()

# 设置游戏窗口大小
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)

# 设置游戏标题
pygame.display.set_caption("数学游戏")

# 设置游戏字体
FONT_SIZE = 32
FONT = pygame.font.Font(None, FONT_SIZE)

# 设置游戏颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# 设置游戏时间
TIME_LIMIT = 60
TIME_FONT_SIZE = 64
TIME_FONT = pygame.font.Font(None, TIME_FONT_SIZE)

# 设置游戏得分
SCORE = 0
SCORE_FONT_SIZE = 64
SCORE_FONT = pygame.font.Font(None, SCORE_FONT_SIZE)

# 设置游戏排名
RANK = []
RANK_FONT_SIZE = 32
RANK_FONT = pygame.font.Font(None, RANK_FONT_SIZE)

# 生成随机数学题
def generate_question():
    question = []
    for i in range(10):
        operator = random.choice(["+", "-", "*", "/"])
        if operator == "+":
            a = random.randint(10, 99)
            b = random.randint(10, 99)
            answer = a + b
        elif operator == "-":
            a = random.randint(10, 99)
            b = random.randint(10, a - 1)
            answer = a - b
        elif operator == "*":
            a = random.randint(1, 9)
            b = random.randint(1, 9)
            answer = a * b
        elif operator == "/":
            b = random.randint(1, 9)
            a = b * random.randint(1, 10)
            answer = a / b
        question.append((a, b, operator, answer))
    return question

# 显示数学题
def show_question(screen, question):
    x = 100
    y = 100
    for i in range(len(question)):
        a, b, operator, answer = question[i]
        text = FONT.render(f"{a} {operator} {b} =", True, BLACK)
        screen.blit(text, (x, y))
        x += text.get_width() + 10

# 显示时间
def show_time(screen, time_left):
    text = TIME_FONT.render(str(time_left), True, RED)
    screen.blit(text, (WINDOW_WIDTH - text.get_width() - 10, 10))

# 显示得分
def show_score(screen, score):
    text = SCORE_FONT.render(f"得分：{score}", True, BLACK)
    screen.blit(text, (10, 10))

# 显示排名
def show_rank(screen, rank):
    x = 10
    y = WINDOW_HEIGHT - RANK_FONT_SIZE - 10
    text = RANK_FONT.render("排名：", True, BLACK)
    screen.blit(text, (x, y))
    x += text.get_width()
    for i in range(len(rank)):
        name, score = rank[i]
        text = RANK_FONT.render(f"{i + 1}. {name}({score})", True, BLACK)
        screen.blit(text, (x, y))
        x += text.get_width() + 10

# 游戏主循环
def main():
    global SCORE
    # 创建游戏窗口
    screen = pygame.display.set_mode(WINDOW_SIZE)

    # 生成随机数学题
    question = generate_question()

    # 设置游戏时间
    time_left = TIME_LIMIT * 60

    # 游戏主循环
    running = True
    while running:
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # 更新游戏时间
        time_left -= 1
        if time_left < 0:
            time_left = 0
            running = False

        # 清空屏幕
        screen.fill(WHITE)

        # 显示数学题
        show_question(screen, question)

        # 显示时间
        show_time(screen, time_left // 60)

        # 显示得分
        show_score(screen, SCORE)

        # 显示排名
        show_rank(screen, RANK)

        # 更新屏幕
        pygame.display.flip()

    # 计算得分
    for i in range(len(question)):
        a, b, operator, answer = question[i]
        text = FONT.render(f"{a} {operator} {b} =", True, BLACK)
        x = 100 + i * (text.get_width() + 10)
        y = 100
        input_text = ""
        while True:
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        exit()
                    elif event.key == pygame.K_RETURN:
                        try:
                            input_answer = int(input_text)
                            if input_answer == answer:
                                SCORE += 10
                            break
                        except:
                            pass
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode

            # 清空屏幕
            screen.fill(WHITE)

            # 显示数学题
            show_question(screen, question)

            # 显示时间
            show_time(screen, time_left // 60)

            # 显示得分
            show_score(screen, SCORE)

            # 显示排名
            show_rank(screen, RANK)

            # 显示输入框
            input_text_surface = FONT.render(input_text, True, BLACK)
            screen.blit(input_text_surface, (x, y))

            # 更新屏幕
            pygame.display.flip()

    # 显示得分和排名
    name = input("请输入您的姓名：")
    RANK.append((name, SCORE))
    RANK.sort(key=lambda x: x[1], reverse=True)
    print(f"您的得分是：{SCORE}")
    print("排名如下：")
    for i in range(len(RANK)):
        name, score = RANK[i]
        print(f"{i + 1}. {name}({score})")

    # 退出 Pygame
    pygame.quit()

if __name__ == "__main__":
    main()
