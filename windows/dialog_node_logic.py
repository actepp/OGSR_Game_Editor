import os
import xml.etree.ElementTree as ET


# ============================================================
#   Узел фразы (логический квадратик)
# ============================================================

class PhraseNode:
    def __init__(self, pid: int):
        self.id = pid
        self.text_key = ""          # ключ из <text>
        self.text_real = ""         # реальный текст из configs/text
        self.next_list: list[int] = []   # список детей (несколько <next>)


# ============================================================
#   Граф диалога (цепочка фраз)
# ============================================================

class DialogGraph:
    def __init__(self, dialog_id: str):
        self.dialog_id = dialog_id
        self.phrases: dict[int, PhraseNode] = {}


# ============================================================
#   Основная логика диалогов
# ============================================================

class DialogNodeLogic:
    def __init__(self, text_root_path: str):
        """
        text_root_path = путь к configs/text
        """
        self.text_root_path = text_root_path
        self.string_table = {}  # id → {"rus": "...", "eng": "..."}

        self._load_string_table()
        self.text_key = ""

    # ---------------------------------------------------------
    #   Загрузка всех текстов из configs/text/*.xml
    # ---------------------------------------------------------
    def _load_string_table(self):
        if not os.path.exists(self.text_root_path):
            print(f"[WARN] Text directory not found: {self.text_root_path}")
            return

        # РЕКУРСИВНЫЙ ОБХОД ВСЕХ ПАПОК
        for dirpath, dirnames, filenames in os.walk(self.text_root_path):
            for filename in filenames:
                if not filename.lower().endswith(".xml"):
                    continue

                full_path = os.path.join(dirpath, filename)

                try:
                    tree = ET.parse(full_path)
                    root = tree.getroot()

                    for s in root.findall("string"):
                        sid = s.get("id")
                        if not sid:
                            continue

                        entry = {}

                        # вариант 1: <string><rus>...</rus><eng>...</eng></string>
                        for child in s:
                            entry[child.tag] = child.text or ""

                        # вариант 2: <string id="x" rus="..." eng="..."/>
                        for attr in ("rus", "eng"):
                            if attr in s.attrib:
                                entry[attr] = s.attrib[attr]

                        self.string_table[sid] = entry

                except Exception as e:
                    print(f"[ERROR] Cannot parse text file {full_path}: {e}")

    # ---------------------------------------------------------
    #   Получить реальный текст по ключу
    # ---------------------------------------------------------
    def resolve_text(self, key: str, locale: str) -> str:
        entry = self.string_table.get(key)
        if not entry:
            return f"[{key}]"

        return entry.get(locale, f"[{key}]")

    # ---------------------------------------------------------
    #   Построить граф диалога из XML
    # ---------------------------------------------------------
    def build_graph(self, dialog_xml_root, locale: str = "rus") -> DialogGraph:
        dialog_id = dialog_xml_root.get("id")
        graph = DialogGraph(dialog_id)

        phrase_list = dialog_xml_root.find("phrase_list")
        if phrase_list is None:
            return graph

        for phrase in phrase_list.findall("phrase"):
            pid = int(phrase.get("id"))
            node = PhraseNode(pid)

            # ключ текста
            node.text_key = phrase.findtext("text", "")

            # реальный текст
            node.text_real = self.resolve_text(node.text_key, locale)

            # собираем ВСЕ <next>
            node.next_list = [
                int(n.text) for n in phrase.findall("next")
                if n.text and n.text.strip()
            ]

            graph.phrases[pid] = node

        return graph
