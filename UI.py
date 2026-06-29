from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDialog,
    QVBoxLayout, QLabel, QPushButton,
    QWidget, QHBoxLayout, QMessageBox, QToolTip, QFileDialog,
    QMenuBar, QMenu
)
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtCore import Qt, QEvent
from windows.window_settings import SettingsDialog

import sys
import os

from settings_manager import (
    settings_exist, load_settings,
    save_settings, DEFAULT_SETTINGS
)


class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Первичная настройка OGSR Game Editor")
        self.setModal(True)
        self.resize(500, 300)

        self.current_step = 1
        self.selected_gamedata = None
        self.all_required_found = False

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.step_widget = QWidget()
        self.step_layout = QVBoxLayout()
        self.step_widget.setLayout(self.step_layout)

        self.layout.addWidget(self.step_widget)

        btn_layout = QHBoxLayout()
        self.btn_prev = QPushButton("Назад")
        self.btn_next = QPushButton("Далее")

        self.btn_prev.clicked.connect(self.prev_step)
        self.btn_next.clicked.connect(self.next_step)

        btn_layout.addWidget(self.btn_prev)
        btn_layout.addWidget(self.btn_next)

        self.layout.addLayout(btn_layout)

        self.update_step_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_screen()

    def center_on_screen(self):
        screen = self.screen().geometry()
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + (screen.height() - self.height()) // 2
        self.move(x, y)

    def update_step_ui(self):
        for i in reversed(range(self.step_layout.count())):
            widget = self.step_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if self.current_step == 1:
            self.show_step_1()
        elif self.current_step == 2:
            self.show_step_2()
        elif self.current_step == 3:
            self.show_step_3()
        elif self.current_step == 4:
            self.finish_setup()

        self.btn_prev.setEnabled(self.current_step > 1)

    def show_step_1(self):
        label = QLabel("ИЗМЕНИТЬ ОПИСАНИЕ\n\n"
                       "Здесь будет вводная информация о редакторе.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_layout.addWidget(label)
        self.btn_next.setEnabled(True)

    def show_step_2(self):
        label = QLabel("Выберите директорию gamedata OGSR")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_select = QPushButton("Выбрать папку")
        btn_select.clicked.connect(self.select_gamedata)

        self.path_label = QLabel("Путь не выбран")
        self.path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.step_layout.addWidget(label)
        self.step_layout.addWidget(btn_select)
        self.step_layout.addWidget(self.path_label)

        self.btn_next.setEnabled(False)

    def select_gamedata(self):
        path = QFileDialog.getExistingDirectory(self, "Выбор gamedata")
        if path:
            self.selected_gamedata = path
            self.path_label.setText(f"Выбрано: {path}")
            self.btn_next.setEnabled(True)

    def show_step_3(self):
        label = QLabel("Проверка структуры OGSR gamedata")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_layout.addWidget(label)

        gamedata = self.selected_gamedata

        checks = [
            ("configs/gameplay", os.path.join(gamedata, "configs", "gameplay")),
            ("configs/creatures", os.path.join(gamedata, "configs", "creatures")),
            ("spawns", os.path.join(gamedata, "spawns")),
            ("configs/text", os.path.join(gamedata, "configs", "text")),
        ]

        self.all_required_found = True

        for name, path in checks:
            row = QHBoxLayout()

            exists = os.path.exists(path)

            icon = QLabel()
            icon.setFixedWidth(25)
            icon.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            if exists:
                icon.setText("✓")
                icon.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
            else:
                icon.setText("?")
                icon.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
                icon.setToolTip(
                    f"Папка '{name}' не найдена.\nОжидаемый путь:\n{path}"
                )
                self.all_required_found = False

            row.addWidget(icon)

            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(name_label)

            if not exists:
                btn = QPushButton("Выбрать папку")
                btn.setFixedHeight(28)
                btn.clicked.connect(lambda _, n=name: self.select_missing_folder(n))
                row.addWidget(btn)

            self.step_layout.addLayout(row)

        self.btn_next.setEnabled(self.all_required_found)

    def select_missing_folder(self, name):
        path = QFileDialog.getExistingDirectory(self, f"Выбор папки для {name}")
        if path:
            QMessageBox.information(
                self,
                "Папка выбрана",
                f"Для '{name}' выбрана папка:\n{path}"
            )

    def finish_setup(self):
        gamedata = self.selected_gamedata

        final_settings = DEFAULT_SETTINGS.copy()

        final_settings["paths"] = {
            "gamedata": gamedata,
            "configs/gameplay": os.path.join(gamedata, "configs", "gameplay"),
            "configs/creatures": os.path.join(gamedata, "configs", "creatures"),
            "configs/text": os.path.join(gamedata, "configs", "text"),
            "spawns": os.path.join(gamedata, "spawns"),
        }

        save_settings(final_settings)
        self.accept()

    def next_step(self):
        self.current_step += 1
        self.update_step_ui()

    def prev_step(self):
        if self.current_step > 1:
            self.current_step -= 1
            self.update_step_ui()


class MainWindow(QMainWindow):
    def __init__(self, settings):
        super().__init__()
        self.setWindowTitle("OGSR Game Editor")
        self.showMaximized()

        self.settings = settings

        self.child_windows: list[QDialog] = []

        self.installEventFilter(self)

        self.init_menu()

    def init_menu(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        file_menu = QMenu("Файл", self)
        menu_bar.addMenu(file_menu)

        action_open = QAction("Открыть...", self)
        action_save = QAction("Сохранить", self)
        action_settings = QAction("Настройки", self)
        action_exit = QAction("Выход", self)

        file_menu.addAction(action_open)
        file_menu.addAction(action_save)
        file_menu.addSeparator()
        file_menu.addAction(action_settings)
        file_menu.addAction(action_exit)

        action_exit.triggered.connect(self.close)
        action_settings.triggered.connect(self.open_settings)

        view_menu = QMenu("Вид", self)
        menu_bar.addMenu(view_menu)

        action_dark = QAction("Тёмная тема", self)
        action_light = QAction("Светлая тема", self)

        view_menu.addAction(action_dark)
        view_menu.addAction(action_light)

        action_dark.triggered.connect(lambda: print("Тёмная тема"))
        action_light.triggered.connect(lambda: print("Светлая тема"))

    def open_settings(self):
        dlg = SettingsDialog(self)
        self.child_windows.append(dlg)
        dlg.show()

    def eventFilter(self, obj, event):
        if obj is self and event.type() == QEvent.Type.WindowStateChange:
            minimized = self.windowState() & Qt.WindowState.WindowMinimized

            for w in self.child_windows:
                if minimized:
                    w.showMinimized()
                else:
                    w.showNormal()

        return super().eventFilter(obj, event)


def validate_settings_paths(settings):
    paths = settings.get("paths", {})

    required_keys = [
        "gamedata",
        "configs/gameplay",
        "configs/creatures",
        "configs/text",
        "spawns"
    ]

    for key in required_keys:
        p = paths.get(key, "")
        if not p or not os.path.exists(p):
            return False

    return True


def run_app():
    app = QApplication(sys.argv)

    if not settings_exist():
        settings = DEFAULT_SETTINGS.copy()
        main_window = MainWindow(settings)
        main_window.show()

        dlg = WelcomeDialog(main_window)
        dlg.exec()

        settings = load_settings()
        main_window.settings = settings
    else:
        settings = load_settings()
        main_window = MainWindow(settings)
        main_window.show()

    # 🔥 Применяем шрифт глобально
    font_settings = settings.get("font", {"family": "Segoe UI", "size": 10})
    app.setFont(QFont(font_settings["family"], font_settings["size"]))

    paths_ok = validate_settings_paths(settings)

    if not paths_ok:
        dlg = SettingsDialog(main_window)
        main_window.child_windows.append(dlg)
        dlg.show()

    sys.exit(app.exec())
