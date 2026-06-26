import pygame
import os

class MusicPlayer:
    def __init__(self, music_folder="music"):
        """Инициализация музыкального плеера"""
        pygame.mixer.init()
        
        self.music_folder = music_folder
        self.playlist = []
        self.current_track = 0
        self.is_playing = False
        
        # Загружаем плейлист
        self.load_playlist()
        
        # Загружаем первый трек
        if self.playlist:
            self.load_track(self.current_track)
    
    def load_playlist(self):
        """Загружает список треков из папки"""
        if os.path.exists(self.music_folder):
            self.playlist = [f for f in os.listdir(self.music_folder) 
                           if f.endswith(('.mp3', '.wav'))]
        else:
            print(f"Папка {self.music_folder} не найдена!")
    
    def load_track(self, index):
        """Загружает трек по индексу"""
        if 0 <= index < len(self.playlist):
            track_path = os.path.join(self.music_folder, self.playlist[index])
            pygame.mixer.music.load(track_path)
    
    def play(self):
        """Играет музыку"""
        pygame.mixer.music.play()
        self.is_playing = True
    
    def stop(self):
        """Останавливает музыку"""
        pygame.mixer.music.stop()
        self.is_playing = False
    
    def next_track(self):
        """Переключает на следующий трек"""
        if self.playlist:
            self.current_track = (self.current_track + 1) % len(self.playlist)
            self.load_track(self.current_track)
            self.play()
    
    def previous_track(self):
        """Переключает на предыдущий трек"""
        if self.playlist:
            self.current_track = (self.current_track - 1) % len(self.playlist)
            self.load_track(self.current_track)
            self.play()
    
    def get_current_track_name(self):
        """Возвращает имя текущего трека"""
        if self.playlist:
            return self.playlist[self.current_track]
        return "No tracks"
    
    def get_status(self):
        """Возвращает статус плеера"""
        return "Playing..." if self.is_playing else "Stopped"
    
    def has_tracks(self):
        """Проверяет есть ли треки в плейлисте"""
        return len(self.playlist) > 0