from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QWidget, QFileDialog
)
from PyQt6.QtCore import Qt
import os

from settings_manager import load_settings, save_settings


# ---------------------------------------------------------
# Нормализация путей (всегда прямые слэши)
# ---------------------------------------------------------
def normalize(path: str) -> str:
    return path.replace("\\", "/")


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # окно должно сворачиваться вместе с родителем
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

        # --- Основной layout ---
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # --- Левая колонка ---
        self.category_list = QListWidget()
        self.category_list.addItem("Папки")
        self.category_list.setFixedWidth(150)
        main_layout.addWidget(self.category_list)

        # --- Правая колонка ---
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_widget.setLayout(self.content_layout)
        main_layout.addWidget(self.content_widget)

        # Загружаем первую категорию
        self.show_category_paths()

        # Подключаем сигнал после загрузки
        self.category_list.currentRowChanged.connect(self.change_category)

    # ---------------------------------------------------------
    # Переключение категорий
    # ---------------------------------------------------------
    def change_category(self, index):
        self.clear_layout(self.content_layout)

        if index == 0:
            self.show_category_paths()

    # ---------------------------------------------------------
    # Категория "Папки"
    # ---------------------------------------------------------
    def show_category_paths(self):
        title = QLabel("Пути OGSR")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.content_layout.addWidget(title)

        items = [
            ("gamedata", normalize(self.paths.get("gamedata", ""))),
            ("configs/gameplay", normalize(self._sub("configs/gameplay"))),
            ("configs/creatures", normalize(self._sub("configs/creatures"))),
            ("configs/text", normalize(self._sub("configs/text"))),
            ("spawns", normalize(self._sub("spawns"))),
        ]

        for name, path in items:
            self._add_path_row(name, path)

        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self.save_all)
        self.content_layout.addWidget(btn_save)

    # ---------------------------------------------------------
    # Вспомогательная функция: получить путь к подпапке
    # ---------------------------------------------------------
    def _sub(self, subpath):
        gamedata = self.paths.get("gamedata", "")
        if not gamedata:
            return ""
        return normalize(os.path.join(gamedata, subpath))

    # ---------------------------------------------------------
    # Создание строки пути
    # ---------------------------------------------------------
    def _add_path_row(self, name, path):
        row = QHBoxLayout()

        # индикатор ✓ / ✗
        icon = QLabel()
        icon.setFixedWidth(20)
        if path and os.path.exists(path):
            icon.setText("✓")
            icon.setStyleSheet("color: green; font-weight: bold;")
        else:
            icon.setText("✗")
            icon.setStyleSheet("color: red; font-weight: bold;")

        row.addWidget(icon)

        # название
        lbl_name = QLabel(name)
        lbl_name.setFixedWidth(150)
        row.addWidget(lbl_name)

        # путь
        lbl_path = QLabel(path if path else "—")
        lbl_path.setStyleSheet("color: #bbb;")
        row.addWidget(lbl_path)

        # кнопка выбора
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

            if name == "gamedata":
                self.paths["gamedata"] = norm

            # перерисовать категорию
            self.change_category(0)

    # ---------------------------------------------------------
    # Сохранение настроек
    # ---------------------------------------------------------
    def save_all(self):
        self.settings["paths"] = self.paths
        save_settings(self.settings)
        self.close()

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
