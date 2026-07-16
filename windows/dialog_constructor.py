from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QLineEdit, QSplitter, QMenu, QApplication
)
from PyQt6.QtGui import QAction, QPainter, QPen, QColor, QFont
from PyQt6.QtCore import Qt, QPoint, QRectF, QRect
from windows.dialog_properties import DialogProperties
from windows.dialog_node_logic import DialogNodeLogic
from PyQt6.QtGui import QTextLayout, QTextOption
from PyQt6.QtCore import QPointF, QEvent
import os
import math
import re

AVAILABLE_LOCALES = ["rus", "eng"]

# ============================================================
#   Узел диалога (квадратик)
# ============================================================

class DialogNode:
    def __init__(self, dialog_id: str, x: float, y: float):
        self.dialog_id = dialog_id
        self.x = x
        self.y = y

        self.editing = False
        self.editor = None
        self.modified = False

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

    def settings_button_rect(self):
        size = self.right_button_size
        return QRectF(
            self.x + self.width - size*2 - 8,   # ← слева от крестика
            self.y + (self.header_height - size) / 2,
            size,
            size
        )

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

    def find_main_window(self):
        mw = self.parent()
        while mw is not None:
            if hasattr(mw, "res_loader"):
                return mw
            mw = mw.parent()
        return None

    def get_app_font(self):
        return QApplication.instance().font()

    def update_editor_geometry(self, node):
        if not node.editing or not node.editor:
            return

        sx = node.x * self.scale + self.offset_x
        sy = node.y * self.scale + self.offset_y + node.header_height * self.scale
        sw = node.width * self.scale
        sh = node.height * self.scale - node.header_height * self.scale

        node.editor.setGeometry(int(sx), int(sy), int(sw), int(sh))

    def smart_font_size(self, base: int) -> int:
        """
        Текст уменьшается при уменьшении масштаба,
        а при увеличении растёт только до 1.5× от базового размера.
        """
        if self.scale < 1.0:
            return int(base * self.scale)

        # ограничение сверху — максимум 1.5×
        return int(base * min(self.scale, 1.3))

    def spawn_graph(self, graph):
        self.nodes.clear()

        # строим карту детей
        children = {}
        for pid, phrase in graph.phrases.items():
            for nxt in phrase.next_list:
                children.setdefault(pid, []).append(int(nxt))

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
        child_pids = {n for phrase in graph.phrases.values() for n in phrase.next_list}
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

            node.text_key = phrase.text_key
            node.logic_text_real = phrase.text_real

            node.logic_next_list = phrase.next_list

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

            self.update_editor_geometry(node)

            rect = QRect(int(sx), int(sy), int(sw), int(sh))
            header_rect = QRect(int(sx), int(sy), int(sw), int(node.header_height * self.scale))

            # тело узла
            painter.setPen(QPen(QColor(180, 180, 180)))
            painter.setBrush(QColor(40, 40, 40))
            painter.drawRect(rect)

            # ------------------------------------------------
            #   ПОДСВЕТКА НЕСОХРАНЁННОГО СОСТОЯНИЯ
            # ------------------------------------------------
            if node.modified:
                glow_color = QColor(80, 200, 80, 180)  # чуть ярче и плотнее
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(glow_color, 5))    # толщина рамки увеличена
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
            painter.drawText(header_rect, Qt.AlignmentFlag.AlignCenter, str(node.logic_id))

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
            #   КНОПКА ШЕСТЕРЁНКИ
            # ------------------------------------------------
            sb = node.settings_button_rect()
            sb_sx = int(sb.x() * self.scale + self.offset_x)
            sb_sy = int(sb.y() * self.scale + self.offset_y)
            sb_sw = int(sb.width() * self.scale)
            sb_sh = int(sb.height() * self.scale)

            # координаты центра
            cx = sb_sx + sb_sw / 2
            cy = sb_sy + sb_sh / 2

            # радиусы
            outer_r = sb_sw / 2 - 2
            inner_r = outer_r * 0.55
            tooth_r1 = outer_r * 0.85
            tooth_r2 = outer_r

            # рисуем зубцы
            painter.setPen(QPen(QColor(230, 230, 230), 2))

            for angle in range(0, 360, 30):  # зубцов больше → выглядит как шестерёнка
                rad = angle * math.pi / 180

                # внутренняя точка зубца
                x1 = cx + tooth_r1 * math.cos(rad)
                y1 = cy + tooth_r1 * math.sin(rad)

                # внешняя точка зубца
                x2 = cx + tooth_r2 * math.cos(rad)
                y2 = cy + tooth_r2 * math.sin(rad)

                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

            # внешний круг
            painter.setPen(QPen(QColor(200, 200, 200), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), outer_r, outer_r)

            # внутренний круг
            painter.setPen(QPen(QColor(180, 180, 180), 2))
            painter.setBrush(QColor(120, 120, 120))
            painter.drawEllipse(QPointF(cx, cy), inner_r, inner_r)


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
            font = QFont(app_font.family(), app_font.pointSize())
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
            for nxt in node.logic_next_list:
                target = self.find_node_by_phrase_id(nxt)
                if target:
                    self.draw_link(painter, node, target)

    def finish_editing(self, node, save=False):
        new_text = node.editor.toPlainText().strip()

        node.logic_text_real = new_text
        node.editor.hide()
        node.editor.deleteLater()
        node.editor = None
        node.editing = False

        if not save:
            node.modified = True
        else:
            node.modified = False

        if save:
            print("try to save")
            # сохраняем в XML локали
            mw = self.find_main_window()
            if mw is None:
                print("[ERROR] Cannot find MainWindow for saving locale")
                return

            loader = mw.res_loader


            text_root = loader.paths["configs/text"]

            key = node.text_key
            locale = node.locale
            new_text = node.logic_text_real

            # ищем файл, где есть нужный <string id="...">
            for filename in os.listdir(text_root):
                if not filename.endswith(".xml"):
                    continue

                full_path = os.path.join(text_root, filename)

                try:
                    tree = ET.parse(full_path)
                    root = tree.getroot()

                    found = False

                    for s in root.findall("string"):
                        sid = s.get("id")
                        if sid == key:
                            # вариант 1: <string><rus>...</rus></string>
                            tag = s.find(locale)
                            if tag is not None:
                                tag.text = new_text
                            else:
                                # вариант 2: <string id="x" rus="..." />
                                s.set(locale, new_text)

                            found = True
                            break

                    if found:
                        tree.write(full_path, encoding="cp1251")
                        print(f"[OK] Locale saved: {key} → {locale} = {new_text}")
                        break

                except Exception as e:
                    print(f"[ERROR] Cannot update locale file {filename}: {e}")
            print("[finish_editing] calling save_node_locale()")
            self.save_node_locale(node)
    # --------------------------------------------------------
    #   Панорамирование + перетаскивание + ресайз + кнопки
    # --------------------------------------------------------
    def mousePressEvent(self, event):
        pos = event.position().toPoint()

        wx = (pos.x() - self.offset_x) / self.scale
        wy = (pos.y() - self.offset_y) / self.scale

        print(f"\n=== [PRESS] ({wx:.1f}, {wy:.1f}) ===")

        # --- закрытие активного редактора ---
        for n in self.nodes:
            if n.editing and n.editor:
                print(f"[PRESS] Editor active on node {n.dialog_id}:{n.logic_id}")

                # логируем попадание в галку
                if n.left_button_rect().contains(wx, wy):
                    print("[PRESS] Click on CHECKBOX while editor open → DO NOT close editor")
                    break

                # логируем попадание внутрь редактора
                if n.editor.geometry().contains(event.position().toPoint()):
                    print("[PRESS] Click INSIDE editor → DO NOT close editor")
                    break

                # логируем закрытие редактора
                print("[PRESS] Click OUTSIDE editor → closing editor (save=False)")
                self.finish_editing(n, save=False)
                break

        for node in reversed(self.nodes):
                        # ============================================================
            #   8) КОНТЕКСТНОЕ МЕНЮ (ПКМ)
            # ============================================================
            if event.button() == Qt.MouseButton.RightButton:

                # запрещаем меню если редактор открыт
                if node.editing:
                    return

                # запрещаем меню если клик по кнопкам
                if node.left_button_rect().contains(wx, wy):
                    return
                if node.right_button_rect().contains(wx, wy):
                    return
                if node.settings_button_rect().contains(wx, wy):
                    return
                if node.locale_button_rect().contains(wx, wy):
                    return

                # показываем меню только если клик по телу ноды
                if node.rect().contains(wx, wy):

                    menu = QMenu(self)

                    act_add_after = menu.addAction("Добавить отсюда")
                    act_delete = menu.addAction("Удалить фразу")

                    action = menu.exec(self.mapToGlobal(pos))

                    if action == act_delete:
                        self.delete_phrase(node)
                        return

                    if action == act_add_after:
                        self.add_phrase_after(node)
                        return
            # ============================================================
            #   1) КНОПКА ЛОКАЛИ
            # ============================================================
            if node.locale_button_rect().contains(wx, wy):
                print(f"[PRESS] Locale button on {node.dialog_id}:{node.logic_id}")
                node.locale_open = not node.locale_open
                self.update()
                return

            # ============================================================
            #   2) СПИСОК ЛОКАЛЕЙ
            # ============================================================
            if node.locale_open:
                loc = node.locale_button_rect()
                box_x = loc.x()
                box_y = loc.y() + node.locale_button_size + 4
                box_w = 80
                box_h = len(AVAILABLE_LOCALES) * 22

                if QRectF(box_x, box_y, box_w, box_h).contains(wx, wy):
                    print(f"[PRESS] Locale list click on {node.dialog_id}:{node.logic_id}")
                    index = int((wy - box_y) // 22)
                    if 0 <= index < len(AVAILABLE_LOCALES):
                        node.locale = AVAILABLE_LOCALES[index]

                        logic = DialogNodeLogic(self.constructor.parent().res_loader.paths["configs/text"])
                        new_text = logic.resolve_text(node.text_key, node.locale)
                        node.logic_text_real = new_text if new_text.strip() else "NONE"

                    node.locale_open = False
                    self.update()
                    return

                print("[PRESS] Click outside locale list → closing list")
                node.locale_open = False
                self.update()

            # ============================================================
            #   РЕСАЙЗ
            # ============================================================
            if self.is_in_resize_corner(node, wx, wy):
                print(f"[PRESS] Resize start on {node.dialog_id}:{node.logic_id}")
                self.active_node = node
                node.resizing = True
                node.resize_offset_x = wx - (node.x + node.width)
                node.resize_offset_y = wy - (node.y + node.height)
                return

            # ============================================================
            #   3) ДВОЙНОЙ КЛИК ПО ТЕКСТУ
            # ============================================================
            text_rect = QRectF(
                node.x,
                node.y + node.header_height,
                node.width,
                node.height - node.header_height
            )

            if text_rect.contains(wx, wy):
                print(f"[PRESS] Text area click on {node.dialog_id}:{node.logic_id}")
                if event.type() == QEvent.Type.MouseButtonDblClick and \
                   event.button() == Qt.MouseButton.LeftButton:
                    print("[PRESS] Double click → start editing")
                    self.start_editing(node)
                return

            # ============================================================
            #   4) ГАЛОЧКА
            # ============================================================
            if node.left_button_rect().contains(wx, wy):
                print(f"[PRESS] CHECKBOX pressed for {node.dialog_id}:{node.logic_id}")
                node.pressed_left_button = True
                self.update()
                return

            # ============================================================
            #   5) ШЕСТЕРЁНКА
            # ============================================================
            if node.settings_button_rect().contains(wx, wy):
                print(f"[PRESS] Settings button on {node.dialog_id}:{node.logic_id}")

                # --- ПЕРЕЗАГРУЗКА ДИАЛОГА ---
                dialog_id = node.dialog_id.split(":")[0]

                mw = self.constructor.window()      # главное окно
                if hasattr(mw, "res_loader"):
                    mw.res_loader.reload_dialog(dialog_id)
                else:
                    print("[ERROR] res_loader not found in main window")

                # --- ОТКРЫТИЕ ОКНА ---
                from windows.phrase_properties import PhraseProperties
                dlg = PhraseProperties(self.constructor.window(), node)
                dlg.show()
                return

            # ============================================================
            #   6) КРЕСТИК
            # ============================================================
            if node.right_button_rect().contains(wx, wy):
                print(f"[PRESS] CLOSE pressed for {node.dialog_id}:{node.logic_id}")
                node.pressed_right_button = True
                self.update()
                return

            # ============================================================
            #   7) ПЕРЕТАСКИВАНИЕ
            # ============================================================
            if node.header_rect().contains(wx, wy):
                print(f"[PRESS] Drag start on {node.dialog_id}:{node.logic_id}")
                self.active_node = node
                node.dragging = True
                node.drag_offset_x = wx - node.x
                node.drag_offset_y = wy - node.y
                return

        # панорамирование
        if event.button() == Qt.MouseButton.LeftButton:
            print("[PRESS] Panning start")
            self._last_mouse_pos = pos

    def start_editing(self, node):
        if node.editing:
            return

        node.editing = True

        # создаём QTextEdit
        from PyQt6.QtWidgets import QTextEdit
        editor = QTextEdit(self)
        editor.setPlainText(node.logic_text_real)

        # позиционируем
        sx = node.x * self.scale + self.offset_x
        sy = node.y * self.scale + self.offset_y + node.header_height * self.scale
        sw = node.width * self.scale
        sh = node.height * self.scale - node.header_height * self.scale

        editor.setGeometry(int(sx), int(sy), int(sw), int(sh))
        editor.show()

        node.editor = editor

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
        wx = (event.position().x() - self.offset_x) / self.scale
        wy = (event.position().y() - self.offset_y) / self.scale

        print(f"\n=== [RELEASE] ({wx:.1f}, {wy:.1f}) ===")

        for node in list(self.nodes):

            # --- галочка ---
            if node.left_button_rect().contains(wx, wy):
                print(f"[RELEASE] CHECKBOX released for {node.dialog_id}:{node.logic_id}")
                print(f"[RELEASE] node.editing={node.editing}")

                if node.editing:
                    print("[RELEASE] Editor open → finish_editing(save=True)")
                    self.finish_editing(node, save=True)
                else:
                    print("[RELEASE] Editor closed → save_node_locale()")
                    self.save_node_locale(node)

                node.modified = False
                self.update()
                return

            # --- крестик ---
            if node.right_button_rect().contains(wx, wy):
                print(f"[RELEASE] CLOSE released for {node.dialog_id}:{node.logic_id}")
                self.delete_branch(node)
                self.update()
                return

        if self.active_node:
            print(f"[RELEASE] Stop dragging/resizing for {self.active_node.dialog_id}:{self.active_node.logic_id}")
            self.active_node.dragging = False
            self.active_node.resizing = False
            self.active_node = None

        if event.button() == Qt.MouseButton.LeftButton:
            print("[RELEASE] End panning")
            self._last_mouse_pos = None

    def save_node_locale(self, node):
        # ищем MainWindow
        mw = self.parent()
        while mw is not None and not hasattr(mw, "res_loader"):
            mw = mw.parent()

        if mw is None:
            print("[ERROR] Cannot find MainWindow for saving locale")
            return

        loader = mw.res_loader
        text_root = loader.paths["configs/text"]

        key = node.text_key
        locale = node.locale
        new_text = node.logic_text_real

        # --- РЕКУРСИВНЫЙ ОБХОД ВСЕХ ПАПОК ---
        for dirpath, dirnames, filenames in os.walk(text_root):
            for filename in filenames:
                if not filename.endswith(".xml"):
                    continue

                full_path = os.path.join(dirpath, filename)

                with open(full_path, "r", encoding="windows-1251") as f:
                    lines = f.readlines()

                inside_string = False
                modified = False

                for i, line in enumerate(lines):
                    # нашли начало блока <string id="...">
                    if f'<string id="{key}"' in line:
                        inside_string = True

                    if inside_string:
                        # вариант 1: <rus>...</rus>
                        if f"<{locale}>" in line:
                            indent = line[:len(line) - len(line.lstrip())]
                            lines[i] = f"{indent}<{locale}>{new_text}</{locale}>\n"
                            modified = True
                            inside_string = False
                            break

                        # вариант 2: атрибуты rus="..."
                        if f'{locale}="' in line:
                            import re
                            lines[i] = re.sub(
                                rf'{locale}=".*?"',
                                f'{locale}="{new_text}"',
                                line
                            )
                            modified = True
                            inside_string = False
                            break

                        if "</string>" in line:
                            inside_string = False

                if modified:
                    with open(full_path, "w", encoding="windows-1251") as f:
                        f.writelines(lines)

                    print(f"[OK] Locale saved: {key} → {locale} = {new_text}")
                    return  # ← ВАЖНО: выходим после первого найденного файла

        print(f"[WARN] Locale key '{key}' not found in ANY text XML")


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

    def delete_phrase(self, node: DialogNode):
        import re

        dialog_id = node.dialog_id.split(":")[0]
        phrase_id = str(node.logic_id)

        mw = self.find_main_window()
        if mw is None or not hasattr(mw, "res_loader"):
            print("[delete_phrase] MainWindow or res_loader not found")
            return

        loader = mw.res_loader
        xml_path = loader.dialogs[dialog_id]["xml_path"]

        # читаем файл
        try:
            with open(xml_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            print("[delete_phrase] Cannot read XML:", e)
            return

        # --------------------------------------------------------
        #   1) Найти границы <dialog id="..."> ... </dialog>
        # --------------------------------------------------------
        dialog_start = None
        dialog_end = None

        pattern_dialog = rf'<dialog\s+[^>]*id="{dialog_id}"'
        for i, line in enumerate(lines):
            if re.search(pattern_dialog, line):
                dialog_start = i
                break

        if dialog_start is None:
            print("[delete_phrase] dialog start not found")
            return

        for i in range(dialog_start + 1, len(lines)):
            if "</dialog>" in lines[i]:
                dialog_end = i
                break

        if dialog_end is None:
            print("[delete_phrase] dialog end not found")
            return

        # --------------------------------------------------------
        #   2) Найти <phrase id="X"> ... </phrase> внутри диалога
        # --------------------------------------------------------
        start = None
        end = None

        pattern_phrase = rf'<phrase\s+[^>]*id="{phrase_id}"'
        for i in range(dialog_start, dialog_end + 1):
            if re.search(pattern_phrase, lines[i]):
                start = i
                break

        if start is None:
            print("[delete_phrase] phrase not found")
            return

        for i in range(start + 1, dialog_end + 1):
            if "</phrase>" in lines[i]:
                end = i
                break

        if end is None:
            print("[delete_phrase] phrase end not found")
            return

        # --------------------------------------------------------
        #   3) Удалить саму фразу
        # --------------------------------------------------------
        new_dialog_block = []
        for i in range(dialog_start, dialog_end + 1):
            if not (start <= i <= end):
                new_dialog_block.append(lines[i])

        # --------------------------------------------------------
        #   4) Удалить только внутри диалога все <next>X</next>
        # --------------------------------------------------------
        old_next = f"<next>{phrase_id}</next>"

        cleaned_dialog_block = []
        for line in new_dialog_block:
            if old_next not in line:
                cleaned_dialog_block.append(line)

        # --------------------------------------------------------
        #   5) Собрать новый файл
        # --------------------------------------------------------
        new_lines = (
            lines[:dialog_start] +
            cleaned_dialog_block +
            lines[dialog_end + 1:]
        )

        # --------------------------------------------------------
        #   6) Записать файл
        # --------------------------------------------------------
        try:
            with open(xml_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception as e:
            print("[delete_phrase] Cannot write XML:", e)
            return

        print(f"[delete_phrase] Phrase {phrase_id} deleted from dialog {dialog_id}")

        # --------------------------------------------------------
        #   7) Перезагрузить диалог
        # --------------------------------------------------------
        loader.reload_dialog(dialog_id)

        # --------------------------------------------------------
        #   8) Перерисовать граф
        # --------------------------------------------------------
        dialog_data = loader.get_dialog(dialog_id)
        xml_root = dialog_data["xml_node"]

        logic = DialogNodeLogic(loader.paths["configs/text"])
        graph = logic.build_graph(xml_root)

        self.spawn_graph(graph)


    def add_phrase_after(self, node: DialogNode):
        dialog_id = node.dialog_id.split(":")[0]
        phrase_id = str(node.logic_id)

        mw = self.find_main_window()
        loader = mw.res_loader

        xml_path = loader.dialogs[dialog_id]["xml_path"]

        # читаем файл
        with open(xml_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # ищем максимальный id
        import re
        max_id = 0
        for line in lines:
            m = re.search(r'<phrase\s+[^>]*id="(\d+)"', line)
            if m:
                max_id = max(max_id, int(m.group(1)))

        new_id = max_id + 1

        # ищем текущую фразу
        start = None
        end = None

        pattern = rf'<phrase\s+[^>]*id="{phrase_id}"'
        for i, line in enumerate(lines):
            if re.search(pattern, line):
                start = i
                break

        if start is None:
            print("[add_phrase_after] phrase not found")
            return

        for i in range(start + 1, len(lines)):
            if "</phrase>" in lines[i]:
                end = i
                break

        if end is None:
            print("[add_phrase_after] phrase end not found")
            return

        # вставляем новую фразу перед </phrase_list>
        insert_index = None
        for i, line in enumerate(lines):
            if "<phrase_list" in line:
                # ищем конец phrase_list
                for j in range(i+1, len(lines)):
                    if "</phrase_list>" in lines[j]:
                        insert_index = j
                        break
                break

        if insert_index is None:
            print("[add_phrase_after] phrase_list not found")
            return

        new_phrase = [
            f'        <phrase id="{new_id}">\n',
            f'            <text>new_phrase</text>\n',
            f'        </phrase>\n'
        ]

        lines[insert_index:insert_index] = new_phrase

        # обновляем next у текущей фразы
        new_next = f"<next>{new_id}</next>"
        old_next = None

        # ищем старый next
        for i in range(start, end+1):
            if "<next>" in lines[i]:
                old_next = lines[i].strip()
                lines[i] = f"            {new_next}\n"
                break

        # если next не было — добавляем
        if old_next is None:
            lines.insert(end, f"            {new_next}\n")

        # сохраняем
        with open(xml_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        # перезагрузка диалога
        loader.reload_dialog(dialog_id)

        # перерисовка
        dialog_data = loader.get_dialog(dialog_id)
        xml_root = dialog_data["xml_node"]

        logic = DialogNodeLogic(loader.paths["configs/text"])
        graph = logic.build_graph(xml_root)

        self.spawn_graph(graph)

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
                if n.logic_id == cur:
                    for child in n.logic_next_list:
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

    def refresh_dialog(self, dialog_id):
        mw = self.parent()
        loader = mw.res_loader

        # перезагрузка XML
        loader.reload_dialog(dialog_id)

        # обновление списка диалогов
        self.update_filter("")

        # получить путь к XML
        dialog_data = loader.get_dialog(dialog_id)
        xml_path = dialog_data["xml_path"]

        # загрузить XML вручную
        import xml.etree.ElementTree as ET
        try:
            xml_root = ET.parse(xml_path).getroot()

            # построить граф
            logic = DialogNodeLogic(loader.paths["configs/text"])
            graph = logic.build_graph(xml_root)

            # перерисовать
            self.grid_view.spawn_graph(graph)

        except Exception as e:
            print("[WARN] refresh_dialog failed:", e)


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
        self.refresh_dialog(dialog_id)
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

        dlg = DialogProperties(self.window(), dialog_data)
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
