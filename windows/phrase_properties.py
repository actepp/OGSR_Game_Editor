import xml.etree.ElementTree as ET

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QGridLayout, QComboBox, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt


def make_line():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    line.setStyleSheet("color: #444;")
    return line


class ClickableSquare(QLabel):
    def __init__(self, text, normal_style, pressed_style):
        super().__init__(text)
        self.normal_style = normal_style
        self.pressed_style = pressed_style
        self.setStyleSheet(self.normal_style)
        self.clicked = lambda: None
        self._is_pressed = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_pressed = True
            self.setStyleSheet(self.pressed_style)

    def mouseReleaseEvent(self, event):
        if not self._is_pressed:
            return
        self._is_pressed = False
        self.setStyleSheet(self.normal_style)
        if self.rect().contains(event.position().toPoint()):
            self.clicked()


class PhraseProperties(QDialog):
    def __init__(self, parent, node):
        super().__init__(parent)
        self.node = node

        # GUI → XML
        self.tag_map = {
            "Give info": "give_info",
            "Disable info": "disable_info",
            "Action": "action",
            "Precondition": "precondition",
            "Has info": "has_info",
            "Dont has info": "dont_has_info"
        }

        fm = self.fontMetrics()
        self.tag_column_width = max(
            fm.horizontalAdvance(name) for name in self.tag_map.keys()
        ) + 45

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle("Свойства фразы")
        self.resize(500, 300)

        # ============================================================
        #   ГЛАВНЫЙ LAYOUT
        # ============================================================
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # ============================================================
        #   ШАПКА — как в DialogProperties
        # ============================================================
        header_grid = QGridLayout()
        header_grid.setColumnStretch(0, 1)

        title = QLabel(f"{node.text_key}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 6px;")
        title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        header_grid.addWidget(title, 0, 0)
        main_layout.addLayout(header_grid)

        # линия под шапкой
        main_layout.addWidget(make_line())

        # ============================================================
        #   ЗОНА СВОЙСТВ — растягивается
        # ============================================================
        self.props_container = QVBoxLayout()
        main_layout.addLayout(self.props_container)

        self.rows = []

        # ============================================================
        #   Загружаем XML строки фразы
        # ============================================================
        xml_rows = self.load_phrase_xml()

        if xml_rows:
            for tag, value in xml_rows:
                gui_name = next((k for k, v in self.tag_map.items() if v == tag), "Precondition")
                self.add_row(gui_name, tag, value)

        # ============================================================
        #   ПЛЮСИК
        # ============================================================
        plus_row = QHBoxLayout()
        plus_row.addStretch()

        self.btn_plus = ClickableSquare("+",
            """
            QLabel {
                color: white;
                background-color: #009900;
                font-size: 18px;
                font-weight: bold;
                border: 1px solid #006600;
                min-width: 24px;
                min-height: 24px;
                max-width: 24px;
                max-height: 24px;
                qproperty-alignment: AlignCenter;
            }
            """,
            """
            QLabel {
                color: white;
                background-color: #007700;
                font-size: 18px;
                font-weight: bold;
                border: 1px solid #005500;
                min-width: 24px;
                min-height: 24px;
                max-width: 24px;
                max-height: 24px;
                qproperty-alignment: AlignCenter;
            }
            """
        )
        self.btn_plus.clicked = self.add_empty_row
        plus_row.addWidget(self.btn_plus)

        self.props_container.addLayout(plus_row)

        # ============================================================
        #   Растягивающий элемент — как в DialogProperties
        # ============================================================
        main_layout.addStretch()

        # ============================================================
        #   НИЖНЯЯ ПАНЕЛЬ — прибита к низу
        # ============================================================
        btn_layout = QHBoxLayout()
        main_layout.addLayout(btn_layout)

        btn_save = QPushButton("Сохранить")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                font-weight: bold;
                padding: 6px 14px;
                border: 1px solid #3e8e41;
            }
            QPushButton:hover {
                background-color: #5ecf60;
            }
        """)
        btn_save.clicked.connect(lambda: None)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)

        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.close)
        btn_layout.addWidget(btn_cancel)

    # ============================================================
    #   Загрузка XML фразы
    # ============================================================
    def load_phrase_xml(self):
        mw = self.parent()
        while mw is not None and not hasattr(mw, "res_loader"):
            mw = mw.parent()

        if mw is None:
            return []

        loader = mw.res_loader

        raw_id = str(self.node.dialog_id)
        dialog_id = raw_id.split(":")[0]
        phrase_id = str(self.node.logic_id)

        if dialog_id not in loader.dialogs:
            return []

        dialog_node = loader.dialogs[dialog_id]["xml_node"]

        phrase_list = dialog_node.find("phrase_list")
        if phrase_list is None:
            return []

        phrases = phrase_list.findall("phrase")

        phrase_node = next((p for p in phrases if p.get("id") == phrase_id), None)
        if phrase_node is None:
            return []

        results = []
        for child in phrase_node:
            tag = child.tag
            if tag not in self.tag_map.values():
                continue
            value = (child.text or "").strip()
            results.append((tag, value))

        return results

    # ============================================================
    #   Создание строки
    # ============================================================
    def add_row(self, gui_name="Precondition", xml_tag="precondition", param_value=""):
        row_container = QVBoxLayout()
        row = QHBoxLayout()

        combo = QComboBox()
        combo.setFixedWidth(self.tag_column_width)
        combo.setStyleSheet("""
            QComboBox {
                color: white;
                background-color: #303030;
                border: 1px solid #505050;
                padding-left: 6px;
            }
        """)

        for name in self.tag_map.keys():
            combo.addItem(name)

        combo.setCurrentText(gui_name)
        combo.row_xml_tag = xml_tag
        combo.row_gui_tag = gui_name

        row.addWidget(combo)

        vline = QFrame()
        vline.setFrameShape(QFrame.Shape.VLine)
        vline.setStyleSheet("color: #444;")
        row.addWidget(vline)

        edit = QLabel(param_value if param_value else "...")
        edit.setStyleSheet("color: #ccc; padding-left: 10px;")
        row.addWidget(edit, 1)

        btn_del = ClickableSquare("−",
            """
            QLabel {
                color: white;
                background-color: #b00000;
                font-size: 18px;
                font-weight: bold;
                border: 1px solid #700000;
                min-width: 24px;
                min-height: 24px;
                max-width: 24px;
                max-height: 24px;
                qproperty-alignment: AlignCenter;
            }
            """,
            """
            QLabel {
                color: white;
                background-color: #8a0000;
                font-size: 18px;
                font-weight: bold;
                border: 1px solid #500000;
                min-width: 24px;
                min-height: 24px;
                max-width: 24px;
                max-height: 24px;
                qproperty-alignment: AlignCenter;
            }
            """
        )
        btn_del.clicked = lambda rc=row_container: self.delete_row(rc)
        row.addWidget(btn_del)

        row_container.addLayout(row)
        row_container.addWidget(make_line())

        self.rows.append(row_container)
        self.props_container.insertLayout(len(self.rows) - 1, row_container)

    def add_empty_row(self):
        self.add_row()

    def delete_row(self, row_container):
        if row_container in self.rows:
            self.rows.remove(row_container)

            while row_container.count():
                item = row_container.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self._delete_layout(item.layout())

            self._delete_layout(row_container)

    def _delete_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._delete_layout(item.layout())
