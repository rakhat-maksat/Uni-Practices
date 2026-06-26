import pygame
from datetime import datetime

class MickeyClock:
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y

        # ФОН (циферблат)
        self.clock_face = pygame.image.load("images/clock.png").convert_alpha()
        self.clock_face = pygame.transform.scale(self.clock_face, (500, 500))
        self.clock_rect = self.clock_face.get_rect(center=(center_x, center_y))

        # ТЕЛО МИККИ
        self.body = pygame.image.load("images/mUmrP.png").convert_alpha()
        self.body = pygame.transform.scale(self.body, (500, 500))
        self.body_rect = self.body.get_rect(center=(center_x, center_y))

        # РУКИ
        self.left_hand = pygame.image.load("images/hand_left.png").convert_alpha()
        self.right_hand = pygame.image.load("images/hand_right.png").convert_alpha()

        self.left_hand = pygame.transform.scale(self.left_hand, (120, 200))
        self.right_hand = pygame.transform.scale(self.right_hand, (120, 200))

        # ⚠️ OFFSET (настраивается!)
        self.left_offset = (0, -80)
        self.right_offset = (0, -80)

        # Шрифт
        self.font = pygame.font.Font(None, 48)

    def get_time(self):
        now = datetime.now()
        return now.minute, now.second

    def calculate_angle(self, value):
        angle = value * 6
        return -angle + 90

    def rotate_hand(self, image, angle, offset):
        rotated_image = pygame.transform.rotate(image, angle)

        offset_vec = pygame.math.Vector2(offset)
        rotated_offset = offset_vec.rotate(-angle)

        rect = rotated_image.get_rect(center=(
            self.center_x + rotated_offset.x,
            self.center_y + rotated_offset.y
        ))

        return rotated_image, rect

    def draw(self, screen):
        minutes, seconds = self.get_time()

        minute_angle = self.calculate_angle(minutes)
        second_angle = self.calculate_angle(seconds)

        # 1. Фон
        screen.blit(self.clock_face, self.clock_rect)

        # 2. Руки (за телом или перед — зависит от твоего PNG)
        left_hand, left_rect = self.rotate_hand(
            self.left_hand, second_angle, self.left_offset
        )

        right_hand, right_rect = self.rotate_hand(
            self.right_hand, minute_angle, self.right_offset
        )

        screen.blit(left_hand, left_rect)
        screen.blit(right_hand, right_rect)

        # 3. Тело поверх (чтобы закрыть соединение рук)
        screen.blit(self.body, self.body_rect)

        # 4. Цифровое время
        text = self.font.render(f"{minutes:02d}:{seconds:02d}", True, (0, 0, 0))
        screen.blit(text, (self.center_x - 50, 550))