from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from settings_manager import load_settings

DEFAULT_FONT = {"family": "Segoe UI", "size": 10}


def get_font_settings(settings=None):
    """Настройки шрифта из settings.json с подстановкой дефолтов."""
    if settings is None:
        settings = load_settings()

    font_settings = settings.get("font") or {}

    try:
        size = int(font_settings.get("size", DEFAULT_FONT["size"]))
    except (TypeError, ValueError):
        size = DEFAULT_FONT["size"]

    return {
        "family": font_settings.get("family") or DEFAULT_FONT["family"],
        "size": size if size > 0 else DEFAULT_FONT["size"],
    }


def apply_app_font(family=None, size=None):
    """
    Применяет шрифт ко всему приложению.

    Одного QApplication.setFont() мало:
      * пока активна тема (QSS), дочерние виджеты не наследуют шрифт
        приложения и берут шрифт стиля;
      * QApplication.setStyle() сбрасывает явно заданные шрифты виджетов.

    Поэтому шрифт ставится каждому живому виджету явно. Вызывать нужно
    после смены стиля/темы и после создания новых окон с интерфейсом.
    """
    if family is None or size is None:
        current = get_font_settings()
        family = family if family else current["family"]
        size = size if size else current["size"]

    font = QFont(family, size)

    app = QApplication.instance()
    app.setFont(font)

    widgets = app.allWidgets()
    for widget in widgets:
        widget.setFont(font)
        widget.update()

    print(f"[FONT] apply_app_font: {family} {size}pt -> {len(widgets)} виджетов")
    return font