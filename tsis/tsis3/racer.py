import pygame
import random
import os
from pygame.locals import *

# ==================== CONSTANTS ====================
SCREEN_WIDTH  = 400
SCREEN_HEIGHT = 600
FPS = 60

BASE_SPEED = 5
COINS_FOR_SPEED = 10

# Colors
BLACK     = (0,   0,   0)
WHITE     = (255, 255, 255)
RED       = (255,  50,  50)
BLUE      = (50,  100, 220)
GREEN     = (50,  200,  80)
YELLOW    = (255, 220,   0)
ORANGE    = (255, 140,   0)
GRAY      = (120, 120, 120)
DARK_GRAY = (60,  60,  60)
PURPLE    = (160,  50, 210)
CYAN      = (0,   200, 220)

# Difficulty → traffic density multiplier
DIFF_SETTINGS = {
    "easy":   {"traffic_interval": 3000, "obstacle_interval": 5000, "extra_enemy": 1},
    "normal": {"traffic_interval": 2000, "obstacle_interval": 3500, "extra_enemy": 2},
    "hard":   {"traffic_interval": 1200, "obstacle_interval": 2200, "extra_enemy": 3},
}

# ==================== FONTS ====================
_font_small = None
_font_hud   = None

def _get_fonts():
    global _font_small, _font_hud
    if _font_small is None:
        _font_small = pygame.font.SysFont("Verdana", 18)
        _font_hud   = pygame.font.SysFont("Verdana", 16, bold=True)
    return _font_small, _font_hud


# ==================== IMAGE LOADING ====================
_images = {}

def _load_images():
    """Load all game images once. Called at start of run_game()."""
    global _images
    if _images:
        return _images

    def load(path, size):
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, size)
        # fallback: colored rect if image missing
        s = pygame.Surface(size, pygame.SRCALPHA)
        s.fill((180, 180, 180, 200))
        return s

    _images["background"] = load("background.jpg", (SCREEN_WIDTH, SCREEN_HEIGHT))
    _images["player"]     = load("Player.jpg",     (50, 70))
    _images["enemy"]      = load("Enemy.jpg",       (50, 70))

    # Sound
    _images["sound_bg"]    = None
    _images["sound_crash"] = None
    try:
        pygame.mixer.init()
        if os.path.exists("background.wav"):
            _images["sound_bg"] = pygame.mixer.Sound("background.wav")
        if os.path.exists("crash.wav"):
            _images["sound_crash"] = pygame.mixer.Sound("crash.wav")
    except:
        pass

    return _images


# ==================== HELPERS ====================
def safe_x(player_rect):
    px = player_rect.centerx
    candidates = [x for x in range(50, SCREEN_WIDTH - 50, 60) if abs(x - px) > 70]
    return random.choice(candidates) if candidates else random.choice([60, 160, 260, 340])



