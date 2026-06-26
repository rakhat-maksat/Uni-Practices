import pygame
import sys
import random
import time
from pygame.locals import *

pygame.init()

FPS = 60
FramePerSec = pygame.time.Clock()

BLUE   = (0,   0,   255)
RED    = (255, 0,   0)
GREEN  = (0,   255, 0)
BLACK  = (0,   0,   0)
WHITE  = (255, 255, 255)
YELLOW = (255, 220, 0)

SCREEN_WIDTH  = 400
SCREEN_HEIGHT = 600
SPEED  = 5   
SCORE  = 0   
COINS  = 0   

font = pygame.font.SysFont("Verdana", 60)
font_small = pygame.font.SysFont("Verdana", 20)
game_over_text = font.render("Game Over", True, BLACK)  

DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
DISPLAYSURF.fill(WHITE)
pygame.display.set_caption("Racer")

def load_image_or_rect(path, fallback_size, fallback_color):
    try:
        return pygame.image.load(path).convert_alpha()
    except FileNotFoundError:
        surf = pygame.Surface(fallback_size, pygame.SRCALPHA)
        surf.fill(fallback_color)
        return surf

background   = load_image_or_rect("background.jpg", (SCREEN_WIDTH, SCREEN_HEIGHT), (80, 80, 80))
enemy_image  = load_image_or_rect("Enemy.jpg",           (60, 80),                      RED)
player_image = load_image_or_rect("Player.jpg",          (50, 70),                      BLUE)

if background.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
    background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))


class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = enemy_image.copy()
        self.rect  = self.image.get_rect()
        self.rect.center = (random.randint(40, SCREEN_WIDTH - 40), 0)

    def move(self):
        global SCORE
        self.rect.move_ip(0, SPEED)
        if self.rect.top > SCREEN_HEIGHT:
            SCORE += 1                                             # player dodged one car
            self.rect.top = 0
            self.rect.center = (random.randint(40, SCREEN_WIDTH - 40), 0)


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_image.copy()
        self.rect  = self.image.get_rect()
        self.rect.center = (160, 520)   

    def move(self):
        pressed = pygame.key.get_pressed()
        if self.rect.left > 0 and pressed[K_LEFT]:
            self.rect.move_ip(-5, 0)
        if self.rect.right < SCREEN_WIDTH and pressed[K_RIGHT]:
            self.rect.move_ip(5, 0)


class Coin(pygame.sprite.Sprite):
    RADIUS = 12   # radius in pixels

    def __init__(self):
        super().__init__()
        # Draw a yellow circle on a transparent surface
        size = self.RADIUS * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (self.RADIUS, self.RADIUS), self.RADIUS)
        pygame.draw.circle(self.image, (200, 160, 0), (self.RADIUS, self.RADIUS), self.RADIUS, 2)  # border
        self.rect = self.image.get_rect()
        self._respawn()

    def _respawn(self):
        """Place the coin at a random horizontal position above the screen."""
        self.rect.center = (random.randint(20, SCREEN_WIDTH - 20),
                            random.randint(-SCREEN_HEIGHT, -20))  # above the visible area

    def move(self):
        """Move the coin downward at half the enemy speed; respawn when off screen."""
        self.rect.move_ip(0, max(2, SPEED // 2))   # coins are slower than enemies
        if self.rect.top > SCREEN_HEIGHT:
            self._respawn()


P1 = Player()
E1 = Enemy()

coins_group = pygame.sprite.Group()
for _ in range(3):
    coins_group.add(Coin())

# Sprite groups:
#   enemies      – used for collision detection with player
#   coins_group  – used for coin pickup detection
#   all_sprites  – used for drawing/moving everything
enemies = pygame.sprite.Group()
enemies.add(E1)
all_sprites = pygame.sprite.Group()
all_sprites.add(P1, E1, *coins_group)


INC_SPEED = pygame.USEREVENT + 1
pygame.time.set_timer(INC_SPEED, 1000)

# SPAWN_COIN fires every 4 seconds to randomly add extra coins
SPAWN_COIN = pygame.USEREVENT + 2
pygame.time.set_timer(SPAWN_COIN, 4000)


while True:

    # --- Process Events ---
    for event in pygame.event.get():

        if event.type == QUIT:                  # window close button
            pygame.quit()
            sys.exit()

        if event.type == INC_SPEED:             # increase enemy speed every second
            SPEED += 0.5

        if event.type == SPAWN_COIN:            # randomly spawn an extra coin
            if random.random() < 0.6:           # 60 % chance of spawning
                new_coin = Coin()
                coins_group.add(new_coin)
                all_sprites.add(new_coin)

    # --- Draw Background (must be drawn first so sprites appear on top) ---
    DISPLAYSURF.blit(background, (0, 0))

    # --- Draw and Move All Sprites ---
    for entity in all_sprites:
        entity.move()
        DISPLAYSURF.blit(entity.image, entity.rect)

    # --- Coin Collection Check ---
    collected = pygame.sprite.spritecollide(P1, coins_group, False)
    for coin in collected:
        COINS += 1          # increment coin counter
        coin._respawn()     # reuse the coin object – move it back above the screen

    # --- HUD: score (top-left) ---
    score_surf = font_small.render(f"Score: {SCORE}", True, BLACK)
    DISPLAYSURF.blit(score_surf, (10, 10))

    # --- HUD: coins (top-right) ---
    coins_surf = font_small.render(f"Coins: {COINS}", True, YELLOW)
    coin_x = SCREEN_WIDTH - coins_surf.get_width() - 10   # right-align with 10 px margin
    DISPLAYSURF.blit(coins_surf, (coin_x, 10))

    # --- Collision with Enemy → Game Over ---
    if pygame.sprite.spritecollideany(P1, enemies):
        # Try to play crash sound (silently ignore if file is missing)
        try:
            pygame.mixer.Sound("crash.wav").play()
            time.sleep(0.5)
        except Exception:
            pass

        # Show red Game Over screen
        DISPLAYSURF.fill(RED)
        DISPLAYSURF.blit(game_over_text, (30, 250))

        # Show final score and coins on the game over screen
        final_score = font_small.render(f"Score: {SCORE}   Coins: {COINS}", True, BLACK)
        DISPLAYSURF.blit(final_score, (80, 340))

        pygame.display.update()

        # Clean up all sprites then pause before quitting
        for entity in all_sprites:
            entity.kill()
        time.sleep(2)
        pygame.quit()
        sys.exit()

    # --- Update Display and Tick Clock ---
    pygame.display.update()
    FramePerSec.tick(FPS)
