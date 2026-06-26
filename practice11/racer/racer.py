import pygame
import sys
import random
import time
from pygame.locals import *

# Initialize pygame
pygame.init()

# FPS settings
FPS = 60
FramePerSec = pygame.time.Clock()

# Colors
BLUE   = (0, 0, 255)
RED    = (255, 0, 0)
BLACK  = (0, 0, 0)
WHITE  = (255, 255, 255)
YELLOW = (255, 220, 0)

# Screen settings
SCREEN_WIDTH  = 400
SCREEN_HEIGHT = 600

# Game variables
BASE_SPEED = 5
SPEED = BASE_SPEED
SCORE = 0
COINS = 0
COINS_FOR_SPEED = 10   # every 10 coins → increase speed

# Fonts
font = pygame.font.SysFont("Verdana", 60)
font_small = pygame.font.SysFont("Verdana", 20)
game_over_text = font.render("Game Over", True, BLACK)

# Create window
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Racer")

# Load images (with fallback)
def load_image_or_rect(path, size, color):
    try:
        return pygame.image.load(path).convert_alpha()
    except:
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill(color)
        return surf

background   = load_image_or_rect("background.jpg", (SCREEN_WIDTH, SCREEN_HEIGHT), (80, 80, 80))
enemy_image  = load_image_or_rect("Enemy.jpg", (60, 80), RED)
player_image = load_image_or_rect("Player.jpg", (50, 70), BLUE)

# Resize background if needed
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))


# ================= ENEMY =================
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = enemy_image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = (random.randint(40, SCREEN_WIDTH - 40), -50)

    def move(self):
        global SCORE
        self.rect.move_ip(0, SPEED)

        # If enemy leaves screen → respawn + score
        if self.rect.top > SCREEN_HEIGHT:
            SCORE += 1
            self.rect.center = (random.randint(40, SCREEN_WIDTH - 40), -50)


# ================= PLAYER =================
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = (160, 520)

    def move(self):
        pressed = pygame.key.get_pressed()

        if self.rect.left > 0 and pressed[K_LEFT]:
            self.rect.move_ip(-5, 0)

        if self.rect.right < SCREEN_WIDTH and pressed[K_RIGHT]:
            self.rect.move_ip(5, 0)


# ================= COIN =================
class Coin(pygame.sprite.Sprite):
    RADIUS = 12

    def __init__(self):
        super().__init__()

        # Random weight
        self.weight = random.choice([1, 2, 5])

        # Color depends on value
        if self.weight == 1:
            color = YELLOW
        elif self.weight == 2:
            color = (255, 150, 0)
        else:
            color = (255, 215, 0)

        # Create coin surface
        size = self.RADIUS * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (self.RADIUS, self.RADIUS), self.RADIUS)

        # Show value on coin
        value_text = font_small.render(str(self.weight), True, BLACK)
        self.image.blit(value_text, (4, 2))

        self.rect = self.image.get_rect()
        self.respawn()

    def respawn(self):
        """Spawn coin above screen at random position"""
        self.rect.center = (
            random.randint(20, SCREEN_WIDTH - 20),
            random.randint(-SCREEN_HEIGHT, -20)
        )

    def move(self):
        """Move coin down slower than enemy"""
        self.rect.move_ip(0, max(2, SPEED // 2))

        if self.rect.top > SCREEN_HEIGHT:
            self.respawn()


# Create objects
P1 = Player()
E1 = Enemy()

coins_group = pygame.sprite.Group()
for _ in range(3):
    coins_group.add(Coin())

enemies = pygame.sprite.Group(E1)
all_sprites = pygame.sprite.Group(P1, E1, *coins_group)

# Spawn extra coins event
SPAWN_COIN = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_COIN, 4000)


# ================= GAME LOOP =================
while True:

    # -------- EVENTS --------
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

        # Randomly add new coin
        if event.type == SPAWN_COIN:
            if random.random() < 0.6:
                new_coin = Coin()
                coins_group.add(new_coin)
                all_sprites.add(new_coin)

    # -------- DRAW BACKGROUND --------
    DISPLAYSURF.blit(background, (0, 0))

    # -------- MOVE & DRAW --------
    for entity in all_sprites:
        entity.move()
        DISPLAYSURF.blit(entity.image, entity.rect)

    # -------- COIN COLLECTION --------
    collected = pygame.sprite.spritecollide(P1, coins_group, True)

    for coin in collected:
        COINS += coin.weight

        # Respawn new coin
        new_coin = Coin()
        coins_group.add(new_coin)
        all_sprites.add(new_coin)

    # -------- SPEED SCALING --------
    SPEED = BASE_SPEED + (COINS // COINS_FOR_SPEED)

    # -------- DRAW SCORE --------
    score_surf = font_small.render(f"Score: {SCORE}", True, BLACK)
    DISPLAYSURF.blit(score_surf, (10, 10))

    # -------- DRAW COINS --------
    coins_surf = font_small.render(f"Coins: {COINS}", True, YELLOW)
    DISPLAYSURF.blit(coins_surf, (SCREEN_WIDTH - coins_surf.get_width() - 10, 10))

    # -------- COLLISION --------
    if pygame.sprite.spritecollideany(P1, enemies):

        try:
            pygame.mixer.Sound("crash.wav").play()
            time.sleep(0.5)
        except:
            pass

        DISPLAYSURF.fill(RED)
        DISPLAYSURF.blit(game_over_text, (30, 250))

        final = font_small.render(f"Score: {SCORE}  Coins: {COINS}", True, BLACK)
        DISPLAYSURF.blit(final, (80, 340))

        pygame.display.update()
        time.sleep(2)

        pygame.quit()
        sys.exit()

    # -------- UPDATE --------
    pygame.display.update()
    FramePerSec.tick(FPS)