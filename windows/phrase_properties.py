from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

class PhraseProperties(QDialog):
    def __init__(self, parent, node):
        super().__init__(parent)
        self.node = node

        # глобальная таблица тегов GUI → XML
        self.tag_map = {
            "Give info": "give_info",
            "Disable info": "disable_info",
            "Action": "action",
            "Precondition": "precondition"
        }

        # окно поверх всех
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle("Свойства фразы")
        self.resize(500, 300)

        # основной layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # --- ШАПКА ---
        title = QLabel(f"{node.text_key}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # --- ГОРИЗОНТАЛЬНАЯ ЛИНИЯ ---
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: rgb(120, 120, 120);")
        layout.addWidget(line)

        # --- КОНТЕЙНЕР ДЛЯ СВОЙСТВ ---
        self.props_layout = QVBoxLayout()
        layout.addLayout(self.props_layout)

        # тестовые строки (позже заменим на реальные данные)
        for gui_name, xml_tag in self.tag_map.items():
            row = QHBoxLayout()

            lbl = QLabel(gui_name)
            lbl.setStyleSheet("color: white; font-size: 14px;")
            row.addWidget(lbl)

            edit = QLabel("...")  # позже заменим на QLineEdit
            edit.setStyleSheet("color: #ccc; padding-left: 10px;")
            row.addWidget(edit, 1)

            btn_del = QLabel("✖")
            btn_del.setStyleSheet("color: red; font-weight: bold; padding: 4px;")
            row.addWidget(btn_del)

            self.props_layout.addLayout(row)

        # --- ПЛЮСИК ---
        plus_row = QHBoxLayout()
        plus_row.addStretch()

        btn_plus = QLabel("➕")
        btn_plus.setStyleSheet("color: #4caf50; font-size: 18px; font-weight: bold; padding: 4px;")
        plus_row.addWidget(btn_plus)

        self.props_layout.addLayout(plus_row)

        # нижняя панель с кнопкой закрытия
        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)

        btn_layout.addStretch()

        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)
