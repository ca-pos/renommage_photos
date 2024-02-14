from pathlib import Path

import pyexiv2

from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QGroupBox, QLabel, QPushButton, QHBoxLayout, QScrollArea
from PySide6.QtGui import QPixmap, QTransform, QPalette, QBrush
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
        print('display')
#################################################################################
class PhotoExif():
    """
    PhotoExif Définit un objet PhotoEXIF à partir d'un fichier NEF (RAW de Nikon). L'objet contient les informations exif extraites du fichier RAW et nécessaires pour le fonctionnement de renomme.py

    Reçoit
        file [str] : chemin du fichier NEF

    Attributs
        original_name [str]     : nom du fichier original (sur la carte mémoire)
        original_suffix [str]   : l'extension du fichier original (NEF pour Nikon)
        date [%Y %m %d]         : date de la prise de vue
        oriention [int]         : 8 = portrait, autre valeur = paysage
        nikon_file_number [int] : si Nikon (ext = NEF), le numéro d'ordre de la photo
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
    hidden_list = list()
    changed = Signal(str)
    def __init__(self):
        super().__init__()

        fichier_raw = [str(fichier) for fichier in Path('./pictures').glob('*.NEF')]
        fichier_raw = sorted(fichier_raw)

        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.addStretch()
        self.setLayout(layout)

        for i in range(len(fichier_raw)):
            if i > 3:
                continue
            photo_file = fichier_raw[i]
            blur = ''
            for j in range(len(Gallery.hidden_list)):
                if photo_file.find(Gallery.hidden_list[j]) != -1:
                    blur = BLURRED
            th = Thumbnails(photo_file, blur)
            th.setStyleSheet('background-color: #ee6')  # background jaune
            th.changed.connect(self.refresh_blur_list)
            layout.addWidget(th)
#--------------------------------------------------------------------------------            
    @Slot(result=str)
    def refresh_blur_list(self, e):
        try:
            index = Gallery.hidden_list.index(e)
            Gallery.hidden_list.pop(index)
        except ValueError:
            Gallery.hidden_list.append(e)
        self.changed.emit('appel')
#################################################################################
class Thumbnails(QWidget):
    changed = Signal(str)
    def __init__(self, photo, blur):
        super().__init__()
        self.photo = PhotoExif(photo)
        self.full_path_tmp = TMP_DIR + self.photo.original_name + blur + '.jpeg'

        layout  = QGridLayout()
        self.setLayout(layout)
        groupbox = QGroupBox(self.photo.original_name)
        layout.addWidget(groupbox)
        vbox = QVBoxLayout()
        groupbox.setLayout(vbox)

        label = QLabel(self)

        pixmap = QPixmap(self.full_path_tmp)
        print('$', self.full_path_tmp)
        if self.photo.orientation == 8:
            transform = QTransform().rotate(270)
            pixmap = pixmap.transformed(transform)
        pixmap = pixmap.scaled(PIXMAP_SCALE, Qt.AspectRatioMode.KeepAspectRatio)
        label.setPixmap(pixmap)

        self.btn = QPushButton('')
        if self.full_path_tmp.find(BLURRED) == -1:
            self.btn.setStyleSheet('background-color: #6e6')
            self.btn.setText('Masquer')
        else:
            self.btn.setStyleSheet('background-color: #e66')
            self.btn.setText('Afficher')
        self.btn.setCheckable(True)
        self.btn.setFixedSize(pixmap.width(), 25)
        self.btn.clicked.connect(self.masquer)

        groupbox.setFixedHeight(pixmap.height()+self.btn.height()+45)
        groupbox.setFixedWidth(int(1.2*pixmap.width()))
        
        vbox.addWidget(label)
        vbox.addWidget(self.btn)
        vbox.setSpacing(0)
        vbox.addStretch()
#--------------------------------------------------------------------------------
    def blur_image(self):
        if not self.full_path_tmp.find(BLURRED) == -1:
            return
        full_blurred_path = self.full_path_tmp[:-5] + BLURRED + self.full_path_tmp[-5:]
        img = Image.open(self.full_path_tmp)
        img_blur = img.filter(ImageFilter.GaussianBlur(80))
        img_blur.save(full_blurred_path)        
#--------------------------------------------------------------------------------
    @Slot(result=str)
    def masquer(self):
        sig = self.photo.original_name[:]
        #----- sans doute à enlever
        print('masquer')
        if self.btn.isChecked():
            self.btn.setText('Afficher')
            self.btn.setStyleSheet('background-color: #e66')
            self.blur_image()
        else:
            self.btn.setText('Masquer')
            self.btn.setStyleSheet('background-color: #6e6')
        #------ jusque là
        self.changed.emit(sig)
#################################################################################
