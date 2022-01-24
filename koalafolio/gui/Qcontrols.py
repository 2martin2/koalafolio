# -*- coding: utf-8 -*-
"""
Created on Sun Sep 16 20:26:21 2018

@author: Martin
"""

import PyQt5.QtGui as qtgui
import PyQt5.QtWidgets as qtwidgets
import PyQt5.QtCore as qtcore
import re
from pathlib import Path
import koalafolio.gui.QLogger as logger
import koalafolio.gui.QLoggerWidget as loggerwidget
import os

localLogger = logger.globalLogger

qt = qtcore.Qt
# %% constants
PATHREGEX = r"^\w:((\\|/)\w+)*(|.\w+)$"
FLOATREGEX = "^([\+\-]|)(\d*)(.(\d*)|)((e[\+\-]\d*)|)$"

# %% variables
pathRegexCompiled = re.compile(PATHREGEX, re.IGNORECASE | re.MULTILINE)
floatRegexCompiled = re.compile(FLOATREGEX, re.MULTILINE)


# %% controls
class StyledFrame(qtwidgets.QFrame):
    def __init__(self, parent, *args, **kwargs):
        super(StyledFrame, self).__init__(parent=parent, *args, **kwargs)

        self.setFrameShape(qtwidgets.QFrame.StyledPanel)
        self.setFrameShadow(qtwidgets.QFrame.Raised)


