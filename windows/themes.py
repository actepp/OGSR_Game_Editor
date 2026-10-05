from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication

THEME_DARK = {
    "bg_base": QColor("#1e1e1e"),
    "bg_surface": QColor("#252526"),
    "bg_elevated": QColor("#2d2d30"),
    "bg_input": QColor("#3c3c3c"),
    "border": QColor("#3e3e42"),
    "border_strong": QColor("#555555"),
    "text": QColor("#cccccc"),
    "text_secondary": QColor("#858585"),
    "text_inverse": QColor("#1e1e1e"),
    "accent": QColor("#0078d4"),
    "accent_hover": QColor("#1a86d9"),
    "success": QColor("#4caf50"),
    "success_hover": QColor("#5ecf60"),
    "error": QColor("#f44336"),
    "error_hover": QColor("#e53935"),
    "warning": QColor("#ff9800"),
    "node_body": QColor("#2d2d30"),
    "node_header": QColor("#383838"),
    "node_border": QColor("#505055"),
    "node_text": QColor("#cccccc"),
    "node_modified": QColor("#80c880"),
    "grid": QColor("#252526"),
    "grid_major": QColor("#353535"),
    "link": QColor("#b8b850"),
    "locale_bg": QColor("#4a4a6a"),
    "locale_hover": QColor("#5a5a80"),
    "check_bg": QColor("#3c8c3c"),
    "check_border": QColor("#1e5a1e"),
    "delete_bg": QColor("#aa3333"),
    "delete_hover": QColor("#cc4444"),
    "delete_border": QColor("#7a1e1e"),
    "add_bg": QColor("#2e7d32"),
    "add_hover": QColor("#388e3c"),
    "add_border": QColor("#1b5e20"),
}

THEME_LIGHT = {
    "bg_base": QColor("#eaeaea"),
    "bg_surface": QColor("#dcdcdc"),
    "bg_elevated": QColor("#cccccc"),
    "bg_input": QColor("#c4c4c4"),
    "border": QColor("#b0b0b0"),
    "border_strong": QColor("#888888"),
    "text": QColor("#1e1e1e"),
    "text_secondary": QColor("#484848"),
    "text_inverse": QColor("#1e1e1e"),
    "accent": QColor("#0078d4"),
    "accent_hover": QColor("#1a86d9"),
    "success": QColor("#4caf50"),
    "success_hover": QColor("#43a047"),
    "error": QColor("#d32f2f"),
    "error_hover": QColor("#c62828"),
    "warning": QColor("#f57c00"),
    "node_body": QColor("#cfcfcf"),
    "node_header": QColor("#bcbcbc"),
    "node_border": QColor("#9e9e9e"),
    "node_text": QColor("#1e1e1e"),
    "node_modified": QColor("#2e7d32"),
    "grid": QColor("#c8c8c8"),
    "grid_major": QColor("#aaaaaa"),
    "link": QColor("#7a7a20"),
    "locale_bg": QColor("#b8b8d8"),
    "locale_hover": QColor("#a8a8c8"),
    "check_bg": QColor("#4caf50"),
    "check_border": QColor("#388e3c"),
    "delete_bg": QColor("#d32f2f"),
    "delete_hover": QColor("#c62828"),
    "delete_border": QColor("#b71c1c"),
    "add_bg": QColor("#4caf50"),
    "add_hover": QColor("#43a047"),
    "add_border": QColor("#388e3c"),
}

THEMES = {
    "dark": THEME_DARK,
    "light": THEME_LIGHT,
}


def get_theme(theme_name: str):
    return THEMES.get(theme_name, THEME_DARK)


def _current_theme_name() -> str:
    from settings_manager import load_settings
    return load_settings().get("theme", "dark")


def divider_style(theme_name: str = None):
    if theme_name is None:
        theme_name = _current_theme_name()
    c = get_theme(theme_name)
    color = c["border"].name()
    return f"color: {color};"


def disabled_npc_button_style(theme_name: str = None):
    if theme_name is None:
        theme_name = _current_theme_name()
    c = get_theme(theme_name)
    return (
        f"QPushButton {{"
        f"background-color: {c['bg_elevated'].name()};"
        f"color: {c['text_secondary'].name()};"
        f"padding: 4px 10px;"
        f"border-radius: 4px;"
        f"}}"
    )


