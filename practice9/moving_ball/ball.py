import pygame

class Ball:
    def __init__(self, x, y, radius=25, color=(255, 0, 0), speed=20):
        """Инициализация мяча"""
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.speed = speed
    
    def move_up(self, screen_height):
        """Двигает мяч вверх"""
        # Проверяем границу (верх экрана)
        if self.y - self.speed - self.radius >= 0:
            self.y -= self.speed
    
    def move_down(self, screen_height):
        """Двигает мяч вниз"""
        # Проверяем границу (низ экрана)
        if self.y + self.speed + self.radius <= screen_height:
            self.y += self.speed
    
    def move_left(self, screen_width):
        """Двигает мяч влево"""
        # Проверяем границу (левая сторона)
        if self.x - self.speed - self.radius >= 0:
            self.x -= self.speed
    
    def move_right(self, screen_width):
        """Двигает мяч вправо"""
        # Проверяем границу (правая сторона)
        if self.x + self.speed + self.radius <= screen_width:
            self.x += self.speed
    
    def draw(self, screen):
        """Рисует мяч на экране"""
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
    
    def get_position(self):
        """Возвращает текущую позицию мяча"""
        return (self.x, self.y)