# %% Headings
class Heading(qtwidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super(Heading, self).__init__(*args, **kwargs)

        self.setObjectName("QHeading")


# %% SubHeadings
class SubHeading(qtwidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super(SubHeading, self).__init__(*args, **kwargs)

        self.setObjectName("QSubHeading")


# status bar for printing logging entries
class StatusBar(StyledFrame):
    def __init__(self, parent, height=80, dataPath=None, *args, **kwargs):
        super(StatusBar, self).__init__(parent=parent, *args, **kwargs)

        self.logfile = os.path.join(dataPath, 'logfile.txt')

        self.setObjectName('statusbar')
        self.setFrameShadow(qtwidgets.QFrame.Sunken)
        self.setFixedHeight(height)

        self.statusView = loggerwidget.QLogView(parent=self, logfile=self.logfile)
        self.statusView.setFrameStyle(qtwidgets.QFrame.StyledPanel)

        self.statusLayout = qtwidgets.QVBoxLayout(self)
        self.statusLayout.addWidget(self.statusView)

    def printStatus(self, status):
        self.statusLabel.setText(status)

    def setModel(self, model):
        self.statusView.setModel(model)


# lineEdit where files can be dropped
class LineEditDropable(qtwidgets.QLineEdit):
    def __init__(self, parent, *args, **kwargs):
        super(LineEditDropable, self).__init__(parent=parent, *args, **kwargs)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        data = event.mimeData()
        if data.hasUrls():
            for url in data.urls():
                if url.isLocalFile():
                    self.clear()
                    self.insert(url.toLocalFile())
                    break
        event.acceptProposedAction()


# path input with line edit and qfiledialo
class PathInput(qtwidgets.QWidget):
    textChanged = qtcore.pyqtSignal()

    def __init__(self, parent, *args, **kwargs):
        super(PathInput, self).__init__(parent=parent, *args, **kwargs)

        # add Label
        self.pathLabel = qtwidgets.QLabel("Path:", self)
        # add FileDialog for path
        self.fileDialog = qtwidgets.QFileDialog(self)
        self.fileDialog.setFileMode(qtwidgets.QFileDialog.AnyFile)
        self.lineEdit = LineEditDropable(self)
        self.lineEdit.setPlaceholderText("enter path/ drop file or folder")
        self.lineEdit.textChanged.connect(lambda: self.textChanged.emit())

        # add path select button
        self.filePathButton = qtwidgets.QPushButton("File", self)
        self.filePathButton.clicked.connect(lambda: self.selectFilePath())
        self.folderPathButton = qtwidgets.QPushButton("Folder", self)
        self.folderPathButton.clicked.connect(lambda: self.selectFolderPath())

        # layout content
        self.horizontalLayout = qtwidgets.QHBoxLayout(self)
        self.horizontalLayout.addWidget(self.pathLabel)
        self.horizontalLayout.addWidget(self.lineEdit)
        self.horizontalLayout.addWidget(self.filePathButton)
        self.horizontalLayout.addWidget(self.folderPathButton)
        self.horizontalLayout.addWidget(self.fileDialog)

    def getPath(self):
        # return only valid path, otherwise return None
        try:
            path = Path(self.lineEdit.text())
            if ((path.is_file() | path.is_dir())):
                return path
            else:
                return None
        except Exception as ex:
            localLogger.warning("converting path -" + self.lineEdit.text() + "- failed: " + str(ex))
            return None

    def setPath(self, path):
        self.lineEdit.setText(path)

    def getText(self):
        return self.lineEdit.text()

    def selectFilePath(self):
        pathReturn = self.fileDialog.getOpenFileName()
        if pathReturn[0]:
            self.lineEdit.clear()
            self.lineEdit.insert(pathReturn[0])

    def selectFolderPath(self):
        pathReturn = self.fileDialog.getExistingDirectory()
        if pathReturn:
            self.lineEdit.clear()
            self.lineEdit.insert(pathReturn)

    def pathIsValid(self):
        # check return value of getPath
        if self.getPath():
            return True
        return False


# styled label for showing single values in gui
class StyledLabelCont(qtwidgets.QFrame):
    def __init__(self, parent, header='', text='', *args, **kwargs):
        super(StyledLabelCont, self).__init__(parent=parent, *args, **kwargs)

        self.setObjectName('StyledLabelCont')
        self.title = qtwidgets.QPushButton(header, self)
        self.title.setCheckable(True)
        self.title.setObjectName('StyledLabelTitle')
        self.title.setMinimumHeight(25)
        # self.title.setAlignment(qt.AlignCenterS)
        titleFont = qtgui.QFont("Arial", 11)
        self.title.setFont(titleFont)

        self.body = qtwidgets.QWidget()
        # self.body.setAlignment(qt.AlignCenter)
        self.body.setObjectName('StyledLabelBody')
        self.body.sizePolicy().setRetainSizeWhenHidden(False)

        self.bodyLayout = qtwidgets.QGridLayout(self.body)
        self.bodyLayout.setContentsMargins(6, 4, 6, 4)
        self.bodyLayout.setOriginCorner(qt.TopRightCorner)

        self.vertLayout = qtwidgets.QVBoxLayout()
        self.vertLayout.addWidget(self.title)
        self.vertLayout.addWidget(self.body)
        self.vertLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vertLayout)

        self.title.toggled.connect(lambda state: self.isToggled(state))
        self.title.setChecked(True)

    def minimumSizeHint(self):
        return self.sizeHint()

    def sizeHint(self):
        s = qtcore.QSize()
        st = self.title.sizeHint()
        sb = self.body.sizeHint()
        if self.title.isChecked():
            s.setHeight((st.height() + sb.height()) + 10)
            s.setWidth(135)
        else:
            s.setHeight(st.height())
            s.setWidth(135)
        return s

    def minimumSize(self):
        self.minimumSizeHint()

    def setHeader(self, header):
        self.title.setText(header)
        # self.resize(self.sizeHint())

    def addWidget(self, widget):
        widget.setParent(self.body)
        self.bodyLayout.addWidget(widget, len(self.body.children())-2, 0, qt.AlignRight)
        self.resize(self.sizeHint())

    def setBodyColor(self, color):
        self.body.setStyleSheet("color: " + str(color))

    def isToggled(self, checked):
        self.body.setVisible(checked)
        self.resize(self.sizeHint())


class DragWidget(qtwidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(DragWidget, self).__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.setObjectName('DragWidget')
        # self.setStyleSheet('QFrame#DragWidget{background-color: black}')
        self.dragObject = None
        self.dragPixmap = qtgui.QPixmap()
        self.dragDelta = qtcore.QPoint(0, 0)

    def setMoveArea(self, ml=10, mu=10, mr=10, mb=10):
        g = self.geometry()
        self.moveArea = qtcore.QRect(ml, mu, g.width() - 2 * mr, g.height() - 2 * mb)

    def move(self, *args, **kwargs):
        super(DragWidget, self).move(*args, **kwargs)
        self.setMoveArea(10)

    def minimumSizeHint(self):
        s = qtcore.QSize()
        s.setWidth(max(child.pos().x() + child.width() + 10 for child in self.children()))
        s.setHeight(max(child.pos().y() + child.height() + 10 for child in self.children()))
        return s

    def sizeHint(self):
        return self.parent().size()*2

    def mousePressEvent(self, event):
        self.setMoveArea(0, 0, 50, 30)
        self.dragObject = self.childAt(event.pos())
        if not self.dragObject:
            return
        while(self.dragObject.parent() != self):
            self.dragObject = self.dragObject.parent()
            if not self.dragObject:
                return
        self.dragDelta = self.dragObject.pos() - event.pos()
        self.dragObject.render(self.dragPixmap)
        event.ignore()

    def mouseMoveEvent(self, event):
        if self.dragObject:
            objPos = event.pos() + self.dragDelta
            if self.moveArea.contains(objPos):
                self.dragObject.move(objPos)
            # elif not self.geometry().contains(event.pos()):
            else:
                self.dragObject = None

    def mouseReleaseEvent(self, event):
        if self.dragObject:
            objPos = event.pos() + self.dragDelta
            if self.moveArea.contains(objPos):
                self.dragObject.move(objPos)
                self.updateGeometry()
        self.dragObject = None


# %% functions
def changeColorBrightness(rgb, change):
    r = int(rgb[1:3], 16)
    if (r > 256 - change):
        r = r - change
    else:
        r = r + change
    g = int(rgb[3:5], 16)
    if (g > 256 - change):
        g = g - change
    else:
        g = g + change
    b = int(rgb[5:7], 16)
    if (b > 256 - change):
        b = b - change
    else:
        b = b + change
    return '#' + "{:02x}".format(r) + "{:02x}".format(g) + "{:02x}".format(b)


def floatToString(f, n):
    #    s = ("%.8f" % f).rstrip('0').rstrip('.')
    s = str(f)
    if '.' not in s:
        return s
    s = s.rstrip('0').rstrip('.')
    if len(s) <= n:  # 12.4
        return s
    sMatch = floatRegexCompiled.match(s)
    try:
        if len(sMatch[2]) >= n:  # 123456789
            return sMatch[1] + sMatch[2] + sMatch[5]
        if sMatch[2] != '0':  # 12.3456789
            return sMatch[1] + sMatch[2] + sMatch[3][0:n - len(sMatch[2]) + 1] + sMatch[5]
        zeroMatch = re.match("^(0*)(\d*?)$", sMatch[4])
        return sMatch[1] + sMatch[2] + '.' + zeroMatch[1] + zeroMatch[2][0:n].rstrip('0') + sMatch[5]  # 0.000000001234
    except Exception as ex:
        localLogger.warning('error converting float to string: ' + str(ex) + ', string is ' + s)
    return s


testvalues = [0.002100001, 12.001]
teststrings = []
for testvalue in testvalues:
    teststrings.append(floatToString(testvalue, 4))
