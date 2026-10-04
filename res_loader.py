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
        # --- Загрузка локализаций ---
        text_root = self.paths.get("configs/text")
        if text_root and os.path.exists(text_root):
            self.text_loader = TextLoader(text_root)
        else:
            self.text_loader = None

        if self.ready:
            self._load_dialogs()

        self._scan_lua_functions()

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

    def get_dialogs_xml_path(self):
        return os.path.join(self.paths["configs/gameplay"], "dialogs", "dialogs.xml")

    # ---------------------------------------------------------
    # ЗАГРУЗКА ДИАЛОГОВ
    # ---------------------------------------------------------
    def _load_dialogs(self):
        dialogs_dir = os.path.join(self.paths["configs/gameplay"], "dialogs")

        if not os.path.exists(dialogs_dir):
            self.errors.append(f"Папка dialogs не найдена: {dialogs_dir}")
            return

        # ВАЖНО: очищаем старый список диалогов
        self.dialogs.clear()

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

                for dialog in root.findall("dialog"):
                    dialog_id = dialog.get("id")

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

                    pre_lines = []
                    has_lines = []
                    dont_lines = []
                    init_lines = []

                    for i in range(start, end + 1):
                        line = lines[i]
                        if "<precondition>" in line and "<phrase" not in line:
                            pre_lines.append(i)
                        if "<has_info>" in line and "<phrase" not in line:
                            has_lines.append(i)
                        if "<dont_has_info>" in line and "<phrase" not in line:
                            dont_lines.append(i)
                        if "<init_func>" in line and "<phrase" not in line:
                            init_lines.append(i)

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
                            "init": init_lines,
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
        init_func = [n.text for n in node.findall("init_func")]

        return {
            "id": dialog_id,
            "xml_path": data["xml_path"],
            "xml_node": data["xml_node"],     # ← ДОБАВЛЕНО
            "xml_root": data["xml_root"],     # ← ДОБАВЛЕНО
            "lines": data["lines"],           # ← ДОБАВЛЕНО
            "line_map": data["line_map"],     # ← ДОБАВЛЕНО

            "preconditions": preconditions,
            "has_info": has_info,
            "dont_has_info": dont_has_info,
            "init_func": init_func
        }

    # ---------------------------------------------------------
    # СОХРАНЕНИЕ ДИАЛОГА — ПОСТРОЧНО (ТОЛЬКО ДЛЯ СУЩЕСТВУЮЩИХ)
    # ---------------------------------------------------------
    def save_dialog(self, dialog_id, new_data):
        global EDIT_BUFFER

        # Диалог должен существовать в loader.dialogs
        if dialog_id not in self.dialogs:
            print(f"[ERROR] save_dialog: dialog '{dialog_id}' not found in loader.dialogs")
            return

        entry = self.dialogs[dialog_id]
        lines = entry["lines"]
        path = entry["xml_path"]

        to_delete = new_data.get("_delete_lines", [])

        # --- Ищем начало и конец диалога ---
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

        # --- Применяем EDIT_BUFFER ---
        if EDIT_BUFFER:
            for pair in EDIT_BUFFER:
                old_tag   = pair["old_tag"]
                new_tag   = pair["new_tag"]
                old_param = pair["old_param"]
                new_param = pair["new_param"]

                old_line = f"<{old_tag}>{old_param}</{old_tag}>"
                new_line = f"<{new_tag}>{new_param}</{new_tag}>"

                found = False

                for i in range(start, end + 1):
                    if old_line in lines[i]:
                        lines[i] = lines[i].replace(old_line, new_line)
                        found = True

                if not found:
                    print(f"[ERROR] Строка '{old_line}' не найдена в диалоге — отмена сохранения")
                    return

        # --- Удаляем строки ---
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

        dialog_node = None
        for d in root.findall("dialog"):
            if d.get("id") == dialog_id:
                dialog_node = d
                break

        if dialog_node is None:
            print(f"[ERROR] reload_dialog: dialog '{dialog_id}' not found in XML")
            return False

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

        pre_lines = []
        has_lines = []
        dont_lines = []
        init_lines = []

        for i in range(start, end + 1):
            line = lines[i]
            if "<precondition>" in line and "<phrase" not in line:
                pre_lines.append(i)
            if "<has_info>" in line and "<phrase" not in line:
                has_lines.append(i)
            if "<dont_has_info>" in line and "<phrase" not in line:
                dont_lines.append(i)
            if "<init_func>" in line and "<phrase" not in line:
                init_lines.append(i)

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
                "init": init_lines,
            }
        }

        print(f"[OK] Диалог {dialog_id} перезагружен из XML.")
        return True

    def _scan_lua_functions(self):
        scripts_root = self.paths.get("scripts")
        if not scripts_root or not os.path.exists(scripts_root):
            self.lua_functions = set()
            return

        functions = set()

        for dirpath, dirnames, filenames in os.walk(scripts_root):
            for fname in filenames:
                if not (fname.lower().endswith(".script") or fname.lower().endswith(".lua")):
                    continue

                full_path = os.path.join(dirpath, fname)
                namespace = os.path.splitext(fname)[0]

                try:
                    with open(full_path, "r", encoding="latin-1", errors="ignore") as f:
                        content = f.read()
                    func_names = re.findall(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
                except Exception:
                    continue

                for func_name in func_names:
                    functions.add(f"{namespace}.{func_name}")

        self.lua_functions = functions

class TextLoader:
    """
    Загружает ВСЕ xml-файлы из configs/text/ и всех подпапок.
    Создаёт индекс локализаций, доступный через self.localization.
    """

    def __init__(self, root_text_path):
        self.root = root_text_path
        self.text_xml = []          # список всех xml-файлов
        self.localization = {}      # ключ → текст
        self.load_all_xml()
        self.load_localization()

    # ---------------------------------------------------------
    # Рекурсивный обход всех подпапок text/
    # ---------------------------------------------------------
    def load_all_xml(self):
        self.text_xml.clear()

        for dirpath, dirnames, filenames in os.walk(self.root):
            for fname in filenames:
                if fname.lower().endswith(".xml"):
                    full_path = os.path.join(dirpath, fname)
                    self.text_xml.append(full_path)

        print(f"[TextLoader] Найдено XML файлов: {len(self.text_xml)}")

    # ---------------------------------------------------------
    # Загрузка всех строк локализации
    # ---------------------------------------------------------
    def load_localization(self):
        self.localization.clear()

        for xml_path in self.text_xml:
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()

                for node in root.findall(".//string"):
                    key = node.get("id")
                    text = (node.text or "").strip()
                    if key:
                        self.localization[key] = text

            except Exception as e:
                print(f"[TextLoader] Ошибка чтения {xml_path}: {e}")

        print(f"[TextLoader] Загружено строк: {len(self.localization)}")

    # ---------------------------------------------------------
    # Получение строки по ключу
    # ---------------------------------------------------------
    def get(self, key, default=""):
        return self.localization.get(key, default)
