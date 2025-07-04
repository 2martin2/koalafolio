# -*- coding: utf-8 -*-
"""
Created on Sun Dec 16 19:09:51 2018

@author: Martin
"""

from PyQt5.QtGui import QBrush, QColor, QPainterPath
from PyQt5.QtWidgets import QApplication, QCheckBox, QHBoxLayout, QHeaderView, QSpinBox, QStyledItemDelegate, QTextEdit, QVBoxLayout, QWidget
from PyQt5.QtCore import QAbstractItemModel, QEvent, QModelIndex, QRect, QSize, QVariant, Qt, pyqtSignal
import koalafolio.gui.widgets.Qcontrols as controls
import koalafolio.gui.widgets.FilterableTable as fTable
import koalafolio.gui.widgets.ScrollableTable as sTable
import koalafolio.gui.widgets.QCharts as charts
import koalafolio.PcpCore.core as core
import koalafolio.gui.helper.QSettings as settings
import koalafolio.gui.helper.QStyle as style
import datetime
import koalafolio.gui.helper.QLogger as logger
import os
import configparser

localLogger = logger.globalLogger

# %% portfolio table view
class QPortfolioTableView(sTable.QScrollableTreeView):
    def __init__(self, parent, *args, **kwargs):
        super(QPortfolioTableView, self).__init__(parent=parent, *args, **kwargs)

        self.setItemDelegate(QCoinTableDelegate())
        # self.setRootIsDecorated(False)

        self.setSortingEnabled(True)
        # self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.setSelectionMode(QAbstractItemView.NoSelection)

        self.visibleEditorIndex = []
        self.collapsed.connect(self.collapsedCallback)
        self.expanded.connect(self.expandedCallback)

        self.horizontalHeader().sectionResized.connect(lambda index, oldSize, newSize: self.sectionSizeChanged(index, oldSize, newSize))

    def sectionSizeChanged(self, index, oldSize, newSize):
        sourceModel = self.model().sourceModel()
        if index >= sourceModel.firstValueColumn:
            self.updateValueColumnCount(oldSize, newSize)

    def updateValueColumnCount(self, oldSize, newSize, forceUpdate=False):
        sourceModel = self.model().sourceModel()
        if forceUpdate:
            if newSize >= 220:
                sourceModel.changeValueColumnWidth(3)
            if (newSize >= 150 and newSize < 220):
                sourceModel.changeValueColumnWidth(2)
            if newSize < 150:
                sourceModel.changeValueColumnWidth(1)
        else:
            if oldSize < 220 and newSize >= 220:
                sourceModel.changeValueColumnWidth(3)
            if (oldSize < 150 or oldSize >= 220) and (newSize >= 150 and newSize < 220):
                sourceModel.changeValueColumnWidth(2)
            if oldSize >= 150 and newSize < 150:
                sourceModel.changeValueColumnWidth(1)

    def initView(self):
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.setColumnWidth(1, 160)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
        self.setColumnWidth(2, 100)
        # self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.verticalHeader().setVisible(False)
        valueSectionSize = self.horizontalHeader().sectionSize(self.model().sourceModel().firstValueColumn)
        self.updateValueColumnCount(valueSectionSize, valueSectionSize, forceUpdate=True)

    def reset(self):
        super(QPortfolioTableView, self).reset()
        self.initView()

    def setModel(self, model):
        super(QPortfolioTableView, self).setModel(model)
        self.initView()

    def horizontalHeader(self):
        return self.header()

    def collapsedCallback(self, index):
        child = self.model().index(0, 0, index)
        child2 = self.model().index(0, 1, index)
        self.closePersistentEditor(child)
        self.closePersistentEditor(child2)

    def expandedCallback(self, index):
        rows = self.model().rowCount(index)
        columns = self.model().columnCount(index)
        for row in range(rows):
            for column in range(columns):
                child = self.model().index(row, column, index)
                self.openPersistentEditor(child)

    def drawRow(self, painter, options, index):
        painter.save()
        myCol = style.myStyle.getQColor('BACKGROUND_BITDARK')
        myBrush = QBrush(myCol)
        mypen = painter.pen()
        mypen.setBrush(myBrush)
        painter.setPen(mypen)
        rect = options.rect
        # draw upper horz line
        painter.drawLine(rect.x(), rect.y(), rect.x() + rect.width(), rect.y())
        # draw lower horz line
        painter.drawLine(rect.x(), rect.y() + rect.height(), rect.x() + rect.width(), rect.y() + rect.height())
        # restore painter
        super(QPortfolioTableView, self).drawRow(painter, options, index)

    def visualRect(self, index: QModelIndex) -> QRect:
        rect = super(QPortfolioTableView, self).visualRect(index)
        if index.parent().isValid():  # child level
            if index.column() == 0:  # properties
                sectionStart = self.header().logicalIndex(0)
                sectionEnd = self.header().logicalIndex(2)
                left = self.header().sectionViewportPosition(sectionStart)
                right = self.header().sectionViewportPosition(sectionEnd) + self.header().sectionSize(sectionEnd)
                indent = 1 * self.indentation()
                left += indent
                # update visual rect
                rect.setX(int(left + 1))
                rect.setY(int(rect.y() + 1))
                rect.setWidth(right - left - 2)
                rect.setHeight(rect.height() - 2)

            if index.column() == 3:  # chart
                sectionStart = self.header().logicalIndex(3)
                sectionEnd = self.header().logicalIndex(self.header().count() - 1)
                left = self.header().sectionViewportPosition(sectionStart)
                right = self.header().sectionViewportPosition(sectionEnd) + self.header().sectionSize(sectionEnd)
                # update visual rect
                rect.setX(int(left + 1))
                rect.setY(int(rect.y() + 1))
                rect.setWidth(right - left - 2)
                rect.setHeight(rect.height() - 2)
        return rect


