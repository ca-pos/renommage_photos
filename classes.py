from pathlib import Path

import pyexiv2
import random

from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QGroupBox, QLabel, QPushButton, QHBoxLayout, QScrollArea, QCheckBox
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

        bg_color = self.new_color()
        for i in range(len(fichier_raw)):
            # only for development with short photo list
            if i > 3:       
               continue
            photo_file = fichier_raw[i]
            blur = ''
            for j in range(len(Gallery.hidden_list)):
                if photo_file.find(Gallery.hidden_list[j]) != -1:
                    blur = BLURRED
            th = Thumbnails(photo_file, blur)
            exif = PhotoExif(photo_file)
            if i == 0:
                old_date = exif.date
            if not old_date == exif.date:
                bg_color = self.new_color()
                old_date = exif.date
            th.setStyleSheet(f'background-color: {bg_color}')  # random bg color 
            th.changed.connect(self.refresh_blur_list)
            layout.addWidget(th)
#--------------------------------------------------------------------------------    
    def new_color(self):
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)
        return '#%02x%02x%02x' % (red, green, blue)
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
                path to RAW file
            blur: str
                whether or not the displayed JPEG should be blurred: clear = empty string, blurred = BLURRED constant
        """
        super().__init__()
        self.photo = PhotoExif(photo)
        self.full_path_tmp = TMP_DIR + self.photo.original_name + blur + '.jpeg'

        thumbnail_title = self.photo.original_name + ' ('  + self.photo.date.replace(' ', '/') + ')'

        label = QLabel(self)
        label.setStyleSheet('margin: 0px 0px 5px 0px')
        pixmap = QPixmap(self.full_path_tmp)
        if self.photo.orientation == 'portrait':
            transform = QTransform().rotate(270)
            pixmap = pixmap.transformed(transform)
        pixmap = pixmap.scaled(PIXMAP_SCALE, Qt.AspectRatioMode.KeepAspectRatio)
        label.setPixmap(pixmap)

        # create the show/hide button (afficher/masquer)
        self.btn = QPushButton('')
        if self.full_path_tmp.find(BLURRED) == -1:
            self.btn.setStyleSheet('background-color: #6e6')
            self.btn.setText('Masquer')
        else:
            self.btn.setStyleSheet('background-color: #e66')
            self.btn.setText('Afficher')
        self.btn.setCheckable(True)
        self.btn.setFixedSize(BUTTON_H_SIZE, BUTTON_V_SIZE)
        self.btn.clicked.connect(self.masquer)

        # create a checkbox to select thumbnails
        self.select = QCheckBox()
        self.select.setFixedSize(BUTTON_V_SIZE, BUTTON_V_SIZE)
        self.select.setStyleSheet("QCheckBox::indicator"
                               "{"
                               "width :15px;"
                               "height : 15px;"
                               "background-color: #ccc;"
                               "border: 1px solid;"
                               "margin: 5px"
                               "}")

        layout  = QGridLayout()
        self.setLayout(layout)

        groupbox = QGroupBox(thumbnail_title)
        groupbox.setFixedHeight(pixmap.height()+self.btn.height()+45)
        groupbox.setFixedWidth(int(1*pixmap.width()))
        layout.addWidget(groupbox)

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        groupbox.setLayout(vbox)
        vbox.addWidget(label)
        hbox.addWidget(self.btn, alignment=Qt.AlignmentFlag.AlignLeft)
        hbox.addWidget(self.select, alignment=Qt.AlignmentFlag.AlignRight)
        vbox.addLayout(hbox)
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
        if Path(full_blurred_path).exists():
            return
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
