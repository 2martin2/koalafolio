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
import koalafolio.gui.QSettings as settings

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


# status bar for printing logging entries
class StatusBar(StyledFrame):
    def __init__(self, parent, height=80, *args, **kwargs):
        super(StatusBar, self).__init__(parent=parent, *args, **kwargs)

        self.setObjectName('statusbar')
        self.setFrameShadow(qtwidgets.QFrame.Sunken)
        self.setFixedHeight(height)

        self.statusView = logger.QLogView(self)
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
        # return only vaild path, otherwise return None
        try:
            path = Path(self.lineEdit.text())
            if ((path.is_file() | path.is_dir())):
                return path
            else:
                return None
        except Exception as ex:
            print("converting path -" + self.lineEdit.text() + "- failed: " + str(ex))
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

# %% tables
class DataFrameTable(qtwidgets.QTableWidget):
    def __init__(self, parent, *args, **kwargs):
        super(DataFrameTable, self).__init__(parent=parent, *args, **kwargs)

        self.setSortingEnabled(True)
        self.horizontalHeader().setSectionResizeMode(qtwidgets.QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(qtwidgets.QHeaderView.ResizeToContents)

    def fromDataFrame(self, dataframe):
        # header
        tableHeader = dataframe.columns.values.tolist()
        self.setColumnCount(len(tableHeader))
        self.setHorizontalHeaderLabels(tableHeader)

        # data
        self.setRowCount(dataframe.shape[0])
        for rowIndex, row in dataframe.iterrows():
            self.setRow(row.tolist(), rowIndex)

    def setRow(self, row, rowIndex):
        # check size of row
        if len(row) == self.columnCount():
            for columnIndex in range(len(row)):
                self.setItem(rowIndex, columnIndex, qtwidgets.QTableWidgetItem(str(row[columnIndex])))

    def setColumn(self, column, columnIndex):
        # check size of column
        if len(column) == self.rowCount():
            for rowIndex in range(len(column)):
                self.setItem(rowIndex, columnIndex, qtwidgets.QTableWidgetItem(str(column[rowIndex])))


# && Filterable Trade Table Widget
class QFilterTableView(qtwidgets.QWidget):
    def __init__(self, parent, tableView, *args, **kwargs):
        super(QFilterTableView, self).__init__(parent=parent, *args, **kwargs)

        self.proxyModel = SortFilterProxyModel()
        self.tableView = tableView
        self.tableView.setParent(self)
        self.tableView.setModel(self.proxyModel)
        self.tableView.show()

        self.filterLine = qtwidgets.QWidget(self)
        self.filterLine.setFixedHeight(20)
        self.filterMargin = 4
        self.resetFilterButton = qtwidgets.QPushButton('X', self)
        # self.setWidgetStyle()
        self.resetFilterButton.setFixedWidth(25)
        self.resetFilterButton.setFixedHeight(20)
        self.resetFilterButton.clicked.connect(self.clearFilter)
        self.resetFilterButton.move(0, 0)

        self.filterBoxes = []
        self.initFilterBoxes()
        self.proxyModel.modelReset.connect(self.initFilterBoxes)

        self.vertLayout = qtwidgets.QVBoxLayout(self)
        self.vertLayout.addWidget(self.filterLine)
        self.vertLayout.addWidget(self.tableView)
        self.vertLayout.setContentsMargins(5, 2, 5, 5)

        self.tableView.viewResized.connect(self.layoutFilterRow)
        self.tableView.viewUpdated.connect(self.layoutFilterRow)
        self.tableView.horizontalHeader().geometriesChanged.connect(self.layoutFilterRow)
        self.tableView.horizontalHeader().sectionResized.connect(self.sectionChanged)

    def clearWidgetStyle(self):
        self.resetFilterButton.setStyleSheet("")

    def setWidgetStyle(self):
        margin = (self.resetFilterButton.width() - self.resetFilterButton.height())
        self.resetFilterButton.setStyleSheet(
            "QPushButton {border-image: url(./graphics/delete.png) " + str(margin) + " 0 " + str(margin) + " 0 stretch;}")

    def initFilterBoxes(self):
        for filterBox in self.filterBoxes:
            filterBox.setParent(None)
        self.filterBoxes = []
        for index in range(self.tableView.model().columnCount()):
            self.filterBoxes.append(qtwidgets.QLineEdit(self))
            self.filterBoxes[index].textChanged.connect(lambda t, x=index: self.filterColumns(t, x))
            self.filterBoxes[index].setPlaceholderText('no filter')
            self.filterBoxes[index].setFixedHeight(20)
        self.layoutFilterRow()

    def sectionChanged(self, index, oldSize, newSize):
        if index < len(self.filterBoxes):
            self.setFilterBoxSize(index, newSize)

    def layoutFilterRow(self):
        tableStart = 5
        self.resetFilterButton.move(tableStart, 0)
        vertHeaderWidth = self.tableView.verticalHeader().width()
        buttonWidth = 25 if vertHeaderWidth < 25 else vertHeaderWidth
        self.resetFilterButton.setFixedWidth(buttonWidth)
        # layout boxes
        if self.filterBoxes:
            self.filterBoxes[0].move(tableStart + buttonWidth + self.filterMargin, 0)
            self.setFilterBoxSize(0, self.tableView.columnWidth(0))


    def setFilterBoxSize(self, index, size):
        size -= self.filterMargin
        if index == 0:
            # check if button needs space of first column
            vertHeaderWidth = self.tableView.verticalHeader().width()
            buttonWidth = self.resetFilterButton.width()
            filterSize = size - buttonWidth + vertHeaderWidth
            # filterSize = filterSize if filterSize > 20 else 20
            self.filterBoxes[index].setFixedWidth(filterSize)
        else:
            self.filterBoxes[index].setFixedWidth(size)
        # move filterboxes after changed box
        for col in range(index+1, len(self.filterBoxes)):
            pos = self.filterBoxes[col - 1].pos()
            pos.setX(pos.x() + self.filterBoxes[col - 1].width() + self.filterMargin)
            self.filterBoxes[col].move(pos)

    def setModel(self, model):
        self.proxyModel.setSourceModel(model)
        self.initFilterBoxes()

    def filterColumns(self, text, col):
        self.tableView.model().setFilterByColumn(text, col)

    def clearFilter(self):
        for filterBox in self.filterBoxes:
            filterBox.clear()

    def switchRegexFilter(self, state):
        if state == qt.Checked:
            self.proxyModel.useRegex = True
        else:  # not checked
            self.proxyModel.useRegex = False



# %% Trade table model
# class QTradeTableModel(qtcore.QAbstractTableModel):
class SortFilterProxyModel(qtcore.QSortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        super(SortFilterProxyModel, self).__init__(*args, **kwargs)
        self.filters = {}
        self.setFilterCaseSensitivity(qt.CaseInsensitive)

        self.sortedRow = 0
        self.sortedDir = 0

    def sort(self, row, order):
        super(SortFilterProxyModel, self).sort(row, order)
        self.sortedRow = row
        self.sortedDir = order

    def setFilterByColumn(self, regex, column):
        self.filters[column] = regex
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        for key, regex in self.filters.items():
            ix = self.sourceModel().index(source_row, key, source_parent)
            if ix.isValid():
                text = str(self.sourceModel().data(ix))
                try:
                    if settings.mySettings.getGuiSettings()['filterUseRegex']:
                        if not re.match('.*' + regex + '.*', text, re.IGNORECASE):
                            return False
                    else:  # no regex
                        if not regex.lower() in text.lower():
                            return False
                except Exception as ex:  # skip column if regex error
                    pass
        return True


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
        print(str(ex) + ', string is ' + s)
    return s


testvalues = [0.002100001, 12.001]
teststrings = []
for testvalue in testvalues:
    teststrings.append(floatToString(testvalue, 4))
