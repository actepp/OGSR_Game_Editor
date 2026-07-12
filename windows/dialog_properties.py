import os
import re

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QGridLayout, QFrame, QLineEdit, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QObject, QEvent

EDIT_BUFFER = []   # [{ "old": "...", "new": "..." }]

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
    def __init__(self, text, grid_layout, on_commit, dialog):
        super().__init__(text)
        self.grid = grid_layout
        self.on_commit = on_commit
        self.dialog = dialog
        self.setStyleSheet("padding: 2px;")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        # Если есть активный редактор — сначала завершаем его
        if self.dialog.active_editor is not None:
            self.dialog.finish_edit_external()
            #return  # предотвращаем запуск start_edit в этот же момент

        self.start_edit()


    def start_edit(self):
        index = self.grid.indexOf(self)
        if index < 0:
            return

        row, col, _, _ = self.grid.getItemPosition(index)

        editor = EditLine(self.text(), self.dialog, self)

        # ВАЖНО: сохраняем OLD прямо в editor
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
        old_value = editor.old_value  # ← теперь OLD всегда правильный

        if old_value != new_value:

            updated = False

            # 1) Проверяем: это повторное редактирование?
            #    Тогда old_value == предыдущему NEW
            for pair in EDIT_BUFFER:
                if pair["new"] == old_value:
                    print(f"[EDIT] Повторное редактирование: {pair['old']} -> {new_value}")
                    pair["new"] = new_value
                    updated = True
                    break

            # 2) Если нет — это первое редактирование этой строки
            if not updated:
                print(f"[EDIT] Новая запись: {old_value} -> {new_value}")
                EDIT_BUFFER.append({
                    "old": old_value,
                    "new": new_value
                })

            # Лог состояния буфера
            print("[BUFFER STATE]")
            for pair in EDIT_BUFFER:
                print(f"   OLD: {pair['old']}  ->  NEW: {pair['new']}")

        # --- стандартная логика обновления GUI ---
        self.on_commit(new_value)

        index = self.grid.indexOf(editor)
        row, col, _, _ = self.grid.getItemPosition(index)

        self.grid.removeWidget(editor)
        editor.deleteLater()

        self.setText(new_value)
        self.grid.addWidget(self, row, col)
        self.show()

        if "preconditions" in self.dialog.dialog_data:
            try:
                idx = self.dialog.dialog_data["preconditions"].index(new_value)
                exists = self.dialog.check_precondition(new_value)

                if not exists:
                    self.setStyleSheet("background-color: #330000; color: red; padding: 2px;")
                else:
                    self.setStyleSheet("padding: 2px;")
            except:
                pass

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


