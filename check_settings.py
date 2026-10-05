import json
import os

settings_path = os.path.join('E:', 'GitHub', 'OGSR_Game_Editor', 'dist', 'settings', 'settings.json')
if os.path.exists(settings_path):
    with open(settings_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    font = data.get("font", {})
    print(f"font settings: {font}")
else:
    print("settings.json not found")
