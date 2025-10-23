from sys import exit
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from package.widgets import MainWindow


def main() -> None:
    app = QApplication([])
    app.setWindowIcon(QIcon('icon.ico'))

    window = MainWindow()
    window.show()

    exit(app.exec())


if __name__ == "__main__":
    main()
