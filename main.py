from sys import exit
from PySide6.QtWidgets import QApplication
from widgets.widgets import MainWindow


def main() -> None:
    app = QApplication([])

    window = MainWindow()
    window.show()

    exit(app.exec())


if __name__ == "__main__":
    main()
