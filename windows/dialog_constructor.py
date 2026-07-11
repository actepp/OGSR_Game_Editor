from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QLineEdit, QSplitter, QMenu, QApplication
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

        # Левая часть: поиск + список диалогов
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

        # перехватываем клавиши для копирования
        self.dialog_list.keyPressEvent = self._list_key_press

        left_layout.addWidget(self.dialog_list)
        splitter.addWidget(left_container)

        # Правая часть: рабочая область (пока заглушка)
        right_container = QWidget()
        right_layout = QVBoxLayout()
        right_container.setLayout(right_layout)

        placeholder = QLabel("Рабочая область конструктора диалогов")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(placeholder)
        right_layout.addStretch()

        splitter.addWidget(right_container)

        splitter.setSizes([300, 900])

        self.all_dialogs: list[str] = []
        self.load_dialogs()

    def load_dialogs(self):
        """Загружает список диалогов из ResourceLoader и заполняет QListWidget."""
        loader = self.parent().res_loader
        dialog_ids = loader.get_dialog_list()
        dialog_ids.sort()

        self.all_dialogs = dialog_ids

        self.dialog_list.clear()
        for d in dialog_ids:
            self.dialog_list.addItem(d)

    def update_filter(self, text: str):
        """Фильтрация списка диалогов по подстроке."""
        text = text.lower()
        self.dialog_list.clear()

        for d in self.all_dialogs:
            if text in d.lower():
                self.dialog_list.addItem(d)

    def open_context_menu(self, position):
        """Контекстное меню по правому клику на диалоге."""
        item = self.dialog_list.itemAt(position)
        if not item:
            return

        dialog_id = item.text()

        menu = QMenu(self)
        open_action = QAction("Открыть", self)
        props_action = QAction("Свойства", self)

        menu.addAction(open_action)
        menu.addAction(props_action)
        menu.addSeparator()

        props_action.triggered.connect(lambda: self.show_properties(dialog_id))

        menu.exec(self.dialog_list.mapToGlobal(position))

    def show_properties(self, dialog_id: str):
        """Открывает окно свойств диалога."""
        loader = self.parent().res_loader
        dialog_data = loader.get_dialog(dialog_id)

        dlg = DialogProperties(self, dialog_data)
        dlg.show()

    def save_current_dialog(self):
        """Сохраняет текущий выбранный диалог."""
        item = self.dialog_list.currentItem()
        if not item:
            return

        dialog_id = item.text()
        loader = self.parent().res_loader
        data = loader.get_dialog(dialog_id)
        loader.save_dialog(dialog_id, data)

    def _list_key_press(self, event):
        """Обработка клавиш в списке диалогов (копирование Ctrl+C)."""
        if event.key() == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            item = self.dialog_list.currentItem()
            if item:
                QApplication.clipboard().setText(item.text())
        else:
            # пробрасываем стандартное поведение
            QListWidget.keyPressEvent(self.dialog_list, event)

    def refresh_dialog(self, dialog_id):
        """
        После сохранения диалога нужно просто перерисовать список.
        Данные берутся из ResourceLoader при открытии свойств.
        """
        self.load_dialogs()   # перечитать список ID из loader
        self.update_filter(self.search_box.text())  # сохранить фильтр

        print(f"[OK] refresh_dialog: диалог {dialog_id} обновлён в UI.")
