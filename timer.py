import ctypes
import sys

from PyQt5.QtCore import QTime, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QPushButton,
    QButtonGroup,
    QLCDNumber,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QGroupBox
)
from PyQt5.QtWinExtras import QWinTaskbarButton

APPID = 'local.timer'

class Window(QMainWindow):
    INTERVALS = (
        (0, 'None', ''),
        (5, '5 secs.', '5s'),
        (15 * 60, '15 mins.', '15m'),
        (30 * 60, '30 mins.', '30m'),
        (60 * 60, '60 mins.', '60m')
    )

    CONTEXTS = (None, 'work', 'play')

    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('clock.ico'))
        self.resize(250, 300)
        self.interval = None
        self.context = None

        self.timer = Timer()
        self.timer.textChanged.connect(self.updateTitle)
        self.timer.started.connect(self.updateTitle)
        self.timer.stopped.connect(self.updateTitle)
        self.timer.reset_.connect(self.updateTitle)

        self.progressButton = QWinTaskbarButton()
        self.progress = self.progressButton.progress()

        self.updateTitle()
        self.setupWidgets()

    def showEvent(self, event):
        super().showEvent(event)
        self.progressButton.setWindow(self.windowHandle())

    def updateTitle(self, text=None):
        title = ''
        if self.context:
            title += self.context.title()
            if self.interval:
                title += ' ({})'.format(self.INTERVALS[self.interval][2])
        elif self.interval:
            title = '{}'.format(self.INTERVALS[self.interval][2])
        if self.context or self.interval:
            title += ' | '
        title += text or self.timer.text()
        if self.interval:
            secs = self.INTERVALS[self.interval][0]
            title += ' ({}%)'.format(int(100 * self.timer.seconds() / secs))
        self.setWindowTitle(title)

        if self.interval:
            seconds = self.timer.seconds()
            if seconds <= self.progress.maximum():
                self.progress.setValue(seconds)
            elif not self.progress.isStopped():
                self.progress.stop()

    def setupWidgets(self):
        central = QWidget()
        layout = QVBoxLayout()
        central.setLayout(layout)
        layout.addWidget(self.controlButtons())
        layout.addWidget(self.timer, 1)
        layout.addWidget(self.intervalButtons())
        layout.addWidget(self.contextButtons())
        self.setCentralWidget(central)

    def controlButtons(self):
        widget = QWidget()
        group = QButtonGroup(widget)
        layout = QHBoxLayout()
        widget.setLayout(layout)

        startButton = QPushButton('Start')
        startButton.setCheckable(True)

        def onStart():
            self.timer.start()
            if self.progress.isPaused():
                self.progress.resume()

        startButton.clicked.connect(lambda: self.timer.start())
        group.addButton(startButton)
        layout.addWidget(startButton)

        stopButton = QPushButton('Stop')
        stopButton.setCheckable(True)

        def onStop():
            self.timer.stop()
            self.progress.setPaused(True)

        stopButton.clicked.connect(onStop)
        group.addButton(stopButton)
        layout.addWidget(stopButton)

        resetButton = QPushButton('Reset')

        def onReset():
            self.timer.reset()
            self.progress.resume()

        resetButton.clicked.connect(onReset)
        layout.addWidget(resetButton)

        return widget

    def intervalButtons(self):
        widget = QGroupBox('Interval')
        group = QButtonGroup(widget)
        layout = QHBoxLayout()
        widget.setLayout(layout)

        def setInterval():
            self.interval = group.checkedId()
            interval = self.INTERVALS[self.interval][0]
            self.updateTitle()
            if interval:
                self.progress.show()
                self.progress.setMaximum(interval)
                value = self.timer.seconds()
                if value < interval:
                    self.progress.resume()
                else:
                    self.progress.stop()
                self.progress.setValue(min(interval, value))
            else:
                self.progress.hide()

        for i, interval in enumerate(self.INTERVALS):
            button = QPushButton(interval[1])
            button.setCheckable(True)
            button.clicked.connect(setInterval)
            group.addButton(button, i)
            layout.addWidget(button, 1 if i > 0 else 0)

        return widget

    def contextButtons(self):
        widget = QGroupBox('Context')
        group = QButtonGroup(widget)
        layout = QHBoxLayout()
        widget.setLayout(layout)

        def setContext():
            self.context = self.CONTEXTS[group.checkedId()]
            self.updateTitle()

        for i, context in enumerate(self.CONTEXTS):
            button = QPushButton(context.title() if context else 'None')
            button.setCheckable(True)
            button.clicked.connect(setContext)
            group.addButton(button, i)
            layout.addWidget(button, 1 if i > 0 else 0)

        return widget

class Timer(QLCDNumber):
    textChanged = pyqtSignal(str)
    started = pyqtSignal()
    stopped = pyqtSignal()
    reset_ = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.reset()

    def start(self):
        self.timer.start(1000)
        self.started.emit()

    def stop(self):
        self.timer.stop()
        self.stopped.emit()

    def reset(self):
        self.time = QTime(0, 0)
        self.display(self.time.toString())
        self.reset_.emit()

    def isRunning(self):
        return self.timer.isActive()

    def text(self):
        if self.time.hour() == 0:
            return self.time.toString('mm:ss')
        else:
            return self.time.toString('h:mm:ss')

    def seconds(self):
        return self.time.hour() * 3600 + self.time.minute() * 60 + self.time.second()

    def tick(self):
        self.time = self.time.addSecs(1)
        text = self.text()
        if len(text) != self.digitCount():
            self.setDigitCount(len(text))
        self.display(text)
        self.textChanged.emit(text)

if __name__ == '__main__':
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APPID)

    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())
