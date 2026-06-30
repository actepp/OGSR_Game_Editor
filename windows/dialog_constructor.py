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

        splitter = QSplitter(Qt.Orientation.Horizontal)

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(splitter)

        left_container = QWidget()
        left_layout = QVBoxLayout()
        left_container.setLayout(left_layout)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Поиск диалога...")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.textChanged.connect(self.update_filter)
        left_layout.addWidget(self.search_box)

        self.dialog_list = QListWidget()
        self.dialog_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.dialog_list.customContextMenuRequested.connect(self.open_context_menu)

        left_layout.addWidget(self.dialog_list)
        splitter.addWidget(left_container)

        right_container = QWidget()
        right_layout = QVBoxLayout()
        right_container.setLayout(right_layout)

        placeholder = QLabel("Рабочая область конструктора диалогов")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(placeholder)
        right_layout.addStretch()

        splitter.addWidget(right_container)

        splitter.setSizes([300, 900])

        self.load_dialogs()

    def load_dialogs(self):
        loader = self.parent().res_loader
        dialog_ids = loader.get_dialog_list()
        dialog_ids.sort()

        self.all_dialogs = dialog_ids

        self.dialog_list.clear()
        for d in dialog_ids:
            self.dialog_list.addItem(d)

    def update_filter(self, text):
        text = text.lower()
        self.dialog_list.clear()

        for d in self.all_dialogs:
            if text in d.lower():
                self.dialog_list.addItem(d)

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

        props_action.triggered.connect(lambda: self.show_properties(dialog_id))

        menu.exec(self.dialog_list.mapToGlobal(position))

    def show_properties(self, dialog_id):
        loader = self.parent().res_loader
        dialog_data = loader.get_dialog(dialog_id)

        dlg = DialogProperties(self, dialog_data)
        dlg.show()

    def save_current_dialog(self):
        """Сохраняет текущий выбранный диалог"""
        item = self.dialog_list.currentItem()
        if not item:
            return

        dialog_id = item.text()
        loader = self.parent().res_loader
        data = loader.get_dialog(dialog_id)
        loader.save_dialog(dialog_id, data)
