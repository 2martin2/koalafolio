# -*- coding: utf-8 -*-
"""
Created on Thu Oct  4 15:15:19 2018

@author: VOL4ABT
"""

# todo: check why default section is written to file ?!
# todo: implement conversion from Settings Dict as get and set methods


import gui.QLogger as logger
import PyQt5.QtWidgets as qtwidgets
import PyQt5.QtCore as qtcore
import PyQt5.QtGui as qtgui
import PcpCore.settings as settings

qt = qtcore.Qt
localLogger = logger.globalLogger


class QSettings(settings.Settings):
    def __init__(self, *args, **kwargs):
        super(QSettings, self).__init__(*args, **kwargs)

    def initSettings(self):
        # set default settings

        # window settings
        self['window'] = {}
        self['window']['windowsize'] = '1200x600'
        self['window']['windowpos'] = '200,200'
        self['window']['windowstate'] = '0'
        self['window']['windowTitle'] = 'KoalaFolio'
        self['window']['windowstyle'] = 'Fusion'
        self['window']['stylesheetname'] = 'defaultStyle'
        # color settings
        self['color'] = {}
        self['color']['BACKGROUND'] = '42,46,51'
        self['color']['TEXT_NORMAL'] = '255,255,255'
        self['color']['TEXT_HIGHLIGHTED'] = '42,46,51'
        self['color']['PRIMARY'] = '75,180,255'
        self['color']['SECONDARY'] = '255,105,75'
        self['color']['TERTIARY'] = '75,255,240'
        self['color']['NEGATIV'] = '255,90,75'
        self['color']['POSITIV'] = '90,255,75'
        self['color']['NEUTRAL'] = '200,200,200'
        # gui settings
        self['gui'] = {}
        self['gui']['filterUseRegex'] = 'True'
        self['gui']['portfolioFilterRow'] = '3'
        self['gui']['tradeFilterRow'] = '2'
        self['gui']['portfolioFilterDir'] = (str(qt.AscendingOrder))
        self['gui']['tradeFilterDir'] = str(qt.AscendingOrder)
        self['gui']['toolTipsEnabled'] = 'True'
        self['gui']['performanceChartIndex'] = '0'

        super(QSettings, self).initSettings()

    def getWindowProperties(self):
        windowProperties = {}
        try:
            size = [int(s) for s in self['window']['windowsize'].split('x')]
            pos = [int(s) for s in self['window']['windowpos'].split(',')]
        except Exception as ex:
            localLogger.error('error parsing window geometry: ' + str(ex))
            localLogger.info('using default window geometry')
            size = [1200, 800]
            pos = [200, 200]
        windowProperties['geometry'] = qtcore.QRect(pos[0], pos[1], size[0], size[1])
        try:
            state = qt.WindowState(int(self['window']['windowstate']))
        except Exception as ex:
            localLogger.error('error parsing window state: ' + str(ex))
            localLogger.info('using default window state')
            state = qt.WindowNoState
        windowProperties['state'] = state
        return windowProperties

    def setWindowProperties(self, geometry, state):
        if state == qt.WindowNoState:  # only set window size if window is in normal state
            self['window']['windowpos'] = str(geometry.x()) + ',' + str(geometry.y())
            self['window']['windowSize'] = str(geometry.width()) + 'x' + str(geometry.height())
        self['window']['windowState'] = str(int(state))

    def getColors(self):
        def convertColor(colorStr, *default):
            try:
                color = colorStr.split(',')
                r = int(color[0])
                g = int(color[1])
                b = int(color[2])
                return r, g, b  # return tuple
            except Exception as ex:
                localLogger.warning('error parsing color ' + colorStr + ': ' + str(ex))
                localLogger.info('using default color')
                return default

        colorDict = {}
        for key in self['color']:
            if key == 'default':
                continue
            if key == 'TEXT_NORMAL':
                colorDict[key.upper()] = convertColor(self['color'][key], 0, 0, 0)
                continue
            colorDict[key.upper()] = convertColor(self['color'][key], 255, 255, 255)
        return colorDict

    def getColor(self, name):
        colors = self.getColors()
        if name in colors:
            return colors[name]
        else:
            return 255, 255, 255  # return white if invalid colorname

    def setColor(self, name, *value):
        for key in self['colors']:
            if key.lower() == name.lower():
                self['colors'][key] = str(value).replace('(', '').replace(')', '')

    def getGuiSettings(self):
        gui = {}
        try:
            gui['filterUseRegex'] = self.getboolean('gui', 'filterUseRegex')
        except ValueError:
            gui['filterUseRegex'] = True
        try:
            gui['portfolioFilterRow'] = self.getint('gui', 'portfolioFilterRow')
        except ValueError:
            gui['portfolioFilterRow'] = 3
        try:
            gui['tradeFilterRow'] = self.getint('gui', 'tradeFilterRow')
        except ValueError:
            gui['tradeFilterRow'] = 2
        try:
            gui['portfolioFilterDir'] = self.getint('gui', 'portfolioFilterDir')
        except ValueError:
            gui['portfolioFilterDir'] = qt.AscendingOrder
        try:
            gui['tradeFilterDir'] = self.getint('gui', 'tradeFilterDir')
        except ValueError:
            gui['tradeFilterDir'] = qt.AscendingOrder
        try:
            gui['toolTipsEnabled'] = self.getboolean('gui', 'toolTipsEnabled')
        except ValueError:
            gui['toolTipsEnabled'] = True
        try:
            gui['performanceChartIndex'] = self.getint('gui', 'performanceChartIndex')
        except ValueError:
            gui['performanceChartIndex'] = 0
        return gui

    def getGuiSetting(self, key):
        return self.getGuiSettings()[key]

    def setGuiSettings(self, gui):
        for key in gui:
            if key in self['gui']:
                self['gui'][key] = str(gui[key])
            else:
                raise KeyError('invalid key ' + key + ' for gui settings')


