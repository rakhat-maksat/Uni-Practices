import json
import os

LEADERBOARD_FILE = "leaderboard.json"
SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "sound": True,
    "car_color": "blue",
    "difficulty": "normal"
}

# ============ SETTINGS ============

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                # merge with defaults in case keys missing
                for k, v in DEFAULT_SETTINGS.items():
                    if k not in data:
                        data[k] = v
                return data
        except:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

# ============ LEADERBOARD ============

def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return []

def save_score(name, score, distance, coins):
    board = load_leaderboard()
    board.append({
        "name": name,
        "score": score,
        "distance": distance,
        "coins": coins
    })
    board.sort(key=lambda x: x["score"], reverse=True)
    board = board[:10]
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(board, f, indent=2)
    return board