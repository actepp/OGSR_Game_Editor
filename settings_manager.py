import json
import os
import sys

SETTINGS_DIR = "settings"
SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "window": {
        "width": 900,
        "height": 600,
        "maximized": False
    },
    "theme": "dark",
    "font": {
        "family": "Segoe UI",
        "size": 10
    }
}

def get_base_path():
    # если запущено как EXE → рядом с .exe
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # если запущено как .py → рядом с .py
    return os.path.dirname(__file__)

def get_settings_path():
    base = get_base_path()
    return os.path.join(base, SETTINGS_DIR, SETTINGS_FILE)

def settings_exist():
    return os.path.exists(get_settings_path())

def load_settings():
    path = get_settings_path()

    # если файла нет — создаём
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4, ensure_ascii=False)
        return DEFAULT_SETTINGS

    # если есть — читаем
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(data):
    path = get_settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
