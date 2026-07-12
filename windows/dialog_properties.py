import os
import re
import xml.etree.ElementTree as ET

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QGridLayout, QFrame, QLineEdit,
    QWidget, QSizePolicy, QComboBox
)
from PyQt6.QtCore import Qt, QObject, QEvent

# Глобальный буфер изменений:
# каждая запись: {old_tag, new_tag, old_param, new_param}
EDIT_BUFFER = []

# Доступные теги: GUI-имя -> XML-имя
TAG_MAP = {
    "Precondition": "precondition",
    "Has Info": "has_info",
    "Dont Has Info": "dont_has_info"
}


def make_line():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    line.setStyleSheet("color: #444;")
    return line


def make_vline():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.VLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    line.setStyleSheet("color: #444;")
    return line


class EditLine(QLineEdit):
    def __init__(self, text, dialog, label):
        super().__init__(text)
        self.dialog = dialog
        self.label = label
        self.setStyleSheet("padding: 2px;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.clearFocus()
            return

        if event.key() == Qt.Key.Key_Escape:
            self.setText(self.label.text())
            self.dialog.cancel_edit()
            return

        super().keyPressEvent(event)


class ClickFilter(QObject):
    def __init__(self, dialog):
        super().__init__()
        self.dialog = dialog

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            editor = self.dialog.active_editor
            if editor is not None:
                pos = event.position().toPoint()
                if not editor.geometry().contains(pos):
                    self.dialog.finish_edit_external()
        return False


class TagCombo(QComboBox):
    def __init__(self, dialog, current_xml_tag, param_value):
        super().__init__()
        self.dialog = dialog

        # param_value — это ОРИГИНАЛЬНЫЙ XML-параметр для этой строки
        self.original_param = param_value

        gui_tag = None
        for k, v in TAG_MAP.items():
            if v == current_xml_tag:
                gui_tag = k
                break
        if gui_tag is None:
            gui_tag = list(TAG_MAP.keys())[0]

        # Оригинальный XML-тег (из файла)
        self.original_xml_tag = current_xml_tag
        # Последний выбранный GUI-тег
        self.old_gui_tag = gui_tag

        self.addItems(TAG_MAP.keys())
        self.setCurrentText(gui_tag)

        self.currentIndexChanged.connect(self.on_change)

    def on_change(self):
        new_gui_tag = self.currentText()
        new_xml = TAG_MAP[new_gui_tag]
        old_xml = TAG_MAP[self.old_gui_tag]

        # Ищем запись в буфере по ОРИГИНАЛЬНОМУ XML-параметру
        pair = None
        for p in EDIT_BUFFER:
            if p["old_param"] == self.original_param:
                pair = p
                break

        # Если тег вернулся к исходному — просто сбрасываем new_tag в оригинальный
        if new_xml == self.original_xml_tag:
            if pair is not None:
                pair["new_tag"] = self.original_xml_tag
                # Если вообще никаких изменений (тег и параметр совпадают с оригиналом) — можно удалить запись
                if pair["new_tag"] == pair["old_tag"] and pair["new_param"] == pair["old_param"]:
                    EDIT_BUFFER.remove(pair)
            self.old_gui_tag = new_gui_tag
            return

        # Если запись уже есть — обновляем только new_tag
        if pair is not None:
            pair["new_tag"] = new_xml
        else:
            # Создаём новую запись: old_tag/old_param — всегда из XML
            EDIT_BUFFER.append({
                "old_tag": self.original_xml_tag,
                "new_tag": new_xml,
                "old_param": self.original_param,
                "new_param": self.original_param
            })

        self.old_gui_tag = new_gui_tag


class EditableLabel(QLabel):
    def __init__(self, text, grid_layout, on_commit, dialog, tag):
        super().__init__(text)
        self.tag = tag
        self.grid = grid_layout
        self.on_commit = on_commit
        self.dialog = dialog
        self.setStyleSheet("padding: 2px;")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # ОРИГИНАЛЬНЫЙ XML-параметр для этой строки
        self.original_param = text

    def mousePressEvent(self, event):
        if self.dialog.active_editor is not None:
            self.dialog.finish_edit_external()
        self.start_edit()

    def start_edit(self):
        index = self.grid.indexOf(self)
        if index < 0:
            return

        row, col, _, _ = self.grid.getItemPosition(index)

        editor = EditLine(self.text(), self.dialog, self)
        editor.old_value = self.text()
        editor.editingFinished.connect(lambda: self.finish_edit(editor))

        self.grid.removeWidget(self)
        self.hide()

        self.grid.addWidget(editor, row, col)
        editor.setFocus()

        self.dialog.active_editor = editor
        self.dialog.active_label = self

    def finish_edit(self, editor):
        new_value = editor.text().strip()
        old_value = editor.old_value  # предыдущее GUI-значение, чисто для сравнения
        tag = self.tag

        # Ключ для буфера — ОРИГИНАЛЬНЫЙ XML-параметр
        xml_key = self.original_param

        if old_value != new_value:
            # Ищем запись по old_param == ОРИГИНАЛЬНОМУ XML-параметру
            pair = None
            for p in EDIT_BUFFER:
                if p["old_param"] == xml_key:
                    pair = p
                    break

            if pair is not None:
                # Обновляем только new_param
                pair["new_param"] = new_value
            else:
                # Создаём новую запись: old_tag/old_param — всегда из XML
                EDIT_BUFFER.append({
                    "old_tag": tag,
                    "new_tag": tag,
                    "old_param": xml_key,
                    "new_param": new_value
                })

        # Обновляем внутренние данные диалога (GUI-список)
        self.on_commit(new_value)

        index = self.grid.indexOf(editor)
        row, col, _, _ = self.grid.getItemPosition(index)

        self.grid.removeWidget(editor)
        editor.deleteLater()

        self.setText(new_value)
        self.grid.addWidget(self, row, col)
        self.show()

        self.dialog.active_editor = None
        self.dialog.active_label = None


class DeleteButton(QPushButton):
    def __init__(self, on_delete):
        super().__init__("–")
        self.on_delete = on_delete

        self.setFixedWidth(30)
        self.setStyleSheet("""
            QPushButton {
                background-color: #aa0000;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)

        self.clicked.connect(self.on_delete)


class AddButton(QPushButton):
    def __init__(self, on_add):
        super().__init__("+")
        self.on_add = on_add

        self.setFixedWidth(30)
        self.setStyleSheet("""
            QPushButton {
                background-color: #008800;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #00aa00;
            }
        """)

        self.clicked.connect(self.on_add)


class DialogProperties(QDialog):
    def __init__(self, parent, dialog_data):
        super().__init__(parent)

        dialog_id = dialog_data["id"]

        self.active_editor = None
        self.active_label = None


        dc = self.parent()
        mw = dc.parent()
        self.loader = mw.res_loader
        self.dialog_id = dialog_id

        self.loader.reload_dialog(dialog_id)
        self.dialog_data = self.loader.get_dialog(dialog_id)
        self.dialog_data["_delete_lines"] = []

        self.setWindowTitle(f"Свойства {dialog_id}")
        self.resize(650, 500)
        self.setWindowModality(Qt.WindowModality.WindowModal)

        self.filter = ClickFilter(self)
        self.installEventFilter(self.filter)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.grid = QGridLayout()
        grid = self.grid
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 3)
        grid.setColumnStretch(3, 0)
        main_layout.addLayout(grid)

        row = 0
        self.current_row = row

        name_label = QLabel(dialog_id)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 6px;")
        name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        grid.addWidget(name_label, row, 0, 1, 4)
        row += 1
        # --- NPC строка ---
        gameplay_path = os.path.join(self.loader.paths["configs/gameplay"])
        npc_name = find_npc_for_dialog(dialog_id, gameplay_path)

        npc_label = QLabel("NPC:")
        npc_label.setStyleSheet("font-weight: bold; padding: 4px;")

        npc_button = QPushButton(npc_name if npc_name else "Не найден")
        npc_button.setEnabled(False)  # пока не кликабельная
        npc_button.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: white;
                padding: 4px 10px;
                border-radius: 4px;
            }
        """)

        grid.addWidget(npc_label, row, 0)
        grid.addWidget(make_vline(), row, 1)
        grid.addWidget(npc_button, row, 2, 1, 2)
        row += 1

        grid.addWidget(make_line(), row, 0, 1, 4)
        row += 1

        grid.addWidget(make_line(), row, 0, 1, 4)
        row += 1



        grid.addWidget(npc_label, row, 0)
        grid.addWidget(make_vline(), row, 1)
        grid.addWidget(npc_button, row, 2, 1, 2)
        row += 1

        grid.addWidget(make_line(), row, 0, 1, 4)
        row += 1


        xml_path = self.dialog_data["xml_path"].replace("\\", "/")
        grid.addWidget(QLabel("Путь:"), row, 0)
        grid.addWidget(make_vline(), row, 1)

        lbl_xml = QLabel(xml_path)
        lbl_xml.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lbl_xml.setStyleSheet("color: #ccc;")
        grid.addWidget(lbl_xml, row, 2, 1, 2)
        row += 1

        grid.addWidget(make_line(), row, 0, 1, 4)
        row += 1

        self.current_row = row

        self.render_section(
            section_name="preconditions",
            xml_tag="precondition",
            commit_func=self.commit_pre,
        )

        self.render_section(
            section_name="has_info",
            xml_tag="has_info",
            commit_func=self.commit_hi,
        )

        self.render_section(
            section_name="dont_has_info",
            xml_tag="dont_has_info",
            commit_func=self.commit_dhi,
        )

        add_btn = AddButton(self.add_new_param)
        grid.addWidget(add_btn, self.current_row, 3)
        self.current_row += 1

        main_layout.addStretch()

        btn_layout = QHBoxLayout()
        main_layout.addLayout(btn_layout)

        btn_save = QPushButton("Сохранить")
        btn_cancel = QPushButton("Отмена")

        btn_save.clicked.connect(self.save_dialog)

        def cancel_all():
            EDIT_BUFFER.clear()
            self.close()

        btn_cancel.clicked.connect(cancel_all)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)

    def render_section(self, section_name, xml_tag, commit_func):
        lst = self.dialog_data.get(section_name)
        if not lst:
            return

        grid = self.grid
        row = self.current_row

        for i, value in enumerate(lst):

            combo = TagCombo(self, xml_tag, value)
            grid.addWidget(combo, row, 0)
            grid.addWidget(make_vline(), row, 1)

            lbl = EditableLabel(
                value,
                grid,
                lambda v, idx=i: commit_func(idx, v),
                self,
                xml_tag
            )

            def delete_item(i=i, combo=combo, lbl=lbl, value=value):
                if self.active_editor is not None and self.active_label is lbl:
                    editor = self.active_editor
                    idx = grid.indexOf(editor)
                    if idx >= 0:
                        r, c, _, _ = grid.getItemPosition(idx)
                        grid.removeWidget(editor)
                    editor.deleteLater()
                    self.active_editor = None
                    self.active_label = None

                del_btn = self.sender()

                pair = next(
                    (p for p in EDIT_BUFFER if p["old_param"] == lbl.original_param),
                    None
                )

                if pair:
                    tag_for_delete = pair["old_tag"]
                    param_for_delete = pair["old_param"]
                else:
                    tag_for_delete = xml_tag
                    param_for_delete = value

                line_text = f"<{tag_for_delete}>{param_for_delete}</{tag_for_delete}>"
                self.dialog_data["_delete_lines"].append(line_text)

                lst.pop(i)

                combo.setParent(None)
                lbl.setParent(None)
                del_btn.setParent(None)

                EDIT_BUFFER[:] = [
                    p for p in EDIT_BUFFER
                    if not (
                        p["old_param"] == lbl.original_param or
                        p["new_param"] == lbl.original_param
                    )
                ]

            del_btn = DeleteButton(delete_item)

            grid.addWidget(lbl, row, 2)
            grid.addWidget(del_btn, row, 3)

            row += 1
            grid.addWidget(make_line(), row, 0, 1, 4)
            row += 1

        self.current_row = row

    def commit_pre(self, index, val):
        lst = self.dialog_data["preconditions"]
        old = self.active_editor.old_value
        try:
            real_index = lst.index(old)
            lst[real_index] = val.strip()
        except ValueError:
            pass

    def commit_hi(self, index, val):
        lst = self.dialog_data["has_info"]
        old = self.active_editor.old_value
        try:
            real_index = lst.index(old)
            lst[real_index] = val.strip()
        except ValueError:
            pass

    def commit_dhi(self, index, val):
        lst = self.dialog_data["dont_has_info"]
        old = self.active_editor.old_value
        try:
            real_index = lst.index(old)
            lst[real_index] = val.strip()
        except ValueError:
            pass

    def add_new_param(self):
        new_value = "new_param"
        self.dialog_data["preconditions"].append(new_value)
        self.close()
        DialogProperties(self.parent(), self.dialog_data).show()

    def save_dialog(self):
        dc = self.parent()
        mw = dc.parent()
        loader = mw.res_loader

        dialog_id = self.dialog_data["id"]

        loader.save_dialog(dialog_id, self.dialog_data)
        loader.reload_dialog(dialog_id)
        dc.refresh_dialog(dialog_id)

        EDIT_BUFFER.clear()
        self.close()

    def cancel_edit(self):
        editor = self.active_editor
        label = self.active_label

        if editor is None or label is None:
            return

        index = self.grid.indexOf(editor)
        row, col, _, _ = self.grid.getItemPosition(index)

        self.grid.removeWidget(editor)
        editor.deleteLater()

        self.grid.addWidget(label, row, col)
        label.show()

        self.active_editor = None
        self.active_label = None

    def finish_edit_external(self):
        if self.active_editor is not None:
            self.active_editor.clearFocus()

    def closeEvent(self, event):
        EDIT_BUFFER.clear()
        super().closeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_screen()

    def center_on_screen(self):
        screen = self.screen().geometry()
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + (screen.height() - self.height()) // 2
        self.move(x, y)

