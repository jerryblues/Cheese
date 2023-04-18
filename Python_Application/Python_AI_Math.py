import pygame
import random
import sys

pygame.init()

screen_width = 800  # 屏幕宽度
screen_height = 600  # 屏幕高度
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('四则运算')

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

MARGIN_TOP = 100
LINE_SPACING = 50
ANSWER_MARGIN_TOP = 20

questions = []
for i in range(5):
    # 加法
    num1 = random.randint(10, 99)
    num2 = random.randint(10, 99)
    answer = num1 + num2
    options = [answer + random.randint(1, 20), answer - random.randint(1, 20)]
    options.append(answer)
    random.shuffle(options)
    question = f'{num1} + {num2} = ?'
    questions.append((question, answer, options))

    # 减法
    num1 = random.randint(10, 99)
    num2 = random.randint(10, num1)
    answer = num1 - num2
    options = [answer + random.randint(1, 20), answer - random.randint(1, 20)]
    options.append(answer)
    random.shuffle(options)
    question = f'{num1} - {num2} = ?'
    questions.append((question, answer, options))

    # 乘法
    num1 = random.randint(1, 9)
    num2 = random.randint(1, 9)
    answer = num1 * num2
    options = [answer + random.randint(1, 20), answer - random.randint(1, 20)]
    options.append(answer)
    random.shuffle(options)
    question = f'{num1} × {num2} = ?'
    questions.append((question, answer, options))

    # 除法
    num1 = random.randint(1, 81)
    num2 = random.randint(1, 9)
    answer = num1 // num2
    num1 = answer * num2
    options = [answer + random.randint(1, 20), answer - random.randint(1, 20)]
    options.append(answer)
    random.shuffle(options)
    question = f'{num1} ÷ {num2} = ?'
    questions.append((question, answer, options))


class Button:
    def __init__(self, text, x, y, width, height, font):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font

    def is_mouse_over(self, pos):
        mouse_x, mouse_y = pos
        return self.x <= mouse_x <= self.x + self.width and self.y <= mouse_y <= self.y + self.height

    def draw(self, surface, color):
        pygame.draw.rect(surface, color, (self.x, self.y, self.width, self.height))
        text_surface = self.font.render(self.text, True, BLACK)
        text_x = self.x + (self.width - text_surface.get_width()) / 2
        text_y = self.y + (self.height - text_surface.get_height()) / 2
        surface.blit(text_surface, (text_x, text_y))


# 题目索引
question_index = 0

# 答对数量
correct_count = 0

# 游戏是否结束的标志
game_over = False

# 初始化答案提示
answer_text = pygame.font.SysFont('Simsun', 32).render('', True, BLACK)

# 循环游戏
while not game_over:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_over = True
        # 按下 ESC 键退出游戏
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            game_over = True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                pos = pygame.mouse.get_pos()
                for i in range(len(options_buttons)):
                    if options_buttons[i].is_mouse_over(pos):
                        selected_answer = i
                        # 判断答案是否正确
                        if selected_answer == correct_answer_index:
                            print('第', question_index + 1, '题：回答正确')
                            correct_count += 1
                            answer_text = pygame.font.SysFont('Simsun', 32).render('回答正确', True, (0, 255, 0))
                        else:
                            print('第', question_index + 1, '题：回答错误')
                            answer_text = pygame.font.SysFont('Simsun', 32).render('回答错误', True, (255, 0, 0))

                        question_index += 1
                        if question_index == len(questions):
                            game_over = True

    screen.fill(WHITE)

    # 显示题目和选项
    if question_index < len(questions):
        question_text = pygame.font.SysFont('Simsun', 48).render(questions[question_index][0], True, BLACK)
        question_x = (screen_width - question_text.get_width()) / 2
        question_y = MARGIN_TOP
        screen.blit(question_text, (question_x, question_y))

        options_buttons = []
        options_text_height = 0
        options_y = question_y + question_text.get_height() + LINE_SPACING + ANSWER_MARGIN_TOP
        for i in range(len(questions[question_index][2])):
            option_text = str(questions[question_index][2][i])
            option_button = Button(option_text, 0, options_y, 0, 0, pygame.font.SysFont('Simsun', 32))
            option_button.width = option_button.font.size(option_button.text)[0] + 20
            option_button.height = option_button.font.size(option_button.text)[1] + 10
            option_button.x = (screen_width - option_button.width * len(questions[question_index][2])) / (len(questions[question_index][2]) + 1) * (
                    i + 1) + option_button.width * i
            option_button.draw(screen, (200, 200, 200))
            options_buttons.append(option_button)

            # 计算选项高度，用于计算输入框位置
            options_text_height = max(options_text_height, option_button.height)

            # 记录正确答案选项的索引
            if questions[question_index][2][i] == questions[question_index][1]:
                correct_answer_index = i

        # 显示答案提示
        answer_text_x = (screen_width - answer_text.get_width()) / 2
        answer_text_y = options_y + options_text_height + LINE_SPACING
        screen.blit(answer_text, (answer_text_x, answer_text_y))

        # 显示答对数量
        correct_count_text = pygame.font.SysFont('Simsun', 32).render(f'正确/总数：{correct_count}/{len(questions)}', True, BLACK)
        correct_count_x = (screen_width - correct_count_text.get_width()) / 2
        correct_count_y = answer_text_y + answer_text.get_height() + LINE_SPACING
        screen.blit(correct_count_text, (correct_count_x, correct_count_y))

    # 显示总分和结束游戏
    else:
        # 计算总分数
        total_score = correct_count * 10

        # 显示总分数和答对的数量
        score_font = pygame.font.SysFont('Simsun', 48)
        score_text = score_font.render(f"总分：{total_score}", True, BLACK)
        score_text_rect = score_text.get_rect(center=(screen_width / 2, screen_height / 2 - 150))

        count_text = score_font.render(f"正确：{correct_count}", True, BLACK)
        count_text_rect = count_text.get_rect(center=(screen_width / 2, screen_height / 2 - 50))

        total_text = score_font.render(f"总数：{len(questions)}", True, BLACK)
        total_text_rect = total_text.get_rect(center=(screen_width / 2, screen_height / 2 + 50))

        screen.blit(score_text, score_text_rect)
        screen.blit(count_text, count_text_rect)
        screen.blit(total_text, total_text_rect)

        # 显示结束游戏提示
        end_game_text = pygame.font.SysFont('Simsun', 32).render('按 Esc 退出游戏', True, BLACK)
        end_game_x = (screen_width - end_game_text.get_width()) / 2
        end_game_y = total_text_rect.bottom + LINE_SPACING
        screen.blit(end_game_text, (end_game_x, end_game_y))

        # 更新屏幕
        pygame.display.update()

        # 等待按下 ESC 键
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            # 每帧都要更新一下屏幕，确保结束游戏提示能够正常显示
            pygame.display.update()

    pygame.display.update()

pygame.quit()
