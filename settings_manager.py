import json
import os

SETTINGS_DIR = "settings"
SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "window": {
        "width": 900,
        "height": 600,
        "maximized": False
    },
    "paths": {
        "dialogs_root": "game_data/dialogs/"
    },
    "editor": {
        "autosave": True,
        "theme": "dark"
    }
}

def get_settings_path():
    return os.path.join(os.path.dirname(__file__), SETTINGS_DIR, SETTINGS_FILE)

def load_settings():
    path = get_settings_path()

    # если нет папки — создаём
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # если нет файла — создаём с дефолтом
    if not os.path.exists(path):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS

    # читаем файл
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(data):
    path = get_settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
