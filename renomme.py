import sys
from pathlib import Path

import rawpy
import imageio
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget, QVBoxLayout, QPushButton, QGroupBox
from PySide6.QtGui import QPixmap
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
        central_widget.setLayout(main_layout)

        display_wdg = QLabel('toto')
        pixmap = QPixmap('./pictures/thumbails/_DSC8143.jpeg')
        display_wdg.setPixmap(pixmap)
        main_layout.addWidget(display_wdg)
        

#################################################################################
class Photo():
    def __init__(self, exif) -> None:
        pass
#################################################################################
def main() -> bool:
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.setFixedSize(main_size)
    main_window.setWindowTitle("Renommage des photos")
    
    f = QFile("./style.qss")
    f.open(QIODevice.ReadOnly)
    app.setStyleSheet(QTextStream(f).readAll())

    main_window.show()
    sys.exit(app.exec())

    return True


################################################################################
from PySide6.QtGui import QIcon, QFont, QPixmap, QMovie, QRegion
from PySide6.QtCore import Qt



class Vignette(QWidget):
    def __init__(self):
        super().__init__()

        #self.setGeometry(200, 200, 700, 400)
        self.setWindowTitle("Vignette")
        self.setWindowIcon(QIcon('qt.png'))

        layout  = QGridLayout()
        self.setLayout(layout)

        groupbox = QGroupBox("_DSC8149.jpeg")

        layout.addWidget(groupbox)

        vbox = QVBoxLayout()
        groupbox.setLayout(vbox)

        label = QLabel(self)
        pixmap = QPixmap("./pictures/thumbnails/_DSC8149.jpeg")
        pixmap = pixmap.scaled(QSize(250,250), Qt.AspectRatioMode.KeepAspectRatio)
        label.setPixmap(pixmap)

        titre = QLabel("_DSC8149.jpeg")
        print(pixmap.size())
        titre.setAlignment(Qt.AlignCenter)
        titre.setStyleSheet("padding: 10px 10px 0px 10px")

        btn = QPushButton("Supprimer")

        vbox.addWidget(label)
        #vbox.addWidget(titre)
        vbox.addWidget(btn)
        vbox.setSpacing(0)
        vbox.addStretch()


app = QApplication(sys.argv)
window = Vignette()
window.show()
sys.exit(app.exec())

# if __name__ == '__main__':
#     main()