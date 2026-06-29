from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QWidget, QFileDialog, QFontComboBox, QSpinBox, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import os

from settings_manager import load_settings, save_settings


def normalize(path: str) -> str:
    return path.replace("\\", "/")


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self.setWindowTitle("Настройки")
        self.resize(700, 450)
        self.setModal(False)

        self.settings = load_settings()
        self.paths = self.settings.get("paths", {})
        self.font_settings = self.settings.get("font", {
            "family": "Segoe UI",
            "size": 10
        })

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # --- Левая колонка ---
        self.category_list = QListWidget()
        self.category_list.addItem("Папки")
        self.category_list.addItem("Шрифт")
        self.category_list.setFixedWidth(150)
        main_layout.addWidget(self.category_list)

        # --- Правая колонка ---
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_widget.setLayout(self.content_layout)
        main_layout.addWidget(self.content_widget)

        self.update_category_styles()

        self.show_category_paths()

        self.category_list.currentRowChanged.connect(self.change_category)

    # ---------------------------------------------------------
    # Жирность активного пункта
    # ---------------------------------------------------------
    def update_category_styles(self):
        for i in range(self.category_list.count()):
            item = self.category_list.item(i)
            f = item.font()
            f.setBold(i == self.category_list.currentRow())
            item.setFont(f)

    # ---------------------------------------------------------
    # Переключение категорий
    # ---------------------------------------------------------
    def change_category(self, index):
        self.clear_layout(self.content_layout)
        self.update_category_styles()

        if index == 0:
            self.show_category_paths()
        elif index == 1:
            self.show_category_font()

    # ---------------------------------------------------------
    # Категория "Папки"
    # ---------------------------------------------------------
    def show_category_paths(self):
        title = QLabel("Пути OGSR")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.content_layout.addWidget(title)

        items = [
            ("gamedata", normalize(self.paths.get("gamedata", ""))),
            ("configs/gameplay", normalize(self.paths.get("configs/gameplay", ""))),
            ("configs/creatures", normalize(self.paths.get("configs/creatures", ""))),
            ("configs/text", normalize(self.paths.get("configs/text", ""))),
            ("spawns", normalize(self.paths.get("spawns", ""))),
        ]

        self.indicators = []

        for name, path in items:
            self._add_path_row(name, path)

        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self.save_all)
        self.btn_save = btn_save
        self.content_layout.addWidget(btn_save)

        self.content_layout.addStretch()
        self.update_save_button_state()

    # ---------------------------------------------------------
    # Категория "Шрифт"
    # ---------------------------------------------------------
    def show_category_font(self):
        title = QLabel("Настройки шрифта")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.content_layout.addWidget(title)

        # Выбор семейства шрифта
        row_font = QHBoxLayout()
        lbl_font = QLabel("Семейство шрифта:")
        row_font.addWidget(lbl_font)

        self.font_combo = QFontComboBox()

        # Фильтруем только нормальные шрифты (TTF/OTF)
        self.font_combo.setFontFilters(
            QFontComboBox.FontFilter.ScalableFonts
        )

        self.font_combo.setCurrentFont(QFont(self.font_settings["family"]))
        row_font.addWidget(self.font_combo)

        self.content_layout.addLayout(row_font)

        # Выбор размера шрифта
        row_size = QHBoxLayout()
        lbl_size = QLabel("Размер шрифта:")
        row_size.addWidget(lbl_size)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(6, 40)
        self.size_spin.setValue(self.font_settings["size"])
        row_size.addWidget(self.size_spin)

        self.content_layout.addLayout(row_size)

        # Кнопка сохранения
        btn_save = QPushButton("Применить шрифт")
        btn_save.clicked.connect(self.save_font)
        self.content_layout.addWidget(btn_save)

        self.content_layout.addStretch()

    # ---------------------------------------------------------
    # Сохранение шрифта
    # ---------------------------------------------------------
    def save_font(self):
        family = self.font_combo.currentFont().family()
        size = self.size_spin.value()

        self.font_settings["family"] = family
        self.font_settings["size"] = size

        self.settings["font"] = self.font_settings
        save_settings(self.settings)

        # Применяем глобально
        font = QFont(family, size)
        app = QApplication.instance()
        app.setFont(font)

        self.close()


    # ---------------------------------------------------------
    # Создание строки пути
    # ---------------------------------------------------------
    def _add_path_row(self, name, path):
        row = QHBoxLayout()

        icon = QLabel()
        icon.setFixedWidth(20)

        if path and os.path.exists(path):
            icon.setText("✓")
            icon.setStyleSheet("color: green; font-weight: bold;")
        else:
            icon.setText("✗")
            icon.setStyleSheet("color: red; font-weight: bold;")

        self.indicators.append(icon)
        row.addWidget(icon)

        lbl_name = QLabel(name)
        lbl_name.setFixedWidth(150)
        row.addWidget(lbl_name)

        lbl_path = QLabel(path if path else "—")
        lbl_path.setStyleSheet("color: #bbb;")
        row.addWidget(lbl_path)

        btn = QPushButton("Выбрать…")
        btn.clicked.connect(lambda _, n=name, l=lbl_path: self.select_path(n, l))
        row.addWidget(btn)

        self.content_layout.addLayout(row)

    # ---------------------------------------------------------
    # Выбор пути
    # ---------------------------------------------------------
    def select_path(self, name, label_widget):
        path = QFileDialog.getExistingDirectory(self, f"Выбор папки для {name}")
        if path:
            norm = normalize(path)
            label_widget.setText(norm)
            self.paths[name] = norm
            self.change_category(0)

    # ---------------------------------------------------------
    # Сохранение путей
    # ---------------------------------------------------------
    def save_all(self):
        self.settings["paths"] = self.paths
        save_settings(self.settings)
        self.close()

    # ---------------------------------------------------------
    # Активация кнопки "Сохранить"
    # ---------------------------------------------------------
    def update_save_button_state(self):
        for icon in self.indicators:
            if icon.text() == "✗":
                self.btn_save.setEnabled(False)
                return
        self.btn_save.setEnabled(True)

    # ---------------------------------------------------------
    # Очистка layout
    # ---------------------------------------------------------
    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                sub = item.layout()
                if sub:
                    self.clear_layout(sub)

    # ---------------------------------------------------------
    # Центрирование окна
    # ---------------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        screen = self.screen().geometry()
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + (screen.height() - self.height()) // 2
        self.move(x, y)