def name_edit_style(theme_name: str = None):
    if theme_name is None:
        theme_name = _current_theme_name()
    c = get_theme(theme_name)
    return (
        f"QLineEdit {{"
        f"font-size: 18px; font-weight: bold; padding: 6px;"
        f"background: {c['bg_elevated'].name()};"
        f"color: {c['text'].name()};"
        f"border: 1px solid {c['border_strong'].name()};"
        f"border-radius: 4px;"
        f"}}"
    )


def primary_button_style(theme_name: str = None):
    if theme_name is None:
        theme_name = _current_theme_name()
    c = get_theme(theme_name)
    return (
        f"QPushButton {{"
        f"background-color: {c['success'].name()};"
        f"color: {c['text_inverse'].name()};"
        f"font-weight: bold;"
        f"padding: 6px 14px;"
        f"border: 1px solid {c['success_hover'].name()};"
        f"}}"
        f"QPushButton:hover {{"
        f"background-color: {c['success_hover'].name()};"
        f"}}"
        f"QPushButton:disabled {{"
        f"background-color: {c['border'].name()};"
        f"color: {c['text_secondary'].name()};"
        f"border: 1px solid {c['border_strong'].name()};"
        f"}}"
    )


def path_label_style(theme_name: str = None):
    if theme_name is None:
        theme_name = _current_theme_name()
    c = get_theme(theme_name)
    return f"color: {c['text_secondary'].name()};"


def combo_box_row_style(theme_name: str = None):
    if theme_name is None:
        theme_name = _current_theme_name()
    c = get_theme(theme_name)
    return (
        f"QComboBox {{"
        f"color: {c['text'].name()};"
        f"background-color: {c['bg_elevated'].name()};"
        f"border: 1px solid {c['border_strong'].name()};"
        f"padding-left: 6px;"
        f"}}"
    )


def phrase_row_label_style(theme_name: str = None, color=None):
    if theme_name is None:
        theme_name = _current_theme_name()
    c = get_theme(theme_name)
    if color is None:
        color = c["text_secondary"].name()
    return f"color: {color}; padding-left: 10px;"


def phrase_edit_field_style(theme_name: str = None, text_color=None):
    if theme_name is None:
        theme_name = _current_theme_name()
    c = get_theme(theme_name)
    if text_color is None:
        text_color = c["text"].name()
    return f"color: {text_color}; background-color: {c['bg_input'].name()}; padding-left: 10px;"


def disabled_save_button_style(theme_name: str = None):
    if theme_name is None:
        theme_name = _current_theme_name()
    c = get_theme(theme_name)
    return (
        f"QPushButton {{"
        f"background-color: {c['bg_input'].name()};"
        f"color: {c['text_secondary'].name()};"
        f"border: 1px solid {c['border_strong'].name()};"
        f"}}"
    )


def error_text_style(theme_name: str = None):
    if theme_name is None:
        theme_name = _current_theme_name()
    c = get_theme(theme_name)
    return c["error"].name()


def success_text_style(theme_name: str = None):
    if theme_name is None:
        theme_name = _current_theme_name()
    c = get_theme(theme_name)
    return c["success"].name()


def apply_theme(theme_name: str):
    app = QApplication.instance()
    if theme_name == "dark":
        app.setStyleSheet(DARK_THEME_QSS)
    else:
        app.setStyleSheet(LIGHT_THEME_QSS)