# %% portfolio coin container
class QCoinContainer(QAbstractItemModel, core.CoinList):
    coinAdded = pyqtSignal([list])
    # use bulk event to load prices for several coins at once (faster)
    triggerApiUpdateForCoins = pyqtSignal([list])
    triggerPriceUpdateForCoins = pyqtSignal([list])

    def __init__(self, dataPath=None, *args, **kwargs):
        super(QCoinContainer, self).__init__(*args, **kwargs)

        self.dataPath = dataPath
        self.coinDatabase = QCoinInfoDatabase(path=dataPath)
        # self.coinAdded.connect(self.saveCoins)
        self.newCoins = []


    def loadApiDataForNewCoins(self):
        localLogger.info("loadCoinData, new Coins: " + str(len(self.newCoins)))  # + ", " + str(self.newCoins))
        while self.newCoins:
            coins = self.newCoins[-100:]
            self.newCoins = self.newCoins[:-100]
            # trigger data update for up to 100 coins to prevent api errors
            self.triggerApiUpdateForCoins.emit(coins)

    def loadPriceForAllCoins(self):
        coinList = self.getCoinNames()
        # devide coins list into packets of 1000 to prevent api errors
        while coinList:
            coins = coinList[-100:]
            coinList = coinList[:-100]
            # trigger price update for up to 100 coins
            self.triggerPriceUpdateForCoins.emit(coins)

    def setPath(self, path):
        self.dataPath = path
        self.coinDatabase.setPath(path)

    def restoreCoins(self):
        if self.dataPath:
            # try to restore data from previous session
            coins = self.coinDatabase.getCoins()
            for coin in coins:
                if not self.hasMember(coin):
                    self.addCoin(coin)
                    for wallet in self.coinDatabase.getCoinWallets(coin):
                        self.getCoinByName(coin).addWallet(wallet)
            self.coinDatabase.updateCoinInfo(self)
        self.loadApiDataForNewCoins()

    def saveCoins(self):
        if self.dataPath:
            if os.path.isfile(os.path.join(self.dataPath, 'Coins.csv')):
                if os.path.isfile(os.path.join(self.dataPath, 'Coins.csv.bak')):
                    try:  # delete old backup
                        os.remove(os.path.join(self.dataPath, 'Coins.csv.bak'))
                    except Exception as ex:
                        localLogger.warning('error deleting coin info backup in QCoinContainer: ' + str(ex))
                try:  # create backup
                    os.rename(os.path.join(self.dataPath, 'Coins.csv'),
                              os.path.join(self.dataPath, 'Coins.csv.bak'))
                except Exception as ex:
                    localLogger.warning('error creating coin info backup in QCoinContainer: ' + str(ex))
            self.coinDatabase.setCoinInfo(self)

    def setWalletProperties(self, parentrow, childrow, notes, taxYearLimitEnabled, taxYearLimit):
        self.coins[parentrow].wallets[childrow].notes = notes
        self.coins[parentrow].wallets[childrow].taxYearLimitEnabled = taxYearLimitEnabled
        self.coins[parentrow].wallets[childrow].taxYearLimit = taxYearLimit
        self.saveCoins()


