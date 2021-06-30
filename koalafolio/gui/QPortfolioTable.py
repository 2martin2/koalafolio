# -*- coding: utf-8 -*-
"""
Created on Sun Dec 16 19:09:51 2018

@author: Martin
"""

import PyQt5.QtGui as qtgui
import PyQt5.QtWidgets as qtwidgets
import PyQt5.QtCore as qtcore
import koalafolio.gui.Qcontrols as controls
import koalafolio.gui.FilterableTable as fTable
import koalafolio.gui.ScrollableTable as sTable
import koalafolio.gui.QCharts as charts
import koalafolio.PcpCore.core as core
import koalafolio.gui.QSettings as settings
import koalafolio.gui.QStyle as style
import datetime
import koalafolio.gui.QLogger as logger
import os
import configparser

qt = qtcore.Qt
localLogger = logger.globalLogger

# %% portfolio table view
class QPortfolioTableView(sTable.QScrollableTreeView):
    def __init__(self, parent, *args, **kwargs):
        super(QPortfolioTableView, self).__init__(parent=parent, *args, **kwargs)

        self.setItemDelegate(QCoinTableDelegate())
        # self.setRootIsDecorated(False)

        self.setSortingEnabled(True)
        # self.setEditTriggers(qtwidgets.QAbstractItemView.NoEditTriggers)
        # self.setSelectionMode(qtwidgets.QAbstractItemView.NoSelection)

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
        self.horizontalHeader().setSectionResizeMode(qtwidgets.QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, qtwidgets.QHeaderView.Interactive)
        self.horizontalHeader().setSectionResizeMode(1, qtwidgets.QHeaderView.Interactive)
        self.setColumnWidth(1, 160)
        self.horizontalHeader().setSectionResizeMode(2, qtwidgets.QHeaderView.Interactive)
        self.setColumnWidth(2, 100)
        # self.verticalHeader().setSectionResizeMode(qtwidgets.QHeaderView.ResizeToContents)
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
        if index.parent().isValid():
            firstSection = self.header().logicalIndex(0)
            # midSection = self.header().logicalIndex(2)
            lastSection = self.header().logicalIndex(self.header().count() - 1)
            left = self.header().sectionViewportPosition(firstSection)
            # mid = self.header().sectionViewportPosition(midSection) + self.header().sectionSize(midSection)
            right = self.header().sectionViewportPosition(lastSection) + self.header().sectionSize(lastSection)
            indent = 1 * self.indentation()
            left += indent

            options.rect.setX(left)
            options.rect.setWidth(right - left)

            # self.itemDelegate(index).paint(painter, options, index)
        else:
            super(QPortfolioTableView, self).drawRow(painter, options, index)
        painter.save()
        myCol = style.myStyle.getQColor('BACKGROUND_BITDARK')
        myBrush = qtgui.QBrush(myCol)
        mypen = painter.pen()
        mypen.setBrush(myBrush)
        painter.setPen(mypen)
        rect = options.rect
        if index.parent().isValid():  # child level, draw lower line over indent
            # draw lower horz line
            x = rect.x() - self.indentation()
            painter.drawLine(x, rect.y() + rect.height(), rect.x() + rect.width(), rect.y() + rect.height())
            # draw upper horz line
            painter.drawLine(x, rect.y(), rect.x() + rect.width(), rect.y())
            # draw mid line
            mid = rect.width() * 0.3 + 20
            painter.drawLine(mid, rect.y(), mid, rect.y() + rect.height())
        else:
            # draw lower horz line
            painter.drawLine(rect.x(), rect.y() + rect.height(), rect.x() + rect.width(), rect.y() + rect.height())
        painter.restore()