def find_npc_for_dialog(dialog_id, gameplay_path):
    """
    Ищет НПС по диалогу в specific_characters_files.
    Возвращает ИМЕННО ID NPC (из атрибута id="...").
    """

    npc_dir = os.path.join(gameplay_path, "specific_characters_files")
    if not os.path.exists(npc_dir):
        return None

    # Регулярки
    re_char_start = re.compile(r'\s*<specific_character\b[^>]*id="([^"]+)"', re.IGNORECASE)
    re_actor      = re.compile(r'<actor_dialog>(.*?)</actor_dialog>', re.IGNORECASE)
    re_start      = re.compile(r'<start_dialog>(.*?)</start_dialog>', re.IGNORECASE)

    for filename in os.listdir(npc_dir):
        if not filename.endswith(".xml"):
            continue

        full_path = os.path.join(npc_dir, filename)

        try:
            with open(full_path, "r", encoding="cp1251", errors="ignore") as f:
                lines = f.readlines()
        except:
            continue

        inside_character = False
        current_npc_id = None

        for line in lines:

            # Начало блока NPC
            m_start = re_char_start.search(line)
            if m_start:
                inside_character = True
                current_npc_id = m_start.group(1)
                continue

            # Конец блока NPC
            if inside_character and "</specific_character>" in line:
                inside_character = False
                current_npc_id = None
                continue

            if not inside_character:
                continue

            # actor_dialog
            m_actor = re_actor.search(line)
            if m_actor and m_actor.group(1) == dialog_id:
                return current_npc_id

            # start_dialog
            m_start_d = re_start.search(line)
            if m_start_d and m_start_d.group(1) == dialog_id:
                return current_npc_id

    return None