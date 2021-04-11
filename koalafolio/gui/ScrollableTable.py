# -*- coding: utf-8 -*-
"""
Created on 11.04.2021

@author: Martin
"""

import PyQt5.QtGui as qtgui
import PyQt5.QtCore as qtcore
from PyQt5.QtWidgets import QScrollBar, QTreeView, QTableView

class MinWheelScrollingScrollbar(QScrollBar):
    def __init__(self, orientation, parent):
        super(MinWheelScrollingScrollbar, self).__init__(orientation=orientation, parent=parent)

    def wheelEvent(self, event: qtgui.QWheelEvent):
        numPixels = event.pixelDelta()
        numDegrees = event.angleDelta() / 8

        if numPixels:
            self.scrollWithPixels(numPixels)
        elif numDegrees:
            numSteps = numDegrees / 15
            self.scrollWithDegrees(numSteps.y())

        event.accept()

    def scrollWithPixels(self, numPixels):
        self.setValue(self.value() - numPixels)

    def scrollWithDegrees(self, numSteps):
        self.setValue(self.value() - self.singleStep() * numSteps)


class QScrollableTreeView(QTreeView):
    def __init__(self, parent, *args, **kwargs):
        super(QScrollableTreeView, self).__init__(parent=parent, *args, **kwargs)

        self.setVerticalScrollBar(MinWheelScrollingScrollbar(orientation=qtcore.Qt.Vertical, parent=self))


class QScrollableTableView(QTableView):
    def __init__(self, parent, *args, **kwargs):
        super(QScrollableTableView, self).__init__(parent=parent, *args, **kwargs)

        self.setVerticalScrollBar(MinWheelScrollingScrollbar(orientation=qtcore.Qt.Vertical, parent=self))