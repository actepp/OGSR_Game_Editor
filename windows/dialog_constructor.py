from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QLineEdit, QSplitter, QMenu, QApplication
)
from PyQt6.QtGui import QAction, QPainter, QPen, QColor, QFont
from PyQt6.QtCore import Qt, QPoint, QRectF, QRect
from windows.dialog_properties import DialogProperties
from windows.dialog_node_logic import DialogNodeLogic
from PyQt6.QtGui import QTextLayout, QTextOption
from PyQt6.QtCore import QPointF

AVAILABLE_LOCALES = ["rus", "eng"]


# ============================================================
#   Узел диалога (квадратик)
# ============================================================

class DialogNode:
    def __init__(self, dialog_id: str, x: float, y: float):
        self.dialog_id = dialog_id
        self.x = x
        self.y = y

        self.locale = "rus"   # локаль по умолчанию
        self.locale_open = False
        self.locale_button_size = 26

        self.width = 260
        self.height = 120
        self.header_height = 32

        # dragging
        self.dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        # resizing only bottom-right
        self.resizing = False
        self.resize_offset_x = 0
        self.resize_offset_y = 0

        # кнопки
        self.left_button_size = 20
        self.right_button_size = 20

        # визуальная реакция кнопок
        self.pressed_left_button = False
        self.pressed_right_button = False

        # логика
        self.logic_text_real = ""
        self.logic_next = None
        self.logic_id = None  # id фразы

    def locale_button_rect(self):
        return QRectF(
            self.x + 4 + self.left_button_size + 6,
            self.y + (self.header_height - self.locale_button_size) / 2,
            self.locale_button_size,
            self.locale_button_size
        )

    def rect(self):
        return QRectF(self.x, self.y, self.width, self.height)

    def header_rect(self):
        return QRectF(self.x, self.y, self.width, self.header_height)

    def left_button_rect(self):
        return QRectF(
            self.x + 4,
            self.y + (self.header_height - self.left_button_size) / 2,
            self.left_button_size,
            self.left_button_size
        )

    def right_button_rect(self):
        return QRectF(
            self.x + self.width - self.right_button_size - 4,
            self.y + (self.header_height - self.right_button_size) / 2,
            self.right_button_size,
            self.right_button_size
        )


# ============================================================
#   Бесконечная сетка + узлы
# ============================================================