DARK_THEME_QSS = """
/* ===== BASE ===== */
QWidget {
    background-color: #1e1e1e;
    color: #cccccc;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
    outline: none;
}

/* ===== MENU BAR ===== */
QMenuBar {
    background-color: #252526;
    color: #cccccc;
    border-bottom: 1px solid #3e3e42;
    padding: 4px 0px;
    spacing: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #3e3e42;
}

QMenuBar::item:pressed {
    background-color: #505055;
}

/* ===== DROPDOWN MENU ===== */
QMenu {
    background-color: #2d2d30;
    color: #cccccc;
    border: 1px solid #3e3e42;
    padding: 4px;
    spacing: 2px;
}

QMenu::item {
    background-color: transparent;
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #3e3e42;
    margin: 4px 8px;
}

/* ===== BUTTONS ===== */
QPushButton {
    background-color: #3c3c3c;
    color: #cccccc;
    border: 1px solid #555555;
    border-radius: 6px;
    padding: 6px 14px;
    min-height: 28px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #4a4a4a;
    border-color: #666666;
}

QPushButton:pressed {
    background-color: #505055;
    border-color: #0078d4;
}

QPushButton:disabled {
    background-color: #2a2a2a;
    color: #616161;
    border-color: #3e3e42;
}

/* Primary / accent button variant (used via class or explicit stylesheet) */
QPushButton[class="primary"],
QPushButton[style-class="primary"] {
    background-color: #0078d4;
    color: #ffffff;
    border: 1px solid #005a9e;
}

QPushButton[class="primary"]:hover,
QPushButton[style-class="primary"]:hover {
    background-color: #1a86d9;
}

QPushButton[class="primary"]:pressed,
QPushButton[style-class="primary"]:pressed {
    background-color: #005a9e;
}

/* ===== INPUT FIELDS ===== */
QLineEdit, QFontComboBox {
    background-color: #3c3c3c;
    color: #cccccc;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 24px;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
}

QLineEdit:hover, QFontComboBox:hover {
    border-color: #666666;
}

QLineEdit:focus, QFontComboBox:focus {
    border-color: #0078d4;
    background-color: #404040;
}

QLineEdit:disabled, QFontComboBox:disabled {
    background-color: #2a2a2a;
    color: #616161;
    border-color: #3e3e42;
}

/* ===== COMBO BOX ===== */
QComboBox {
    background-color: #3c3c3c;
    color: #cccccc;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 24px;
}

QComboBox:hover {
    border-color: #666666;
}

QComboBox:focus {
    border-color: #0078d4;
}

QComboBox:disabled {
    background-color: #2a2a2a;
    color: #616161;
    border-color: #3e3e42;
}

QComboBox QAbstractItemView {
    background-color: #2d2d30;
    color: #cccccc;
    border: 1px solid #3e3e42;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
    outline: none;
    padding: 2px;
}

/* ===== LIST WIDGET ===== */
QListWidget {
    background-color: #252526;
    color: #cccccc;
    border: 1px solid #3e3e42;
    border-radius: 4px;
    outline: none;
}

QListWidget::item {
    padding: 6px 10px;
    border-radius: 3px;
}

QListWidget::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}

QListWidget::item:hover:!selected {
    background-color: #2d2d30;
}

/* ===== TEXT EDIT ===== */
QTextEdit {
    background-color: #252526;
    color: #cccccc;
    border: 1px solid #3e3e42;
    border-radius: 4px;
    padding: 4px;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
}

QTextEdit:focus {
    border-color: #0078d4;
}

/* ===== PROGRESS BAR ===== */
QProgressBar {
    background-color: #252526;
    border: 1px solid #3e3e42;
    border-radius: 6px;
    text-align: center;
    color: #cccccc;
    min-height: 18px;
}

QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 5px;
    margin: 1px;
}

/* ===== SCROLL BARS ===== */
QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 12px;
    margin: 0px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #555555;
    border-radius: 6px;
    min-height: 30px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #666666;
}

QScrollBar::handle:vertical:pressed {
    background-color: #0078d4;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: #1e1e1e;
    height: 12px;
    margin: 0px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #555555;
    border-radius: 6px;
    min-width: 30px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #666666;
}

QScrollBar::handle:horizontal:pressed {
    background-color: #0078d4;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
    width: 0px;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}

/* ===== TOOL TIPS ===== */
QToolTip {
    background-color: #2d2d30;
    color: #cccccc;
    border: 1px solid #3e3e42;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}

/* ===== FRAMES / DIVIDERS ===== */
QFrame[frameShape="4"] {
    color: #3e3e42;
}

QFrame[frameShape="5"] {
    color: #3e3e42;
}

/* ===== GROUP BOX ===== */
QGroupBox {
    border: 1px solid #3e3e42;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: 500;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px 0 6px;
    color: #858585;
}

/* ===== TAB WIDGET ===== */
QTabWidget::pane {
    border: 1px solid #3e3e42;
    border-radius: 4px;
    background-color: #1e1e1e;
    top: -1px;
}

QTabBar::tab {
    background-color: #2d2d30;
    color: #858585;
    border: 1px solid #3e3e42;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 6px 14px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #1e1e1e;
    color: #cccccc;
    border-bottom: 2px solid #0078d4;
}

QTabBar::tab:hover:!selected {
    background-color: #383838;
}

/* ===== MESSAGE BOX ===== */
QMessageBox {
    background-color: #1e1e1e;
}

QMessageBox QLabel {
    color: #cccccc;
}

/* ===== CHECKBOX ===== */
QCheckBox {
    spacing: 8px;
    color: #cccccc;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #555555;
    background-color: #3c3c3c;
}

QCheckBox::indicator:hover {
    border-color: #0078d4;
}

QCheckBox::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
}

QCheckBox::indicator:disabled {
    background-color: #2a2a2a;
    border-color: #3e3e42;
}

/* ===== RADIO BUTTON ===== */
QRadioButton {
    spacing: 8px;
    color: #cccccc;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 1px solid #555555;
    background-color: #3c3c3c;
}

QRadioButton::indicator:hover {
    border-color: #0078d4;
}

QRadioButton::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
}

QRadioButton::indicator:disabled {
    background-color: #2a2a2a;
    border-color: #3e3e42;
}

/* ===== STATUS BAR ===== */
QStatusBar {
    background-color: #252526;
    color: #858585;
    border-top: 1px solid #3e3e42;
}

QStatusBar::item {
    border: none;
    padding: 0 8px;
}
"""


