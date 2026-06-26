import pygame
from ball import Ball

# Инициализация Pygame
pygame.init()

# Настройки окна
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Moving Ball Game")

# Цвета
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# Создаем мяч в центре экрана
ball = Ball(WIDTH // 2, HEIGHT // 2, radius=25, color=RED, speed=20)

# Шрифт для инструкций
font = pygame.font.Font(None, 32)

# Часы
clock = pygame.time.Clock()

# Главный цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Обработка нажатий клавиш
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                ball.move_up(HEIGHT)
            elif event.key == pygame.K_DOWN:
                ball.move_down(HEIGHT)
            elif event.key == pygame.K_LEFT:
                ball.move_left(WIDTH)
            elif event.key == pygame.K_RIGHT:
                ball.move_right(WIDTH)
    
    # Отрисовка
    screen.fill(WHITE)  # Белый фон
    
    # Рисуем мяч
    ball.draw(screen)
    
    # Инструкции
    instruction_text = font.render("Use Arrow Keys to Move", True, BLACK)
    screen.blit(instruction_text, (WIDTH // 2 - 150, 20))
    
    # Показываем позицию мяча
    pos_x, pos_y = ball.get_position()
    pos_text = font.render(f"Position: ({pos_x}, {pos_y})", True, BLACK)
    screen.blit(pos_text, (20, HEIGHT - 40))
    
    # Обновляем экран
    pygame.display.flip()
    
    # 60 FPS
    clock.tick(60)

# Выход
pygame.quit()