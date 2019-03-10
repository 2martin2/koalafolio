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
import gui.QCharts as charts
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

    def triggerPriceUpdate(self):
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
            key = settings.mySettings['currency']['defaultreportcurrency']
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
            painter.drawText(contentRect, qt.AlignHCenter | qt.AlignTop, currentValueStr)
            painter.drawText(contentRect, qt.AlignRight | qt.AlignTop, gainStr)
            painter.setFont(defaultFont)
            painter.drawText(contentRect, qt.AlignHCenter | qt.AlignBottom, currentPriceStr)

            # draw day gain
            if gainDay >= 0:
                drawColor = qtgui.QColor(*settings.mySettings.getColor('POSITIV'))
            else:
                drawColor = qtgui.QColor(*settings.mySettings.getColor('NEGATIV'))
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


class ArcValueChart(qtchart.QChartView):
    def __init__(self, width, height, *args, **kwargs):
        super(ArcValueChart, self).__init__(*args, **kwargs)

        self.setMinimumHeight(height)
        self.setMinimumWidth(width)

        self.heading = qtwidgets.QLabel('', self)
        self.currentValueLabel = qtwidgets.QLabel('', self)
        self.currentValueLabel.setFont(qtgui.QFont("Arial", 12))
        self.currentPerfLabel = qtwidgets.QLabel('', self)
        self.currentPerfLabel.setFont(qtgui.QFont("Arial", 11))
        for label in [self.currentValueLabel, self.currentPerfLabel]:
            label.setVisible(False)
            self.setColor(qtgui.QColor(255, 255, 255))
        self.currentValueLabel.setMargin(0)
        self.currentPerfLabel.setMargin(0)
        # self.updateLabelPos()

    def updateLabelPos(self):
        center = self.geometry().center()
        pos1 = qtcore.QPoint()
        pos2 = qtcore.QPoint()
        pos1.setX(center.x() - self.currentValueLabel.width() / 2)
        pos2.setX(pos1.x() + self.currentValueLabel.width() - self.currentPerfLabel.width())
        pos1.setY(center.y() - self.currentValueLabel.height() / 2)
        pos2.setY(center.y() + self.currentPerfLabel.height() / 2)
        self.currentValueLabel.move(pos1)
        self.currentPerfLabel.move(pos2)

    def moveEvent(self, event):
        super(ArcValueChart, self).moveEvent(event)
        self.updateLabelPos()

    def resizeEvent(self, event):
        super(ArcValueChart, self).resizeEvent(event)
        self.updateLabelPos()

    def setText(self, text1, text2):
        self.currentValueLabel.setText(text1)
        self.currentPerfLabel.setText(text2)
        self.currentValueLabel.adjustSize()
        self.currentPerfLabel.adjustSize()
        self.updateLabelPos()
        self.currentValueLabel.setVisible(True)
        self.currentPerfLabel.setVisible(True)

    def setColor(self, col):
        print('*{background-color: rgba(0, 0, 0, 0); color:  #000000;}')
        print('*{background-color: rgba(0, 0, 0, 0); color:  ' + col.name() + ';}')
        self.currentValueLabel.setStyleSheet('*{background-color: rgba(0, 0, 0, 0); color:  ' + col.name() + ';}')
        self.currentPerfLabel.setStyleSheet('*{background-color: rgba(0, 0, 0, 0); color:  ' + col.name() + ';}')




