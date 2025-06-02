from PyQt5.QtGui import QFont, QPainter
from PyQt5.QtWidgets import QApplication, QFileDialog, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QStackedLayout, QStyleFactory, QTableWidget, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
import PyQt5.QtChart as qtchart



class MainWindow(QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)
        self.setStyle(QStyleFactory.create('Fusion'))
#        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(500,300,1000,600)
        self.setWindowTitle("PyCryptoPortfolio")
#        self.resize(1000,600)
        self.layoutUI()

    def layoutUI(self):
#        self.setStyleSheet("background-color: white;")
#        self.setStyleSheet(" * {background-color: #ffffff} QFrame { border: 0px; background-color: #ffffff }")
        self.setStyleSheet(" * {{background-color: {0}}} QFrame {{ border: 0px; background-color: {0} }}".format("#ff00ff") )

#        self.setObjectName("mainWindow")
#        self.setStyleSheet("#mainWindow { background-color: white; border: 0px white}")

        self.mainLayout = QHBoxLayout(self)
        self.setContentsMargins(0,0,0,0)
 
        
        self.sidebarFrame = QFrame(self)
        self.sidebarFrame.setStyleSheet("background-color: red;")  
#        self.sidebarFrame.setObjectName("sidebarFrame")
#        self.sidebarFrame.setStyleSheet("#sidebarFrame { background-color: white; border: 0px white}")                        
        self.sidebarFrame.setFrameShape(QFrame.StyledPanel)
        self.sidebarFrame.setFrameShadow(QFrame.Raised)
        self.sidebarFrame.setFixedWidth(120)
        
        self.contentFrame = QFrame(self)
#        self.contentFrame.setStyleSheet("background-color: yellow;")
#        self.contentFrame.setObjectName("contentFrame")
#        self.contentFrame.setStyleSheet("#contentFrame { background-color: white; border: 0px white}")
        self.contentFrame.setFrameShape(QFrame.StyledPanel)
        self.contentFrame.setFrameShadow(QFrame.Raised)
        
        self.contentFrame2 = QFrame(self)
#        self.contentFrame.setStyleSheet("background-color: yellow;")
#        self.contentFrame.setObjectName("contentFrame")
#        self.contentFrame.setStyleSheet("#contentFrame { background-color: white; border: 0px white}")
        self.contentFrame2.setFrameShape(QFrame.StyledPanel)
        self.contentFrame2.setFrameShadow(QFrame.Raised)
        
        
        # stacked content layout
        self.stackedLayout = QStackedLayout()
        self.stackedLayout.addWidget(self.contentFrame)
        self.stackedLayout.addWidget(self.contentFrame2)
        
        
        self.statusbarFrame = QFrame(self)
        self.statusbarFrame.setStyleSheet("background-color: blue;")
#        self.statusbarFrame.setObjectName("statusbarFrame")
#        self.statusbarFrame.setStyleSheet("#statusbarFrame { background-color: white; border: 0px white}")
        self.statusbarFrame.setFrameShape(QFrame.StyledPanel)
        self.statusbarFrame.setFrameShadow(QFrame.Raised)
        self.statusbarFrame.setFixedHeight(30)
        
        # buttons sidebar
        self.button1 = QPushButton("b1", self.sidebarFrame)
        self.button2 = QPushButton("b2", self.sidebarFrame)
        self.button3 = QPushButton("b3", self.sidebarFrame)
        self.button4 = QPushButton("b4", self.sidebarFrame)
        buttonHeight = 80
        self.button1.setFixedHeight(buttonHeight)
        self.button2.setFixedHeight(buttonHeight)
        self.button3.setFixedHeight(buttonHeight)
        self.button4.setFixedHeight(buttonHeight)
        self.button1.clicked.connect(lambda: self.stackedLayout.setCurrentIndex(0))
        self.button2.clicked.connect(lambda: self.stackedLayout.setCurrentIndex(1))
