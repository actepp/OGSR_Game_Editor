import os
import re

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QGridLayout, QFrame, QLineEdit, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QObject, QEvent

EDIT_BUFFER = []


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


class EditableLabel(QLabel):
    def __init__(self, text, grid_layout, on_commit, dialog, tag):
        super().__init__(text)
        self.tag = tag
        self.grid = grid_layout
        self.on_commit = on_commit
        self.dialog = dialog
        self.setStyleSheet("padding: 2px;")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

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
        old_value = editor.old_value
        tag = editor.label.tag

        if old_value != new_value:
            updated = False

            for pair in EDIT_BUFFER:
                if pair["new_param"] == old_value and pair["old_tag"] == tag:
                    pair["new_param"] = new_value
                    updated = True
                    break

            if not updated:
                EDIT_BUFFER.append({
                    "old_tag": tag,
                    "new_tag": tag,
                    "old_param": old_value,
                    "new_param": new_value
                })

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

        # Заголовок
        name_label = QLabel(dialog_id)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 6px;")
        name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        grid.addWidget(name_label, row, 0, 1, 4)
        row += 1

        grid.addWidget(make_line(), row, 0, 1, 4)
        row += 1

        # Путь к XML
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

        # --- Унифицированные секции ---
        self.render_section(
            section_name="preconditions",
            title="Precondition:",
            tag="precondition",
            commit_func=self.commit_pre,
        )

        self.render_section(
            section_name="has_info",
            title="Has Info:",
            tag="has_info",
            commit_func=self.commit_hi,
        )

        self.render_section(
            section_name="dont_has_info",
            title="Dont Has Info:",
            tag="dont_has_info",
            commit_func=self.commit_dhi,
        )

        # Кнопка добавления
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

    # -------------------------
    #  Универсальный рендер секции
    # -------------------------
    def render_section(self, section_name, title, tag, commit_func):
        lst = self.dialog_data.get(section_name)
        if not lst:
            return

        grid = self.grid
        row = self.current_row

        for i, value in enumerate(lst):

            lbl_name = QLabel(title)
            grid.addWidget(lbl_name, row, 0)
            grid.addWidget(make_vline(), row, 1)

            lbl = EditableLabel(
                value,
                grid,
                lambda v, idx=i: commit_func(idx, v),
                self,
                tag
            )

            def delete_item(i=i, lbl_name=lbl_name, lbl=lbl, value=value):
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
                line_text = f"<{tag}>{value}</{tag}>"
                self.dialog_data["_delete_lines"].append(line_text)

                lst.pop(i)

                lbl.setParent(None)
                del_btn.setParent(None)
                lbl_name.setParent(None)

                EDIT_BUFFER[:] = [
                    pair for pair in EDIT_BUFFER
                    if not (
                        pair["old_param"] == value or
                        pair["new_param"] == value
                    )
                ]

            del_btn = DeleteButton(delete_item)

            grid.addWidget(lbl, row, 2)
            grid.addWidget(del_btn, row, 3)

            row += 1
            grid.addWidget(make_line(), row, 0, 1, 4)
            row += 1

        self.current_row = row

    # -------------------------
    #  COMMIT handlers
    # -------------------------
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

    # -------------------------
    #  ADD NEW PARAM
    # -------------------------
    def add_new_param(self):
        new_value = "new_param"
        self.dialog_data["preconditions"].append(new_value)
        self.close()
        DialogProperties(self.parent(), self.dialog_data).show()

    # -------------------------
    #  SAVE
    # -------------------------
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

    # -------------------------
    #  CANCEL EDIT
    # -------------------------
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
