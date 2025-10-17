from PySide6.QtWidgets import QMenuBar, QMainWindow, QMenu, QTableWidget, QWidget, QVBoxLayout, QFileDialog, QTableWidgetItem, QHeaderView
from PySide6.QtCore import QSize, QSettings
from PySide6.QtGui import QKeySequence
from package.functions import read_file


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
        file_menu = Menu(self)
        menu_bar.addMenu(file_menu)
        self.setMenuBar(menu_bar)

    def closeEvent(self, event) -> None:
        self.settings.setValue('geometry', self.saveGeometry())
        super().closeEvent(event)

    def add_file_name_to_window_title(self, file_name: str) -> None:
        self.setWindowTitle(f'{file_name} - {self.window_title}')


class Menu(QMenu):
    def __init__(self, parent: MainWindow) -> QMenu:
        super().__init__('&Файл', parent=parent)
        self.addAction(
            'Открыть файл...', self._on_open_file, shortcut=QKeySequence.StandardKey.Open)
        self.addAction(
            'Сохранить', self._on_save_file, shortcut=QKeySequence.StandardKey.Save)

    def _on_open_file(self) -> None:
        parent: MainWindow = self.parent()

        file_path, _ = QFileDialog.getOpenFileUrl(
            caption='Открыть файл',
            filter='Fmg (*.fmg)',
            dir=parent.settings.value('last_directory')
        )

        if file_path.isEmpty():
            return

        file_name = file_path.fileName()
        parent.add_file_name_to_window_title(file_name)

        file_url = file_path.url()
        parent.settings.setValue('last_directory', file_url)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        table = Table()
        layout.addWidget(table)
        parent.setCentralWidget(central_widget)

        file_path = file_path.path()[1:]
        table.load_data_from_file(file_path)
        table.resizeRowsToContents()
        table.resizeColumnsToContents()

    def _on_save_file(self) -> None:
        print(QKeySequence.StandardKey.Save)


class Table(QTableWidget):
    def __init__(self) -> QTableWidget:
        super().__init__()
        self.verticalHeader().setVisible(False)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['ID', 'Текст'])
        self.resizeColumnsToContents()
        self.horizontalHeader().setMinimumSectionSize(40)
        self.horizontalHeader().setFixedHeight(20)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setMinimumSectionSize(12)
        self.verticalHeader().setDefaultSectionSize(20)
        self.setWordWrap(True)
        # self.verticalHeader().setSectionResizeMode(
        #     QHeaderView.ResizeMode.ResizeToContents)
        self.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.setStyleSheet("QHeaderView::section{background-color:Snow}")

    def load_data_from_file(self, file_path: str) -> None:
        data = read_file(file_path)

        for key, value in data.items():
            id = QTableWidgetItem(key)
            text = QTableWidgetItem(value)

            row_index = self.rowCount()
            self.insertRow(row_index)
            self.setItem(row_index, 0, id)
            self.setItem(row_index, 1, text)
