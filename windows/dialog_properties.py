from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QGridLayout, QFrame, QLineEdit
)
from PyQt6.QtCore import Qt, QObject, QEvent


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
    """QLineEdit, который не закрывает окно по Enter."""
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.clearFocus()   # фиксируем значение
            return              # НЕ закрываем окно
        super().keyPressEvent(event)


class ClickFilter(QObject):
    """Глобальный фильтр кликов — завершает редактирование."""
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
    """Кликабельный QLabel, превращающийся в QLineEdit."""
    def __init__(self, text, grid_layout, on_commit, dialog):
        super().__init__(text)
        self.grid = grid_layout
        self.on_commit = on_commit
        self.dialog = dialog
        self.setStyleSheet("padding: 2px;")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        self.start_edit()

    def start_edit(self):
        index = self.grid.indexOf(self)
        if index < 0:
            return

        row, col, _, _ = self.grid.getItemPosition(index)

        editor = EditLine(self.text())
        editor.setStyleSheet("padding: 2px;")
        editor.editingFinished.connect(lambda: self.finish_edit(editor))

        self.grid.removeWidget(self)
        self.hide()

        self.grid.addWidget(editor, row, col)
        editor.setFocus()

        self.dialog.active_editor = editor
        self.dialog.active_label = self

    def finish_edit(self, editor):
        new_value = editor.text()
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


class DialogProperties(QDialog):
    def __init__(self, parent, dialog_data):
        super().__init__(parent)

        self.dialog_data = dialog_data
        dialog_id = dialog_data["id"]

        self.active_editor = None
        self.active_label = None

        self.setWindowTitle(f"Свойства {dialog_id}")
        self.resize(550, 400)
        self.setWindowModality(Qt.WindowModality.WindowModal)

        # глобальный фильтр кликов
        self.filter = ClickFilter(self)
        self.installEventFilter(self.filter)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        grid = QGridLayout()
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 3)
        main_layout.addLayout(grid)

        row = 0

        # Путь (не редактируется)
        xml_path = dialog_data["xml_path"].replace("\\", "/")
        grid.addWidget(QLabel("Путь:"), row, 0)
        grid.addWidget(make_vline(), row, 1)
        grid.addWidget(QLabel(xml_path), row, 2)
        row += 1
        grid.addWidget(make_line(), row, 0, 1, 3)
        row += 1

        # Приоритет
        def commit_priority(val):
            try:
                self.dialog_data["priority"] = int(val)
            except:
                pass

        grid.addWidget(QLabel("Приоритет:"), row, 0)
        grid.addWidget(make_vline(), row, 1)
        grid.addWidget(EditableLabel(str(dialog_data["priority"]), grid, commit_priority, self), row, 2)
        row += 1
        grid.addWidget(make_line(), row, 0, 1, 3)
        row += 1

        # PRECONDITIONS
        if dialog_data["preconditions"]:
            def commit_pre(val):
                self.dialog_data["preconditions"] = [v.strip() for v in val.split(",")]

            grid.addWidget(QLabel("Preconditions:"), row, 0)
            grid.addWidget(make_vline(), row, 1)
            grid.addWidget(EditableLabel(", ".join(dialog_data["preconditions"]), grid, commit_pre, self), row, 2)
            row += 1
            grid.addWidget(make_line(), row, 0, 1, 3)
            row += 1

        # HAS_INFO
        if dialog_data["has_info"]:
            def commit_hi(val):
                self.dialog_data["has_info"] = [v.strip() for v in val.split(",")]

            grid.addWidget(QLabel("Has Info:"), row, 0)
            grid.addWidget(make_vline(), row, 1)
            grid.addWidget(EditableLabel(", ".join(dialog_data["has_info"]), grid, commit_hi, self), row, 2)
            row += 1
            grid.addWidget(make_line(), row, 0, 1, 3)
            row += 1

        # DONT_HAS_INFO
        if dialog_data["dont_has_info"]:
            def commit_dhi(val):
                self.dialog_data["dont_has_info"] = [v.strip() for v in val.split(",")]

            grid.addWidget(QLabel("Dont Has Info:"), row, 0)
            grid.addWidget(make_vline(), row, 1)
            grid.addWidget(EditableLabel(", ".join(dialog_data["dont_has_info"]), grid, commit_dhi, self), row, 2)
            row += 1
            grid.addWidget(make_line(), row, 0, 1, 3)
            row += 1

        main_layout.addStretch()

        btn_layout = QHBoxLayout()
        main_layout.addLayout(btn_layout)

        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)

    def finish_edit_external(self):
        """Завершение редактирования при клике вне поля."""
        if self.active_editor is not None:
            self.active_editor.clearFocus()

    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_screen()

    def center_on_screen(self):
        screen = self.screen().geometry()
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + (screen.height() - self.height()) // 2
        self.move(x, y)
