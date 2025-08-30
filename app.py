from PyQt6 import QtWidgets
from lampshade.main_window import MainWindow


def main():
    app = QtWidgets.QApplication([])
    w = MainWindow()
    w.resize(1300, 900)
    w.show()
    app.exec()


if __name__ == "__main__":
    main()