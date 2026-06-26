import pygame
from pygame.locals import *
from persistence import load_leaderboard, save_settings

# Colors
BLACK  = (0, 0, 0)
WHITE  = (255, 255, 255)
GRAY   = (180, 180, 180)
DARK   = (40, 40, 40)
RED    = (220, 50, 50)
GREEN  = (50, 200, 80)
YELLOW = (255, 220, 0)
BLUE   = (50, 100, 220)
ORANGE = (255, 140, 0)

SCREEN_WIDTH  = 400
SCREEN_HEIGHT = 600

font_big   = None
font_med   = None
font_small = None
font_tiny  = None

def _init_fonts():
    global font_big, font_med, font_small, font_tiny
    if font_big is None:
        font_big   = pygame.font.SysFont("Verdana", 48, bold=True)
        font_med   = pygame.font.SysFont("Verdana", 28)
        font_small = pygame.font.SysFont("Verdana", 20)
        font_tiny  = pygame.font.SysFont("Verdana", 16)


def draw_button(surf, text, rect, color=BLUE, hover=False):
    c = tuple(min(255, v + 30) for v in color) if hover else color
    pygame.draw.rect(surf, c, rect, border_radius=10)
    pygame.draw.rect(surf, WHITE, rect, 2, border_radius=10)
    label = font_small.render(text, True, WHITE)
    lx = rect.x + (rect.width  - label.get_width())  // 2
    ly = rect.y + (rect.height - label.get_height()) // 2
    surf.blit(label, (lx, ly))


def draw_panel(surf, rect, alpha=200):
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel.fill((0, 0, 0, alpha))
    surf.blit(panel, (rect.x, rect.y))


# ===================== USERNAME SCREEN =====================
def username_screen(surf):
    """Ask player for their name. Returns the entered name string."""
    _init_fonts()
    clock = pygame.time.Clock()
    name = ""
    active = True

    input_rect = pygame.Rect(80, 280, 240, 44)

    while active:
        surf.fill(DARK)

        title = font_big.render("RACER", True, YELLOW)
        surf.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

        sub = font_med.render("Enter your name:", True, WHITE)
        surf.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 210))

        pygame.draw.rect(surf, WHITE, input_rect, border_radius=8)
        pygame.draw.rect(surf, YELLOW, input_rect, 2, border_radius=8)
        name_surf = font_med.render(name + "|", True, BLACK)
        surf.blit(name_surf, (input_rect.x + 8, input_rect.y + 8))

        hint = font_tiny.render("Press ENTER to continue", True, GRAY)
        surf.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 350))

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                import sys; sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_RETURN and name.strip():
                    active = False
                elif event.key == K_BACKSPACE:
                    name = name[:-1]
                elif len(name) < 16 and event.unicode.isprintable():
                    name += event.unicode

        pygame.display.update()
        clock.tick(60)

    return name.strip()


# ===================== MAIN MENU =====================
def main_menu(surf):
    """Returns: 'play', 'leaderboard', 'settings', 'quit'"""
    _init_fonts()
    clock = pygame.time.Clock()
    buttons = {
        "play":        pygame.Rect(120, 200, 160, 48),
        "leaderboard": pygame.Rect(120, 268, 160, 48),
        "settings":    pygame.Rect(120, 336, 160, 48),
        "quit":        pygame.Rect(120, 404, 160, 48),
    }
    labels = {
        "play": "Play",
        "leaderboard": "Leaderboard",
        "settings": "Settings",
        "quit": "Quit"
    }
    colors = {
        "play": GREEN,
        "leaderboard": BLUE,
        "settings": ORANGE,
        "quit": RED
    }

    while True:
        surf.fill(DARK)
        mouse = pygame.mouse.get_pos()

        title = font_big.render("RACER", True, YELLOW)
        surf.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        sub = font_tiny.render("Arcade Driving Game", True, GRAY)
        surf.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 162))

        for key, rect in buttons.items():
            hover = rect.collidepoint(mouse)
            draw_button(surf, labels[key], rect, colors[key], hover)

        for event in pygame.event.get():
            if event.type == QUIT:
                return "quit"
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                for key, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        return key

        pygame.display.update()
        clock.tick(60)