class InfiniteGridWidget(QWidget):
    """
    Бесконечное поле с сеткой, панорамированием, зумом, узлами и ресайзом.
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

        self.resize_margin = 12  # зона нижнего правого угла

    def get_app_font(self):
        return QApplication.instance().font()

    def smart_font_size(self, base: int) -> int:
        """
        Умный размер шрифта:
        - до scale 1.5 — растёт нормально
        - после scale 1.5 — рост замедляется
        - после scale 3 — почти не растёт
        """
        if self.scale <= 1.5:
            return int(base * self.scale)

        if self.scale <= 3:
            return int(base * (1.5 + (self.scale - 1.5) * 0.4))

        return int(base * (1.5 + (3 - 1.5) * 0.4))  # фиксируем максимум

    def spawn_graph(self, graph):
        self.nodes.clear()

        # строим карту детей
        children = {}
        for pid, phrase in graph.phrases.items():
            nxt = phrase.next
            if nxt is not None:
                nxt = int(nxt)
                children.setdefault(pid, []).append(nxt)

        positions = {}

        # раскладка одного дерева
        def layout(pid, x, y):
            if pid in positions:
                return
            positions[pid] = (x, y)

            if pid not in children:
                return

            kids = children[pid]
            count = len(kids)
            spread = 320

            if count == 1:
                layout(kids[0], x, y + 200)
                return

            start_x = x - (spread * (count - 1)) // 2
            for i, kid in enumerate(kids):
                layout(kid, start_x + spread * i, y + 200)

        # ищем корни — фразы без родителя
        all_pids = set(graph.phrases.keys())
        child_pids = {int(p.next) for p in graph.phrases.values() if p.next}
        root_candidates = list(all_pids - child_pids)

        # раскладываем каждое дерево отдельно
        offset_x = 50
        for root in sorted(root_candidates):
            layout(root, offset_x, 50)
            offset_x += 500

        # раскладываем висячие узлы
        orphan_x = offset_x
        orphan_y = 50
        for pid in sorted(all_pids):
            if pid not in positions:
                positions[pid] = (orphan_x, orphan_y)
                orphan_y += 200

        # создаём узлы
        for pid, phrase in graph.phrases.items():
            x, y = positions[pid]

            node = DialogNode(f"{graph.dialog_id}:{pid}", x, y)
            node.logic_id = pid

            # ключ текста — нужен для переключения локали
            node.text_key = phrase.text_key

            # текст по умолчанию (rus)
            node.logic_text_real = phrase.text_real

            node.logic_next = int(phrase.next) if phrase.next else None

            self.nodes.append(node)


        self.update()



    def find_node_by_phrase_id(self, pid):
        for n in self.nodes:
            if n.logic_id == pid:
                return n
        return None

    def draw_link(self, painter, node, target):
        if not target:
            return

        # центры узлов
        node_cx = node.x + node.width / 2
        node_cy = node.y + node.height / 2

        target_cx = target.x + target.width / 2
        target_cy = target.y + target.height / 2

        # определяем направление
        dx = target_cx - node_cx
        dy = target_cy - node_cy

        # выбираем точку выхода
        if abs(dx) > abs(dy):
            # горизонтальное направление
            if dx > 0:
                # target справа
                start_x = node.x + node.width
                start_y = node_cy
                end_x = target.x
                end_y = target_cy
            else:
                # target слева
                start_x = node.x
                start_y = node_cy
                end_x = target.x + target.width
                end_y = target_cy
        else:
            # вертикальное направление
            if dy > 0:
                # target ниже
                start_x = node_cx
                start_y = node.y + node.height
                end_x = target_cx
                end_y = target.y
            else:
                # target выше
                start_x = node_cx
                start_y = node.y
                end_x = target_cx
                end_y = target.y + target.height

        # масштабируем
        sx = start_x * self.scale + self.offset_x
        sy = start_y * self.scale + self.offset_y
        tx = end_x * self.scale + self.offset_x
        ty = end_y * self.scale + self.offset_y

        # рисуем линию
        pen = QPen(QColor(200, 200, 80), 2)
        painter.setPen(pen)
        painter.drawLine(int(sx), int(sy), int(tx), int(ty))

        # --------------------------------------------------------
        #   Рисуем стрелку на конце
        # --------------------------------------------------------
        arrow_size = 12  # длина стрелки

        # направление линии
        dx = tx - sx
        dy = ty - sy
        length = (dx*dx + dy*dy) ** 0.5
        if length == 0:
            return

        # нормализуем
        ux = dx / length
        uy = dy / length

        # перпендикуляр
        px = -uy
        py = ux

        # точки стрелки
        ax = tx - ux * arrow_size
        ay = ty - uy * arrow_size

        left_x  = ax + px * (arrow_size / 2)
        left_y  = ay + py * (arrow_size / 2)
        right_x = ax - px * (arrow_size / 2)
        right_y = ay - py * (arrow_size / 2)

        painter.setBrush(QColor(200, 200, 80))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(
            QPoint(int(tx), int(ty)),
            QPoint(int(left_x), int(left_y)),
            QPoint(int(right_x), int(right_y))
        )


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
    #   Проверка попадания в нижний правый угол
    # --------------------------------------------------------
    def is_in_resize_corner(self, node: DialogNode, wx: float, wy: float):
        corner_x = node.x + node.width
        corner_y = node.y + node.height

        return (
            abs(wx - corner_x) <= self.resize_margin and
            abs(wy - corner_y) <= self.resize_margin
        )

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

        pen = QPen(QColor(25, 25, 25))  # более тёмная сетка
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
        #   Рисуем узлы
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

            # текст в шапке
            painter.setPen(QPen(QColor(230, 230, 230)))
            app_font = self.get_app_font()
            font = QFont(app_font.family(), self.smart_font_size(app_font.pointSize()))
            painter.setFont(font)
            painter.drawText(header_rect, Qt.AlignmentFlag.AlignCenter, node.dialog_id)

            # --- область текста ---
            left_padding = 8 * self.scale

            text_rect = QRect(
                int(sx + left_padding),
                int(sy + node.header_height * self.scale),
                int(sw - left_padding),
                int(sh - node.header_height * self.scale)
            )


            # включаем обрезку по рамке узла
            painter.save()
            painter.setClipRect(text_rect)

            # --- Автоперенос текста ---
            layout = QTextLayout(node.logic_text_real, painter.font())
            opt = QTextOption()
            opt.setWrapMode(QTextOption.WrapMode.WordWrap)
            layout.setTextOption(opt)

            layout.beginLayout()
            lines = []
            while True:
                line = layout.createLine()
                if not line.isValid():
                    break
                line.setLineWidth(sw - left_padding)  # ширина квадратика
                lines.append(line)
            layout.endLayout()

            # рисуем построчно
            y_offset = sy + node.header_height * self.scale + 4
            for line in lines:
                line.draw(painter, QPointF(sx + left_padding, y_offset))
                y_offset += line.height()

            painter.restore()

            # ------------------------------------------------
            #   ЛЕВАЯ КНОПКА — галочка
            # ------------------------------------------------
            lb = node.left_button_rect()
            lb_sx = int(lb.x() * self.scale + self.offset_x)
            lb_sy = int(lb.y() * self.scale + self.offset_y)
            lb_sw = int(lb.width() * self.scale)
            lb_sh = int(lb.height() * self.scale)

            color = QColor(60, 140, 60) if not node.pressed_left_button else QColor(40, 100, 40)
            painter.setBrush(color)
            painter.setPen(QPen(QColor(30, 90, 30)))
            painter.drawRect(lb_sx, lb_sy, lb_sw, lb_sh)

            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(lb_sx + 4, lb_sy + lb_sh // 2,
                             lb_sx + lb_sw // 2, lb_sy + lb_sh - 4)
            painter.drawLine(lb_sx + lb_sw // 2, lb_sy + lb_sh - 4,
                             lb_sx + lb_sw - 4, lb_sy + 4)

            # ------------------------------------------------
            #   ПРАВАЯ КНОПКА — крестик
            # ------------------------------------------------
            rb = node.right_button_rect()
            rb_sx = int(rb.x() * self.scale + self.offset_x)
            rb_sy = int(rb.y() * self.scale + self.offset_y)
            rb_sw = int(rb.width() * self.scale)
            rb_sh = int(rb.height() * self.scale)

            color = QColor(150, 60, 60) if not node.pressed_right_button else QColor(110, 40, 40)
            painter.setBrush(color)
            painter.setPen(QPen(QColor(90, 30, 30)))
            painter.drawRect(rb_sx, rb_sy, rb_sw, rb_sh)

            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(rb_sx + 4, rb_sy + 4,
                             rb_sx + rb_sw - 4, rb_sy + rb_sh - 4)
            painter.drawLine(rb_sx + rb_sw - 4, rb_sy + 4,
                             rb_sx + 4, rb_sy + rb_sh - 4)

            # ------------------------------------------------
            #   КНОПКА ЛОКАЛИ
            # ------------------------------------------------
            loc = node.locale_button_rect()
            loc_sx = int(loc.x() * self.scale + self.offset_x)
            loc_sy = int(loc.y() * self.scale + self.offset_y)
            loc_sw = int(loc.width() * self.scale)
            loc_sh = int(loc.height() * self.scale)


            painter.setBrush(QColor(70, 70, 120))
            painter.setPen(QPen(QColor(40, 40, 80)))
            painter.drawRect(loc_sx, loc_sy, loc_sw, loc_sh)

            painter.setPen(QPen(QColor(255, 255, 255)))
            app_font = self.get_app_font()
            font = QFont(app_font.family(), self.smart_font_size(app_font.pointSize()))
            painter.setFont(font)
            painter.drawText(QRect(loc_sx, loc_sy, loc_sw, loc_sh),
                             Qt.AlignmentFlag.AlignCenter,
                             node.locale.upper())

            # ------------------------------------------------
            #   ВЫПАДАЮЩИЙ СПИСОК ЛОКАЛЕЙ
            # ------------------------------------------------
            if node.locale_open:
                box_w = 80 * self.scale
                box_h = len(AVAILABLE_LOCALES) * (22 * self.scale)

                box_x = loc_sx
                box_y = loc_sy + loc_sh + 4

                painter.setBrush(QColor(50, 50, 50))
                painter.setPen(QPen(QColor(120, 120, 120)))
                painter.drawRect(int(box_x), int(box_y), int(box_w), int(box_h))

                for i, lang in enumerate(AVAILABLE_LOCALES):
                    item_y = box_y + i * (22 * self.scale)

                    painter.setPen(QPen(QColor(220, 220, 220)))

                    app_font = self.get_app_font()
                    font = QFont(app_font.family(), self.smart_font_size(app_font.pointSize()))
                    painter.setFont(font)

                    painter.drawText(
                        QRect(
                            int(box_x),
                            int(item_y),
                            int(box_w),
                            int(22 * self.scale)
                        ),
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                        f"  {lang.upper()}"
                    )

            # ------------------------------------------------
            #   Треугольник ресайза
            # ------------------------------------------------
            tri_size = 12 * self.scale

            p1 = QPoint(int(sx + sw), int(sy + sh))
            p2 = QPoint(int(sx + sw - tri_size), int(sy + sh))
            p3 = QPoint(int(sx + sw), int(sy + sh - tri_size))

            painter.setBrush(QColor(160, 160, 160))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(p1, p2, p3)

            # ------------------------------------------------
            #   Линки между узлами
            # ------------------------------------------------
            if node.logic_next is not None:
                target = self.find_node_by_phrase_id(node.logic_next)
                self.draw_link(painter, node, target)

    # --------------------------------------------------------
    #   Панорамирование + перетаскивание + ресайз + кнопки
    # --------------------------------------------------------
    def mousePressEvent(self, event):
        pos = event.position().toPoint()

        wx = (pos.x() - self.offset_x) / self.scale
        wy = (pos.y() - self.offset_y) / self.scale

        for node in reversed(self.nodes):

            # --- кнопка локали ---
            if node.locale_button_rect().contains(wx, wy):
                node.locale_open = not node.locale_open
                self.update()
                return

            # --- выбор локали ---
            if node.locale_open:
                loc = node.locale_button_rect()
                box_x = loc.x()
                box_y = loc.y() + node.locale_button_size + 4
                box_w = 80
                box_h = len(AVAILABLE_LOCALES) * 22

                if QRectF(box_x, box_y, box_w, box_h).contains(wx, wy):
                    index = int((wy - box_y) // 22)
                    if 0 <= index < len(AVAILABLE_LOCALES):
                        node.locale = AVAILABLE_LOCALES[index]

                        # 🔥 ПЕРЕЗАГРУЗКА ТЕКСТА ПО ЛОКАЛИ
                        logic = DialogNodeLogic(self.constructor.parent().res_loader.paths["configs/text"])
                        new_text = logic.resolve_text(node.text_key, node.locale)
                        node.logic_text_real = new_text if new_text.strip() else "NONE"

                    node.locale_open = False
                    self.update()
                    return

                # клик вне списка — закрыть
                node.locale_open = False
                self.update()

            # --- кнопка галочки ---
            if node.left_button_rect().contains(wx, wy):
                node.pressed_left_button = True
                self.update()
                return

            # --- кнопка крестика ---
            if node.right_button_rect().contains(wx, wy):
                node.pressed_right_button = True
                self.update()
                return

            # --- ресайз ---
            if self.is_in_resize_corner(node, wx, wy):
                self.active_node = node
                node.resizing = True
                node.resize_offset_x = wx - (node.x + node.width)
                node.resize_offset_y = wy - (node.y + node.height)
                return

            # --- перетаскивание за шапку ---
            if node.header_rect().contains(wx, wy):
                self.active_node = node
                node.dragging = True
                node.drag_offset_x = wx - node.x
                node.drag_offset_y = wy - node.y
                return

        # иначе — панорамирование
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_mouse_pos = pos

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        wx = (pos.x() - self.offset_x) / self.scale
        wy = (pos.y() - self.offset_y) / self.scale

        # ---------------------------
        #   Ресайз узла
        # ---------------------------
        if self.active_node and self.active_node.resizing:
            node = self.active_node

            new_w = wx - node.x - node.resize_offset_x
            new_h = wy - node.y - node.resize_offset_y

            if new_w > 80:
                node.width = new_w
            if new_h > node.header_height + 40:
                node.height = new_h

            self.update()
            return

        # ---------------------------
        #   Перетаскивание узла
        # ---------------------------
        if self.active_node and self.active_node.dragging:
            node = self.active_node
            node.x = wx - node.drag_offset_x
            node.y = wy - node.drag_offset_y
            self.update()
            return

        # ---------------------------
        #   Панорамирование
        # ---------------------------
        if self._last_mouse_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            dx = pos.x() - self._last_mouse_pos.x()
            dy = pos.y() - self._last_mouse_pos.y()

            self.offset_x += dx
            self.offset_y += dy

            self._last_mouse_pos = pos
            self.update()

    def mouseReleaseEvent(self, event):
        # кнопки — отпускание
        wx = (event.position().x() - self.offset_x) / self.scale
        wy = (event.position().y() - self.offset_y) / self.scale

        for node in list(self.nodes):

            # --- галочка ---
            if node.pressed_left_button:
                node.pressed_left_button = False

                if node.left_button_rect().contains(wx, wy):
                    print(f"[OK] SAVE clicked for {node.dialog_id}")
                self.update()

            # --- крестик ---
            if node.pressed_right_button:
                node.pressed_right_button = False

                if node.right_button_rect().contains(wx, wy):
                    print(f"[OK] CLOSE clicked for {node.dialog_id}")
                    self.delete_branch(node)
                    return

                self.update()

        if self.active_node:
            self.active_node.dragging = False
            self.active_node.resizing = False
            self.active_node = None

        if event.button() == Qt.MouseButton.LeftButton:
            self._last_mouse_pos = None
    # --------------------------------------------------------
    #   Удаление ветки (родитель + все потомки)
    # --------------------------------------------------------
    def delete_branch(self, root_node: DialogNode):
        root_pid = root_node.logic_id

        # собрать всех потомков
        to_delete = self.collect_descendants(root_pid)
        to_delete.add(root_pid)

        # удалить узлы
        self.nodes = [n for n in self.nodes if n.logic_id not in to_delete]

        self.update()


    # --------------------------------------------------------
    #   Сбор всех потомков по связям next
    # --------------------------------------------------------
    def collect_descendants(self, pid):
        result = set()
        stack = [pid]

        while stack:
            cur = stack.pop()

            # если у узла есть дети
            for n in self.nodes:
                if n.logic_id == cur and n.logic_next is not None:
                    child = n.logic_next
                    if child not in result:
                        result.add(child)
                        stack.append(child)

        return result

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
        self.grid_view.constructor = self
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
    #   Открытие диалога → узлы на сетке
    # --------------------------------------------------------
    def open_dialog(self, dialog_id: str):
        loader = self.parent().res_loader

        # получаем данные диалога
        dialog_data = loader.get_dialog(dialog_id)
        dialog_xml = dialog_data["xml_node"]

        # пути берём из loader
        logic = DialogNodeLogic(loader.paths["configs/text"])

        graph = logic.build_graph(dialog_xml, locale="rus")

        self.grid_view.spawn_graph(graph)

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
                # тут можешь добавить копирование id в буфер, если нужно
                print(f"[INFO] Copied dialog id: {item.text()}")