# ==================== ROAD ====================
class Road:
    """Scrolling road using background.jpg."""
    def __init__(self):
        imgs = _load_images()
        self._bg  = imgs["background"]
        self.y1   = 0
        self.y2   = -SCREEN_HEIGHT
        # Lane stripe overlay colors
        self.lane_color  = (200, 200, 200)
        self.stripe_w    = 6
        self.stripe_h    = 40
        self.stripe_gap  = 30
        self.lanes_x     = [100, 200, 300]

    def update(self, speed):
        self.y1 = (self.y1 + speed) % SCREEN_HEIGHT
        self.y2 = self.y1 - SCREEN_HEIGHT

    def draw(self, surf):
        surf.blit(self._bg, (0, self.y1))
        surf.blit(self._bg, (0, self.y2))
        # Draw lane markings on top
        for y_off in [self.y1, self.y2]:
            for lx in self.lanes_x:
                y = y_off
                while y < y_off + SCREEN_HEIGHT:
                    pygame.draw.rect(surf, self.lane_color,
                                     (lx - self.stripe_w // 2, y, self.stripe_w, self.stripe_h))
                    y += self.stripe_h + self.stripe_gap


# ==================== PLAYER ====================
class Player(pygame.sprite.Sprite):
    def __init__(self, car_color="blue"):
        super().__init__()
        imgs = _load_images()
        self._base_image  = imgs["player"].copy()
        self.image        = self._base_image.copy()
        self.rect         = self.image.get_rect(center=(160, 520))
        self.has_shield   = False
        self.nitro_active = False
        self.nitro_timer  = 0
        self.speed_bonus  = 0

    def _draw_shield_effect(self):
        pygame.draw.rect(self.image, CYAN, (0, 0, self.image.get_width(), self.image.get_height()), 3)

    def update_shield_visual(self):
        self.image = self._base_image.copy()
        if self.has_shield:
            self._draw_shield_effect()

    def move(self, speed):
        pressed = pygame.key.get_pressed()
        if self.rect.left > 32 and pressed[K_LEFT]:
            self.rect.move_ip(-5, 0)
        if self.rect.right < SCREEN_WIDTH - 32 and pressed[K_RIGHT]:
            self.rect.move_ip(5, 0)

    def activate_nitro(self, duration=4):
        self.nitro_active = True
        self.nitro_timer  = duration
        self.speed_bonus  = 4

    def activate_shield(self):
        self.has_shield = True
        self.update_shield_visual()

    def use_shield(self):
        self.has_shield = False
        self.update_shield_visual()

    def tick(self, dt):
        if self.nitro_active:
            self.nitro_timer -= dt
            if self.nitro_timer <= 0:
                self.nitro_active = False
                self.speed_bonus  = 0


# ==================== ENEMY (traffic car) ====================
class Enemy(pygame.sprite.Sprite):
    def __init__(self, player_rect=None):
        super().__init__()
        imgs = _load_images()
        self.image = imgs["enemy"].copy()
        self.rect  = self.image.get_rect()
        x = safe_x(player_rect) if player_rect else random.randint(40, SCREEN_WIDTH - 40)
        self.rect.center = (x, -60)
        self.lane_speed = random.uniform(0.8, 1.3)

    def move(self, speed):
        self.rect.move_ip(0, speed * self.lane_speed)
        if self.rect.top > SCREEN_HEIGHT + 20:
            self.kill()


# ==================== COIN ====================
class Coin(pygame.sprite.Sprite):
    RADIUS = 12

    def __init__(self):
        super().__init__()
        self.weight = random.choices([1, 2, 5], weights=[60, 30, 10])[0]
        color = YELLOW if self.weight == 1 else (255, 150, 0) if self.weight == 2 else (255, 215, 0)
        size = self.RADIUS * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (self.RADIUS, self.RADIUS), self.RADIUS)
        font_small, _ = _get_fonts()
        label = font_small.render(str(self.weight), True, BLACK)
        self.image.blit(label, (4, 2))
        self.rect = self.image.get_rect()
        self._respawn()

    def _respawn(self):
        self.rect.center = (
            random.randint(40, SCREEN_WIDTH - 40),
            random.randint(-SCREEN_HEIGHT, -30)
        )

    def move(self, speed):
        self.rect.move_ip(0, max(2, speed // 2))
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# ==================== POWER-UPS ====================
POWERUP_TYPES = ["nitro", "shield", "repair"]
POWERUP_COLORS = {"nitro": ORANGE, "shield": CYAN, "repair": GREEN}
POWERUP_LABELS = {"nitro": "N", "shield": "S", "repair": "R"}
POWERUP_LIFETIME = 8  # seconds before disappears

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, ptype=None):
        super().__init__()
        self.ptype    = ptype or random.choice(POWERUP_TYPES)
        self.lifetime = POWERUP_LIFETIME
        color = POWERUP_COLORS[self.ptype]

        _, font_hud = _get_fonts()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.rect(self.image, color, (0, 0, 30, 30), border_radius=6)
        pygame.draw.rect(self.image, WHITE, (0, 0, 30, 30), 2, border_radius=6)
        lbl = font_hud.render(POWERUP_LABELS[self.ptype], True, WHITE)
        self.image.blit(lbl, (30 // 2 - lbl.get_width() // 2, 30 // 2 - lbl.get_height() // 2))

        self.rect = self.image.get_rect()
        self.rect.center = (random.randint(50, SCREEN_WIDTH - 50), -40)

    def move(self, speed):
        self.rect.move_ip(0, max(2, speed // 2))
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def tick(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()


# ==================== OBSTACLE ====================
class Obstacle(pygame.sprite.Sprite):
    TYPES = ["oil", "pothole", "barrier"]

    def __init__(self, player_rect=None):
        super().__init__()
        self.otype = random.choice(self.TYPES)
        self.image, self.slow = self._make(self.otype)
        self.rect = self.image.get_rect()
        x = safe_x(player_rect) if player_rect else random.randint(50, SCREEN_WIDTH - 50)
        self.rect.center = (x, -40)

    def _make(self, otype):
        _, font_hud = _get_fonts()
        if otype == "oil":
            s = pygame.Surface((50, 24), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (30, 30, 120, 180), (0, 0, 50, 24))
            lbl = font_hud.render("OIL", True, WHITE)
            s.blit(lbl, (8, 4))
            return s, True
        elif otype == "pothole":
            s = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(s, (40, 40, 40), (18, 18), 18)
            pygame.draw.circle(s, (20, 20, 20), (18, 18), 12)
            return s, False
        else:  # barrier
            s = pygame.Surface((60, 20), pygame.SRCALPHA)
            pygame.draw.rect(s, ORANGE, (0, 0, 60, 20), border_radius=4)
            pygame.draw.rect(s, BLACK,  (0, 0, 60, 20), 2, border_radius=4)
            lbl = font_hud.render("STOP", True, BLACK)
            s.blit(lbl, (8, 2))
            return s, False

    def move(self, speed):
        self.rect.move_ip(0, max(3, speed // 2 + 1))
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# ==================== NITRO STRIP (road event) ====================
class NitroStrip(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((SCREEN_WIDTH - 64, 16), pygame.SRCALPHA)
        for x in range(0, SCREEN_WIDTH - 64, 20):
            pygame.draw.rect(self.image, YELLOW, (x, 0, 14, 16))
        self.rect = self.image.get_rect()
        self.rect.topleft = (32, -20)

    def move(self, speed):
        self.rect.move_ip(0, speed + 1)
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# ==================== HUD ====================
def draw_hud(surf, score, coins, distance, finish_dist,
             active_powerup, powerup_timer, speed):
    _, font_hud = _get_fonts()
    # Top bar background
    bar = pygame.Surface((SCREEN_WIDTH, 50), pygame.SRCALPHA)
    bar.fill((0, 0, 0, 160))
    surf.blit(bar, (0, 0))

    sc = font_hud.render(f"Score: {score}", True, WHITE)
    surf.blit(sc, (8, 6))

    co = font_hud.render(f"Coins: {coins}", True, YELLOW)
    surf.blit(co, (8, 28))

    dist_text = f"Dist: {int(distance)}m / {finish_dist}m"
    dt_surf = font_hud.render(dist_text, True, WHITE)
    surf.blit(dt_surf, (SCREEN_WIDTH // 2 - dt_surf.get_width() // 2, 6))

    sp = font_hud.render(f"Speed: {int(speed)}", True, CYAN)
    surf.blit(sp, (SCREEN_WIDTH - sp.get_width() - 8, 28))

    # Active power-up
    if active_powerup:
        color = POWERUP_COLORS.get(active_powerup, WHITE)
        pu_bg = pygame.Surface((180, 26), pygame.SRCALPHA)
        pu_bg.fill((0, 0, 0, 140))
        surf.blit(pu_bg, (SCREEN_WIDTH // 2 - 90, SCREEN_HEIGHT - 36))
        pu_text = f"{active_powerup.upper()} {powerup_timer:.1f}s" if powerup_timer > 0 else active_powerup.upper()
        pu_surf = font_hud.render(pu_text, True, color)
        surf.blit(pu_surf, (SCREEN_WIDTH // 2 - pu_surf.get_width() // 2, SCREEN_HEIGHT - 32))


# ==================== MAIN GAME SESSION ====================
def run_game(surf, settings, username):
    """
    Run one game session.
    Returns dict: {score, distance, coins, reason}
    """
    clock = pygame.time.Clock()
    imgs  = _load_images()
    diff  = settings.get("difficulty", "normal")
    diff_cfg = DIFF_SETTINGS.get(diff, DIFF_SETTINGS["normal"])

    # --- Background music ---
    if settings.get("sound", True) and imgs.get("sound_bg"):
        imgs["sound_bg"].play(loops=-1)

    # --- State ---
    score    = 0
    coins    = 0
    distance = 0.0
    FINISH_DISTANCE = 3000
    speed    = BASE_SPEED
    running  = True
    crashed  = False

    active_powerup = None
    powerup_timer  = 0.0

    # --- Road ---
    road = Road()

    # --- Sprites ---
    player = Player(car_color=settings.get("car_color", "blue"))

    enemies_group   = pygame.sprite.Group()
    coins_group     = pygame.sprite.Group()
    powerups_group  = pygame.sprite.Group()
    obstacles_group = pygame.sprite.Group()
    events_group    = pygame.sprite.Group()
    all_sprites     = pygame.sprite.Group()

    all_sprites.add(player)

    # Initial enemies
    for _ in range(diff_cfg["extra_enemy"]):
        e = Enemy(player.rect)
        enemies_group.add(e)
        all_sprites.add(e)

    # Initial coins
    for _ in range(3):
        c = Coin()
        coins_group.add(c)
        all_sprites.add(c)

    # --- Timers ---
    SPAWN_COIN     = USEREVENT + 1
    SPAWN_ENEMY    = USEREVENT + 2
    SPAWN_POWERUP  = USEREVENT + 3
    SPAWN_OBSTACLE = USEREVENT + 4
    SPAWN_EVENT    = USEREVENT + 5

    pygame.time.set_timer(SPAWN_COIN,     4000)
    pygame.time.set_timer(SPAWN_ENEMY,    diff_cfg["traffic_interval"])
    pygame.time.set_timer(SPAWN_POWERUP,  7000)
    pygame.time.set_timer(SPAWN_OBSTACLE, diff_cfg["obstacle_interval"])
    pygame.time.set_timer(SPAWN_EVENT,    10000)

    slowdown_timer = 0.0  # seconds of slow-down from oil

    while running:
        dt = clock.tick(FPS) / 1000.0  # seconds

        # -------- EVENTS --------
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                import sys; sys.exit()

            if event.type == SPAWN_COIN:
                if random.random() < 0.7:
                    nc = Coin()
                    coins_group.add(nc)
                    all_sprites.add(nc)

            if event.type == SPAWN_ENEMY:
                # Scale count with distance
                count = 1 + int(distance / 800)
                count = min(count, diff_cfg["extra_enemy"] + 2)
                for _ in range(count):
                    ne = Enemy(player.rect)
                    enemies_group.add(ne)
                    all_sprites.add(ne)
                score += 1  # survived another wave

            if event.type == SPAWN_POWERUP:
                if len(powerups_group) < 2:
                    pu = PowerUp()
                    powerups_group.add(pu)
                    all_sprites.add(pu)

            if event.type == SPAWN_OBSTACLE:
                if random.random() < 0.8:
                    ob = Obstacle(player.rect)
                    obstacles_group.add(ob)
                    all_sprites.add(ob)

            if event.type == SPAWN_EVENT:
                # Road event: nitro strip
                if random.random() < 0.5:
                    ns = NitroStrip()
                    events_group.add(ns)
                    all_sprites.add(ns)

        # -------- SPEED CALC --------
        base = BASE_SPEED + (coins // COINS_FOR_SPEED)
        effective_speed = base + player.speed_bonus
        if slowdown_timer > 0:
            slowdown_timer -= dt
            effective_speed = max(2, effective_speed - 3)

        # -------- UPDATE ROAD --------
        road.update(effective_speed)
        distance += effective_speed * dt * 3

        # -------- MOVE SPRITES --------
        player.move(effective_speed)
        player.tick(dt)

        for e in enemies_group:
            e.move(effective_speed)
        for c in coins_group:
            c.move(effective_speed)
        for ob in obstacles_group:
            ob.move(effective_speed)
        for ev in events_group:
            ev.move(effective_speed)
        for pu in list(powerups_group):
            pu.move(effective_speed)
            pu.tick(dt)

        # -------- POWERUP TIMER --------
        if active_powerup and active_powerup == "nitro":
            powerup_timer -= dt
            if powerup_timer <= 0:
                active_powerup = None
                powerup_timer  = 0

        # -------- COIN COLLECTION --------
        collected_coins = pygame.sprite.spritecollide(player, coins_group, True)
        for coin in collected_coins:
            coins += coin.weight
            score += coin.weight * 2
            nc = Coin()
            coins_group.add(nc)
            all_sprites.add(nc)

        # -------- POWERUP COLLECTION --------
        collected_pu = pygame.sprite.spritecollide(player, powerups_group, True)
        for pu in collected_pu:
            if pu.ptype == "nitro":
                player.activate_nitro(4)
                active_powerup = "nitro"
                powerup_timer  = 4.0
                score += 10
            elif pu.ptype == "shield":
                player.activate_shield()
                active_powerup = "shield"
                powerup_timer  = -1  # until hit
                score += 5
            elif pu.ptype == "repair":
                active_powerup = "repair"
                powerup_timer  = 0
                score += 5

        # -------- NITRO STRIP (road event) --------
        hit_strip = pygame.sprite.spritecollide(player, events_group, True)
        if hit_strip:
            player.activate_nitro(3)
            if active_powerup != "nitro":
                active_powerup = "nitro"
                powerup_timer  = 3.0

        # -------- OBSTACLE COLLISION --------
        hit_obstacles = pygame.sprite.spritecollide(player, obstacles_group, True)
        for ob in hit_obstacles:
            if player.has_shield:
                player.use_shield()
                active_powerup = None
            elif ob.slow:
                slowdown_timer = 2.0  # oil spill → slowdown
            else:
                crashed = True

        # -------- ENEMY COLLISION --------
        if pygame.sprite.spritecollideany(player, enemies_group):
            if player.has_shield:
                player.use_shield()
                active_powerup = None
                # push enemies away
                for e in enemies_group:
                    if player.rect.colliderect(e.rect):
                        e.kill()
            elif active_powerup == "repair":
                active_powerup = None
                powerup_timer  = 0
            else:
                crashed = True

        if crashed:
            running = False

        # -------- FINISH CHECK --------
        if distance >= FINISH_DISTANCE:
            score += 500  # finish bonus
            running = False

        # -------- DRAW --------
        surf.fill((30, 30, 30))
        road.draw(surf)

        # Draw sprites
        for entity in enemies_group:
            surf.blit(entity.image, entity.rect)
        for entity in coins_group:
            surf.blit(entity.image, entity.rect)
        for entity in obstacles_group:
            surf.blit(entity.image, entity.rect)
        for entity in events_group:
            surf.blit(entity.image, entity.rect)
        for entity in powerups_group:
            surf.blit(entity.image, entity.rect)
        surf.blit(player.image, player.rect)

        # HUD
        draw_hud(surf, score, coins, distance, FINISH_DISTANCE,
                 active_powerup, powerup_timer, effective_speed)

        pygame.display.update()

    # Clean timers
    for ev in [SPAWN_COIN, SPAWN_ENEMY, SPAWN_POWERUP, SPAWN_OBSTACLE, SPAWN_EVENT]:
        pygame.time.set_timer(ev, 0)

    # Stop music, play crash sound
    try:
        if imgs.get("sound_bg"):
            imgs["sound_bg"].stop()
        if crashed and settings.get("sound", True) and imgs.get("sound_crash"):
            imgs["sound_crash"].play()
            pygame.time.wait(600)
    except:
        pass

    return {"score": score, "distance": distance, "coins": coins}