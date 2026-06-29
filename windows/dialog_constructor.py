from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QWidget
)
from PyQt6.QtCore import Qt


class DialogConstructor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Конструктор диалогов")
        self.resize(800, 600)
        self.setModal(False)

        # Основной layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Заголовок
        title = QLabel("Конструктор диалогов")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        main_layout.addWidget(title)

        # Заглушка — позже добавим дерево диалогов, редактор узлов и т.д.
        placeholder = QLabel("Здесь будет интерфейс конструктора диалогов")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #888; font-size: 16px;")
        main_layout.addWidget(placeholder)

        # Нижняя панель кнопок
        btn_layout = QHBoxLayout()
        main_layout.addLayout(btn_layout)

        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)

        # Растяжка
        main_layout.addStretch()

    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_screen()

    def center_on_screen(self):
        screen = self.screen().geometry()
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + (screen.height() - self.height()) // 2
        self.move(x, y)
