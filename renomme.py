import sys
import shutil

from PySide6.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget
from PySide6.QtGui import QIcon
from PySide6.QtCore import QFile, QTextStream, QIODevice

from constants import *
from sub import *
#################################################################################
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setUI()
#--------------------------------------------------------------------------------
    def setUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QGridLayout()
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)

        photos_test = (7986, 8064, 8080, 8081, 8084, 8134, 8135, 8145, 8146, 8147, 8148, 8149)

        # création de la scrollarea display
        self.display = Display()
        # création du widget photos
        photos = Photos(photos_test)
        # ajouter photos à la scrollaera
        self.display.setWidget(photos)
        self.display.setWidgetResizable(True)
        # ajouter la scrollaera au layout principal (du central widget)
        main_layout.addWidget(self.display)
#--------------------------------------------------------------------------------
def refresh_display(photo_list: list, ):
        pass
#################################################################################
#################################################################################
def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.setWindowIcon(QIcon('qt.png'))
    main_window.setFixedSize(MAIN_SIZE)
    main_window.setWindowTitle("Renommage des photos")
    
    f = QFile("./style.qss")
    f.open(QIODevice.ReadOnly)
    app.setStyleSheet(QTextStream(f).readAll())

    main_window.show()
    shutil.rmtree(TMP_DIR)
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
