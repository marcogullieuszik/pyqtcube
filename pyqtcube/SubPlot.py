import pyqtgraph as pg
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox

from .CustomWidgets import SliderText
from .SpecViewer import SpecViewer

pg.setConfigOptions(antialias=True)

vel_c = 299792.458


class SubplotController(object):
    def __init__(self, spec1Color='k', spec2Color='r'):
        self.spec1Color = spec1Color
        self.spec2Color = spec2Color
        self.subplots = []
        self.x2 = None
        self.y2 = None
        self.vel = 0
        self.o = None

    def linkTo(self, o: SpecViewer):
        self.o = o
        self.o.sigSubplotDefined.connect(self.createSubplot)

    def createSubplot(self, v1, v2, parent=None):

        sub1 = SubPlot(v1, v2, spec1Color=self.spec1Color, spec2Color=self.spec2Color)
        sub1.setVel(self.vel)
        sub1.setData1(self.x1, self.y1)
        sub1.setData2(self.x2, self.y2)
        sub1.slider.sigValueChanged.connect(self.changeVel)
        self.subplots.append(sub1)

    def showAll(self):
        for w in self.subplots:
            w.raise_()
            w.show()

    def hideAll(self):
        for w in self.subplots:
            w.hide()

    @property
    def x1(self):
        return self.o.wav

    @property
    def y1(self):
        return self.o.spec

    def changeVel(self, v):
        self.vel = v
        for s in self.subplots:
            s.slider.blockSignals(True)
            s.setVel(v)
            s.slider.blockSignals(False)
        if self.x2 is not None:
            self.plotData2()

    def setData1(self):
        for s in self.subplots:
            s.setData1(self.x1, self.y1)

    def setData2(self):
        self.x2 = self.x1
        self.y2 = self.y1
        self.plotData2()

    def plotData2(self):
        for s in self.subplots:
            s.setData2(self.x2 * (1 + self.vel / vel_c), self.y2)


class SubPlot(QMainWindow):
    def __init__(self, v1, v2,
                 spec1Color='k',
                 spec2Color='r'):
        super().__init__()
        self.title = "SubPlot"
        self.setWindowTitle(self.title)
        mainbox = QVBoxLayout()

        pw = pg.PlotWidget()
        self.p1 = pw.plotItem
        self.p1.setLabels(left='Spectrum1')
        self.p1.setAutoVisible(y=True)
        # create a new ViewBox, link the right axis to its coordinate system
        self.p2 = pg.ViewBox()
        self.p1.showAxis('right')
        self.p1.scene().addItem(self.p2)
        self.p1.getAxis('right').linkToView(self.p2)
        self.p2.setXLink(self.p1)
        self.p1.getAxis('right').setLabel('Spectrum2', color=spec2Color)
        self.p2.setAutoVisible(y=True)

        self.updateViews()
        self.p1.vb.sigResized.connect(self.updateViews)

        pen1 = pg.mkPen(spec1Color, width=1)
        pen2 = pg.mkPen(spec2Color, width=1)
        self.plot1 = self.p1.plot(pen=pen1)
        self.plot2 = pg.PlotCurveItem(pen=pen2)

        self.p2.addItem(self.plot2)

        topBox = QHBoxLayout()
        self.cb = QCheckBox("auto scale")
        self.slider = SliderText(label="V", vmin=-500, vmax=500, step=2)

        topBox.addWidget(self.cb)
        topBox.addWidget(self.slider)

        mainbox.addLayout(topBox)
        mainbox.addWidget(pw)

        widget = QWidget()
        widget.setLayout(mainbox)
        self.setCentralWidget(widget)
        #    self.setLayout(mainbox)

        self.cb.toggled.connect(self.cb_toggle)
        self.p1.vb.sigStateChanged.connect(self.updatecb)

        self.p1.setXRange(v1, v2)

        self.show()

    def setVel(self, v):
        self.slider.setValue(v)

    def updatecb(self, vb):
        self.cb.setChecked(bool(vb.getState()['autoRange'][1]))

    def cb_toggle(self, ev):
        self.plot1.getViewBox().enableAutoRange(axis='y', enable=ev)

    def setData1(self, x, y):
        self.plot1.setData(x, y)

    def setData2(self, x, y):
        self.plot2.setData(x, y)

    def updateViews(self):
        # view has resized; update auxiliary views to match
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
        self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)
