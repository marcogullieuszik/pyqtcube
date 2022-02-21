import os
import warnings

import astropy.units as u
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QCheckBox, QSpinBox
from astropy.convolution import convolve, Gaussian1DKernel

from .CustomWidgets import PlotItemKey, AutoScaleController

warnings.filterwarnings("ignore")

pg.setConfigOptions(antialias=True)

pg.setConfigOptions(foreground='k')
pg.setConfigOptions(background='w')


class InfiniteZLine(pg.InfiniteLine):
    def __init__(self, pos=None, lam0=None, lab="", flag=True):
        pen = pg.mkPen((0, 0, 0, 50), width=1)
        super().__init__(pos=pos, angle=90, movable=True, pen=pen, hoverPen='b')
        self.lam0 = lam0
        self.lab = lab
        self.flag = bool(flag)
        self.textItem = pg.TextItem(lab, angle=90, color='k', anchor=(0, 0.5))
        self.textItem.setPos(pos, 0)
        self.setVisible(flag)
        self.textItem.setVisible(flag)

    def setVisible(self, b: bool):
        super().setVisible(b)
        self.textItem.setVisible(b)
        self.flag = b


class LineControllerWidget(QWidget):
    def __init__(self, line: InfiniteZLine):
        super().__init__()
        super().__init__()
        self.line = line
        self.cb = QCheckBox()
        self.cb.setChecked(line.flag)
        t2 = QLabel("%4d" % line.lam0)
        t1 = QLabel(line.lab)

        layout = QHBoxLayout()
        layout.addWidget(self.cb)
        layout.addWidget(t2)
        layout.addWidget(t1)
        layout.addStretch(1)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        self.setLayout(layout)
        self.cb.toggled.connect(self.toggled)

    def toggled(self):
        self.line.setVisible(self.cb.checkState())


