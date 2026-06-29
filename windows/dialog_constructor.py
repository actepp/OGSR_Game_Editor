from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget
)
from PyQt6.QtCore import Qt


class DialogConstructor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Флаг изменений
        self.modified = False

        # Основной горизонтальный layout — слева навигация, справа рабочая область
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # -----------------------------
        # Левая панель — список диалогов
        # -----------------------------
        self.dialog_list = QListWidget()
        self.dialog_list.setFixedWidth(250)
        self.dialog_list.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                color: #ddd;
                font-size: 14px;
                padding: 5px;
            }
        """)

        # Пока пусто — позже загрузим реальные диалоги
        # self.dialog_list.addItem("dialog_01")
        # self.dialog_list.addItem("dialog_02")

        main_layout.addWidget(self.dialog_list)

        # -----------------------------
        # Правая рабочая область (пока пустая)
        # -----------------------------
        self.workspace = QWidget()
        workspace_layout = QVBoxLayout()
        self.workspace.setLayout(workspace_layout)

        placeholder = QLabel("Рабочая область конструктора диалогов")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #666; font-size: 18px;")

        workspace_layout.addWidget(placeholder)
        workspace_layout.addStretch()

        main_layout.addWidget(self.workspace)