LIGHT_THEME_QSS = """
/* ===== BASE ===== */
QWidget {
    background-color: #eaeaea;
    color: #1e1e1e;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
    outline: none;
}

/* ===== MENU BAR ===== */
QMenuBar {
    background-color: #dcdcdc;
    color: #1e1e1e;
    border-bottom: 1px solid #b0b0b0;
    padding: 4px 0px;
    spacing: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #cccccc;
}

QMenuBar::item:pressed {
    background-color: #bcbcbc;
}

/* ===== DROPDOWN MENU ===== */
QMenu {
    background-color: #dcdcdc;
    color: #1e1e1e;
    border: 1px solid #b0b0b0;
    padding: 4px;
    spacing: 2px;
}

QMenu::item {
    background-color: transparent;
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #b0b0b0;
    margin: 4px 8px;
}

/* ===== BUTTONS ===== */
QPushButton {
    background-color: #cccccc;
    color: #1e1e1e;
    border: 1px solid #aaaaaa;
    border-radius: 6px;
    padding: 6px 14px;
    min-height: 28px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #bcbcbc;
    border-color: #999999;
}

QPushButton:pressed {
    background-color: #aaaaaa;
    border-color: #0078d4;
}

QPushButton:disabled {
    background-color: #e0e0e0;
    color: #888888;
    border-color: #b0b0b0;
}

QPushButton[class="primary"],
QPushButton[style-class="primary"] {
    background-color: #0078d4;
    color: #ffffff;
    border: 1px solid #005a9e;
}

QPushButton[class="primary"]:hover,
QPushButton[style-class="primary"]:hover {
    background-color: #1a86d9;
}

QPushButton[class="primary"]:pressed,
QPushButton[style-class="primary"]:pressed {
    background-color: #005a9e;
}

/* ===== INPUT FIELDS ===== */
QLineEdit, QFontComboBox {
    background-color: #c4c4c4;
    color: #1e1e1e;
    border: 1px solid #aaaaaa;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 24px;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
}

QLineEdit:hover, QFontComboBox:hover {
    border-color: #888888;
}

QLineEdit:focus, QFontComboBox:focus {
    border-color: #0078d4;
    background-color: #bcbcbc;
}

QLineEdit:disabled, QFontComboBox:disabled {
    background-color: #dcdcdc;
    color: #888888;
    border-color: #b0b0b0;
}

/* ===== COMBO BOX ===== */
QComboBox {
    background-color: #cccccc;
    color: #1e1e1e;
    border: 1px solid #aaaaaa;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 24px;
}

QComboBox:hover {
    border-color: #888888;
}

QComboBox:focus {
    border-color: #0078d4;
}

QComboBox:disabled {
    background-color: #dcdcdc;
    color: #888888;
    border-color: #b0b0b0;
}

QComboBox QAbstractItemView {
    background-color: #dcdcdc;
    color: #1e1e1e;
    border: 1px solid #b0b0b0;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
    outline: none;
    padding: 2px;
}

/* ===== LIST WIDGET ===== */
QListWidget {
    background-color: #dcdcdc;
    color: #1e1e1e;
    border: 1px solid #b0b0b0;
    border-radius: 4px;
    outline: none;
}

QListWidget::item {
    padding: 6px 10px;
    border-radius: 3px;
}

QListWidget::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}

QListWidget::item:hover:!selected {
    background-color: #cccccc;
}

/* ===== TEXT EDIT ===== */
QTextEdit {
    background-color: #c4c4c4;
    color: #1e1e1e;
    border: 1px solid #b0b0b0;
    border-radius: 4px;
    padding: 4px;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
}

QTextEdit:focus {
    border-color: #0078d4;
}

/* ===== PROGRESS BAR ===== */
QProgressBar {
    background-color: #dcdcdc;
    border: 1px solid #b0b0b0;
    border-radius: 6px;
    text-align: center;
    color: #1e1e1e;
    min-height: 18px;
}

QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 5px;
    margin: 1px;
}

/* ===== SCROLL BARS ===== */
QScrollBar:vertical {
    background-color: #eaeaea;
    width: 12px;
    margin: 0px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #999999;
    border-radius: 6px;
    min-height: 30px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #777777;
}

QScrollBar::handle:vertical:pressed {
    background-color: #0078d4;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: #eaeaea;
    height: 12px;
    margin: 0px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #999999;
    border-radius: 6px;
    min-width: 30px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #777777;
}

QScrollBar::handle:horizontal:pressed {
    background-color: #0078d4;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
    width: 0px;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}

/* ===== TOOL TIPS ===== */
QToolTip {
    background-color: #dcdcdc;
    color: #1e1e1e;
    border: 1px solid #b0b0b0;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}

/* ===== FRAMES / DIVIDERS ===== */
QFrame[frameShape="4"] {
    color: #888888;
}

QFrame[frameShape="5"] {
    color: #888888;
}

/* ===== GROUP BOX ===== */
QGroupBox {
    border: 1px solid #b0b0b0;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: 500;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px 0 6px;
    color: #484848;
}

/* ===== TAB WIDGET ===== */
QTabWidget::pane {
    border: 1px solid #b0b0b0;
    border-radius: 4px;
    background-color: #eaeaea;
    top: -1px;
}

QTabBar::tab {
    background-color: #dcdcdc;
    color: #484848;
    border: 1px solid #b0b0b0;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 6px 14px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #eaeaea;
    color: #1e1e1e;
    border-bottom: 2px solid #0078d4;
}

QTabBar::tab:hover:!selected {
    background-color: #cccccc;
}

/* ===== MESSAGE BOX ===== */
QMessageBox {
    background-color: #eaeaea;
}

QMessageBox QLabel {
    color: #1e1e1e;
}

/* ===== CHECKBOX ===== */
QCheckBox {
    spacing: 8px;
    color: #1e1e1e;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #aaaaaa;
    background-color: #cccccc;
}

QCheckBox::indicator:hover {
    border-color: #0078d4;
}

QCheckBox::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
}

QCheckBox::indicator:disabled {
    background-color: #dcdcdc;
    border-color: #b0b0b0;
}

/* ===== RADIO BUTTON ===== */
QRadioButton {
    spacing: 8px;
    color: #1e1e1e;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 1px solid #aaaaaa;
    background-color: #cccccc;
}

QRadioButton::indicator:hover {
    border-color: #0078d4;
}

QRadioButton::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
}

QRadioButton::indicator:disabled {
    background-color: #dcdcdc;
    border-color: #b0b0b0;
}

/* ===== SPLITTER ===== */
QSplitter::handle {
    background-color: #b0b0b0;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

/* ===== STATUS BAR ===== */
QStatusBar {
    background-color: #dcdcdc;
    color: #484848;
    border-top: 1px solid #b0b0b0;
}

QStatusBar::item {
    border: none;
    padding: 0 8px;
}
"""
