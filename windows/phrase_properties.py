import os
import re
import xml.etree.ElementTree as ET

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QGridLayout, QComboBox, QSizePolicy, QFrame, QLineEdit
)
from PyQt6.QtCore import Qt, QEvent

# Глобальный буфер изменений
EDIT_BUFFER = []


def make_line():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    line.setStyleSheet("color: #444;")
    return line


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
        if self.rect().contains(event.position().toPoint()):
            self.clicked()


class PhraseProperties(QDialog):
    def __init__(self, parent, node):
        super().__init__(parent)
        self.node = node

        self.tag_map = {
            "Give info": "give_info",
            "Disable info": "disable_info",
            "Action": "action",
            "Precondition": "precondition",
            "Has info": "has_info",
            "Dont has info": "dont_has_info"
        }

        fm = self.fontMetrics()
        self.tag_column_width = max(
            fm.horizontalAdvance(name) for name in self.tag_map.keys()
        ) + 45

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle("Свойства фразы")
        self.resize(500, 300)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        header_grid = QGridLayout()
        header_grid.setColumnStretch(0, 1)

        title = QLabel(f"{node.text_key}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 6px;")
        title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        header_grid.addWidget(title, 0, 0)
        main_layout.addLayout(header_grid)

        main_layout.addWidget(make_line())

        self.props_container = QVBoxLayout()
        main_layout.addLayout(self.props_container)

        self.rows = []

        xml_rows = self.load_phrase_xml()

        if xml_rows:
            for tag, value in xml_rows:
                gui_name = next((k for k, v in self.tag_map.items() if v == tag), "Precondition")
                self.add_row(gui_name, tag, value)

        plus_row = QHBoxLayout()
        plus_row.addStretch()

        self.btn_plus = ClickableSquare("+",
            """
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
            """,
            """
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
        )
        self.btn_plus.clicked = self.add_empty_row
        plus_row.addWidget(self.btn_plus)

        self.props_container.addLayout(plus_row)

        main_layout.addStretch()

        btn_layout = QHBoxLayout()
        main_layout.addLayout(btn_layout)

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
            QPushButton:disabled {
                background-color: #555;
                color: #888;
                border: 1px solid #444;
            }
        """)
        btn_save.clicked.connect(self.save_phrase_xml)
        self.btn_save = btn_save
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)

        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.on_cancel)
        btn_layout.addWidget(btn_cancel)

        self.installEventFilter(self)

    def load_phrase_xml(self):
        mw = self.parent()
        while mw is not None and not hasattr(mw, "res_loader"):
            mw = mw.parent()

        if mw is None:
            return []

        loader = mw.res_loader

        raw_id = str(self.node.dialog_id)
        dialog_id = raw_id.split(":")[0]
        phrase_id = str(self.node.logic_id)

        if dialog_id not in loader.dialogs:
            return []

        dialog_node = loader.dialogs[dialog_id]["xml_node"]

        phrase_list = dialog_node.find("phrase_list")
        if phrase_list is None:
            return []

        phrases = phrase_list.findall("phrase")

        phrase_node = next((p for p in phrases if p.get("id") == phrase_id), None)
        if phrase_node is None:
            return []

        results = []
        for child in phrase_node:
            tag = child.tag
            if tag not in self.tag_map.values():
                continue
            value = (child.text or "").strip()
            results.append((tag, value))

        return results

    def _get_res_loader(self):
        mw = self.parent()
        while mw is not None and not hasattr(mw, "res_loader"):
            mw = mw.parent()
        return getattr(mw, "res_loader", None)

    def _update_row_color(self, row_container):
        loader = self._get_res_loader()
        if loader is None:
            return

        if not hasattr(loader, "lua_functions"):
            return

        edit = row_container.edit_edit
        label = row_container.edit_label
        text = edit.text().strip()

        xml_tag = row_container.edit_meta.get("new_tag")
        if xml_tag not in ("action", "precondition"):
            edit.setStyleSheet("color: white; background-color: #202020; padding-left: 10px;")
            label.setStyleSheet("color: #ccc; padding-left: 10px;")
            label.setToolTip("")
            edit.setToolTip("")
            return

        if not text:
            color = "white"
            label_color = "#ccc"
            tooltip = ""
        else:
            if not self._validate_syntax(text):
                color = "#ff5252"
                label_color = "#ff5252"
                tooltip = "Ошибка синтаксиса: проверьте пробелы и кавычки (допустимы только одинарные)"
            else:
                func_name, arg_count = self._parse_function_call(text)

                if func_name not in loader.lua_functions:
                    color = "#ff5252"
                    label_color = "#ff5252"
                    tooltip = "Функция не найдена: проверьте правильность написания файла/функции"
                else:
                    param_info = loader.lua_functions_params.get(func_name, {})
                    has_varargs = param_info.get("has_varargs", False)
                    param_count = param_info.get("count", 0)

                    if not has_varargs and arg_count > param_count:
                        color = "#ff5252"
                        label_color = "#ff5252"
                        tooltip = f"Превышено количество аргументов: функция ожидает {param_count}, передано {arg_count}"
                    else:
                        color = "#a5d6a7"
                        label_color = "#a5d6a7"
                        tooltip = ""

        edit.setStyleSheet(f"color: {color}; background-color: #202020; padding-left: 10px;")
        label.setStyleSheet(f"color: {label_color}; padding-left: 10px;")
        label.setToolTip(tooltip)
        edit.setToolTip(tooltip)
        self._update_save_button()

    def _has_errors(self):
        for row in self.rows:
            edit = row.edit_edit
            text = edit.text().strip()
            xml_tag = row.edit_meta.get("new_tag")

            if xml_tag in ("action", "precondition") and text:
                if not self._validate_syntax(text):
                    return True

                func_name, arg_count = self._parse_function_call(text)
                if func_name not in self._get_res_loader().lua_functions:
                    return True

                param_info = self._get_res_loader().lua_functions_params.get(func_name, {})
                has_varargs = param_info.get("has_varargs", False)
                param_count = param_info.get("count", 0)
                if not has_varargs and arg_count > param_count:
                    return True
        return False

    def _update_save_button(self):
        if not hasattr(self, "btn_save"):
            return
        self.btn_save.setEnabled(not self._has_errors())

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

    def _create_row_meta(self, xml_tag, param_value, is_new):
        # old_* всегда из XML до сохранения
        # new_* самообновляемые
        return {
            "old_tag": None if is_new else xml_tag,
            "old_param": None if is_new else (param_value or ""),
            "new_tag": xml_tag,
            "new_param": param_value or "",
            "registered": False
        }

    def _register_row_in_buffer(self, row_container):
        global EDIT_BUFFER
        meta = row_container.edit_meta
        if not meta["registered"]:
            EDIT_BUFFER.append(meta)
            meta["registered"] = True

    def add_row(self, gui_name="Precondition", xml_tag="precondition", param_value=""):
        row_container = QVBoxLayout()
        row = QHBoxLayout()

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

        vline = QFrame()
        vline.setFrameShape(QFrame.Shape.VLine)
        vline.setStyleSheet("color: #444;")
        row.addWidget(vline)

        edit_label = QLabel(param_value if param_value else "...")
        edit_label.setStyleSheet("color: #ccc; padding-left: 10px;")

        edit_edit = QLineEdit(param_value)
        edit_edit.setStyleSheet("color: white; background-color: #202020; padding-left: 10px;")
        edit_edit.hide()

        edit_edit.textChanged.connect(lambda text, rc=row_container: self._update_row_color(rc))

        # meta: is_new = True если строка создана плюсом
        is_new = (param_value == "" and xml_tag == "precondition" and gui_name == "Precondition")
        row_meta = self._create_row_meta(xml_tag, param_value, is_new)
        row_container.edit_meta = row_meta

        def label_mousePressEvent(event, label=edit_label, edit=edit_edit, rc=row_container):
            if event.button() == Qt.MouseButton.LeftButton:
                self._register_row_in_buffer(rc)
                label.hide()
                edit.show()
                edit.setFocus()
                edit.selectAll()

        edit_label.mousePressEvent = label_mousePressEvent

        def on_combo_changed(text, rc=row_container, combo=combo):
            self._register_row_in_buffer(rc)
            new_xml_tag = self.tag_map[text]
            rc.edit_meta["new_tag"] = new_xml_tag
            self._update_row_color(rc)

        combo.currentTextChanged.connect(on_combo_changed)

        row.addWidget(edit_label, 1)
        row.addWidget(edit_edit, 1)

        btn_del = ClickableSquare("−",
            """
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
            """,
            """
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
        )
        btn_del.clicked = lambda rc=row_container: self.delete_row(rc)
        row.addWidget(btn_del)

        row_container.addLayout(row)
        row_container.addWidget(make_line())

        row_container.edit_label = edit_label
        row_container.edit_edit = edit_edit
        row_container.combo = combo

        self.rows.append(row_container)
        self.props_container.insertLayout(len(self.rows) - 1, row_container)

        self._update_row_color(row_container)

    def add_empty_row(self):
        # новая строка, old_* пустые
        self.add_row()

    def delete_row(self, row_container):
        global EDIT_BUFFER

        if row_container in self.rows:
            self.rows.remove(row_container)

            meta = row_container.edit_meta

            # Если строка была в XML — добавляем запись на удаление
            if meta["old_tag"] is not None and meta["old_param"] is not None:
                EDIT_BUFFER.append({
                    "old_tag": meta["old_tag"],
                    "old_param": meta["old_param"],
                    "new_tag": None,
                    "new_param": None,
                    "delete": True
                })

            # Если строка была новой — просто удаляем
            if meta in EDIT_BUFFER:
                EDIT_BUFFER.remove(meta)

            # Удаляем виджеты
            while row_container.count():
                item = row_container.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self._delete_layout(item.layout())

            self._delete_layout(row_container)


    def _delete_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._delete_layout(item.layout())

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            pos = event.position().toPoint()

            for row in self.rows:
                edit = row.edit_edit
                label = row.edit_label

                if edit.isVisible():
                    if not edit.geometry().contains(pos):
                        text = edit.text().strip()
                        row.edit_meta["new_param"] = text
                        label.setText(text if text else "...")
                        self._update_row_color(row)
                        edit.hide()
                        label.show()

        return super().eventFilter(obj, event)

    def _finalize_all_edits(self):
        # закрываем все редакторы и фиксируем new_param
        for row in self.rows:
            edit = row.edit_edit
            label = row.edit_label
            if edit.isVisible():
                text = edit.text().strip()
                row.edit_meta["new_param"] = text
                label.setText(text if text else "...")
                self._update_row_color(row)
                edit.hide()
                label.show()

    def on_cancel(self):
        global EDIT_BUFFER
        EDIT_BUFFER.clear()
        self.close()

    def refresh_phrase(self):
        # Удаляем старые строки
        for row in self.rows:
            while row.count():
                item = row.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self._delete_layout(item.layout())
            self._delete_layout(row)

        self.rows.clear()

        # Перечитываем XML
        xml_rows = self.load_phrase_xml()

        # Создаём строки заново
        if xml_rows:
            for tag, value in xml_rows:
                gui_name = next((k for k, v in self.tag_map.items() if v == tag), "Precondition")
                self.add_row(gui_name, tag, value)

    def save_phrase_xml(self):
        global EDIT_BUFFER

        # 1) Закрываем все редакторы и фиксируем new_param
        self._finalize_all_edits()

        # 2) Проверка на пустые параметры
        for row in self.rows:
            meta = row.edit_meta
            if not meta.get("delete"):  # удалённые строки можно игнорировать
                if meta["new_param"].strip() == "":
                    print("[PhraseProperties] Параметр пуст — сохранение запрещено")
                    return

        # 3) Получаем loader
        mw = self.parent()
        while mw is not None and not hasattr(mw, "res_loader"):
            mw = mw.parent()

        if mw is None:
            print("[PhraseProperties] Нет res_loader — сохранить невозможно")
            return

        loader = mw.res_loader

        # 4) Идентификаторы
        raw_id = str(self.node.dialog_id)
        dialog_id = raw_id.split(":")[0]
        phrase_id = str(self.node.logic_id)

        if dialog_id not in loader.dialogs:
            print("[PhraseProperties] Диалог не найден")
            return

        xml_path = loader.dialogs[dialog_id]["xml_path"]

        # 5) Читаем файл построчно
        try:
            with open(xml_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"[PhraseProperties] Ошибка чтения {xml_path}: {e}")
            return

        # 6) Находим границы <dialog>
        start_dialog = None
        end_dialog = None

        pattern_dialog = rf'<dialog\s+[^>]*id="{dialog_id}"'
        for i, line in enumerate(lines):
            if re.search(pattern_dialog, line):
                start_dialog = i
                break

        if start_dialog is not None:
            for i in range(start_dialog + 1, len(lines)):
                if "</dialog>" in lines[i]:
                    end_dialog = i
                    break

        if start_dialog is None or end_dialog is None:
            print(f"[PhraseProperties] Не найдены границы dialog {dialog_id}")
            return

        # 7) Находим границы <phrase>
        start_phrase = None
        end_phrase = None

        pattern_phrase = rf'<phrase\s+[^>]*id="{phrase_id}"'
        for i in range(start_dialog, end_dialog + 1):
            if re.search(pattern_phrase, lines[i]):
                start_phrase = i
                break

        if start_phrase is not None:
            for i in range(start_phrase + 1, end_dialog + 1):
                if "</phrase>" in lines[i]:
                    end_phrase = i
                    break

        if start_phrase is None or end_phrase is None:
            print(f"[PhraseProperties] Не найдены границы phrase {phrase_id}")
            return

        # 8) Применяем EDIT_BUFFER
        for meta in EDIT_BUFFER:
            old_tag = meta["old_tag"]
            old_param = meta["old_param"]
            new_tag = meta["new_tag"]
            new_param = meta["new_param"]

            # === УДАЛЕНИЕ СТРОКИ ===
            if meta.get("delete"):
                old_line = f"<{old_tag}>{old_param}</{old_tag}>"
                found = False

                for i in range(start_phrase, end_phrase + 1):
                    if old_line in lines[i]:
                        lines.pop(i)
                        found = True
                        end_phrase -= 1
                        end_dialog -= 1
                        break

                if not found:
                    print(f"[PhraseProperties] Не удалось удалить строку '{old_line}'")
                continue

            # === РЕДАКТИРОВАНИЕ СТРОКИ ===
            if old_tag is not None and old_param is not None:
                old_line = f"<{old_tag}>{old_param}</{old_tag}>"
                new_line = f"<{new_tag}>{new_param}</{new_tag}>"

                found = False
                for i in range(start_phrase, end_phrase + 1):
                    if old_line in lines[i]:
                        lines[i] = lines[i].replace(old_line, new_line)
                        found = True
                        break

                if not found:
                    print(f"[PhraseProperties] Строка '{old_line}' не найдена для замены")
                continue

            # === НОВАЯ СТРОКА ===
            new_line = f"<{new_tag}>{new_param}</{new_tag}>"
            indent = "        "  # 8 пробелов, как обычно внутри <phrase>
            insert_index = end_phrase
            lines.insert(insert_index, indent + new_line + "\n")
            end_phrase += 1
            end_dialog += 1

        # 9) Записываем файл
        with open(xml_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"[PhraseProperties] Сохранено: {xml_path}")

        # 10) Перезагружаем диалог в ResourceLoader
        loader.reload_dialog(dialog_id)

        # 11) Очищаем буфер и обновляем GUI
        EDIT_BUFFER.clear()
        self.refresh_phrase()
        self.close()