#        self.lowerBtn.setFixedSize(50,10)
        # layout in lower frame
        self.sidebarVerticalLayout = QVBoxLayout(self.sidebarFrame)
        self.sidebarVerticalLayout.addWidget(self.button1)
        self.sidebarVerticalLayout.addWidget(self.button2)
        self.sidebarVerticalLayout.addWidget(self.button3)
        self.sidebarVerticalLayout.addWidget(self.button4)
        self.sidebarVerticalLayout.addStretch()
        
        # content contentFrame
        # content items
        self.contentbutton = QPushButton("some button", self.contentFrame)
        self.contentlabel = QLabel("some text", self.contentFrame)
        mySeries = qtchart.QPieSeries()
        mySeries.append('BTC', 20000)
        mySeries.append('ETH', 60000)
        mySeries.append('LTC', 2000)
#        mySlice = mySeries.slices().at(1)
#        mySlice.setExploded()
        self.myChart = qtchart.QChart()
        self.myChart.addSeries(mySeries)
#        self.myChart.setTitle("chart example")
        self.myChart.legend().hide()
        self.myChartView = qtchart.QChartView(self.myChart)
        self.myChartView.setRenderHint(QPainter.Antialiasing)
#        self.contentFrame.addWidget(self.myChartView)
        self.myTable = QTableWidget(50,8,self.contentFrame)
        self.myTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # layout content
        self.contentLayout = QVBoxLayout(self.contentFrame)
        self.horzLayout1 = QHBoxLayout()
        self.vertLayout1 = QVBoxLayout()
        
        self.contentLayout.addLayout(self.horzLayout1)
        self.contentLayout.addWidget(self.myTable)
        self.horzLayout1.addLayout(self.vertLayout1)
        self.horzLayout1.addStretch()
        self.horzLayout1.addWidget(self.myChartView)
        self.vertLayout1.addWidget(self.contentbutton)
        self.vertLayout1.addWidget(self.contentlabel)
        self.vertLayout1.addStretch()
        
        
        # content contentFrame2
        # content items
        
        self.pathlabel = QLabel("Path:", self.contentFrame2)
        self.fileDialog = QFileDialog(self.contentFrame2)
#        self.fileDialog.setFileMode(QFileDialog.DirectoryOnly)
        self.pathEntry = QLineEdit(self.contentFrame2)
        self.pathEntry.setPlaceholderText("enter Path/ drop file or folder")
        self.selectPathButton = QPushButton("Select", self.contentFrame2)
        self.selectPathButton.clicked.connect(lambda: self.selectPath())
       

        # layout content
        self.contentLayout2 = QVBoxLayout(self.contentFrame2)
        self.horzLayout21 = QHBoxLayout()
        
        self.contentLayout2.addLayout(self.horzLayout21)
        self.horzLayout21.addWidget(self.pathlabel)
        self.horzLayout21.addWidget(self.pathEntry)
        self.horzLayout21.addWidget(self.selectPathButton)

        
        # labels statusbar
        self.label1 = QLabel("little bit status", self.statusbarFrame)
        font = QFont("Arial", 10)
        self.label1.setFont(font)
        self.label2 = QLabel("some more status", self.statusbarFrame)
        self.label2.setFont(font)
#        self.lowerBtn.setFixedSize(50,10)
        # layout in lower frame
        self.statusbarHorizontalLayout = QHBoxLayout(self.statusbarFrame)
        self.statusbarHorizontalLayout.addWidget(self.label1)
        self.statusbarHorizontalLayout.addWidget(self.label2)
        self.statusbarHorizontalLayout.addStretch()
        
        
        
        # put frames in horizontal layout
        self.horizontalFrameLayout = QHBoxLayout()
        self.horizontalFrameLayout.addWidget(self.sidebarFrame)
        self.horizontalFrameLayout.addLayout(self.stackedLayout)

        
        # put frames in vertical layout
        self.verticalFrameLayout = QVBoxLayout()
        self.verticalFrameLayout.setSpacing(0)
        self.verticalFrameLayout.addLayout(self.horizontalFrameLayout)
        self.verticalFrameLayout.addWidget(self.statusbarFrame)
        
        
        # put subLayouts in main layout
        self.mainLayout.addLayout(self.verticalFrameLayout)
        
 
        self.show()
        
    def selectPath(self):
#        self.pathReturn = self.fileDialog.getOpenFileName()
        self.pathReturn = self.fileDialog.getExistingDirectory()
        print(self.pathReturn[0])
    
        
        
        

if __name__ == '__main__':
    app = QApplication([])
#    app.setStyle(QStyleFactory.create('Fusion'))
    window = MainWindow()
    app.exec_()
