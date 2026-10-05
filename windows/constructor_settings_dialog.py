from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from font_manager import apply_app_font


class ConstructorSettingsDialog(QDialog):
    """
    Окно настроек конструктора диалогов.

    Пока содержит только заготовку: интерфейс будет реализован
    на следующих шагах (цвета, размеры нод, поведение сетки и т.д.).
    """

    def __init__(self, parent=None, constructor=None):
        super().__init__(parent)

        self.constructor = constructor

        self.setWindowTitle("Настройки конструктора")
        self.resize(500, 400)
        self.setModal(False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        title = QLabel("Настройки конструктора диалогов")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title)

        info = QLabel(
            "Здесь будут настройки:\n"
            "• цвета и размеры нод\n"
            "• поведение сетки и масштаб\n"
            "• горячие клавиши\n"
            "• и т.д."
        )
        info.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        info.setWordWrap(True)
        main_layout.addWidget(info)

        main_layout.addStretch()

        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.close)
        main_layout.addWidget(btn_close)

        apply_app_font()

    def refresh_theme(self):
        apply_app_font()