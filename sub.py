from pathlib import Path
import tempfile, os

from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QGroupBox, QLabel, QPushButton
from PySide6.QtGui import QPixmap, QTransform
from PySide6.QtCore import Qt

from constants import *

import rawpy
# import imageio
import pyexiv2

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
            thumb = raw.extract_thumb()
        self.thumb = thumb.data
#################################################################################
class Thumbnails(QWidget):
    def __init__(self, photo):
        super().__init__()

        f_tmp = tempfile.mkstemp(suffix='.jpeg')[1]
        os.makedirs(TMP_DIR, exist_ok=True)
        tempfile.tempdir = TMP_DIR

        with open(f_tmp, 'wb') as f:
            f.write(photo.thumb)

        layout  = QGridLayout()
        self.setLayout(layout)

        groupbox = QGroupBox(photo.original_name)
        print(photo.original_name)

        layout.addWidget(groupbox)

        vbox = QVBoxLayout()
        groupbox.setLayout(vbox)

        label = QLabel(self)

        pixmap = QPixmap(f_tmp)
        if photo.orientation == 8:
            transform = QTransform().rotate(270)
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
