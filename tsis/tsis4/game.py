import pygame
import sys
import os
import random
import time
from pygame.locals import *
from config import get_snake_color, get_snake_dark_color

#КОНСТАНТЫ

CELL       = 20
COLS       = 30
ROWS       = 28
HUD_HEIGHT = 40

SCREEN_W = COLS * CELL
SCREEN_H = ROWS * CELL + HUD_HEIGHT

BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
GREEN      = (0,   200, 0)
DARK_GREEN = (0,   140, 0)
RED        = (220, 0,   0)
GRAY       = (50,  50,  50)
LIGHT_GRAY = (120, 120, 120)
DARK_GRAY  = (80,  80,  80)
GOLD       = (255, 215, 0)
SILVER     = (192, 192, 192)
ORANGE     = (255, 140, 0)
DARK_RED   = (139, 0,   0)
PURPLE     = (180, 0,   255)
CYAN       = (0,   220, 220)
BLUE       = (30,  100, 255)

UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)

FOODS_PER_LEVEL = 5
BASE_FPS        = 8
FPS_INCREMENT   = 2

POWERUP_FIELD_LIFETIME  = 8.0   # сек: пропадает с поля если не собран
POWERUP_EFFECT_DURATION = 5.0   # сек: длительность эффекта speed/slow
OBSTACLE_LEVEL_START    = 3     # с какого уровня появляются препятствия
OBSTACLES_PER_LEVEL     = 5     # сколько блоков добавляется за уровень

#ТИПЫ ЕДЫ

FOOD_TYPES = [
    {"name": "normal",  "color": RED,      "points": 5,  "lifetime": 8.0, "weight": 55},
    {"name": "silver",  "color": SILVER,   "points": 15, "lifetime": 5.0, "weight": 25},
    {"name": "gold",    "color": GOLD,     "points": 30, "lifetime": 3.0, "weight": 10},
    {"name": "poison",  "color": DARK_RED, "points": 0,  "lifetime": 6.0, "weight": 10},
]

POWERUP_TYPES = [
    {"name": "speed_boost", "color": ORANGE, "label": "FAST"},
    {"name": "slow_motion", "color": CYAN,   "label": "SLOW"},
    {"name": "shield",      "color": BLUE,   "label": "SHIELD"},
]

#ВСПОМОГАТЕЛЬНЫЕ

def pick_food_type():
    weights = [ft["weight"] for ft in FOOD_TYPES]
    total   = sum(weights)
    r       = random.uniform(0, total)
    cumul   = 0
    for ft in FOOD_TYPES:
        cumul += ft["weight"]
        if r <= cumul:
            return ft
    return FOOD_TYPES[0]

def border_walls():
    walls = set()
    for c in range(COLS):
        walls.add((c, 0))
        walls.add((c, ROWS - 1))
    for r in range(1, ROWS - 1):
        walls.add((0, r))
        walls.add((COLS - 1, r))
    return walls

def load_level_file(level_number):
    filename = f"level{level_number}.txt"
    walls = set()
    if not os.path.exists(filename):
        return walls
    with open(filename, "r") as f:
        lines = f.readlines()
    for row_idx, line in enumerate(lines):
        if row_idx >= ROWS:
            break
        for col_idx, ch in enumerate(line.rstrip("\n")):
            if col_idx >= COLS:
                break
            if ch == "#":
                walls.add((col_idx, row_idx))
    return walls

def level_file_exists(n):
    return os.path.exists(f"level{n}.txt")

def all_walls_for_level(n):
    return border_walls() | load_level_file(n)

def free_cells(walls, obstacles=None):
    blocked = set(walls)
    if obstacles:
        blocked |= set(obstacles)
    cells = set()
    for r in range(1, ROWS - 1):
        for c in range(1, COLS - 1):
            if (c, r) not in blocked:
                cells.add((c, r))
    return cells