# %% portfolio table model
class QPortfolioTableModel(QCoinContainer):
    triggerViewReset = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(QPortfolioTableModel, self).__init__(*args, **kwargs)

        # init keys and header
        self.valueCols = 3
        self.firstValueColumn = 3
        self.parents = []
        self.initDisplayCurrencies()

    def initDisplayCurrencies(self):
        self.keys = [*core.CoinValue().value]
        self.setColumnHeader(self.valueCols)

    def rowCount(self, parent : QModelIndex):
        if parent.isValid():
            if not parent.parent().isValid():  # first child level
                return len(self.coins[parent.row()].wallets)
            else:
                return 0  # only one child level
        else:  # top level
            return len(self.coins)

    def columnCount(self, parent : QModelIndex):
        if parent.isValid():
            if not parent.parent().isValid():  # first child level
                return 4
            else:
                return 0  # only one child level
        else:  # top level
            return len(self.header)

    def parent(self, index):
        try:
            return self.parents[index.internalId()]
        except IndexError:
            return QModelIndex()

    def index(self, row : int, column : int, parent : QModelIndex):
        # save parent
        if parent in self.parents:
            parentId = self.parents.index(parent)
        else:
            self.parents.append(parent)
            parentId = len(self.parents)-1
        if not parent.isValid():  # top level
            return self.createIndex(row, column, parentId)
        if parent.isValid() and not parent.parent().isValid():  # first child level
            return self.createIndex(row, column, parentId)
        # only one child level
        return QModelIndex()

    def data(self, index, role=Qt.DisplayRole):
        if index.parent().isValid():  # child level
            if role == Qt.DisplayRole:
                if index.column() == 0:  # wallet properties
                    wallet = self.coins[index.parent().row()].wallets[index.row()]
                    return QWalletPropertiesData(walletname=wallet.getWalletName(),
                                                 notes=wallet.notes,
                                                 taxLimitEnabled=wallet.taxYearLimitEnabled,
                                                 taxLimitYears=wallet.taxYearLimit)
                if index.column() == 3:  # wallet chart
                    return self.coins[index.parent().row()].wallets[index.row()]
        else:  # top level
            if role == Qt.DisplayRole:
                if index.column() == 0:  # coin row
                    return self.coins[index.row()].coinname  # return coinname
                if index.column() == 1:  # balance row
                    return self.coins[index.row()]  # return CoinBalance
                if index.column() == 2:  # profit row
                    return self.coins[index.row()].getTotalProfit()  # return profit
                if index.column() >= self.firstValueColumn:  # return CoinBalance and key
                    keys = [*core.CoinValue().value]
                    return self.coins[index.row()], keys[index.column() - self.firstValueColumn], self.valueCols
            if role == Qt.DecorationRole:
                if index.column() == 0:
                    coinIcon = self.coins[index.row()].coinIcon
                    if coinIcon:
                        return coinIcon
                    else:
                        return QVariant()
        return QVariant()

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.header[section]
            elif orientation == Qt.Vertical:
                return section
        if role == Qt.ToolTipRole:
            if orientation == Qt.Horizontal:
                if section >= 3:  # value Header
                    return self.valueHeaderToolTip
        return QVariant()

    def setColumnHeader(self, cols):
        if cols == 3:
            self.valueHeaderToolTip = 'invest value\t\tcurrent value\t\tperformance\n' + \
                                        'invest price\t\tcurrent price\t\tchange/24h'
            self.header = ['coin', 'balance', 'realized ' + settings.mySettings.reportCurrency()] + \
                          ['performance ' + key for key in self.keys]
        elif cols == 2:
            self.valueHeaderToolTip = 'current value\t\tperformance\n' + \
                                      'current price\t\tchange/24h'
            self.header = ['coin', 'balance', 'realized ' + settings.mySettings.reportCurrency()] + \
                          ['performance ' + key for key in self.keys]
        else:
            self.valueHeaderToolTip = 'current price\nchange/24h'
            self.header = ['coin', 'balance', 'realized ' + settings.mySettings.reportCurrency()] + \
                          ['price ' + key for key in self.keys]

    def changeValueColumnWidth(self, cols):
        self.valueCols = cols
        self.setColumnHeader(cols)
        self.headerDataChanged.emit(Qt.Horizontal, 0, len(self.header) - 1)
        RowStartIndex = self.index(0, self.firstValueColumn, QModelIndex())
        RowEndIndex = self.index(len(self.coins)-1, len(self.header) - 1, QModelIndex())
        self.dataChanged.emit(RowStartIndex, RowEndIndex)

    def flags(self, index):
        if index.parent().isValid():  # child level
            return Qt.ItemIsEditable | Qt.ItemIsEnabled
        # top level
        return Qt.ItemIsEnabled

    def setData(self, index: QModelIndex, value, role: int):
        if role == Qt.EditRole:
            if index.parent().isValid():  # child level
                if index.column() == 0:  # properties
                    self.setWalletProperties(index.parent().row(), index.row(), value.notes, value.taxLimitEnabled,
                                             value.taxLimitYears)
        return True

    def histPricesChanged(self, coins):
        super(QPortfolioTableModel, self).histPricesChanged(coins)
        self.pricesUpdated()
        # update all DelegateItems of the updated coins
        for coinname in coins:
            row = self.getCoinIndexByName(coinname)
            parent = self.index(row, 0, QModelIndex())
            ChildStartIndex = self.index(0, 3, parent)
            ChildEndIndex = self.index(self.rowCount(parent)-1, 3, parent)
            self.dataChanged.emit(ChildStartIndex, ChildEndIndex)

    def histPriceUpdateFinished(self):
        super(QPortfolioTableModel, self).histPriceUpdateFinished()
        self.pricesUpdated()

    def pricesUpdated(self):
        # update all rows
        RowStartIndex = self.index(0, 2, QModelIndex())
        RowEndIndex = self.index(len(self.coins)-1, len(self.header) - 1, QModelIndex())
        self.dataChanged.emit(RowStartIndex, RowEndIndex)

    def setPrices(self, prices, coins):
        missingCoins = []
        for coin in coins:
            if coin not in prices:
                missingCoins.append(coin)
        localLogger.info("prices returned from Api: " + str(len(prices)) + ", no price returned for: " + str(missingCoins))
        super(QPortfolioTableModel, self).setPrices(prices, coins)
        self.pricesUpdated()

    def setPriceChartData(self, priceChartData):
        super(QPortfolioTableModel, self).setPriceChartData(priceChartData)

    # emit dataChanged when trade is updated
    def tradeChanged(self, trade):
        coin = super(QPortfolioTableModel, self).tradeChanged(trade)
        if coin:
            row = self.coins.index(coin)
            RowStartIndex = self.index(row, 0, QModelIndex())
            RowEndIndex = self.index(row, len(self.header) - 1, QModelIndex())
            self.dataChanged.emit(RowStartIndex, RowEndIndex)

    # emit layout changed when coin is added
    def addTrades(self, trades):
        self.beginResetModel()
        super(QPortfolioTableModel, self).addTrades(trades)
        self.endResetModel()
        self.loadApiDataForNewCoins()
        self.saveCoins()

    def triggerPriceUpdate(self):
        self.loadPriceForAllCoins()

    def addCoin(self, coinname):
        newCoin = super(QPortfolioTableModel, self).addCoin(coinname)
        # coin update will be done for all coins at once since it is much faster
        # self.coinAdded.emit([newCoin.coinname])
        self.newCoins.append(newCoin.coinname)
        return newCoin

    def setIcons(self, icons, coins):
        localLogger.info("icons returned: " + str(len(icons)))
        missingCoins = []
        for coin in coins:
            if coin not in icons:
                missingCoins.append(coin)
        for coin in icons:
            try:
                self.getCoinByName(coin).coinIcon = icons[coin]
            except KeyError:
                pass
        RowStartIndex = self.index(0, 0, QModelIndex())
        RowEndIndex = self.index(len(self.coins) - 1, 0, QModelIndex())
        self.dataChanged.emit(RowStartIndex, RowEndIndex)

    def deleteTrades(self, trades):
        self.beginResetModel()
        super(QPortfolioTableModel, self).deleteTrades(trades)
        self.endResetModel()

    def clearCoins(self):
        self.beginResetModel()
        self.coins = []
        self.parents = []
        self.endResetModel()

    def updateDisplayCurrencies(self, keys):
        self.initDisplayCurrencies()
        self.clearCoins()
        self.restoreCoins()
        self.triggerViewReset.emit()

    def taxYearWalletChanged(self):
        # update all DelegateItems
        for row in range(self.rowCount(QModelIndex())):
            parent = self.index(row, 0, QModelIndex())
            ChildStartIndex = self.index(0, 0, parent)
            ChildEndIndex = self.index(self.rowCount(parent) - 1, 3, parent)
            self.dataChanged.emit(ChildStartIndex, ChildEndIndex)


