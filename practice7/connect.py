import psycopg2
from config import DB_CONFIG

def get_connection():
    """Создает подключение к PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        return None