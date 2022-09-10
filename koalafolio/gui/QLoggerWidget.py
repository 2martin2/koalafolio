# -*- coding: utf-8 -*-
"""
Created on Wen Jan 02 14:21:00 2019

@author: Martin
"""

import os.path
import PyQt5.QtCore as qtcore
import PyQt5.QtGui as qtgui
import PyQt5.QtWidgets as qtwidgets
import koalafolio.gui.ScrollableTable as sTable
import QThreads


qt = qtcore.Qt

class QLogModel(qtcore.QAbstractListModel):
    def __init__(self, *args, **kwargs):
        super(QLogModel, self).__init__(*args, **kwargs)
        self.stringList = []
        self.messageType = []
        self.color = []

        self.errorColorBrush = qtgui.QBrush(qtgui.QColor(255, 0, 0, 255))
        self.warningColorBrush = qtgui.QBrush(qtgui.QColor(255, 165, 0, 255))

    def addString(self, message, messageType):
        row = len(self.stringList)
        # RowStartIndex = self.index(row, row)
        # RowEndIndex = self.index(row, row)
        self.beginInsertRows(qtcore.QModelIndex(), row, row+1)
        self.stringList.append(message)
        self.messageType.append(messageType)

        # infoColor = qtgui.QColor(0, 0, 0, 255)
        if messageType == 'e':
            self.color.append(self.errorColorBrush)
        elif messageType == 'w':
            self.color.append(self.warningColorBrush)
        else:
            self.color.append(qtcore.QVariant())
        self.endInsertRows()

    def rowCount(self, parent):
        return len(self.stringList)

    def data(self, index, role):
        if role == qt.DisplayRole:
            return self.stringList[index.row()]
        if role == qt.ForegroundRole:
            return self.color[index.row()]
        return qtcore.QVariant()

    def nextIndex(self, currentIndex):
        return self.index(currentIndex.row()+1, 0, currentIndex.parent())



class QLogView(qtwidgets.QListView):

    def __init__(self, parent=None, logfile=None, *args, **kwargs):
        super(QLogView, self).__init__(parent=parent, *args, **kwargs)

        self.logfile = logfile
        self.setVerticalScrollBar(sTable.MinWheelScrollingScrollbar(orientation=qtcore.Qt.Vertical, parent=self))

        self.autoScrollTimer = TimedAutoScroll()
        self.autoScrollTimer.performScrollStep.connect(self.scrollStep)

        self.currentLastRow = 0
        self.scrollBarRowOffset = 3

    def setModel(self, model, *args, **kwargs):
        self.currentLastRow = model.rowCount(parent=qtcore.QModelIndex()) - 1
        self.verticalScrollBar().setValue(1)
        self.scrollBarRowOffset = self.currentLastRow - self.verticalScrollBar().value()
        super(QLogView, self).setModel(model, *args, **kwargs)

    def rowsInserted(self, parent, start, end):
        super(QLogView, self).rowsInserted(parent, start, end)
        self.autoScrollTimer.addScrollSteps(end-start)
        #self.scrollToBottom()

    def scrollStep(self):
        self.currentLastRow += 1
        if self.isAtCurrentLastRow():
            index = self.model().index(self.currentLastRow, 0, qtcore.QModelIndex())
            self.scrollTo(index, qtwidgets.QAbstractItemView.PositionAtBottom)

    def isAtCurrentLastRow(self):
        #print("currentLastRow: " + str(self.currentLastRow) + ", scrollBarValue: " + str(self.verticalScrollBar().value() + self.scrollBarRowOffset))
        return -1 <= (self.verticalScrollBar().value() + self.scrollBarRowOffset) - self.currentLastRow <= 1

    def mouseDoubleClickEvent(self, a0: qtgui.QMouseEvent) -> None:
        try:
            os.system(self.logfile)
        except Exception:
            return


class TimedAutoScroll(qtcore.QObject):
    performScrollStep = qtcore.pyqtSignal()

    def __init__(self):
        super(TimedAutoScroll, self).__init__()
        self.scrollStepCount = 0
        self.isScrollQueueEmpty = True

        self.scrollTimer = qtcore.QTimer()
        self.scrollTimer.timeout.connect(self.triggerStep)
        self.scrollTimer.start(300)

    def addScrollSteps(self, count):
        self.scrollStepCount += count
        if self.isScrollQueueEmpty:
            self.triggerStep()

    def triggerStep(self):
        if self.scrollStepCount > 0:
            self.isScrollQueueEmpty = False
            self.scrollStepCount -= 1
            self.performScrollStep.emit()
        else:
            self.isScrollQueueEmpty = True
