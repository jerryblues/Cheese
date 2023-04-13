import pygame
import random

# 初始化 Pygame
pygame.init()
CLOCK = pygame.time.Clock()

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# 游戏参数
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
NUM_QUESTIONS = 5
QUESTION_FONT_NAME = 'SimSun'
QUESTION_FONT_SIZE = 32
ANSWER_FONT_NAME = 'SimSun'
ANSWER_FONT_SIZE = 24
PADDING = 20
QUESTION_OFFSET_Y = 50
ANSWER_OFFSET_X = 400
ANSWER_OFFSET_Y = 50
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 50
BUTTON_FONT_NAME = 'SimSun'
BUTTON_FONT_SIZE = 24

# 运算符
OPERATORS = ['+', '-', '*', '/']

# 生成题目和答案
questions = []
answers = []
for i in range(NUM_QUESTIONS):
    a = random.randint(1, 100)
    b = random.randint(1, 100)
    op = random.choice(OPERATORS)
    if op == '+':
        c = a + b
    elif op == '-':
        c = a - b
    elif op == '*':
        c = a * b
    else:
        c = a // b
    question = '{} {} {} = ?'.format(a, op, b)
    answer = str(c)
    questions.append(question)
    answers.append(answer)

# 打乱答案顺序
for i in range(NUM_QUESTIONS):
    random.shuffle(answers[i])

# 创建 Pygame 窗口
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Math Quiz')

# 创建字体对象
question_font = pygame.font.SysFont(QUESTION_FONT_NAME, QUESTION_FONT_SIZE)
answer_font = pygame.font.SysFont(ANSWER_FONT_NAME, ANSWER_FONT_SIZE)
button_font = pygame.font.SysFont(BUTTON_FONT_NAME, BUTTON_FONT_SIZE)

# 创建按钮矩形对象
buttons = []
for i in range(NUM_QUESTIONS):
    button_x = ANSWER_OFFSET_X + PADDING
    button_y = ANSWER_OFFSET_Y + PADDING + i * (BUTTON_HEIGHT + PADDING)
    button_rect = pygame.Rect(button_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
    buttons.append(button_rect)

# 创建得分文本对象
score = 0
score_text = button_font.render('Score: {}'.format(score), True, BLACK)

# 游戏循环
running = True
while running:
    # 处理事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            for i in range(NUM_QUESTIONS):
                question_x = PADDING
                question_y = QUESTION_OFFSET_Y + i * (QUESTION_FONT_SIZE + PADDING)
                question_rect = pygame.Rect(question_x, question_y, question_font.size(questions[i])[0], question_font.size(questions[i])[1])
                if question_rect.collidepoint(pos):
                    for j in range(NUM_QUESTIONS):
                        answer_x = ANSWER_OFFSET_X + PADDING
                        answer_y = ANSWER_OFFSET_Y + j * (ANSWER_FONT_SIZE + PADDING)
                        answer_rect = pygame.Rect(answer_x, answer_y, answer_font.size(answers[i][j])[0], answer_font.size(answers[i][j])[1])
                        if answer_rect.collidepoint(pos):
                            if answers[i][j] == answers[i][0]:
                                buttons[i].color = GREEN
                                score += 20
                            else:
                                buttons[i].color = RED
                            score_text = button_font.render('Score: {}'.format(score), True, BLACK)

    # 绘制背景
    SCREEN.fill(WHITE)

    # 绘制题目和答案
    for i in range(NUM_QUESTIONS):
        question_x = PADDING
        question_y = QUESTION_OFFSET_Y + i * (QUESTION_FONT_SIZE + PADDING)
        question_text = question_font.render(questions[i], True, BLACK)
        SCREEN.blit(question_text, (question_x, question_y))

        for j in range(NUM_QUESTIONS):
            answer_x = ANSWER_OFFSET_X + PADDING
            answer_y = ANSWER_OFFSET_Y + j * (ANSWER_FONT_SIZE + PADDING)
            answer_text = answer_font.render(answers[i][j], True, BLACK)
            SCREEN.blit(answer_text, (answer_x, answer_y))

    # 绘制按钮
    for i in range(NUM_QUESTIONS):
        pygame.draw.rect(SCREEN, buttons[i].color, buttons[i])
        button_text = button_font.render('Ans', True, BLACK)
        button_text_x = buttons[i].x + (BUTTON_WIDTH - button_text.get_width()) // 2
        button_text_y = buttons[i].y + (BUTTON_HEIGHT - button_text.get_height()) // 2
        SCREEN.blit(button_text, (button_text_x, button_text_y))

    # 绘制得分文本
    SCREEN.blit(score_text, (SCREEN_WIDTH - PADDING - score_text.get_width(), PADDING))

    # 更新屏幕
    pygame.display.flip()

# 退出 Pygame
pygame.quit()