class DialogProperties(QDialog):
    def __init__(self, parent, dialog_data):
        super().__init__(parent)

        # ID диалога из переданных данных
        dialog_id = dialog_data["id"]

        self.active_editor = None
        self.active_label = None

        # доступ к loader и dialog_id
        dc = self.parent()
        mw = dc.parent()
        self.loader = mw.res_loader
        self.dialog_id = dialog_id

        # ПЕРЕЧИТЫВАЕМ ДИАЛОГ ИЗ ФАЙЛА, БЕРЁМ СВЕЖИЕ ДАННЫЕ
        self.loader.reload_dialog(dialog_id)
        self.dialog_data = self.loader.get_dialog(dialog_id)

        # список строк, которые надо удалить из XML (по тексту)
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

        # Имя диалога
        name_label = QLabel(dialog_id)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 6px;
        """)
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

        # Preconditions
        if self.dialog_data["preconditions"]:
            def commit_pre(index, val):
                self.dialog_data["preconditions"][index] = val.strip()

            for i, pre in enumerate(self.dialog_data["preconditions"]):

                exists = self.check_precondition(pre)

                lbl_name = QLabel("Precondition:")
                grid.addWidget(lbl_name, row, 0)
                grid.addWidget(make_vline(), row, 1)

                lbl = EditableLabel(
                    pre,
                    grid,
                    lambda v, idx=i: commit_pre(idx, v),
                    self
                )

                if not exists:
                    lbl_name.setStyleSheet("color: red; font-weight: bold;")
                    lbl.setStyleSheet("background-color: #330000; color: red; padding: 2px;")
                else:
                    lbl_name.setStyleSheet("")
                    lbl.setStyleSheet("padding: 2px;")

                def delete_pre(i=i, lbl_name=lbl_name, lbl=lbl, value=pre):
                    if self.active_editor is not None:
                        self.finish_edit_external()

                    del_btn = self.sender()

                    line_text = f"<precondition>{value}</precondition>"
                    self.dialog_data["_delete_lines"].append(line_text)

                    self.dialog_data["preconditions"].pop(i)

                    lbl.setParent(None)
                    del_btn.setParent(None)
                    lbl_name.setParent(None)
                    before = len(EDIT_BUFFER)
                    EDIT_BUFFER[:] = [
                        pair for pair in EDIT_BUFFER
                        if pair["old"] != value and pair["new"] != value
                    ]
                    after = len(EDIT_BUFFER)

                    print(f"[DELETE] Удалили '{value}', буфер: {before} -> {after}")


                del_btn = DeleteButton(delete_pre)

                grid.addWidget(lbl, row, 2)
                grid.addWidget(del_btn, row, 3)

                row += 1
                grid.addWidget(make_line(), row, 0, 1, 4)
                row += 1

        # Has Info
        if self.dialog_data["has_info"]:
            def commit_hi(index, val):
                self.dialog_data["has_info"][index] = val.strip()

            for i, hi in enumerate(self.dialog_data["has_info"]):

                lbl_name = QLabel("Has Info:")
                grid.addWidget(lbl_name, row, 0)
                grid.addWidget(make_vline(), row, 1)

                lbl = EditableLabel(
                    hi,
                    grid,
                    lambda v, idx=i: commit_hi(idx, v),
                    self
                )

                def delete_hi(i=i, lbl_name=lbl_name, lbl=lbl, value=hi):
                    if self.active_editor is not None:
                        self.finish_edit_external()
                    del_btn = self.sender()  # кнопка, по которой нажали

                    line_text = f"<has_info>{value}</has_info>"
                    self.dialog_data["_delete_lines"].append(line_text)

                    self.dialog_data["has_info"].pop(i)

                    lbl.setParent(None)
                    del_btn.setParent(None)
                    lbl_name.setParent(None)
                    before = len(EDIT_BUFFER)
                    EDIT_BUFFER[:] = [
                        pair for pair in EDIT_BUFFER
                        if pair["old"] != value and pair["new"] != value
                    ]
                    after = len(EDIT_BUFFER)

                    print(f"[DELETE] Удалили '{value}', буфер: {before} -> {after}")


                del_btn = DeleteButton(delete_hi)

                grid.addWidget(lbl, row, 2)
                grid.addWidget(del_btn, row, 3)

                row += 1
                grid.addWidget(make_line(), row, 0, 1, 4)
                row += 1

        # Dont Has Info
        if self.dialog_data["dont_has_info"]:
            def commit_dhi(index, val):
                self.dialog_data["dont_has_info"][index] = val.strip()

            for i, dhi in enumerate(self.dialog_data["dont_has_info"]):

                lbl_name = QLabel("Dont Has Info:")
                grid.addWidget(lbl_name, row, 0)
                grid.addWidget(make_vline(), row, 1)

                lbl = EditableLabel(
                    dhi,
                    grid,
                    lambda v, idx=i: commit_dhi(idx, v),
                    self
                )

                def delete_dhi(i=i, lbl_name=lbl_name, lbl=lbl, value=dhi):
                    if self.active_editor is not None:
                        self.finish_edit_external()
                    del_btn = self.sender()

                    line_text = f"<dont_has_info>{value}</dont_has_info>"
                    self.dialog_data["_delete_lines"].append(line_text)

                    self.dialog_data["dont_has_info"].pop(i)

                    lbl.setParent(None)
                    del_btn.setParent(None)
                    lbl_name.setParent(None)
                    before = len(EDIT_BUFFER)
                    EDIT_BUFFER[:] = [
                        pair for pair in EDIT_BUFFER
                        if pair["old"] != value and pair["new"] != value
                    ]
                    after = len(EDIT_BUFFER)

                    print(f"[DELETE] Удалили '{value}', буфер: {before} -> {after}")

                del_btn = DeleteButton(delete_dhi)

                grid.addWidget(lbl, row, 2)
                grid.addWidget(del_btn, row, 3)

                row += 1
                grid.addWidget(make_line(), row, 0, 1, 4)
                row += 1

        main_layout.addStretch()

        btn_layout = QHBoxLayout()
        main_layout.addLayout(btn_layout)

        btn_save = QPushButton("Сохранить")
        btn_cancel = QPushButton("Отмена")

        btn_save.clicked.connect(self.save_dialog)
        def cancel_all():
            print("[CANCEL] Полная очистка буфера")
            EDIT_BUFFER.clear()
            self.close()

        btn_cancel.clicked.connect(cancel_all)


        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)

    def finish_edit_external(self):
        if self.active_editor is not None:
            self.active_editor.clearFocus()

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

    def save_dialog(self):
        dc = self.parent()
        mw = dc.parent()
        loader = mw.res_loader

        dialog_id = self.dialog_data["id"]

        # ---------- ЭТАП 1: применяем EDIT_BUFFER к XML ----------

        xml_path = self.dialog_data["xml_path"].replace("\\", "/")

        try:
            with open(xml_path, "r", encoding="utf-8") as f:
                xml_content = f.read()
        except UnicodeDecodeError:
            with open(xml_path, "r", encoding="cp1251") as f:
                xml_content = f.read()

        # Если буфер пустой — просто идём дальше
        if EDIT_BUFFER:
            print("[SAVE] Применяем буфер изменений к XML")
            for pair in EDIT_BUFFER:
                old = pair["old"]
                new = pair["new"]

                if old == new:
                    continue

                if old not in xml_content:
                    print(f"[ERROR] В XML не найден OLD '{old}' для замены на '{new}'")
                    # Жёстко вылетаем, ничего не сохраняем
                    return

                print(f"[SAVE] Замена в XML: {old} -> {new}")
                xml_content = xml_content.replace(old, new)

            # Записываем обновлённый XML обратно
            try:
                with open(xml_path, "w", encoding="utf-8") as f:
                    f.write(xml_content)
            except UnicodeEncodeError:
                with open(xml_path, "w", encoding="cp1251") as f:
                    f.write(xml_content)

        # ---------- ЭТАП 2: твой текущий механизм сохранения ----------

        loader.save_dialog(dialog_id, self.dialog_data)
        loader.reload_dialog(dialog_id)
        dc.refresh_dialog(dialog_id)

        print("[SAVE] Диалог сохранён, буфер изменений НЕ очищаем (на твой выбор)")
        self.close()


    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_screen()

    def center_on_screen(self):
        screen = self.screen().geometry()
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + (screen.height() - self.height()) // 2
        self.move(x, y)

    def check_precondition(self, precondition: str) -> bool:
        if "." not in precondition:
            return False

        module, func = precondition.split(".", 1)

        loader = self.parent().parent().res_loader
        scripts_root = loader.paths.get("scripts")

        if not scripts_root or not os.path.exists(scripts_root):
            print("ERROR: scripts path not found:", scripts_root)
            return False

        target_file = None
        for root, dirs, files in os.walk(scripts_root):
            for f in files:
                name = f.lower()
                if name == f"{module.lower()}.script" or name == f"{module.lower()}.lua":
                    target_file = os.path.join(root, f)
                    break
            if target_file:
                break

        if not target_file:
            print("ERROR: module file not found:", module)
            return False

        try:
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(target_file, "r", encoding="cp1251") as f:
                    content = f.read()
            except Exception as e:
                print("ERROR reading script:", e)
                return False

        pattern = rf"function\s+{func}\s*\("
        found = re.search(pattern, content) is not None

        if not found:
            print(f"ERROR: function {func} not found in {target_file}")

        return found
