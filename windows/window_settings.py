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


REQUIRED_PATHS = [
    "gamedata",
    "configs",
    "configs/gameplay",
    "configs/creatures",
    "spawns",
    "scripts"
]


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

        # авто‑сканирование дефолтных подпапок
        self.auto_scan_gamedata()

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
    # Авто‑сканирование дефолтных подпапок внутри gamedata
    # ---------------------------------------------------------
    def auto_scan_gamedata(self):
        gamedata = self.paths.get("gamedata")
        if not gamedata or not os.path.exists(gamedata):
            return

        defaults = {
            "configs": os.path.join(gamedata, "configs"),
            "configs/gameplay": os.path.join(gamedata, "configs", "gameplay"),
            "configs/creatures": os.path.join(gamedata, "configs", "creatures"),
            "configs/text": os.path.join(gamedata, "configs", "text"),
            "spawns": os.path.join(gamedata, "spawns"),
            "scripts": os.path.join(gamedata, "scripts"),
        }

        changed = False

        for key, default_path in defaults.items():
            if os.path.exists(default_path):
                self.paths[key] = normalize(default_path)
                changed = True

        if changed:
            self.settings["paths"] = self.paths
            save_settings(self.settings)

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
            ("configs", normalize(self.paths.get("configs", ""))),
            ("configs/gameplay", normalize(self.paths.get("configs/gameplay", ""))),
            ("configs/creatures", normalize(self.paths.get("configs/creatures", ""))),
            ("configs/text", normalize(self.paths.get("configs/text", ""))),
            ("spawns", normalize(self.paths.get("spawns", ""))),
            ("scripts", normalize(self.paths.get("scripts", ""))),   # ← ДОБАВЛЕНО
        ]


        self.indicators = []
        self.indicator_names = []

        for name, path in items:
            self._add_path_row(name, path)

        self.btn_save = QPushButton("Сохранить")
        self.btn_save.clicked.connect(self.save_all)
        self.content_layout.addWidget(self.btn_save)

        self.content_layout.addStretch()

        self.update_save_button_state()

    # ---------------------------------------------------------
    # Категория "Шрифт"
    # ---------------------------------------------------------
    def show_category_font(self):
        title = QLabel("Настройки шрифта")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.content_layout.addWidget(title)

        row_font = QHBoxLayout()
        lbl_font = QLabel("Семейство шрифта:")
        row_font.addWidget(lbl_font)

        self.font_combo = QFontComboBox()
        self.font_combo.setFontFilters(
            QFontComboBox.FontFilter.ScalableFonts
        )
        self.font_combo.setCurrentFont(QFont(self.font_settings["family"]))
        row_font.addWidget(self.font_combo)

        self.content_layout.addLayout(row_font)

        row_size = QHBoxLayout()
        lbl_size = QLabel("Размер шрифта:")
        row_size.addWidget(lbl_size)

        # 🔥 фикс кликабельности кнопки "увеличить"
        QApplication.setStyle("Fusion")

        self.size_spin = QSpinBox()
        self.size_spin.setRange(6, 40)
        self.size_spin.setValue(self.font_settings["size"])
        row_size.addWidget(self.size_spin)
        self.size_spin.setStyleSheet("""
            QSpinBox {
                min-height: 32px;
                height: 32px;
                font-size: 16px;
            }
            QSpinBox::up-button {
                width: 24px;
                height: 16px;
            }
            QSpinBox::down-button {
                width: 24px;
                height: 16px;
            }
            QSpinBox::up-arrow {
                width: 12px;
                height: 12px;
            }
            QSpinBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)

        self.content_layout.addLayout(row_size)

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

        exists = path and os.path.exists(path)

        if exists:
            icon.setText("✓")
            icon.setStyleSheet("color: green; font-weight: bold;")
        else:
            icon.setText("✗")
            icon.setStyleSheet("color: red; font-weight: bold;")

        self.indicators.append(icon)
        self.indicator_names.append(name)
        row.addWidget(icon)

        lbl_name = QLabel(name)
        lbl_name.setFixedWidth(150)
        row.addWidget(lbl_name)

        lbl_path = QLabel(path if path else "—")
        lbl_path.setStyleSheet("color: #bbb;")
        row.addWidget(lbl_path)

        btn = QPushButton("Выбрать…")

        # gamedata — всегда выбираем вручную
        if name == "gamedata":
            btn.clicked.connect(lambda _, n=name, l=lbl_path: self.select_path(n, l))

        # configs — НИКОГДА не выбираем вручную
        elif name == "configs":
            btn.setEnabled(False)

        # остальные — выбираем только если отсутствуют
        else:
            if exists:
                btn.setEnabled(False)
            else:
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

            if name == "gamedata":
                self.auto_scan_gamedata()

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
        has_errors = False

        for name, icon in zip(self.indicator_names, self.indicators):
            if name in REQUIRED_PATHS and icon.text() == "✗":
                has_errors = True
                break

        theme = self.settings.get("theme", "light")

        if has_errors:
            self.btn_save.setEnabled(False)

            if theme == "dark":
                self.btn_save.setStyleSheet("""
                    QPushButton {
                        background-color: #2e2e2e;
                        color: #777;
                        border: 1px solid #444;
                    }
                """)
            else:
                self.btn_save.setStyleSheet("""
                    QPushButton {
                        background-color: #e0e0e0;
                        color: #888;
                        border: 1px solid #ccc;
                    }
                """)
        else:
            self.btn_save.setEnabled(True)
            self.btn_save.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    border: 1px solid #3e8e41;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)

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
