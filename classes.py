from pathlib import Path

import rawpy
import pyexiv2

from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QGroupBox, QLabel, QPushButton, QHBoxLayout, QScrollArea
from PySide6.QtGui import QPixmap, QTransform, QPalette
from PySide6.QtCore import Qt, Signal, Slot
from PIL import Image, ImageFilter

from constants import *

#################################################################################
class Display(QScrollArea):
    def __init__(self, gallery) -> None:
        super().__init__()
        self.setBackgroundRole(QPalette.Dark)
        self.setWidget(gallery)
        self.setWidgetResizable(True)
#################################################################################
class PhotoExif():
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
    def __init__(self, file) -> None:

        path = Path(file)
        self.original_path = str(path.cwd())
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
#################################################################################
class Gallery(QWidget):
    hides = list()
    def __init__(self, hide = ''):
        super().__init__()
        Gallery.hides.append(hide)
        self.populate_gallery()  

    def populate_gallery(self):
        pathlist_jpeg = Path(TMP_DIR).glob('*.jpeg')
        self.blur = ''

        fichier_raw = [str(fichier) for fichier in Path('./pictures').glob('*.NEF')]
        fichier_raw = sorted(fichier_raw)

        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.addStretch()
        self.setLayout(layout)

        # for f in pathlist_jpeg:
        #     continue
        #     print(str(f).split('/')[-1].replace(BLURRED, '').split('.')[-2])

        # clear_photos_list =[str(fichier) for fichier in Path(TMP_DIR).glob('*.jpeg') if str(fichier).find(BLURRED) == -1]

        for i in range(len(fichier_raw)):
            if i > 1:
                continue
            photo_file = fichier_raw[i]
            print('@', photo_file)

            for j in range(len(Gallery.hides)):
                print('#j', j, Gallery.hides)
                if photo_file.find(Gallery.hides[j]) != -1:
                    print(BLURRED)
                # else:
                #     print('*')
            # print(self.blur)
            print('thumbnails')
                # print('+j', j, photo_file.find(Gallery.hides[j]))
            th = Thumbnails(photo_file)
            th.setStyleSheet('background-color: #ee6')
            th.changed.connect(self.refresh_gallery)
            layout.addWidget(th)

    def refresh_gallery(self, e):
        print('-', e)
        print('+', Gallery.hides)
        if e in Gallery.hides:
            self.blur = ''
        else:
            self.blur = BLURRED
#################################################################################
class Thumbnails(QWidget):
    changed = Signal(str)
    def __init__(self, photo):
        super().__init__()
        self.photo = PhotoExif(photo)
        self.full_path_tmp = TMP_DIR + self.photo.original_name + '.jpeg'

        layout  = QGridLayout()
        self.setLayout(layout)

        groupbox = QGroupBox(self.photo.original_name)

        layout.addWidget(groupbox)

        vbox = QVBoxLayout()
        groupbox.setLayout(vbox)

        label = QLabel(self)

        pixmap = QPixmap(self.full_path_tmp)
        if self.photo.orientation == 8:
            transform = QTransform().rotate(270)
            pixmap = pixmap.transformed(transform)
        pixmap = pixmap.scaled(PIXMAP_SCALE, Qt.AspectRatioMode.KeepAspectRatio)
        label.setPixmap(pixmap)

        self.btn = QPushButton("Masquer")
        self.btn.value = self.photo.original_name[-4:]
        self.btn.setCheckable(True)
        self.btn.setStyleSheet('background-color: #6e6')
        self.btn.setFixedSize(pixmap.width(), 25)
        self.btn.clicked.connect(self.masquer)

        groupbox.setFixedHeight(pixmap.height()+self.btn.height()+45)
        groupbox.setFixedWidth(1.2*pixmap.width())
        
        vbox.addWidget(label)
        vbox.addWidget(self.btn)
        vbox.setSpacing(0)
        vbox.addStretch()
#--------------------------------------------------------------------------------
    def blur_image(self):
        full_blurred_path = self.full_path_tmp[:-5] + BLURRED + self.full_path_tmp[-5:]
        img = Image.open(self.full_path_tmp)
        img_blur = img.filter(ImageFilter.GaussianBlur(80))
        img_blur.save(full_blurred_path)        
#--------------------------------------------------------------------------------
    @Slot(str)
    def masquer(self):
        sig = self.photo.original_name[:]
        if self.btn.isChecked():
            self.btn.setText('Afficher')
            self.btn.setStyleSheet('background-color: #e66')
            self.blur_image()
        else:
            self.btn.setText('Masquer')
            self.btn.setStyleSheet('background-color: #6e6')

        self.changed.emit(sig)
#################################################################################
