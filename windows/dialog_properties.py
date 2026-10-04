import os
import re
import xml.etree.ElementTree as ET

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QGridLayout, QFrame, QLineEdit,
    QWidget, QSizePolicy, QComboBox, QMessageBox, 
    QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, QObject, QEvent

EDIT_BUFFER = []

TAG_MAP = {
    "Precondition": "precondition",
    "Has Info": "has_info",
    "Dont Has Info": "dont_has_info",
    "Script Dialog": "init_func"
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

class DialogReloadProgress(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Обновление диалогов")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setFixedSize(260, 80)

        layout = QVBoxLayout(self)

        label = QLabel("Перезагрузка диалогов...")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        bar = QProgressBar()
        bar.setRange(0, 0)  # бесконечный индикатор
        layout.addWidget(bar)

    def center_on_parent(self):
        if self.parent():
            p = self.parent().geometry()
            x = p.x() + (p.width() - self.width()) // 2
            y = p.y() + (p.height() - self.height()) // 2
            self.move(x, y)

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
    def __init__(self, dialog, current_xml_tag, param_value, label=None):
        super().__init__()
        self.dialog = dialog
        self.original_param = param_value
        self.label = label
        if current_xml_tag is None:
            gui_tag = "Precondition"
            self.original_xml_tag = None
            self.old_gui_tag = "Precondition"
        else:
            gui_tag = None
            for k, v in TAG_MAP.items():
                if v == current_xml_tag:
                    gui_tag = k
                    break
            if gui_tag is None:
                gui_tag = "Precondition"
            self.original_xml_tag = current_xml_tag
            self.old_gui_tag = gui_tag
        self.addItems(TAG_MAP.keys())
        self.setCurrentText(gui_tag)
        self.currentIndexChanged.connect(self.on_change)

    def on_change(self):
        new_gui_tag = self.currentText()
        new_xml = TAG_MAP[new_gui_tag]
        if self.original_param is None and self.original_xml_tag is None:
            self.old_gui_tag = new_gui_tag
            if self.label is not None:
                self.label.set_tag(new_xml)
                self.dialog.revalidate_label(self.label)
            self.dialog.check_save_enabled()
            return
        old_xml = TAG_MAP[self.old_gui_tag]
        pair = None
        for p in EDIT_BUFFER:
            if p["old_param"] == self.original_param:
                pair = p
                break
        if new_xml == self.original_xml_tag:
            if pair is not None:
                pair["new_tag"] = self.original_xml_tag
                if pair["new_tag"] == pair["old_tag"] and pair["new_param"] == pair["old_param"]:
                    EDIT_BUFFER.remove(pair)
            self.old_gui_tag = new_gui_tag
            if self.label is not None:
                self.label.set_tag(new_xml)
                self.dialog.revalidate_label(self.label)
            self.dialog.check_save_enabled()
            return
        if pair is not None:
            pair["new_tag"] = new_xml
        else:
            EDIT_BUFFER.append({
                "old_tag": self.original_xml_tag,
                "new_tag": new_xml,
                "old_param": self.original_param,
                "new_param": self.original_param
            })
        self.old_gui_tag = new_gui_tag
        if self.label is not None:
            self.label.set_tag(new_xml)
            self.dialog.revalidate_label(self.label)
        self.dialog.check_save_enabled()


class EditableLabel(QLabel):
    def __init__(self, text, grid_layout, on_commit, dialog, tag):
        super().__init__(text)
        self.tag = tag
        self.grid = grid_layout
        self.on_commit = on_commit
        self.dialog = dialog
        self.setStyleSheet("padding: 2px;")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.original_param = text if text != "" else None

    def set_tag(self, tag):
        self.tag = tag
        self.dialog.revalidate_label(self)

    def mousePressEvent(self, event):
        if self.dialog.active_editor is not None:
            self.dialog.finish_edit_external()
        self.start_edit()

    def start_edit(self):
        print(f"[DEBUG] start_edit: label={self}, text={self.text()!r}, tag={self.tag!r}")
        index = self.grid.indexOf(self)
        if index < 0:
            return
        row, col, _, _ = self.grid.getItemPosition(index)
        editor = EditLine(self.text(), self.dialog, self)
        editor.old_value = self.text()
        editor.editingFinished.connect(lambda: self.finish_edit(editor))
        editor.textChanged.connect(lambda text, ed=editor, lbl=self: self.dialog.on_editor_text_changed(ed, lbl))
        self.grid.removeWidget(self)
        self.hide()
        self.grid.addWidget(editor, row, col)
        editor.setFocus()
        self.dialog.active_editor = editor
        self.dialog.active_label = self
        print(f"[DEBUG] start_edit: calling on_editor_text_changed")
        self.dialog.on_editor_text_changed(editor, self)

    def finish_edit(self, editor):
        print(f"[DEBUG] finish_edit called")
        if self.dialog.active_editor is None or self.dialog.active_label is None:
            print(f"[DEBUG] finish_edit: early return")
            return

        new_value = editor.text().strip()
        old_value = editor.old_value
        tag = self.tag
        xml_key = self.original_param
        print(f"[DEBUG] finish_edit: new_value={new_value!r}, old_value={old_value!r}, tag={tag!r}")

        if self.original_param is None:
            index = self.grid.indexOf(editor)
            row, col, _, _ = self.grid.getItemPosition(index)

            self.grid.removeWidget(editor)
            editor.deleteLater()

            self.setText(new_value)
            self.grid.addWidget(self, row, col)
            self.show()

            self.dialog.active_editor = None
            self.dialog.active_label = None
            self.dialog.revalidate_label(self)
            self.dialog.check_save_enabled()
            return

        if old_value != new_value:
            pair = None
            for p in EDIT_BUFFER:
                if p["old_param"] == xml_key:
                    pair = p
                    break

            if pair is not None:
                pair["new_param"] = new_value
            else:
                EDIT_BUFFER.append({
                    "old_tag": tag,
                    "new_tag": tag,
                    "old_param": xml_key,
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
        print(f"[DEBUG] finish_edit: calling revalidate and check_save")
        self.dialog.revalidate_label(self)
        self.dialog.check_save_enabled()

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
    def __init__(self, parent, dialog_data, is_new=False):
        super().__init__(parent)
        self.is_new = is_new
        dialog_id = dialog_data["id"]
        self.active_editor = None
        self.active_label = None
        self.new_rows = []
        self.validated_labels = []
        mw = self.parent()          # теперь это MainWindow
        self.loader = mw.res_loader
        self.dialog_id = dialog_id
        if is_new:
            # Новый диалог — используем переданные данные
            self.dialog_data = dialog_data
        else:
            # Старый диалог — загружаем из файлов
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
        self.name_edit = QLineEdit(dialog_id)
        self.name_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_edit.setStyleSheet("""
            QLineEdit {
                font-size: 18px;
                font-weight: bold;
                padding: 6px;
                background: #333;
                color: #eee;
                border: 1px solid #555;
                border-radius: 4px;
            }
        """)
        grid.addWidget(self.name_edit, row, 0, 1, 4)

        row += 1
        gameplay_path = os.path.join(self.loader.paths["configs/gameplay"])
        npc_name = find_npc_for_dialog(dialog_id, gameplay_path)
        npc_label = QLabel("NPC:")
        npc_label.setStyleSheet("font-weight: bold; padding: 4px;")
        npc_button = QPushButton(npc_name if npc_name else "Не найден")
        npc_button.setEnabled(False)
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
        # Путь к файлу диалога
        if not is_new:
            xml_path = self.dialog_data["xml_path"].replace("\\", "/")
            self.xml_path = xml_path

            grid.addWidget(QLabel("Путь:"), row, 0)
            grid.addWidget(make_vline(), row, 1)

            lbl_xml = QLabel(xml_path)
            lbl_xml.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lbl_xml.setStyleSheet("color: #ccc;")
            grid.addWidget(lbl_xml, row, 2, 1, 2)

            row += 1
            grid.addWidget(make_line(), row, 0, 1, 4)
            row += 1
        else:
            # Новый диалог — пути нет
            self.xml_path = None
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
        self.render_section(
            section_name="init_func",
            xml_tag="init_func",
            commit_func=self.commit_init_func,
        )

        add_btn = AddButton(self.add_new_param)
        grid.addWidget(add_btn, self.current_row, 3)
        self.current_row += 1
        main_layout.addStretch()
        btn_layout = QHBoxLayout()
        main_layout.addLayout(btn_layout)
        self.btn_save = QPushButton("Сохранить")
        self.btn_save.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #555;
                color: #888;
                border: 1px solid #444;
            }
        """)
        btn_cancel = QPushButton("Отмена")
        self.btn_save.clicked.connect(self.save_dialog)
        def cancel_all():
            EDIT_BUFFER.clear()
            self.close()
        btn_cancel.clicked.connect(cancel_all)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(btn_cancel)
        self.check_save_enabled()

    def generate_phrase_name(self, dialog_id):
        loader = self.loader

        used = set()

        # собираем все ключи фраз
        for d in loader.dialogs.values():
            for phrase in d["xml_node"].findall(".//phrase"):
                t = phrase.find("text")
                if t is not None and t.text:
                    used.add(t.text.strip())

        # ищем свободное имя
        idx = 0
        while True:
            candidate = f"{dialog_id}_{idx}"
            if candidate not in used:
                return candidate
            idx += 1

    def generate_locale_key(self, phrase_name):
        loader = self.loader

        used = set(loader.text_loader.localization.keys())

        idx = 0
        while True:
            candidate = f"{phrase_name}_text"
            if candidate not in used:
                return candidate
            idx += 1


    def render_section(self, section_name, xml_tag, commit_func):
        lst = self.dialog_data.get(section_name)
        if not lst:
            return
        grid = self.grid
        row = self.current_row
        for i, value in enumerate(lst):
            lbl = EditableLabel(
                value,
                grid,
                lambda v, idx=i: commit_func(idx, v),
                self,
                xml_tag
            )
            self.validated_labels.append((lbl, xml_tag))
            combo = TagCombo(self, xml_tag, value, lbl)
            grid.addWidget(combo, row, 0)
            grid.addWidget(make_vline(), row, 1)
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
                self.check_save_enabled()
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

    def commit_init_func(self, index, val):
        lst = self.dialog_data["init_func"]
        old = self.active_editor.old_value
        try:
            real_index = lst.index(old)
            lst[real_index] = val.strip()
        except ValueError:
            pass

    def redraw_plus_button(self):
        # Удаляем старый плюсик
        for i in range(self.grid.count()):
            w = self.grid.itemAt(i).widget()
            if isinstance(w, AddButton):
                w.setParent(None)
                break

        # Ставим новый плюсик внизу
        add_btn = AddButton(self.add_new_param)
        self.grid.addWidget(add_btn, self.current_row, 3)

    def add_new_param(self):
        grid = self.grid
        row = self.current_row

        lbl = EditableLabel(
            "",
            grid,
            lambda v: None,
            self,
            None
        )
        self.validated_labels.append((lbl, "precondition"))

        combo = TagCombo(self, None, None, lbl)
        combo.setCurrentText("Precondition")
        grid.addWidget(combo, row, 0)
        grid.addWidget(make_vline(), row, 1)

        def delete_new():
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
            combo.setParent(None)
            lbl.setParent(None)
            del_btn.setParent(None)

            self.new_rows = [
                r for r in self.new_rows
                if r["combo"] is not combo or r["label"] is not lbl
            ]

            self.check_save_enabled()

            # Перерисовать плюсик после удаления
            self.redraw_plus_button()

        del_btn = DeleteButton(delete_new)

        grid.addWidget(lbl, row, 2)
        grid.addWidget(del_btn, row, 3)

        row += 1
        grid.addWidget(make_line(), row, 0, 1, 4)
        row += 1

        self.current_row = row
        self.new_rows.append({"combo": combo, "label": lbl})

        self.check_save_enabled()

        # Переместить плюсик вниз
        self.redraw_plus_button()

    def rename_dialog_id(self, old_id, new_id):
        loader = self.loader

        # 1. Меняем ID в dialog_data
        self.dialog_data["id"] = new_id

        # 2. Меняем ID в XML
        entry = loader.dialogs.get(old_id)
        if not entry:
            print("[ERROR] Cannot rename dialog: entry not found")
            return

        xml_path = entry["xml_path"]

        try:
            with open(xml_path, "r", encoding="cp1251", errors="ignore") as f:
                lines = f.readlines()

            new_lines = []
            for line in lines:
                # заменяем id="old_id" → id="new_id"
                new_lines.append(line.replace(f'id="{old_id}"', f'id="{new_id}"'))

            with open(xml_path, "w", encoding="cp1251", errors="ignore") as f:
                f.writelines(new_lines)

            print(f"[OK] Dialog ID renamed: {old_id} → {new_id}")

        except Exception as e:
            print(f"[ERROR] rename_dialog_id: {e}")
            return

        # 3. Перезагружаем диалоги
        loader._load_dialogs()

        # 4. Обновляем список диалогов в GUI
        mw = self.parent()
        mw.dialog_constructor.load_dialogs()

    def save_dialog(self):
        mw = self.parent()
        loader = mw.res_loader

        old_id = self.dialog_id
        new_id = self.name_edit.text().strip()

        # --- Проверка уникальности имени диалога ---
        if new_id in loader.dialogs and new_id != old_id:
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Имя занято")
            msg.setText(f"Диалог с именем '{new_id}' уже существует.")
            msg.setInformativeText("Введите другое имя.")
            msg.exec()
            return

        # --- Переименование диалога ---
        if new_id != old_id:
            print(f"[RENAME] {old_id} → {new_id}")
            self.rename_dialog_id(old_id, new_id)
            self.dialog_id = new_id
            self.dialog_data["id"] = new_id
            loader._load_dialogs()
            entry = loader.dialogs.get(new_id)
            if entry:
                self.xml_path = entry["xml_path"]

        # --- Пересчёт первой фразы ---
        base = self.dialog_id

        if self.dialog_data.get("phrase_list"):
            idx = 0
            phrase_id = f"{base}_{idx}"
            locale_key = f"{phrase_id}_text"

            self.dialog_data["phrase_list"][0]["id"] = phrase_id
            self.dialog_data["phrase_list"][0]["text"] = locale_key

        dialog_id = self.dialog_id

        # ============================================================
        #   СОХРАНЕНИЕ НОВОГО ДИАЛОГА
        # ============================================================
        if self.is_new:
            
            # --- показываем прогресс ---
            dlg_prog = DialogReloadProgress(self)
            dlg_prog.center_on_parent()
            dlg_prog.show()
            QApplication.processEvents()
            loader._load_dialogs()
            dlg_prog.close()

            self.append_dialog_to_constructor_file()
            dialog_entry = loader.dialogs.get(dialog_id)
            if dialog_entry:
                xml_path = dialog_entry["xml_path"]

                try:
                    with open(xml_path, "r", encoding="cp1251", errors="ignore") as f:
                        lines = f.readlines()

                    start = None
                    pattern = re.compile(r'<dialog\b[^>]*\bid="' + re.escape(dialog_id) + r'"')
                    for i, line in enumerate(lines):
                        if pattern.search(line):
                            start = i
                            break

                    if start is not None and self.new_rows:
                        if start + 1 < len(lines):
                            indent_match = re.match(r'^(\s*)', lines[start + 1])
                        else:
                            indent_match = re.match(r'^(\s*)', lines[start])
                        indent = indent_match.group(1) if indent_match else "    "

                        new_lines = []
                        for row in self.new_rows:
                            combo = row["combo"]
                            label = row["label"]
                            gui_tag = combo.currentText()
                            xml_tag = TAG_MAP.get(gui_tag)
                            if xml_tag is None:
                                continue

                            param_value = label.text().strip()
                            if not param_value:
                                continue

                            new_lines.append(f"{indent}<{xml_tag}>{param_value}</{xml_tag}>\n")

                        insert_pos = start + 1
                        lines[insert_pos:insert_pos] = new_lines

                        with open(xml_path, "w", encoding="cp1251", errors="ignore") as f:
                            f.writelines(lines)

                except Exception as e:
                    print(f"[ERROR] Cannot insert properties into new dialog: {e}")

            mw.dialog_constructor.load_dialogs()
            EDIT_BUFFER.clear()
            self.new_rows.clear()
            self.close()
            return

        # ============================================================
        #   СОХРАНЕНИЕ СТАРОГО ДИАЛОГА
        # ============================================================
        loader.save_dialog(dialog_id, self.dialog_data)

        # --- Вставка новых строк (preconditions, has_info, etc.) ---
        try:
            with open(self.xml_path, "r", encoding="cp1251", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            EDIT_BUFFER.clear()
            self.close()
            return

        dialog_start_idx = None
        pattern = re.compile(r'<dialog\b[^>]*\bid="' + re.escape(dialog_id) + r'"')

        for i, line in enumerate(lines):
            if pattern.search(line):
                dialog_start_idx = i
                break

        if dialog_start_idx is not None and self.new_rows:
            if dialog_start_idx + 1 < len(lines):
                indent_match = re.match(r'^(\s*)', lines[dialog_start_idx + 1])
            else:
                indent_match = re.match(r'^(\s*)', lines[dialog_start_idx])

            indent = indent_match.group(1) if indent_match else "    "

            new_lines = []
            for row in self.new_rows:
                combo = row["combo"]
                label = row["label"]
                gui_tag = combo.currentText()
                xml_tag = TAG_MAP.get(gui_tag)
                if xml_tag is None:
                    continue

                param_value = label.text().strip()
                if not param_value:
                    continue

                new_lines.append(f"{indent}<{xml_tag}>{param_value}</{xml_tag}>\n")

            insert_pos = dialog_start_idx + 1
            lines[insert_pos:insert_pos] = new_lines

            try:
                with open(self.xml_path, "w", encoding="cp1251", errors="ignore") as f:
                    f.writelines(lines)
            except Exception:
                pass

        EDIT_BUFFER.clear()
        self.new_rows.clear()
        self.close()

    def append_dialog_to_constructor_file(self):
        loader = self.parent().res_loader
        dialog_id = self.dialog_data["id"]

        # ============================================================
        #   Проверка уникальности ID диалога
        # ============================================================
        if dialog_id in loader.dialogs:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Ошибка")
            msg.setText(f"Диалог с именем '{dialog_id}' уже существует.")
            msg.setInformativeText("Введите другое имя.")
            msg.exec()
            return

        # ============================================================
        #   Путь к файлу constructor_dialogs.xml
        # ============================================================
        constructor_file = os.path.join(
            loader.paths["configs/gameplay"],
            "dialogs",
            "constructor_dialogs.xml"
        )

        # если файла нет — создаём пустой шаблон
        if not os.path.exists(constructor_file):
            content = (
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<game_dialogs>\n'
                '</game_dialogs>\n'
            )
            with open(constructor_file, "wb") as f:
                f.write(content.encode("utf-8"))

        # читаем как байты
        with open(constructor_file, "rb") as f:
            raw = f.read()

        end_tag = b"</game_dialogs>"
        pos = raw.find(end_tag)

        if pos == -1:
            print("[ERROR] Не найден </game_dialogs>")
            return

        # ============================================================
        #   Формируем блок диалога
        # ============================================================
        new_block = (
            b'  <dialog id="' + dialog_id.encode("ascii") + b'">\n'
            b'    <phrase_list>\n'
        )

        for phrase in self.dialog_data["phrase_list"]:
            pid = str(phrase["id"]).encode("ascii")
            text = phrase["text"].encode("utf-8")

            new_block += (
                b'      <phrase id="' + pid + b'">\n'
                b'        <text>' + text + b'</text>\n'
                b'      </phrase>\n'
            )

        new_block += (
            b'    </phrase_list>\n'
            b'  </dialog>\n'
        )

        # вставляем перед </game_dialogs>
        new_raw = raw[:pos] + new_block + raw[pos:]

        with open(constructor_file, "wb") as f:
            f.write(new_raw)

        print(f"[OK] Диалог {dialog_id} сохранён в constructor_dialogs.xml")

        # ============================================================
        #   СОЗДАНИЕ / ОБНОВЛЕНИЕ ФАЙЛА ЛОКАЛЕЙ (ручная запись)
        # ============================================================


        # ============================================================
        #   Перезагрузка диалогов
        # ============================================================
        loader._load_dialogs()


    def indent(self, elem, level=0):
        i = "\n" + level * "    "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "    "
            for child in elem:
                self.indent(child, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if not elem.text or not elem.text.strip():
                elem.text = ""
            if not elem.tail or not elem.tail.strip():
                elem.tail = i

    def check_save_enabled(self):
        print(f"[DEBUG] check_save_enabled called")
        for row in self.new_rows:
            label = row["label"]
            if label.text().strip() == "":
                print(f"[DEBUG] check_save_enabled: empty new row, disabling")
                self.btn_save.setEnabled(False)
                return
        for label, tag in self.validated_labels:
            if tag in ("precondition", "init_func"):
                text = label.text().strip()
                print(f"[DEBUG] check_save_enabled: checking label text={text!r}, tag={tag!r}")
                if text and self._has_label_error(text):
                    print(f"[DEBUG] check_save_enabled: error found, disabling")
                    self.btn_save.setEnabled(False)
                    return
        print(f"[DEBUG] check_save_enabled: enabling")
        self.btn_save.setEnabled(True)

    def _has_label_error(self, text):
        print(f"[DEBUG] _has_label_error: text={text!r}")
        if not self._validate_syntax(text):
            print(f"[DEBUG] _has_label_error: syntax error")
            return True
        func_name, arg_count = self._parse_function_call(text)
        print(f"[DEBUG] _has_label_error: func={func_name}, args={arg_count}, exists={func_name in self.loader.lua_functions}")
        if func_name not in self.loader.lua_functions:
            print(f"[DEBUG] _has_label_error: function not found")
            return True
        param_info = self.loader.lua_functions_params.get(func_name, {})
        has_varargs = param_info.get("has_varargs", False)
        param_count = param_info.get("count", 0)
        if not has_varargs and arg_count > param_count:
            print(f"[DEBUG] _has_label_error: too many args (expected {param_count}, got {arg_count})")
            return True
        print(f"[DEBUG] _has_label_error: no error")
        return False

    def on_editor_text_changed(self, editor, label):
        text = editor.text().strip()
        tag = label.tag
        print(f"[DEBUG] on_editor_text_changed: text={text!r}, tag={tag!r}")

        if tag not in ("precondition", "init_func"):
            editor.setStyleSheet("padding: 2px;")
            label.setStyleSheet("padding: 2px;")
            label.setToolTip("")
            self.check_save_enabled()
            return

        if not text:
            editor.setStyleSheet("padding: 2px;")
            label.setStyleSheet("padding: 2px;")
            label.setToolTip("")
            self.check_save_enabled()
            return

        if not self._validate_syntax(text):
            editor.setStyleSheet("color: #ff5252; padding: 2px;")
            label.setStyleSheet("color: #ff5252; padding: 2px;")
            label.setToolTip("Ошибка синтаксиса: проверьте пробелы и кавычки (допустимы только одинарные)")
        else:
            func_name, arg_count = self._parse_function_call(text)
            if func_name not in self.loader.lua_functions:
                editor.setStyleSheet("color: #ff5252; padding: 2px;")
                label.setStyleSheet("color: #ff5252; padding: 2px;")
                label.setToolTip("Функция не найдена: проверьте правильность написания файла/функции")
            else:
                param_info = self.loader.lua_functions_params.get(func_name, {})
                has_varargs = param_info.get("has_varargs", False)
                param_count = param_info.get("count", 0)
                if not has_varargs and arg_count > param_count:
                    editor.setStyleSheet("color: #ff5252; padding: 2px;")
                    label.setStyleSheet("color: #ff5252; padding: 2px;")
                    label.setToolTip(f"Превышено количество аргументов: функция ожидает {param_count}, передано {arg_count}")
                else:
                    editor.setStyleSheet("color: #a5d6a7; padding: 2px;")
                    label.setStyleSheet("color: #a5d6a7; padding: 2px;")
                    label.setToolTip("")

        self.check_save_enabled()

    def revalidate_label(self, label):
        text = label.text().strip()
        tag = label.tag

        if tag not in ("precondition", "init_func"):
            label.setStyleSheet("padding: 2px;")
            label.setToolTip("")
            return

        if not text:
            label.setStyleSheet("padding: 2px;")
            label.setToolTip("")
            return

        if not self._validate_syntax(text):
            label.setStyleSheet("color: #ff5252; padding: 2px;")
            label.setToolTip("Ошибка синтаксиса: проверьте пробелы и кавычки (допустимы только одинарные)")
        else:
            func_name, arg_count = self._parse_function_call(text)
            if func_name not in self.loader.lua_functions:
                label.setStyleSheet("color: #ff5252; padding: 2px;")
                label.setToolTip("Функция не найдена: проверьте правильность написания файла/функции")
            else:
                param_info = self.loader.lua_functions_params.get(func_name, {})
                has_varargs = param_info.get("has_varargs", False)
                param_count = param_info.get("count", 0)
                if not has_varargs and arg_count > param_count:
                    label.setStyleSheet("color: #ff5252; padding: 2px;")
                    label.setToolTip(f"Превышено количество аргументов: функция ожидает {param_count}, передано {arg_count}")
                else:
                    label.setStyleSheet("color: #a5d6a7; padding: 2px;")
                    label.setToolTip("")

    @staticmethod
    def _validate_syntax(text):
        stripped = text.strip()

        if stripped != text:
            return False

        if "(" in stripped:
            if not stripped.endswith(")"):
                return False

            paren_index = stripped.index("(")
            func_name_part = stripped[:paren_index]
            func_name = func_name_part.strip()

            if func_name_part != func_name:
                return False

            if " " in func_name:
                return False

            args_str = stripped[paren_index + 1:-1]

            if not func_name:
                return False

            if args_str.strip():
                args = [args_str]
                in_string = False
                string_char = None
                result = []
                for char in args_str:
                    if char in ('"', "'") and not in_string:
                        in_string = True
                        string_char = char
                        result.append(char)
                    elif char == string_char and in_string:
                        in_string = False
                        string_char = None
                        result.append(char)
                    elif char == ',' and not in_string:
                        result.append('\x00')
                    else:
                        result.append(char)
                split_args = ''.join(result).split('\x00')

                for arg in split_args:
                    arg = arg.strip()
                    if not arg:
                        return False
                    if not (arg.startswith("'") and arg.endswith("'") and len(arg) > 2):
                        return False
                    inner = arg[1:-1]
                    if '"' in inner:
                        return False
                    if "'" in inner:
                        return False

                return True
            else:
                return False
        else:
            return True

    @staticmethod
    def _parse_function_call(text):
        if "(" in text and text.endswith(")"):
            paren_index = text.index("(")
            func_name = text[:paren_index].strip()
            args_str = text[paren_index + 1:-1]

            if not args_str.strip():
                return func_name, 0

            arg_count = 1
            in_string = False
            string_char = None
            for char in args_str:
                if char in ('"', "'") and not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char and in_string:
                    in_string = False
                    string_char = None
                elif char == ',' and not in_string:
                    arg_count += 1

            return func_name, arg_count
        else:
            return text.strip(), 0

    def cancel_edit(self):
        editor = self.active_editor
        label = self.active_label
        print(f"[DEBUG] cancel_edit: editor={editor}, label={label}")
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
        print(f"[DEBUG] cancel_edit: about to revalidate label={label}, text={label.text()!r}, tag={label.tag}")
        self.revalidate_label(label)
        print(f"[DEBUG] cancel_edit: after revalidate, style={label.styleSheet()!r}")
        self.check_save_enabled()

    def finish_edit_external(self):
        if self.active_editor is not None and self.active_label is not None:
            self.active_label.finish_edit(self.active_editor)

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
    npc_dir = os.path.join(gameplay_path, "specific_characters_files")
    if not os.path.exists(npc_dir):
        return None
    re_char_start = re.compile(r'\s*<specific_character\b[^>]*id="([^"]+)"', re.IGNORECASE)
    re_actor = re.compile(r'<actor_dialog>(.*?)</actor_dialog>', re.IGNORECASE)
    re_start = re.compile(r'<start_dialog>(.*?)</start_dialog>', re.IGNORECASE)
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
            m_start = re_char_start.search(line)
            if m_start:
                inside_character = True
                current_npc_id = m_start.group(1)
                continue
            if inside_character and "</specific_character>" in line:
                inside_character = False
                current_npc_id = None
                continue
            if not inside_character:
                continue
            m_actor = re_actor.search(line)
            if m_actor and m_actor.group(1) == dialog_id:
                return current_npc_id
            m_start_d = re_start.search(line)
            if m_start_d and m_start_d.group(1) == dialog_id:
                return current_npc_id
    return None
