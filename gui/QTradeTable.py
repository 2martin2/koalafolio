# -*- coding: utf-8 -*-
"""
Created on Wed Dec 19 18:11:53 2018

@author: Martin
"""

# -*- coding: utf-8 -*-
"""
Created on Sun Dec 16 19:09:51 2018

@author: Martin
"""

import PyQt5.QtGui as qtgui
import PyQt5.QtWidgets as qtwidgets
import PyQt5.QtCore as qtcore
import gui.Qcontrols as controls
import os
import PcpCore.core as core
import Import.Converter as converter
import gui.QThreads as threads
import gui.QLogger as logger
import Import.TradeImporter as importer
import Import.Models as models

localLogger = logger.globalLogger
qt = qtcore.Qt


# trade table
class TradeTableWidget(qtwidgets.QTableWidget):
    tradeChanged = qtcore.pyqtSignal('PyQt_PyObject')

    def __init__(self, parent, *args, **kwargs):
        super(TradeTableWidget, self).__init__(parent=parent, *args, **kwargs)

        self.cellChanged.connect(self.cellChangedCallback)
        self.setTradeList(core.TradeList())  # link to empty tradeList
        self.keys = [*core.CoinValue().value]
        self.header = ['id', 'partner id', 'date', 'type', 'coin', 'amount', 'exchange'] + ['value ' + key for key in
                                                                                            self.keys]
        self.setColumnCount(len(self.header))
        self.setHorizontalHeaderLabels(self.header)

        self.horizontalHeader().setSectionResizeMode(qtwidgets.QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(qtwidgets.QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(True)

        self.setSortingEnabled(True)

    #        self.setEditTriggers(qtwidgets.QAbstractItemView.NoEditTriggers)
    #        self.setSelectionMode(qtwidgets.QAbstractItemView.NoSelection)

    def setTradeList(self, tradeList):
        #        print('4 set trade list of table widget')
        self.cellChanged.disconnect(self.cellChangedCallback)
        self.setSortingEnabled(False)
        self.tradeList = tradeList
        self.setRowCount(len(self.tradeList))
        for rowIndex in range(len(self.tradeList)):
            trade = self.tradeList[rowIndex]
            tradeRow = [trade.tradeID, trade.tradePartnerId, trade.date, trade.tradeType, trade.coin, trade.amount,
                        trade.exchange if trade.exchange else '']
            tradeRow += [trade.value[key] for key in trade.value]
            self.setRow(tradeRow, rowIndex)
            columnNotEditable = [0, 1, 3, 4]
            for column in columnNotEditable:
                self.item(rowIndex, column).setFlags(self.item(rowIndex, column).flags() & ~qt.ItemIsEditable)

        # set Columns not editable
        #        columnNotEditable = [0,1,3,4]
        #        for column in columnNotEditable:
        #            self.setColumnFlag(column, qt.ItemIsEditable, False)
        self.setSortingEnabled(True)
        self.cellChanged.connect(self.cellChangedCallback)

    #        print('5 table widget refreshed')

    def setColumnFlag(self, column, flag, enable):
        if enable:  # enable flag
            for row in range(self.rowCount()):
                self.item(row, column).setFlags(self.item(row, column).flags() | flag)
        else:  # disable flag
            for row in range(self.rowCount()):
                self.item(row, column).setFlags(self.item(row, column).flags() & ~flag)

    def setRow(self, row, rowIndex):
        # check size of row
        if len(row) == self.columnCount():
            for columnIndex in range(len(row)):
                self.setItem(rowIndex, columnIndex, qtwidgets.QTableWidgetItem(str(row[columnIndex])))

    def getTradeListItemByIndex(self, row, column):
        # ['id', 'partner id', 'date', 'type', 'coin', 'amount', 'exchange'] + ['value ' + key for key in self.keys]
        trade = self.tradeList.getTradeById(self.item(row, 0).text())
        firstValueIndex = 7
        if column == 0:
            return trade.tradeID
        elif column == 1:
            return trade.tradePartnerId
        elif column == 2:
            return trade.date
        elif column == 3:
            return trade.tradeType
        elif column == 4:
            return trade.coin
        elif column == 5:
            return trade.amount
        elif column == 6:
            return trade.exchange
        elif column >= firstValueIndex:
            return trade.value[self.keys[column - firstValueIndex]]

    def setTradeListItemByIndex(self, row, column):
        # ['id', 'partner id', 'date', 'type', 'coin', 'amount', 'exchange'] + ['value ' + key for key in self.keys]
        text = self.item(row, column).text()
        trade = self.tradeList.getTradeById(self.item(row, 0).text())
        firstValueIndex = 7
        try:
            if column == 0:
                trade.tradeID = text
            elif column == 1:
                trade.tradePartnerId = text
            elif column == 2:
                timestamp = converter.convertDate(text)
                if timestamp:
                    trade.date = timestamp
                else:
                    return
            elif column == 3:
                trade.tradeType = text
            elif column == 4:
                trade.coin = text
            elif column == 5:
                trade.amount = float(text)
            elif column == 6:
                trade.exchange = text
            elif column >= firstValueIndex:
                trade.value[self.keys[column - firstValueIndex]] = float(text)
            self.tradeChanged.emit(trade)
        except Exception as ex:
            print('error in TradeTableWidget: ' + str(ex))

    @qtcore.pyqtSlot(int, int)
    def cellChangedCallback(self, row, column):
        item = self.item(row, column)
        #        itemListOld = self.getTradeListItemByIndex(row, column)
        self.setTradeListItemByIndex(row, column)
        #        itemListNew = self.getTradeListItemByIndex(row, column)
        self.cellChanged.disconnect(self.cellChangedCallback)
        item.setText(str(self.getTradeListItemByIndex(row, column)))
        self.cellChanged.connect(self.cellChangedCallback)
        pass


# %% Trade table view
class QTradeTableView(qtwidgets.QTableView):
    def __init__(self, parent, *args, **kwargs):
        super(QTradeTableView, self).__init__(parent=parent, *args, **kwargs)

        self.setModel(QTradeTableModel())
        self.horizontalHeader().setSectionResizeMode(qtwidgets.QHeaderView.Stretch)
        # self.verticalHeader().setSectionResizeMode(qtwidgets.QHeaderView.ResizeToContents)
        self.verticalHeader().setSectionResizeMode(qtwidgets.QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(25)
        self.setItemDelegate(QTradeTableDelegate())

        self.setSortingEnabled(True)


    def filterColumns(self, text, col):
        print('filter trades: ' + str(col) + '; ' + text)

    def clearFilter(self):
        for filterBox in self.filterBoxes:
            filterBox.clear()


# #%% Trade table model
# class QTradeItemModel(qtcore.QAbstractItemModel):
#     def __init__(self, *args, **kwargs):
#         super(QTradeItemModel, self).__init__(*args, **kwargs)


# trade list
class QTradeContainer(qtcore.QAbstractTableModel, core.TradeList):
    tradesAdded = qtcore.pyqtSignal()
    #    tradeChanged = qtcore.pyqtSignal('PyQt_PyObject')
    pricesUpdated = qtcore.pyqtSignal()

    def __init__(self, dataPath=None, *args, **kwargs):
        super(QTradeContainer, self).__init__(*args, **kwargs)

        # buffer for restoring deleted trades
        self.deletedTradesStack = []
        self.deletedIndexesStack = []
        self.deletedNumberStack = []
        self.dataPath = dataPath

    def restoreTrades(self):
        if self.dataPath:
            # try to restore data from previous session
            try:
                # newTradeList = core.TradeList()
                # newTradeList.fromCsv(os.path.join(self.dataPath, 'Trades.csv'))
                # self.addTrades(newTradeList)
                content = importer.loadTradesFromFile(os.path.join(self.dataPath, 'Trades.csv'))
                if not content.empty:
                    tradeListTemp, feeListTemp, match, skippedRows = importer.convertTradesSingle(
                        models.IMPORT_MODEL_LIST, content, os.path.join(self.dataPath, 'Trades.csv'))
                    # check import
                    if match:
                        self.mergeTradeList(tradeListTemp)
                        self.mergeTradeList(feeListTemp)
                        importedRows = len(tradeListTemp.trades) + len(feeListTemp.trades)
                        localLogger.info('imported trades: ' + str(importedRows)
                                         + '; skipped trades: ' + str(skippedRows))
            except Exception as ex:
                localLogger.warning('error parsing trades: ' + str(ex))
        self.updatePrices()

    def saveTrades(self):
        if self.dataPath:
            try:
                self.toCsv(os.path.join(self.dataPath, 'Trades.csv'))
            except Exception as ex:
                print('error in QTradeContainer: ' + str(ex))

    def addTrades(self, newTrades):
        if not (newTrades.isEmpty()):
            # merge Trades
            self.mergeTradeList(newTrades)
            # save the trades as csv
            self.saveTrades()
            # trigger price update
            self.updatePrices()
            # emit trades added
            self.tradesAdded.emit()


    def insertTrades(self, rows, trades):
        for row, trade in zip(rows, trades):
            self.beginInsertRows(row, 1)
            self.trades.insert(row, trade)
            self.endInsertRows()
        return True

    def removeTrades(self, rows):
        self.deletedNumberStack.append(len(rows))
        for row in rows:
            self.deletedTrades.append(self.trades[row])
            self.deletedIndexes.append(row)
            self.beginRemoveRows(row, 1)
            del self.trades[row]
            self.endRemoveRows()
        return True

    def undoRemoveTrades(self):
        for num in range(self.deletedNumberStack.pop()):
            ind = self.deletedIndexesStack.pop[-1]
            trade = self.deletedTradesStack.pop[-1]
            self.beginInsertRows(ind, 1)
            self.trades.insert(ind, trade)
            self.endInsertRows()
        return True

    # update historical prices every time new trades are added
    def updatePrices(self):
        localLogger.info('loading historical prices, can take some time (depending on api limitations)')
        self.updateTradePriceThread = threads.UpdateTradePriceThread(self)
        self.updateTradePriceThread.tradePricesUpdated.connect(self.pricesUpdatedCallback)
        self.updateTradePriceThread.start()

    def pricesUpdatedCallback(self):
        localLogger.info('historical prices loaded')
        self.saveTrades()
        self.pricesUpdated.emit()


# %% Trade table model
# class QTradeTableModel(qtcore.QAbstractTableModel):
class QTradeTableModel(QTradeContainer):
    def __init__(self, *args, **kwargs):
        super(QTradeTableModel, self).__init__(*args, **kwargs)

        # link empty tradeList
        self.keys = [*core.CoinValue().value]
        self.header = ['id', 'partner id', 'date', 'type', 'coin', 'amount', 'exchange'] + ['value ' + key for key in
                                                                                            self.keys]
        self.headerLen = len(self.header)
        self.tradesLen = len(self.trades)
        self.showPrices(True)
        self.firstValueColumn = 7
        self.columnNotEditable = [0, 1, 3, 4]

    def rowCount(self, parent):
        return self.tradesLen

    def columnCount(self, parent):
        return self.headerLen

    def data(self, index, role):
        if role == qt.DisplayRole:
            # ['id', 'partner id', 'date', 'type', 'coin', 'amount', 'exchange'] + ['value' + key for key in self.keys]
            if index.column() == 0:  # return id
                return self.trades[index.row()].tradeID
            if index.column() == 1:  # return partner id
                return self.trades[index.row()].tradePartnerId
            if index.column() == 2:  # return date
                return str(self.trades[index.row()].date)
            if index.column() == 3:  # return type
                return self.trades[index.row()].tradeType
            if index.column() == 4:  # return coin
                return self.trades[index.row()].coin
            if index.column() == 5:  # return amount
                return str(self.trades[index.row()].amount)
            if index.column() == 6:  # return exchange
                return self.trades[index.row()].exchange
            if index.column() >= self.firstValueColumn:  # return value
                key = self.keys[index.column() - self.firstValueColumn]
                return str(self.trades[index.row()].value[key])

        return qtcore.QVariant()

    def headerData(self, section, orientation, role):
        if role == qt.DisplayRole:
            if orientation == qt.Horizontal:
                return self.header[section]
            elif orientation == qt.Vertical:
                return section
        return qtcore.QVariant()

    def setData(self, index, value, role):
        def returnAfterChange():
            self.dataChanged.emit(index, index)
            self.saveTrades()
            return True

        if role == qt.EditRole:
            try:
                #                seperatePrint(['setData', str(index.row()), str(index.column()), str(value), self.trades[index.row()].toString()], '; ')
                # ['id', 'partner id', 'date', 'type', 'coin', 'amount', 'exchange'] + ['value' + key for key in self.keys]
                if index.column() == 0:  # return id
                    self.trades[index.row()].tradeID = value
                    returnAfterChange()
                if index.column() == 1:  # return partner id
                    self.trades[index.row()].tradePartnerId = value
                    returnAfterChange()
                if index.column() == 2:  # return date
                    date = converter.convertDate(value)
                    if date:
                        self.trades[index.row()].date = converter.convertDate(value)
                        returnAfterChange()
                    else:
                        raise ValueError('trade date can not be converted')
                if index.column() == 3:  # return type
                    self.trades[index.row()].tradeType = value
                    returnAfterChange()
                if index.column() == 4:  # return coin
                    self.trades[index.row()].coin = value
                    returnAfterChange()
                if index.column() == 5:  # return amount
                    self.trades[index.row()].amount = float(value)
                    returnAfterChange()
                if index.column() == 6:  # return exchange
                    self.trades[index.row()].exchange = value
                    returnAfterChange()
                if index.column() >= self.firstValueColumn:  # return value
                    key = self.keys[index.column() - self.firstValueColumn]
                    self.trades[index.row()].value[key] = float(value)
                    returnAfterChange()
            except:
                return False
        return True

    def flags(self, index):
        if index.column() in self.columnNotEditable:  # not editable
            return qt.ItemIsSelectable | qt.ItemIsEnabled
        else:  # editable
            return qt.ItemIsSelectable | qt.ItemIsEditable | qt.ItemIsEnabled

    def showPrices(self, showPrices=True):
        self.pricesShowen = showPrices
        if showPrices:
            self.header = ['id', 'partner id', 'date', 'type', 'coin', 'amount', 'exchange'] + ['value ' + key for key
                                                                                                in self.keys]
            self.headerLen = len(self.header)
        else:
            self.header = ['id', 'partner id', 'date', 'type', 'coin', 'amount', 'exchange']
            self.headerLen = len(self.header)

    def setExchange(self, exchange):
        self.beginResetModel()
        for trade in self.trades:
            trade.exchange = exchange
        self.endResetModel()
        # RowStartIndex = self.index(0, 6)
        # RowEndIndex = self.index(len(self.trades), 6)
        # self.dataChanged.emit(RowStartIndex, RowEndIndex)
        # for row in range(0, len(self.trades)):
        #     index = self.index(row, 6)
        #     self.dataChanged.emit(index, index)
            # self.setData(index, exchange, qt.EditRole)

    def copyFromTradeList(self, tradeList):
        self.beginResetModel()
        self.trades = tradeList.trades
        self.tradesLen = len(self.trades)
        self.endResetModel()

    def clearTrades(self):
        self.beginResetModel()
        self.tradesLen = 0
        self.trades = []
        self.endResetModel()

    # reimplement base funcs
    def addTrades(self, trades):
        self.beginResetModel()
        super(QTradeTableModel, self).addTrades(trades)
        self.tradesLen = len(self.trades)
        self.endResetModel()

    def mergeTradeList(self, tradeList):
        self.beginResetModel()
        super(QTradeTableModel, self).mergeTradeList(tradeList)
        self.tradesLen = len(self.trades)
        self.endResetModel()

    def insertRows(self, position, rows, parent):
        for row in rows:
            self.insertTrades(position + row, core.Trade())
        return True

    def removeRows(self, position, rows, parent):
        for row in range(position+rows):
            self.removeTrades(self, row)
        return True

    def pricesUpdatedCallback(self):
        if self.pricesShowen:
            RowStartIndex = self.index(0, self.firstValueColumn)
            RowEndIndex = self.index(len(self.trades), len(self.header) - 1)
            self.dataChanged.emit(RowStartIndex, RowEndIndex)
            super(QTradeTableModel, self).pricesUpdatedCallback()


# %% Trade table delegates
# class QCoinBalanceDelegate(qtwidgets.QStyledItemDelegate):
class QTradeTableDelegate(qtwidgets.QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(QTradeTableDelegate, self).__init__(*args, **kwargs)

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
        return super(QTradeTableDelegate, self).sizeHint(option, index)


def seperatePrint(elements, seperator):
    printString = ''
    for element in elements:
        printString += element + seperator
    print(printString)
