from PyQt6.QtWidgets import QApplication, QMainWindow
import sys

from settings_manager import load_settings

def run_app():
    settings = load_settings()

    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("OGSR Game Editor")

    # применяем настройки окна
    w = settings["window"]["width"]
    h = settings["window"]["height"]
    window.resize(w, h)

    if settings["window"]["maximized"]:
        window.showMaximized()
    else:
        window.show()

    sys.exit(app.exec())
