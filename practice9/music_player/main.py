import pygame
from player import MusicPlayer

# Инициализация Pygame
pygame.init()

# Настройки окна
WIDTH, HEIGHT = 800, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Music Player")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
GREEN = (0, 200, 0)
RED = (255, 0, 0)

# Шрифты
font_title = pygame.font.Font(None, 56)
font_info = pygame.font.Font(None, 36)
font_controls = pygame.font.Font(None, 28)

# Создаем плеер
music_player = MusicPlayer("music")

# Часы
clock = pygame.time.Clock()

# Главный цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Обработка клавиш
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:  # Play
                music_player.play()
            elif event.key == pygame.K_s:  # Stop
                music_player.stop()
            elif event.key == pygame.K_n:  # Next
                music_player.next_track()
            elif event.key == pygame.K_b:  # Back (Previous)
                music_player.previous_track()
            elif event.key == pygame.K_q:  # Quit
                running = False
    
    # Отрисовка
    screen.fill(WHITE)
    
    # Заголовок
    title = font_title.render("🎵 Music Player 🎵", True, BLUE)
    title_rect = title.get_rect(center=(WIDTH // 2, 50))
    screen.blit(title, title_rect)
    
    # Линия разделитель
    pygame.draw.line(screen, BLACK, (50, 100), (WIDTH - 50, 100), 2)
    
    # Текущий трек
    if music_player.has_tracks():
        track_name = music_player.get_current_track_name()
        track_text = font_info.render(f"Now: {track_name}", True, BLACK)
        screen.blit(track_text, (50, 130))
    else:
        no_tracks = font_info.render("No tracks in folder!", True, RED)
        screen.blit(no_tracks, (50, 130))
    
    # Статус плеера
    status = music_player.get_status()
    status_color = GREEN if music_player.is_playing else RED
    status_text = font_info.render(f"Status: {status}", True, status_color)
    screen.blit(status_text, (50, 180))
    
    # Линия разделитель
    pygame.draw.line(screen, BLACK, (50, 240), (WIDTH - 50, 240), 2)
    
    # Инструкции (управление)
    controls_title = font_info.render("Controls:", True, BLACK)
    screen.blit(controls_title, (50, 260))
    
    instructions = [
        "P - Play",
        "S - Stop",
        "N - Next Track",
        "B - Previous Track",
        "Q - Quit"
    ]
    
    y_pos = 310
    for instruction in instructions:
        text = font_controls.render(f"• {instruction}", True, BLACK)
        screen.blit(text, (70, y_pos))
        y_pos += 35
    
    # Обновляем экран
    pygame.display.flip()
    
    # 60 FPS
    clock.tick(60)

# Выход
pygame.quit()