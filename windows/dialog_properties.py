from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt


def make_line():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    line.setStyleSheet("color: #444;")
    return line


class DialogProperties(QDialog):
    def __init__(self, parent, dialog_data):
        super().__init__(parent)

        self.dialog_data = dialog_data
        dialog_id = dialog_data["id"]

        # Заголовок окна
        self.setWindowTitle(f"Свойства {dialog_id}")
        self.resize(550, 400)
        self.setWindowModality(Qt.WindowModality.WindowModal)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # ------------------------------
        # ТАБЛИЦА СВОЙСТВ
        # ------------------------------
        grid = QGridLayout()
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 3)
        main_layout.addLayout(grid)

        row = 0

        # XML путь
        xml_path = dialog_data["xml_path"].replace("\\", "/")
        grid.addWidget(QLabel("Путь:"), row, 0)
        grid.addWidget(QLabel(xml_path), row, 1)
        row += 1
        grid.addWidget(make_line(), row, 0, 1, 2)
        row += 1

        # Priority
        grid.addWidget(QLabel("Приоритет:"), row, 0)
        grid.addWidget(QLabel(str(dialog_data["priority"])), row, 1)
        row += 1
        grid.addWidget(make_line(), row, 0, 1, 2)
        row += 1

        # PRECONDITIONS
        if dialog_data["preconditions"]:
            grid.addWidget(QLabel("Preconditions:"), row, 0)
            grid.addWidget(QLabel(", ".join(dialog_data["preconditions"])), row, 1)
            row += 1
            grid.addWidget(make_line(), row, 0, 1, 2)
            row += 1

        # HAS_INFO
        if dialog_data["has_info"]:
            grid.addWidget(QLabel("Has Info:"), row, 0)
            grid.addWidget(QLabel(", ".join(dialog_data["has_info"])), row, 1)
            row += 1
            grid.addWidget(make_line(), row, 0, 1, 2)
            row += 1

        # DONT_HAS_INFO
        if dialog_data["dont_has_info"]:
            grid.addWidget(QLabel("Dont Has Info:"), row, 0)
            grid.addWidget(QLabel(", ".join(dialog_data["dont_has_info"])), row, 1)
            row += 1
            grid.addWidget(make_line(), row, 0, 1, 2)
            row += 1

        main_layout.addStretch()

        # Кнопка закрытия
        btn_layout = QHBoxLayout()
        main_layout.addLayout(btn_layout)

        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)

    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_screen()

    def center_on_screen(self):
        screen = self.screen().geometry()
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + (screen.height() - self.height()) // 2
        self.move(x, y)
