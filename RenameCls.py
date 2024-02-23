from pathlib import Path
from telnetlib import GA
from tkinter.messagebox import RETRY

import pyexiv2
import random
import string
from functools import partial

from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QGroupBox, QLabel, QPushButton, QHBoxLayout, QScrollArea, QCheckBox
from PySide6.QtGui import QPixmap, QTransform, QPalette, QKeyEvent, QIcon
from PySide6.QtCore import Qt, Signal, Slot, QObject, QEvent
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
    PhotoExif object contains the exif informations necessary for the present program and a compressed version of the original date

    Attributes
        dir: str
            directory containing the RAW files
        original_name: str
            original name (stem) from camera memory card
        original_suffix: str
            original ext (NEF for Nikon)
        date [%Y %m %d]: str
            original date (date of the shooting)
        compressed_date: tuple
            the first element of the tuple represents the decade (format: YYYX), the second one the date itself (format: YMDD, where Y is the last part of the year et M is the month as a letter between A for january and L for december)
            Note: the compressed date is for compatibility with old files (the time of the 8.3 filenames)
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
        index = int(self.date[5:7]) - 1
        tmp_date = self.date[3] + string.ascii_uppercase[index] + self.date[-2:]
        self.compressed_date = (self.date[0:3]+'X', tmp_date)
        orientation = meta_data['Exif.Image.Orientation'].value
        self.orientation = 'portrait' if orientation == 8 else 'landscape'
        if self.original_suffix == '.NEF':
            self.nikon_file_number = meta_data['Exif.NikonFi.FileNumber'].value
        else:
            self.nikon_file_number = -1
#################################################################################
class Gallery(QWidget):
    select1 = False
    list_set = False
    checked_list_fixed = list()
    counter = 0
    """
    Gallery creates a widget that contains Thumbnails object

    Args:
        QWidget: QWidget

    Signals:
        When a Thumbnails object is changed (on a signal emitted by the Thumbnails object) the Gallery object is updated and a changed signal (an empty str) is emitted

    Class Variables:
        hidden_list: list of the thumbnails to be displayed blurred
    """
    def __init__(self):
        """
        __init__ creates Gallery objects
        """
        super().__init__()

        self.checked_list_count = -1

        fichier_raw = [str(fichier) for fichier in Path('./pictures').glob('*.NEF')]
        fichier_raw = sorted(fichier_raw)

        self.layout = QHBoxLayout()
        self.layout.setSpacing(0)
        self.layout.addStretch()
        self.setLayout(self.layout)
        
        bg_color = self.new_color()
        for i in range(len(fichier_raw)):
            # only for development with short photo list
            if i > 3:       
               continue
            photo_file = fichier_raw[i]
            th = Thumbnails(photo_file)
            exif = th.exif
            if i == 0:
                old_date = exif.date
            if not old_date == exif.date:
                bg_color = self.new_color()
                old_date = exif.date
            th.set_bg_color(bg_color)
            th.selected.connect(partial(self.thumb_selected, th.rank))
            self.layout.addWidget(th)
#--------------------------------------------------------------------------------    
    def new_color(self):
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)
        return '#%02x%02x%02x' % (red, green, blue)
#--------------------------------------------------------------------------------    
    def thumb_selected(self, rank: int, button_checked: bool):
        Gallery.counter += 1
        if Gallery.counter > 50:
            print('ÇA BOUCLE')
            exit(1)
        if str(Thumbnails.modifier).split('.')[1][:-8] == 'Alt':
            bg_color = self.new_color()
            self.w(rank).setStyleSheet(f'background-color: {bg_color}')
            return

        print('--->', self.checked_list())

        length = len(self.checked_list())
        # length == 0 -> same button checked and immediatly after unchecked
        # just return in the final program
        if length == 0:
            print('LISTE VIDE')
            exit()
        if button_checked:
            if not Gallery.select1:
                print('On a le premier')
                Gallery.select1 = True
                return
            if not Gallery.list_set:
                Gallery.list_set = True
                temp_list = self.checked_list()
                print('On a le second')
                first = temp_list[0]
                last = temp_list[1]
                self.checked_list_count = last - first + 1 if self.checked_list_count == -1     else self.checked_list_count            
                for i in range(first+1, last):
                    self.w(i).set_checked(True)
                Gallery.checked_list_fixed = self.checked_list()
            return

        in_between = (rank >= Gallery.checked_list_fixed[0] and
                      rank <= Gallery.checked_list_fixed[-1])
        
        print('+', in_between, rank, Gallery.checked_list_fixed, Gallery.list_set)
        if Gallery.list_set and in_between:
            self.unset_others(rank)
            return
        if Gallery.list_set and len(self.checked_list()) == self.checked_list_count + 1:
            print('ON CHANGE LA LISTE')

            Gallery.list_set = False
            self.unset_others(rank)
#--------------------------------------------------------------------------------    
    def unset_others(self, rank: int):
        print('usrk', rank)
        self.w(rank).set_checked(True)
        return
        for i in Gallery.checked_list_fixed:
            if not i == rank:
                self.w(i).set_checked(False)
#--------------------------------------------------------------------------------    
    def checked_list(self):
        n = list()
        for i in range(1, Thumbnails.count+1):
            if self.w(i).is_selected:
                n.append(i)
        return n
#--------------------------------------------------------------------------------    
    def w(self, rank: int):
        return self.layout.itemAt(rank).widget()
