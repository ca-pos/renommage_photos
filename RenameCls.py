from pathlib import Path
# from telnetlib import GA
# from tkinter.messagebox import RETRY

import pyexiv2
import random
import string
from functools import partial

from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QGroupBox, QLabel, QPushButton, QHBoxLayout, QScrollArea, QCheckBox, QListWidget
from PySide6.QtGui import QPixmap, QTransform, QPalette, QKeyEvent, QIcon
from PySide6.QtCore import Qt, Signal, Slot, QObject, QSize
from PIL import Image, ImageFilter

from constants import *

#################################################################################
class Display(QScrollArea):
    def __init__(self, gallery) -> None:
        super().__init__()
        # self.setBackgroundRole(QPalette.Dark)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFixedHeight(SCROLLAREA_V_SIZE)
        self.setStyleSheet('background-color: #303030')
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
        self._file = file
        self._date_suffix = ''
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
#--------------------------------------------------------------------------------
    @property
    def file(self):
        return self._file
    @property
    def full_path(self):
        return '/'.join([self.dir, self.file])
    @property
    def date_suffix(self):
        # print('Récupération du suffixe de la date')
        return str(self._date_suffix)
    @date_suffix.setter
    def date_suffix(self, suffix: str):
        # print('Attribution suffixe')
        self._date_suffix = suffix
    @property
    def compressed_date(self):
        index = int(self.date[5:7]) - 1
        tmp_date = self.date[3] + string.ascii_uppercase[index] + self.date[-2:]
        self._compressed_date = (str(self.date[0:3])+'0', str(tmp_date), self.date_suffix)
        return self._compressed_date
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
        fichier_raw2 = ['pictures/_DSC8147.NEF', 'pictures/_DSC8148.NEF', 'pictures/_DSC8149.NEF']
        #----------------------------------------------------------------------------
        self.first = -1
        self.last = -1
        self.list_set = False
        self.checked_list = list()
        
        self.layout = QHBoxLayout()
        self.layout.setSpacing(0)
        self.layout.addStretch()
        self.setLayout(self.layout)

        ### create Thumbnails and add to Gallery
        self.populate_gallery(fichier_raw)
        ### process signals from controls
        controls.sliced.connect(self.slice_date)
        controls.cleared.connect(self.clear_selection)
        controls.erase_blurred.connect(self.erase_blurred)
#--------------------------------------------------------------------------------
    def erase_blurred(self):
        for i in range(1, Thumbnails.count+1):
            if self.w(i).hidden:
                self.w(i).deleteLater()
#--------------------------------------------------------------------------------
    def clear_gallery(self):
        for i in range(1, Thumbnails.count+1):
            self.w(i).deleteLater()
#--------------------------------------------------------------------------------
    def populate_gallery(self, fichier_raw):
        for i_thumb in range(len(fichier_raw)):
            # only for development --------------------------
            # for development with short photo list, set to 4
            # for development with long photo list, set > 12
            if i_thumb > 4:       
               continue
            # development -----------------------------------
            photo_file = fichier_raw[i_thumb]
            th = Thumbnails(photo_file)
            self.layout.addWidget(th)
            th.set_bg_color(self.assign_bg_color(th.rank))
            ### process signals from thumbnails
            th.selected.connect(partial(self.thumb_selected, th.rank))
            th.colored.connect(partial(self.change_group_bg_color, th.rank))
#--------------------------------------------------------------------------------
    def slice_date(self):
        if len(self.checked_list) == 0: # no selection
            return
        first_index = self.checked_list[0]
        original_suffix = self.w(first_index).exif.date_suffix        
        if not self.valid_selection(first_index, original_suffix):
            return
        if original_suffix == '':
            self.initialize_all_dates(first_index) # replace '' with '?' & update thumbnail title
        suffix = self.get_suffix(first_index)
        for i in self.checked_list:
            self.w(i).exif.date_suffix = suffix
            self.update_thumbnail_title(i)
        self.change_group_bg_color(first_index, 0)
        self.clear_selection()

        # for i in range(1, Thumbnails.count+1):
        #     print(self.w(i).exif.compressed_date)
        return
