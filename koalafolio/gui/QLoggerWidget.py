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

qt = qtcore.Qt

class QLogModel(qtcore.QAbstractListModel):
    def __init__(self, *args, **kwargs):
        super(QLogModel, self).__init__(*args, **kwargs)
        self.stringList = []
        self.messageType = []
        self.color = []

    def addString(self, message, messageType):
        row = len(self.stringList)
        # RowStartIndex = self.index(row, row)
        # RowEndIndex = self.index(row, row)
        self.beginInsertRows(qtcore.QModelIndex(), row, row)
        self.stringList.append(message)
        self.messageType.append(messageType)
        errorColor = qtgui.QColor(255, 0, 0, 255)
        warningColor = qtgui.QColor(255, 165, 0, 255)
        # infoColor = qtgui.QColor(0, 0, 0, 255)
        if messageType == 'e':
            self.color.append(qtgui.QBrush(errorColor))
        elif messageType == 'w':
            self.color.append(qtgui.QBrush(warningColor))
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


class QLogView(qtwidgets.QListView):
    def __init__(self, parent=None, logfile=None, *args, **kwargs):
        super(QLogView, self).__init__(parent=parent, *args, **kwargs)

        self.logfile = logfile
        self.setVerticalScrollBar(sTable.MinWheelScrollingScrollbar(orientation=qtcore.Qt.Vertical, parent=self))

    def rowsInserted(self, parent, start, end):
        super(QLogView, self).rowsInserted(parent, start, end)
        self.scrollToBottom()

    def mouseDoubleClickEvent(self, a0: qtgui.QMouseEvent) -> None:
        try:
            os.system(self.logfile)
        except Exception:
            return