# %% portfolio overview
class PortfolioOverview(qtwidgets.QWidget):
    def __init__(self, controller, height=200, *args, **kwargs):
        super(PortfolioOverview, self).__init__(*args, **kwargs)

        self.controller = controller
        self.height = height
        self.setFixedHeight(self.height)
        self.setContentsMargins(0, 0, 0, 0)
        self.horzLayout = qtwidgets.QHBoxLayout(self)
        self.horzLayout.setContentsMargins(0, 0, 0, 0)

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

        # donut chart
        self.currentValueChart = charts.LabeledDonatChart(self.height, self.height, 3, parent=self)
        self.donutSliceInvested = self.currentValueChart.addSlice('invested', 1, -1, False)
        self.donutSlicePerformance = self.currentValueChart.addSlice('performance', 0.5, -1, False)
        self.horzLayout.addWidget(self.currentValueChart)

        # bar chart
        self.fiatSet = qtchart.QBarSet("fiat")
        self.profitSet = qtchart.QBarSet("profit")
        self.investedSet = qtchart.QBarSet("invested")
        self.feeSet = qtchart.QBarSet("fees")
        sets = [self.fiatSet, self.profitSet, self.investedSet, self.feeSet]
        for set, label in zip(sets, ['fiat', 'profit', 'invested', 'fees']):
            set.setLabel(label)
        # fiat, profit, invest, fees  (fiat, current)
        fiatvalues = [2000, 10000]
        profitvalues = [0, 5000]
        investedvalues = [12000, 0]
        feevalues = [1000, 0]
        values = [fiatvalues, profitvalues, investedvalues, feevalues]

        for set, valueRow in zip(sets, values):
            for value in valueRow:
                set.append(value)

        self.barSeries = qtchart.QHorizontalStackedBarSeries()
        for set in sets:
            self.barSeries.append(set)
        self.barSeries.setLabelsVisible(True)

        self.barChart = qtchart.QChart()
        self.barChart.setBackgroundVisible(False)
        self.barChart.addSeries(self.barSeries)
        self.barChart.setAnimationOptions(qtchart.QChart.SeriesAnimations)

        categories = ['return', 'invest']
        barAxisY = qtchart.QBarCategoryAxis()
        barAxisY.append(categories)
        self.barChart.addAxis(barAxisY, qt.AlignLeft)
        self.barSeries.attachAxis(barAxisY)
        barAxisX = qtchart.QValueAxis()
        self.barChart.addAxis(barAxisX, qt.AlignBottom)
        self.barSeries.attachAxis(barAxisX)

        # self.barChart.legend().setVisible(False)
        self.barChart.setMinimumWidth(self.height*2)
        self.barChart.setMinimumHeight(self.height)

        self.barChartView = qtchart.QChartView(self.barChart)
        self.barChartView.setRenderHint(qtgui.QPainter.Antialiasing)

        self.horzLayout.addWidget(self.barChartView)


        # labels
        fiatLabels = [self.investedFiatLabel, self.returnedFiatLabel]
        portfolioLabels = [self.currentInvestLabel, self.hypotheticalCoinValueLabel]
        profitLabels = [self.realizedProfitLabel, self.unrealizedProfitLabel, self.paidFeesLabel]
        # otherLabels = [None, self.paidFeesLabel]
        labels = [None, fiatLabels, portfolioLabels, profitLabels, None]

        # self.labelGridLayout = qtwidgets.QGridLayout()
        # self.labelGridLayout.setContentsMargins(0, 0, 0, 0)
        self.horzLayout.setContentsMargins(0, 0, 0, 0)
        self.labelVertLayouts = []
        row = 0
        column = 0
        for columnLabels in labels:
            if columnLabels:
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
                # self.horzLayout.addLayout(self.labelVertLayouts[-1])
            # else:
                # self.horzLayout.addStretch()
            row = 0
            column += 1


        # pie chart
        self.portfolioChart = charts.LabeledDonatChart(self.height+30, self.height, 1, parent=self)
        self.horzLayout.addWidget(self.portfolioChart)

        self.refresh()

    def refresh(self):
        self.negColor = qtgui.QColor(*settings.mySettings.getColor('NEGATIV'))
        self.posColor = qtgui.QColor(*settings.mySettings.getColor('POSITIV'))
        self.neutrColor = qtgui.QColor(*settings.mySettings.getColor('NEUTRAL'))

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
        if self.controller.tradeList.isEmpty():
            startYear = datetime.datetime.now().year
        else:
            startYear = min([trade.date for trade in self.controller.tradeList]).year
        stopYear = datetime.datetime.now().year
        realizedProfitPerYear = {}
        paidFeesPerYear = {}

        for year in range(startYear, stopYear+1):
            realizedProfitPerYear[str(year)] = core.CoinValue()
            paidFeesPerYear[str(year)] = core.CoinValue()

        # calculate all needed values
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
                # realizedProfit.add(coin.tradeMatcher.getTotalProfit())
            for trade in coin.trades:
                if trade.tradeType == "fee":
                    paidFees.add(trade.value.mult(-1))
            # realizedProfitPerYearCoinList[coin.coinname] = (coin.tradeMatcher.getTimeDeltaProfit(
            #         datetime.date(year=2017, month=1, day=1), datetime.date(year=2019, month=12, day=31),
            #         taxFreeTimeDelta=settings.mySettings.getTaxSetting('taxfreelimityears'))[taxCoinName])
            for year in range(startYear, stopYear + 1):
                startDate = datetime.date(year=year, month=1, day=1)
                endDate = datetime.date(year=year, month=12, day=31)
                realizedProfitPerYear[str(year)].add(coin.tradeMatcher.getTimeDeltaProfit(startDate, endDate,
                    taxFreeTimeDelta=settings.mySettings.getTaxSetting('taxfreelimityears')))
                if trade.tradeType == "fee" and trade.date.date() >= startDate and trade.date.date() <= endDate:
                    paidFeesPerYear[str(year)].add(trade.value)
            # fiat and coins
            # currentInvestAll.add(coin.initialValue)
            # hypotheticalValueAll.add(coin.currentValue)
            # realizedProfitAll.add(coin.tradeMatcher.getTotalProfit())

        # realizedProfitPerYearCoinListSum = sum([realizedProfitPerYearCoinList[key] for key in realizedProfitPerYearCoinList])
        fiatPerformance = (totalReturnFiat-totalInvestFiat).div(totalInvestFiat).mult(100)
        hypotheticalPerformanceNoFiat = (hypotheticalCoinValueNoFiat.div(currentInvestNoFiat)
                                         - core.CoinValue().setValue(1)).mult(100)
        unrealizedProfit = hypotheticalCoinValueNoFiat - currentInvestNoFiat

        def setLabelColor(label, isPositiv):
            if isPositiv:
                label.setBodyColor(self.posColor.name())
            else:
                label.setBodyColor(self.negColor.name())

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

        # donat chart
        self.currentValueChart.chartView.setText(
            [controls.floatToString(currentInvestNoFiat[taxCoinName], numberOfDecimals) + ' ' + taxCoinName,
            controls.floatToString(hypotheticalCoinValueNoFiat[taxCoinName], numberOfDecimals) + ' ' + taxCoinName,
            "%.2f%%" % hypotheticalPerformanceNoFiat[taxCoinName]])

        if unrealizedProfit[taxCoinName] < 0:
            self.donutSliceInvested.setValue(currentInvestNoFiat[taxCoinName]+unrealizedProfit[taxCoinName])
            self.donutSliceInvested.setColor(self.neutrColor)
            self.donutSlicePerformance.setValue(-unrealizedProfit[taxCoinName])
            self.donutSlicePerformance.setColor(self.negColor)
            self.currentValueChart.chartView.setColor([self.neutrColor, self.negColor, self.negColor])
        else:
            self.donutSliceInvested.setValue(currentInvestNoFiat[taxCoinName])
            self.donutSliceInvested.setColor(self.neutrColor)
            self.donutSlicePerformance.setValue(unrealizedProfit[taxCoinName])
            self.donutSlicePerformance.setColor(self.posColor)
            self.currentValueChart.chartView.setColor([self.neutrColor, self.posColor, self.posColor])


        # pie chart
        pieSeries = qtchart.QPieSeries()
        # topSlices = []
        sortedModelIndex = sorted(range(len(self.model)), key=lambda x: self.model.coins[x].currentValue[taxCoinName], reverse=True)
        otherssum = core.CoinValue()
        try:
            topvalue = self.model.coins[sortedModelIndex[0]].currentValue[taxCoinName]
        except IndexError:
            topvalue = 0
        for index in sortedModelIndex:
            coin = self.model.coins[index]
            if coin.currentValue[taxCoinName] > topvalue/30 and coin.currentValue[taxCoinName] > abs(hypotheticalCoinValueNoFiat[taxCoinName]/50):
                pieSeries.append(coin.coinname, coin.currentValue[taxCoinName])
            elif coin.currentValue[taxCoinName] > 0:
                otherssum.add(coin.currentValue)
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

        def nextColor(rgbcolor, step):
            rgbcolornorm = [color/255 for color in rgbcolor]
            hls_color = colorsys.rgb_to_hls(*tuple(rgbcolornorm))
            rgbcolornew = colorsys.hls_to_rgb(hls_color[0]+step/360, hls_color[1], hls_color[2])
            return [rgbcolornew[0]*255, rgbcolornew[1]*255, rgbcolornew[2]*255]

        color = [191, 64, 159]
        for slice in pieSeries.slices():
            color = nextColor(color, 50)
            slice.setBrush(qtgui.QColor(*tuple(color)))
            slice.setLabelColor(qtgui.QColor(*tuple(color)))
            slice.setLabelPosition(qtchart.QPieSlice.LabelOutside)

        pieSeries.setHoleSize(0.6)
        self.portfolioChart.setSeries(pieSeries)
        self.portfolioChart.chartView.setText([controls.floatToString(hypotheticalCoinValueNoFiat[taxCoinName],
                                                            numberOfDecimals) + ' ' + taxCoinName])
        self.portfolioChart.chartView.setColor(qtgui.QColor(*settings.mySettings.getColor('NEUTRAL')), False)


    def displayCurrenciesChangedSlot(self):
        # todo: update ui layout and trigger value update
        pass

