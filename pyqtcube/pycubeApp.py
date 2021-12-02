import signal
import sys
from functools import partial

import astropy.units as u
import numpy as np
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, \
    QVBoxLayout, QSplitter, QAction, \
    QMessageBox

from .DataCube import DataCube
from .PyCubeImageViewer import PyCubeImageViewerPanel
from .SpecViewer import SpecViewer
from .SubPlot import SubplotController


def __sigint_handler(*args):
    """Handler for the SIGINT signal."""
    sys.stderr.write('\r')
    QApplication.quit()


class Window(QMainWindow):
    def __init__(self, parent=None):
        super().__init__()
        self.title = "PyCube"
        self.cube = None
        self.x = None
        self.y = None
        self.z = None
        self.imageviewer = PyCubeImageViewerPanel()
        self.specviewer = SpecViewer()

        self.imageModes = [
            'Single Line',
            'Line band',
            'Line band - continuum'
        ]
        self.imageMode = 0

        self.subplotController = SubplotController()
        self.subplotController.linkTo(self.specviewer)

        self.initUI()
        self.initMenu()

        # setup
        self.setWindowTitle(self.title)

        self.imageviewer.wid_magnifier.sizeZoom = 5
        #        self.imageviewer.wid_magnifier.markerColor = 'g'
        #        self.imageviewer.wid_panner.markerColor = 'g'

        self.show()

        self.imageviewer.sigPosChanged.connect(self.posChanged)

        self.specviewer.sigSpecChange.connect(self.specChanged)
        self.specviewer.sigRadiusChanged.connect(self.radiusChanged)

    #    @property
    #    def ima(self):
    #        return self.imaFunc()

    def initUI(self):
        mainbox = QVBoxLayout()
        mainbox.setSpacing(2)
        mainbox.setContentsMargins(0, 0, 0, 0)
        # create the splitter in mainbox
        splitter = QSplitter(Qt.Vertical)
        mainbox.addWidget(splitter)
        window = QWidget()
        window.setLayout(mainbox)
        self.setCentralWidget(window)

        splitter.addWidget(self.imageviewer)
        splitter.addWidget(self.specviewer)

    def initMenu(self):
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('&File')
        modeMenu = mainMenu.addMenu('&Mode')
        specMenu = mainMenu.addMenu('Spectra')

        exitButton = QAction('Exit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.triggered.connect(self.close)
        fileMenu.addAction(exitButton)

        for i, m in enumerate(self.imageModes):
            modeButton = QAction(m, self)
            modeButton.setShortcut('Ctrl+%d' % (i + 1))
            modeButton.triggered.connect(partial(self.setmode, i))
            modeMenu.addAction(modeButton)

        linesButton = QAction("Show reference lines", self)
        linesButton.setShortcut("Ctrl+L")
        linesButton.triggered.connect(self.specviewer.zLineController.showDialog)
        specMenu.addAction(linesButton)

        subsource = QAction("Set secondary source for Spectal Zooom Plots", self)
        subsource.setShortcut("Ctrl+S")
        subsource.triggered.connect(self.setSubplotSource)
        specMenu.addAction(subsource)

        a = QAction("Show All Spectal Zooom Plots", self)
        a.triggered.connect(self.subplotController.showAll)
        specMenu.addAction(a)
        a = QAction("Hide All Spectal Zooom Plots", self)
        a.triggered.connect(self.subplotController.hideAll)
        specMenu.addAction(a)

    def setWavelenghtUnit(self, s):
        if type(s) == str:
            ss = u.Unit(s)
        elif type(s) == u.Unit:
            ss = s
        else:
            raise TypeError

        self.specviewer.wavelenght_unit = ss

    def imageSingleLine(self):
        return self.cube.get_channel(self.z)

    def imageBand(self):
        wu = self.specviewer.wavelenght_unit
        c1, c2 = self.specviewer.regionC.getRegion()
        return self.cube.get_image_band(c1 * wu, c2 * wu)

    def imageBandContinummSubtracted(self):
        wu = self.specviewer.wavelenght_unit
        c1, c2 = self.specviewer.regionC.getRegion()
        b1, b2 = self.specviewer.regionB.getRegion()
        r1, r2 = self.specviewer.regionR.getRegion()

        fluxc = self.cube.get_image_band(c1 * wu, c2 * wu)
        fluxb = self.cube.get_image_band(b1 * wu, b2 * wu)
        fluxr = self.cube.get_image_band(r1 * wu, r2 * wu)

        c = 0.5 * (c1 + c2)
        r = 0.5 * (r1 + r2)
        b = 0.5 * (b1 + b2)
        k = (c - b) / (r - b)
        return fluxc - (k * fluxb + (1 - k) * fluxr)

    def showError(self, s):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(s)
        msg.setWindowTitle("Error")
        msg.exec_()

    def checkBand(self, b, e):
        c1, c2 = b.getRegion()
        if c1 == c2:
            self.showError(e + " not defined")
        return c1 == c2

    def setmode(self, m):
        self.specviewer.viewRegionMode = m != 0
        self.specviewer.applyRegionMode()

        if m == 0:
            self.ima = self.imageSingleLine()
            self.imageviewer.updateImage(self.ima)
        elif m == 1:
            if self.checkBand(self.specviewer.regionC, "Line band"): return
            self.ima = self.imageBand()
            self.imageviewer.updateImage(self.ima)
        elif m == 2:
            if self.checkBand(self.specviewer.regionC, "Line band"): return
            if self.checkBand(self.specviewer.regionB, "Blue band"): return
            if self.checkBand(self.specviewer.regionR, "Red band"): return
            self.ima = self.imageBandContinummSubtracted()
            self.imageviewer.updateImage(self.ima)
        self.imageMode = m
        self.imageviewer.label_imagemode.setText(self.imageModes[m])

    def setSubplotSource(self):
        self.subplotController.setData2()
        self.imageviewer.setPosMarker2()

    def posChanged(self, x, y):
        self.x = x
        self.y = y
        self.specviewer.updateSpec(self.cube.get_1dSpec(self.x, self.y))
        self.subplotController.setData1()

    def radiusChanged(self, r):
        self.imageviewer.posMarker.setRadius(r)
        self.r = r
        self.specviewer.updateSpec(self.cube.get_1dSpec(self.x, self.y, r=r))
        self.subplotController.setData1()

    def specChanged(self, idx):
        self.z = idx

        self.ima = self.imageSingleLine()
        self.imageviewer.updateImage(self.ima)

    def setCube(self, cube: DataCube):
        self.cube = cube
        nz, ny, nx = cube.shape
        self.z = nz // 2
        #        self.z=self.cube.closest_spectral_channel(6842*u.AA)
        ima = cube.get_channel(self.z)
        self.y, self.x = np.unravel_index(np.nanargmax(ima, axis=None), ima.shape)

        self.imageviewer.wcs = cube.wcs.celestial
        self.setmode(0)
        self.imageviewer.wid_image.vb.autoRange(padding=0)
        self.imageviewer.posMarker.setPositon(self.x, self.y)

        self.specviewer.setWavelengts(self.cube.wavelenght)
        self.specviewer.updateSpec(self.cube.get_1dSpec(self.x, self.y))
        self.specviewer.setVlineId(self.z)

    #        self.imageviewer.updateImage(ima)
    #        self.imageviewer.setPosMarker(x,y)

    def closeEvent(self, *args) -> None:
        super(Window, self).closeEvent(*args)
        app = QApplication.instance()
        app.closeAllWindows()


def run(cube: DataCube = None):
    signal.signal(signal.SIGINT, __sigint_handler)

    app = QApplication(sys.argv)
    window = Window()

    s = """

*{
    color: #ffffff;
    background-color:rgb(51,51,51);
    }
        QLineEdit:disabled{ 
        background-color: rgb(51,51,51);
        }

        QLineEdit,QSpinBox,QComboBox { 
        background-color: rgb(70,70,70);
        }
    """
    #    with open("ccc.css") as ff:
    #        s=ff.read()

    app.setStyleSheet(s)

    #    from qt_material import apply_stylesheet
    #    apply_stylesheet(app, theme='dark_teal.xml',save_as="ccc.css")

    #    window.setWavelenghtUnit("nm")
    window.setCube(cube)

    rec = window.screen().availableGeometry()
    w = min(1000, rec.width())
    h = min(1000, rec.height())
    window.resize(w, h)

    timer = QTimer()
    timer.start(100)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.
    sys.exit(app.exec_())
