import pygame
import random

WIDTH = 640
HEIGHT = 480
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("贪食蛇游戏")

snake = [(WIDTH // 2, HEIGHT // 2)]
foods = []
for i in range(3):
    food = (random.randint(0, WIDTH - 10), random.randint(0, HEIGHT - 10))
    foods.append(food)

# 新增速度变量及速度增加功能
speed = 5

# 新增生命值变量及生命值功能
life = 3

# 新增积分变量
score = 0

# 新增一个列表存储历史得分
scores = []

# 新增障碍物列表
obstacles = []

# 生命食物坐标
life_food = None


def update_snake(direction):
    global foods, speed, life, score, obstacles, life_food

    x, y = snake[0]
    if direction == 'up':
        y -= 10
    elif direction == 'down':
        y += 10
    elif direction == 'left':
        x -= 10
    elif direction == 'right':
        x += 10

    # 判断蛇头是否到达屏幕边缘
    if x < 0:
        x = WIDTH - 10
    elif x >= WIDTH:
        x = 0
    elif y < 0:
        y = HEIGHT - 10
    elif y >= HEIGHT:
        y = 0

    snake.insert(0, (x, y))

    for food in foods:
        # 判断蛇是否吃到食物，设置为10，则必须穿过食物，20则可以从食物边缘经过
        if abs(x - food[0]) < 20 and abs(y - food[1]) < 20:
            foods.remove(food)
            food = (random.randint(0, WIDTH - 10), random.randint(0, HEIGHT - 10))
            foods.append(food)

            # 判断积分是否达到1000的整数倍，如果是，生成生命食物
            score += 100
            if score % 1000 == 0:
                # life += 1
                # obstacles = []
                if not life_food:
                    life_food = (random.randint(0, WIDTH - 10), random.randint(0, HEIGHT - 10))

            # 蛇吃掉食物后，速度加1、出现障碍物
            speed += 1
            if len(obstacles) < 6:
                obstacle = (random.randint(0, WIDTH - 10), random.randint(0, HEIGHT - 10))
                obstacles.append(obstacle)

            break
    else:
        snake.pop(-1)

    return False


def check_game_over():
    global life, snake, score, scores, life_food, obstacles

    x, y = snake[0]

    # 判断是否越界
    if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
        life -= 1
        if life <= 0:
            scores.append(score)
            score = 0
            return True
        else:
            length = len(snake)
            center_x, center_y = WIDTH // 2, HEIGHT // 2
            snake = [(center_x, center_y)]
            for i in range(length - 1):
                snake.append((center_x, center_y + (i + 1) * 10))

            # 显示剩余生命值
            font = pygame.font.SysFont('Arial', 20)
            life_text = font.render(f'Life: {life}', True, (255, 255, 255))
            screen.blit(life_text, (10, 10))

            pygame.display.update()

            return False

    # 判断是否撞到自己
    for i in range(1, len(snake)):
        if snake[i] == snake[0]:
            life -= 1
            if life <= 0:
                scores.append(score)
                score = 0
                return True
            else:
                length = len(snake)
                center_x, center_y = WIDTH // 2, HEIGHT // 2
                snake = [(center_x, center_y)]
                for i in range(length - 1):
                    snake.append((center_x, center_y + (i + 1) * 10))

                # 显示剩余生命值
                font = pygame.font.SysFont('Arial', 20)
                life_text = font.render(f'Life: {life}', True, (255, 255, 255))
                screen.blit(life_text, (10, 10))

                pygame.display.update()

                return False

    # 判断是否撞到障碍物
    for obstacle in obstacles:
        if abs(x - obstacle[0]) < 10 and abs(y - obstacle[1]) < 10:
            obstacles.remove(obstacle)
            life -= 1
            if life <= 0:
                scores.append(score)
                score = 0
                return True
            break

    # 判断是否吃到生命食物
    if life_food and abs(x - life_food[0]) < 20 and abs(y - life_food[1]) < 20:
        life += 1
        life_food = None
        obstacles = []

    return False


def game():
    global life, snake, score, scores, life_food, obstacles, foods, speed

    direction = 'right'
    game_over = False
    clock = pygame.time.Clock()

    paused = False

    while not game_over:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and direction != 'down':
                    direction = 'up'
                elif event.key == pygame.K_DOWN and direction != 'up':
                    direction = 'down'
                elif event.key == pygame.K_LEFT and direction != 'right':
                    direction = 'left'
                elif event.key == pygame.K_RIGHT and direction != 'left':
                    direction = 'right'
                elif event.key == pygame.K_SPACE:
                    paused = not paused

        if not paused:
            update_snake(direction)

        if check_game_over():
            game_over = True

        screen.fill((0, 0, 0))

        # 绘制食物
        for food in foods:
            # pygame.draw.rect(screen, BLUE, pygame.Rect(food[0], food[1], 15, 15))
            pygame.draw.polygon(screen, BLUE,
                                [(food[0] + 7.5, food[1]), (food[0] + 15, food[1] + 7.5), (food[0] + 7.5, food[1] + 15), (food[0], food[1] + 7.5)])
        # 绘制障碍物
        for obstacle in obstacles:
            pygame.draw.rect(screen, RED, pygame.Rect(obstacle[0], obstacle[1], 12, 12))

        # 绘制生命食物
        if life_food:
            # 方形
            # pygame.draw.rect(screen, YELLOW, pygame.Rect(life_food[0], life_food[1], 12, 12))
            # 三星形
            x, y = life_food
            size = 10  # 三角形的大小
            pygame.draw.polygon(screen, YELLOW, [(x, y + 2 * size), (x + 2 * size, y + 2 * size), (x + size, y)], 0)

        # 绘制蛇
        for i, point in enumerate(snake):
            if i == 0:
                pygame.draw.circle(screen, YELLOW, point, 10)
            else:
                pygame.draw.circle(screen, GREEN, point, 10)

        # pygame.draw.rect(screen, GREEN, pygame.Rect(snake[0][0], snake[0][1], 10, 10))
        # for i in range(1, len(snake)):
        #     pygame.draw.rect(screen, GREEN, pygame.Rect(snake[i][0], snake[i][1], 10, 10))

        # 显示生命值
        font = pygame.font.SysFont('Arial', 20)
        life_text = font.render(f'Life: {life}', True, (255, 255, 255))
        screen.blit(life_text, (10, 10))

        # 显示积分
        score_text = font.render(f'Score: {score}', True, (255, 255, 255))
        screen.blit(score_text, (WIDTH - 110, 10))

        clock.tick(speed)

        pygame.display.update()

    # 游戏结束后，显示积分表
    font = pygame.font.SysFont('Arial', 30)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
                elif event.key == pygame.K_SPACE:
                    # 重新开始游戏
                    snake = [(WIDTH // 2, HEIGHT // 2)]
                    foods = []
                    for i in range(3):
                        food = (random.randint(0, WIDTH - 10), random.randint(0, HEIGHT - 10))
                        foods.append(food)

                    # 重置速度、生命值、积分、障碍物、生命食物
                    speed = 5
                    life = 3
                    score = 0
                    obstacles = []
                    life_food = None

                    game()
            elif event.type == pygame.QUIT:
                pygame.quit()
                exit()

        # 显示当前得分以及历史得分
        screen.fill((0, 0, 0))
        score_text = font.render(f'Your Score: {score}', True, (255, 255, 255))
        screen.blit(score_text, (WIDTH // 2 - 100, HEIGHT // 2 - 50))

        history_text = font.render('Score History:', True, (255, 255, 255))
        screen.blit(history_text, (WIDTH // 2 - 100, HEIGHT // 2 + 20))

        for i in range(len(scores)):
            score_item = font.render(f'{i+1}. {scores[i]}', True, (255, 255, 255))
            screen.blit(score_item, (WIDTH // 2 - 100, HEIGHT // 2 + 20 + 40 * (i+1)))

        restart_text = font.render('Press SPACE to restart, ESC to quit', True, (255, 255, 255))
        screen.blit(restart_text, (WIDTH // 2 - 250, HEIGHT - 50))

        pygame.display.update()


game()
