# -*- coding: utf-8 -*-
"""
Created on 11.04.2021

@author: Martin
"""

from PyQt5.QtCore import QModelIndex, QSortFilterProxyModel, Qt, pyqtSignal
import re
import koalafolio.gui.QLogger as logger
import koalafolio.gui.FilterableHeader as filterableHeader
import koalafolio.gui.ScrollableTable as sTable

localLogger = logger.globalLogger

# proxy model for sorting and filtering tables
class SortFilterProxyModel(QSortFilterProxyModel):
    """proxy model that can be filtered by regex and sorted """
    def __init__(self, *args, **kwargs):
        super(SortFilterProxyModel, self).__init__(*args, **kwargs)
        self.filters = {}
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.useRegex = True

        self.sortedRow = 0
        self.sortedDir = 0

    def sort(self, row, order):
        super(SortFilterProxyModel, self).sort(row, order)
        self.sortedRow = row
        self.sortedDir = order

    def setFilterByColumn(self, column, regex):
        self.filters[column] = regex
        self.invalidateFilter()

    def lessThan(self, index1, index2):
        try:
            return float(index1.data()) < float(index2.data())
        except ValueError:
            return str(index1.data()) < str(index2.data())

    def filterAcceptsRow(self, source_row, source_parent):
        for key, regex in self.filters.items():
            ix = self.sourceModel().index(source_row, key, source_parent)
            if ix.isValid():
                text = str(self.sourceModel().data(ix))
                try:
                    if self.useRegex:
                        if not re.match('.*' + regex + '.*', text, re.IGNORECASE):
                            return False
                    else:  # no regex
                        if not regex.lower() in text.lower():
                            return False
                except Exception as ex:  # skip column if regex error
                    pass
        return True



class FilterableTableView(sTable.QScrollableTableView):
    """Table View with Filterable Header"""
    # filterActivated Signal: [filterboxIndex, filterText]
    filterActivated = pyqtSignal([int, str])
    def __init__(self, *args, **kwargs):
        super(FilterableTableView, self).__init__(*args, **kwargs)

        # add filterable Header as horizontal Header
        header = filterableHeader.FilterableHeaderView(self)
        self.setHorizontalHeader(header)
        header.filterActivated.connect(self.filterActivated)

    def setModel(self, model: SortFilterProxyModel):
        """create filter boxes regarding column count of new model"""
        super(FilterableTableView, self).setModel(model)
        # init filter boxes of header view
        self.initFilterBoxes()
        model.sourceModelChanged.connect(lambda: self.initFilterBoxes())
        # connect filter Activated Signal of this view with Filter Slot from model
        self.filterActivated.connect(lambda index, text: model.setFilterByColumn(index, text))

    def initFilterBoxes(self):
        self.horizontalHeader().setFilterBoxes(self.model().columnCount(QModelIndex()))

    def clearFilters(self, checked):
        """clear all Filters of horizontal header"""
        self.horizontalHeader().clearFilters()

    def columnCountChanged(self, oldCount, newCount):
        """update filterbox count if column Count has changed"""
        super(FilterableTableView, self).columnCountChanged(oldCount, newCount)
        # reinit filter boxes of header view
        self.horizontalHeader().setFilterBoxes(newCount)


class FilterableTreeView(sTable.QScrollableTreeView):
    """Table View with Filterable Header"""
    # filterActivated Signal: [filterboxIndex, filterText]
    filterActivated = pyqtSignal([int, str])
    def __init__(self, *args, **kwargs):
        super(FilterableTreeView, self).__init__(*args, **kwargs)

        # add filterable Header as horizontal Header
        header = filterableHeader.FilterableHeaderView(self)
        self.setHeader(header)
        header.filterActivated.connect(self.filterActivated)

    def setModel(self, model: SortFilterProxyModel):
        """create filter boxes regarding column count of new model"""
        super(FilterableTreeView, self).setModel(model)
        # init filter boxes of header view
        self.initFilterBoxes()
        model.sourceModelChanged.connect(lambda: self.initFilterBoxes())
        # connect filter Activated Signal of this view with Filter Slot from model
        self.filterActivated.connect(lambda index, text: model.setFilterByColumn(index, text))

    def initFilterBoxes(self):
        self.header().setFilterBoxes(self.model().columnCount(QModelIndex()))

    def clearFilters(self, checked):
        """clear all Filters of horizontal header"""
        self.header().clearFilters()

    def columnCountChanged(self, oldCount, newCount):
        """update filterbox count if column Count has changed"""
        super(FilterableTreeView, self).columnCountChanged(oldCount, newCount)
        # reinit filter boxes of header view
        self.header().setFilterBoxes(newCount)