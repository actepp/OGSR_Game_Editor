import os
import re
import xml.etree.ElementTree as ET
from windows.dialog_properties import EDIT_BUFFER

class ResourceLoader:
    def __init__(self, settings, progress_callback=None):
        self.settings = settings
        self.paths = settings.get("paths", {})
        self.progress_callback = progress_callback

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
            "spawns",
            "scripts"
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

        xml_files = [f for f in os.listdir(dialogs_dir) if f.endswith(".xml")]
        total = len(xml_files)
        processed = 0

        for filename in xml_files:
            full_path = os.path.join(dialogs_dir, filename)

            try:
                tree = ET.parse(full_path)
                root = tree.getroot()

                with open(full_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                # --- Проходим по всем диалогам в файле ---
                for dialog in root.findall("dialog"):
                    dialog_id = dialog.get("id")

                    # --- Ищем начало диалога ---
                    start = None
                    pattern = rf'<dialog\s+[^>]*id="{dialog_id}"'
                    for i, line in enumerate(lines):
                        if re.search(pattern, line):
                            start = i
                            break

                    # --- Ищем конец диалога ---
                    end = None
                    if start is not None:
                        for i in range(start + 1, len(lines)):
                            if "</dialog>" in lines[i]:
                                end = i
                                break

                    # --- Fallback если не нашли границы ---
                    if start is None or end is None:
                        print(f"[WARN] Диалог {dialog_id}: не удалось определить границы, fallback.")
                        start = 0
                        end = len(lines) - 1

                    # --- Строим line_map только внутри диалога ---
                    pre_lines = []
                    has_lines = []
                    dont_lines = []

                    for i in range(start, end + 1):
                        line = lines[i]
                        if "<precondition>" in line and "<phrase" not in line:
                            pre_lines.append(i)
                        if "<has_info>" in line and "<phrase" not in line:
                            has_lines.append(i)
                        if "<dont_has_info>" in line and "<phrase" not in line:
                            dont_lines.append(i)

                    # --- Сохраняем диалог ---
                    self.dialogs[dialog_id] = {
                        "id": dialog_id,
                        "xml_path": full_path,
                        "xml_node": dialog,
                        "xml_root": root,
                        "lines": lines,
                        "line_map": {
                            "pre": pre_lines,
                            "has": has_lines,
                            "dont": dont_lines,
                        }
                    }

            except Exception as e:
                self.errors.append(f"Ошибка чтения {filename}: {e}")

            processed += 1
            if self.progress_callback:
                percent = int((processed / total) * 100)
                self.progress_callback(percent)

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
            "xml_path": data["xml_path"],
            "preconditions": preconditions,
            "has_info": has_info,
            "dont_has_info": dont_has_info
        }

    # ---------------------------------------------------------
    # СОХРАНЕНИЕ ДИАЛОГА — ПОСТРОЧНО
    # ---------------------------------------------------------
    def save_dialog(self, dialog_id, new_data):
        entry = self.dialogs[dialog_id]
        lines = entry["lines"]
        path = entry["xml_path"]

        # строки, которые нужно удалить
        to_delete = new_data.get("_delete_lines", [])

        # --- Ищем границы диалога ---
        start = None
        end = None

        pattern = rf'<dialog\s+[^>]*id="{dialog_id}"'
        for i, line in enumerate(lines):
            if re.search(pattern, line):
                start = i
                break

        if start is not None:
            for i in range(start + 1, len(lines)):
                if "</dialog>" in lines[i]:
                    end = i
                    break

        if start is None or end is None:
            print(f"[ERROR] save_dialog: cannot find dialog boundaries for {dialog_id}")
            return

        # --- ЭТАП 1: применяем EDIT_BUFFER ТОЛЬКО внутри диалога ---
        global EDIT_BUFFER

        if EDIT_BUFFER:
            print("[SAVE] Применяем EDIT_BUFFER к XML")

            for pair in EDIT_BUFFER:
                old = pair["old"]
                new = pair["new"]

                found = False

                # замены только внутри диалога
                for i in range(start, end + 1):
                    if old in lines[i]:
                        lines[i] = lines[i].replace(old, new)
                        found = True

                if not found:
                    print(f"[ERROR] OLD '{old}' не найден в диалоге — отмена сохранения")
                    return

        # --- ЭТАП 2: удаляем строки ТОЛЬКО внутри диалога ---
        new_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            if start <= i <= end:
                if stripped in to_delete:
                    continue

            new_lines.append(line)

        # --- Сохраняем файл ---
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        print(f"[OK] Диалог {dialog_id} сохранён.")

    # ---------------------------------------------------------
    # ПЕРЕЗАГРУЗКА ДИАЛОГА
    # ---------------------------------------------------------
    def reload_dialog(self, dialog_id):
        entry = self.dialogs.get(dialog_id)
        if not entry:
            print(f"[ERROR] reload_dialog: dialog '{dialog_id}' not found")
            return False

        xml_path = entry["xml_path"]

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except Exception as e:
            print(f"[ERROR] reload_dialog: cannot parse XML '{xml_path}': {e}")
            return False

        try:
            with open(xml_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"[ERROR] reload_dialog: cannot read lines: {e}")
            return False

        # --- Ищем диалог по ID ---
        dialog_node = None
        for d in root.findall("dialog"):
            if d.get("id") == dialog_id:
                dialog_node = d
                break

        if dialog_node is None:
            print(f"[ERROR] reload_dialog: dialog '{dialog_id}' not found in XML")
            return False

        # --- Ищем границы диалога ---
        start = None
        pattern = rf'<dialog\s+[^>]*id="{dialog_id}"'
        for i, line in enumerate(lines):
            if re.search(pattern, line):
                start = i
                break

        end = None
        if start is not None:
            for i in range(start + 1, len(lines)):
                if "</dialog>" in lines[i]:
                    end = i
                    break

        if start is None or end is None:
            start = 0
            end = len(lines) - 1

        # --- Строим line_map ---
        pre_lines = []
        has_lines = []
        dont_lines = []

        for i in range(start, end + 1):
            line = lines[i]
            if "<precondition>" in line and "<phrase" not in line:
                pre_lines.append(i)
            if "<has_info>" in line and "<phrase" not in line:
                has_lines.append(i)
            if "<dont_has_info>" in line and "<phrase" not in line:
                dont_lines.append(i)

        self.dialogs[dialog_id] = {
            "id": dialog_id,
            "xml_path": xml_path,
            "xml_node": dialog_node,
            "xml_root": root,
            "lines": lines,
            "line_map": {
                "pre": pre_lines,
                "has": has_lines,
                "dont": dont_lines,
            }
        }

        print(f"[OK] Диалог {dialog_id} перезагружен из XML.")
        return True
