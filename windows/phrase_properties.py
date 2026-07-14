from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QComboBox
)
from PyQt6.QtCore import Qt


# ============================================================
#   Кликабельный квадрат с эффектом нажатия
# ============================================================
class ClickableSquare(QLabel):
    def __init__(self, text, normal_style, pressed_style):
        super().__init__(text)
        self.normal_style = normal_style
        self.pressed_style = pressed_style
        self.setStyleSheet(self.normal_style)
        self.clicked = lambda: None
        self._is_pressed = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_pressed = True
            self.setStyleSheet(self.pressed_style)

    def mouseReleaseEvent(self, event):
        if not self._is_pressed:
            return

        self._is_pressed = False
        self.setStyleSheet(self.normal_style)

        # действие только если отпускание ЛКМ произошло внутри кнопки
        if self.rect().contains(event.position().toPoint()):
            self.clicked()


# ============================================================
#   Окно свойств фразы
# ============================================================
class PhraseProperties(QDialog):
    def __init__(self, parent, node):
        super().__init__(parent)
        self.node = node

        # GUI → XML
        self.tag_map = {
            "Give info": "give_info",
            "Disable info": "disable_info",
            "Action": "action",
            "Precondition": "precondition"
        }

        # ширина колонки тегов
        fm = self.fontMetrics()
        self.tag_column_width = max(
            fm.horizontalAdvance(name) for name in self.tag_map.keys()
        ) + 45

        # окно
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle("Свойства фразы")
        self.resize(500, 300)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # --- ШАПКА ---
        title = QLabel(f"{node.text_key}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # линия
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: rgb(120, 120, 120);")
        layout.addWidget(line)

        # контейнер строк
        self.props_layout = QVBoxLayout()
        layout.addLayout(self.props_layout)

        # список строк
        self.rows = []

        # стили квадратов
        self.minus_normal = """
        QLabel {
            color: white;
            background-color: #b00000;
            font-size: 18px;
            font-weight: bold;
            border: 1px solid #700000;
            min-width: 24px;
            min-height: 24px;
            max-width: 24px;
            max-height: 24px;
            qproperty-alignment: AlignCenter;
        }
        """

        self.minus_pressed = """
        QLabel {
            color: white;
            background-color: #8a0000;
            font-size: 18px;
            font-weight: bold;
            border: 1px solid #500000;
            min-width: 24px;
            min-height: 24px;
            max-width: 24px;
            max-height: 24px;
            qproperty-alignment: AlignCenter;
        }
        """

        self.plus_normal = """
        QLabel {
            color: white;
            background-color: #009900;
            font-size: 18px;
            font-weight: bold;
            border: 1px solid #006600;
            min-width: 24px;
            min-height: 24px;
            max-width: 24px;
            max-height: 24px;
            qproperty-alignment: AlignCenter;
        }
        """

        self.plus_pressed = """
        QLabel {
            color: white;
            background-color: #007700;
            font-size: 18px;
            font-weight: bold;
            border: 1px solid #005500;
            min-width: 24px;
            min-height: 24px;
            max-width: 24px;
            max-height: 24px;
            qproperty-alignment: AlignCenter;
        }
        """

        # создаём стартовые строки
        for gui_name, xml_tag in self.tag_map.items():
            self.add_row(gui_name, xml_tag)

        # плюсик
        self.plus_row = QHBoxLayout()
        self.plus_row.addStretch()

        self.btn_plus = ClickableSquare("+", self.plus_normal, self.plus_pressed)
        self.btn_plus.clicked = self.add_empty_row
        self.plus_row.addWidget(self.btn_plus)

        self.props_layout.addLayout(self.plus_row)

        # нижняя панель
        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)

        btn_save = QPushButton("Сохранить")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                font-weight: bold;
                padding: 6px 14px;
                border: 1px solid #3e8e41;
            }
            QPushButton:hover {
                background-color: #5ecf60;
            }
        """)
        btn_save.clicked.connect(lambda: None)
        btn_layout.addWidget(btn_save)

        btn_layout.addStretch()

        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.close)
        btn_layout.addWidget(btn_cancel)

    # ============================================================
    #   Создание строки
    # ============================================================
    def add_row(self, gui_name="Precondition", xml_tag="precondition"):
        row_container = QVBoxLayout()
        row = QHBoxLayout()

        # TAG = ComboBox
        combo = QComboBox()
        combo.setFixedWidth(self.tag_column_width)
        combo.setStyleSheet("""
            QComboBox {
                color: white;
                background-color: #303030;
                border: 1px solid #505050;
                padding-left: 6px;
            }
        """)

        for name in self.tag_map.keys():
            combo.addItem(name)

        combo.setCurrentText(gui_name)
        combo.row_xml_tag = xml_tag
        combo.row_gui_tag = gui_name

        row.addWidget(combo)

        # вертикальная линия
        vline = QLabel()
        vline.setFixedWidth(1)
        vline.setStyleSheet("background-color: rgb(80, 80, 80);")
        row.addWidget(vline)

        # PARAMETER
        edit = QLabel("...")
        edit.setStyleSheet("color: #ccc; padding-left: 10px;")
        row.addWidget(edit, 1)

        # МИНУС
        btn_del = ClickableSquare("−", self.minus_normal, self.minus_pressed)
        btn_del.clicked = lambda rc=row_container: self.delete_row(rc)
        row.addWidget(btn_del)

        row_container.addLayout(row)

        # линия
        hline = QLabel()
        hline.setFixedHeight(1)
        hline.setStyleSheet("background-color: rgb(120, 120, 120);")
        row_container.addWidget(hline)

        self.rows.append(row_container)
        self.props_layout.insertLayout(len(self.rows) - 1, row_container)

    # ============================================================
    #   Добавление пустой строки
    # ============================================================
    def add_empty_row(self):
        self.add_row()

    # ============================================================
    #   Удаление строки
    # ============================================================
    def delete_row(self, row_container):
        if row_container in self.rows:
            self.rows.remove(row_container)

            # удаляем все виджеты строки
            while row_container.count():
                item = row_container.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self._delete_layout(item.layout())

            # удаляем сам layout
            self._delete_layout(row_container)

    def _delete_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._delete_layout(item.layout())
