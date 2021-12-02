import pyqtgraph as pg
from PyQt5 import QtCore
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QComboBox, QSpinBox
from astropy.convolution import convolve, Gaussian2DKernel

from .ImageViewer import ImageViewer


class PositionMarker(QtCore.QObject):
    x = 0
    y = 0
    r = 0
    color = (0, 255, 0)

    def __init__(self):
        super().__init__()

        self.cross = pg.PlotDataItem(symbolBrush=self.color,
                                     symbolPen=None,
                                     symbolSize=30, symbol='+', pen=None)

        self.circle = pg.QtGui.QGraphicsEllipseItem(10, 10, self.r, self.r)
        self.circle.setPen(pg.mkPen(self.color, width=5))
        self.circle.setVisible(False)

    def setPositon(self, x, y):
        self.x = x
        self.y = y
        self.updatePlot()

    def setRadius(self, r):
        self.r = r
        self.circle.setVisible(r > 0)
        self.updatePlot()

    def updatePlot(self):
        self.cross.setData([self.x + .5, ], [self.y + .5, ])
        self.circle.setRect(0.5 + self.x - self.r,
                            0.5 + self.y - self.r,
                            2 * self.r, 2 * self.r)

    def addTo(self, vb: pg.ViewBox):
        vb.addItem(self.cross)
        vb.addItem(self.circle)


class PyCubeImageViewerPanel(ImageViewer):
    sigPosChanged = QtCore.pyqtSignal(int, int)

    def __init__(self, colormap='inferno'):
        super().__init__()
        self.ima0 = None
        self.sb_smooth = QSpinBox()
        self.sb_smooth.setRange(0, 15)
        self.sb_smooth.setSingleStep(1)

        self.cb_cmap = QComboBox()
        cmaps = ["cividis", "viridis", "inferno", "magma", "plasma"]
        self.cb_cmap.addItems(cmaps)
        self.label_imagemode = QLabel("A")

        self.cb_cmap.setCurrentText(colormap)
        self.cbCmapChanged()

        self.topBox.setSpacing(5)
        self.topBox.setContentsMargins(5, 5, 5, 5)

        topLayout = QHBoxLayout()

        topLayout.addWidget(QLabel("smooth"))
        topLayout.addWidget(self.sb_smooth)
        topLayout.addSpacing(20)
        topLayout.addWidget(QLabel("cmap"))
        topLayout.addWidget(self.cb_cmap)
        topLayout.addSpacing(20)
        topLayout.addWidget(self.label_imagemode)
        topLayout.addStretch(1)

        self.topBox.addLayout(topLayout)

        # markers
        self.markerColor = (0, 204, 0)
        self.markerColor2 = (204, 0, 0)

        self.posMarker = PositionMarker()
        PositionMarker.color = self.markerColor
        self.posMarker.addTo(self.wid_image.vb)
        self.posMarker2 = pg.PlotDataItem([100], [100], symbolBrush=self.markerColor2,
                                          symbolPen=None,
                                          symbolSize=30, symbol='x', pen=None)
        self.posMarker2.setVisible(False)
        self.wid_image.vb.addItem(self.posMarker2)

        self.cb_cmap.currentIndexChanged.connect(self.cbCmapChanged)

        self.wid_image.vb.sigKeyPress.connect(self.keyPressed)
        self.sb_smooth.valueChanged.connect(self.updateImaSmo)

    def setPosMarker(self, x, y):
        self.posMarker.setPositon(x, y)

    def setPosMarker2(self):
        self.posMarker2.setVisible(True)
        self.posMarker2.setData(*self.posMarker.cross.getData())

    def cbCmapChanged(self):
        c = self.cb_cmap.currentText()
        self.setColorMap(c)

    def updateImaSmo(self):
        smo = self.sb_smooth.value()
        if smo > 0:
            kernel = Gaussian2DKernel(smo)
            ima = convolve(self.ima0, kernel)
        else:
            ima = self.ima0
        super().updateImage(ima)

    def updateImage(self, ima, autorange=False):
        self.ima0 = ima
        self.updateImaSmo()

    def keyPressed(self, ev):
        if ev.key() == QtCore.Qt.Key_Space:
            x = self.xCur
            y = self.yCur
            self.posMarker.setPositon(x, y)
            self.sigPosChanged.emit(x, y)
