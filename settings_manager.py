import json
import os

SETTINGS_DIR = "settings"
SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "window": {
        "width": 900,
        "height": 600,
        "maximized": False
    }
}

def get_settings_path():
    return os.path.join(os.path.dirname(__file__), SETTINGS_DIR, SETTINGS_FILE)

def settings_exist():
    return os.path.exists(get_settings_path())

def load_settings():
    path = get_settings_path()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(data):
    path = get_settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
