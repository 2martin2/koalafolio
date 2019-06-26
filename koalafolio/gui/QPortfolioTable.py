# -*- coding: utf-8 -*-
"""
Created on Sun Dec 16 19:09:51 2018

@author: Martin
"""

import PyQt5.QtGui as qtgui
import PyQt5.QtWidgets as qtwidgets
import PyQt5.QtCore as qtcore
import PyQt5.QtChart as qtchart
import koalafolio.gui.Qcontrols as controls
import koalafolio.gui.QCharts as charts
import koalafolio.PcpCore.core as core
import koalafolio.gui.QSettings as settings
import koalafolio.gui.QStyle as style
import colorsys
import koalafolio.gui.QThreads as threads
import datetime
import koalafolio.gui.QLogger as logger
from PIL.ImageQt import ImageQt
import os
import configparser

qt = qtcore.Qt
localLogger = logger.globalLogger

# %% portfolio table view
class QPortfolioTableView(qtwidgets.QTreeView):
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

        self.verticalScrollBar().setSingleStep(1)
        self.verticalScrollBar().setPageStep(1)

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
        child = self.model().index(0, 0, index)
        child2 = self.model().index(0, 1, index)
        self.openPersistentEditor(child)
        self.openPersistentEditor(child2)

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
        if index.parent().isValid():  # draw lower line over indent
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
            self.coinDatabase.updateCoinInfo(self)
        self.coinAdded.emit(self.getCoinNames())

    def saveCoins(self):
        if self.dataPath:
            if os.path.isfile(os.path.join(self.dataPath, 'Coins.csv')):
                if os.path.isfile(os.path.join(self.dataPath, 'Coins.csv.bak')):
                    try:  # delete old backup
                        os.remove(os.path.join(self.dataPath, 'Coins.csv.bak'))
                    except Exception as ex:
                        print('error deleting coin info backup in QCoinContainer: ' + str(ex))
                try:  # create backup
                    os.rename(os.path.join(self.dataPath, 'Coins.csv'),
                              os.path.join(self.dataPath, 'Coins.csv.bak'))
                except Exception as ex:
                    print('error creating coin info backup in QCoinContainer: ' + str(ex))
            self.coinDatabase.setCoinInfo(self)

    def setNotes(self, index, notes):
        self.coins[index].notes = notes
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
                return 1
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
                    return self.coins[index.parent().row()].notes
                if index.column() == 1:
                    return self.coins[index.parent().row()]
        else:  # top level
            if role == qt.DisplayRole:
                if index.column() == 0:  # coin row
                    return self.coins[index.row()].coinname  # return coinname
                if index.column() == 1:  # balance row
                    return self.coins[index.row()]  # return CoinBalance
                if index.column() == 2:  # profit row
                    return self.coins[index.row()].tradeMatcher.getTotalProfit()  # return profit
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
                self.setNotes(index.parent().row(), value)
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