def safe_start(walls):
    for dc in range(COLS // 2):
        col = COLS // 2 + dc
        row = ROWS // 2
        candidates = [(col - i, row) for i in range(3)]
        if all(c not in walls for c in candidates):
            return candidates
    return [(3, 1), (2, 1), (1, 1)]

#ГЕНЕРАЦИЯ ПРЕПЯТСТВИЙ

def generate_obstacles(level, walls, snake):
    """Случайные блоки-препятствия, не перекрывающие змейку."""
    if level < OBSTACLE_LEVEL_START:
        return set()

    count   = OBSTACLES_PER_LEVEL * (level - OBSTACLE_LEVEL_START + 1)
    blocked = set(walls) | set(snake)
    # буферная зона вокруг змейки (3 клетки)
    buffer  = set()
    for (c, r) in snake:
        for dc in range(-3, 4):
            for dr in range(-3, 4):
                buffer.add((c + dc, r + dr))

    candidates = [
        (c, r)
        for r in range(1, ROWS - 1)
        for c in range(1, COLS - 1)
        if (c, r) not in blocked and (c, r) not in buffer
    ]
    random.shuffle(candidates)
    return set(candidates[:count])

#СПАВН ЕДЫ И ПАУЭРАПОВ

def spawn_food(snake_cells, walls, obstacles=None):
    blocked = set(walls) | set(snake_cells)
    if obstacles:
        blocked |= obstacles
    valid = free_cells(walls, obstacles) - set(snake_cells)
    if not valid:
        return None
    pos   = random.choice(list(valid))
    ftype = pick_food_type()
    return {"pos": pos, "ftype": ftype, "spawned": time.time()}

def food_time_left(food):
    if food is None:
        return 0.0
    return max(0.0, food["ftype"]["lifetime"] - (time.time() - food["spawned"]))

def spawn_powerup(snake_cells, walls, obstacles=None, food=None):
    blocked = set(walls) | set(snake_cells)
    if obstacles:
        blocked |= obstacles
    if food:
        blocked.add(food["pos"])
    valid = [
        (c, r)
        for r in range(1, ROWS - 1)
        for c in range(1, COLS - 1)
        if (c, r) not in blocked
    ]
    if not valid:
        return None
    pos   = random.choice(valid)
    ptype = random.choice(POWERUP_TYPES)
    return {"pos": pos, "ptype": ptype, "spawned": time.time()}

def powerup_time_left(pu):
    if pu is None:
        return 0.0
    return max(0.0, POWERUP_FIELD_LIFETIME - (time.time() - pu["spawned"]))

#СОСТОЯНИЕ ИГРЫ

def new_game_state(level=1, score=0, settings=None):
    if settings is None:
        settings = {}
    walls     = all_walls_for_level(level)
    snake     = safe_start(walls)
    obstacles = generate_obstacles(level, walls, snake)
    fps       = BASE_FPS + (level - 1) * FPS_INCREMENT

    return {
        "snake":     snake,
        "direction": RIGHT,
        "next_dir":  RIGHT,
        "walls":     walls,
        "obstacles": obstacles,
        "food":      spawn_food(snake, walls, obstacles),
        "powerup":   None,         # текущий пауэрап на поле
        "powerup_next_spawn": time.time() + random.uniform(5, 12),
        "score":     score,
        "level":     level,
        "foods_eaten_this_level": 0,
        "fps":       fps,
        "base_fps":  fps,

        # активные эффекты
        "effect":         None,     # "speed_boost" | "slow_motion" | "shield" | None
        "effect_end":     0.0,
        "shield_active":  False,    # щит ждёт первого столкновения

        # настройки
        "settings": settings,
    }

#ПРИМЕНЕНИЕ ЭФФЕКТА

def apply_powerup_effect(state, ptype_name):
    if ptype_name == "speed_boost":
        state["effect"]     = "speed_boost"
        state["effect_end"] = time.time() + POWERUP_EFFECT_DURATION
        state["fps"]        = state["base_fps"] + 4
    elif ptype_name == "slow_motion":
        state["effect"]     = "slow_motion"
        state["effect_end"] = time.time() + POWERUP_EFFECT_DURATION
        state["fps"]        = max(2, state["base_fps"] - 3)
    elif ptype_name == "shield":
        state["effect"]       = "shield"
        state["shield_active"] = True
        # щит не имеет таймера — до первого столкновения

def tick_effects(state):
    """Обновляем эффекты по таймеру."""
    if state["effect"] in ("speed_boost", "slow_motion"):
        if time.time() >= state["effect_end"]:
            state["effect"] = None
            state["fps"]    = state["base_fps"]

#ИГРОВОЙ ШАГ

def game_step(state):
    """
    Выполняет один игровой тик.
    Возвращает:
      "playing"    — всё нормально
      "game_over"  — змейка умерла
      "level_done" — уровень пройден
      "win"        — все уровни пройдены (нет файла следующего уровня)
    """
    tick_effects(state)

    # пауэрап: исчез с поля по таймеру
    if state["powerup"] is not None and powerup_time_left(state["powerup"]) <= 0:
        state["powerup"] = None

    # пауэрап: спавним новый если нет на поле
    if state["powerup"] is None and time.time() >= state["powerup_next_spawn"]:
        state["powerup"] = spawn_powerup(
            state["snake"], state["walls"],
            state["obstacles"], state["food"]
        )
        state["powerup_next_spawn"] = time.time() + random.uniform(10, 20)

    # еда: истёк таймер
    if state["food"] is not None and food_time_left(state["food"]) <= 0:
        state["food"] = spawn_food(state["snake"], state["walls"], state["obstacles"])

    # движение
    state["direction"] = state["next_dir"]
    dx, dy = state["direction"]
    hc, hr = state["snake"][0]
    new_head = (hc + dx, hr + dy)

    # столкновение со стеной
    wall_hit = new_head in state["walls"]
    # столкновение с препятствием
    obs_hit  = new_head in state["obstacles"]
    # столкновение с собой
    self_hit = new_head in state["snake"]

    if (wall_hit or obs_hit or self_hit):
        if state["shield_active"]:
            # щит поглощает одно столкновение
            state["shield_active"] = False
            state["effect"]        = None
            # остаёмся на месте (не двигаемся в стену)
            return "playing"
        return "game_over"

    state["snake"].insert(0, new_head)

    # подбор пауэрапа
    if state["powerup"] is not None and new_head == state["powerup"]["pos"]:
        apply_powerup_effect(state, state["powerup"]["ptype"]["name"])
        state["powerup"]           = None
        state["powerup_next_spawn"] = time.time() + random.uniform(8, 15)
        # хвост не убираем (змейка растёт при подборе пауэрапа)
        return "playing"

    # еда
    food = state["food"]
    if food is not None and new_head == food["pos"]:
        fname = food["ftype"]["name"]

        if fname == "poison":
            # укоротить на 2 сегмента
            for _ in range(2):
                if len(state["snake"]) > 1:
                    state["snake"].pop()
            if len(state["snake"]) <= 1:
                return "game_over"
            state["food"] = spawn_food(state["snake"], state["walls"], state["obstacles"])
        else:
            state["score"] += food["ftype"]["points"]
            state["foods_eaten_this_level"] += 1
            state["food"] = spawn_food(state["snake"], state["walls"], state["obstacles"])

            if state["foods_eaten_this_level"] >= FOODS_PER_LEVEL:
                next_level = state["level"] + 1
                if level_file_exists(next_level):
                    return "level_done"
                else:
                    return "win"
    else:
        state["snake"].pop()

    return "playing"

#ОТРИСОВКА

pygame.init()
screen     = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Snake")
clock      = pygame.time.Clock()
font_hud   = pygame.font.SysFont("Consolas", 20, bold=True)
font_large = pygame.font.SysFont("Consolas", 40, bold=True)
font_med   = pygame.font.SysFont("Consolas", 26, bold=True)
font_small = pygame.font.SysFont("Consolas", 18)
font_pts   = pygame.font.SysFont("Consolas", 11, bold=True)

def draw_cell(surface, col, row, color, shrink=2):
    rect = pygame.Rect(
        col * CELL + shrink,
        row * CELL + HUD_HEIGHT + shrink,
        CELL - shrink * 2,
        CELL - shrink * 2,
    )
    pygame.draw.rect(surface, color, rect, border_radius=3)

def draw_text(surface, text, font, color, x, y):
    surf = font.render(text, True, color)
    surface.blit(surf, (x, y))

def draw_grid(surface):
    for c in range(COLS):
        x = c * CELL
        pygame.draw.line(surface, (30, 30, 30), (x, HUD_HEIGHT), (x, SCREEN_H))
    for r in range(ROWS):
        y = r * CELL + HUD_HEIGHT
        pygame.draw.line(surface, (30, 30, 30), (0, y), (SCREEN_W, y))

def draw_walls(surface, walls):
    border = border_walls()
    for (c, r) in walls:
        color = LIGHT_GRAY if (c, r) in border else DARK_GRAY
        draw_cell(surface, c, r, color, shrink=1)

def draw_obstacles(surface, obstacles):
    for (c, r) in obstacles:
        draw_cell(surface, c, r, (160, 80, 0), shrink=1)
        # крестик сверху для отличия от стен
        cx = c * CELL + CELL // 2
        cy = r * CELL + HUD_HEIGHT + CELL // 2
        pygame.draw.line(surface, (100, 50, 0), (cx - 4, cy - 4), (cx + 4, cy + 4), 2)
        pygame.draw.line(surface, (100, 50, 0), (cx + 4, cy - 4), (cx - 4, cy + 4), 2)

def draw_snake(surface, snake, settings):
    head_color = get_snake_color(settings)
    body_color = get_snake_dark_color(settings)
    for i, (c, r) in enumerate(snake):
        draw_cell(surface, c, r, head_color if i == 0 else body_color)

def draw_food(surface, food):
    if food is None:
        return
    col, row = food["pos"]
    cx = col * CELL + CELL // 2
    cy = row * CELL + HUD_HEIGHT + CELL // 2

    radius = CELL // 2 - 2
    color  = food["ftype"]["color"]
    pygame.draw.circle(surface, color, (cx, cy), radius)
    r, g, b = color
    pygame.draw.circle(surface, (max(0, r-60), max(0, g-60), max(0, b-60)), (cx, cy), radius, 2)

    # полоска таймера
    lifetime  = food["ftype"]["lifetime"]
    time_left = food_time_left(food)
    ratio     = time_left / lifetime
    bar_w = CELL - 4
    bar_h = 3
    bar_x = col * CELL + 2
    bar_y = (row + 1) * CELL + HUD_HEIGHT - bar_h - 1
    pygame.draw.rect(surface, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
    filled_w = int(bar_w * ratio)
    if filled_w > 0:
        if ratio > 0.5:
            t  = (ratio - 0.5) / 0.5
            bc = (int(255 * (1 - t)), 220, 0)
        else:
            t  = ratio / 0.5
            bc = (255, int(200 * t), 0)
        pygame.draw.rect(surface, bc, (bar_x, bar_y, filled_w, bar_h))

    pts_text = f"+{food['ftype']['points']}" if food["ftype"]["name"] != "poison" else "X"
    pts_surf = font_pts.render(pts_text, True, color)
    surface.blit(pts_surf, (col * CELL + CELL, row * CELL + HUD_HEIGHT))

def draw_powerup(surface, powerup):
    if powerup is None:
        return
    col, row = powerup["pos"]
    cx = col * CELL + CELL // 2
    cy = row * CELL + HUD_HEIGHT + CELL // 2
    color = powerup["ptype"]["color"]

    # мигающий квадрат
    t = time.time()
    alpha = int(180 + 75 * abs((t % 1.0) - 0.5) * 2)
    s = pygame.Surface((CELL - 4, CELL - 4), pygame.SRCALPHA)
    s.fill((*color, min(255, alpha)))
    surface.blit(s, (col * CELL + 2, row * CELL + HUD_HEIGHT + 2))

    # таймер полоска
    ratio = powerup_time_left(powerup) / POWERUP_FIELD_LIFETIME
    bar_w = CELL - 4
    bar_h = 2
    bar_x = col * CELL + 2
    bar_y = (row + 1) * CELL + HUD_HEIGHT - bar_h - 1
    pygame.draw.rect(surface, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
    pygame.draw.rect(surface, color, (bar_x, bar_y, int(bar_w * ratio), bar_h))

def draw_hud(surface, state, personal_best):
    surface.fill(GRAY, (0, 0, SCREEN_W, HUD_HEIGHT))

    draw_text(surface, f"Score: {state['score']}", font_hud, WHITE, 10, 10)

    prog = f"{state['foods_eaten_this_level']}/{FOODS_PER_LEVEL}"
    ps   = font_hud.render(prog, True, ORANGE)
    surface.blit(ps, (SCREEN_W // 2 - ps.get_width() // 2, 10))

    ls = font_hud.render(f"Lv {state['level']}", True, GOLD)
    surface.blit(ls, (SCREEN_W - ls.get_width() - 10, 10))

    # личный рекорд
    pb_surf = font_small.render(f"PB:{personal_best}", True, SILVER)
    surface.blit(pb_surf, (SCREEN_W - pb_surf.get_width() - 10, HUD_HEIGHT - 18))

    # активный эффект
    if state["effect"]:
        eff_colors = {"speed_boost": ORANGE, "slow_motion": CYAN, "shield": BLUE}
        eff_labels = {"speed_boost": "FAST", "slow_motion": "SLOW", "shield": "SHIELD"}
        color = eff_colors.get(state["effect"], WHITE)
        label = eff_labels.get(state["effect"], "")
        if state["effect"] in ("speed_boost", "slow_motion"):
            left  = max(0.0, state["effect_end"] - time.time())
            label = f"{label} {left:.1f}s"
        eff_surf = font_small.render(label, True, color)
        surface.blit(eff_surf, (SCREEN_W // 2 - eff_surf.get_width() // 2 + 60, 10))

def draw_overlay(surface, lines, colors=None, font=None):
    if font is None:
        font = font_large
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 170))
    surface.blit(ov, (0, 0))
    total_h = len(lines) * 55
    start_y = (SCREEN_H - total_h) // 2
    for i, line in enumerate(lines):
        color = (colors[i] if colors and i < len(colors) else WHITE)
        surf  = font.render(line, True, color)
        surface.blit(surf, (SCREEN_W // 2 - surf.get_width() // 2, start_y + i * 55))