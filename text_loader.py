import os
import xml.etree.ElementTree as ET


class TextLoader:
    """
    Загружает ВСЕ xml-файлы из configs/text/ и всех подпапок.
    Создаёт индекс локализаций, доступный через self.text_xml.
    """

    def __init__(self, root_text_path):
        """
        root_text_path — путь к configs/text/
        """
        self.root = root_text_path
        self.text_xml = []          # список всех xml-файлов
        self.localization = {}      # ключ → текст
        self.load_all_xml()

    # ============================================================
    #   Рекурсивный обход всех подпапок text/
    # ============================================================
    def load_all_xml(self):
        """
        Ищет все XML-файлы в каталоге text/ и всех подпапках.
        """
        self.text_xml.clear()

        for dirpath, dirnames, filenames in os.walk(self.root):
            for fname in filenames:
                if fname.lower().endswith(".xml"):
                    full_path = os.path.join(dirpath, fname)
                    self.text_xml.append(full_path)

        print(f"[TextLoader] Найдено XML файлов: {len(self.text_xml)}")

    # ============================================================
    #   Загрузка всех текстов из найденных XML
    # ============================================================
    def load_localization(self):
        """
        Загружает все строки локализации из всех XML.
        Формат OGSR: <string id="...">Текст</string>
        """
        self.localization.clear()

        for xml_path in self.text_xml:
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()

                for node in root.findall(".//string"):
                    key = node.get("id")
                    text = (node.text or "").strip()
                    if key:
                        self.localization[key] = {
                            "text": text,
                            "source_file": xml_path,
                        }

            except Exception as e:
                print(f"[TextLoader] Ошибка чтения {xml_path}: {e}")

        print(f"[TextLoader] Загружено строк: {len(self.localization)}")

    # ============================================================
    #   Получение строки по ключу
    # ============================================================
    def get(self, key, default=""):
        value = self.localization.get(key, default)
        if isinstance(value, dict):
            return value.get("text", default)
        return value
