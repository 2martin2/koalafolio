# -*- coding: utf-8 -*-
"""
Created on 11.04.2021

@author: Martin
"""

from PyQt5 import QtCore
from PyQt5.QtWidgets import QHeaderView, QLineEdit

class FilterableHeaderView(QHeaderView):
    """QHeaderView with filterboxes

    Filterboxes are placed under each header item and Signal filterActivated is fired whenever Text is changed in a box
    """
    # filterActivated Signal: [filterboxIndex, filterText]
    filterActivated = QtCore.pyqtSignal([int, str])

    def __init__(self, parent):
        super(FilterableHeaderView, self).__init__(QtCore.Qt.Horizontal, parent)
        self._editors = []
        self._padding = 4
        self.setStretchLastSection(True)
        #self.setResizeMode(QHeaderView.Stretch)
        self.setDefaultAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.setSectionsClickable(True)
        self.setSortIndicatorShown(True)
        self.sectionResized.connect(self.adjustPositions)
        parent.horizontalScrollBar().valueChanged.connect(self.adjustPositions)

    def setFilterBoxes(self, count):
        while self._editors:
            editor = self._editors.pop()
            editor.deleteLater()
        for index in range(count):
            editor = QLineEdit(self.parent())
            editor.setPlaceholderText('Filter')
            editor.textChanged.connect(lambda text, x=index: self.filterActivated.emit(x, text))
            self._editors.append(editor)
        self.adjustPositions()

    def emitFilterActivated(self, index, text):
        self.filterActivated.emit(index, text)

    def sizeHint(self):
        size = super().sizeHint()
        if self._editors:
            height = self._editors[0].sizeHint().height()
            size.setHeight(size.height() + height + self._padding)
        return size

    def updateGeometries(self):
        if self._editors:
            height = self._editors[0].sizeHint().height()
            self.setViewportMargins(0, 0, 0, height + self._padding)
        else:
            self.setViewportMargins(0, 0, 0, 0)
        super().updateGeometries()
        self.adjustPositions()

    def adjustPositions(self):
        for index, editor in enumerate(self._editors):
            height = editor.sizeHint().height()
            CompensateY = 0
            CompensateX = 0
            if self._editors[index].__class__.__name__ == "QComboBox":
                CompensateY = +2
            elif self._editors[index].__class__.__name__ == "QWidget":
                CompensateY = -1
            elif self._editors[index].__class__.__name__ == "QPushButton":
                CompensateY = -1
            elif self._editors[index].__class__.__name__ == "QCheckBox":
                CompensateY = 4
                CompensateX = 4
            editor.move(self.pos().x() + self.sectionPosition(index) - self.offset() + 1 + CompensateX,self.pos().y() + height + (self._padding // 2) + 2 + CompensateY)
            editor.resize(self.sectionSize(index), height)

    def filterText(self, index):
        if 0 <= index < len(self._editors):
            if self._editors[index].__class__.__name__ == "QLineEdit":
                return self._editors[index].text()
        return ''

    def setFilterText(self, index, text):
        if 0 <= index < len(self._editors):
            self._editors[index].setText(text)

    def clearFilters(self):
        for editor in self._editors:
            editor.clear()


# class Window(QWidget):
#     def __init__(self):
#         super(Window, self).__init__()
#         self.view = QTableView()
#         layout = QVBoxLayout(self)
#         layout.addWidget(self.view)
#         header = FilterableHeaderView(self.view)
#         self.view.setHorizontalHeader(header)
#         model = QtGui.QStandardItemModel(self.view)
#         model.setHorizontalHeaderLabels('One Two Three Four Five Six Seven'.split())
#         self.view.setModel(model)
#         header.setFilterBoxes(model.columnCount())
#         header.filterActivated.connect(self.handleFilterActivated)
#
#     def handleFilterActivated(self):
#         header = self.view.horizontalHeader()
#         for index in range(header.count()):
#             print((index, header.filterText(index)))
#
#
# if __name__ == '__main__':
#
#     app = QApplication(sys.argv)
#     window = Window()
#     window.setGeometry(800, 100, 600, 300)
#     window.show()
#     sys.exit(app.exec_())