#--------------------------------------------------------------------------------
    def valid_selection(self, first_index, original_suffix) ->bool:
        print('La sélection est-elle valide ?')
        boundary = self.different_dates()
        if boundary > 0:
            print(f'Pas la même date aux rangs', {boundary-1}, 'et', {boundary})
            return False
        if original_suffix == '' and not self.first_series_of_day(first_index):
                print(f'Le début de la sélection', {first_index}, 'ne coincide pas avec un début de date')
                return False
        if original_suffix in list(string.ascii_lowercase):
            print('La vignette n°', {original_suffix}, 'fait déjà partie d\'un groupe')
            return False
        if original_suffix == '?' and self.w(first_index-1).exif.date_suffix == '?':
            print('Un ou plusieurs items oubliés avant', {first_index})
            return False
        checked_list_range = self.checked_list[-1] - self.checked_list[0] + 1
        print('clr', checked_list_range, len(self.checked_list))
        if not checked_list_range == len(self.checked_list):
            print('Les items sélectionnés ne sont pas contigus')
            return False

        return True
#--------------------------------------------------------------------------------
    def initialize_all_dates(self, first):
        items_per_date = list()
        for i in range(1, Thumbnails.count+1):
            if self.w(i).exif.date == self.w(first).exif.date:
                items_per_date.append(i)
        for i in items_per_date:
            self.w(i).exif.date_suffix = '?'
            self.update_thumbnail_title(i)
#--------------------------------------------------------------------------------
    def update_thumbnail_title(self, index):
            title1 = self.w(index).get_thumbnail_title()[:-13]
            title = self.w(index).get_thumbnail_title()[-12:-1]
            title = title + self.w(index).get_date_suffix() +')'
            self.w(index).set_thumbnail_title(title1 + title)
#--------------------------------------------------------------------------------
    def different_dates(self) -> int:
        """
        different_dates checks if the selecter items lies across date boundary

        Returns:
            int:
                -1 if date is the same for all items
                the boundary where the date change otherwise
        """
        for i in self.checked_list[1:]:
            if not self.w(i).exif.date == self.w(i-1).exif.date:
                return i
        return -1
#--------------------------------------------------------------------------------
    def clear_selection(self):
        for i in self.checked_list:
            self.w(i).set_selection(False)
        self.first = -1
        self.last = -1
        self.checked_list.clear()
#--------------------------------------------------------------------------------
    def thumb_selected(self, rank: int, button_checked: bool):
        self._modifier = str(Thumbnails.modifier).split('.')[1][:-8]
        if self._modifier == 'Control':
            # if self._modifier == 'Shift' and not self.in_list_ok(rank):
            #     return
            flag = not self.w(rank).get_selection()
            self.w(rank).set_selection(flag)
            if rank in self.checked_list:
                rank = -rank
            self.update_checked_list(rank)
            print('upd lst 2', self.checked_list)
            return

        print('--->', self.checked_list)

        length = len(self.checked_list)
        if length == 0: # not in final version
            print('LISTE VIDE')
        if self.first == -1:
            print('On a le premier :', end=' ')
            print(rank)
            self.update_checked_list(rank)
            self.first = rank
            self.w(rank).set_selection(True)
            return
        if self.last == -1:
            if rank == self.first: # same thumb clicked twice -> no selection
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
    def assign_bg_color(self, rank: int):
        if rank > 1 and self.w(rank).exif.date == self.w(rank-1).exif.date:
            color = self.w(rank-1).get_bg_color()
        else:
            color = self.new_color()
        return str(color)
#--------------------------------------------------------------------------------
    def change_group_bg_color(self, rank: int, e: int):
        date = self.w(rank).exif.compressed_date
        bg_color = self.new_color()
        for i in range(1, Thumbnails.count + 1):
            if self.w(i).exif.compressed_date == date:
                self.w(i).set_bg_color(bg_color)
#--------------------------------------------------------------------------------
    def new_color(self):
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)
        return '#%02x%02x%02x' % (red, green, blue)
#--------------------------------------------------------------------------------
    # def in_list_ok(self, rank):
    #     ok = list()
    #     ok.append(self.checked_list[0])
    #     ok.append(self.checked_list[-1])
    #     ok.append(self.checked_list[0]-1)
    #     ok.append(self.checked_list[-1]+1)
    #     if not rank in ok:
    #         print('Il y a un trou')
    #         return False
    #     if rank in ok[:-2]:
    #         rank = -rank
    #     self.update_checked_list(rank)
    #     return True
#--------------------------------------------------------------------------------
    def first_series_of_day(self, first_index: int):
        if first_index == 1:
            return True
        if not self.w(first_index).exif.date == self.w(first_index-1).exif.date:
            return True
        return False
