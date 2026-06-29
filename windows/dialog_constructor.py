from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QLineEdit, QSplitter
)
from PyQt6.QtCore import Qt


class DialogConstructor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.modified = False

        # -----------------------------------------------------
        # ОСНОВНОЙ SPLITTER — левая панель + рабочая область
        # -----------------------------------------------------
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3a3a3a;
                width: 6px;
                margin: 0px;
            }
            QSplitter::handle:hover {
                background-color: #5a5a5a;
            }
        """)

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(splitter)

        # -----------------------------------------------------
        # ЛЕВАЯ ПАНЕЛЬ (контейнер)
        # -----------------------------------------------------
        left_container = QWidget()
        left_layout = QVBoxLayout()
        left_container.setLayout(left_layout)

        # Поле поиска
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Поиск диалога...")
        self.search_box.textChanged.connect(self.update_filter)
        left_layout.addWidget(self.search_box)

        # Список диалогов
        self.dialog_list = QListWidget()
        self.dialog_list.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                color: #ddd;
                font-size: 14px;
                padding: 5px;
            }
            QScrollBar:vertical {
                background: #1e1e1e;
                width: 12px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #444;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)
        left_layout.addWidget(self.dialog_list)

        splitter.addWidget(left_container)

        # -----------------------------------------------------
        # ПРАВАЯ ПАНЕЛЬ — рабочая область
        # -----------------------------------------------------
        right_container = QWidget()
        right_layout = QVBoxLayout()
        right_container.setLayout(right_layout)

        placeholder = QLabel("Рабочая область конструктора диалогов")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #666; font-size: 18px;")

        right_layout.addWidget(placeholder)
        right_layout.addStretch()

        splitter.addWidget(right_container)

        # -----------------------------------------------------
        # Настройки splitter
        # -----------------------------------------------------
        splitter.setSizes([300, 900])  # стартовая ширина левой панели
        splitter.setStretchFactor(0, 0)  # левая панель фиксируется
        splitter.setStretchFactor(1, 1)  # правая растягивается

        # -----------------------------------------------------
        # ЗАГРУЗКА ДИАЛОГОВ
        # -----------------------------------------------------
        self.load_dialogs()

    # ---------------------------------------------------------
    # ЗАГРУЗКА СПИСКА ДИАЛОГОВ ИЗ res_loader
    # ---------------------------------------------------------
    def load_dialogs(self):
        loader = self.parent().res_loader
        dialog_ids = loader.get_dialog_list()

        dialog_ids.sort()

        self.all_dialogs = dialog_ids

        self.dialog_list.clear()
        for d in dialog_ids:
            self.dialog_list.addItem(d)

    # ---------------------------------------------------------
    # ФИЛЬТР ПОИСКА
    # ---------------------------------------------------------
    def update_filter(self, text):
        text = text.lower()
        self.dialog_list.clear()

        for d in self.all_dialogs:
            if text in d.lower():
                self.dialog_list.addItem(d)
