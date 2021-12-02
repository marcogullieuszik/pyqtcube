import warnings

import astropy.wcs.utils as wcsutils
import pyqtgraph as pg
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QLabel, QCheckBox, \
    QGraphicsRectItem
from astropy import visualization as vis

from .CustomWidgets import FloatLineEdit, ViewBoxKey

warnings.filterwarnings("ignore")

pg.setConfigOptions(imageAxisOrder='row-major')
pg.setConfigOptions(antialias=True)


class MyQSimpleImage(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.ci.layout.setContentsMargins(0, 0, 0, 0)
        self.ci.layout.setSpacing(0)  # might not be necessary for you
        self.vb = ViewBoxKey(border=(66, 66, 66), enableMenu=False)
        self.setBackground('k')
        self.vb.autoRange(padding=0)
        self.vb.setAspectLocked(True)

        self.img = pg.ImageItem()
        self.vb.addItem(self.img)
        self.addItem(self.vb)

    def setImage(self, ima):
        self.img.setImage(ima)


class MainImage(MyQSimpleImage):
    def __init__(self, parent=None):
        super().__init__(parent=parent)


class MagnifierImage(MyQSimpleImage):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # square at the center of the zooming area
        self.__vv = pg.ViewBox(enableMenu=False)
        self.vb.scene().addItem(self.__vv)
        x = [-.5, .5, .5, -.5, -.5]
        y = [-.5, -.5, .5, .5, -.5]
        self.__p = pg.PlotDataItem(x, y)
        self.__vv.setMouseEnabled(False, False)

        self.__vv.addItem(self.__p)
        self.__vv.setZValue(99)
        self.vb.sigResized.connect(lambda: self.__vv.setGeometry(self.vb.sceneBoundingRect()))
        self.sizeZoom = 3

        self.markerColor = 'r'

    def updatePos(self, x, y):
        self.vb.setRange(
            xRange=(x - self.sizeZoom, x + self.sizeZoom),
            yRange=(y - self.sizeZoom, y + self.sizeZoom),
            padding=0
        )

        self.img.setVisible(True)

    @property
    def markerColor(self):
        return self._markerColor

    @markerColor.setter
    def markerColor(self, c):
        self._markerColor = c
        pen = pg.mkPen(color=c, width=3)
        self.__p.setPen(pen)

    @property
    def sizeZoom(self):
        return self._sizeZoom

    @sizeZoom.setter
    def sizeZoom(self, v):
        self._sizeZoom = v
        self.__vv.setRange(
            xRange=[-v, v],
            yRange=[-v, v],
            padding=0)


class PannerRect(QGraphicsRectItem):

    def __init__(self, parent=None):
        super(PannerRect, self).__init__(parent=parent)


class PannerImage(MyQSimpleImage):
    markerColor = 'r'
    sigPanRectMoved2 = QtCore.pyqtSignal(float, float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(200, 200)

        self.vb.setMouseEnabled(False, False)

        self.rect1 = PannerRect()
        # self.rect1.setFlag(QGraphicsItem.ItemIsMovable)
        self.vb.addItem(self.rect1, ignoreBounds=True)

        self.setPanRect(50, 50, 200, 200)
        self.markerColor = 'r'

    @property
    def markerColor(self):
        return self._markerColor

    @markerColor.setter
    def markerColor(self, c):
        self._markerColor = c
        pen = pg.mkPen(color=c, width=3)
        self.rect1.setPen(pen)

    def setPanRect(self, x1, y1, w, h):
        self.rect1.setRect(x1, y1, w, h)


class ImageViewer(QWidget):
    def __init__(self):
        super(ImageViewer, self).__init__()
        self.ima = None
        self.wcs = None

        self.xCur = 0
        self.yCur = 0

        self.wid_magnifier = MagnifierImage(parent=self)
        self.wid_image = MainImage(parent=self)
        self.wid_panner = PannerImage(parent=self)

        self.le_x = QLineEdit()
        self.le_y = QLineEdit()
        self.le_ra = QLineEdit()
        self.le_de = QLineEdit()
        self.le_v = QLineEdit()
        self.le_zmin = FloatLineEdit()
        self.le_zmax = FloatLineEdit()

        self.le_x.setReadOnly(True)
        self.le_y.setReadOnly(True)
        self.le_ra.setReadOnly(True)
        self.le_de.setReadOnly(True)
        self.le_v.setReadOnly(True)
        self.cb_autoscale = QCheckBox("auto scale")

        self.cb_autoscale.setChecked(True)
        self.le_zmin.setEnabled(False)
        self.le_zmax.setEnabled(False)

        self.wid_magnifier.setFixedSize(200, 200)
        self.wid_panner.setFixedSize(200, 200)

        mainbox0 = QVBoxLayout()
        self.topBox = QHBoxLayout()
        mainbox0.addLayout(self.topBox)

        mainbox = QHBoxLayout()
        mainbox0.addLayout(mainbox)
        mainbox.setSpacing(2)
        mainbox.setContentsMargins(0, 0, 0, 0)

        leftBox = QVBoxLayout()
        mainbox.addLayout(leftBox, stretch=0)

        gridContainer = QWidget()
        gridContainer.setFixedWidth(200)
        grid = QGridLayout(gridContainer)
        v = [
            ["value", self.le_v],
            ["x", self.le_x],
            ["y", self.le_y],
            ["RA", self.le_ra],
            ["DEC", self.le_de],
            ["min", self.le_zmin],
            ["max", self.le_zmax],
        ]
        for i, (l, w) in enumerate(v):
            _ = QLabel(l)
            _.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            grid.addWidget(_, i, 0)
            grid.addWidget(w, i, 1)

        leftBox.addWidget(self.wid_magnifier)
        leftBox.addWidget(gridContainer)
        leftBox.addWidget(self.cb_autoscale)

        leftBox.addStretch(1)
        leftBox.addWidget(self.wid_panner)
        mainbox.addWidget(self.wid_image)

        self.setLayout(mainbox0)

        self.cb_autoscale.setEnabled(False)
        self.le_zmin.returnPressed.connect(self.zvaluesChanged)
        self.le_zmax.returnPressed.connect(self.zvaluesChanged)
        self.cb_autoscale.toggled.connect(self.autoscaleToggled)

    def rangeChanged(self):
        [xmin, xmax], [ymin, ymax] = self.wid_image.vb.viewRange()

        dx = xmax - xmin
        dy = ymax - ymin

        self.wid_panner.setPanRect(xmin, ymin, dx, dy)

    def autoscaleToggled(self, state):
        self.le_zmin.setEnabled(not state)
        self.le_zmax.setEnabled(not state)
        if state:
            self.zautoscale()

    def zautoscale(self):
        zmin, zmax = vis.ZScaleInterval().get_limits(self.ima)
        self.le_zmin.setText(str(zmin))
        self.le_zmax.setText(str(zmax))
        self.zvaluesChanged()

    def zvaluesChanged(self):
        zmin = float(self.le_zmin.text())
        zmax = float(self.le_zmax.text())
        for w in [self.wid_image, self.wid_magnifier, self.wid_panner]:
            w.img.setLevels((zmin, zmax))

    def mouseMoved(self, pos):

        x = self.wid_image.img.mapFromScene(pos).x()
        y = self.wid_image.img.mapFromScene(pos).y()
        self.wid_magnifier.updatePos(x, y)

        # #        set min max levels to the values around mouse pos
        #         _x=int(x)
        #         _y=int(y)
        #         d=self.wid_magnifier.sizeZoom
        #         _ima=self.ima[_y-d:_y+d,_x-d:_x+d]
        #         #z1,z2=self.wid_image.img.levels
        #         z1=_ima.min()
        #         z2=_ima.max()
        #         self.wid_magnifier.img.setLevels([z1,z2])
        #         self.wid_image.img.setLevels([z1,z2])

        if ((x >= 0) & (x <= self.ima.shape[1]) &
                (y >= 0) & (y <= self.ima.shape[0])):
            self.xCur = int(x)
            self.yCur = int(y)
            self.le_x.setText("%.1f" % x)
            self.le_y.setText("%.1f" % y)
            self.le_v.setText("%s" % self.ima[self.yCur, self.xCur])
            if self.wcs is not None:
                coo = wcsutils.pixel_to_skycoord(x, y, wcs=self.wcs)
                self.le_ra.setText(coo.ra.to_string(unit='hourangle', sep=":", precision=4))
                self.le_de.setText(coo.dec.to_string(unit='deg', sep=":", precision=4, alwayssign=True))

    def updateImage(self, ima, autorange=False):
        # if this is the 1st time the Image is loaded
        # then activate some signals
        if self.ima is None:
            self.wid_image.scene().sigMouseMoved.connect(self.mouseMoved)
            self.wid_image.vb.sigRangeChanged.connect(self.rangeChanged)

        self.cb_autoscale.setEnabled(True)

        self.ima = ima
        for i in (self.wid_image, self.wid_panner, self.wid_magnifier):
            i.setImage(ima)
            if (i != self.wid_image) | (autorange == True):
                i.vb.autoRange(padding=0)

        if self.cb_autoscale.checkState():
            self.zautoscale()
        else:
            self.zvaluesChanged()

    def setColorMap(self, colormap):
        cm = pg.colormap.get(colormap)
        lut = cm.getLookupTable(nPts=256)
        for i in (self.wid_image, self.wid_panner, self.wid_magnifier):
            i.img.setLookupTable(lut)
