from pathlib import Path
# from telnetlib import GA
# from tkinter.messagebox import RETRY

import pyexiv2
import random
import string
from functools import partial

from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QGroupBox, QLabel, QPushButton, QHBoxLayout, QScrollArea, QCheckBox
from PySide6.QtGui import QPixmap, QTransform, QPalette, QKeyEvent, QIcon
from PySide6.QtCore import Qt, Signal, Slot, QObject, QSize
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
    """
    Gallery creates a widget that contains Thumbnails object

    Args:
        QWidget: QWidget

    Signals:
        When a Thumbnails object is changed (on a signal emitted by the Thumbnails object) the Gallery object is updated and a changed signal (an empty str) is emitted

    Class Variables:
        hidden_list: list of the thumbnails to be displayed blurred
    """
    def __init__(self, controls):
        """
        __init__ creates Gallery objects
        """
        super().__init__()
        # development only ---------------------------------------------------------
        fichier_raw = [str(fichier) for fichier in Path('./pictures').glob('*.NEF')]
        fichier_raw = sorted(fichier_raw)
        #----------------------------------------------------------------------------
        self.first = -1
        self.last = -1
        self.list_set = False
        self.checked_list = list()
        self.old_date = ''
        
        self.layout = QHBoxLayout()
        self.layout.setSpacing(0)
        self.layout.addStretch()
        self.setLayout(self.layout)
        
        for i_thumb in range(len(fichier_raw)):
            # only for development with short photo list
            if i_thumb > 3:       
               continue
            photo_file = fichier_raw[i_thumb]
            th = Thumbnails(photo_file)
            self.layout.addWidget(th)
            th.set_bg_color(self.assign_bg_color(th.rank))
            th.selected.connect(partial(self.thumb_selected, th.rank))
            th.colored.connect(partial(self.change_group_bg_color, th.exif.date))
#--------------------------------------------------------------------------------
    def assign_bg_color(self, rank: int):
        if rank > 1 and self.w(rank).exif.date == self.w(rank-1).exif.date:
            color = self.w(rank-1).get_bg_color()
        else:
            color = self.new_color()
        return str(color)
#--------------------------------------------------------------------------------
    def change_group_bg_color(self, date:str, e: str):
        bg_color = self.new_color()
        for i in range(1, Thumbnails.count + 1):
            if self.w(i).exif.date == date:
                self.w(i).set_bg_color(bg_color)
#--------------------------------------------------------------------------------
    def new_color(self):
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)
        return '#%02x%02x%02x' % (red, green, blue)
#--------------------------------------------------------------------------------  
    def thumb_selected(self, rank: int, button_checked: bool):
        self._modifier = str(Thumbnails.modifier).split('.')[1][:-8]
        if self._modifier == 'Control':
            if not self.in_list_ok(rank):
                return
            flag = not self.w(rank).get_selection()
            self.w(rank).set_selection(flag)
            return

        print('--->', self.checked_list)

        length = len(self.checked_list)
        if length == 0:
            print('LISTE VIDE')
        if self.first == -1:
            print('On a le premier :', end=' ')
            print(rank)
            self.update_checked_list(rank)
            self.first = rank
            self.w(rank).set_selection(True)
            return
        if self.last == -1:
            if rank == self.first: # same thumb clicked twice
                self.w(rank).set_selection(False)
                self.first = -1
                self.checked_list.clear()
                return
            print('On a le second :', end=' ')
            print(rank)
            self.update_checked_list(rank)
            tmp = self.first
            self.first = min(rank, tmp)
            self.last = max(rank, tmp)
            self.w(rank).set_selection(True)
            for i in range(self.first+1, self.last):
                self.w(i).set_selection(True)
                self.update_checked_list(i)
            return
        else:
            print('ON CHANGE DE LISTE')
            if rank in self.checked_list:
                print('INTÉRIEUR')
            else:
                print('EXTÉRIEUR')
            for i in self.checked_list:
                self.w(i).set_selection(False)
            self.w(rank).set_selection(True)
            self.checked_list.clear()
            self.first = rank
            self.last = -1
            self.update_checked_list(rank)
#--------------------------------------------------------------------------------
    def in_list_ok(self, rank):
        ok = list()
        ok.append(self.checked_list[0])
        ok.append(self.checked_list[-1])
        ok.append(self.checked_list[0]-1)
        ok.append(self.checked_list[-1]+1)
        if not rank in ok:
            print('Il y a un trou')
            return False
        if rank in ok[:-2]:
            rank = -rank
        self.update_checked_list(rank)
        return True
#--------------------------------------------------------------------------------
    def update_checked_list(self, item: int):
        if item == 0:
            print('item == 0, est-ce normal ?')
            return
        if item > 0:
            self.checked_list.append(item)
        if item < 0:
            item = -item
            self.checked_list.remove(item)
        self.checked_list.sort()
        print('upd lst', self.checked_list)
#--------------------------------------------------------------------------------
    def w(self, rank: int):
        return self.layout.itemAt(rank).widget()
