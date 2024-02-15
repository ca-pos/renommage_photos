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
#################################################################################
class PhotoExif():
    """
    PhotoExif object contains the exif informations necessary for the present program

    Attributes
        dir: str
            directory containing the RAW files
        original_name: str
            original name (stem) from camera memory card
        original_suffix: str
            original ext (NEF for Nikon)
        date [%Y %m %d]: str
            original date (date of the shooting)
        oriention: str
            portrait (exif orientation == 8), landscape (otherwise)
        nikon_file_number: int
            Nikon file number
    """
    def __init__(self, file) -> None:
        """
        __init__ creates PhotoExif objects

        Args:
            file: str
                path to the RAW file
        """
        path = Path(file)
        self.dir = str(path.cwd()) # maybe useless
        self.original_name = path.stem
        self.original_suffix = path.suffix
        meta_data = pyexiv2.ImageMetadata(file)
        meta_data.read()
        self.date = meta_data['Exif.Image.DateTimeOriginal'].value.strftime('%Y %m %d')
        orientation = meta_data['Exif.Image.Orientation'].value
        self.orientation = 'portrait' if orientation == 8 else 'landscape'
        if self.original_suffix == '.NEF':
            self.nikon_file_number = meta_data['Exif.NikonFi.FileNumber'].value
        else:
            self.nikon_file_number = -1
#################################################################################
class Gallery(QWidget):
    """
    Gallery creates a widget that contains Thumbnails object

    Args:
        QWidget: QWidget

    Signals:
        When a Thumbnails object is changed (on a signal emitted by the Thumbnails object) the Gallery object is updated and a changed signal (an empty str) is emitted

    Class Variables:
        hidden_list: list of the thumbnails to be displayed blurred
    """
    hidden_list = list()
    changed = Signal(str)
    def __init__(self):
        """
        __init__ creates Gallery objects
        """
        super().__init__()

        fichier_raw = [str(fichier) for fichier in Path('./pictures').glob('*.NEF')]
        fichier_raw = sorted(fichier_raw)

        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.addStretch()
        self.setLayout(layout)

        for i in range(len(fichier_raw)):
            if i > 3:       # only for development with short photo list
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
        self.changed.emit('')
#################################################################################
class Thumbnails(QWidget):
    """
    Thumbnails Thumbnails object comprised a title (original name of the image from exif data), JPEG embedded in the RAW file, and a Show (Afficher) / Hide (Masquer) checkable pushbutton. JPEG of hidden thumbnails are blurred

    Args:
        QWidget: QWidget

    Signals:
        When status is changed (hidden/shown) a changed signal is emitted which contains the the exif original name (stem)
    """
    changed = Signal(str)
    def __init__(self, photo: str, blur: str):
        """
        __init__ creates Thumbnails objects

        Args:
            photo: str
            blur: str
                whether or not the displayed JPEG should be blurred: clear = empty string, blurred = BLURRED constant
        """
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
        if self.photo.orientation == 'portrait':
            transform = QTransform().rotate(270)
            pixmap = pixmap.transformed(transform)
        pixmap = pixmap.scaled(PIXMAP_SCALE, Qt.AspectRatioMode.KeepAspectRatio)
        label.setPixmap(pixmap)

        # creates the show (afficher) / hide (masquer) button
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
        """
        blur_image blur jpeg image: hidden images are shown blurred (not to be transferred to disk)
        """
        # if blurred image exists, don't create it again
        if not self.full_path_tmp.find(BLURRED) == -1:
            return
        full_blurred_path = self.full_path_tmp[:-5] + BLURRED + self.full_path_tmp[-5:]
        img = Image.open(self.full_path_tmp)
        img_blur = img.filter(ImageFilter.GaussianBlur(80))
        img_blur.save(full_blurred_path)        
#--------------------------------------------------------------------------------
    @Slot(result=str)
    def masquer(self):
        sig = self.photo.original_name
        if self.btn.isChecked():
            self.blur_image()
        self.changed.emit(sig) # status (shown/hidden) of a thumbnail has changed
#################################################################################