#--------------------------------------------------------------------------------
    def get_suffix(self, first_index):
        if self.first_series_of_day(first_index):
            return 'a'
        else:
            previous = self.w(first_index-1).exif.date_suffix
            if not previous:
                print('Erreur de début')
                return ''
            return self.get_next_letter(previous)
#--------------------------------------------------------------------------------
    def get_next_letter(self, letter):
            letters = string.ascii_lowercase
            return letters[letters.index(letter) + 1]
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
#--------------------------------------------------------------------------------
    def update_thumbnail_date(self, i, suffix):
            # update suffix
            self.w(i).exif.date_suffix = suffix
            # update title
            thumbnail_title = self.w(i).get_thumbnail_title()[:-1] + suffix + ')'
            self.w(i).set_thumbnail_title(thumbnail_title)
#################################################################################
class Controls(QWidget):
    sliced = Signal(bool)   # do slicing of the date
    cleared = Signal(bool)  # clear selection
    erase_blurred = Signal(bool)  # remove blurred items
    erase_selected = Signal(bool) # remove selected items
    def __init__(self):
        super().__init__()

        ### OPERATIONS GROUP

        # add suffix to selection
        lbl_slice_date = QLabel('Ajouter un suffixe à la date de la sélection')
        btn_slice_date = CPushButton(funct=self._slice)
        # clear checked list
        lbl_clear_checked_list = QLabel('Réinitialiser la sélection')
        btn_clear_checked_list = CPushButton(funct=self._clear_selection)
        # subtitle
        lbl_remove = QLabel('Suppression d\'items')
        lbl_remove.setStyleSheet('font-size: 16px')
        # remove blurred items
        lbl_erase_blurred = QLabel('Supprimer les items masqués')
        btn_erase_blurred = CPushButton(funct=self._erase_blurred)
        # remove selected items
        lbl_erase_selected = QLabel('Supprimer les items sélectionnés')
        btn_erase_selected = CPushButton(funct=self._erase_selected)
        # create vboxes for operations group (ctrl1)
        vbox_lbl_op = QVBoxLayout() #for labels
        vbox_btn_op = QVBoxLayout() #fot buttons
        vbox_lbl_op.addWidget(lbl_slice_date)
        vbox_btn_op.addWidget(btn_slice_date)
        vbox_lbl_op.addWidget(lbl_clear_checked_list)
        vbox_btn_op.addWidget(btn_clear_checked_list)
        vbox_lbl_op.addWidget(lbl_remove)  # subtitle removing ops
        vbox_btn_op.addWidget(QLabel(""))  # create an empty line in button column
        vbox_lbl_op.addWidget(lbl_erase_blurred, alignment=Qt.AlignmentFlag.AlignRight)
        vbox_btn_op.addWidget(btn_erase_blurred)
        vbox_lbl_op.addWidget(lbl_erase_selected, alignment=Qt.AlignmentFlag.AlignRight)
        vbox_btn_op.addWidget(btn_erase_selected)
        # add vboxes to hbox
        hbox_op = QHBoxLayout()
        hbox_op.addLayout(vbox_lbl_op)
        hbox_op.addLayout(vbox_btn_op)
        # groupbox for operations commands
        groupbox_op = QGroupBox('Opérations')
        groupbox_op.setFixedSize(int(.35*H_SIZE), GROUP_1_V_SIZE)
        groupbox_op.setObjectName('ctrl1')
        groupbox_op.setLayout(hbox_op)

        ### DIRECTORIES GROUP

        # origin dir button
        btn_origin_dir = QPushButton('Répertoire d\'origine')
        btn_origin_dir.setObjectName('btn_orig')
        # origin dir reminder
        lst_orig_dir = QListWidget()
        lst_orig_dir.setFixedHeight(20)
        lst_orig_dir.addItem('Origine')
        lst_dest_dir = QListWidget()
        lst_dest_dir.setFixedHeight(20)
        lst_dest_dir.addItem('Destination')
        # destination dir button
        btn_dest_dir = QPushButton('Répertoire de sortie')
        btn_dest_dir.setObjectName('btn_dest')
        # create vboxes for dir buttons 
        vbox_dir_orig = QVBoxLayout()
        vbox_dir_dest = QVBoxLayout()
        vbox_dir_orig.addWidget(btn_origin_dir)
        vbox_dir_dest.addWidget(btn_dest_dir)
        vbox_dir_orig.addWidget(lst_orig_dir)
        vbox_dir_dest.addWidget(lst_dest_dir)
        # add vboxes to hbox_dir
        hbox_dir = QHBoxLayout()
        hbox_dir.addLayout(vbox_dir_orig)
        hbox_dir.addLayout(vbox_dir_dest)
        # groupbox for dir buttons
        groupbox_dir = QGroupBox('Répertoires')
        # groupbox_dir.setFixedHeight(100)
        groupbox_dir.setObjectName('ctrl2')
        groupbox_dir.setLayout(hbox_dir)

        ### ACTION BUTTONS

        # start button
        btn_xqt = QPushButton('Exécuter')
        btn_xqt.setObjectName('xqt')
        btn_xqt.setFixedSize(ACT_BTN_SIZE)
        # help button
        btn_help = QPushButton('Aide')
        btn_help.setObjectName('help')
        btn_help.setFixedSize(ACT_BTN_SIZE)
        # add buttons to hbox_act
        hbox_act = QHBoxLayout()
        hbox_act.addWidget(btn_help)
        hbox_act.addWidget(btn_xqt)
        # groupbox for act buttons (probably unecessary)
        groupbox_act = QGroupBox()
        groupbox_act.setLayout(hbox_act)


        ### GLOBAL LAYOUT
        layout = QGridLayout()  # global layout
        self.setLayout(layout)
        layout.addWidget(groupbox_op, 0, 0, 2, 1)
        layout.addWidget(groupbox_dir, 0, 1, 1, 1)
        # layout.setColumnStretch(1, 5)

        layout.addWidget(groupbox_act, 1, 1, 1, 1)