#################################################################################
class Controls(QWidget):
    def __init__(self):
        super().__init__()

        hbox = QHBoxLayout()
        self.setLayout(hbox)
        lbl_suffix = QLabel('Ajouter un suffixe à la date de la sélection')
        btn_add_suffix = QPushButton('')
        btn_add_suffix.setFixedSize(BUTTON_V_SIZE, BUTTON_V_SIZE)
        hbox.addWidget(lbl_suffix)
        hbox.addWidget(btn_add_suffix)
        hbox.addStretch()
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
    colored = Signal(str)
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
        self.bg_color = '#bbb' #maybe useless, to check
        self.is_selected = False
        self._full_path_tmp = TMP_DIR + self.exif.original_name + '.jpeg'
        self._full_path_tmp_blurred = TMP_DIR + self.exif.original_name + BLURRED + '.jpeg'
        Thumbnails.count += 1 
        self.rank = Thumbnails.count

        thumbnail_title = self.exif.original_name + '  ('  + self.exif.date.replace(' ', '/') + ')'
        reversed_date = '/'.join(list(reversed(self.exif.date.split(' '))))
        thumbnail_title = self.exif.original_name + '  (' + reversed_date +')'

        self._label = QLabel(self)
        self._label.setStyleSheet('margin: 0px 0px 5px 0px')
        self.set_pixmap(self._full_path_tmp)

        # create the show/hide button (afficher/masquer)
        self.btn = QPushButton('')
        self.update_hide_button(False)
        self.btn.setCheckable(True)
        self.btn.setFixedSize(MASK_BUTTON_H_SIZE, BUTTON_V_SIZE)
        self.btn.clicked.connect(self.hide)

        # creates a checkbox to change bg color
        self.change_bg_color = QCheckBox()
        self.change_bg_color.setObjectName('colored')
        self.change_bg_color.setFixedSize(BUTTON_V_SIZE, BUTTON_V_SIZE)
        self.change_bg_color.stateChanged.connect(self._change_color)

        # creates a checkbox to select thumbnails
        self.select = QPushButton()# QCheckBox()
        self.select.setFixedSize(BUTTON_V_SIZE, BUTTON_V_SIZE)
        self.select.clicked.connect(self._selection)
        self.select.setStyleSheet(f'background-color: {self.bg_color}')
        self.select.setIconSize(QSize(ICON_H_SIZE, ICON_V_SIZE))
        self.set_selection(False)

        layout  = QGridLayout()
        self.setLayout(layout)

        groupbox = QGroupBox(thumbnail_title)
        groupbox.setFixedHeight(self._pixmap.height()+self.btn.height()+45)
        groupbox.setFixedWidth(int(1.0*self._pixmap.width()))
        layout.addWidget(groupbox)

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.setSpacing(0)
        groupbox.setLayout(vbox)
        vbox.addWidget(self._label)
        hbox.addWidget(self.btn, alignment=Qt.AlignmentFlag.AlignLeft)
        hbox.addStretch()
        hbox.addWidget(self.change_bg_color, alignment=Qt.AlignmentFlag.AlignRight)
        hbox.addWidget(self.select, alignment=Qt.AlignmentFlag.AlignRight)
        vbox.addLayout(hbox)
        vbox.setSpacing(0)
        vbox.addStretch()
#--------------------------------------------------------------------------------
    def set_selection(self, flag: bool):
        self.is_selected = flag
        if flag:
            self.select.setIcon(QIcon('./icons/_active__yes.png'))
        else:
            self.select.setIcon(QIcon(''))
#--------------------------------------------------------------------------------
    def get_selection(self):
        return self.is_selected
#--------------------------------------------------------------------------------
    def blur_pixmap(self):
        if not Path(self._full_path_tmp_blurred).exists():
            img = Image.open(self._full_path_tmp)
            img = img.filter(ImageFilter.GaussianBlur(80))
            img.save(self._full_path_tmp_blurred)
        self.set_pixmap(self._full_path_tmp_blurred)
#--------------------------------------------------------------------------------
    def get_bg_color(self):
        print('+++', self.bg_color)
        return self.bg_color
#--------------------------------------------------------------------------------
    def set_bg_color(self, color: str):
        """
        set_bg_color set background color

        Args:
            color (str): color of the background
        """
        self.setStyleSheet(f'background-color: {color}')
        self.bg_color = color
#--------------------------------------------------------------------------------
    def set_pixmap(self, pixmap_path: str):
        self._pixmap = QPixmap(pixmap_path)
        if self.exif.orientation == 'portrait':
            transform = QTransform().rotate(270)
            self._pixmap = self._pixmap.transformed(transform)
        self._pixmap = self._pixmap.scaled(PIXMAP_SCALE, Qt.AspectRatioMode.KeepAspectRatio)
        self._label.setPixmap(self._pixmap)
#--------------------------------------------------------------------------------
    def update_hide_button(self, blur: bool):
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
        # flag = not self.get_selection()
        # self.set_selection(flag)
        # set = True if e else False
        # self.is_selected = set
        self.selected.emit(True)
#--------------------------------------------------------------------------------
    @Slot(result=bool)
    def _change_color(self, e: int):
        self.colored.emit('')
#--------------------------------------------------------------------------------
    @Slot(result=str)
    def hide(self):
        if self.btn.isChecked():
            self.blur_pixmap()
            self.update_hide_button(True)
        else:
            self.set_pixmap(self._full_path_tmp)
            self.update_hide_button(False)
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
