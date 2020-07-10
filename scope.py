####################################################################################
# Title: 
#   Real time plotter in PyQt
#
# Author:
#   Pedro Iniguez Huerta
#
# Description:
#   The purpose of this software is to build a cheap scope than can run in a Raspberry Pi
#   
# Notes:
#   - The base code was downloaded from K.Mulier's respond to following stackoverflow question:
#   https://stackoverflow.com/questions/38469630/realtime-plotting-with-pyqt-plotwidget-error-message-plotwidget-object-is-not
#   - At this point this code looks very different because it was changed to contain additional functionalities. 
#   - This is just the Software part however working on developing the Hardware part too.


import sys
import os
from PyQt5 import QtCore, QtGui, QtWidgets
import functools
import numpy as np
import random as rd
import matplotlib
matplotlib.use("Qt4Agg")
from matplotlib.figure import Figure
from matplotlib.animation import TimedAnimation
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import time
import threading



quit = False
logMode = 1
onPlay = True
playNSteps = 0
REFRESH_TIME = 10
REFRESH_SLEEP = 0.01
XOFFSET = 0
YOFFSET = 0
SAMPLES = 100
YLIMIT  = 100
XLIMIT  = SAMPLES
XVIEW   = SAMPLES / 2
XSCALE  = 1
YSCALE   = YLIMIT/10
GRID_SIZE = XLIMIT + 1
GRID_DIVISIONS_MAYOR = 10
GRID_DIVISIONS_MINOR = 5
GRID_MAYOR = GRID_SIZE / GRID_DIVISIONS_MAYOR
GRID_MINOR = GRID_MAYOR / GRID_DIVISIONS_MINOR
ALPHA_MINOR = 0.2
ALPHA_MAYOR = 0.5
LOW_Y = -(XLIMIT / 2)
HIGH_Y = XLIMIT / 2
LOW_X =  0
HIGH_X = XLIMIT

BACKGROUND_COLOR = "black"
GRID_COLOR  = "while"
PEN1_COLOR = "yellow"
PEN2_COLOR = "green"
PEN3_COLOR = "blue"
PEN4_COLOR = "red"
PAINT_COLOR = "white"


def log(text):
    if logMode > 0:
        print(text)

def setCustomSize(x, width, height):
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(x.sizePolicy().hasHeightForWidth())
    x.setSizePolicy(sizePolicy)
    x.setMinimumSize(QtCore.QSize(width, height))
    x.setMaximumSize(QtCore.QSize(width, height))


class CustomMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(CustomMainWindow, self).__init__()

        self.jumpSize = 5

        # Define the geometry of the main window
        self.setGeometry(50, 50, 1050, 650)
        self.setWindowTitle("Real time plotter")

        # Create FRAME_A
        self.FRAME_A = QtWidgets.QFrame(self)
        self.FRAME_A.setStyleSheet("QWidget { background-color: %s }" % QtGui.QColor(210,210,235,255).name())
        self.LAYOUT_A = QtWidgets.QGridLayout()
        self.FRAME_A.setLayout(self.LAYOUT_A)
        self.setCentralWidget(self.FRAME_A)

        self.buttons = 0

        # Place the Y zoom in button
        self.zoomYInBtn = QtWidgets.QPushButton(text = 'Y+')
        setCustomSize(self.zoomYInBtn, 100, 50)
        self.zoomYInBtn.clicked.connect(self.zoomYInBtnAction)
        self.LAYOUT_A.addWidget(self.zoomYInBtn, *(1,self.buttons))
        self.buttons += 1

        # Place the Y zoom out button
        self.zoomYOutBtn = QtWidgets.QPushButton(text = 'Y-')
        setCustomSize(self.zoomYOutBtn, 100, 50)
        self.zoomYOutBtn.clicked.connect(self.zoomYOutBtnAction)
        self.LAYOUT_A.addWidget(self.zoomYOutBtn, *(1,self.buttons))
        self.buttons += 1

        # Place the X zoom In button
        self.zoomXInBtn = QtWidgets.QPushButton(text = 'X+')
        setCustomSize(self.zoomXInBtn, 100, 50)
        self.zoomXInBtn.clicked.connect(self.zoomXInBtnAction)
        self.LAYOUT_A.addWidget(self.zoomXInBtn, *(1,self.buttons))
        self.buttons += 1

        # Place the X zoom out button
        self.zoomXOutBtn = QtWidgets.QPushButton(text = 'X-')
        setCustomSize(self.zoomXOutBtn, 100, 50)
        self.zoomXOutBtn.clicked.connect(self.zoomXOutBtnAction)
        self.LAYOUT_A.addWidget(self.zoomXOutBtn, *(1,self.buttons))
        self.buttons += 1
   
        # Place the up button
        self.upBtn = QtWidgets.QPushButton(text = 'up')
        setCustomSize(self.upBtn, 100, 50)
        self.upBtn.clicked.connect(self.upBtnAction)
        self.LAYOUT_A.addWidget(self.upBtn, *(1,self.buttons))
        self.buttons += 1

        # Place the down button
        self.downBtn = QtWidgets.QPushButton(text = 'down')
        setCustomSize(self.downBtn, 100, 50)
        self.downBtn.clicked.connect(self.downBtnAction)
        self.LAYOUT_A.addWidget(self.downBtn, *(1,self.buttons))
        self.buttons += 1

        # Place the left button
        self.leftBtn = QtWidgets.QPushButton(text = 'left')
        setCustomSize(self.leftBtn, 100, 50)
        self.leftBtn.clicked.connect(self.leftBtnAction)
        self.LAYOUT_A.addWidget(self.leftBtn, *(1,self.buttons))
        self.buttons += 1

        # Place the right button
        self.rightBtn = QtWidgets.QPushButton(text = 'right')
        setCustomSize(self.rightBtn, 100, 50)
        self.rightBtn.clicked.connect(self.rightBtnAction)
        self.LAYOUT_A.addWidget(self.rightBtn, *(1,self.buttons))
        self.buttons += 1

        # Place the resetXY button
        self.resetXYBtn = QtWidgets.QPushButton(text = 'XY')
        setCustomSize(self.resetXYBtn, 100, 50)
        self.resetXYBtn.clicked.connect(self.resetXYBtnAction)
        self.LAYOUT_A.addWidget(self.resetXYBtn, *(1,self.buttons))
        self.buttons += 1

        # Place the pause button
        self.pauseBtn = QtWidgets.QPushButton(text = 'pause')
        setCustomSize(self.pauseBtn, 100, 50)
        self.pauseBtn.clicked.connect(self.pauseBtnAction)
        self.LAYOUT_A.addWidget(self.pauseBtn, *(1,self.buttons))
        self.buttons += 1

        # Place the close button
        self.closeBtn = QtWidgets.QPushButton(text = 'close')
        setCustomSize(self.closeBtn, 100, 50)
        self.closeBtn.clicked.connect(self.closeBtnAction)
        self.LAYOUT_A.addWidget(self.closeBtn, *(1,self.buttons))
        self.buttons += 1

        # Place the matplotlib figure
        self.myFig = CustomFigCanvas()
        self.LAYOUT_A.addWidget(self.myFig, *(0,0,1,self.buttons))

        # Add the callbackfunc to ..
        myDataLoop = threading.Thread(name = 'myDataLoop', target = dataSendLoop,  args = (self.addData_callbackFunc,))
        myDataLoop.start()

        self.show()

    def upBtnAction(self):
        log("up")
        self.myFig.up(self.jumpSize)

    def downBtnAction(self):
        log("down")
        self.myFig.down(self.jumpSize)

    def leftBtnAction(self):
        log("left")
        self.myFig.left(self.jumpSize)

    def rightBtnAction(self):
        log("right")
        self.myFig.right(self.jumpSize)

    def zoomYInBtnAction(self):
        log("zoom Y in")
        self.myFig.zoomY(self.jumpSize)

    def zoomYOutBtnAction(self):
        log("zoom Y out")
        self.myFig.zoomY(-self.jumpSize)

    def zoomXInBtnAction(self):
        log("zoom X in")
        self.myFig.zoomX(self.jumpSize)

    def zoomXOutBtnAction(self):
        log("zoom X out")
        self.myFig.zoomX(-self.jumpSize)

    def pauseBtnAction(self):
        text = self.myFig.pausePlay()
        self.pauseBtn.setText(text)

    def resetXYBtnAction(self):
        log("reset X,Y")
        text = self.myFig.resetXY(True)

    def closeBtnAction(self):
        global quit
        log("closing")
        quit = True
        self.close()
        sys.exit(0)

    def addData_callbackFunc(self, value):
        # log("Add data: " + str(value))
        self.myFig.addData(value)


