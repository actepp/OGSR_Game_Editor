from PyQt6.QtWidgets import QApplication

# -----------------------------
# ТЁМНАЯ ТЕМА
# -----------------------------
DARK_THEME = """
QWidget {
    background-color: #2b2b2b;
    color: #e6e6e6;
}

/* Верхнее меню */
QMenuBar {
    background-color: #3c3c3c;
    color: #ffffff;
    border-bottom: 1px solid #555;
}

QMenuBar::item {
    background-color: transparent;from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout

class PhraseProperties(QDialog):
    def __init__(self, parent, node):
        super().__init__(parent)
        self.node = node

        self.setWindowTitle(f"Фраза: {node.text_key}")
        self.resize(600, 400)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel(f"Ключ: {node.text_key}"))
        layout.addWidget(QLabel(f"Локаль: {node.locale.upper()}"))

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(node.logic_text_real)
        layout.addWidget(self.text_edit)

        btns = QHBoxLayout()
        layout.addLayout(btns)

        btn_save = QPushButton("Сохранить")
        btn_cancel = QPushButton("Отмена")

        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)

        btn_cancel.clicked.connect(self.close)
        btn_save.clicked.connect(self.save_phrase)

    def save_phrase(self):
        new_text = self.text_edit.toPlainText().strip()
        self.node.logic_text_real = new_text
        self.close()

    padding: 4px 10px;
}

QMenuBar::item:selected {
    background-color: #505050;
}

/* Выпадающие меню */
QMenu {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555;
}

QMenu::item:selected {
    background-color: #505050;
}

/* Кнопки */
QPushButton {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555;
    padding: 5px;
}

QPushButton:hover {
    background-color: #505050;
}

/* Поля ввода */
QLineEdit, QListWidget, QSpinBox, QFontComboBox {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555;
}
"""


# -----------------------------
# СВЕТЛАЯ ТЕМА
# -----------------------------
LIGHT_THEME = """
QWidget {
    background-color: #ffffff;
    color: #202020;
}

/* Верхнее меню */
QMenuBar {
    background-color: #e0e0e0;
    color: #202020;
    border-bottom: 1px solid #b0b0b0;
}

QMenuBar::item {
    background-color: transparent;
    padding: 4px 10px;
}

QMenuBar::item:selected {
    background-color: #d0d0d0;
}

/* Выпадающие меню */
QMenu {
    background-color: #ffffff;
    color: #202020;
    border: 1px solid #b0b0b0;
}

QMenu::item:selected {
    background-color: #e0e0e0;
}

/* Кнопки */
QPushButton {
    background-color: #e0e0e0;
    color: #202020;
    border: 1px solid #aaa;
    padding: 5px;
}

QPushButton:hover {
    background-color: #d0d0d0;
}

/* Поля ввода */
QLineEdit, QListWidget, QSpinBox, QFontComboBox {
    background-color: #ffffff;
    color: #202020;
    border: 1px solid #aaa;
}
"""


# -----------------------------
# ПРИМЕНЕНИЕ ТЕМЫ
# -----------------------------
def apply_theme(theme_name: str):
    app = QApplication.instance()
    if theme_name == "dark":
        app.setStyleSheet(DARK_THEME)
    else:
        app.setStyleSheet(LIGHT_THEME)
