import sys
# from tempfile import gettempdir, mkstemp, tempdir
import shutil

# from PIL import Image
from PySide6.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QHBoxLayout, QScrollArea
from PySide6.QtGui import QPalette, QIcon, QImage
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

        # création de la scrollarea display
        display = QScrollArea()
        display.setBackgroundRole(QPalette.Dark)

        # création du widget photos
        photos = QWidget()
        display_layout = QHBoxLayout()
        display_layout.setSpacing(0)
        display_layout.addStretch()
        photos.setLayout(display_layout)

        # ici il faut construire (remplir) le widget photos

        for i in range(0, len(photos_test)):
            ph_name = f"./pictures/_DSC{photos_test[i]}.NEF"
            photo = Photo(ph_name)
            v = Thumbnails(photo)
            
            display_layout.addWidget(v)

        # ajouter photos à la scrollaera
        display.setWidget(photos)
        display.setWidgetResizable(True)

        # ajouter la scrollaera au layout principal (du central widget)
        main_layout.addWidget(display)
#################################################################################
#################################################################################
def main() -> bool:
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
