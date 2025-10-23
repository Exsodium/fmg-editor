from PySide6.QtWidgets import (QMenuBar, QMainWindow, QMenu, QTableWidget,
                               QWidget, QVBoxLayout, QFileDialog,
                               QTableWidgetItem, QStyledItemDelegate,
                               QPlainTextEdit, QHeaderView, QApplication,
                               QMessageBox, QPushButton)
from PySide6.QtCore import (QSize, QSettings, Qt, QModelIndex,
                            QAbstractItemModel, QRect, QCoreApplication,
                            QTranslator)
from PySide6.QtGui import QKeySequence, QAction, QActionGroup
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

        self.translator = QTranslator()
        self.language = self.settings.value('language', 'en')

        menu_bar = QMenuBar()
        self.file_menu = FileMenu(self)
        language_menu = LanguageMenu(self)
        menu_bar.addMenu(self.file_menu)
        menu_bar.addMenu(language_menu)
        self.setMenuBar(menu_bar)

    def closeEvent(self, event) -> None:
        window_title = self.windowTitle()
        if '•' in window_title:
            file_name = window_title[2:window_title.find('.fmg') + 4]
            message_box = QMessageBox(
                parent=self,
                text=f'{QApplication.translate('Message box', 'Text')} {file_name}?',
                icon=QMessageBox.Icon.Warning
            )
            message_box.setWindowTitle(self.window_title)

            save_button = QPushButton(
                QApplication.translate('Message box', '&Save'))
            discard_button = QPushButton(
                QApplication.translate('Message box', '&Don\'t Save'))
            cancel_button = QPushButton(
                QApplication.translate('Message box', '&Cancel'))

            message_box.addButton(
                save_button, QMessageBox.ButtonRole.AcceptRole)
            message_box.addButton(
                discard_button, QMessageBox.ButtonRole.DestructiveRole)
            message_box.addButton(
                cancel_button, QMessageBox.ButtonRole.RejectRole)
            message_box.setDefaultButton(save_button)

            message_box.exec()

            clicked_button = message_box.clickedButton()

            if clicked_button == save_button:
                self.file_menu._on_save_file()
            elif clicked_button == discard_button:
                pass
            else:
                event.ignore()
                return

        self.settings.setValue('geometry', self.saveGeometry())
        super().closeEvent(event)

    def apply_language(self, language_code: str) -> None:
        QApplication.removeTranslator(self.translator)

        if self.translator.load(f'translations\\{language_code}.qm'):
            QApplication.installTranslator(self.translator)
            self.language = language_code

            self.settings.setValue('language', language_code)
            self.retranslate_ui()

    def retranslate_ui(self) -> None:
        for action in self.menuBar().actions():
            action.menu().retranslate_menu()

        central_widget = self.centralWidget()

        if central_widget:
            table: Table = self.centralWidget().children()[-1]
            table.retranslate_table()

    def add_file_name_to_window_title(self, file_name: str) -> None:
        self.setWindowTitle(f'{file_name} - {self.window_title}')

    def add_dot_to_window_title(self) -> None:
        self.setWindowTitle(f'• {self.windowTitle()}')


class LanguageMenu(QMenu):
    def __init__(self, parent: MainWindow) -> QMenu:
        super().__init__(parent)
        self.main_window = parent
        language_group = QActionGroup(self)
        language_group.setExclusive(True)

        language_codes = ['en', 'ru']

        for language_code in language_codes:
            action = self.addAction(str())
            action.setCheckable(True)
            action.setData(language_code)
            language_group.addAction(action)

            if language_code == self.main_window.settings.value('language'):
                action.setChecked(True)

            action.triggered.connect(self._on_language_selected)

        self.apply_language(self.main_window.settings.value('language'))

    def _on_language_selected(self) -> None:
        action = self.sender()

        if action and action.isChecked():
            language_code = action.data()
            self.main_window.apply_language(language_code)

    def apply_language(self, language_code: str) -> None:
        translator = self.main_window.translator
        QApplication.removeTranslator(translator)

        if translator.load(f'translations\\{language_code}.qm'):
            QApplication.installTranslator(translator)
            self.retranslate_menu()

    def retranslate_menu(self) -> None:
        self.setTitle(QCoreApplication.translate(
            'Languages menu', '&Language'))
        lang_actions = self.actions()
        lang_actions[0].setText(QCoreApplication.translate(
            'Languages menu', '&English'))
        lang_actions[1].setText(QCoreApplication.translate(
            'Languages menu', '&Russian'))


