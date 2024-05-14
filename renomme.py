import sys, os
import shutil

import rawpy

from PySide6.QtWidgets import QApplication, QMainWindow, QGridLayout, QVBoxLayout, QWidget
from PySide6.QtGui import QIcon
from PySide6.QtCore import QFile, QTextStream, QIODevice

from constants import *
from RenameCls import *
#################################################################################
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        ### seulement pour la mise au point
        ### only for the development phase --------------------------------------
        # will be from camera memory card in the final version
        # short list:
        photos_test_short = ('_DSC7986.NEF', '_DSC8064.NEF', '_DSC8080.NEF', '_DSC8081.NEF', '_DSC8084.NEF')
        # longer list: 
        photos_test_long = ('_DSC7986.NEF', '_DSC8064.NEF', '_DSC8080.NEF', '_DSC8081.NEF', '_DSC8084.NEF', '_DSC8134.NEF', '_DSC8135.NEF', '_DSC8145.NEF', '_DSC8146.NEF', '_DSC8147.NEF', '_DSC8148.NEF', '_DSC8149.NEF')
        self.photos_test = photos_test_short
        # development only ------------------------------------------------------
        self.eventFilter = KeyPressFilter(parent=self)
        self.installEventFilter(self.eventFilter)

        self.create_thumb_jpeg(self.photos_test)
        self.setUI()
        self.show_display()
#--------------------------------------------------------------------------------
    def create_thumb_jpeg(self, photos_test: tuple):
        """
        Summary
            create_thumb_jpeg: Creates a temporary directory for JPEG embedded in NEF files
        
        Args:
            photos_test: list[str] 
                list of the RAW files from which the JPEG is to be extracted
        """

        os.makedirs(TMP_DIR, exist_ok=True)
        for i in range(0, len(photos_test)):
            photo_file = f'./pictures/{photos_test[i]}'
            photo_exif = PhotoExif(photo_file)
            full_path_for_thumb = TMP_DIR + photo_exif.original_name + '.jpeg'
            file_path = './pictures/'+ photos_test[i]
            with rawpy.imread(file_path) as raw:
               thumb = raw.extract_thumb()
            with open(full_path_for_thumb, 'wb') as file:
                file.write(thumb.data)
#--------------------------------------------------------------------------------
    def setUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        central_widget.setLayout(self.main_layout)
#--------------------------------------------------------------------------------
    def show_display(self):
        controls = Controls()
        # creates widget gallery (contains Thumbnails objects)
        gallery = Gallery(controls, self.photos_test)
        # creates scrollarea (contains gallery)
        display = Display(gallery)
        # adds scrollarea to main layout (central widget)
        self.main_layout.addWidget(display)
        self.main_layout.addWidget(controls)
#################################################################################
#################################################################################
def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.setWindowIcon(QIcon('./icons/qt.png'))
    main_window.setFixedSize(MAIN_SIZE)
    main_window.setWindowTitle("Renommage des photos")
    
    f = QFile("./style.qss")
    f.open(QIODevice.ReadOnly)
    app.setStyleSheet(QTextStream(f).readAll())

    # shutil.rmtree(TMP_DIR) <- useless here!
    main_window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
