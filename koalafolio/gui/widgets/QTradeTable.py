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

from PyQt5.QtWidgets import QHeaderView, QLineEdit, QStyledItemDelegate
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, QVariant, Qt, pyqtSignal
import os
import koalafolio.PcpCore.core as core
import koalafolio.Import.Converter as converter
import koalafolio.gui.helper.QLogger as logger
import koalafolio.Import.TradeImporter as importer
import koalafolio.Import.Models as models
import koalafolio.gui.helper.QStyle as style
import koalafolio.gui.widgets.FilterableTable as ftable

localLogger = logger.globalLogger

# %% Trade table view
class QTradeTableView(ftable.FilterableTableView):
    def __init__(self, parent, *args, **kwargs):
        super(QTradeTableView, self).__init__(parent=parent, *args, **kwargs)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(30)
        self.setItemDelegate(QTradeTableDelegate())

        self.setSortingEnabled(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.deleteSelectedTrades()
        else:
            super(QTradeTableView, self).keyPressEvent(event)

    def deleteSelectedTrades(self):
        if self.selectionModel().hasSelection():
            inds = self.selectionModel().selectedIndexes()
            rows = []
            for ind in inds:
                sourceInd = self.model().mapToSource(ind)
                if not sourceInd.row() in rows:
                    rows.append(sourceInd.row())
            self.model().sourceModel().deleteTrades(rows)

    def addWalletToSelectedTrades(self, wallet):
        if self.selectionModel().hasSelection():
            inds = self.selectionModel().selectedIndexes()
            rows = []
            for ind in inds:
                sourceInd = self.model().mapToSource(ind)
                if not sourceInd.row() in rows:
                    rows.append(sourceInd.row())
            self.model().sourceModel().setWalletOfTrades(rows, wallet)
        else:
            self.model().sourceModel().setWallet(wallet)

    def addExchangeToSelectedTrades(self, wallet):
        if self.selectionModel().hasSelection():
            inds = self.selectionModel().selectedIndexes()
            rows = []
            for ind in inds:
                sourceInd = self.model().mapToSource(ind)
                if not sourceInd.row() in rows:
                    rows.append(sourceInd.row())
            self.model().sourceModel().setExchangeOfTrades(rows, wallet)
        else:
            self.model().sourceModel().setExchange(wallet)

    def deleteSimilarTrades(self):
        self.model().sourceModel().deleteSimilarTrades()



# trade list
class QTradeContainer(QAbstractTableModel, core.TradeList):
    tradesAdded = pyqtSignal('PyQt_PyObject')
    tradesRemoved = pyqtSignal('PyQt_PyObject')
    triggerHistPriceUpdate = pyqtSignal('PyQt_PyObject')
    #    tradeChanged = pyqtSignal('PyQt_PyObject')
    histPricesUpdated = pyqtSignal(list)
    histPriceUpdateFinished = pyqtSignal()

    def __init__(self, dataPath=None, *args, **kwargs):
        super(QTradeContainer, self).__init__(*args, **kwargs)

        # buffer for restoring deleted trades
        self.deletedTradesStack = []
        self.deletedIndexesStack = []
        self.addedTradesStack = []
        self.changedNumberStack = []
        self.dataPath = dataPath

        self.tradesAdded.connect(lambda tradeList: self.updateHistPrices(tradeList))

    def restoreTrades(self):
        if self.dataPath:
            # try to restore data from previous session
            try:
                if os.path.isfile(os.path.join(self.dataPath, 'Trades.csv')):
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
                            self.tradesAdded.emit(self)
            except Exception as ex:
                localLogger.warning('error parsing trades: ' + str(ex))

    def saveTrades(self):
        if self.dataPath:
            if os.path.isfile(os.path.join(self.dataPath, 'Trades.csv')):
                if os.path.isfile(os.path.join(self.dataPath, 'Trades.csv.bak')):
                    try:  # delete old backup
                        os.remove(os.path.join(self.dataPath, 'Trades.csv.bak'))
                    except Exception as ex:
                        localLogger.warning('error deleting trades backup in QTradeContainer: ' + str(ex))
                try:  # create backup
                    os.rename(os.path.join(self.dataPath, 'Trades.csv'),
                              os.path.join(self.dataPath, 'Trades.csv.bak'))
                except Exception as ex:
                    localLogger.warning('error creating trades backup in QTradeContainer: ' + str(ex))
            try:  # save trades
                self.toCsv(os.path.join(self.dataPath, 'Trades.csv'))
                localLogger.info("trades saved")
            except Exception as ex:
                localLogger.error('error saving trades in QTradeContainer: ' + str(ex))

    def addTrades(self, newTrades):
        if not (newTrades.isEmpty()):
            # merge Trades
            addedTrades = self.mergeTradeList(newTrades)
            for trade in addedTrades:
                self.changedNumberStack.append(len(addedTrades))
                self.addedTradesStack.append(trade)
            # save the trades as csv
            self.saveTrades()
            # emit trades added
            self.tradesAdded.emit(addedTrades)

    def insertTrades(self, rows, trades):
        try:
            for index in sorted(range(len(rows)), key=rows.__getitem__):
                row = rows[index]
                trade = trades[index]
                self.beginInsertRows(QModelIndex(), row, row)
                self.trades.insert(row, trade)
                self.endInsertRows()
        except TypeError:
            row = rows
            trade = trades
            self.beginInsertRows(QModelIndex(), row, row)
            self.trades.insert(row, trade)
            self.endInsertRows()
            trades = core.TradeList()
            trades.addTrade(trade)
        # save new trades
        self.saveTrades()
        # emit trades added
        self.tradesAdded.emit(trades)

    def removeTrades(self, tradeList):
        for trade in tradeList:
            row = self.trades.index(trade)
            self.beginRemoveRows(QModelIndex(), row, row)
            self.trades.pop(row)
            self.endRemoveRows()
        # save new trades
        self.saveTrades()
        # emit trades added
        self.tradesRemoved.emit(tradeList)

    def undoRemoveAddTrades(self):
        if self.changedNumberStack:
            num = self.changedNumberStack.pop()
            if num < 0:  # trades have been removed
                tradeList = core.TradeList()
                tradeList.trades = self.deletedTradesStack[num:]
                self.deletedTradesStack = self.deletedTradesStack[0:num]
                rows = self.deletedIndexesStack[num:]
                self.deletedIndexesStack = self.deletedIndexesStack[0:num]
                self.insertTrades(rows, tradeList)
            if num > 0:  # trades have been added
                tradeList = core.TradeList()
                tradeList.trades = self.addedTradesStack[-num:]
                self.addedTradesStack = self.addedTradesStack[0:-num]
                self.removeTrades(tradeList)

    def deleteTrades(self, rows):
        self.beginResetModel()
        rows.sort(reverse=True)
        self.changedNumberStack.append(-len(rows))
        tradeList = core.TradeList()
        for row in rows:
            tradeList.addTrade(self.trades[row])
            self.deletedTradesStack.append(self.trades[row])
            self.deletedIndexesStack.append(row)
        for row in rows:
            self.beginRemoveRows(QModelIndex(), row, row)
            self.trades.pop(row)
            self.endRemoveRows()
        # save new trades
        self.saveTrades()
        # emit trades added
        self.tradesRemoved.emit(tradeList)
        self.endResetModel()
        return True

    def deleteAllTrades(self):
        return self.deleteTrades(list(range(len(self.trades))))

    def updateHistPrices(self, tradeList):
        for trade in tradeList:
            if not trade.valueLoaded:
                localLogger.info('loading historical prices. Can take some time (depending on api limitations)')
                self.triggerHistPriceUpdate.emit(tradeList)
                return

    def setHistPrices(self, prices, tradesLeft=None):
        localLogger.info(str(len(prices)) + " new hist prices recieved")
        updatedCoins = super(QTradeContainer, self).setHistPrices(prices)
        self.histPricesUpdatedCallback(updatedCoins, tradesLeft)

    def histPricesUpdatedCallback(self, updatedCoins, tradesLeft):
        self.saveTrades()
        self.histPricesUpdated.emit(updatedCoins)
        if tradesLeft == 0:
            # check if still Trades missing histValue and have not been tried yet
            for trade in self.trades:
                # do not try more than twice.
                if not trade.valueLoaded and trade.valueLoadingFailedCnt < 2:
                    self.triggerHistPriceUpdate.emit(self)
                    return
            # trigger priceUpdateFinished
            localLogger.info('all historical prices loaded')
            self.histPriceUpdateFinished.emit()
        else:
            localLogger.info('loading historical prices: ' + str(tradesLeft) + ' trades left')


# %% Trade table model
# class QTradeTableModel(QAbstractTableModel):
class QTradeTableModel(QTradeContainer):
    def __init__(self, *args, **kwargs):
        super(QTradeTableModel, self).__init__(*args, **kwargs)

        # link empty tradeList
        self.initDisplayCurrencies()

        #self.tradesLen = len(self.trades)
        self.showPrices(True)
        self.firstValueColumn = 8
        self.enableEditMode(True)

    def enableEditMode(self, enable):
        if enable:
            self.columnNotEditable = [0, 1, 3, 4]
        else:
            self.columnNotEditable = list(range(self.headerLen))

    def initDisplayCurrencies(self):
        self.keys = [*core.CoinValue().value]
        self.header = ['id', 'partner id', 'date', 'type', 'coin', 'amount', 'exchange', 'wallet'] + ['value ' + key for key in
                                                                                            self.keys]
        self.headerLen = len(self.header)

    def rowCount(self, parent):
        return len(self.trades)

    def columnCount(self, parent):
        return self.headerLen

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
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
            if index.column() == 7:  # return wallet
                return self.trades[index.row()].wallet
            if index.column() >= self.firstValueColumn:  # return value
                key = self.keys[index.column() - self.firstValueColumn]
                return str(self.trades[index.row()].value[key])

        return QVariant()

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.header[section]
            elif orientation == Qt.Vertical:
                return section
        return QVariant()

    def setData(self, index, value, role):
        def returnAfterChange():
            self.dataChanged.emit(index, index)
            self.saveTrades()
            return True

        if role == Qt.EditRole:
            try:
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
                if index.column() == 7:  # return wallet
                    self.trades[index.row()].wallet = value
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
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        else:  # editable
            return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled

    def showPrices(self, showPrices=True):
        self.pricesShowen = showPrices
        if showPrices:
            self.header = ['id', 'partner id', 'date', 'type', 'coin', 'amount', 'exchange', 'wallet'] + ['value ' + key for key
                                                                                                in self.keys]
            self.headerLen = len(self.header)
        else:
            self.header = ['id', 'partner id', 'date', 'type', 'coin', 'amount', 'exchange', 'wallet']
            self.headerLen = len(self.header)

    def setExchange(self, exchange):
        self.beginResetModel()
        for trade in self.trades:
            trade.exchange = exchange
        self.endResetModel()

    def setWallet(self, wallet):
        self.beginResetModel()
        for trade in self.trades:
            trade.wallet = wallet
        self.endResetModel()

    def setExchangeOfTrades(self, rows, exchange):
        self.beginResetModel()
        for row in rows:
            self.trades[row].exchange = exchange
        self.endResetModel()

    def setWalletOfTrades(self, rows, wallet):
        self.beginResetModel()
        for row in rows:
            self.trades[row].wallet = wallet
        self.endResetModel()

    def copyFromTradeList(self, tradeList):
        self.beginResetModel()
        self.trades = tradeList.trades
        # self.tradesLen = len(self.trades)
        self.endResetModel()

    def clearTrades(self):
        self.beginResetModel()
        # self.tradesLen = 0
        self.trades = []
        self.endResetModel()

    # reimplement base funcs
    def addTrades(self, trades):
        self.beginResetModel()
        super(QTradeTableModel, self).addTrades(trades)
        # self.tradesLen = len(self.trades)
        self.endResetModel()

    def mergeTradeList(self, tradeList):
        self.beginResetModel()
        addedTrades = super(QTradeTableModel, self).mergeTradeList(tradeList)
        # self.tradesLen = len(self.trades)
        self.endResetModel()
        return addedTrades

    def insertRows(self, position, rows, parent):
        for row in rows:
            self.insertTrades(position + row, core.Trade())
        return True

    def removeRows(self, position, rows, parent):
        for row in range(position+rows):
            self.deleteTrades(row)
        return True

    def histPricesUpdatedCallback(self, updatedCoins, tradesLeft):
        super(QTradeTableModel, self).histPricesUpdatedCallback(updatedCoins, tradesLeft)
        if self.pricesShowen:
            RowStartIndex = self.index(0, self.firstValueColumn)
            RowEndIndex = self.index(len(self.trades) - 1, len(self.header) - 1, QModelIndex())
            self.dataChanged.emit(RowStartIndex, RowEndIndex)

    def updateDisplayCurrencies(self, keys):
        self.initDisplayCurrencies()
        self.clearTrades()
        self.restoreTrades()

    def recalcIds(self):
        super(QTradeTableModel, self).recalcIds()
        self.saveTrades()
        self.updateColumn(0)
        self.updateColumn(1)

    def updateRow(self, row):
        StartIndex = self.index(row, 0)
        EndIndex = self.index(row, len(self.header) - 1)
        self.dataChanged.emit(StartIndex, EndIndex)

    def updateColumn(self, col):
        StartIndex = self.index(0, col)
        EndIndex = self.index(len(self.trades) - 1, col)
        self.dataChanged.emit(StartIndex, EndIndex)



# %% import Trade table model
class QImportTradeTableModel(QTradeTableModel):
    def __init__(self, baseModel, *args, **kwargs):
        super(QImportTradeTableModel, self).__init__(*args, **kwargs)

        self.baseModel = baseModel

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.ForegroundRole:
            if index.row() >= len(self.trades):
                print('error ' + str(index.row()) + ' ' + str(len(self.trades)))
                return QVariant()
            if self.trades[index.row()] in self.baseModel.trades:
                return style.myStyle.getQColor('text_highlighted_midlight'.upper())
            if self.baseModel.checkApproximateEquality(self.trades[index.row()]):
                return style.myStyle.getQColor('NEGATIV')
        return super(QImportTradeTableModel, self).data(index, role)

    def deleteSimilarTrades(self):
        row = 0
        deleteRows = []
        for trade in self.trades:
            if trade in self.baseModel.trades or self.baseModel.checkApproximateEquality(trade):
                deleteRows.append(row)
            row += 1
        self.deleteTrades(deleteRows)



# %% Trade table delegates
# class QCoinBalanceDelegate(QStyledItemDelegate):
class QTradeTableDelegate(QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(QTradeTableDelegate, self).__init__(*args, **kwargs)

    def createEditor(self, parent, option, index):
        if int(index.flags()) & Qt.ItemIsEditable:
            return QLineEdit(parent)
        return None

    def setEditorData(self, editor, index):
        editor.setText(index.data())

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text(), Qt.EditRole)

    def sizeHint(self, option, index):
        return super(QTradeTableDelegate, self).sizeHint(option, index)


def seperatePrint(elements, seperator):
    printString = ''
    for element in elements:
        printString += element + seperator
    print(printString)
