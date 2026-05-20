from pathlib import Path

from PySide6.QtCore import QRect, QSettings, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QHeaderView,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from fmg import read_fmg, write_fmg


class MainWindow(QMainWindow):
    app_name: str = 'FmgEditor'
    owner: str = 'Exsodium'

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(self.app_name)
        self.setMinimumSize(400, 400)
        self.resize(600, 800)

        self.settings = QSettings(self.owner, self.app_name)
        geometry = self.settings.value('geometry')

        if geometry:
            self.restoreGeometry(geometry)

        menu_bar = QMenuBar(self)
        self.file_menu = FileMenu(menu_bar, self)
        menu_bar.addMenu(self.file_menu)
        self.setMenuBar(menu_bar)

    def closeEvent(self, event) -> None:
        window_title = self.windowTitle()

        if '•' in window_title:
            file_name = window_title.split(' ')[1]
            message_box = QMessageBox(
                QMessageBox.Icon.Warning,
                self.app_name,
                f'Want to save your changes to {file_name}?',
                parent=self)

            save_button = QPushButton('Save')
            dont_save_button = QPushButton('Don\'t Save')
            cancel_button = QPushButton('Cancel')

            message_box.addButton(save_button, QMessageBox.ButtonRole.AcceptRole)
            message_box.addButton(dont_save_button, QMessageBox.ButtonRole.DestructiveRole)
            message_box.addButton(cancel_button, QMessageBox.ButtonRole.RejectRole)
            message_box.setDefaultButton(save_button)
            message_box.exec()

            clicked_button = message_box.clickedButton()

            if clicked_button == save_button:
                self.file_menu._on_save_file()
            elif clicked_button == dont_save_button:
                pass
            else:
                event.ignore()
                return

        self.settings.setValue('geometry', self.saveGeometry())
        super().closeEvent(event)

    def add_file_name_to_window_title(self, file_name: str) -> None:
        self.setWindowTitle(f'{file_name} - {self.app_name}')

    def add_dot_to_window_title(self) -> None:
        self.setWindowTitle(f'• {self.windowTitle()}')

class FileMenu(QMenu):
    def __init__(self, parent: QMenuBar, main_window: MainWindow) -> None:
        super().__init__('File', parent)
        self.main_window = main_window

        open_action = QAction('Open', parent=self, shortcut=QKeySequence(QKeySequence.StandardKey.Open))
        self.save_action = QAction('Save', parent=self, enabled=False, shortcut=QKeySequence(QKeySequence.StandardKey.Save))
        exit_action = QAction('Exit', parent=self)

        open_action.triggered.connect(self._on_open_file)
        self.save_action.triggered.connect(self._on_save_file)
        exit_action.triggered.connect(self._on_exit)

        self.addAction(open_action)
        self.addAction(self.save_action)
        self.addSeparator()
        self.addAction(exit_action)

    def _on_open_file(self) -> None:
        directory = self.main_window.settings.value('dir', '')
        directory = str(directory)

        path, _ = QFileDialog.getOpenFileName(
            caption='Open file',
            filter='Fmg files (*.fmg)',
            dir=directory
        )

        if not path:
            return

        self.path = Path(path)
        directory = str(self.path.parent)
        self.main_window.add_file_name_to_window_title(self.path.name)
        self.main_window.settings.setValue('dir', directory)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.table = Table(central_widget)

        self.main_window.setCentralWidget(central_widget)
        layout.addWidget(self.table)

        data = read_fmg(self.path)
        self.table.fill(data)

        self.save_action.setEnabled(False)

    def _on_save_file(self) -> None:
        data = []

        for i in range(self.table.rowCount()):
            id = self.table.item(i, 0).text()  # pyright: ignore [reportOptionalMemberAccess]
            text = self.table.item(i, 1).text()  # pyright: ignore [reportOptionalMemberAccess]

            data.append((int(id), text))

        data = tuple(data)
        write_fmg(data, self.path)

        self.main_window.setWindowTitle(self.main_window.windowTitle()[2:])
        self.save_action.setEnabled(False)

    def _on_exit(self) -> None:
        self.main_window.close()

    def set_save_action_enabled(self) -> None:
        self.save_action.setEnabled(True)

class Table(QTableWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setColumnCount(2)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setMinimumSectionSize(12)
        self.verticalHeader().setDefaultSectionSize(20)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        self.setHorizontalHeaderLabels(['ID', 'Text'])
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setFixedHeight(20)
        self.horizontalHeader().setMinimumSectionSize(40)

        self.setStyleSheet('QHeaderView::section{background-color:White}')
        self.setItemDelegate(PlainTextEditDelegate(self))

    def fill(self, data: tuple[tuple[int, str], ...]):
        for id_, text in data:
            index = self.rowCount()
            self.insertRow(index)
            self.setItem(index, 0, QTableWidgetItem(str(id_)))
            self.setItem(index, 1, QTableWidgetItem(text))

        self.resizeRowsToContents()
        self.resizeColumnsToContents()

class PlainTextEditDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index) -> QPlainTextEdit:
        editor = QPlainTextEdit(parent)
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        return editor

    def setEditorData(self, editor, index) -> None:
        value = index.data(Qt.ItemDataRole.EditRole)
        editor.setPlainText(str(value))

    def setModelData(self, editor, model, index) -> None:
        old_value: str = index.data(Qt.ItemDataRole.EditRole)
        new_value = editor.toPlainText()
        model.setData(index, new_value, Qt.ItemDataRole.EditRole)

        current = self
        while current.parent():  # pyright: ignore [reportOptionalMemberAccess]
            current = current.parent()  # pyright: ignore [reportOptionalMemberAccess]

        main_window: MainWindow = current  # pyright: ignore [reportAssignmentType]
        menu = main_window.file_menu

        if old_value != new_value:
            if '•' not in main_window.windowTitle():
                main_window.add_dot_to_window_title()
            menu.set_save_action_enabled()

    def updateEditorGeometry(self, editor, option, index) -> None:
        rect: QRect = option.rect
        rect.setHeight(rect.height() + 8)
        editor.setGeometry(rect)