#--------------------------------------------------------------------------------
    @Slot(result=bool)
    def _clear_selection(self, event: int):
        self.cleared.emit(True)
    @Slot(result=bool)
    def _slice(self, event:int):
        self.sliced.emit(True)
    @Slot(result=bool)
    def _erase_blurred(self, event: int):
        self.erase_blurred.emit(True)
    def _erase_selected(self, event: int):
        self.erase_selected.emit(True)
#################################################################################
class CPushButton(QPushButton):
    def __init__(self, funct):
        super().__init__()
        self.setFixedSize(BUTTON_V_SIZE, BUTTON_V_SIZE)
        self.clicked.connect(funct)
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
        self._hidden = False

        # self._thumbnail_title = ''
        self.thumbnail_title = self.exif.original_name + '  ('  + self.exif.date.replace(' ', '/') + ')'
        reversed_date = '/'.join(list(reversed(self.exif.date.split(' '))))
        self.thumbnail_title = self.exif.original_name + '  (' + reversed_date + self.exif.date_suffix + ')'

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

        self.groupbox = QGroupBox(self.thumbnail_title)
        self.groupbox.setObjectName('thumb')
        self.groupbox.setFixedHeight(self._pixmap.height()+self.btn.height()+45)
        self.groupbox.setFixedWidth(int(1.0*self._pixmap.width()))
        layout.addWidget(self.groupbox)

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.setSpacing(0)
        self.groupbox.setLayout(vbox)
        vbox.addWidget(self._label)
        hbox.addWidget(self.btn, alignment=Qt.AlignmentFlag.AlignLeft)
        hbox.addStretch()
        hbox.addWidget(self.change_bg_color, alignment=Qt.AlignmentFlag.AlignRight)
        hbox.addWidget(self.select, alignment=Qt.AlignmentFlag.AlignRight)
        vbox.addLayout(hbox)
        vbox.setSpacing(0)
        vbox.addStretch()
#--------------------------------------------------------------------------------
    @property
    def hidden(self):
        return self._hidden
    @hidden.setter
    def hidden(self, flag: bool):
        self._hidden = flag
#--------------------------------------------------------------------------------
    def get_date_suffix(self):
        return self.exif.date_suffix
#--------------------------------------------------------------------------------
    def get_thumbnail_title(self):
        return self.thumbnail_title
#--------------------------------------------------------------------------------
    def set_thumbnail_title(self, title):
        self.groupbox.setTitle(title)
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
        self.selected.emit(True)
    @Slot(result=str)
    def _change_color(self, e: int):
        self.colored.emit(self.rank)
    @Slot(result=str)
    def hide(self):
        if self.btn.isChecked():
            self.hidden = True
            self.blur_pixmap()
            self.update_hide_button(True)
        else:
            self.hidden = False
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