class ZlineSelectDialog(QWidget):
    def __init__(self, lines: list[InfiniteZLine]):
        super().__init__()
        mainbox = QVBoxLayout()

        gridContainer = QWidget()
        grid = QGridLayout(gridContainer)
        grid.setContentsMargins(5, 5, 5, 5)
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(5)
        ncol = 3
        nrow = int(np.ceil(len(lines) / ncol))
        for i, line in enumerate(lines):
            grid.addWidget(LineControllerWidget(line), i % nrow, i // nrow)
        mainbox.addWidget(gridContainer)
        self.setLayout(mainbox)


class ZLineController(QtCore.QObject):
    sigRedshiftChanged = QtCore.pyqtSignal(float)

    def __init__(self, vbPlot, vbLab):
        super().__init__()
        self.z = 0
        self.lines = []
        self.vbLab = vbLab
        self.vbPlot = vbPlot
        ifile = os.path.join(
            os.path.dirname(__file__),
            'linelist_vacuum_air.txt')

        self.loadlineList(ifile)
        self.dialog = ZlineSelectDialog(self.lines)

    def lineDragged(self, line):
        self.z = (line.value() - line.lam0) / line.lam0
        for ll in self.lines:
            ll.setValue(ll.lam0 * (1 + self.z))
            ll.textItem.setPos(ll.lam0 * (1 + self.z), 0)
        self.sigRedshiftChanged.emit(self.z)

    def loadlineList(self, ifile):

        with open(ifile) as ff:
            for l in ff.readlines():
                if l.strip().startswith("#"): continue
                if l.strip() == "": continue
                vv = l.split()
                lam = float(vv[0])
                lab = vv[2]
                flag = bool(vv[3])
                l = InfiniteZLine(pos=lam, lam0=lam, lab=lab, flag=flag)
                self.vbPlot.addItem(l)
                self.vbLab.addItem(l.textItem)
                l.sigDragged.connect(self.lineDragged)
                self.lines.append(l)

    def showDialog(self):
        self.dialog.show()
        self.dialog.setFocus()
        self.dialog.activateWindow()


class SpecViewer(QWidget):
    penSpec = pg.mkPen((0, 0, 0), width=1)
    penVline = pg.mkPen((0, 255, 0, 204), width=1)
    penZline = pg.mkPen((204, 204, 204, 124), width=1)

    background = 'w'
    sigSpecChange = QtCore.pyqtSignal(int)
    sigRadiusChanged = QtCore.pyqtSignal(int)
    sigSubplotDefined = QtCore.pyqtSignal(float, float)

    wav = None
    spec = None
    redshift = 0
    idx = 0

    def __init__(self):
        super().__init__()
        self.spec = None
        self.wavelenght_unit = u.AA
        #        self.wav = None

        self.xMouse = None
        self.yMouse = None
        self.smooth = 0

        self.sb_smoothSpe = QSpinBox()
        self.sb_smoothSpe.setRange(0, 15)
        self.sb_smoothSpe.setSingleStep(1)

        self.sb_radiusSpe = QSpinBox()
        self.sb_radiusSpe.setRange(0, 15)

        self.le_redshift = QLabel("%s" % self.redshift)
        self.le_redshift.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self.label_position=QLabel("xy")
        self.editRegion = None
        self.viewRegionMode = False

        self.plotWidget = pg.GraphicsLayoutWidget()
        #        self.plotWidget.setBackground(self.background)

        self.vb0 = pg.ViewBox(enableMenu=False)  # border='r')
        self.plotWidget.ci.layout.setSpacing(0)

        self.vb0.setYRange(0, 1)
        self.plotWidget.addItem(self.vb0)
        self.vb0.setFixedHeight(50)
        self.plotWidget.nextRow()

        self.vb = PlotItemKey(enableMenu=False)
        self.plotWidget.addItem(self.vb)
        self.vb.getAxis('top').show()
        self.vb.getAxis('right').show()
        self.vb.getAxis('top').setStyle(showValues=False)
        self.vb.getAxis('right').setStyle(showValues=False)
        self.vb0.setXLink(self.vb)

        self.plotSpec = pg.PlotCurveItem(pen=self.penSpec)
        self.vb.addItem(self.plotSpec)

        self.zLineController = ZLineController(vbPlot=self.vb, vbLab=self.vb0)
        self.vline = pg.InfiniteLine(0, pen=self.penVline)
        self.vb.addItem(self.vline)

        kwd = dict(movable=False, hoverBrush=None, hoverPen=None)
        self.regionC = pg.LinearRegionItem([0, 0], brush=(0, 255, 0, 102), **kwd)
        self.regionB = pg.LinearRegionItem([0, 0], brush=(0, 0, 255, 102), **kwd)
        self.regionR = pg.LinearRegionItem([0, 0], brush=(255, 0, 0, 102), **kwd)
        self.regionZ = pg.LinearRegionItem([0, 0], brush=(102, 102, 102, 102), **kwd)
        self.vb.addItem(self.regionC)
        self.vb.addItem(self.regionB)
        self.vb.addItem(self.regionR)
        self.vb.addItem(self.regionZ)
        self.applyRegionMode()

        self.initUI()

        self.vb.scene().sigMouseMoved.connect(self.mouseMoved)
        self.vb.sigKeyPress.connect(self.keyPressed)
        self.vb.sigKeyRelease.connect(self.keyReleased)

        self.sb_smoothSpe.valueChanged.connect(self.smoothchange)
        self.zLineController.sigRedshiftChanged.connect(self.redshiftChanged)
        self.sb_radiusSpe.valueChanged.connect(self.specRadiuschange)
        self.plotWidget.setContentsMargins(5, 5, 5, 5)

    @property
    def wav(self):
        return (self._wav.to(self.wavelenght_unit)).value

    def initUI(self):
        mainbox = QVBoxLayout(self)
        mainbox.setSpacing(5)
        mainbox.setContentsMargins(5, 5, 5, 5)

        topBox = QHBoxLayout()

        cb_autoscale = AutoScaleController(self.vb, label="auto-scale Y")
        topBox.addWidget(cb_autoscale, stretch=0)
        topBox.addSpacing(20)
        topBox.addWidget(QLabel("smooth"))
        topBox.addWidget(self.sb_smoothSpe)
        topBox.addSpacing(20)
        topBox.addWidget(QLabel("radius"))
        topBox.addWidget(self.sb_radiusSpe)
        topBox.addSpacing(20)
        topBox.addWidget(QLabel("z="))
        topBox.addWidget(self.le_redshift)
        topBox.addStretch(1)
        topBox.addWidget(self.label_position)

        mainbox.addLayout(topBox)

        mainbox.addWidget(self.plotWidget)

    def applyRegionMode(self):
        self.vline.setVisible(not self.viewRegionMode)
        self.regionC.setVisible(self.viewRegionMode)
        self.regionB.setVisible(self.viewRegionMode)
        self.regionR.setVisible(self.viewRegionMode)

    def setWavelengts(self, w):
        self._wav = w

        self.vb.setLimits(xMin=self.wav.min(), xMax=self.wav.max())

    def updateLabelPos(self,s):
        self.label_position.setText(s)

    def updateSpec(self, v):
        self.spec = v
        self.updateSpecPlot()

    #    def setSpec(self, x, y):
    #        self.wav = x
    #        self.spec = y
    #        self.vb.setLimits(xMin=self.wav.min(), xMax=self.wav.max())
    #
    #        self.updateSpecPlot()

    def updateSpecPlot(self):
        if self.smooth == 0:
            y = self.spec
        else:
            kernel = Gaussian1DKernel(self.smooth)
            y = convolve(self.spec, kernel)

        self.plotSpec.setData(self.wav, y)

        self.vb.setAutoVisible(y=True)

    def smoothchange(self):
        self.smooth = self.sb_smoothSpe.value()
        self.updateSpecPlot()

    def specRadiuschange(self):
        r = self.sb_radiusSpe.value()
        self.sigRadiusChanged.emit(r)

    def mouseMoved(self, pos):
        """ set the mouse position"""
        self.xMouse = self.plotSpec.mapFromScene(pos).x()
        self.yMouse = self.plotSpec.mapFromScene(pos).y()

        if self.editRegion is not None:
            r0 = self.editRegion.lines[0].value()
            self.editRegion.setRegion((r0, self.xMouse))

    def setVlineId(self, idx):
        self.idx = idx
        val = self.wav[idx]
        self.setVlinePos(val)

    def setVlinePos(self, val):
        self.vline.setValue(val)

    def redshiftChanged(self, z):
        self.redshift = z
        self.le_redshift.setText("%.7f" % z)

    def keyPressed(self, ev):
        # print ("keyPressed",ev.key)

        if not self.viewRegionMode:
            if (ev.key() == QtCore.Qt.Key_I):
                idx = np.argmin(np.abs(self.wav - self.xMouse))
                if self.idx == idx: return
                self.idx = idx
                self.setVlineId(idx)
                self.sigSpecChange.emit(self.idx)

            if ev.key() == QtCore.Qt.Key_Right:
                self.idx += 1
                self.setVlineId(self.idx)
                self.sigSpecChange.emit(self.idx)

            if ev.key() == QtCore.Qt.Key_Left:
                self.idx -= 1
                self.setVlineId(self.idx)
                self.sigSpecChange.emit(self.idx)

        # here return if event is triggered by repeated keyPress
        if ev.isAutoRepeat(): return

        if ev.key() == QtCore.Qt.Key_J:
            xx, yy = self.vb.viewRange()
            xx[0] = self.xMouse
            self.vb.setXRange(*xx, padding=0)

        if ev.key() == QtCore.Qt.Key_K:
            xx, yy = self.vb.viewRange()
            xx[1] = self.xMouse
            self.vb.setXRange(*xx, padding=0)

        if ev.key() == QtCore.Qt.Key_L:
            self.vb.enableAutoRange(x=True)

        if ev.key() == QtCore.Qt.Key_R:
            self.viewRegionMode = not self.viewRegionMode
            self.applyRegionMode()

        v = [
            [QtCore.Qt.Key_X, self.regionB],
            [QtCore.Qt.Key_C, self.regionC],
            [QtCore.Qt.Key_V, self.regionR],
        ]
        for k, r in v:
            if ev.key() == k:
                self.viewRegionMode = True
                self.applyRegionMode()
                self.editRegion = r
                self.editRegion.setRegion([self.xMouse, self.xMouse])

        if ev.key() == QtCore.Qt.Key_Z:
            self.editRegion = self.regionZ
            self.editRegion.setRegion([self.xMouse, self.xMouse])
            self.regionZ.setVisible(True)

    def keyReleased(self, ev):
        if ev.isAutoRepeat(): return
        if self.editRegion is not None:
            if ev.key() == QtCore.Qt.Key_Z:
                self.editRegion.setVisible(False)
                self.sigSubplotDefined.emit(*self.regionZ.getRegion())
            self.editRegion = None