class QTableSortingModel(fTable.SortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        super(QTableSortingModel, self).__init__(*args, **kwargs)

        self.useRegex = False

    def lessThan(self, index1, index2):
        column = index1.column()
        if not index1.parent().isValid():  # top level
            if column == 2:
                profit1 = index1.data()[settings.mySettings.reportCurrency()]
                profit2 = index2.data()[settings.mySettings.reportCurrency()]
                return profit1 < profit2
            if column >= self.sourceModel().firstValueColumn:
                coinBalance1, key1, cols1 = index1.data()
                coinBalance2, key2, cols2 = index2.data()
                if cols1 >= 2:
                    return coinBalance1.getCurrentValue()[key1] < coinBalance2.getCurrentValue()[key2]
                else:
                    return coinBalance1.getChange24h(key1) < coinBalance2.getChange24h(key2)
            return index1.data() < index2.data()
        else:  # child level
            if column == 0:  # properties
                # sort by walletname
                return str(index1.data().walletname) < str(index2.data().walletname)
            if column == 3:  # chart
                # sort by walletname inverted
                return str(index1.data().getWalletName()) >= str(index2.data().getWalletName())
            else:
                return str(index1.data()) < str(index2.data())

    def filterAcceptsRow(self, source_row, source_parent):
        # get coinbalance from column 3 to filter rows
        index = self.sourceModel().index(source_row, 3, source_parent)
        if source_parent.isValid():  # child level
            parent_row = source_parent.row()
            parentIndex = self.sourceModel().index(parent_row, 3, QModelIndex())
        filterAcceptsRow = super(QTableSortingModel, self).filterAcceptsRow(source_row, source_parent)
        if filterAcceptsRow:
            if settings.mySettings.getGuiSetting('hidelowbalancecoins'):
                if source_parent.isValid():  # child level
                    # check if parent is filtered
                    data, cur, rows = self.sourceModel().data(parentIndex)
                    if data.balance <= 0:
                        return False
                    # parent is visible, check wallet
                    data = self.sourceModel().data(index)
                else:  # top level
                    data, cur, rows = self.sourceModel().data(index)
                if data.balance <= 0:
                    return False
            if settings.mySettings.getGuiSetting('hidelowvaluecoins'):
                if source_parent.isValid():  # child level
                    # check if parent is filtered
                    data, cur, rows = self.sourceModel().data(parentIndex)
                    if data.getCurrentValue()[settings.mySettings.reportCurrency()] \
                            <= settings.mySettings.getGuiSetting('lowvaluefilterlimit(reportcurrency)'):
                        return False
                    # parent is visible, check wallet
                    data = self.sourceModel().data(index)
                else:  # top level
                    data, cur, rows = self.sourceModel().data(index)
                if data.getCurrentValue()[settings.mySettings.reportCurrency()] \
                        <= settings.mySettings.getGuiSetting('lowvaluefilterlimit(reportcurrency)'):
                    return False
        return filterAcceptsRow

# %% portfolio table delegate
# class QCoinBalanceDelegate(QStyledItemDelegate):
class QCoinTableDelegate(QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(QCoinTableDelegate, self).__init__(*args, **kwargs)

        self.marginV = 4  # vertical margin
        self.marginH = 15  # horizontal margin
        self.lastCols = 0

    def paint(self, painter, option, index):
        cellStartX = option.rect.x() + self.marginH
        cellStartY = option.rect.y() + self.marginV
        cellWidth = option.rect.width() - 2 * self.marginH
        cellHeight = option.rect.height() - 2 * self.marginV
        cellStopX = cellStartX + cellWidth
        cellStopY = cellStartY + cellHeight

        # if not in child level and in column 0 or 1 or 3 or 4 draw right grid line
        if not (index.parent().isValid() and (index.column() == 0 or
                                              index.column() == 1 or
                                              index.column() == 3 or
                                              index.column() == 4)):
            painter.save()
            myCol = style.myStyle.getQColor('BACKGROUND_BITDARK')
            myBrush = QBrush(myCol)
            mypen = painter.pen()
            mypen.setBrush(myBrush)
            painter.setPen(mypen)
            rect = option.rect
            # draw left line
            # painter.drawLine(rect.x(), rect.y(), rect.x(), rect.y() + rect.height())
            # draw right line
            painter.drawLine(rect.x() + rect.width(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height())
            painter.restore()

        contentRect = QRect(cellStartX, cellStartY, cellWidth, cellHeight)
        painter.save()
        if not index.parent().isValid():  # top level
            if index.column() == 0:  # coin
                super(QCoinTableDelegate, self).paint(painter, option, index)
            elif index.column() == 1:  # balance
                coinBalance = index.data(Qt.DisplayRole)
                # settings
                taxFreeLimitEnabled = False
                taxFreeLimitYears = 100
                if settings.mySettings.getTaxSetting('taxfreelimit'):  # global tax limit enabled
                    if settings.mySettings.getTaxSetting('usewallettaxfreelimityears'):  # use wallet tax limit
                        for wallet in coinBalance.wallets:
                            if wallet.taxYearLimitEnabled:
                                taxFreeLimitEnabled = True
                                if taxFreeLimitYears > wallet.taxYearLimit:
                                    taxFreeLimitYears = wallet.taxYearLimit
                    else:  # use global tax limit
                        taxFreeLimitEnabled = True
                        taxFreeLimitYears = settings.mySettings.getTaxSetting('taxfreelimityears')
                balance = controls.floatToString(coinBalance.balance, 5)
                defaultFont = painter.font()
                # paint balance text
                newFont = painter.font()
                newFont.setPixelSize(15)
                painter.setFont(newFont)
                myCol = style.myStyle.getQColor('TEXT_NORMAL')
                myBrush = QBrush(myCol)
                mypen = painter.pen()
                mypen.setBrush(myBrush)
                painter.setPen(mypen)
                painter.drawText(contentRect, Qt.AlignHCenter | Qt.AlignTop, balance)
                painter.setFont(defaultFont)

                if taxFreeLimitEnabled:  # draw tax free buys

                    taxFreeLabel = '>' + str(taxFreeLimitYears) + 'y'
                    buyAmountVal = coinBalance.getBuyAmountLeftTaxFree()
                    buyAmount = controls.floatToString(buyAmountVal, 4)
                    if buyAmountVal > 0:
                        # paint buy that can be sold tax free
                        buyColor = QColor(*settings.mySettings.getColor('POSITIV'))
                        buyBrush = QBrush(buyColor)
                        buyPen = painter.pen()
                        buyPen.setBrush(buyBrush)
                        painter.setPen(buyPen)
                        painter.drawText(contentRect, Qt.AlignLeft | Qt.AlignBottom, buyAmount)
                        painter.drawText(contentRect, Qt.AlignLeft | Qt.AlignTop, taxFreeLabel)
                else:  # draw buy amount and sell amount
                    buyAmount = controls.floatToString(coinBalance.getBuyAmount(), 4)
                    sellAmount = controls.floatToString(coinBalance.getSellAmount(), 4)

                    # paint buy
                    buyColor = QColor(*settings.mySettings.getColor('POSITIV'))
                    buyBrush = QBrush(buyColor)
                    buyPen = painter.pen()
                    buyPen.setBrush(buyBrush)
                    painter.setPen(buyPen)
                    painter.drawText(contentRect, Qt.AlignLeft | Qt.AlignBottom, buyAmount)

                    # paint sell
                    sellColor = QColor(*settings.mySettings.getColor('NEGATIV'))
                    sellBrush = QBrush(sellColor)
                    sellPen = painter.pen()
                    sellPen.setBrush(sellBrush)
                    painter.setPen(sellPen)
                    painter.drawText(contentRect, Qt.AlignRight | Qt.AlignBottom, sellAmount)

            elif index.column() == 2:  # realized
                profit = index.data(Qt.DisplayRole)
                key = settings.mySettings.reportCurrency()
                # for key in profit:
                # draw profit
                if profit[key] >= 0:
                    drawColor = QColor(*settings.mySettings.getColor('POSITIV'))
                else:
                    drawColor = QColor(*settings.mySettings.getColor('NEGATIV'))
                pen = painter.pen()
                pen.setBrush(QBrush(drawColor))
                painter.setPen(pen)
                newFont = painter.font()
                newFont.setPixelSize(14)
                painter.setFont(newFont)
                profitString = controls.floatToString(profit[key], 4)
                painter.drawText(contentRect, Qt.AlignHCenter | Qt.AlignVCenter, profitString)

            elif index.column() >= index.model().sourceModel().firstValueColumn:  # performance
                try:  # catch key error if currency is not in database. Could happen during currency switch
                    coinBalance, key, cols = index.data(Qt.DisplayRole)
                    boughtValue = coinBalance.initialValue[key]
                    boughtPrice = coinBalance.getInitialPrice()[key]
                    currentValue = coinBalance.getCurrentValue()[key]
                    currentPrice = coinBalance.getCurrentPrice()[key]
                    boughtValueStr = (controls.floatToString(boughtValue, 4))
                    boughtPriceStr = (controls.floatToString(boughtPrice, 4) + '/p')
                    currentValueStr = (controls.floatToString(currentValue, 4))
                    currentPriceStr = (controls.floatToString(currentPrice, 4) + '/p')
                    if boughtPrice == 0:
                        gain = 0
                    else:
                        gain = (currentPrice / boughtPrice - 1) * 100
                    gainStr = ("%.2f%%" % (gain))
                    gainDay = coinBalance.getChange24h(key)
                    gainDayStr = ("%.2f%%/24h" % (gainDay))


                    positivColor = style.myStyle.getQColor('POSITIV')
                    negativColor = style.myStyle.getQColor('NEGATIV')
                    neutralColor = style.myStyle.getQColor('TEXT_NORMAL')

                    def drawText(alignHorz, alignVert, fontSize, color, text):
                        newFont = painter.font()
                        newFont.setPixelSize(fontSize)
                        painter.setFont(newFont)
                        pen = painter.pen()
                        pen.setColor(color)
                        painter.setPen(pen)
                        painter.drawText(contentRect, alignHorz | alignVert, text)

                    if cols == 3:  # draw all
                        drawText(Qt.AlignLeft, Qt.AlignTop, 14, neutralColor, boughtValueStr)
                        drawText(Qt.AlignLeft, Qt.AlignBottom, 12, neutralColor, boughtPriceStr)
                        if gain > 0:
                            drawText(Qt.AlignHCenter, Qt.AlignTop, 14, positivColor, currentValueStr)
                            drawText(Qt.AlignHCenter, Qt.AlignBottom, 12, positivColor, currentPriceStr)
                            drawText(Qt.AlignRight, Qt.AlignTop, 14, positivColor, gainStr)
                        elif gain < 0:
                            drawText(Qt.AlignHCenter, Qt.AlignTop, 14, negativColor, currentValueStr)
                            drawText(Qt.AlignHCenter, Qt.AlignBottom, 12, negativColor, currentPriceStr)
                            drawText(Qt.AlignRight, Qt.AlignTop, 14, negativColor, gainStr)
                        else:
                            drawText(Qt.AlignHCenter, Qt.AlignTop, 14, neutralColor, currentValueStr)
                            drawText(Qt.AlignHCenter, Qt.AlignBottom, 12, neutralColor, currentPriceStr)
                            drawText(Qt.AlignRight, Qt.AlignTop, 14, neutralColor, gainStr)
                        if gainDay >= 0:
                            drawText(Qt.AlignRight, Qt.AlignBottom, 12, positivColor, gainDayStr)
                        else:
                            drawText(Qt.AlignRight, Qt.AlignBottom, 12, negativColor, gainDayStr)
                    elif cols == 2:  # skip current value and price
                        if gain > 0:
                            drawText(Qt.AlignLeft, Qt.AlignTop, 14, positivColor, currentValueStr)
                            drawText(Qt.AlignLeft, Qt.AlignBottom, 12, positivColor, currentPriceStr)
                            drawText(Qt.AlignRight, Qt.AlignTop, 14, positivColor, gainStr)
                        elif gain < 0:
                            drawText(Qt.AlignLeft, Qt.AlignTop, 14, negativColor, currentValueStr)
                            drawText(Qt.AlignLeft, Qt.AlignBottom, 12, negativColor, currentPriceStr)
                            drawText(Qt.AlignRight, Qt.AlignTop, 14, negativColor, gainStr)
                        else:
                            drawText(Qt.AlignLeft, Qt.AlignTop, 14, neutralColor, currentValueStr)
                            drawText(Qt.AlignLeft, Qt.AlignBottom, 12, neutralColor, currentPriceStr)
                            drawText(Qt.AlignRight, Qt.AlignTop, 14, neutralColor, gainStr)
                        if gainDay >= 0:
                            drawText(Qt.AlignRight, Qt.AlignBottom, 12, positivColor, gainDayStr)
                        else:
                            drawText(Qt.AlignRight, Qt.AlignBottom, 12, negativColor, gainDayStr)
                    else:  # draw value and daygain
                        if gainDay >= 0:
                            drawText(Qt.AlignHCenter, Qt.AlignTop, 14, positivColor, currentPriceStr)
                            drawText(Qt.AlignHCenter, Qt.AlignBottom, 12, positivColor, gainDayStr)
                        else:
                            drawText(Qt.AlignHCenter, Qt.AlignTop, 14, negativColor, currentPriceStr)
                            drawText(Qt.AlignHCenter, Qt.AlignBottom, 12, negativColor, gainDayStr)
                except KeyError as ex:
                    localLogger.warning("currency is missing in coindata: " + str(ex))
        else:  # child level
            super(QCoinTableDelegate, self).paint(painter, option, index)
        painter.restore()

    def createEditor(self, parent, option, index):
        if index.parent().isValid():  # child level
            if index.column() == 0:  # properties
                if int(index.flags()) & Qt.ItemIsEditable:
                    propertiesWidget = QWalletPropertiesWidget(parent)
                    # self.updateEditorGeometry(propertiesWidget, option, index)
                    propertiesWidget.dataChanged.connect(self.commitData)
                    return propertiesWidget
            if index.column() == 3:  # chart
                timelinechart = charts.BuyTimelineChartCont(parent)
                return timelinechart
        return None

    def setEditorData(self, editor, index):
        if index.parent().isValid():  # child level
            if index.column() == 0:  # properties
                editor.setData(index.data())
                return
            if index.column() == 3:  # chart
                # clear data before adding new changes
                editor.clearData()
                data = index.data()
                # get settings
                taxfreelimityears = 0
                taxfreelimitEnabled = False
                if settings.mySettings.getTaxSetting('taxfreelimit'):  # global tax limit enabled
                    if settings.mySettings.getTaxSetting('usewallettaxfreelimityears'):  # use wallet tax limit
                        if data.taxYearLimitEnabled:  # wallet tax limit enabled
                            taxfreelimityears = data.taxYearLimit
                            taxfreelimitEnabled = True
                    else:  # use global tax limit
                        taxfreelimityears = settings.mySettings.getTaxSetting('taxfreelimityears')
                        taxfreelimitEnabled = True
                coinchartdatatype = settings.mySettings.getGuiSetting("coinchartdatatype")
                editor.setTitle("Wallet: " + data.walletname)
                # draw buys left
                if coinchartdatatype == 'buys':
                    dates = []
                    vals = []
                    oldSum = 0
                    # draw buy prices
                    priceDates = []
                    prices = []
                    # buys left
                    for trade in data.tradeMatcher.buysLeft:
                        date = datetime.datetime.combine(trade.date, datetime.time(0, 0, 0, 0))
                        # buys left
                        dates.append(date)
                        vals.append(oldSum)
                        dates.append(date)
                        vals.append(oldSum + trade.amount)
                        oldSum = vals[-1]
                        # prices
                        priceDates.append(date)
                        prices.append(trade.getPrice()[settings.mySettings.reportCurrency()])
                else:  # coinchartdatatype == 'balance':
                    # balance
                    tradesSorted = data.tradeMatcher.trades
                    # tradesSorted.sort(key=lambda x: x.date, reverse=False)
                    dates = [datetime.datetime.combine(tradesSorted[0].date, datetime.time(0, 0, 0, 0))]
                    vals = [0]
                    oldSum = 0
                    priceDates = []
                    prices = []
                    for trade in tradesSorted:
                        date = datetime.datetime.combine(trade.date, datetime.time(0, 0, 0, 0))
                        # balance
                        dates.append(date)
                        vals.append(oldSum)
                        dates.append(date)
                        vals.append(oldSum + trade.amount)
                        oldSum = vals[-1]
                        # prices
                        priceDates.append(date)
                        prices.append(trade.getPrice()[settings.mySettings.reportCurrency()])
                if dates:
                    # buys left
                    dates.append(datetime.datetime.now())
                    vals.append(vals[-1])
                    # prices
                    if not data.priceChartData: # if not price chart data available add at least current value
                        priceDates.append(datetime.datetime.now())
                        prices.append(data.getCurrentPrice()[settings.mySettings.reportCurrency()])
                    # draw chart data
                    if coinchartdatatype == 'buys':
                        editor.addData(dates, vals, style.myStyle.getQColor('PRIMARY_MIDLIGHT'), "buys", lineWidth=3)
                    else:  # coinchartdatatype == 'balance':
                        editor.addData(dates, vals, style.myStyle.getQColor('PRIMARY_MIDLIGHT'), "balance", lineWidth=3)
                    # draw taxlimit
                    if taxfreelimitEnabled:
                        limitDate = datetime.datetime.now().replace(year=datetime.datetime.now().year -
                                                                         taxfreelimityears)
                        firstDate = datetime.datetime.combine(data.tradeMatcher.buysLeft[0].date, datetime.time(0, 0, 0, 0))
                        limitDates = [limitDate, limitDate]
                        limitAmount = data.getBuyAmountLeftTaxFree()
                        limitVals = [limitAmount, 0]
                        editor.addData(limitDates, limitVals, style.myStyle.getQColor('POSITIV'), "taxfree",
                                       lineWidth=3, updateAxis=False)
                    editor.addData(priceDates, prices, style.myStyle.getQColor('SECONDARY'),
                                   "buyPrice " + settings.mySettings.reportCurrency(), lineWidth=3,
                                   chartType="scatter", axis='price')
                    if data.priceChartData:
                        dates, prices = map(list, zip(*data.priceChartData))
                        editor.addData(dates, prices, style.myStyle.getQColor('SECONDARY_MIDLIGHT'),
                                       "price " + settings.mySettings.reportCurrency(), lineWidth=1,
                                       chartType="line", axis='price')
                return

    # def updateEditorGeometry(self, editor, option, index):
    #     debugrow = index.row()
    #     debugcol = index.column()
    #     debugrect = option.rect
    #     debugParent = editor.parent()
    #     debugSize = self.sizeHint(option, index)
    #     if index.parent().isValid():  # child level
    #         if index.column() == 0:  # properties
    #             editor.setGeometry(option.rect)
    #             return
    #         if index.column() == 3:  # chart
    #             editor.setGeometry(option.rect)
    #             return
    #     else:
    #         raise TypeError

    def setModelData(self, editor, model, index):
        if index.parent().isValid():  # child level
            if index.column() == 0:  # propertiesWidget
                model.setData(index, editor.getData(), Qt.EditRole)

    def sizeHint(self, option, index):
        if index.parent().isValid():  # child level
            childLevelHight = 200
            if index.column() == 0:  # properties
                return QSize(350, childLevelHight)
            if index.column() == 1 or index.column() == 2:  # properties
                return QSize(0, childLevelHight)
            elif index.column() == 3:  # chart
                size = super(QCoinTableDelegate, self).sizeHint(option, index)
                return QSize(size.width(), childLevelHight)
        else:  # top level
            topLevelHight = 40
            if index.column() == 0:  # coin
                return QSize(50, topLevelHight)
            elif index.column() == 1:  # balance
                return QSize(100, topLevelHight)
            elif index.column() >= 2:  # realized
                return QSize(200, topLevelHight)
        return QSize()


class QWalletPropertiesWidget(QWidget):
    dataChanged = pyqtSignal([QWidget])
    def __init__(self, parent):
        super(QWalletPropertiesWidget, self).__init__(parent=parent)

        self.walletname = ''

        self.setFocusPolicy(Qt.StrongFocus)

        # notes
        self.notesTextedit = QTextEdit(self)
        self.notesTextedit.setPlaceholderText('notes')
        self.notesTextedit.installEventFilter(self)

        self.optionsLayout = QHBoxLayout()

        # tax limit
        self.timeLimitBox = QCheckBox("tax year limit", self)
        self.timeLimitBox.installEventFilter(self)
        self.timeLimitEdit = QSpinBox(self)
        self.timeLimitEdit.installEventFilter(self)
        self.timeLimitEdit.setValue(1)
        self.timeLimitEdit.setMinimum(0)
        self.timeLimitBox.setCheckState(Qt.Checked)
        self.timeLimitBox.setTristate(False)

        self.optionsLayout.addWidget(self.timeLimitBox)
        self.optionsLayout.addWidget(self.timeLimitEdit)
        self.optionsLayout.addStretch()

        self.vertLayout = QVBoxLayout(self)
        self.vertLayout.addWidget(self.notesTextedit)
        self.vertLayout.addLayout(self.optionsLayout)

        self.timeLimitBox.stateChanged.connect(self.timeLimitCheckBoxChanged)
        self.timeLimitCheckBoxChanged()

    def setData(self, data):
        self.walletname = data.walletname
        self.notesTextedit.setText(data.notes)
        if settings.mySettings.getTaxSetting('usewallettaxfreelimityears'):
            self.timeLimitBox.setEnabled(True)
            self.timeLimitEdit.setEnabled(True)
            self.timeLimitBox.setCheckState(data.taxLimitEnabled)
            self.timeLimitBox.setTristate(False)
            self.timeLimitEdit.setValue(data.taxLimitYears)
        else:
            self.timeLimitBox.setEnabled(False)
            self.timeLimitEdit.setEnabled(False)
            self.timeLimitBox.setCheckState(settings.mySettings.getTaxSetting('taxfreelimit'))
            self.timeLimitBox.setTristate(False)
            self.timeLimitEdit.setValue(settings.mySettings.getTaxSetting('taxfreelimityears'))

    def getData(self):
        return QWalletPropertiesData(walletname=self.walletname,
                                     notes=self.notesTextedit.toPlainText(),
                                     taxLimitEnabled=self.timeLimitBox.isChecked(),
                                     taxLimitYears=self.timeLimitEdit.value())

    def timeLimitCheckBoxChanged(self):
        if settings.mySettings.getTaxSetting('usewallettaxfreelimityears'):
            if self.timeLimitBox.isChecked():
                self.timeLimitEdit.setEnabled(True)
            else:
                self.timeLimitEdit.setEnabled(False)

    def eventFilter(self, object: 'QObject', event: 'QEvent') -> bool:
        if object is None:
            return False
        if event.type() == QEvent.FocusOut:
            w = QApplication.focusWidget()
            while w:  # don't worry about focus changes internally in the editor
                if w == object:
                    return False
                w = w.parentWidget()
            self.dataChanged.emit(self)

        return False

    def sizeHint(self):
        return QSize(0, 0)


class QWalletPropertiesData:
    def __init__(self, walletname, notes, taxLimitEnabled, taxLimitYears):
        self.walletname = walletname
        self.notes = notes
        self.taxLimitEnabled = taxLimitEnabled
        self.taxLimitYears = taxLimitYears


class QArrowPainterPath(QPainterPath):
    def __init__(self, startX, startY, width, height, *args, **kwargs):
        super(QArrowPainterPath, self).__init__(*args, **kwargs)

        self.startX = startX
        self.startY = startY

        #        self.height = 6 * size
        #        self.width = 9 * size
        self.height = height
        self.width = width

        self.stopX = self.startX + self.width
        self.stopY = self.startY + self.height

        self.moveTo(startX, startY)
        self.lineTo(startX + self.width / 9 * 5, startY)
        self.lineTo(startX + self.width / 9 * 5, startY - self.height / 6 * 2)
        self.lineTo(startX + self.width, startY + self.height / 6 * 2)
        self.lineTo(startX + self.width / 9 * 5, startY + self.height)
        self.lineTo(startX + self.width / 9 * 5, startY + self.height / 6 * 4)
        self.lineTo(startX, startY + self.height / 6 * 4)
        self.lineTo(startX, startY)
        self.closeSubpath()


# coin info file
class QCoinInfoDatabase(configparser.ConfigParser):
    def __init__(self, path=None, *args, **kwargs):
        super(QCoinInfoDatabase, self).__init__(*args, **kwargs)

        self.filePath = None
        if path:
            self.setPath(path)


    def setPath(self, path):
        self.filePath = os.path.join(path, 'coininfo.txt')
        # init settings
        if not os.path.isfile(self.filePath):
            self.saveCoins()
        else:
            self.readCoins()
            self.saveCoins()
        return self

    def saveCoins(self):
        try:
            with open(self.filePath, 'w') as coinfile:
                self.write(coinfile)
            logger.globalLogger.info('coins saved')
            return True
        except Exception as ex:
            logger.globalLogger.error('error in saveCoins: ' + str(ex))
            return False

    def readCoins(self):
        try:
            self.read(self.filePath)
            logger.globalLogger.info('coin info loaded')
        except Exception as ex:
            logger.globalLogger.error('coin info can not be loaded: ' + str(ex))

    def setCoinInfo(self, coinList):
        for coinwallets in coinList:
            coinname = coinwallets.coinname
            if not coinname in self:
                self[coinname] = {}
            for coin in coinwallets:
                if coin.walletname == "DEFAULT":
                    notename = "notes"
                    taxYearEnabledName = "taxyearenabled"
                    taxYearLimitName = "taxyearlimit"
                else:
                    notename = "notes" + "_" + coin.walletname
                    taxYearEnabledName = "taxyearenabled" + "_" + coin.walletname
                    taxYearLimitName = "taxyearlimit" + "_" + coin.walletname
                self[coinname][notename] = coin.notes
                self[coinname][taxYearEnabledName] = str(coin.taxYearLimitEnabled)
                self[coinname][taxYearLimitName] = str(coin.taxYearLimit)
        self.saveCoins()

    def updateCoinInfo(self, coinList):
        for coinwallets in coinList:
            coinname = coinwallets.coinname
            for coin in coinwallets:
                if coin.walletname == "DEFAULT":
                    notename = "notes"
                    taxYearEnabledName = "taxyearenabled"
                    taxYearLimitName = "taxyearlimit"
                else:
                    notename = "notes" + "_" + coin.walletname
                    taxYearEnabledName = "taxyearenabled" + "_" + coin.walletname
                    taxYearLimitName = "taxyearlimit" + "_" + coin.walletname
                try:
                    coin.notes = self[coinname][notename]
                    coin.taxYearLimitEnabled = self.getboolean(coinname, taxYearEnabledName)
                    coin.taxYearLimit = self.getint(coinname, taxYearLimitName)
                except (KeyError, configparser.NoOptionError):
                    pass

    def getCoins(self):
        coins = []
        for key in self:
            if key != 'DEFAULT':
                coins.append(key)
        return coins

    def getCoinWallets(self, coin):
        wallets = []
        try:
            for key in self[coin]:
                if '_' in key:
                    wallets.append(key.split('_')[1])
                else:
                    wallets.append("")
        except KeyError:
            wallets.append("")  # add default wallet if coin not present
        return wallets