#################################################################################
class Thumbnails(QWidget):
    """
    Thumbnails summary: Thumbnails object comprised 
        - a title (original name of the image from exif data), 
        - the JPEG embedded in the RAW file,
        - a Show (Afficher) / Hide (Masquer) checkable pushbutton,
        - a checkbox for thumbnail selection.
    JPEG of hidden thumbnails are blurred.

    Args:
        QWidget: QWidget

    Signals:
        When status is changed (hidden/shown) a changed signal is emitted which contains the the exif original name (stem)
    """
    selected = Signal(bool)
    modifier = Qt.KeyboardModifier.NoModifier
    count: int = 0

    def __init__(self, photo: str):
        """
        __init__ creates Thumbnails objects

        Args:
            photo: str
                path to RAW file
            blur: str
                whether or not the displayed JPEG should be blurred: clear = empty string, blurred = BLURRED constant
            id: int
                id number

        Attributes:
            id: int
                id number
            exif: <RenameCls.PhotoExif>
                exif data (of the original RAW file) needed for the present program
            bg_color: int
                background color of the Thumbnails

        Methods:
            set_bg_color(color: str)
                set background color to "color"
        """
        super().__init__()
        self.exif = PhotoExif(photo)
        self.bg_color = ''
        self.is_selected = False
        self._full_path_tmp = TMP_DIR + self.exif.original_name + '.jpeg'
        self._full_path_tmp_blurred = TMP_DIR + self.exif.original_name + BLURRED + '.jpeg'
        Thumbnails.count += 1 
        self.rank = Thumbnails.count

        thumbnail_title = self.exif.original_name + '  ('  + self.exif.date.replace(' ', '/') + ')'

        self._label = QLabel(self)
        self._label.setStyleSheet('margin: 0px 0px 5px 0px')
        self.set_pixmap(self._full_path_tmp)

        # create the show/hide button (afficher/masquer)
        self.btn = QPushButton('')
        self.update_button(False)
        self.btn.setCheckable(True)
        self.btn.setFixedSize(BUTTON_H_SIZE, BUTTON_V_SIZE)
        self.btn.clicked.connect(self.hide)

        # create a checkbox to select thumbnails
        self.select = QCheckBox()
        self.select.setFixedSize(BUTTON_V_SIZE, BUTTON_V_SIZE)
        self.select.stateChanged.connect(self._selection)
        
        layout  = QGridLayout()
        self.setLayout(layout)

        groupbox = QGroupBox(thumbnail_title)
        groupbox.setFixedHeight(self._pixmap.height()+self.btn.height()+45)
        groupbox.setFixedWidth(int(1.0*self._pixmap.width()))
        layout.addWidget(groupbox)

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        groupbox.setLayout(vbox)
        vbox.addWidget(self._label)
        hbox.addWidget(self.btn, alignment=Qt.AlignmentFlag.AlignLeft)
        hbox.addWidget(self.select, alignment=Qt.AlignmentFlag.AlignRight)
        vbox.addLayout(hbox)
        vbox.setSpacing(0)
        vbox.addStretch()
#--------------------------------------------------------------------------------
    def set_checked(self, flag):
        self.select.setChecked(flag)
#--------------------------------------------------------------------------------
    def blur_pixmap(self):
        if not Path(self._full_path_tmp_blurred).exists():
            img = Image.open(self._full_path_tmp)
            img = img.filter(ImageFilter.GaussianBlur(80))
            img.save(self._full_path_tmp_blurred)
        self.set_pixmap(self._full_path_tmp_blurred)
#--------------------------------------------------------------------------------
    def set_bg_color(self, color: str):
        """
        set_bg_color set background color

        Args:
            color (str): color of the background
        """
        self.setStyleSheet(f'background-color: {color}')
#--------------------------------------------------------------------------------
    def set_pixmap(self, pixmap_path: str):
        self._pixmap = QPixmap(pixmap_path)
        if self.exif.orientation == 'portrait':
            transform = QTransform().rotate(270)
            self._pixmap = self._pixmap.transformed(transform)
        self._pixmap = self._pixmap.scaled(PIXMAP_SCALE, Qt.AspectRatioMode.KeepAspectRatio)
        self._label.setPixmap(self._pixmap)
#--------------------------------------------------------------------------------
    def update_button(self, blur: bool):
        if blur:
            self.btn.setStyleSheet('background-color: #e66')
            self.btn.setText('Afficher')
        else:
            self.btn.setStyleSheet('background-color: #6e6')
            self.btn.setText('Masquer')
#--------------------------------------------------------------------------------
    @Slot(result=bool)
    def _selection(self, e: int):
        # e: 2 = set, 0 = unset
        set = True if e else False
        self.is_selected = set
        self.selected.emit(set)
#--------------------------------------------------------------------------------
    @Slot(result=str)
    def hide(self):
        if self.btn.isChecked():
            self.blur_pixmap()
            self.update_button(True)
        else:
            self.set_pixmap(self._full_path_tmp)
            self.update_button(False)
#################################################################################
class KeyPressFilter(QObject):
    def eventFilter(self, widget, event):
        if event.type() == QKeyEvent.KeyPress:
            Thumbnails.modifier = event.modifiers()
        elif event.type() == QKeyEvent.KeyRelease:
            Thumbnails.modifier = Qt.KeyboardModifier.NoModifier
        return False
#################################################################################
# class CCheckBox(QCheckBox):
#     def __init__(self):
#         super().__init__()
#     def mousePressEvent(self, e: QMouseEvent) -> None:
#         if e.button() == Qt.LeftButton:
#             print('left button')
#         return super().mousePressEvent(e)
#################################################################################
