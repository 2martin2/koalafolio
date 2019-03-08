# -*- coding: utf-8 -*-
"""
Created on Sun Dec 16 19:09:51 2018

@author: Martin
"""

import PyQt5.QtGui as qtgui
import PyQt5.QtWidgets as qtwidgets
import PyQt5.QtCore as qtcore
import PyQt5.QtChart as qtchart
import gui.Qcontrols as controls
import PcpCore.core as core
import gui.QSettings as settings
import colorsys
import gui.QThreads as threads
import datetime
import gui.QLogger as logger

qt = qtcore.Qt
localLogger = logger.globalLogger

# %% portfolio table view
class QPortfolioTableView(qtwidgets.QTableView):
    def __init__(self, parent, *args, **kwargs):
        super(QPortfolioTableView, self).__init__(parent=parent, *args, **kwargs)

        self.setModel(QPortfolioTableModel())
        self.horizontalHeader().setSectionResizeMode(qtwidgets.QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, qtwidgets.QHeaderView.Interactive)
        self.horizontalHeader().setSectionResizeMode(1, qtwidgets.QHeaderView.Interactive)
        self.setColumnWidth(1, 160)
        self.horizontalHeader().setSectionResizeMode(2, qtwidgets.QHeaderView.Interactive)
        self.setColumnWidth(2, 100)
        self.verticalHeader().setSectionResizeMode(qtwidgets.QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.setItemDelegate(QCoinTableDelegate())

        self.setSortingEnabled(True)
        self.setEditTriggers(qtwidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(qtwidgets.QAbstractItemView.NoSelection)


# %% portfolio table model
class QPortfolioTableModel(qtcore.QAbstractTableModel, core.CoinList):
    coinAdded = qtcore.pyqtSignal([list])

    def __init__(self, *args, **kwargs):
        super(QPortfolioTableModel, self).__init__(*args, **kwargs)

        # init keys and header
        self.keys = [*core.CoinValue().value]
        self.header = ['coin', 'balance', 'realized ' + settings.mySettings['currency']['defaultreportcurrency']] + ['value ' + key for key in self.keys]
        self.firstValueColumn = 3

    def rowCount(self, parent):
        return len(self.coins)

    def columnCount(self, parent):
        return len(self.header)

    def data(self, index, role=qt.DisplayRole):
        if role == qt.DisplayRole:
            if index.column() == 0:  # coin row
                return self.coins[index.row()].coinname  # return coinname
            if index.column() == 1:  # balance row
                return self.coins[index.row()]  # return CoinBalance
            if index.column() == 2:  # profit row
                return self.coins[index.row()].tradeMatcher.getTotalProfit()  # return profit
            if index.column() >= self.firstValueColumn:  # return CoinBalance and key
                keys = [*core.CoinValue().value]
                return self.coins[index.row()], keys[index.column() - self.firstValueColumn]
        return qtcore.QVariant()

    def headerData(self, section, orientation, role):
        if role == qt.DisplayRole:
            if orientation == qt.Horizontal:
                return self.header[section]
            elif orientation == qt.Vertical:
                return section
        return qtcore.QVariant()

    def setData(self, index, value, role):
        if role == qt.EditRole:
            print('setData: ' + str(index.row()) + '; ' + str(index.column()))
        return True

    def flags(self, index):
        return qt.ItemIsSelectable | qt.ItemIsEditable | qt.ItemIsEnabled

    def histPricesChanged(self):
        super(QPortfolioTableModel, self).histPricesChanged()
        self.pricesUpdated()

    def histPriceUpdateFinished(self):
        super(QPortfolioTableModel, self).histPriceUpdateFinished()
        self.pricesUpdated()

    def pricesUpdated(self):
        RowStartIndex = self.index(0, 2)
        RowEndIndex = self.index(len(self.coins)-1, len(self.header) - 1)
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
        self.coinAdded.emit(self.getCoinNames())

    def addCoin(self, coinname):
        retval = super(QPortfolioTableModel, self).addCoin(coinname)
        # self.coinAdded.emit([coinname])
        return retval

    def deleteTrades(self, trades):
        self.beginResetModel()
        super(QPortfolioTableModel, self).deleteTrades(trades)
        self.endResetModel()


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
            profit1 = index1.data()[settings.mySettings['currency']['defaultreportcurrency']]
            profit2 = index2.data()[settings.mySettings['currency']['defaultreportcurrency']]
            return profit1 < profit2
        if column >= self.sourceModel().firstValueColumn:
            coinBalance1, key1 = index1.data()
            coinBalance2, key2 = index2.data()
            return coinBalance1.currentValue[key1] < coinBalance2.currentValue[key2]
        return index1.data() < index2.data()


# %% portfolio table delegate
# class QCoinBalanceDelegate(qtwidgets.QStyledItemDelegate):
class QCoinTableDelegate(qtwidgets.QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(QCoinTableDelegate, self).__init__(*args, **kwargs)

        self.marginV = 4  # vertical margin
        self.marginH = 15  # horizontal margin

    def paint(self, painter, option, index):
        painter.save()
        cellStartX = option.rect.x() + self.marginH
        cellStartY = option.rect.y() + self.marginV
        cellWidth = option.rect.width() - 2 * self.marginH
        cellHeight = option.rect.height() - 2 * self.marginV
        cellStopX = cellStartX + cellWidth
        cellStopY = cellStartY + cellHeight

        contentRect = qtcore.QRect(cellStartX, cellStartY, cellWidth, cellHeight)

        if index.column() == 0:  # coin
            super(QCoinTableDelegate, self).paint(painter, option, index)
        elif index.column() == 1:  # balance
            coinBalance = index.data(qt.DisplayRole)
            balance = controls.floatToString(coinBalance.balance, 5)
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

            # paint buy
            buyColor = qtgui.QColor(0, 180, 0, 255)
            buyBrush = qtgui.QBrush(buyColor)
            buyPen = painter.pen()
            buyPen.setBrush(buyBrush)
            painter.setPen(buyPen)
            painter.drawText(contentRect, qt.AlignLeft | qt.AlignBottom, buyAmount)
            if firstBuyLeftDate:
                painter.drawText(contentRect, qt.AlignLeft | qt.AlignTop, freeBuyYears)

            # paint sell
            sellColor = qtgui.QColor(180, 0, 0, 255)
            sellBrush = qtgui.QBrush(sellColor)
            sellPen = painter.pen()
            sellPen.setBrush(sellBrush)
            painter.setPen(sellPen)
            painter.drawText(contentRect, qt.AlignRight | qt.AlignBottom, sellAmount)

        elif index.column() == 2:
            profit = index.data(qt.DisplayRole)
            key = settings.mySettings['currency']['defaultreportcurrency']
            # for key in profit:
            # draw profit
            if profit[key] >= 0:
                drawColor = qtgui.QColor(0, 180, 0, 255)
            else:
                drawColor = qtgui.QColor(180, 0, 0, 255)
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
            coinBalance, key = index.data(qt.DisplayRole)
            boughtValue = coinBalance.initialValue[key]
            boughtPrice = coinBalance.getInitialPrice()[key]
            currentValue = coinBalance.currentValue[key]
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
            gainDay = coinBalance.change24h[key]
            gainDayStr = ("%.2f%%/24h" % (gainDay))

            # draw bought value
            defaultFont = painter.font()
            newFont = painter.font()
            newFont.setPixelSize(14)
            painter.setFont(newFont)
            painter.drawText(contentRect, qt.AlignLeft | qt.AlignTop, boughtValueStr)
            painter.setFont(defaultFont)
            painter.drawText(contentRect, qt.AlignLeft | qt.AlignBottom, boughtPriceStr)

            # draw current value and gain
            if gain >= 0:
                drawColor = qtgui.QColor(0, 180, 0, 255)
            else:
                drawColor = qtgui.QColor(180, 0, 0, 255)
            pen = painter.pen()
            pen.setBrush(qtgui.QBrush(drawColor))
            painter.setPen(pen)
            defaultFont = painter.font()
            newFont = painter.font()
            newFont.setPixelSize(14)
            painter.setFont(newFont)
            painter.drawText(contentRect, qt.AlignHCenter | qt.AlignTop, currentValueStr)
            painter.drawText(contentRect, qt.AlignRight | qt.AlignTop, gainStr)
            painter.setFont(defaultFont)
            painter.drawText(contentRect, qt.AlignHCenter | qt.AlignBottom, currentPriceStr)

            # draw day gain
            if gainDay >= 0:
                drawColor = qtgui.QColor(0, 180, 0, 255)
            else:
                drawColor = qtgui.QColor(180, 0, 0, 255)
            pen = painter.pen()
            pen.setBrush(qtgui.QBrush(drawColor))
            painter.setPen(pen)
            painter.drawText(contentRect, qt.AlignRight | qt.AlignBottom, gainDayStr)

        painter.restore()

    # def createEditor(self, parent, option, index):
    #     # return QCoinBalanceTableWidgetItem(core.CoinBalance(), parent=parent)
    #     pass

    # def setEditorData(self, editor, index):
    #     # editor.setText(core.CoinBalance())
    #     pass

    # def updateEditorGeometry(self, editor, option, index):
    #     pass

    # def setModelData(self, editor, model, index):
    #     pass

    def sizeHint(self, option, index):
        if index.column() == 0:
            return qtcore.QSize(50, 40)
        elif index.column() == 1:
            return qtcore.QSize(100, 40)
        elif index.column() >= 2:
            return qtcore.QSize(200, 40)


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
    def __init__(self, controller, height=200, *args, **kwargs):
        super(PortfolioOverview, self).__init__(*args, **kwargs)

        self.controller = controller
        self.height = height
        self.setFixedHeight(self.height)
        self.setContentsMargins(0, 0, 0, 0)
        self.horzLayout = qtwidgets.QHBoxLayout(self)

        # total invested fiat
        self.investedFiatLabel = controls.StyledLabelCont(self, 'fiat invest')
        self.investedFiatValue = qtwidgets.QLabel('xxx')
        self.investedFiatValue.setFont(qtgui.QFont('Arial', 12))
        self.investedFiatLabel.addWidget(self.investedFiatValue)
        # total returned fiat
        self.returnedFiatLabel = controls.StyledLabelCont(self, 'fiat return')
        self.returnedFiatValue = qtwidgets.QLabel('xxx')
        self.returnedFiatValue.setFont(qtgui.QFont('Arial', 12))
        self.returnedFiatLabel.addWidget(self.returnedFiatValue)
        # fiat performance
        # self.fiatPerformanceLabel = controls.StyledLabelCont(self, 'fiat perf')
        self.fiatPerformanceValue = qtwidgets.QLabel('xxx')
        self.fiatPerformanceValue.setFont(qtgui.QFont('Arial', 10))
        self.returnedFiatLabel.addWidget(self.fiatPerformanceValue)

        # invested value of current holdings
        self.currentInvestLabel = controls.StyledLabelCont(self, 'current invest')
        self.currentInvestValue = qtwidgets.QLabel('xxx')
        self.currentInvestValue.setFont(qtgui.QFont('Arial', 12))
        self.currentInvestLabel.addWidget(self.currentInvestValue)
        # current value of current holdings (hypothetical)
        self.hypotheticalCoinValueLabel = controls.StyledLabelCont(self, 'current value')
        self.hypotheticalCoinValue = qtwidgets.QLabel('xxx')
        self.hypotheticalCoinValue.setFont(qtgui.QFont('Arial', 12))
        self.hypotheticalCoinValueLabel.addWidget(self.hypotheticalCoinValue)
        # current performance of current holdings (hypothetical)
        # self.hypotheticalPerformanceLabel = controls.StyledLabelCont(self, 'coin perf')
        self.hypotheticalPerformanceValue = qtwidgets.QLabel('xxx')
        self.hypotheticalPerformanceValue.setFont(qtgui.QFont('Arial', 10))
        self.hypotheticalCoinValueLabel.addWidget(self.hypotheticalPerformanceValue)

        # realized profit (relevant for tax)
        self.realizedProfitLabel = controls.StyledLabelCont(self, 'realized profit')
        self.realizedProfitValue = qtwidgets.QLabel('xxx')
        self.realizedProfitValue.setFont(qtgui.QFont('Arial', 12))
        self.realizedProfitLabel.addWidget(self.realizedProfitValue)
        # unrealized profit (would be relevant for tax if realized)
        self.unrealizedProfitLabel = controls.StyledLabelCont(self, 'unrealized profit')
        self.unrealizedProfitValue = qtwidgets.QLabel('xxx')
        self.unrealizedProfitValue.setFont(qtgui.QFont('Arial', 12))
        self.unrealizedProfitLabel.addWidget(self.unrealizedProfitValue)

        # paid fees
        self.paidFeesLabel = controls.StyledLabelCont(self, 'fees paid')
        self.paidFeesValue = qtwidgets.QLabel('xxx')
        self.paidFeesValue.setFont(qtgui.QFont('Arial', 12))
        self.paidFeesLabel.addWidget(self.paidFeesValue)

        fiatLabels = [self.investedFiatLabel, self.returnedFiatLabel]
        portfolioLabels = [self.currentInvestLabel, self.hypotheticalCoinValueLabel]
        profitLabels = [self.realizedProfitLabel, self.unrealizedProfitLabel, self.paidFeesLabel]
        # otherLabels = [None, self.paidFeesLabel]
        labels = [fiatLabels, portfolioLabels, profitLabels]

        # self.dragWidget = controls.DragWidget(self)

        # self.labelGridLayout = qtwidgets.QGridLayout()
        # self.labelGridLayout.setContentsMargins(0, 0, 0, 0)
        self.labelHorzLayout = qtwidgets.QHBoxLayout()
        self.labelHorzLayout.setContentsMargins(0, 0, 0, 0)
        self.labelVertLayouts = []
        row = 0
        column = 0
        for columnLabels in labels:
            self.labelVertLayouts.append(qtwidgets.QVBoxLayout())
            self.labelVertLayouts[-1].setContentsMargins(0, 0, 0, 0)
            for rowLabel in columnLabels:
                if rowLabel:
                    # self.labelGridLayout.addWidget(rowLabel, row, column)
                    self.labelVertLayouts[-1].addWidget(rowLabel)
                # rowLabel.setParent(self.dragWidget)
                # rowLabel.move(qtcore.QPoint((column+0.5)*125, (row+0.2)*60))
                row += 1
            self.labelVertLayouts[-1].addStretch()
            self.labelHorzLayout.addLayout(self.labelVertLayouts[-1])
            row = 0
            column += 1


        # pie chart
        self.pieSeries = qtchart.QPieSeries()

        self.chart = qtchart.QChart()
        self.chart.setBackgroundVisible(False)
        self.chart.addSeries(self.pieSeries)
        # self.chart.setTitle("portfolio")
        self.chart.legend().hide()
        self.chart.setMargins(qtcore.QMargins(0, 0, 0, 0))
        self.chart.setMinimumWidth(self.height+30)

        self.chartView = qtchart.QChartView(self.chart)
        self.chartView.setRenderHint(qtgui.QPainter.Antialiasing)

        self.horzLayout.addLayout(self.labelHorzLayout)
        # self.horzLayout.addWidget(self.dragWidget)
        self.horzLayout.addStretch()
        self.horzLayout.addWidget(self.chartView)
        self.horzLayout.setContentsMargins(0, 0, 0, 0)

    def setModel(self, model):
        self.model = model
        self.model.modelReset.connect(self.coinTableChangedSlot)
        self.model.dataChanged.connect(self.coinTableChangedSlot)
        self.coinTableChangedSlot()

    def coinTableChangedSlot(self):
        # update new values

        # todo: display all displayCurrencies
        taxCoinName = settings.mySettings['currency']['defaultReportCurrency']
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


        # calculate all need values
        for coin in self.model:
            if coin.isFiat():  # calculate invested and returned fiat
                for trade in coin.trades:
                    if trade.amount < 0:
                        totalInvestFiat.add(trade.value.mult(-1))
                    else:
                        totalReturnFiat.add(trade.value)
            else:  # calculate value of portfolio
                currentInvestNoFiat.add(coin.initialValue)
                hypotheticalCoinValueNoFiat.add(coin.currentValue)
                realizedProfit.add(coin.tradeMatcher.getTotalProfit())
                for trade in coin.trades:
                    if trade.tradeType == "fee":
                        paidFees.add(trade.value.mult(-1))
            # fiat and coins
            # currentInvestAll.add(coin.initialValue)
            # hypotheticalValueAll.add(coin.currentValue)
            # realizedProfitAll.add(coin.tradeMatcher.getTotalProfit())

        fiatPerformance = (totalReturnFiat-totalInvestFiat).div(totalInvestFiat).mult(100)
        hypotheticalPerformanceNoFiat = (hypotheticalCoinValueNoFiat.div(currentInvestNoFiat)
                                         - core.CoinValue().setValue(1)).mult(100)
        unrealizedProfit = hypotheticalCoinValueNoFiat - currentInvestNoFiat

        def setLabelColor(label, isGreen):
            if isGreen:
                label.setBodyColor("green")
            else:
                label.setBodyColor("red")

        # total invested fiat
        self.investedFiatValue.setText(controls.floatToString(totalInvestFiat[taxCoinName],
                                                              numberOfDecimals) + ' ' + taxCoinName)
        # total returned fiat
        self.returnedFiatValue.setText(controls.floatToString(totalReturnFiat[taxCoinName],
                                                              numberOfDecimals) + ' ' + taxCoinName)
        setLabelColor(self.returnedFiatLabel, totalReturnFiat[taxCoinName] >= totalInvestFiat[taxCoinName])
        # fiat performance
        self.fiatPerformanceValue.setText("%.2f%%" % fiatPerformance[taxCoinName])

        # invested Label of current holdings
        self.currentInvestValue.setText(controls.floatToString(currentInvestNoFiat[taxCoinName],
                                                               numberOfDecimals) + ' ' + taxCoinName)
        # current Label of current holdings (hypothetical)
        self.hypotheticalCoinValue.setText(controls.floatToString(hypotheticalCoinValueNoFiat[taxCoinName],
                                                                       numberOfDecimals) + ' ' + taxCoinName)
        setLabelColor(self.hypotheticalCoinValueLabel, hypotheticalCoinValueNoFiat[taxCoinName] >= currentInvestNoFiat[taxCoinName])
        # current performance of current holdings (hypothetical)
        self.hypotheticalPerformanceValue.setText("%.2f%%" % hypotheticalPerformanceNoFiat[taxCoinName])
        # realized profit (relevant for tax)
        self.realizedProfitValue.setText(controls.floatToString(realizedProfit[taxCoinName],
                                                                numberOfDecimals) + ' ' + taxCoinName)
        setLabelColor(self.realizedProfitLabel, realizedProfit[taxCoinName] >= 0)
        # unrealized profit (would be relevant for tax if realized)
        self.unrealizedProfitValue.setText(controls.floatToString(unrealizedProfit[taxCoinName],
                                                                  numberOfDecimals) + ' ' + taxCoinName)
        setLabelColor(self.unrealizedProfitLabel, unrealizedProfit[taxCoinName] >= 0)
        # paid fees
        self.paidFeesValue.setText(controls.floatToString(paidFees[taxCoinName],
                                                                  numberOfDecimals) + ' ' + taxCoinName)
        setLabelColor(self.paidFeesLabel, paidFees[taxCoinName] <= 0)


        # pie chart
        self.pieSeries = qtchart.QPieSeries()
        # topSlices = []
        sortedModelIndex = sorted(range(len(self.model)), key=lambda x: self.model.coins[x].currentValue[taxCoinName], reverse=True)
        otherssum = core.CoinValue()
        try:
            topvalue = self.model.coins[sortedModelIndex[0]].currentValue[taxCoinName]
        except IndexError:
            topvalue = 0
        for index in sortedModelIndex:
            coin = self.model.coins[index]
            if coin.currentValue[taxCoinName] > topvalue/30:
                self.pieSeries.append(coin.coinname, coin.currentValue[taxCoinName])
            elif coin.currentValue[taxCoinName] > 0:
                otherssum.add(coin.currentValue)
        self.pieSeries.append("others", otherssum[taxCoinName])

        if len(self.pieSeries.slices()) > 5:
            for slice in self.pieSeries.slices()[0:5] + [self.pieSeries.slices()[-1]]:
                slice.setLabelVisible()
        else:
            for slice in self.pieSeries.slices():
                slice.setLabelVisible()

        def nextColor(rgbcolor, step):
            rgbcolornorm = [color/255 for color in rgbcolor]
            hls_color = colorsys.rgb_to_hls(*tuple(rgbcolornorm))
            rgbcolornew = colorsys.hls_to_rgb(hls_color[0]+step/360, hls_color[1], hls_color[2])
            return [rgbcolornew[0]*255, rgbcolornew[1]*255, rgbcolornew[2]*255]

        color = [191, 64, 159]
        for slice in self.pieSeries.slices():
            color = nextColor(color, 50)
            # slice.setPen(qtgui.QPen(qt.darkGreen, 2))
            slice.setBrush(qtgui.QColor(*tuple(color)))
            slice.setLabelColor(qtgui.QColor(*tuple(color)))
            slice.setLabelPosition(qtchart.QPieSlice.LabelOutside)

        self.chart.removeAllSeries()
        self.chart.addSeries(self.pieSeries)


    def displayCurrenciesChangedSlot(self):
        # todo: update ui layout and trigger value update
        pass

