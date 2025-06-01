# -*- coding: utf-8 -*-
"""
Created on Thu Oct  4 15:15:19 2018

@author: Martin
"""

# todo: check why default section is written to file ?!


import helper.QLogger as logger
from PyQt5.QtWidgets import QLineEdit, QStyledItemDelegate
from PyQt5.QtCore import QAbstractItemModel, QSize, QVariant, Qt, pyqtSignal
import widgets.ScrollableTable as sTable

localLogger = logger.globalLogger

class SettingsModelItem():
    def __init__(self, key, parentkey, parent):
        self.key = key
        self.parentKey = parentkey
        self.parent = parent

    def isEqual(self, other):
        return self.key == other.key and self.parentKey == other.parentKey


# settings model
class SettingsModel(QAbstractItemModel):
    displayCurrenciesChanged = pyqtSignal([list])
    useWalletTaxFreeLimitYearsChanged = pyqtSignal()

    def __init__(self, settings, *args, **kwargs):
        super(SettingsModel, self).__init__(*args, **kwargs)
        self.settings = settings
        self.sections = list(self.settings)[1:]
        self.items = []
        self.header = ['setting', 'value', 'description']

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            return self.header[section]
        return QVariant()

    def parent(self, index):
        return self.getParentIndexFromIndex(index)

    def rowCount(self, parent):
        if not parent.isValid():
            return len(self.sections)
        else:
            # check if it is a parent or a child item
            if self.getParentIndexFromIndex(parent).isValid():  # only a child item has a valid parent
                return 0  # return no childs
            else:  # parent item, return number of childs
                return len(self.settings[self.getItemFromIndex(parent).key])

    def columnCount(self, parent):
        return 3

    def index(self, row, column, parent):
        if parent.isValid():
            parentkey = self.getItemFromIndex(parent).key
            subsettings = self.settings[parentkey]
            try:
                key = list(subsettings)[row]
            except IndexError:
                key = ""
        else:
            parentkey = ""
            try:
                key = self.sections[row]
            except IndexError:
                key = ""
        newItem = SettingsModelItem(key, parentkey, parent)
        itemId = -1
        itemFound = False
        for item in self.items:
            itemId += 1
            if item.isEqual(newItem):
                itemFound = True
                break
        if not itemFound:
            itemId = len(self.items)
            self.items.append(newItem)
        index = self.createIndex(row, column, itemId)
        return index

    def data(self, index, role):
        if role == Qt.DisplayRole:
            parentIndex = self.getParentIndexFromIndex(index)
            item = self.getItemFromIndex(index)
            if parentIndex.isValid():
                parent = self.getItemFromIndex(parentIndex)
                if index.column() == 0:
                    return item.key
                if index.column() == 1:
                    return self.settings[parent.key][item.key]
                if index.column() == 2:
                    try:
                        return self.settings.descriptions[parent.key][item.key]
                    except KeyError:
                        return 'depricated/ unknowen'
            else:
                return self.sections[index.row()]
        return QVariant()

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            try:
                item = self.getItemFromIndex(index)
                self.settings[item.parentKey][item.key] = value
                self.dataChanged.emit(index, index)
                self.itemChanged(item)
                return True
            except:
                return False
        return False

    def itemChanged(self, item):
        if item.parentKey.lower() == 'currency' and item.key.lower() == 'defaultdisplaycurrencies':
            self.displayCurrenciesChanged.emit(self.settings.displayCurrencies())
        if item.parentKey.lower() == 'tax' and item.key.lower() == 'usewallettaxfreelimityears':
            self.useWalletTaxFreeLimitYearsChanged.emit()

    def resetDefault(self):
        self.beginResetModel()
        oldCur = self.settings.displayCurrencies()
        self.settings.resetDefault()
        if oldCur != self.settings.displayCurrencies():
            self.displayCurrenciesChanged.emit(self.settings.displayCurrencies())
        self.endResetModel()

    def restoreSettings(self):
        oldCur = self.settings.displayCurrencies()
        self.settings.readSettings()
        if oldCur != self.settings.displayCurrencies():
            self.displayCurrenciesChanged.emit(self.settings.displayCurrencies())

    def flags(self, index):
        column = index.column()
        parent = self.getParentIndexFromIndex(index)
        if parent.isValid():
            if column == 1:
                return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def getParentIndexFromIndex(self, index):
        return self.items[index.internalId()].parent

    def getItemFromIndex(self, index):
        return self.items[index.internalId()]

    def getParentFromIndex(self, index):
        parentIndex = self.getParentIndexFromIndex(index)
        if parentIndex.isValid():
            return self.getItemFromIndex(parentIndex)
        else:
            return None


class SettingsDelegate(QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(SettingsDelegate, self).__init__(*args, **kwargs)

    def createEditor(self, parent, option, index):
        if int(index.flags()) & Qt.ItemIsEditable:
            return QLineEdit(parent)
        return 0

    def setEditorData(self, editor, index):
        editor.setText(index.data())

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text(), Qt.EditRole)

    def sizeHint(self, option, index):
        return QSize()


class SettingsTreeView(sTable.QScrollableTreeView):
    def __init__(self, *args, **kwargs):
        super(SettingsTreeView, self).__init__(*args, **kwargs)

        self.setItemDelegateForColumn(1, SettingsDelegate())
