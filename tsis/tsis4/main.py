import pygame
import sys
import time
import random
from pygame.locals import *

from config  import load_settings, save_settings
from db      import init_db, save_session, get_top10, get_personal_best
from game    import (
    SCREEN_W, SCREEN_H, CELL, COLS, ROWS, HUD_HEIGHT,
    BLACK, WHITE, GREEN, DARK_GREEN, RED, GRAY, LIGHT_GRAY,
    DARK_GRAY, GOLD, SILVER, ORANGE, PURPLE, CYAN, BLUE, DARK_RED,
    screen, clock,
    font_hud, font_large, font_med, font_small, font_pts,
    new_game_state, game_step,
    draw_walls, draw_obstacles, draw_snake, draw_food,
    draw_powerup, draw_hud, draw_overlay, draw_grid,
    level_file_exists, FOODS_PER_LEVEL,
)

pygame.init()
pygame.display.set_caption("Snake")

#БД

try:
    init_db()
    DB_OK = True
except Exception as e:
    print(f"[DB] Не удалось подключиться: {e}")
    DB_OK = False

# ── ВСПОМОГАТЕЛЬНЫЕ UI ───────────────────────────────────────────────────────

def draw_text_center(surface, text, font, color, y):
    surf = font.render(text, True, color)
    surface.blit(surf, (SCREEN_W // 2 - surf.get_width() // 2, y))

def draw_button(surface, text, font, rect, active=False):
    color  = (70, 70, 70) if not active else (100, 160, 100)
    border = GOLD if active else LIGHT_GRAY
    pygame.draw.rect(surface, color,  rect, border_radius=8)
    pygame.draw.rect(surface, border, rect, 2, border_radius=8)
    surf = font.render(text, True, WHITE)
    surface.blit(surf, (
        rect.centerx - surf.get_width()  // 2,
        rect.centery - surf.get_height() // 2,
    ))

def make_buttons(labels, start_y, width=240, height=48, gap=16):
    buttons = []
    x = SCREEN_W // 2 - width // 2
    for label in labels:
        buttons.append((label, pygame.Rect(x, start_y, width, height)))
        start_y += height + gap
    return buttons

def get_hovered(buttons, mouse_pos):
    for label, rect in buttons:
        if rect.collidepoint(mouse_pos):
            return label
    return None

# ЭКРАН: ГЛАВНОЕ МЕНЮ

def screen_main_menu(settings):
    username    = ""
    typing      = True          # режим ввода имени
    input_active = True

    buttons = make_buttons(["Play", "Leaderboard", "Settings", "Quit"], start_y=360)
    error   = ""

    while True:
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()

            if event.type == KEYDOWN:
                if input_active:
                    if event.key == K_RETURN:
                        if username.strip():
                            input_active = False
                        else:
                            error = "Enter name!"
                    elif event.key == K_BACKSPACE:
                        username = username[:-1]
                        error    = ""
                    else:
                        if len(username) < 20 and event.unicode.isprintable():
                            username += event.unicode
                            error     = ""

            if event.type == MOUSEBUTTONDOWN and not input_active:
                clicked = get_hovered(buttons, mouse)
                if clicked == "Play":
                    return ("play", username.strip())
                elif clicked == "Leaderboard":
                    return ("leaderboard",)
                elif clicked == "Settings":
                    return ("settings",)
                elif clicked == "Quit":
                    pygame.quit(); sys.exit()

        # ── рисуем ────────────────────────────────────────────────────────
        screen.fill(BLACK)

        # заголовок
        draw_text_center(screen, "SNAKE", font_large, GREEN, 60)
        draw_text_center(screen, "Powered by Python & Pygame", font_small, LIGHT_GRAY, 120)

        # поле ввода имени
        draw_text_center(screen, "Enter player name:", font_med, WHITE, 200)
        inp_rect = pygame.Rect(SCREEN_W // 2 - 150, 238, 300, 44)
        border_c = GOLD if input_active else LIGHT_GRAY
        pygame.draw.rect(screen, DARK_GRAY, inp_rect, border_radius=6)
        pygame.draw.rect(screen, border_c,  inp_rect, 2, border_radius=6)
        disp = username + ("|" if input_active and int(time.time() * 2) % 2 == 0 else "")
        us = font_med.render(disp, True, WHITE)
        screen.blit(us, (inp_rect.x + 10, inp_rect.y + 8))

        if error:
            draw_text_center(screen, error, font_small, RED, 290)
        elif not input_active:
            draw_text_center(screen, f"Hello, {username}!", font_small, GREEN, 290)

        # кнопки
        hovered = get_hovered(buttons, mouse) if not input_active else None
        for label, rect in buttons:
            enabled = not input_active
            draw_button(screen, label, font_med, rect, active=(hovered == label and enabled))
            if not enabled:
                # затемняем если имя ещё не введено
                s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                s.fill((0, 0, 0, 120))
                screen.blit(s, rect.topleft)

        pygame.display.flip()
        clock.tick(30)

# ── ЭКРАН: GAMEPLAY ───────────────────────────────────────────────────────────

def screen_gameplay(username, settings):
    personal_best = 0
    if DB_OK:
        try:
            personal_best = get_personal_best(username)
        except Exception:
            pass

    phase          = "playing"
    clear_deadline = 0.0
    pending_level  = 1
    pending_score  = 0

    state = new_game_state(level=1, score=0, settings=settings)

    while True:
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()

            if event.type == KEYDOWN:

                if phase == "playing":
                    from game import UP, DOWN, LEFT, RIGHT
                    if   event.key in (K_UP,    K_w) and state["direction"] != DOWN:
                        state["next_dir"] = UP
                    elif event.key in (K_DOWN,  K_s) and state["direction"] != UP:
                        state["next_dir"] = DOWN
                    elif event.key in (K_LEFT,  K_a) and state["direction"] != RIGHT:
                        state["next_dir"] = LEFT
                    elif event.key in (K_RIGHT, K_d) and state["direction"] != LEFT:
                        state["next_dir"] = RIGHT
                    elif event.key == K_ESCAPE:
                        return ("menu",)

                elif phase == "level_clear":
                    if event.key in (K_RETURN, K_SPACE):
                        state = new_game_state(level=pending_level,
                                               score=pending_score,
                                               settings=settings)
                        phase = "playing"

        # автопереход с экрана level_clear
        if phase == "level_clear" and time.time() >= clear_deadline:
            state = new_game_state(level=pending_level,
                                   score=pending_score,
                                   settings=settings)
            phase = "playing"

        # игровой тик
        if phase == "playing":
            result = game_step(state)

            if result == "game_over":
                phase = "game_over_anim"
                if DB_OK:
                    try:
                        save_session(username, state["score"], state["level"])
                        personal_best = max(personal_best, state["score"])
                    except Exception as e:
                        print(f"[DB] save_session error: {e}")

            elif result == "level_done":
                pending_level  = state["level"] + 1
                pending_score  = state["score"]
                clear_deadline = time.time() + 2.5
                phase          = "level_clear"

            elif result == "win":
                phase = "win"
                if DB_OK:
                    try:
                        save_session(username, state["score"], state["level"])
                        personal_best = max(personal_best, state["score"])
                    except Exception as e:
                        print(f"[DB] save_session error: {e}")

        # ── рисуем ────────────────────────────────────────────────────────
        screen.fill(BLACK)

        # сетка
        if settings.get("grid_overlay", False):
            draw_grid(screen)

        draw_walls(screen, state["walls"])
        draw_obstacles(screen, state["obstacles"])
        draw_snake(screen, state["snake"], settings)

        if phase in ("playing", "level_clear"):
            draw_food(screen, state["food"])
            draw_powerup(screen, state["powerup"])

        draw_hud(screen, state, personal_best)

        if phase == "level_clear":
            left = max(0.0, clear_deadline - time.time())
            draw_overlay(screen,
                ["LEVEL CLEAR!",
                 f"Level {state['level']} done",
                 f"Score: {state['score']}",
                 f"→ Level {pending_level}",
                 f"ENTER / {left:.1f}s"],
                [GREEN, LIGHT_GRAY, WHITE, GOLD, LIGHT_GRAY])

        elif phase == "game_over_anim":
            return ("game_over", state["score"], state["level"])

        elif phase == "win":
            draw_overlay(screen,
                ["YOU WON!", f"Score: {state['score']}", "ENTER — menu"],
                [GOLD, WHITE, LIGHT_GRAY])
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit(); sys.exit()
                if event.type == KEYDOWN and event.key == K_RETURN:
                    return ("menu",)

        pygame.display.flip()
        clock.tick(state["fps"])

#ЭКРАН: GAME OVER 

def screen_game_over(username, score, level, settings):
    personal_best = 0
    if DB_OK:
        try:
            personal_best = get_personal_best(username)
        except Exception:
            pass

    buttons = make_buttons(["Retry", "Main Menu"], start_y=440)

    while True:
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_RETURN:
                    return "retry"
                if event.key == K_ESCAPE:
                    return "menu"
            if event.type == MOUSEBUTTONDOWN:
                clicked = get_hovered(buttons, mouse)
                if clicked == "Retry":
                    return "retry"
                elif clicked == "Main Menu":
                    return "menu"

        screen.fill(BLACK)
        draw_text_center(screen, "GAME OVER",          font_large, RED,        120)
        draw_text_center(screen, f"Player: {username}", font_med,   LIGHT_GRAY, 200)
        draw_text_center(screen, f"Score:  {score}",   font_med,   WHITE,      250)
        draw_text_center(screen, f"Level: {level}",  font_med,   ORANGE,     295)
        draw_text_center(screen, f"Record: {personal_best}", font_med, GOLD,   340)

        hovered = get_hovered(buttons, mouse)
        for label, rect in buttons:
            draw_button(screen, label, font_med, rect, active=(hovered == label))

        pygame.display.flip()
        clock.tick(30)

#ЭКРАН: ЛИДЕРБОРД

def screen_leaderboard():
    rows = []
    if DB_OK:
        try:
            rows = get_top10()
        except Exception as e:
            print(f"[DB] get_top10 error: {e}")

    back_rect = pygame.Rect(SCREEN_W // 2 - 100, SCREEN_H - 60, 200, 44)

    while True:
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()
            if event.type == KEYDOWN and event.key in (K_ESCAPE, K_RETURN):
                return
            if event.type == MOUSEBUTTONDOWN:
                if back_rect.collidepoint(mouse):
                    return

        screen.fill(BLACK)
        draw_text_center(screen, "LEADERBOARD - TOP 10", font_large, GOLD, 20)

        # заголовок таблицы
        headers = ["#", "Player", "Score", "Lvl", "Date"]
        col_x   = [30, 80, 260, 370, 440]
        y = 90
        for i, h in enumerate(headers):
            surf = font_small.render(h, True, ORANGE)
            screen.blit(surf, (col_x[i], y))

        pygame.draw.line(screen, LIGHT_GRAY, (20, y + 24), (SCREEN_W - 20, y + 24), 1)
        y += 34

        rank_colors = {1: GOLD, 2: SILVER, 3: ORANGE}
        for row in rows:
            rc = rank_colors.get(row["rank"], WHITE)
            cells = [
                str(row["rank"]),
                row["username"][:14],
                str(row["score"]),
                str(row["level"]),
                row["date"],
            ]
            for i, cell in enumerate(cells):
                surf = font_small.render(cell, True, rc)
                screen.blit(surf, (col_x[i], y))
            y += 30

        if not rows:
            draw_text_center(screen, "No data", font_med, LIGHT_GRAY, 300)

        draw_button(screen, "<- Back", font_med, back_rect,
                    active=back_rect.collidepoint(mouse))

        pygame.display.flip()
        clock.tick(30)

#ЭКРАН: НАСТРОЙКИ

COLOR_OPTIONS = [
    ("Green",   (0,   200, 0)),
    ("Blue",     (30,  100, 255)),
    ("Orange", (255, 140, 0)),
    ("Purple",(180, 0,   255)),
    ("White",     (230, 230, 230)),
    ("Light Blue",   (0,   220, 220)),
]

def screen_settings(settings):
    local = dict(settings)
    back_rect = pygame.Rect(SCREEN_W // 2 - 120, SCREEN_H - 70, 240, 48)

    color_rects = []
    cx_start = 60
    for i, (name, _) in enumerate(COLOR_OPTIONS):
        r = pygame.Rect(cx_start + i * 80, 340, 60, 32)
        color_rects.append(r)

    while True:
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                save_settings(local)
                return local

            if event.type == MOUSEBUTTONDOWN:
                # сетка
                grid_rect = pygame.Rect(SCREEN_W // 2 - 120, 180, 240, 44)
                if grid_rect.collidepoint(mouse):
                    local["grid_overlay"] = not local["grid_overlay"]

                # звук
                sound_rect = pygame.Rect(SCREEN_W // 2 - 120, 250, 240, 44)
                if sound_rect.collidepoint(mouse):
                    local["sound"] = not local["sound"]

                # цвет
                for i, rect in enumerate(color_rects):
                    if rect.collidepoint(mouse):
                        local["snake_color"] = list(COLOR_OPTIONS[i][1])

                # сохранить
                if back_rect.collidepoint(mouse):
                    save_settings(local)
                    return local

        screen.fill(BLACK)
        draw_text_center(screen, "SETTINGS", font_large, WHITE, 40)

        # кнопка-переключатель сетки
        grid_rect  = pygame.Rect(SCREEN_W // 2 - 120, 180, 240, 44)
        grid_label = f"Grid: {'ON' if local['grid_overlay'] else 'OFF'}"
        draw_button(screen, grid_label, font_med, grid_rect,
                    active=local["grid_overlay"])

        # кнопка-переключатель звука
        sound_rect  = pygame.Rect(SCREEN_W // 2 - 120, 250, 240, 44)
        sound_label = f"Sound: {'ON' if local['sound'] else 'OFF'}"
        draw_button(screen, sound_label, font_med, sound_rect,
                    active=local["sound"])

        # выбор цвета
        draw_text_center(screen, "Snake colour:", font_med, LIGHT_GRAY, 305)
        current_color = tuple(local["snake_color"])
        for i, (name, color) in enumerate(COLOR_OPTIONS):
            r = color_rects[i]
            pygame.draw.rect(screen, color, r, border_radius=6)
            if tuple(color) == current_color:
                pygame.draw.rect(screen, WHITE, r, 3, border_radius=6)
            ts = font_pts.render(name, True, WHITE)
            screen.blit(ts, (r.x, r.y + 36))

        draw_button(screen, "Save and quit", font_med, back_rect,
                    active=back_rect.collidepoint(mouse))

        pygame.display.flip()
        clock.tick(30)

#ГЛАВНЫЙ ЦИКЛ ПРИЛОЖЕНИЯ

def main():
    settings = load_settings()
    username = ""

    current_screen = "menu"
    last_score     = 0
    last_level     = 1

    while True:
        if current_screen == "menu":
            result = screen_main_menu(settings)
            if result[0] == "play":
                username       = result[1]
                current_screen = "game"
            elif result[0] == "leaderboard":
                current_screen = "leaderboard"
            elif result[0] == "settings":
                current_screen = "settings"

        elif current_screen == "game":
            result = screen_gameplay(username, settings)
            if result[0] == "game_over":
                _, last_score, last_level = result
                current_screen = "game_over"
            elif result[0] == "menu":
                current_screen = "menu"

        elif current_screen == "game_over":
            result = screen_game_over(username, last_score, last_level, settings)
            if result == "retry":
                current_screen = "game"
            else:
                current_screen = "menu"

        elif current_screen == "leaderboard":
            screen_leaderboard()
            current_screen = "menu"

        elif current_screen == "settings":
            settings       = screen_settings(settings)
            current_screen = "menu"

if __name__ == "__main__":
    main()