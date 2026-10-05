from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QWidget, QFileDialog, QFontComboBox, QSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import os

from settings_manager import load_settings, save_settings
from font_manager import apply_app_font, get_font_settings
from windows.themes import (
    path_label_style, primary_button_style, disabled_save_button_style,
    success_text_style, error_text_style
)


def normalize(path: str) -> str:
    return path.replace("\\", "/")


REQUIRED_PATHS = [
    "gamedata",
    "configs",
    "configs/gameplay",
    "configs/creatures",
    "configs/text",
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
        self.font_settings = get_font_settings(self.settings)

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

        # Строим обе категории сразу
        self.paths_container = QWidget()
        self._build_paths_category(self.paths_container)

        self.font_container = QWidget()
        self._build_font_category(self.font_container)

        # По умолчанию показываем "Папки"
        self.content_layout.addWidget(self.paths_container)
        self.content_layout.addWidget(self.font_container)
        self.font_container.hide()

        self.update_category_styles()

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
        current = get_font_settings()

        for i in range(self.category_list.count()):
            item = self.category_list.item(i)
            # шрифт строим от применённого пользовательского, а не от item.font():
            # item.font() без явно заданного шрифта отдаёт шрифт стиля,
            # и он "запекается" в элементе списка навсегда
            f = QFont(current["family"], current["size"])
            f.setBold(i == self.category_list.currentRow())
            item.setFont(f)

    # ---------------------------------------------------------
    # Переключение категорий
    # ---------------------------------------------------------
    def change_category(self, index):
        self.update_category_styles()

        if index == 0:
            self.paths_container.show()
            self.font_container.hide()
        elif index == 1:
            self.paths_container.hide()
            self.font_container.show()
            self._refresh_font_ui()

    # ---------------------------------------------------------
    # Категория "Папки"
    # ---------------------------------------------------------
    def _build_paths_category(self, container):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        container.setLayout(layout)

        title = QLabel("Пути OGSR")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        items = [
            ("gamedata", normalize(self.paths.get("gamedata", ""))),
            ("configs", normalize(self.paths.get("configs", ""))),
            ("configs/gameplay", normalize(self.paths.get("configs/gameplay", ""))),
            ("configs/creatures", normalize(self.paths.get("configs/creatures", ""))),
            ("configs/text", normalize(self.paths.get("configs/text", ""))),
            ("spawns", normalize(self.paths.get("spawns", ""))),
            ("scripts", normalize(self.paths.get("scripts", ""))),
        ]

        self.indicators = []
        self.indicator_names = []

        for name, path in items:
            self._add_path_row(name, path, layout)

        self.btn_save = QPushButton("Сохранить")
        self.btn_save.clicked.connect(self.save_all)
        layout.addWidget(self.btn_save)

        layout.addStretch()

        self.update_save_button_state()

    def _add_path_row(self, name, path, parent_layout):
        row = QHBoxLayout()

        icon = QLabel()
        icon.setFixedWidth(20)

        exists = path and os.path.exists(path)

        if exists:
            icon.setText("✓")
            icon.setStyleSheet(f"color: {success_text_style()}; font-weight: bold;")
        else:
            icon.setText("✗")
            icon.setStyleSheet(f"color: {error_text_style()}; font-weight: bold;")

        self.indicators.append(icon)
        self.indicator_names.append(name)
        row.addWidget(icon)

        lbl_name = QLabel(name)
        lbl_name.setFixedWidth(150)
        row.addWidget(lbl_name)

        lbl_path = QLabel(path if path else "—")
        lbl_path.setStyleSheet(path_label_style())
        row.addWidget(lbl_path)

        btn = QPushButton("Выбрать…")

        if name == "gamedata":
            btn.clicked.connect(lambda _, n=name, l=lbl_path: self.select_path(n, l))
        elif name == "configs":
            btn.setEnabled(False)
        else:
            if exists:
                btn.setEnabled(False)
            else:
                btn.clicked.connect(lambda _, n=name, l=lbl_path: self.select_path(n, l))

        row.addWidget(btn)
        parent_layout.addLayout(row)

    # ---------------------------------------------------------
    # Категория "Шрифт"
    # ---------------------------------------------------------
    def _build_font_category(self, container):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        container.setLayout(layout)

        title = QLabel("Настройки шрифта")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        row_font = QHBoxLayout()
        lbl_font = QLabel("Семейство шрифта:")
        row_font.addWidget(lbl_font)

        self.font_combo = QFontComboBox()
        self.font_combo.setFontFilters(
            QFontComboBox.FontFilter.ScalableFonts
        )
        self.font_combo.setCurrentFont(QFont(self.font_settings["family"]))
        row_font.addWidget(self.font_combo)

        layout.addLayout(row_font)

        row_size = QHBoxLayout()
        lbl_size = QLabel("Размер шрифта:")
        row_size.addWidget(lbl_size)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(6, 40)
        self.size_spin.setValue(self.font_settings["size"])
        self.size_spin.setFont(QFont(self.size_spin.font().family(), 14))
        row_size.addWidget(self.size_spin)

        layout.addLayout(row_size)

        btn_save = QPushButton("Применить шрифт")
        btn_save.clicked.connect(self.save_font)
        layout.addWidget(btn_save)

        layout.addStretch()

        self._font_ui_dirty = False
        self.font_combo.currentFontChanged.connect(self._mark_font_ui_dirty)
        self.size_spin.valueChanged.connect(self._mark_font_ui_dirty)

    def _mark_font_ui_dirty(self, *_):
        self._font_ui_dirty = True

    def _refresh_font_ui(self):
        if self._font_ui_dirty:
            # не затираем несохранённые правки пользователя
            return

        self.font_settings = get_font_settings(load_settings())

        for widget in (self.font_combo, self.size_spin):
            widget.blockSignals(True)
        try:
            self.font_combo.setCurrentFont(QFont(self.font_settings["family"]))
            self.size_spin.setValue(self.font_settings["size"])
        finally:
            for widget in (self.font_combo, self.size_spin):
                widget.blockSignals(False)

    # ---------------------------------------------------------
    # Сохранение шрифта
    # ---------------------------------------------------------
    def save_font(self):
        family = self.font_combo.currentFont().family()
        size = self.size_spin.value()

        self.font_settings["family"] = family
        self.font_settings["size"] = size

        self.settings["font"] = dict(self.font_settings)
        save_settings(self.settings)

        print(f"[FONT] save_font: family={family}, size={size}")

        apply_app_font(family, size)
        self.update_category_styles()

        main_window = self.find_main_window()
        if main_window is not None:
            # синхронизируем копию настроек главного окна, иначе она
            # перезапишет новый размер шрифта при следующем сохранении
            main_window.settings["font"] = dict(self.font_settings)

        self.close()

    # ---------------------------------------------------------
    # Реакция на смену темы (вызывается из MainWindow)
    # ---------------------------------------------------------
    def refresh_theme(self):
        apply_app_font()
        self.update_category_styles()

    # ---------------------------------------------------------
    #   Выбор пути
    # ---------------------------------------------------------
    def select_path(self, name, label_widget):
        path = QFileDialog.getExistingDirectory(self, f"Выбор папки для {name}")
        if path:
            norm = normalize(path)
            label_widget.setText(norm)
            self.paths[name] = norm

            if name == "gamedata":
                self.auto_scan_gamedata()

    # ---------------------------------------------------------
    #   Сохранение путей
    # ---------------------------------------------------------
    def save_all(self):
        self.settings["paths"] = self.paths
        save_settings(self.settings)

        # Сообщаем главному окну, что пути изменились, чтобы оно
        # сразу перечитало ресурсы — иначе диалоги появятся
        # только после перезапуска программы
        main_window = self.find_main_window()
        if main_window is not None:
            main_window.apply_paths(self.paths)

        self.close()

    def find_main_window(self):
        widget = self.parent()
        while widget is not None:
            if hasattr(widget, "apply_paths"):
                return widget
            widget = widget.parent()
        return None

    # ---------------------------------------------------------
    # Активация кнопки "Сохранить"
    # ---------------------------------------------------------
    def update_save_button_state(self):
        has_errors = False

        for name, icon in zip(self.indicator_names, self.indicators):
            if name in REQUIRED_PATHS and icon.text() == "✗":
                has_errors = True
                break

        if has_errors:
            self.btn_save.setEnabled(False)
            self.btn_save.setStyleSheet(disabled_save_button_style())
        else:
            self.btn_save.setEnabled(True)
            self.btn_save.setStyleSheet(primary_button_style())

    # ---------------------------------------------------------
    # Центрирование окна
    # ---------------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        screen = self.screen().geometry()
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + (screen.height() - self.height()) // 2
        self.move(x, y)