class QTableSortingModel(qtcore.QSortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        super(QTableSortingModel, self).__init__(*args, **kwargs)

        self.sortedRow = 0
        self.sortedDir = 0

    def sort(self, row, order):
        super(QTableSortingModel, self).sort(row, order)
        self.sortedRow = row
        self.sortedDir = order

    def lessThan(self, index1, index2):
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
                    buyAmountVal = coinBalance.tradeMatcher.getBuyAmountLeftTaxFree(taxFreeLimitYears)
                    buyAmount = controls.floatToString(buyAmountVal, 4)
                else:
                    buyAmount = controls.floatToString(coinBalance.tradeMatcher.getBuyAmount(), 4)
                    sellAmount = controls.floatToString(coinBalance.tradeMatcher.getSellAmount(), 4)
                    firstBuyLeftDate = coinBalance.tradeMatcher.getFirstBuyLeftDate()
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

            elif index.column() == 2:
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

            elif index.column() >= index.model().sourceModel().firstValueColumn:
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
        if index.parent().isValid():
            if index.column() == 0:
                editor.setText(index.data())
                return
            if index.column() == 1:
                data = index.data()
                # draw buys left
                dates = []
                vals = []
                oldSum = 0
                # draw buy prices
                priceDates = []
                prices = []
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
                if dates:
                    # buys left
                    dates.append(datetime.datetime.now())
                    vals.append(vals[-1])
                    # prices
                    priceDates.append(datetime.datetime.now())
                    prices.append(data.getCurrentPrice()[settings.mySettings.reportCurrency()])
                    # draw taxlimit
                    limitDate = datetime.datetime.now().replace(year=datetime.datetime.now().year -
                                                                     settings.mySettings.getTaxSetting("taxfreelimityears"))
                    firstDate = datetime.datetime.combine(data.tradeMatcher.buysLeft[0].date, datetime.time(0, 0, 0, 0))
                    limitDates = [limitDate, limitDate]
                    limitAmount = data.tradeMatcher.getBuyAmountLeftTaxFree(settings.mySettings.getTaxSetting("taxfreelimityears"))
                    limitVals = [limitAmount, 0]


                    editor.setData(dates, vals, style.myStyle.getQColor('PRIMARY_MIDLIGHT'), "buys", 3)
                    editor.addData(limitDates, limitVals, style.myStyle.getQColor('POSITIV'), "taxfree", 3)
                    editor.addData(priceDates, prices, style.myStyle.getQColor('SECONDARY_MIDLIGHT'), "price", 3,
                                   chartType="Scatter", newAxis=True)
                return

    def updateEditorGeometry(self, editor, option, index):
        if index.parent().isValid():  # child level

            if index.column() == 0:
                size = self.sizeHint(option, index)
                # print("updateGeom width 0: " + str(size.width()) + "; " + str(option.rect.width()))
                rect = qtcore.QRect(editor.parent().x(), option.rect.y() + 5, editor.parent().width() * 0.3,
                                    size.height() - 10)
                editor.setGeometry(rect)
                return
            if index.column() == 1:
                size = self.sizeHint(option, index)
                # print("updateGeom width 1: " + str(size.width()) + "; " + str(option.rect.width()))
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


# %% portfolio overview
class PortfolioOverview(qtwidgets.QWidget):
    expandTable = qtcore.pyqtSignal()
    collapseTable = qtcore.pyqtSignal()
    filterSoldCoins = qtcore.pyqtSignal()

    def __init__(self, controller, height=200, *args, **kwargs):
        super(PortfolioOverview, self).__init__(*args, **kwargs)

        self.controller = controller
        self.styleHandler = self.controller.styleSheetHandler
        self.height = height
        self.setFixedHeight(self.height)
        self.setContentsMargins(0, 0, 0, 0)
        self.horzLayout = qtwidgets.QHBoxLayout(self)
        self.horzLayout.setContentsMargins(0, 0, 0, 0)

        # profit table
        self.profitTable = qtwidgets.QTableWidget()
        self.profitTable.setSelectionMode(qtwidgets.QAbstractItemView.NoSelection)
        self.profitTable.setColumnCount(4)
        self.profitTable.setHorizontalHeaderLabels(["profit", "tax profit", "fees", "fiat profit"])
        self.profitTable.horizontalHeaderItem(0).setToolTip("profit per year")
        self.profitTable.horizontalHeaderItem(1).setToolTip("profit relevant for tax calculation")
        self.profitTable.horizontalHeaderItem(2).setToolTip("fees per year")
        self.profitTable.horizontalHeaderItem(3).setToolTip("fiat profit per year")
        self.profitTable.horizontalHeader().setVisible(True)
        self.profitTable.setSizeAdjustPolicy(qtwidgets.QAbstractScrollArea.AdjustToContents)

        # tax value chart
        self.currentValueChart = charts.LabeledDonatChart(self.height, self.height, 3,
                                                          'crypto performance')
        self.currentValueChart.setHeadingToolTip('this chart shows\nthe performance of\n' +
                                                 'your portfolio\nrelative to the\ncurrent invest\n' +
                                                 '(profit from crypto\ntrades is reinvested)')
        self.donutSliceInvested = self.currentValueChart.addSlice('invested', 1, -1, False)
        self.donutSlicePerformance = self.currentValueChart.addSlice('performance', 0.5, -1, False)
        # fiat value chart
        self.currentFiatValueChart = charts.LabeledDonatChart(self.height, self.height, 3,
                                                              'fiat performance')
        self.currentFiatValueChart.setHeadingToolTip('this chart shows\nthe performance of\nyour portfolio\n' +
                                                     'relative to the\ninitial fiat invest')
        self.sliceFiatInvested = self.currentFiatValueChart.addSlice('fiat invest', 1, -1, False)
        self.sliceCoinValue = self.currentFiatValueChart.addSlice('coin value', 0.5, -1, False)
        self.sliceFiatReturn = self.currentFiatValueChart.addSlice('fiat return', 0.5, -1, False)

        self.perfChartCont = charts.ChartCont(self)
        self.controller.startRefresh.connect(self.perfChartCont.clearButtonStyle)
        self.controller.endRefresh.connect(self.perfChartCont.setButtonStyle)
        self.perfChartCont.addChart(self.currentValueChart)
        self.perfChartCont.addChart(self.currentFiatValueChart)
        self.perfChartCont.setChartIndex(settings.mySettings.getGuiSetting('performanceChartIndex'))
        self.horzLayout.addWidget(self.perfChartCont)

        # table controls
        self.expandAllButton = qtwidgets.QPushButton("expand", self)
        self.expandAllButton.clicked.connect(self.expandTable)
        self.collapseAllButton = qtwidgets.QPushButton("collapse", self)
        self.collapseAllButton.clicked.connect(self.collapseTable)
        # self.filterSoldCoinsBox = qtwidgets.QCheckBox(self)

        self.controlsLayout = qtwidgets.QHBoxLayout()
        self.controlsLayout.addStretch()
        self.controlsLayout.addWidget(self.expandAllButton)
        self.controlsLayout.addWidget(self.collapseAllButton)
        # self.controlsLayout.addWidget(self.filterSoldCoinsBox)
        self.controlsLayout.addStretch()

        self.centerVertLayout = qtwidgets.QVBoxLayout()
        self.centerVertLayout.addWidget(self.profitTable)
        self.centerVertLayout.addStretch()
        self.centerVertLayout.addLayout(self.controlsLayout)

        self.horzLayout.addStretch()
        self.horzLayout.addLayout(self.centerVertLayout)
        self.horzLayout.addStretch()

        # pie chart
        numLabel = len(settings.mySettings.displayCurrencies())
        self.portfolioChart = charts.LabeledDonatChart(self.height + 30, self.height, numLabel, parent=self)
        self.controller.startRefresh.connect(self.portfolioChart.chartView.clearStyleSheet)
        # self.controller.endRefresh.connect(self.portfolioChart.chartView.setColor)
        self.horzLayout.addWidget(self.portfolioChart)

        self.refresh()

    def refresh(self):
        self.negColor = qtgui.QColor(*settings.mySettings.getColor('NEGATIV'))
        self.posColor = qtgui.QColor(*settings.mySettings.getColor('POSITIV'))
        self.neutrColor = qtgui.QColor(*settings.mySettings.getColor('TEXT_NORMAL'))

    def setModel(self, model):
        self.model = model
        self.model.modelReset.connect(self.coinTableChangedSlot)
        self.model.dataChanged.connect(self.coinTableChangedSlot)
        self.coinTableChangedSlot()

    def coinTableChangedSlot(self):
        # update new values

        # todo: display all displayCurrencies
        taxCoinName = settings.mySettings.reportCurrency()
        numberOfDecimals = 4

        # initialize local vars
        # total invested fiat
        totalInvestFiat = core.CoinValue()
        # total returned fiat
        totalReturnFiat = core.CoinValue()
        # fiat performance
        # fiatPerformance = core.CoinValue()

        # invested value of current holdings
        currentInvestNoFiat = core.CoinValue()
        # current value of current holdings (hypothetical)
        hypotheticalCoinValueNoFiat = core.CoinValue()
        # current performance of current holdings (hypothetical)
        # hypotheticalPerformanceNoFiat = core.CoinValue()

        # realized profit (relevant for tax)
        realizedProfit = core.CoinValue()
        # unrealized profit (would be relevant for tax if realized)
        # unrealizedProfit = core.CoinValue()
        # paid fees
        paidFees = core.CoinValue()

        # testing
        # currentInvestAll = core.CoinValue()
        # hypotheticalValueAll = core.CoinValue()
        # realizedProfitAll = core.CoinValue()
        if self.controller.tradeList.isEmpty():
            startYear = datetime.datetime.now().year
        else:
            startYear = min([trade.date for trade in self.controller.tradeList]).year
        stopYear = datetime.datetime.now().year
        realizedProfitPerYear = {}
        paidFeesPerYear = {}
        realizedProfitPerYearCoinList = {}
        fiatPerYear = {}
        taxProfitPerYear = {}

        for year in range(startYear, stopYear+1):
            realizedProfitPerYear[str(year)] = core.CoinValue()
            paidFeesPerYear[str(year)] = core.CoinValue()
            fiatPerYear[str(year)] = core.CoinValue()
            taxProfitPerYear[str(year)] = core.CoinValue()

        # calculate all needed values
        for coin in self.model:
            if coin.isFiat():  # calculate invested and returned fiat
                for trade in coin.trades:
                    if trade.amount < 0:
                        totalInvestFiat.add(trade.getValue().mult(-1))
                    else:
                        totalReturnFiat.add(trade.getValue())
                    # fiat invest/ return per year
                    for year in range(startYear, stopYear + 1):
                        startDate = datetime.date(year=year, month=1, day=1)
                        endDate = datetime.date(year=year, month=12, day=31)
                        if trade.date.date() >= startDate and trade.date.date() <= endDate:
                            fiatPerYear[str(year)].add(trade.getValue())

            else:  # calculate value of portfolio
                currentInvestNoFiat.add(coin.initialValue)
                hypotheticalCoinValueNoFiat.add(coin.getCurrentValue())
                realizedProfit.add(coin.tradeMatcher.getTotalProfit())
            # calc fees per year
            for trade in coin.trades:
                if trade.tradeType == "fee":
                    paidFees.add(trade.getValue())
                    for year in range(startYear, stopYear + 1):
                        startDate = datetime.date(year=year, month=1, day=1)
                        endDate = datetime.date(year=year, month=12, day=31)
                        if trade.date.date() >= startDate and trade.date.date() <= endDate:
                            paidFeesPerYear[str(year)].add(trade.getValue())

            realizedProfitPerYearCoinList[coin.coinname] = (coin.tradeMatcher.getTimeDeltaProfit(
                    datetime.date(year=2017, month=1, day=1), datetime.date(year=2019, month=12, day=31),
                    taxFreeTimeDelta=settings.mySettings.getTaxSetting('taxfreelimityears'))[taxCoinName])
            for year in range(startYear, stopYear + 1):
                startDate = datetime.date(year=year, month=1, day=1)
                endDate = datetime.date(year=year, month=12, day=31)
                taxProfitPerYear[str(year)].add(coin.tradeMatcher.getTimeDeltaProfit(startDate, endDate,
                    taxFreeTimeDelta=settings.mySettings.getTaxSetting('taxfreelimityears')))
                realizedProfitPerYear[str(year)].add(coin.tradeMatcher.getTimeDeltaProfit(startDate, endDate,
                    taxFreeTimeDelta = -1))
            # fiat and coins
            # currentInvestAll.add(coin.initialValue)
            # hypotheticalValueAll.add(coin.getCurrentValue())
            # realizedProfitAll.add(coin.tradeMatcher.getTotalProfit())

        realizedProfitPerYearCoinListSum = sum([realizedProfitPerYearCoinList[key] for key in realizedProfitPerYearCoinList])
        fiatPerformance = (totalReturnFiat-totalInvestFiat).div(totalInvestFiat).mult(100)
        hypotheticalPerformanceNoFiat = (hypotheticalCoinValueNoFiat.div(currentInvestNoFiat)
                                         - core.CoinValue().setValue(1)).mult(100)
        unrealizedProfit = hypotheticalCoinValueNoFiat - currentInvestNoFiat

        def setLabelColor(label, isPositiv):
            if isPositiv:
                label.setBodyColor(self.posColor.name())
            else:
                label.setBodyColor(self.negColor.name())

        # tax value chart
        self.currentValueChart.chartView.setText(
            [controls.floatToString(currentInvestNoFiat[taxCoinName], numberOfDecimals) + ' ' + taxCoinName,
            controls.floatToString(hypotheticalCoinValueNoFiat[taxCoinName], numberOfDecimals) + ' ' + taxCoinName,
            "%.2f%%" % hypotheticalPerformanceNoFiat[taxCoinName]])

        self.currentValueChart.setLabelToolTip(['current invest', 'current value', 'performance'])

        if unrealizedProfit[taxCoinName] < 0:
            self.donutSliceInvested.setValue(currentInvestNoFiat[taxCoinName]+unrealizedProfit[taxCoinName])
            self.donutSliceInvested.setColor(self.neutrColor)
            self.donutSlicePerformance.setValue(-unrealizedProfit[taxCoinName])
            self.donutSlicePerformance.setColor(self.negColor)
            # self.donutSlicePerformance.setLabelColor(self.negColor)
            self.currentValueChart.chartView.setColor([self.neutrColor, self.negColor, self.negColor])
        else:
            self.donutSliceInvested.setValue(currentInvestNoFiat[taxCoinName])
            self.donutSliceInvested.setColor(self.neutrColor)
            self.donutSlicePerformance.setValue(unrealizedProfit[taxCoinName])
            self.donutSlicePerformance.setColor(self.posColor)
            # self.donutSlicePerformance.setLabelColor(self.posColor)
            self.currentValueChart.chartView.setColor([self.neutrColor, self.posColor, self.posColor])

        # fiat value chart
        self.currentFiatValueChart.chartView.setText(
            [controls.floatToString(totalInvestFiat[taxCoinName], numberOfDecimals) + ' ' + taxCoinName,
             controls.floatToString(hypotheticalCoinValueNoFiat[taxCoinName], numberOfDecimals) + ' ' + taxCoinName,
             controls.floatToString(totalReturnFiat[taxCoinName], numberOfDecimals) + ' ' + taxCoinName], qt.AlignCenter)

        self.currentFiatValueChart.setLabelToolTip(['fiat invest', 'current value', 'fiat return'])

        self.sliceFiatInvested.setValue(totalInvestFiat[taxCoinName])
        self.sliceFiatInvested.setColor(self.neutrColor)
        self.sliceFiatReturn.setValue(totalReturnFiat[taxCoinName])
        self.sliceFiatReturn.setColor(self.styleHandler.getQColor('PRIMARY'))
        self.sliceCoinValue.setValue(hypotheticalCoinValueNoFiat[taxCoinName])

        if (hypotheticalCoinValueNoFiat[taxCoinName] + totalReturnFiat[taxCoinName]) \
                < totalInvestFiat[taxCoinName]:
            self.sliceCoinValue.setColor(self.negColor)
            self.currentFiatValueChart.chartView.setColor([self.neutrColor, self.negColor,
                                                       self.styleHandler.getQColor('PRIMARY')])
        else:
            self.sliceCoinValue.setColor(self.posColor)
            self.currentFiatValueChart.chartView.setColor([self.neutrColor, self.posColor,
                                                       self.styleHandler.getQColor('PRIMARY')])

        # profit table
        years = []
        for year in realizedProfitPerYear:
            years.append(year)
        self.profitTable.setRowCount(len(years))
        self.profitTable.setVerticalHeaderLabels(years)
        for year, row in zip(realizedProfitPerYear, range(len(realizedProfitPerYear))):
            self.profitTable.setItem(row, 0, qtwidgets.QTableWidgetItem(
                controls.floatToString(realizedProfitPerYear[year][taxCoinName], 5) + ' ' + taxCoinName))
            self.profitTable.setItem(row, 1, qtwidgets.QTableWidgetItem(
                controls.floatToString(taxProfitPerYear[year][taxCoinName], 5) + ' ' + taxCoinName))
            self.profitTable.setItem(row, 2, qtwidgets.QTableWidgetItem(
                controls.floatToString(paidFeesPerYear[year][taxCoinName], 5) + ' ' + taxCoinName))
            self.profitTable.setItem(row, 3, qtwidgets.QTableWidgetItem(
                controls.floatToString(fiatPerYear[year][taxCoinName], 5) + ' ' + taxCoinName))


        # pie chart
        pieSeries = qtchart.QPieSeries()
        sortedModelIndex = sorted(range(len(self.model)),
                                  key=lambda x: self.model.coins[x].getCurrentValue()[taxCoinName], reverse=True)
        otherssum = core.CoinValue()
        try:
            topvalue = self.model.coins[sortedModelIndex[0]].getCurrentValue()[taxCoinName]
        except IndexError:
            topvalue = 0
        for index in sortedModelIndex:
            coin = self.model.coins[index]
            if coin.getCurrentValue()[taxCoinName] > topvalue/40 and \
                    coin.getCurrentValue()[taxCoinName] > abs(hypotheticalCoinValueNoFiat[taxCoinName]/75):
                pieSeries.append(coin.coinname, coin.getCurrentValue()[taxCoinName])
            elif coin.getCurrentValue()[taxCoinName] > 0:
                otherssum.add(coin.getCurrentValue())
        if otherssum[taxCoinName] > abs(hypotheticalCoinValueNoFiat[taxCoinName]/100):
            slice = pieSeries.append("others", otherssum[taxCoinName])
            slice.setLabelVisible()

        # if len(pieSeries.slices()) > 5:
        #     for slice in pieSeries.slices()[0:5]:
        #         if slice.value() > hypotheticalCoinValueNoFiat[taxCoinName]/20:
        #             slice.setLabelVisible()
        # else:
        for slice in pieSeries.slices():
            if slice.value() > abs(hypotheticalCoinValueNoFiat[taxCoinName]/20):
                slice.setLabelVisible()

        color = [255, 75, 225]
        for slice in pieSeries.slices():
            color = style.nextColor(color, 55)
            slice.setBrush(qtgui.QColor(*tuple(color)))
            slice.setLabelColor(qtgui.QColor(*tuple(color)))
            slice.setLabelPosition(qtchart.QPieSlice.LabelOutside)

        pieSeries.setHoleSize(0.6)
        self.portfolioChart.setSeries(pieSeries)
        portfolioChartLabels = []
        for coin in hypotheticalCoinValueNoFiat:
            portfolioChartLabels.append(controls.floatToString(hypotheticalCoinValueNoFiat[coin],
                                                            numberOfDecimals) + ' ' + coin)
        self.portfolioChart.chartView.setText(portfolioChartLabels, qt.AlignCenter)
        self.portfolioChart.chartView.setColor(self.neutrColor, False)


    def displayCurrenciesChangedSlot(self):
        # todo: update ui layout and trigger value update
        self.portfolioChart.chartView.setLabelCount(len(settings.mySettings.displayCurrencies()))


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
        for coin in coinList:
            if not coin.coinname in self:
                self[coin.coinname] = {}
            self[coin.coinname]['notes'] = coin.notes
        self.saveCoins()

    def updateCoinInfo(self, coinList):
        for coin in coinList:
            try:
                coin.notes = self[coin.coinname]['notes']
            except KeyError:
                coin.notes = ""

    def getCoins(self):
        coins = []
        for key in self:
            if key != 'DEFAULT':
                coins.append(key)
        return coins
