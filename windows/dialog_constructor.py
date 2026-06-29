from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt


class DialogConstructor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.modified = False

        title = QLabel("Конструктор диалогов")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        placeholder = QLabel("Здесь будет интерфейс конструктора диалогов")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #888; font-size: 16px;")
        layout.addWidget(placeholder)

        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)

        layout.addStretch()

    def close_constructor(self):
        # закрываем себя, возвращая пустой центральный виджет
        if self.parent():
            self.parent().setCentralWidget(QWidget())
