import json
import os
import sys

settings_path = os.path.join(os.path.dirname(__file__), "settings", "settings.json")
if os.path.exists(settings_path):
    with open(settings_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    font = data.get("font", {})
    print(f"Current font settings: family={font.get('family')}, size={font.get('size')}")
else:
    print("settings.json not found at:", settings_path)
