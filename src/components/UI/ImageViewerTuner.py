
from PyQt5 import QtWidgets, QtCore

from components.UI.ImageViewer import ImViewSecurityWidget

class imViewTuner(QtWidgets.QWidget):

    def __init__(self, imViewsContainer : ImViewSecurityWidget, imViewID : int,  *args, **kwargs):
        super(imViewTuner, self).__init__(*args, **kwargs)
        self.imViewsContainer = imViewsContainer
        self.imViewID = imViewID
        self.imView = self.imViewsContainer[self.imViewID]
        self.imViewStateChanger = self.imViewsContainer.switchImView
        self.setupUi()
    
    @QtCore.pyqtSlot()
    def imViewCheckBoxChanged(self):
        self.imViewStateChanger(self.imViewID)

    def setupUi(self):
        self.mainLayout = QtWidgets.QVBoxLayout(self)

        self.imViewCheckBox = QtWidgets.QCheckBox()
        self.imViewCheckBox.setCheckState(self.imView.isWorking * 2) # magic to transfrom from True/False to 2/0
        self.imViewCheckBox.setText(f"Monitor {self.imViewID}")
        self.imViewCheckBox.stateChanged.connect(self.imViewCheckBoxChanged)

        self.mainLayout.addWidget(self.imViewCheckBox)