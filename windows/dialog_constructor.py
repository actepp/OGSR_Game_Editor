from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QLineEdit, QSplitter, QMenu
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from windows.dialog_properties import DialogProperties


class DialogConstructor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.modified = False

        # -----------------------------------------------------
        # SPLITTER — левая панель + рабочая область
        # -----------------------------------------------------
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3a3a3a;
                width: 6px;
                margin: 0px;
                border: none;
            }
            QSplitter::handle:hover {
                background-color: #5a5a5a;
            }
        """)

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(splitter)

        # -----------------------------------------------------
        # ЛЕВАЯ ПАНЕЛЬ
        # -----------------------------------------------------
        left_container = QWidget()
        left_layout = QVBoxLayout()
        left_container.setLayout(left_layout)

        # Поле поиска
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Поиск диалога...")
        self.search_box.setClearButtonEnabled(True)
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

        # Контекстное меню
        self.dialog_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.dialog_list.customContextMenuRequested.connect(self.open_context_menu)

        left_layout.addWidget(self.dialog_list)
        splitter.addWidget(left_container)

        # -----------------------------------------------------
        # ПРАВАЯ ПАНЕЛЬ
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

        splitter.setSizes([300, 900])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # -----------------------------------------------------
        # ЗАГРУЗКА ДИАЛОГОВ
        # -----------------------------------------------------
        self.load_dialogs()

    # ---------------------------------------------------------
    # ЗАГРУЗКА СПИСКА ДИАЛОГОВ
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

    # ---------------------------------------------------------
    # КОНТЕКСТНОЕ МЕНЮ
    # ---------------------------------------------------------
    def open_context_menu(self, position):
        item = self.dialog_list.itemAt(position)
        if not item:
            return

        dialog_id = item.text()

        menu = QMenu(self)

        open_action = QAction("Открыть", self)
        props_action = QAction("Свойства", self)

        menu.addAction(open_action)
        menu.addAction(props_action)

        open_action.triggered.connect(lambda: self.open_dialog(dialog_id))
        props_action.triggered.connect(lambda: self.show_properties(dialog_id))

        menu.exec(self.dialog_list.mapToGlobal(position))

    # ---------------------------------------------------------
    # ЗАГЛУШКИ
    # ---------------------------------------------------------
    def open_dialog(self, dialog_id):
        print(f"Открыть диалог: {dialog_id}")

    def show_properties(self, dialog_id):
        loader = self.parent().res_loader
        dialog_data = loader.get_dialog(dialog_id)

        dlg = DialogProperties(self, dialog_data)
        dlg.show()