mySettings = QSettings()

class SettingsIndex(qtcore.QModelIndex):
    def __init__(self, model, row, column, key, parent=qtcore.QModelIndex(), *args, **kwargs):
        super(SettingsIndex, self).__init__(*args, **kwargs)
        self.myParent = parent
        self.name = key
        self.myRow = row
        self.myColumn = column
        self.myModel = model
        self.myIsValid = True

    def column(self):
        return self.myColumn

    def row(self):
        return self.myRow

    def model(self):
        return self.myModel

    def isValid(self):
        return self.myIsValid

    def parent(self):
        return self.myParent()


class SettingsModelItem():
    def __init__(self, key, parentkey, parent):
        self.key = key
        self.parentKey = parentkey
        self.parent = parent

    def isEqual(self, other):
        return self.key == other.key and self.parentKey == other.parentKey


# settings model
class SettingsModel(qtcore.QAbstractItemModel):
    def __init__(self, settings, *args, **kwargs):
        super(SettingsModel, self).__init__(*args, **kwargs)
        self.settings = settings
        self.sections = list(self.settings)[1:]
        self.items = []
        self.header = ['setting', 'value']

    def headerData(self, section, orientation, role):
        if role == qt.DisplayRole:
            return self.header[section]
        return qtcore.QVariant()

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
        return 2

    def index(self, row, column, parent):
        if parent.isValid():
            parentkey = self.getItemFromIndex(parent).key
            subsettings = self.settings[parentkey]
            key = list(subsettings)[row]
        else:
            parentkey = ""
            key = self.sections[row]
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
        if role == qt.DisplayRole:
            parentIndex = self.getParentIndexFromIndex(index)
            item = self.getItemFromIndex(index)
            if parentIndex.isValid():
                parent = self.getItemFromIndex(parentIndex)
                if index.column() == 0:
                    return item.key
                if index.column() == 1:
                    return self.settings[parent.key][item.key]
            else:
                return self.sections[index.row()]
        return qtcore.QVariant()

    def setData(self, index, value, role):
        if role == qt.EditRole:
            try:
                item = self.getItemFromIndex(index)
                self.settings[item.parentKey][item.key] = value
                self.dataChanged.emit(index, index)
                return True
            except:
                return False
        return False

    def flags(self, index):
        column = index.column()
        parent = self.getParentIndexFromIndex(index)
        if parent.isValid():
            if column == 0:
                return qt.ItemIsSelectable | qt.ItemIsEnabled | qt.ItemNeverHasChildren
            if column == 1:
                return qt.ItemIsSelectable | qt.ItemIsEditable | qt.ItemIsEnabled | qt.ItemNeverHasChildren
        else:
            return qt.ItemIsSelectable | qt.ItemIsEnabled

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


class SettingsDelegate(qtwidgets.QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(SettingsDelegate, self).__init__(*args, **kwargs)

    def createEditor(self, parent, option, index):
        if int(index.flags()) & qt.ItemIsEditable:
            return qtwidgets.QLineEdit(parent)
        return 0

    def setEditorData(self, editor, index):
        editor.setText(index.data())

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def setModelData(self, editor, model, index):

        model.setData(index, editor.text(), qt.EditRole)

    def sizeHint(self, option, index):
        return qtcore.QSize()


class SettingsTreeView(qtwidgets.QTreeView):
    def __init__(self, *args, **kwargs):
        super(SettingsTreeView, self).__init__(*args, **kwargs)

        self.setItemDelegateForColumn(1, SettingsDelegate())
