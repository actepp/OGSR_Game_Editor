from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QComboBox
)
from PyQt6.QtCore import Qt


class PhraseProperties(QDialog):
    def __init__(self, parent, node):
        super().__init__(parent)
        self.node = node

        # GUI → XML
        self.tag_map = {
            "Give info": "give_info",
            "Disable info": "disable_info",
            "Action": "action",
            "Precondition": "precondition"
        }

        # ширина колонки тегов
        fm = self.fontMetrics()
        self.tag_column_width = max(
            fm.horizontalAdvance(name) for name in self.tag_map.keys()
        ) + 45

        # окно
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle("Свойства фразы")
        self.resize(500, 300)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # --- ШАПКА ---
        title = QLabel(f"{node.text_key}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # линия
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: rgb(120, 120, 120);")
        layout.addWidget(line)

        # контейнер свойств
        self.props_layout = QVBoxLayout()
        layout.addLayout(self.props_layout)

        # --- СТРОКИ ---
        for gui_name, xml_tag in self.tag_map.items():
            row_container = QVBoxLayout()
            row = QHBoxLayout()

            # TAG = ComboBox (стрелка работает, потому что мы НЕ трогаем down-arrow)
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

            # вертикальная линия
            vline = QLabel()
            vline.setFixedWidth(1)
            vline.setStyleSheet("background-color: rgb(80, 80, 80);")
            row.addWidget(vline)

            # PARAMETER
            edit = QLabel("...")
            edit.setStyleSheet("color: #ccc; padding-left: 10px;")
            row.addWidget(edit, 1)

            # DELETE BUTTON — красный квадрат с белым минусом
            btn_del = QLabel("−")
            btn_del.setStyleSheet("""
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
            """)
            row.addWidget(btn_del)

            # строка
            row_container.addLayout(row)

            # горизонтальная линия
            hline = QLabel()
            hline.setFixedHeight(1)
            hline.setStyleSheet("background-color: rgb(120, 120, 120);")
            row_container.addWidget(hline)

            self.props_layout.addLayout(row_container)

        # --- ПЛЮСИК — зелёный квадрат с белым плюсом ---
        plus_row = QHBoxLayout()
        plus_row.addStretch()

        btn_plus = QLabel("+")
        btn_plus.setStyleSheet("""
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
        """)
        plus_row.addWidget(btn_plus)

        self.props_layout.addLayout(plus_row)

        # --- НИЖНЯЯ ПАНЕЛЬ ---
        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)

        btn_layout.addStretch()

        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)