class CustomFigCanvas(FigureCanvas, TimedAnimation):
    def __init__(self):
        self.addedData = []
        log("" + matplotlib.__version__)

        # The data
        self.xlim = XLIMIT
        self.ylim = YLIMIT
        self.n = np.linspace(0, self.xlim - 1, self.xlim)
        self.ny = np.linspace(0, self.ylim - 1, self.ylim)
        self.y = (self.ny * 0.0) + YOFFSET

        # The window
        self.fig = Figure(figsize=(5,5), dpi=100)
        self.ax1 = self.fig.add_subplot(111)

        # configure grid layout
        major_ticks = np.arange(0, GRID_SIZE, GRID_MAYOR)
        minor_ticks = np.arange(0, GRID_SIZE, GRID_MINOR)

        self.ax1.set_xticks(major_ticks)
        self.ax1.set_xticks(minor_ticks, minor=True)
        self.ax1.set_yticks(major_ticks)
        self.ax1.set_yticks(minor_ticks, minor=True)

        # {'-', '--', '-.', ':', '', (offset, on-off-seq), ...}
        self.ax1.grid(color=GRID_COLOR[0], linestyle="-.",linewidth=1, which="both")
        self.ax1.set_facecolor(BACKGROUND_COLOR) 

        # Different settings for the grids:
        self.ax1.grid(which='minor', alpha=ALPHA_MINOR)
        self.ax1.grid(which='major', alpha=ALPHA_MAYOR)

        # self.ax1 settings
        self.ax1.set_xlabel('time')
        self.ax1.set_ylabel('raw data')
        self.ax1.set_yscale("linear")
        self.line1 = Line2D([], [], color=PEN1_COLOR)
        self.line1_tail = Line2D([], [], color=PAINT_COLOR, linewidth=2)
        self.line1_head = Line2D([], [], color=PAINT_COLOR, marker='o', markeredgecolor=PAINT_COLOR[0])
        self.ax1.add_line(self.line1)
        self.ax1.add_line(self.line1_tail)
        self.ax1.add_line(self.line1_head)

        self.resetXY(False)


        FigureCanvas.__init__(self, self.fig)
        TimedAnimation.__init__(self, self.fig, interval = REFRESH_TIME, blit = True)

    def new_frame_seq(self):
        return iter(range(self.n.size))

    def _init_draw(self):
        lines = [self.line1, self.line1_tail, self.line1_head]
        for l in lines:
            l.set_data([], [])

    def addData(self, value):
        self.addedData.append(value)

    def up(self, value):
        bottom = self.ax1.get_ylim()[0]
        top = self.ax1.get_ylim()[1]
        bottom += value
        top += value
        self.ax1.set_ylim(bottom,top)
        self.draw()

    def down(self, value):
        bottom = self.ax1.get_ylim()[0]
        top = self.ax1.get_ylim()[1]
        bottom -= value
        top -= value
        self.ax1.set_ylim(bottom,top)

    def left(self, value):
        left = self.ax1.get_xlim()[0]
        right = self.ax1.get_xlim()[1]
        left -= value
        right -= value
        self.ax1.set_xlim(left,right)
        self.draw()

    def right(self, value):
        left = self.ax1.get_xlim()[0]
        right = self.ax1.get_xlim()[1]
        left += value
        right += value
        self.ax1.set_xlim(left,right)
        self.draw()

    def zoomY(self, value):
        bottom = self.ax1.get_ylim()[0]
        top = self.ax1.get_ylim()[1]
        bottom += value
        top -= value
        self.ax1.set_ylim(bottom,top)
        self.draw()

    def zoomX(self, value):
        left = self.ax1.get_xlim()[0]
        right = self.ax1.get_xlim()[1]
        left += value
        right -= value
        self.ax1.set_xlim(left,right)
        self.draw()

    def resetXY(self, draw):
        self.ax1.set_xlim(LOW_X/XSCALE, HIGH_X/XSCALE)
        self.ax1.set_ylim(LOW_Y/YSCALE, HIGH_Y/YSCALE)
        if draw:
            self.draw()

    def pausePlay(self):
        global onPlay
        if onPlay == True:
            log("On Pause")
            onPlay = False
            return "Play"
        else:
            log("On Play")
            onPlay = True
            return "Pause"

    def _step(self, *args):
        # Extends the _step() method for the TimedAnimation class.
        try:
            TimedAnimation._step(self, *args)
        except Exception as e:
            self.abc += 1
            log(str(self.abc))
            TimedAnimation._stop(self)

    def _draw_frame(self, framedata):
        global YOFFSET, YSCALE
        margin = 2
        while(len(self.addedData) > 0):
            self.y = np.roll(self.y, -1)
            self.y[-1] = (self.addedData[0])/YSCALE + YOFFSET
            del(self.addedData[0])

        # draw the blue line
        self.line1.set_data(self.n[ 0 : self.n.size - margin ], self.y[ 0 : self.n.size - margin ])

        # Draw last 50 pixels in red
#        self.line1_tail.set_data(np.append(self.n[-10:-1 - margin], self.n[-1 - margin]), np.append(self.y[-10:-1 - margin], self.y[-1 - margin]))

        # Draw a dot for drawing pixel
#        self.line1_head.set_data(self.n[-1 - margin], self.y[-1 - margin])

        # Don't know what this do yet
#        self._drawn_artists = [self.line1, self.line1_tail, self.line1_head]

class Communicate(QtCore.QObject):
    data_signal = QtCore.pyqtSignal(float)

def dataSendLoop(addData_callbackFunc):
    global quit, onPlay, playNSteps, SAMPLES

    # Setup the signal-slot mechanism.
    mySrc = Communicate()
    mySrc.data_signal.connect(addData_callbackFunc)

    # Simulate some data
    n = np.linspace(0, SAMPLES-1, SAMPLES)
    y = (25*(np.sin(n / 8.3)) + 10*(np.sin(n / 7.5)) - 5*(np.sin(n / 1.5)))
#    y = np.sin(n / 7.5) * 200
    i = 0

    while quit == False:
        if i >= SAMPLES:
            i = 0
        time.sleep(REFRESH_SLEEP)

        if onPlay or playNSteps:
            mySrc.data_signal.emit(y[i]) # <- Here you emit a signal!
            i += 1
            if playNSteps > 0:
                playNSteps -= 1

if __name__== '__main__':
    app = app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create('Plastique'))
    myGUI = CustomMainWindow()
    sys.exit(app.exec_())