# %% portfolio coin container
class QCoinContainer(qtcore.QAbstractItemModel, core.CoinList):
    coinAdded = qtcore.pyqtSignal([list])
    PriceUpdateRequest = qtcore.pyqtSignal([list])

    def __init__(self, dataPath=None, *args, **kwargs):
        super(QCoinContainer, self).__init__(*args, **kwargs)

        self.dataPath = dataPath
        self.coinDatabase = QCoinInfoDatabase(path=dataPath)
        # self.coinAdded.connect(self.saveCoins)

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
        self.coinAdded.emit(self.getCoinNames())

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

    def setNotes(self, parentrow, childrow, notes):
        self.coins[parentrow].wallets[childrow].notes = notes
        self.saveCoins()

# %% portfolio table model
class QPortfolioTableModel(QCoinContainer):
    triggerViewReset = qtcore.pyqtSignal()

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

    def rowCount(self, parent):
        if parent.isValid():
            if not parent.parent().isValid():  # first child level
                return len(self.coins[parent.row()].wallets)
            else:
                return 0  # only one child level
        else:  # top level
            return len(self.coins)

    def columnCount(self, parent):
        if parent.isValid():
            if not parent.parent().isValid():  # first child level
                return 2
            else:
                return 0  # only one child level
        else:  # top level
            return len(self.header)

    def parent(self, index):
        try:
            return self.parents[index.internalId()]
        except IndexError:
            return qtcore.QModelIndex()

    def index(self, row, column, parent):
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
        return qtcore.QModelIndex()

    def data(self, index, role=qt.DisplayRole):
        if index.parent().isValid():  # child level
            if role == qt.DisplayRole:
                if index.column() == 0:  # coin row
                    return self.coins[index.parent().row()].wallets[index.row()].notes
                if index.column() == 1:
                    return self.coins[index.parent().row()].wallets[index.row()]
        else:  # top level
            if role == qt.DisplayRole:
                if index.column() == 0:  # coin row
                    return self.coins[index.row()].coinname  # return coinname
                if index.column() == 1:  # balance row
                    return self.coins[index.row()]  # return CoinBalance
                if index.column() == 2:  # profit row
                    return self.coins[index.row()].getTotalProfit()  # return profit
                if index.column() >= self.firstValueColumn:  # return CoinBalance and key
                    keys = [*core.CoinValue().value]
                    return self.coins[index.row()], keys[index.column() - self.firstValueColumn], self.valueCols
            if role == qt.DecorationRole:
                if index.column() == 0:
                    coinIcon = self.coins[index.row()].coinIcon
                    if coinIcon:
                        return coinIcon
                    else:
                        return qtcore.QVariant()
        return qtcore.QVariant()

    def headerData(self, section, orientation, role):
        if role == qt.DisplayRole:
            if orientation == qt.Horizontal:
                return self.header[section]
            elif orientation == qt.Vertical:
                return section
        if role == qt.ToolTipRole:
            if orientation == qt.Horizontal:
                if section >= 3:
                    return self.valueHeaderToolTip
        return qtcore.QVariant()

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
        self.headerDataChanged.emit(qt.Horizontal, 0, len(self.header) - 1)
        RowStartIndex = self.index(0, self.firstValueColumn, qtcore.QModelIndex())
        RowEndIndex = self.index(len(self.coins)-1, len(self.header) - 1, qtcore.QModelIndex())
        self.dataChanged.emit(RowStartIndex, RowEndIndex)

    def flags(self, index):
        if index.parent().isValid():  # child level
            return qt.ItemIsEditable | qt.ItemIsEnabled
        # top level
        return qt.ItemIsEnabled

    def setData(self, index, value, role):
        if index.parent().isValid():  # child level
            if role == qt.EditRole:
                self.setNotes(index.parent().row(), index.row(), value)
        return True

    def histPricesChanged(self):
        super(QPortfolioTableModel, self).histPricesChanged()
        self.pricesUpdated()

    def histPriceUpdateFinished(self):
        super(QPortfolioTableModel, self).histPriceUpdateFinished()
        self.pricesUpdated()

    def pricesUpdated(self):
        RowStartIndex = self.index(0, 2, qtcore.QModelIndex())
        RowEndIndex = self.index(len(self.coins)-1, len(self.header) - 1, qtcore.QModelIndex())
        self.dataChanged.emit(RowStartIndex, RowEndIndex)

    def setPrices(self, prices):
        super(QPortfolioTableModel, self).setPrices(prices)
        self.pricesUpdated()

    def setPriceChartData(self, priceChartData):
        super(QPortfolioTableModel, self).setPriceChartData(priceChartData)

    # emit dataChanged when trade is updated
    def tradeChanged(self, trade):
        coin = super(QPortfolioTableModel, self).tradeChanged(trade)
        if coin:
            row = self.coins.index(coin)
            RowStartIndex = self.index(row, 0)
            RowEndIndex = self.index(row, len(self.header) - 1)
            self.dataChanged.emit(RowStartIndex, RowEndIndex)

    # emit layout changed when coin is added
    def addTrades(self, trades):
        self.beginResetModel()
        super(QPortfolioTableModel, self).addTrades(trades)
        self.endResetModel()
        #  load prices and icons of all coins (not necessary but faster)
        # todo: only pass new coins
        self.coinAdded.emit(self.getCoinNames())
        self.saveCoins()

    def triggerPriceUpdate(self):
        self.PriceUpdateRequest.emit(self.getCoinNames())

    def addCoin(self, coinname):
        newCoin = super(QPortfolioTableModel, self).addCoin(coinname)
        # coin update will be done for all coins at once since it is much faster
        # self.coinAdded.emit([newCoin.coinname])
        return newCoin

    def setIcons(self, icons):
        for coin in icons:
            try:
                self.getCoinByName(coin).coinIcon = icons[coin]
            except:
                pass
        RowStartIndex = self.index(0, 0, qtcore.QModelIndex())
        RowEndIndex = self.index(len(self.coins) - 1, 0, qtcore.QModelIndex())
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


