from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDialog,
    QVBoxLayout, QLabel, QPushButton,
    QWidget, QHBoxLayout, QMessageBox, QToolTip, QFileDialog,
    QMenuBar, QMenu
)
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtCore import Qt, QEvent
from windows.window_settings import SettingsDialog
from windows.themes import apply_theme
from windows.dialog_constructor import DialogConstructor
from res_loader import ResourceLoader
from loader_thread import LoaderThread
from windows.loading_dialog import LoadingDialog


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

        # Храним вручную выбранные пути
        self.manual_paths = {}

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

    # Полная очистка layout (исправляет дублирование строк)
    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            sublayout = item.layout()

            if widget:
                widget.deleteLater()
            if sublayout:
                self.clear_layout(sublayout)

    def update_step_ui(self):
        self.clear_layout(self.step_layout)

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
            ("configs/gameplay", self.manual_paths.get("configs/gameplay", os.path.join(gamedata, "configs", "gameplay"))),
            ("configs/creatures", self.manual_paths.get("configs/creatures", os.path.join(gamedata, "configs", "creatures"))),
            ("spawns", self.manual_paths.get("spawns", os.path.join(gamedata, "spawns"))),
            ("configs/text", self.manual_paths.get("configs/text", os.path.join(gamedata, "configs", "text"))),
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
        if not path:
            return

        norm = path.replace("\\", "/")
        self.manual_paths[name] = norm

        QMessageBox.information(
            self,
            "Папка выбрана",
            f"Для '{name}' выбрана папка:\n{norm}"
        )

        self.update_step_ui()

    def finish_setup(self):
        gamedata = self.selected_gamedata

        final_settings = DEFAULT_SETTINGS.copy()

        final_settings["paths"] = {
            "gamedata": gamedata,
            "configs/gameplay": self.manual_paths.get("configs/gameplay", os.path.join(gamedata, "configs", "gameplay")),
            "configs/creatures": self.manual_paths.get("configs/creatures", os.path.join(gamedata, "configs", "creatures")),
            "configs/text": self.manual_paths.get("configs/text", os.path.join(gamedata, "configs", "text")),
            "spawns": self.manual_paths.get("spawns", os.path.join(gamedata, "spawns")),
            "scripts": os.path.join(gamedata, "scripts"),
        }

        save_settings(final_settings)

        # ВАЖНО: вызвать перезагрузку ресурсов у главного окна
        if self.parent() and hasattr(self.parent(), "reload_resources"):
            self.parent().settings = final_settings
            self.parent().reload_resources()

        self.accept()

    def reload_resources(self):
        """Перезагрузка ресурсов после мастера настройки."""
        self.res_loader = ResourceLoader(self.settings)

        if not self.res_loader.is_ready():
            print("ResourceLoader: пути невалидны, ресурсы не загружены")
        else:
            print("ResourceLoader: ресурсы успешно загружены")


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
        self.workspace_active = False
        self.settings = settings
        self.child_windows: list[QDialog] = []
        self.installEventFilter(self)
        self.init_menu()
        self.update_file_menu_state()
        self.load_resources_with_progress()

    def init_menu(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)
        file_menu = QMenu("Файл", self)
        self.file_menu = file_menu
        menu_bar.addMenu(file_menu)

        # Открыть
        action_open = QAction("Открыть...", self)
        file_menu.addAction(action_open)

        # Закрыть рабочее пространство
        self.action_close_tool = QAction("Закрыть", self)

        self.action_close_tool.triggered.connect(self.close_current_tool)

        # Сохранить
        self.action_save = QAction("Сохранить", self)
        self.action_save.triggered.connect(self.save_current_tool)


        file_menu.addSeparator()

        # Настройки
        action_settings = QAction("Настройки", self)
        file_menu.addAction(action_settings)

        # Выход
        action_exit = QAction("Выход", self)
        file_menu.addAction(action_exit)

        action_exit.triggered.connect(self.close)
        action_settings.triggered.connect(self.open_settings)


        view_menu = QMenu("Вид", self)
        menu_bar.addMenu(view_menu)

        # -----------------------------
        # Меню "Инструменты"
        # -----------------------------
        tools_menu = QMenu("Инструменты", self)
        menu_bar.addMenu(tools_menu)

        # Подменю "Диалоги"
        dialogs_menu = QMenu("Диалоги", self)
        tools_menu.addMenu(dialogs_menu)

        action_dialog_constructor = QAction("Конструктор", self)
        dialogs_menu.addAction(action_dialog_constructor)

        action_dialog_constructor.triggered.connect(self.open_dialog_constructor)

        themes_menu = QMenu("Темы", self)
        #view_menu.addMenu(themes_menu)

        action_dark = QAction("Тёмная тема", self)
        action_light = QAction("Светлая тема", self)

        themes_menu.addAction(action_dark)
        themes_menu.addAction(action_light)

        action_dark.triggered.connect(self.set_dark_theme)
        action_light.triggered.connect(self.set_light_theme)

    def load_resources_with_progress(self):

        dlg = LoadingDialog(self)
        dlg.center_on_screen()
        dlg.show()

        self.loader_thread = LoaderThread(self.settings)
        self.loader_thread.progress.connect(dlg.progress.setValue)

        def on_finished(loader):
            dlg.close()
            self.res_loader = loader
            print("Ресурсы загружены.")

        self.loader_thread.finished.connect(on_finished)
        self.loader_thread.start()


    def save_current_tool(self):
        widget = self.centralWidget()

        # Сохранение диалога
        if isinstance(widget, DialogConstructor):
            widget.save_current_dialog()

    def update_file_menu_state(self):
        if self.workspace_active:
            # Добавляем пункты, если их нет
            if self.action_close_tool not in self.file_menu.actions():
                self.file_menu.insertAction(self.file_menu.actions()[1], self.action_close_tool)

            if self.action_save not in self.file_menu.actions():
                # после "Закрыть"
                index = self.file_menu.actions().index(self.action_close_tool)
                self.file_menu.insertAction(self.file_menu.actions()[index + 1], self.action_save)

        else:
            # Удаляем пункты, если они есть
            if self.action_close_tool in self.file_menu.actions():
                self.file_menu.removeAction(self.action_close_tool)

            if self.action_save in self.file_menu.actions():
                self.file_menu.removeAction(self.action_save)


    def close_current_tool(self):
        widget = self.centralWidget()

        # Если центральный виджет — конструктор диалогов
        if isinstance(widget, DialogConstructor):

            # Проверяем флаг изменений
            if widget.modified:
                reply = QMessageBox.question(
                    self,
                    "Сохранить изменения?",
                    "В конструкторе есть несохранённые изменения.\nСохранить перед закрытием?",
                    QMessageBox.StandardButton.Yes |
                    QMessageBox.StandardButton.No |
                    QMessageBox.StandardButton.Cancel
                )

                if reply == QMessageBox.StandardButton.Cancel:
                    return

                if reply == QMessageBox.StandardButton.Yes:
                    # позже добавим сохранение
                    print("Сохраняем изменения...")

            # Закрываем модуль
            self.setCentralWidget(QWidget())
            self.workspace_active = False
            self.update_file_menu_state()


    def open_dialog_constructor(self):
        #self.reload_resources()  # ← ВАЖНО!
        widget = DialogConstructor(self)
        self.setCentralWidget(widget)

        self.workspace_active = True
        self.update_file_menu_state()

    def reload_resources(self):
        """Перезагрузка ресурсов после мастера настройки."""
        self.res_loader = ResourceLoader(self.settings)

        if not self.res_loader.is_ready():
            print("ResourceLoader: пути невалидны, ресурсы не загружены")
        else:
            print("ResourceLoader: ресурсы успешно загружены")


    def set_dark_theme(self):
        self.settings["theme"] = "dark"
        save_settings(self.settings)
        apply_theme("dark")

        # обновляем открытые окна настроек
        for w in self.child_windows:
            if isinstance(w, SettingsDialog):
                w.refresh_theme()


    def set_light_theme(self):
        self.settings["theme"] = "light"
        save_settings(self.settings)
        apply_theme("light")

        # обновляем открытые окна настроек
        for w in self.child_windows:
            if isinstance(w, SettingsDialog):
                w.refresh_theme()

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
        "spawns",
        "scripts"
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

    theme = settings.get("theme", "light")
    apply_theme(theme)

    font_settings = settings.get("font", {"family": "Segoe UI", "size": 10})
    app.setFont(QFont(font_settings["family"], font_settings["size"]))

    paths_ok = validate_settings_paths(settings)

    if not paths_ok:
        dlg = SettingsDialog(main_window)
        main_window.child_windows.append(dlg)
        dlg.show()

    sys.exit(app.exec())
