import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QWidget, QSizePolicy, \
    QCheckBox, QLineEdit, QLabel, QSlider, QHBoxLayout


class FloatValidator(QtGui.QValidator):
    validationChanged = QtCore.pyqtSignal(QtGui.QValidator.State)

    def __init__(self, parent=None):
        super().__init__(parent)

    def validate(self, s, pos):
        if (s == "") | (s == "-"):
            state = QtGui.QValidator.Intermediate
            self.validationChanged.emit(state)
            return state, s, pos

        if s == ".":
            s = "0."
            pos = 2
        try:
            float(s)
            state = QtGui.QValidator.Acceptable
            self.validationChanged.emit(state)
            out = (state, s, pos)
        except:
            if "e" in s:
                state = QtGui.QValidator.Intermediate
            else:
                state = QtGui.QValidator.Invalid

            out = (state, s, pos)

        self.validationChanged.emit(state)
        return out


class FloatLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        validator = FloatValidator()
        self.setValidator(validator)
        validator.validationChanged.connect(self.handleValidationChange)

    def handleValidationChange(self, state):
        if state == QtGui.QValidator.Invalid:
            colour = 'red'
        elif state == QtGui.QValidator.Intermediate:
            colour = 'gold'
        elif state == QtGui.QValidator.Acceptable:
            self.setStyleSheet('')
            return
        #            colour = 'lime'
        self.setStyleSheet('border: 3px solid %s' % colour)

        QtCore.QTimer.singleShot(1000, lambda: self.setStyleSheet(''))

    def focusOutEvent(self, a0: QtGui.QFocusEvent) -> None:
        super().focusOutEvent(a0)
        state = self.validator().validate(self.text(), 0)[0]
        while state != QtGui.QValidator.Acceptable:
            self.undo()
            state = self.validator().validate(self.text(), 0)[0]
            self.setCursorPosition(0)


class ViewBoxKey(pg.ViewBox):
    """
    A pyqtgraph.ViewVox that emits KeyboardEvent signals
    """
    sigKeyPress = QtCore.pyqtSignal(object)
    sigKeyRelease = QtCore.pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def keyPressEvent(self, ev):
        # if not ev.isAutoRepeat():
        self.sigKeyPress.emit(ev)

    def keyReleaseEvent(self, ev):
        # if not ev.isAutoRepeat():
        self.sigKeyRelease.emit(ev)


class PlotItemKey(pg.PlotItem):
    """
    A pyqtgraph.ViewVox that emits KeyboardEvent signals
    """
    sigKeyPress = QtCore.pyqtSignal(object)
    sigKeyRelease = QtCore.pyqtSignal(object)
    sigHoverIn = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def keyPressEvent(self, ev):
        # if not ev.isAutoRepeat():
        self.sigKeyPress.emit(ev)

    def keyReleaseEvent(self, ev):
        # if not ev.isAutoRepeat():
        self.sigKeyRelease.emit(ev)


class AutoScaleController(QWidget):

    def __init__(self, viewBox, label="auto scale"):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        if isinstance(viewBox, pg.PlotItem):
            self.vb = viewBox.vb
        else:
            self.vb = viewBox

        mainbox = QHBoxLayout()
        mainbox.setSpacing(5)
        mainbox.setContentsMargins(0, 0, 0, 0)

        self.le_min = FloatLineEdit()
        self.le_max = FloatLineEdit()
        self.le_min.setFixedWidth(150)
        self.le_max.setFixedWidth(150)

        mainbox.addWidget(QLabel("Ymin"))
        mainbox.addWidget(self.le_min, stretch=0)
        mainbox.addWidget(QLabel("Ymax"))
        mainbox.addWidget(self.le_max)

        self.cb = QCheckBox(label)
        mainbox.addWidget(self.cb)
        self.setLayout(mainbox)

        self.vb.sigStateChanged.connect(self.__updatecb)
        self.cb.toggled.connect(self.__cb_toggle)

        self.vb.sigYRangeChanged.connect(self.__updateYRangeVals)
        self.le_min.returnPressed.connect(self.__updateYRange)
        self.le_max.returnPressed.connect(self.__updateYRange)

    def __updateYRange(self):
        vmin = float(self.le_min.text())
        vmax = float(self.le_max.text())

        if vmin >= vmax:
            msg = QMessageBox.critical(self, "Critical Error",
                                       "The maximum value is smaller than the minimum \n\n correct and retry!")
            return
        self.vb.setYRange(vmin, vmax, padding=0)

    def __updateYRangeVals(self, _, xy):
        self.le_min.setText(str(xy[0]))
        self.le_max.setText(str(xy[1]))

        self.le_min.setCursorPosition(0)
        self.le_max.setCursorPosition(0)

    def __updatecb(self, vb):
        self.cb.setChecked(bool(self.vb.getState()['autoRange'][1]))

    def __cb_toggle(self, ev):
        self.vb.enableAutoRange(axis='y', enable=ev)


class SliderText(QWidget):
    sigValueChanged = QtCore.pyqtSignal(float)

    def __init__(self, label=None, vmin=None, vmax=None, step=None):
        super().__init__()

        nsteps = int(np.float(vmax - vmin) / step) + 1

        self.__values = np.linspace(vmin, vmax, nsteps)
        mainbox = QHBoxLayout()
        mainbox.setSpacing(2)
        mainbox.setContentsMargins(0, 0, 0, 0)

        if label != None:
            mainbox.addWidget(QLabel(label))

        self.le = FloatLineEdit(self)
        self.le.textChanged.connect(self.check_state)

        self.slider = QSlider(QtCore.Qt.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(nsteps - 1)

        mainbox.addWidget(self.slider)
        mainbox.addWidget(self.le)
        self.setLayout(mainbox)

        self.setValue(0)
        self.le.setText(str(0))
        self.slider.valueChanged.connect(self.sliderChanged)
        self.le.returnPressed.connect(self.textChanged)

    def check_state(self, *args, **kwargs):
        sender = self.sender()
        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]
        if state == QtGui.QValidator.Acceptable:
            color = '#c4df9b'  # green
        elif state == QtGui.QValidator.Intermediate:
            color = '#fff79a'  # yellow
            sender.setStyleSheet('QLineEdit { background-color: %s }' % color)
        else:
            color = '#f6989d'  # red
            sender.setStyleSheet('QLineEdit { background-color: %s }' % color)

    def textChanged(self):
        v = float(self.le.text())
        self.setValue(v)

    def setValue(self, v):
        idx = np.argmin(np.abs(v - self.__values))

        self.slider.setValue(idx)

    def sliderChanged(self, i):
        v = self.__values[i]
        self.le.setText(str(v))
        self.sigValueChanged.emit(v)
