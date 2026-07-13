from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QLineEdit, QSplitter, QMenu, QApplication
)
from PyQt6.QtGui import QAction, QPainter, QPen, QColor, QFont
from PyQt6.QtCore import Qt, QPoint, QRectF, QRect
from windows.dialog_properties import DialogProperties


# ============================================================
#   Узел диалога (квадратик)
# ============================================================

class DialogNode:
    def __init__(self, dialog_id: str, x: float, y: float):
        self.dialog_id = dialog_id
        self.x = x
        self.y = y

        self.width = 260
        self.height = 120
        self.header_height = 32

        self.dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0

    def rect(self):
        return QRectF(self.x, self.y, self.width, self.height)

    def header_rect(self):
        return QRectF(self.x, self.y, self.width, self.header_height)


# ============================================================
#   Бесконечная сетка + узлы
# ============================================================

class InfiniteGridWidget(QWidget):
    """
    Бесконечное поле с сеткой, панорамированием, зумом и узлами.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)

        self.offset_x = 0.0
        self.offset_y = 0.0
        self.scale = 1.0

        self._last_mouse_pos: QPoint | None = None
        self.base_grid_step = 50.0

        self.nodes: list[DialogNode] = []
        self.active_node: DialogNode | None = None

    # --------------------------------------------------------
    #   Добавление узла
    # --------------------------------------------------------
    def add_node(self, dialog_id: str):
        cx = self.width() / 2
        cy = self.height() / 2

        world_x = (cx - self.offset_x) / self.scale
        world_y = (cy - self.offset_y) / self.scale

        node = DialogNode(dialog_id, world_x - 130, world_y - 60)
        self.nodes.append(node)
        self.update()

    # --------------------------------------------------------
    #   Рисование
    # --------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        painter.fillRect(self.rect(), QColor(20, 20, 20))

        w = self.width()
        h = self.height()

        left_world   = (0 - self.offset_x) / self.scale
        right_world  = (w - self.offset_x) / self.scale
        top_world    = (0 - self.offset_y) / self.scale
        bottom_world = (h - self.offset_y) / self.scale

        visible_rect = QRectF(left_world, top_world,
                              right_world - left_world,
                              bottom_world - top_world)

        step = self.base_grid_step

        start_x = (int(visible_rect.left() // step) - 1) * step
        end_x   = (int(visible_rect.right() // step) + 1) * step

        start_y = (int(visible_rect.top() // step) - 1) * step
        end_y   = (int(visible_rect.bottom() // step) + 1) * step

        pen = QPen(QColor(60, 60, 60))
        pen.setWidth(1)
        painter.setPen(pen)

        x = start_x
        while x <= end_x:
            sx = x * self.scale + self.offset_x
            painter.drawLine(int(sx), 0, int(sx), h)
            x += step

        y = start_y
        while y <= end_y:
            sy = y * self.scale + self.offset_y
            painter.drawLine(0, int(sy), w, int(sy))
            y += step

        # ----------------------------------------------------
        #   Рисуем узлы (всегда поверх сетки)
        # ----------------------------------------------------
        for node in self.nodes:
            sx = node.x * self.scale + self.offset_x
            sy = node.y * self.scale + self.offset_y
            sw = node.width * self.scale
            sh = node.height * self.scale

            rect = QRect(int(sx), int(sy), int(sw), int(sh))
            header_rect = QRect(int(sx), int(sy), int(sw), int(node.header_height * self.scale))

            # тело узла
            painter.setPen(QPen(QColor(180, 180, 180)))
            painter.setBrush(QColor(40, 40, 40))
            painter.drawRect(rect)

            # шапка
            painter.setPen(QPen(QColor(200, 200, 200)))
            painter.setBrush(QColor(55, 55, 55))
            painter.drawRect(header_rect)

            # текст
            painter.setPen(QPen(QColor(230, 230, 230)))
            font = QFont("Arial", int(14 * self.scale))
            painter.setFont(font)
            painter.drawText(header_rect, Qt.AlignmentFlag.AlignCenter, node.dialog_id)

    # --------------------------------------------------------
    #   Панорамирование + перетаскивание узлов
    # --------------------------------------------------------
    def mousePressEvent(self, event):
        pos = event.position().toPoint()

        # экран → мир
        world_x = (pos.x() - self.offset_x) / self.scale
        world_y = (pos.y() - self.offset_y) / self.scale

        # проверяем попадание в шапку узла
        for node in reversed(self.nodes):  # верхние узлы проверяем первыми
            hr = node.header_rect()
            if hr.contains(world_x, world_y):
                self.active_node = node
                node.dragging = True
                node.drag_offset_x = world_x - node.x
                node.drag_offset_y = world_y - node.y
                return

        # иначе — панорамирование
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_mouse_pos = pos

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()

        if self.active_node and self.active_node.dragging:
            world_x = (pos.x() - self.offset_x) / self.scale
            world_y = (pos.y() - self.offset_y) / self.scale

            self.active_node.x = world_x - self.active_node.drag_offset_x
            self.active_node.y = world_y - self.active_node.drag_offset_y

            self.update()
            return

        if self._last_mouse_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            dx = pos.x() - self._last_mouse_pos.x()
            dy = pos.y() - self._last_mouse_pos.y()

            self.offset_x += dx
            self.offset_y += dy

            self._last_mouse_pos = pos
            self.update()

    def mouseReleaseEvent(self, event):
        if self.active_node:
            self.active_node.dragging = False
            self.active_node = None

        if event.button() == Qt.MouseButton.LeftButton:
            self._last_mouse_pos = None

    # --------------------------------------------------------
    #   Зум
    # --------------------------------------------------------
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        zoom_factor = 1.0 + (delta / 1200.0)

        new_scale = self.scale * zoom_factor
        new_scale = max(0.0001, min(new_scale, 1000))

        cursor_pos = event.position()
        cx = cursor_pos.x()
        cy = cursor_pos.y()

        world_x_before = (cx - self.offset_x) / self.scale
        world_y_before = (cy - self.offset_y) / self.scale

        self.scale = new_scale

        self.offset_x = cx - world_x_before * self.scale
        self.offset_y = cy - world_y_before * self.scale

        self.update()


# ============================================================
#   Основной конструктор диалогов
# ============================================================

class DialogConstructor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.modified = False

        splitter = QSplitter(Qt.Orientation.Horizontal)

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(splitter)

        # ----------------------------------------------------
        #   Левая часть
        # ----------------------------------------------------
        left_container = QWidget()
        left_layout = QVBoxLayout()
        left_container.setLayout(left_layout)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Поиск диалога...")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.textChanged.connect(self.update_filter)
        left_layout.addWidget(self.search_box)

        self.dialog_list = QListWidget()
        self.dialog_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.dialog_list.customContextMenuRequested.connect(self.open_context_menu)
        self.dialog_list.keyPressEvent = self._list_key_press
        self.dialog_list.itemDoubleClicked.connect(self.open_dialog_from_list)

        left_layout.addWidget(self.dialog_list)
        splitter.addWidget(left_container)

        # ----------------------------------------------------
        #   Правая часть — бесконечная сетка
        # ----------------------------------------------------
        right_container = QWidget()
        right_layout = QVBoxLayout()
        right_container.setLayout(right_layout)

        self.grid_view = InfiniteGridWidget(right_container)
        right_layout.addWidget(self.grid_view)

        splitter.addWidget(right_container)
        splitter.setSizes([300, 900])

        self.all_dialogs: list[str] = []
        self.load_dialogs()

    # --------------------------------------------------------
    #   Загрузка списка диалогов
    # --------------------------------------------------------
    def load_dialogs(self):
        loader = self.parent().res_loader
        dialog_ids = loader.get_dialog_list()
        dialog_ids.sort()

        self.all_dialogs = dialog_ids

        self.dialog_list.clear()
        for d in dialog_ids:
            self.dialog_list.addItem(d)

    # --------------------------------------------------------
    #   Фильтр
    # --------------------------------------------------------
    def update_filter(self, text: str):
        text = text.lower()
        self.dialog_list.clear()

        for d in self.all_dialogs:
            if text in d.lower():
                self.dialog_list.addItem(d)

    # --------------------------------------------------------
    #   Контекстное меню
    # --------------------------------------------------------
    def open_context_menu(self, position):
        item = self.dialog_list.itemAt(position)
        if not item:
            return

        dialog_id = item.text()

        menu = QMenu(self)
        open_action = QAction("Открыть", self)
        props_action = QAction("Свойства", self)

        menu.addAction(open_action)
        menu.addAction(props_action)
        menu.addSeparator()

        open_action.triggered.connect(lambda: self.open_dialog(dialog_id))
        props_action.triggered.connect(lambda: self.show_properties(dialog_id))

        menu.exec(self.dialog_list.mapToGlobal(position))

    # --------------------------------------------------------
    #   Двойной ЛКМ по списку
    # --------------------------------------------------------
    def open_dialog_from_list(self, item):
        dialog_id = item.text()
        self.open_dialog(dialog_id)

    # --------------------------------------------------------
    #   Открытие диалога → узел на сетке
    # --------------------------------------------------------
    def open_dialog(self, dialog_id: str):
        self.grid_view.add_node(dialog_id)

    # --------------------------------------------------------
    #   Свойства диалога
    # --------------------------------------------------------
    def show_properties(self, dialog_id: str):
        loader = self.parent().res_loader
        dialog_data = loader.get_dialog(dialog_id)

        dlg = DialogProperties(self, dialog_data)
        dlg.show()

    # --------------------------------------------------------
    #   Сохранение
    # --------------------------------------------------------
    def save_current_dialog(self):
        item = self.dialog_list.currentItem()
        if not item:
            return

        dialog_id = item.text()
        loader = self.parent().res_loader
        data = loader.get_dialog(dialog_id)
        loader.save_dialog(dialog_id, data)

    # --------------------------------------------------------
    #   Копирование Ctrl+C
    # --------------------------------------------------------
    def _list_key_press(self, event):
        if event.key() == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            item = self.dialog_list.currentItem()
            if item:
                QApplication.clipboard().setText(item.text())
        else:
            QListWidget.keyPressEvent(self.dialog_list, event)

    # --------------------------------------------------------
    #   Обновление UI
    # --------------------------------------------------------
    def refresh_dialog(self, dialog_id):
        self.load_dialogs()
        self.update_filter(self.search_box.text())
        print(f"[OK] refresh_dialog: диалог {dialog_id} обновлён в UI.")
