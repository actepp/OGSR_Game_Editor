from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDialog,
    QVBoxLayout, QLabel, QPushButton,
    QWidget, QHBoxLayout, QMessageBox, QToolTip, QFileDialog,
    QMenuBar, QMenu
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
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

        # нижняя панель кнопок
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

    # -----------------------------
    # Шаги приветственного мастера
    # -----------------------------

    def update_step_ui(self):
        # очищаем содержимое шага
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

    # --- Шаг 1 ---
    def show_step_1(self):
        label = QLabel("ИЗМЕНИТЬ ОПИСАНИЕ\n\n"
                       "Здесь будет вводная информация о редакторе.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_layout.addWidget(label)

        self.btn_next.setEnabled(True)

    # --- Шаг 2 ---
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

    # --- Шаг 3 ---
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

    # --- Шаг 4 ---
    def finish_setup(self):
        final_settings = DEFAULT_SETTINGS.copy()
        final_settings["paths"] = {
            "gamedata": self.selected_gamedata or ""
        }

        save_settings(final_settings)
        self.accept()

    # -----------------------------
    # Переключение шагов
    # -----------------------------

    def next_step(self):
        self.current_step += 1
        self.update_step_ui()

    def prev_step(self):
        if self.current_step > 1:
            self.current_step -= 1
            self.update_step_ui()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Настройки")
        self.resize(400, 300)
        self.setModal(True)

        layout = QVBoxLayout()
        label = QLabel("Здесь будут настройки")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        self.setLayout(layout)

    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_screen()

    def center_on_screen(self):
        screen = self.screen().geometry()
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + (screen.height() - self.height()) // 2
        self.move(x, y)


class MainWindow(QMainWindow):
    def __init__(self, settings):
        super().__init__()
        self.setWindowTitle("OGSR Game Editor")
        self.showMaximized()

        self.settings = settings

        self.init_menu()

    def init_menu(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        # --- Меню "Файл" ---
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

        # --- Меню "Вид" ---
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
        dlg.exec()


def run_app():
    app = QApplication(sys.argv)

    if settings_exist():
        settings = load_settings()
    else:
        settings = DEFAULT_SETTINGS

    main_window = MainWindow(settings)
    main_window.show()

    if not settings_exist():
        dlg = WelcomeDialog(parent=main_window)
        dlg.exec()

        settings = load_settings()

    sys.exit(app.exec())
