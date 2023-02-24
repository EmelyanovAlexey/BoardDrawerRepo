
from threading import Thread
from queue import Queue

import cv2
import numpy as np
import time

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QTimer, QThread
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QPushButton

from components.DrawerModule import Filters

class FPSMeter(QLabel):
    def __init__(self,  *args, **kwargs):
        super(FPSMeter, self).__init__( *args, **kwargs)
        self.paddingLeft = 5
        self.paddingTop = 5

        self.timer = QTimer()
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.FPSDisplay)

        self._fpsTimerPrev = time.time()
        self.framesProcessed = 0
        self.setText("")

        self.timer.start()
    
    def frameProcessed(self):
        self.framesProcessed += 1
    
    def FPSDisplay(self):
        sfromPrevUpdate = time.time() - self._fpsTimerPrev
        self._fpsTimerPrev = time.time()
        self.setText(f"FPS: {round(float(1/sfromPrevUpdate*self.framesProcessed),2)}")
        self.framesProcessed = 0

    def updatePosition(self):
        if hasattr(self.parent(), 'viewport'):
            parentRect = self.parent().viewport().rect()
        else:
            parentRect = self.parent().rect()
        if not parentRect: return
        x = parentRect.width() - self.width() - self.paddingLeft
        y = self.paddingTop
        self.setGeometry(x, y, self.width(), self.height())
    
    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        super().resizeEvent(a0)
        self.updatePosition()

class ImView(QWidget):

    def __init__(self, fps : int = 30, name : str = "", metadata : str = None,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fps = fps
        self.mainLayout = QVBoxLayout(self)
        self.imageLabel = QLabel()
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.imageLabel.setMinimumSize(360, 360)
        self.imageLabel.setSizePolicy(sizePolicy)
        self.imageLabel.setScaledContents(False)

        self.mainLayout.addWidget(self.imageLabel)

        self.FPSMeter = FPSMeter(parent=self)

        self.updateTimer = QTimer()
        self.updateTimer.setInterval(1000//self.fps)
        self.updateTimer.timeout.connect(self.updateImageFromQueue)
        self.imageQueue = Queue()
        self.imageLoaded = True

        self.defaultImage = None
        self.getDefaultImage()

        self.metadata = metadata
        self.isWorking = True
        self.filters = []

        self.updateTimer.start()

    def updateImageFromQueue(self):
        if not self.isWorking: return
        if self.imageQueue.empty():
            if self.imageLoaded:
                self.setPixmap(self.getDefaultImage())
                self.imageLoaded = False
        else:
            self.setPixmap(self.toPixmap(self.imageQueue.get()))
        if self.imageQueue.qsize() >= self.fps:
            self.imageQueue = Queue()

    def addImageToQueue(self, image):
        if image is None: return
        self.imageLoaded = True
        self.imageQueue.put_nowait(image)

    def getDefaultImage(self):
        if self.defaultImage is None:
            try:
                self.defaultImage = QtGui.QPixmap("assets/defaultImage.jpg")
            except:
                self.defaultImage = QtGui.QImage(np.zeros((360, 360, 3)).data, 360, 360, QtGui.QImage.Format.Format_RGB888).rgbSwapped()
        return self.defaultImage

    def toPixmap(self, image : cv2.Mat):
        image = QtGui.QImage(image.data, image.shape[1], image.shape[0], QtGui.QImage.Format.Format_RGB888).rgbSwapped()
        return QtGui.QPixmap.fromImage(image)

    def setPixmap(self, pixmap):
        self.imageLabel.setPixmap(pixmap.scaled(
            self.imageLabel.width(), self.imageLabel.height(),
            Qt.AspectRatioMode.KeepAspectRatio))
        self.FPSMeter.frameProcessed()
    
    def addFilter(self, filter : Filters):
        if filter not in self.filters:
            self.filters.append(filter)
    
    def removeFilter(self, filter : Filters):
        if filter in self.filters:
            self.filters.remove(filter)

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        super().resizeEvent(a0)
        self.FPSMeter.updatePosition()
    
    def setState(self, newState : bool):
        #Sets on/off if necessary returns new state
        if newState == self.isWorking:
            return self.isWorking
        return self.switchState()

    def switchState(self):
        #switch state to opposite returns new state
        self.isWorking = not self.isWorking
        if self.isWorking:
            self.show()
        else:
            self.hide()
        return self.isWorking

class ImViewWindow(QMainWindow):

    def __init__(self, fps : int = 30):
        super(ImViewWindow, self).__init__()
        self.fps = fps
        self.setupUi()
        self.isShow = False
        self.switchBtn = None
        quit = QAction("Quit", self)
        quit.triggered.connect(self.closeEvent)
    
    @QtCore.pyqtSlot()
    def switchBtnFunc(self):
        self.isShow = not self.isShow
        if self.isShow:
            self.switchBtn.setText("Hide window")
            self.imView.isWorking = True
            self.show()
        else:
            self.switchBtn.setText("Show window")
            self.imView.isWorking = False
            self.hide()

    def createSwitchBtn(self):
        if self.switchBtn:
            return self.switchBtn
        self.switchBtn = QPushButton()
        self.switchBtn.setText("Show window")
        self.switchBtn.clicked.connect(self.switchBtnFunc)

        return self.switchBtn

    def setupUi(self):
        self._imView = QWidget()
        imViewLayout = QHBoxLayout(self._imView)
        self.imView = ImView(fps=self.fps)
        self.imView.addFilter(Filters.drawCanvas)
        imViewLayout.addWidget(self.imView)
        self.setCentralWidget(self._imView)
    
    def closeEvent(self, event):
        self.switchBtnFunc()

class ImViewSecurityWidget(QWidget):

    def __init__(self, imViewFPS : int, imViewsContainer : list[ImView], parent = None, rows = 2, columns = 2):
        super(ImViewSecurityWidget, self).__init__(parent)
        self.imViewFPS = imViewFPS
        self.imViewContainer = imViewsContainer
        self.rows = rows
        self.columns = columns
        self.setupUi()

    def setupUi(self):
        self.mainLayout = QtWidgets.QGridLayout(self)

        for row in range(self.rows):
            for column in range(self.columns):
                imView = ImView(fps=self.imViewFPS, metadata=f"POS<{row}:{column}>")
                self.imViewContainer.append(imView)
                self.mainLayout.addWidget(imView, row, column)

    def __getitem__(self, ind) -> ImView:
        return self.imViewContainer[ind]

    def switchImView(self, ind, newState : bool = None):
        imView = self[ind]
        if newState == None:
            returnState = imView.switchState()
        else:
            returnState = imView.setState(newState)
        return returnState