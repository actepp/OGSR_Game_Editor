import os
import xml.etree.ElementTree as ET


class ResourceLoader:
    def __init__(self, settings):
        self.settings = settings
        self.paths = settings.get("paths", {})

        self.ready = False
        self.errors = []

        self.dialogs = {}  # {dialog_id: dialog_data}

        self._validate_paths()

        if self.ready:
            self._load_dialogs()

    def _validate_paths(self):
        required = [
            "gamedata",
            "configs/gameplay",
            "configs/creatures",
            "configs/text",
            "spawns"
        ]

        for key in required:
            path = self.paths.get(key)
            if not path or not os.path.exists(path):
                self.errors.append(f"Путь '{key}' не найден: {path}")

        self.ready = len(self.errors) == 0

    # ---------------------------------------------------------
    # ЗАГРУЗКА ДИАЛОГОВ ИЗ configs/gameplay/dialogs/*.xml
    # ---------------------------------------------------------
    def _load_dialogs(self):
        dialogs_dir = os.path.join(self.paths["configs/gameplay"], "dialogs")

        if not os.path.exists(dialogs_dir):
            self.errors.append(f"Папка dialogs не найдена: {dialogs_dir}")
            return

        for filename in os.listdir(dialogs_dir):
            if not filename.endswith(".xml"):
                continue

            full_path = os.path.join(dialogs_dir, filename)

            try:
                tree = ET.parse(full_path)
                root = tree.getroot()

                # <dialog id="xxx">
                for dialog in root.findall("dialog"):
                    dialog_id = dialog.get("id")
                    priority = dialog.get("priority", "0")

                    self.dialogs[dialog_id] = {
                        "id": dialog_id,
                        "priority": int(priority),
                        "xml_path": full_path,
                        "xml_node": dialog
                    }

            except Exception as e:
                self.errors.append(f"Ошибка чтения {filename}: {e}")

    # ---------------------------------------------------------
    # API
    # ---------------------------------------------------------
    def is_ready(self):
        return self.ready

    def get_dialog_list(self):
        """Возвращает список всех ID диалогов."""
        return list(self.dialogs.keys())

    def get_dialog(self, dialog_id):
        return self.dialogs.get(dialog_id)
