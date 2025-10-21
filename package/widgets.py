from PySide6.QtWidgets import (QMenuBar, QMainWindow, QMenu, QTableWidget,
                               QWidget, QVBoxLayout, QFileDialog,
                               QTableWidgetItem, QStyledItemDelegate,
                               QPlainTextEdit, QHeaderView)
from PySide6.QtCore import (QSize, QSettings, Qt, QModelIndex,
                            QAbstractItemModel, QRect)
from PySide6.QtGui import QKeySequence, QAction
from package.functions import read_file, write_data_to_file


class MainWindow(QMainWindow):
    window_title = 'FmgEditor'
    owner = 'Exsodium'

    def __init__(self) -> QMainWindow:
        super().__init__(
            size=QSize(600, 800),
            minimumSize=QSize(400, 400),
            windowTitle=self.window_title
        )

        self.settings = QSettings(self.owner, self.window_title)
        geometry = self.settings.value('geometry')

        if geometry:
            self.restoreGeometry(geometry)

        menu_bar = QMenuBar()
        file_menu = FileMenu(self)
        language_menu = LanguageMenu()
        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(language_menu)
        self.setMenuBar(menu_bar)

    def closeEvent(self, event) -> None:
        self.settings.setValue('geometry', self.saveGeometry())
        super().closeEvent(event)

    def add_file_name_to_window_title(self, file_name: str) -> None:
        self.setWindowTitle(f'{file_name} - {self.window_title}')

    def add_dot_to_window_title(self) -> None:
        self.setWindowTitle(f'• {self.windowTitle()}')


class FileMenu(QMenu):
    def __init__(self, parent: MainWindow) -> QMenu:
        super().__init__('&Файл', parent=parent)
        self.main_window = parent
        self.addAction(
            'Открыть файл...', self._on_open_file, shortcut=QKeySequence.StandardKey.Open)
        self.save_action: QAction = self.addAction(
            'Сохранить', self._on_save_file, shortcut=QKeySequence.StandardKey.Save)
        self.addSeparator()
        self.addAction('Выход', self._on_exit)

        self.save_action.setEnabled(False)

    def _on_open_file(self) -> None:
        last_directory = self.main_window.settings.value('last_directory')

        file_path, _ = QFileDialog.getOpenFileUrl(
            caption='Открыть файл',
            filter='Fmg (*.fmg)',
            dir=last_directory
        )

        if file_path.isEmpty():
            return

        file_name = file_path.fileName()
        self.main_window.add_file_name_to_window_title(file_name)

        file_url = file_path.url()
        self.main_window.settings.setValue('last_directory', file_url)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.table = Table()
        layout.addWidget(self.table)
        self.main_window.setCentralWidget(central_widget)

        self.file_path = file_path.path()[1:]
        self.table.load_data_from_file(self.file_path)
        self.table.resizeRowsToContents()
        self.table.resizeColumnsToContents()

        self.save_action.setEnabled(False)

    def _on_save_file(self) -> None:
        data = {}

        for i in range(self.table.rowCount()):
            id = self.table.item(i, 0).text()
            text = self.table.item(i, 1).text()

            data[id] = text

        write_data_to_file(data, self.file_path)

        self.main_window.setWindowTitle(self.main_window.windowTitle()[2:])
        self.save_action.setEnabled(False)

    def _on_exit(self) -> None:
        self.main_window.close()

    def set_save_action_enabled(self) -> None:
        self.save_action.setEnabled(True)


class Table(QTableWidget):
    def __init__(self) -> QTableWidget:
        super().__init__()
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['ID', 'Текст'])
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setMinimumSectionSize(40)
        self.horizontalHeader().setFixedHeight(20)
        self.horizontalHeader().setStretchLastSection(True)

        self.verticalHeader().setMinimumSectionSize(12)
        self.verticalHeader().setDefaultSectionSize(20)

        self.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)

        self.setStyleSheet('QHeaderView::section{background-color:Snow}')
        self.setItemDelegate(PlainTextEditDelegate(self))

    def load_data_from_file(self, file_path: str) -> None:
        data = read_file(file_path)

        for key, value in data.items():
            id = QTableWidgetItem(key)
            text = QTableWidgetItem(value)

            row_index = self.rowCount()
            self.insertRow(row_index)
            self.setItem(row_index, 0, id)
            self.setItem(row_index, 1, text)


class PlainTextEditDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QPlainTextEdit(parent)
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        editor.keyPressEvent = self._create_key_press_handler(editor)

        return editor

    def setEditorData(self, editor: QPlainTextEdit, index: QModelIndex):
        value = index.data(Qt.ItemDataRole.EditRole)
        editor.setPlainText(str(value))

    def setModelData(self, editor: QPlainTextEdit, model: QAbstractItemModel, index: QModelIndex):
        old_value: str = index.data(Qt.ItemDataRole.EditRole)
        new_value = editor.toPlainText()

        model.setData(index, new_value, Qt.ItemDataRole.EditRole)
        main_window: MainWindow = self.parent().parent().parent()
        menu: FileMenu = main_window.menuWidget().actions()[0].menu()

        if old_value != new_value:
            if not ('•' in main_window.windowTitle()):
                main_window.add_dot_to_window_title()
            menu.set_save_action_enabled()
        else:
            print('Same')

    def updateEditorGeometry(self, editor: QPlainTextEdit, option, index):
        rect: QRect = option.rect
        rect.setHeight(rect.height() + 10)
        editor.setGeometry(rect)

    def _create_key_press_handler(self, editor: QPlainTextEdit):
        original_key_press_event = editor.keyPressEvent

        def custom_key_press_event(event):
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                self.commitData.emit(editor)
                self.closeEditor.emit(
                    editor, QStyledItemDelegate.EndEditHint.SubmitModelCache)
                return

            original_key_press_event(event)

        return custom_key_press_event


class LanguageMenu(QMenu):
    def __init__(self) -> QMenu:
        super().__init__('&Язык')
        self.addAction('Английский')
        self.addAction('Русский')
