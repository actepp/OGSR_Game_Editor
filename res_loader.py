import os
import re
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
    # ЗАГРУЗКА ДИАЛОГОВ
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
                # читаем XML
                tree = ET.parse(full_path)
                root = tree.getroot()

                # читаем строки файла
                with open(full_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                # ищем диалоги
                for dialog in root.findall("dialog"):
                    dialog_id = dialog.get("id")
                    priority = dialog.get("priority", "0")

                    # ищем строки глобальных свойств
                    pre_lines = []
                    has_lines = []
                    dont_lines = []
                    priority_line = None

                    for i, line in enumerate(lines):
                        if f'<dialog id="{dialog_id}"' in line:
                            priority_line = i
                        if "<precondition>" in line and "<phrase" not in line:
                            pre_lines.append(i)
                        if "<has_info>" in line and "<phrase" not in line:
                            has_lines.append(i)
                        if "<dont_has_info>" in line and "<phrase" not in line:
                            dont_lines.append(i)

                    self.dialogs[dialog_id] = {
                        "id": dialog_id,
                        "priority": int(priority),
                        "xml_path": full_path,
                        "xml_node": dialog,
                        "xml_root": root,
                        "lines": lines,
                        "line_map": {
                            "priority": priority_line,
                            "pre": pre_lines,
                            "has": has_lines,
                            "dont": dont_lines,
                        }
                    }

            except Exception as e:
                self.errors.append(f"Ошибка чтения {filename}: {e}")

    # ---------------------------------------------------------
    # API
    # ---------------------------------------------------------
    def is_ready(self):
        return self.ready

    def get_dialog_list(self):
        return list(self.dialogs.keys())

    def get_dialog(self, dialog_id):
        data = self.dialogs[dialog_id]
        node = data["xml_node"]

        preconditions = [n.text for n in node.findall("precondition")]
        has_info = [n.text for n in node.findall("has_info")]
        dont_has_info = [n.text for n in node.findall("dont_has_info")]

        return {
            "id": dialog_id,
            "priority": data["priority"],
            "xml_path": data["xml_path"],
            "preconditions": preconditions,
            "has_info": has_info,
            "dont_has_info": dont_has_info,
        }

    # ---------------------------------------------------------
    # СОХРАНЕНИЕ ДИАЛОГА — ПОСТРОЧНО
    # ---------------------------------------------------------
    def save_dialog(self, dialog_id, new_data):
        entry = self.dialogs[dialog_id]
        lines = entry["lines"]
        lm = entry["line_map"]
        path = entry["xml_path"]

        # priority
        p_line = lm["priority"]
        if p_line is not None:
            old = lines[p_line]
            if "priority=" in old:
                lines[p_line] = re.sub(
                    r'priority=".*?"',
                    f'priority="{new_data["priority"]}"',
                    old
                )
            else:
                lines[p_line] = old.replace(
                    ">",
                    f' priority="{new_data["priority"]}">'
                )

        # preconditions
        for idx, val in zip(lm["pre"], new_data["preconditions"]):
            lines[idx] = f"    <precondition>{val}</precondition>\n"

        # has_info
        for idx, val in zip(lm["has"], new_data["has_info"]):
            lines[idx] = f"    <has_info>{val}</has_info>\n"

        # dont_has_info
        for idx, val in zip(lm["dont"], new_data["dont_has_info"]):
            lines[idx] = f"    <dont_has_info>{val}</dont_has_info>\n"

        # сохраняем файл
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"[OK] Диалог {dialog_id} сохранён.")
