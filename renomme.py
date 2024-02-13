from genericpath import exists
import sys, os
import shutil

from PySide6.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget
from PySide6.QtGui import QIcon
from PySide6.QtCore import QFile, QTextStream, QIODevice

from constants import *
from classes import *
#################################################################################
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # pour la mise au point seulement
        photos_test = ('_DSC7986.NEF', '_DSC8064.NEF', '_DSC8080.NEF', '_DSC8081.NEF')        
        # Création d'un répertoire temporaire pour les JPEG embarqués dans les RAW
        self.create_thumb_jpeg(photos_test)
        self.setUI()
        self.show_display()
#--------------------------------------------------------------------------------
    def show_display(self):
        # création du widget gallery
        gallery = Gallery()        
        # création de la scrollarea display qui contient gallery
        self.display = Display(gallery)
        # ajouter la scrollaera au layout principal (du central widget)
        self.main_layout.addWidget(self.display)
#--------------------------------------------------------------------------------
    def setUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QGridLayout()
        self.main_layout.setSpacing(0)
        central_widget.setLayout(self.main_layout)

        # photos_test = ('_DSC7986.NEF', '_DSC8064.NEF', '_DSC8080.NEF', '_DSC8081.NEF', '_DSC8084.NEF', '_DSC8134.NEF', '_DSC8135.NEF', '_DSC8145.NEF', '_DSC8146.NEF', '_DSC8147.NEF', '_DSC8148.NEF', '_DSC8149.NEF')
#--------------------------------------------------------------------------------
    def create_thumb_jpeg(self, photos_test):
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

    # shutil.rmtree(TMP_DIR)
    main_window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