class FileMenu(QMenu):
    def __init__(self, parent: MainWindow) -> QMenu:
        super().__init__(parent)
        self.main_window = parent
        self.addAction(str(), self._on_open_file,
                       shortcut=QKeySequence.StandardKey.Open)
        self.save_action: QAction = self.addAction(str(), self._on_save_file,
                                                   shortcut=QKeySequence.StandardKey.Save)
        self.save_action.setEnabled(False)

        self.addSeparator()
        self.addAction(str(), self._on_exit)

        self.apply_language(self.main_window.settings.value('language'))

    def _on_open_file(self) -> None:
        last_directory = self.main_window.settings.value('last_directory')

        file_path, _ = QFileDialog.getOpenFileUrl(
            caption=QCoreApplication.translate('File dialog', 'Open file'),
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
        self.table = Table(self.main_window)
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

    def apply_language(self, language_code: str) -> None:
        translator = self.main_window.translator
        QApplication.removeTranslator(translator)

        if translator.load(f'translations\\{language_code}.qm'):
            QApplication.installTranslator(translator)
            self.retranslate_menu()

    def retranslate_menu(self) -> None:
        self.setTitle(QCoreApplication.translate(
            'File menu', '&File'))
        file_actions = self.actions()
        file_actions[0].setText(QCoreApplication.translate(
            'File menu', '&Open'))
        file_actions[1].setText(QCoreApplication.translate(
            'File menu', '&Save'))
        file_actions[3].setText(QCoreApplication.translate(
            'File menu', '&Exit'))


class Table(QTableWidget):
    def __init__(self, parent: MainWindow) -> QTableWidget:
        super().__init__(parent)
        self.main_window = parent
        self.setColumnCount(2)
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

        self.apply_language(self.main_window.settings.value('language'))

    def load_data_from_file(self, file_path: str) -> None:
        data = read_file(file_path)

        for key, value in data.items():
            id = QTableWidgetItem(key)
            text = QTableWidgetItem(value)

            row_index = self.rowCount()
            self.insertRow(row_index)
            self.setItem(row_index, 0, id)
            self.setItem(row_index, 1, text)

    def apply_language(self, language_code: str) -> None:
        translator = self.main_window.translator
        QApplication.removeTranslator(translator)

        if translator.load(f'translations\\{language_code}.qm'):
            QApplication.installTranslator(translator)
            self.retranslate_table()

    def retranslate_table(self) -> None:
        self.setHorizontalHeaderLabels(
            ['ID', QCoreApplication.translate('Table headers', 'Text')])


class PlainTextEditDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index) -> QPlainTextEdit:
        editor = QPlainTextEdit(parent)
        editor.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editor.keyPressEvent = self._create_key_press_handler(editor)

        return editor

    def setEditorData(self, editor: QPlainTextEdit, index: QModelIndex) -> None:
        value = index.data(Qt.ItemDataRole.EditRole)
        editor.setPlainText(str(value))

    def setModelData(self, editor: QPlainTextEdit, model: QAbstractItemModel, index: QModelIndex) -> None:
        old_value: str = index.data(Qt.ItemDataRole.EditRole)
        new_value = editor.toPlainText()

        model.setData(index, new_value, Qt.ItemDataRole.EditRole)
        main_window: MainWindow = self.parent().parent().parent()
        menu: FileMenu = main_window.menuWidget().actions()[0].menu()

        if old_value != new_value:
            if not ('•' in main_window.windowTitle()):
                main_window.add_dot_to_window_title()
            menu.set_save_action_enabled()

    def updateEditorGeometry(self, editor: QPlainTextEdit, option, index) -> None:
        rect: QRect = option.rect
        rect.setHeight(rect.height() + 10)
        editor.setGeometry(rect)

    def _create_key_press_handler(self, editor: QPlainTextEdit):
        original_key_press_event = editor.keyPressEvent

        def custom_key_press_event(event) -> None:
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                self.commitData.emit(editor)
                self.closeEditor.emit(
                    editor, QStyledItemDelegate.EndEditHint.SubmitModelCache)
                return

            original_key_press_event(event)

        return custom_key_press_event
