import dis
import sys
from pathlib import Path
from numpy import disp

import rawpy
import imageio
import pyexiv2
from PIL import Image
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox, QScrollArea
from PySide6.QtGui import QPixmap, QTransform, QPalette, QIcon
from PySide6.QtCore import QFile, QTextStream, QIODevice, QSize, Qt

from constants import *
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

        photo = Photo("./pictures/_DSC8055.NEF")

        display = QScrollArea()
        photos = QWidget()
        display.setBackgroundRole(QPalette.Dark)
        display_layout = QHBoxLayout()
        display_layout.setSpacing(0)
        display_layout.addStretch()
        photos.setLayout(display_layout)
        for i in range(0, 6):
            v = Vignette()
            display_layout.addWidget(v)
        display.setWidget(photos)
        display.setWidgetResizable(True)

        main_layout.addWidget(display)
#################################################################################
class Vignette(QWidget):
    def __init__(self, file: str = "./pictures/thumbnails/_DSC8055.jpeg"):
        super().__init__()

        layout  = QGridLayout()
        self.setLayout(layout)

        groupbox = QGroupBox("_DSC8149.jpeg")

        layout.addWidget(groupbox)

        vbox = QVBoxLayout()
        groupbox.setLayout(vbox)

        label = QLabel(self)
        transform = QTransform().rotate(270)

        pixmap = QPixmap(file)
        pixmap = pixmap.transformed(transform)
        pixmap = pixmap.scaled(PIXMAP_SCALE, Qt.AspectRatioMode.KeepAspectRatio)
        label.setPixmap(pixmap)

        titre = QLabel("_DSC8149.jpeg")
        titre.setAlignment(Qt.AlignCenter)
        titre.setStyleSheet("padding: 10px 10px 0px 10px")

        btn = QPushButton("Masquer")
        btn.setFixedSize(pixmap.width(), 25)

        groupbox.setFixedHeight(pixmap.height()+btn.height()+45)
        groupbox.setFixedWidth(1.1*pixmap.width())
        
        vbox.addWidget(label)
        vbox.addWidget(btn)
        vbox.setSpacing(0)
        vbox.addStretch()
#################################################################################
class Photo():
    def __init__(self, file: str) -> None:
        path = Path(file)
        self.original_path = path.cwd()
        self.original_name = path.stem
        self.original_suffix = path.suffix
        
        meta_data = pyexiv2.ImageMetadata(file)
        meta_data.read()
        self.date = meta_data['Exif.Image.DateTimeOriginal'].value.strftime('%Y %m %d')
        self.orientation = meta_data['Exif.Image.Orientation'].value
        if self.original_suffix == '.NEF':
            self.nikon_file_number = meta_data['Exif.NikonFi.FileNumber'].value
        else:
            self.nikon_file_number = -1

        with rawpy.imread(file) as raw:
            pass
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
    sys.exit(app.exec())

    return True

if __name__ == '__main__':
    main()