# ===================== SETTINGS SCREEN =====================
def settings_screen(surf, settings):
    """Modify settings dict in place. Returns updated settings."""
    _init_fonts()
    clock = pygame.time.Clock()

    car_colors = ["blue", "red", "green", "yellow"]
    difficulties = ["easy", "normal", "hard"]

    back_rect = pygame.Rect(130, 500, 140, 44)

    while True:
        surf.fill(DARK)
        mouse = pygame.mouse.get_pos()

        title = font_med.render("Settings", True, YELLOW)
        surf.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

        # --- Sound toggle ---
        sound_label = font_small.render("Sound:", True, WHITE)
        surf.blit(sound_label, (60, 130))
        sound_rect = pygame.Rect(240, 126, 100, 36)
        sound_text = "ON" if settings["sound"] else "OFF"
        sound_color = GREEN if settings["sound"] else RED
        draw_button(surf, sound_text, sound_rect, sound_color, sound_rect.collidepoint(mouse))

        # --- Car color ---
        color_label = font_small.render("Car color:", True, WHITE)
        surf.blit(color_label, (60, 210))
        cur_color_idx = car_colors.index(settings["car_color"]) if settings["car_color"] in car_colors else 0
        prev_c_rect = pygame.Rect(190, 206, 36, 36)
        next_c_rect = pygame.Rect(320, 206, 36, 36)
        draw_button(surf, "<", prev_c_rect, BLUE, prev_c_rect.collidepoint(mouse))
        draw_button(surf, ">", next_c_rect, BLUE, next_c_rect.collidepoint(mouse))
        cc_surf = font_small.render(settings["car_color"].capitalize(), True, YELLOW)
        surf.blit(cc_surf, (240, 214))

        # --- Difficulty ---
        diff_label = font_small.render("Difficulty:", True, WHITE)
        surf.blit(diff_label, (60, 290))
        cur_diff_idx = difficulties.index(settings["difficulty"]) if settings["difficulty"] in difficulties else 1
        prev_d_rect = pygame.Rect(190, 286, 36, 36)
        next_d_rect = pygame.Rect(320, 286, 36, 36)
        draw_button(surf, "<", prev_d_rect, BLUE, prev_d_rect.collidepoint(mouse))
        draw_button(surf, ">", next_d_rect, BLUE, next_d_rect.collidepoint(mouse))
        dd_surf = font_small.render(settings["difficulty"].capitalize(), True, YELLOW)
        surf.blit(dd_surf, (240, 294))

        # --- Back ---
        draw_button(surf, "Back", back_rect, GRAY, back_rect.collidepoint(mouse))

        for event in pygame.event.get():
            if event.type == QUIT:
                save_settings(settings)
                return settings
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                if sound_rect.collidepoint(event.pos):
                    settings["sound"] = not settings["sound"]
                elif prev_c_rect.collidepoint(event.pos):
                    settings["car_color"] = car_colors[(cur_color_idx - 1) % len(car_colors)]
                elif next_c_rect.collidepoint(event.pos):
                    settings["car_color"] = car_colors[(cur_color_idx + 1) % len(car_colors)]
                elif prev_d_rect.collidepoint(event.pos):
                    settings["difficulty"] = difficulties[(cur_diff_idx - 1) % len(difficulties)]
                elif next_d_rect.collidepoint(event.pos):
                    settings["difficulty"] = difficulties[(cur_diff_idx + 1) % len(difficulties)]
                elif back_rect.collidepoint(event.pos):
                    save_settings(settings)
                    return settings

        pygame.display.update()
        clock.tick(60)


# ===================== LEADERBOARD SCREEN =====================
def leaderboard_screen(surf):
    _init_fonts()
    clock = pygame.time.Clock()
    board = load_leaderboard()
    back_rect = pygame.Rect(140, 540, 120, 40)

    while True:
        surf.fill(DARK)
        mouse = pygame.mouse.get_pos()

        title = font_med.render("Leaderboard", True, YELLOW)
        surf.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 20))

        # Header
        hdr = font_tiny.render("Rank  Name            Score   Dist", True, GRAY)
        surf.blit(hdr, (20, 70))
        pygame.draw.line(surf, GRAY, (20, 90), (380, 90), 1)

        for i, entry in enumerate(board[:10]):
            color = YELLOW if i == 0 else (GRAY if i >= 3 else WHITE)
            row = f"#{i+1:<4} {entry['name'][:12]:<14} {entry['score']:<7} {int(entry['distance'])}m"
            row_surf = font_tiny.render(row, True, color)
            surf.blit(row_surf, (20, 100 + i * 42))

        if not board:
            empty = font_small.render("No scores yet!", True, GRAY)
            surf.blit(empty, (SCREEN_WIDTH // 2 - empty.get_width() // 2, 200))

        draw_button(surf, "Back", back_rect, BLUE, back_rect.collidepoint(mouse))

        for event in pygame.event.get():
            if event.type == QUIT:
                return
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(event.pos):
                    return
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                return

        pygame.display.update()
        clock.tick(60)


# ===================== GAME OVER SCREEN =====================
def game_over_screen(surf, score, distance, coins):
    """Returns: 'retry' or 'menu'"""
    _init_fonts()
    clock = pygame.time.Clock()
    retry_rect   = pygame.Rect(60,  440, 120, 48)
    menu_rect    = pygame.Rect(220, 440, 120, 48)

    while True:
        surf.fill(DARK)
        mouse = pygame.mouse.get_pos()

        title = font_big.render("Game Over", True, RED)
        surf.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

        lines = [
            ("Score",    str(score),          YELLOW),
            ("Distance", f"{int(distance)} m", WHITE),
            ("Coins",    str(coins),           YELLOW),
        ]
        for idx, (label, val, color) in enumerate(lines):
            lbl_s = font_small.render(label + ":", True, GRAY)
            val_s = font_med.render(val, True, color)
            y = 200 + idx * 70
            surf.blit(lbl_s, (80, y))
            surf.blit(val_s, (80, y + 24))

        draw_button(surf, "Retry",     retry_rect, GREEN, retry_rect.collidepoint(mouse))
        draw_button(surf, "Main Menu", menu_rect,  BLUE,  menu_rect.collidepoint(mouse))

        for event in pygame.event.get():
            if event.type == QUIT:
                return "quit"
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                if retry_rect.collidepoint(event.pos):
                    return "retry"
                if menu_rect.collidepoint(event.pos):
                    return "menu"

        pygame.display.update()
        clock.tick(60)