class QTableSortingModel(fTable.SortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        super(QTableSortingModel, self).__init__(*args, **kwargs)

        self.useRegex = False

    def lessThan(self, index1, index2):
        if not index1.parent().isValid():  # top level
            column = index1.column()
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
        else:  #child level
            return str(index1.data()) < str(index2.data())

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 1, source_parent)
        parent = self.sourceModel().parent(index)
        if parent.isValid():  # child level
            # always use top level for filter
            source_parent = qtcore.QModelIndex()
            source_row = parent.row()
            index = self.sourceModel().index(source_row, 1, source_parent)
        filterAcceptsRow = super(QTableSortingModel, self).filterAcceptsRow(source_row, source_parent)
        if filterAcceptsRow:
            if settings.mySettings.getGuiSetting('hidelowbalancecoins'):
                data = self.sourceModel().data(index)
                if data.balance <= 0:
                    return False
            if settings.mySettings.getGuiSetting('hidelowvaluecoins'):
                data = self.sourceModel().data(index)
                if data.getCurrentValue()[settings.mySettings.reportCurrency()] <= settings.mySettings.getGuiSetting('lowvaluefilterlimit(reportcurrency)'):
                    return False
        return filterAcceptsRow

# %% portfolio table delegate
# class QCoinBalanceDelegate(qtwidgets.QStyledItemDelegate):
class QCoinTableDelegate(qtwidgets.QStyledItemDelegate):
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

        painter.save()
        myCol = style.myStyle.getQColor('BACKGROUND_BITDARK')
        myBrush = qtgui.QBrush(myCol)
        mypen = painter.pen()
        mypen.setBrush(myBrush)
        painter.setPen(mypen)
        rect = option.rect
        # draw right line
        painter.drawLine(rect.x() + rect.width(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height())
        painter.restore()

        contentRect = qtcore.QRect(cellStartX, cellStartY, cellWidth, cellHeight)
        painter.save()
        if not index.parent().isValid():  # top level
            if index.column() == 0:  # coin
                super(QCoinTableDelegate, self).paint(painter, option, index)
            elif index.column() == 1:  # balance
                coinBalance = index.data(qt.DisplayRole)
                balance = controls.floatToString(coinBalance.balance, 5)
                if settings.mySettings.getTaxSetting('taxfreelimit'):
                    taxFreeLimitYears = settings.mySettings.getTaxSetting('taxfreelimityears')
                    freeBuyYears = '>' + str(taxFreeLimitYears) + 'y'
                    buyAmountVal = coinBalance.getBuyAmountLeftTaxFree(taxFreeLimitYears)
                    buyAmount = controls.floatToString(buyAmountVal, 4)
                else:
                    buyAmount = controls.floatToString(coinBalance.getBuyAmount(), 4)
                    sellAmount = controls.floatToString(coinBalance.getSellAmount(), 4)
                    firstBuyLeftDate = coinBalance.getFirstBuyLeftDate()
                    if firstBuyLeftDate:
                        now = datetime.datetime.now()
                        yearDif = now.year - firstBuyLeftDate.year
                        monthDif = now.month - firstBuyLeftDate.month
                        dayDif = now.day - firstBuyLeftDate.day
                        if monthDif < 0 or (monthDif == 0 and dayDif < 0):
                            yearDif -= 1
                        freeBuyYears = '>' + str(yearDif) + 'y'

                defaultFont = painter.font()
                # paint balance text
                newFont = painter.font()
                newFont.setPixelSize(15)
                painter.setFont(newFont)
                painter.drawText(contentRect, qt.AlignHCenter | qt.AlignTop, balance)
                painter.setFont(defaultFont)

                if settings.mySettings.getTaxSetting('taxfreelimit'):
                    if buyAmountVal > 0:
                        # paint buy that can be sold tax free
                        buyColor = qtgui.QColor(*settings.mySettings.getColor('POSITIV'))
                        buyBrush = qtgui.QBrush(buyColor)
                        buyPen = painter.pen()
                        buyPen.setBrush(buyBrush)
                        painter.setPen(buyPen)
                        painter.drawText(contentRect, qt.AlignLeft | qt.AlignBottom, buyAmount)
                        painter.drawText(contentRect, qt.AlignLeft | qt.AlignTop, freeBuyYears)
                else:
                    # paint buy
                    buyColor = qtgui.QColor(*settings.mySettings.getColor('POSITIV'))
                    buyBrush = qtgui.QBrush(buyColor)
                    buyPen = painter.pen()
                    buyPen.setBrush(buyBrush)
                    painter.setPen(buyPen)
                    painter.drawText(contentRect, qt.AlignLeft | qt.AlignBottom, buyAmount)
                    if firstBuyLeftDate:
                        painter.drawText(contentRect, qt.AlignLeft | qt.AlignTop, freeBuyYears)

                    # paint sell
                    sellColor = qtgui.QColor(*settings.mySettings.getColor('NEGATIV'))
                    sellBrush = qtgui.QBrush(sellColor)
                    sellPen = painter.pen()
                    sellPen.setBrush(sellBrush)
                    painter.setPen(sellPen)
                    painter.drawText(contentRect, qt.AlignRight | qt.AlignBottom, sellAmount)

            elif index.column() == 2:  # realized
                profit = index.data(qt.DisplayRole)
                key = settings.mySettings.reportCurrency()
                # for key in profit:
                # draw profit
                if profit[key] >= 0:
                    drawColor = qtgui.QColor(*settings.mySettings.getColor('POSITIV'))
                else:
                    drawColor = qtgui.QColor(*settings.mySettings.getColor('NEGATIV'))
                pen = painter.pen()
                pen.setBrush(qtgui.QBrush(drawColor))
                painter.setPen(pen)
                defaultFont = painter.font()
                newFont = painter.font()
                newFont.setPixelSize(14)
                painter.setFont(newFont)
                profitString = controls.floatToString(profit[key], 4)
                painter.drawText(contentRect, qt.AlignHCenter | qt.AlignVCenter, profitString)

            elif index.column() >= index.model().sourceModel().firstValueColumn:  # performance
                try:  # catch key error if currency is not in database. Could happen during currency switch
                    coinBalance, key, cols = index.data(qt.DisplayRole)
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
                        drawText(qt.AlignLeft, qt.AlignTop, 14, neutralColor, boughtValueStr)
                        drawText(qt.AlignLeft, qt.AlignBottom, 12, neutralColor, boughtPriceStr)
                        if gain > 0:
                            drawText(qt.AlignHCenter, qt.AlignTop, 14, positivColor, currentValueStr)
                            drawText(qt.AlignHCenter, qt.AlignBottom, 12, positivColor, currentPriceStr)
                            drawText(qt.AlignRight, qt.AlignTop, 14, positivColor, gainStr)
                        elif gain < 0:
                            drawText(qt.AlignHCenter, qt.AlignTop, 14, negativColor, currentValueStr)
                            drawText(qt.AlignHCenter, qt.AlignBottom, 12, negativColor, currentPriceStr)
                            drawText(qt.AlignRight, qt.AlignTop, 14, negativColor, gainStr)
                        else:
                            drawText(qt.AlignHCenter, qt.AlignTop, 14, neutralColor, currentValueStr)
                            drawText(qt.AlignHCenter, qt.AlignBottom, 12, neutralColor, currentPriceStr)
                            drawText(qt.AlignRight, qt.AlignTop, 14, neutralColor, gainStr)
                        if gainDay >= 0:
                            drawText(qt.AlignRight, qt.AlignBottom, 12, positivColor, gainDayStr)
                        else:
                            drawText(qt.AlignRight, qt.AlignBottom, 12, negativColor, gainDayStr)
                    elif cols == 2:  # skip current value and price
                        if gain > 0:
                            drawText(qt.AlignLeft, qt.AlignTop, 14, positivColor, currentValueStr)
                            drawText(qt.AlignLeft, qt.AlignBottom, 12, positivColor, currentPriceStr)
                            drawText(qt.AlignRight, qt.AlignTop, 14, positivColor, gainStr)
                        elif gain < 0:
                            drawText(qt.AlignLeft, qt.AlignTop, 14, negativColor, currentValueStr)
                            drawText(qt.AlignLeft, qt.AlignBottom, 12, negativColor, currentPriceStr)
                            drawText(qt.AlignRight, qt.AlignTop, 14, negativColor, gainStr)
                        else:
                            drawText(qt.AlignLeft, qt.AlignTop, 14, neutralColor, currentValueStr)
                            drawText(qt.AlignLeft, qt.AlignBottom, 12, neutralColor, currentPriceStr)
                            drawText(qt.AlignRight, qt.AlignTop, 14, neutralColor, gainStr)
                        if gainDay >= 0:
                            drawText(qt.AlignRight, qt.AlignBottom, 12, positivColor, gainDayStr)
                        else:
                            drawText(qt.AlignRight, qt.AlignBottom, 12, negativColor, gainDayStr)
                    else:  # draw value and daygain
                        if gainDay >= 0:
                            drawText(qt.AlignHCenter, qt.AlignTop, 14, positivColor, currentPriceStr)
                            drawText(qt.AlignHCenter, qt.AlignBottom, 12, positivColor, gainDayStr)
                        else:
                            drawText(qt.AlignHCenter, qt.AlignTop, 14, negativColor, currentPriceStr)
                            drawText(qt.AlignHCenter, qt.AlignBottom, 12, negativColor, gainDayStr)
                except KeyError as ex:
                    localLogger.warning("currency is missing in coindata: " + str(ex))
        # else:  # child level
        #     if index.column() == 1:  # trade hist chart
        #         # draw chart
        painter.restore()

    def createEditor(self, parent, option, index):
        if index.parent().isValid():  # child level
            if index.column() == 0:
                if int(index.flags()) & qt.ItemIsEditable:
                    textedit = qtwidgets.QTextEdit(parent)
                    textedit.setPlaceholderText('notes')
                    self.updateEditorGeometry(textedit, option, index)
                    return textedit
            if index.column() == 1:
                timelinechart = charts.BuyTimelineChartCont(parent)
                return timelinechart
        return None

    def setEditorData(self, editor, index):
        if index.parent().isValid():  # child level
            if index.column() == 0:
                editor.setText(index.data())
                return
            if index.column() == 1:
                # get settings
                taxfreelimityears = settings.mySettings.getTaxSetting("taxfreelimityears")
                taxfreelimit = settings.mySettings.getTaxSetting("taxfreelimit")
                coinchartdatatype = settings.mySettings.getGuiSetting("coinchartdatatype")
                data = index.data()
                editor.setTitle(data.walletname)
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
                    if taxfreelimit:
                        limitDate = datetime.datetime.now().replace(year=datetime.datetime.now().year -
                                                                         taxfreelimityears)
                        firstDate = datetime.datetime.combine(data.tradeMatcher.buysLeft[0].date, datetime.time(0, 0, 0, 0))
                        limitDates = [limitDate, limitDate]
                        limitAmount = data.getBuyAmountLeftTaxFree(taxfreelimityears)
                        limitVals = [limitAmount, 0]
                        editor.addData(limitDates, limitVals, style.myStyle.getQColor('POSITIV'), "taxfree", lineWidth=3, updateAxis=False)
                    editor.addData(priceDates, prices, style.myStyle.getQColor('SECONDARY'),
                                   "buyPrice " + settings.mySettings.reportCurrency(), lineWidth=3,
                                   chartType="scatter", axis='price')
                    if data.priceChartData:
                        dates, prices = map(list, zip(*data.priceChartData))
                        editor.addData(dates, prices, style.myStyle.getQColor('SECONDARY_MIDLIGHT'),
                                       "price " + settings.mySettings.reportCurrency(), lineWidth=1,
                                       chartType="line", axis='price')
                return

    def updateEditorGeometry(self, editor, option, index):
        if index.parent().isValid():  # child level

            if index.column() == 0:
                size = self.sizeHint(option, index)
                rect = qtcore.QRect(editor.parent().x(), option.rect.y() + 5, editor.parent().width() * 0.3,
                                    size.height() - 10)
                editor.setGeometry(rect)
                return
            if index.column() == 1:
                size = self.sizeHint(option, index)
                rect = qtcore.QRect(editor.parent().x() + editor.parent().width() * 0.3 + 20, option.rect.y() + 5, editor.parent().width() * 0.7 - 20,
                                    size.height() - 10)
                editor.setGeometry(rect)
                return
        else:
            raise TypeError

    def setModelData(self, editor, model, index):
        if index.parent().isValid():
            if index.column() == 0:
                model.setData(index, editor.toPlainText(), qt.EditRole)

    def sizeHint(self, option, index):
        if index.parent().isValid():  # child level
            size = super(QCoinTableDelegate, self).sizeHint(option, index)
            return qtcore.QSize(size.width(), 200)
        else:
            if index.column() == 0:
                return qtcore.QSize(50, 40)
            elif index.column() == 1:
                return qtcore.QSize(100, 40)
            elif index.column() >= 2:
                return qtcore.QSize(200, 40)
        return qtcore.QSize()


class QArrowPainterPath(qtgui.QPainterPath):
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
                if coin.walletname == "default":
                    notename = "notes"
                else:
                    notename = "notes" + "_" + coin.walletname
                self[coinname][notename] = coin.notes
        self.saveCoins()

    def updateCoinInfo(self, coinList):
        for coinwallets in coinList:
            coinname = coinwallets.coinname
            for coin in coinwallets:
                if coin.walletname == "default":
                    notename = "notes"
                else:
                    notename = "notes" + "_" + coin.walletname
                try:
                    coin.notes = self[coinname][notename]
                except KeyError:
                    coin.notes = ""

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
