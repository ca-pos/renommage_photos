from pathlib import Path
import tempfile, os

from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QGroupBox, QLabel, QPushButton, QHBoxLayout, QScrollArea
from PySide6.QtGui import QPixmap, QTransform, QPalette
from PySide6.QtCore import Qt, Signal, Slot

from constants import *

import rawpy
import pyexiv2

#################################################################################
class Display(QScrollArea):
    def __init__(self, gallery) -> None:
        super().__init__()
        self.setBackgroundRole(QPalette.Dark)
        self.setWidget(gallery)
        self.setWidgetResizable(True)
#################################################################################
class Photo():
    """
    Photo Définit un objet Photo à partir d'un fichier NEF (RAW de Nikon)
    Reçoit
        file [str] : chemin du fichier NEF
    Attributs
        original_name [str]     : nom du fichier original (sur la carte mémoire)
        original_suffix [str]   : l'extension du fichier original (NEF pour Nikon)
        date [%Y %m %d]         : date de la prise de vue
        oriention [int]         : 8 = portrait, autre valeur = paysage
        nikon_file_number [int] : si Nikon (ext = NEF), le numéro d'ordre de la photo
        thumb [bytes]           : le fichier thumbnail du fichier raw (format jpeg)
    """
    def __init__(self, file: str) -> None:
        path = Path(file)
        # self.original_path = path.cwd()
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
class Gallery(QWidget):
    def __init__(self, photos, hide = '8080'):
        super().__init__()

        self.hide_this = hide
        try:
            self.hides.append(self.hide_this)
        except:
            self.hides = (self.hide_this)
        if photos:
            self.photos = photos
        self.populate_gallery()

    def populate_gallery(self):
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.addStretch()
        self.setLayout(layout)
        for i in range(0, len(self.photos)):
            if str(self.photos[i]) in self.hides:
                continue
            photo_file = f"./pictures/_DSC{self.photos[i]}.NEF"
            photo = Photo(photo_file)
            th = Thumbnails(photo)
            layout.addWidget(th)

    def refresh_gallery(self):
        pass

            # print(layout.count(), layout.indexOf(th))

        # cpt = layout.count()
        # item = layout.itemAt(1)
        # w = item.widget()
        # w.deleteLater()
        # print(cpt)

#################################################################################
class Thumbnails(QWidget):
    clicked = Signal(str)
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

        btn = QPushButton("Masquer")
        btn.value = photo.original_name[-4:]
        btn.setFixedSize(pixmap.width(), 25)
        btn.clicked.connect(self.masquer)

        groupbox.setFixedHeight(pixmap.height()+btn.height()+45)
        groupbox.setFixedWidth(1.1*pixmap.width())
        
        vbox.addWidget(label)
        vbox.addWidget(btn)
        vbox.setSpacing(0)
        vbox.addStretch()
    @Slot(str)
    def masquer(self):
        # print(':', self.sender().value)
        self.clicked.emit(self.sender().value)
#################################################################################
