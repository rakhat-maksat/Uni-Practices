import json
import os

SETTINGS_FILE = "settings.json"

DEFAULTS = {
    "snake_color": [0, 200, 0],
    "grid_overlay": False,
    "sound": False,
}

def load_settings() -> dict:
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULTS.copy())
        return DEFAULTS.copy()
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
        # добавляем отсутствующие ключи дефолтами
        for key, val in DEFAULTS.items():
            if key not in data:
                data[key] = val
        return data
    except (json.JSONDecodeError, IOError):
        return DEFAULTS.copy()

def save_settings(settings: dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def get_snake_color(settings: dict) -> tuple:
    c = settings.get("snake_color", DEFAULTS["snake_color"])
    return tuple(c)

def get_snake_dark_color(settings: dict) -> tuple:
    """Тёмная версия цвета змейки для тела."""
    r, g, b = get_snake_color(settings)
    return (max(0, r - 60), max(0, g - 60), max(0, b - 60))