# -*- coding: utf-8 -*-
"""
Created on 11.04.2021

@author: Martin
"""



from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QAbstractItemView, QAbstractScrollArea, QCheckBox, QHBoxLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtChart import QPieSeries, QPieSlice
import koalafolio.gui.widgets.Qcontrols as controls
import koalafolio.gui.widgets.QCharts as charts
import koalafolio.PcpCore.core as core
import koalafolio.gui.helper.QSettings as settings
import koalafolio.gui.helper.QStyle as style
import datetime
import koalafolio.gui.helper.QLogger as logger
import koalafolio.gui.widgets.QPortfolioTable as ptable
from pages.Qpages import Page

localLogger = logger.globalLogger


# %% portfolio overview
class PortfolioOverview(QWidget):
    expandTable = pyqtSignal()
    collapseTable = pyqtSignal()
    hideLowBalanceChanged = pyqtSignal()
    hideLowValueChanged = pyqtSignal()
    searchBoxTextChanged = pyqtSignal([str])

    def __init__(self, controller, height=200, *args, **kwargs):
        super(PortfolioOverview, self).__init__(*args, **kwargs)

        self.controller = controller
        self.styleHandler = self.controller.styleSheetHandler
        self.height = height
        self.setFixedHeight(self.height)
        self.setContentsMargins(0, 0, 0, 0)
        self.horzLayout = QHBoxLayout(self)
        self.horzLayout.setContentsMargins(0, 0, 0, 0)

        # profit table
        self.profitTable = QTableWidget()
        self.profitTable.setSelectionMode(QAbstractItemView.NoSelection)
        self.profitTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.profitTable.setColumnCount(4)
        self.profitTable.setHorizontalHeaderLabels(["profit", "tax profit", "fees", "fiat profit"])
        self.profitTable.horizontalHeaderItem(0).setToolTip("profit per year")
        self.profitTable.horizontalHeaderItem(1).setToolTip("profit relevant for tax calculation")
        self.profitTable.horizontalHeaderItem(2).setToolTip("fees per year")
        self.profitTable.horizontalHeaderItem(3).setToolTip("fiat profit per year")
        self.profitTable.horizontalHeader().setVisible(True)
        self.profitTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

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

        self.perfChartCont = charts.ChartCont(appPath=self.controller.appPath, parent=self)
        self.controller.startRefresh.connect(self.perfChartCont.clearButtonStyle)
        self.controller.endRefresh.connect(self.perfChartCont.setButtonStyle)
        self.perfChartCont.addChart(self.currentValueChart)
        self.perfChartCont.addChart(self.currentFiatValueChart)
        self.perfChartCont.setChartIndex(settings.mySettings.getGuiSetting('performancechartindex'))
        self.horzLayout.addWidget(self.perfChartCont)

        # table controls
        self.searchBox = QLineEdit(parent=self)
        self.searchBox.setPlaceholderText('search')
        self.searchBox.textChanged.connect(self.searchBoxTextChanged)
        self.expandAllButton = QPushButton("expand", self)
        self.expandAllButton.clicked.connect(self.expandTable)
        self.collapseAllButton = QPushButton("collapse", self)
        self.collapseAllButton.clicked.connect(self.collapseTable)
        self.hideLowBalanceCheckBox = QCheckBox("hide low balance", parent=self)
        if settings.mySettings.getGuiSetting('hidelowbalancecoins'):
            self.hideLowBalanceCheckBox.setCheckState(Qt.Checked)
        else:
            self.hideLowBalanceCheckBox.setCheckState(Qt.Unchecked)
        self.hideLowBalanceCheckBox.stateChanged.connect(lambda state: self.emitHideLowBalanceChanged(state))
        self.hideLowValueCheckBox = QCheckBox("hide low value", parent=self)
        if settings.mySettings.getGuiSetting('hidelowvaluecoins'):
            self.hideLowValueCheckBox.setCheckState(Qt.Checked)
        else:
            self.hideLowValueCheckBox.setCheckState(Qt.Unchecked)
        self.hideLowValueCheckBox.stateChanged.connect(lambda state: self.emitHideLowValueChanged(state))

        self.controlsLayout = QHBoxLayout()
        self.controlsLayout.addStretch()
        self.controlsLayout.addWidget(self.searchBox)
        self.controlsLayout.addWidget(self.hideLowBalanceCheckBox)
        self.controlsLayout.addWidget(self.hideLowValueCheckBox)
        self.controlsLayout.addWidget(self.expandAllButton)
        self.controlsLayout.addWidget(self.collapseAllButton)
        self.controlsLayout.addStretch()

        self.centerVertLayout = QVBoxLayout()
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
        self.negColor = QColor(*settings.mySettings.getColor('NEGATIV'))
        self.posColor = QColor(*settings.mySettings.getColor('POSITIV'))
        self.neutrColor = QColor(*settings.mySettings.getColor('TEXT_NORMAL'))

    def setModel(self, model):
        self.model = model
        self.model.modelReset.connect(self.coinTableChangedSlot)
        self.model.dataChanged.connect(self.coinTableChangedSlot)
        self.coinTableChangedSlot()

    def emitHideLowBalanceChanged(self, state):
        if state == Qt.Checked:
            settings.mySettings.setGuiSetting('hidelowbalancecoins', True)
        else:
            settings.mySettings.setGuiSetting('hidelowbalancecoins', False)
        self.hideLowBalanceChanged.emit()

    def emitHideLowValueChanged(self, state):
        if state == Qt.Checked:
            settings.mySettings.setGuiSetting('hidelowvaluecoins', True)
        else:
            settings.mySettings.setGuiSetting('hidelowvaluecoins', False)
        self.hideLowValueChanged.emit()

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
        fiatPerYear = {}
        taxProfitPerYear = {}
        rewardPerYear = {}

        for year in range(startYear, stopYear+1):
            realizedProfitPerYear[str(year)] = core.CoinValue()
            paidFeesPerYear[str(year)] = core.CoinValue()
            fiatPerYear[str(year)] = core.CoinValue()
            taxProfitPerYear[str(year)] = core.CoinValue()
            rewardPerYear[str(year)] = core.CoinValue()

        # calculate all needed values
        for coin in self.model:
            if coin.isFiat():  # calculate invested and returned fiat
                for trade in coin.trades:
                    # only add fiat trade if partner trade is not fiat
                    isFiatCryptoTrade = True
                    if trade.tradePartnerId:
                        if self.controller.tradeList.getTradeById(trade.tradePartnerId):
                            if self.controller.tradeList.getTradeById(trade.tradePartnerId).isFiat():
                                isFiatCryptoTrade = False
                    if isFiatCryptoTrade:
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
                realizedProfit.add(coin.getTotalProfit())
            # calc fees per year
            for trade in coin.trades:
                if trade.tradeType == "fee":
                    paidFees.add(trade.getValue())
                    for year in range(startYear, stopYear + 1):
                        startDate = datetime.date(year=year, month=1, day=1)
                        endDate = datetime.date(year=year, month=12, day=31)
                        if trade.date.date() >= startDate and trade.date.date() <= endDate:
                            paidFeesPerYear[str(year)].add(trade.getValue())

            for year in range(startYear, stopYear + 1):
                startDate = datetime.date(year=year, month=1, day=1)
                endDate = datetime.date(year=year, month=12, day=31)
                taxProfitPerYear[str(year)].add(coin.getTimeDeltaProfitTaxable(startDate, endDate))
                rewardPerYear[str(year)].add(coin.getTimeDeltaReward(startDate, endDate))
                realizedProfitPerYear[str(year)].add(coin.getTimeDeltaProfit(startDate, endDate))
            # fiat and coins
            # currentInvestAll.add(coin.initialValue)
            # hypotheticalValueAll.add(coin.getCurrentValue())
            # realizedProfitAll.add(coin..getTotalProfit())

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
             controls.floatToString(totalReturnFiat[taxCoinName], numberOfDecimals) + ' ' + taxCoinName], Qt.AlignCenter)

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
            self.profitTable.setItem(row, 0, QTableWidgetItem(
                controls.floatToString(realizedProfitPerYear[year][taxCoinName] + rewardPerYear[year][taxCoinName], 5) + ' ' + taxCoinName))
            self.profitTable.setItem(row, 1, QTableWidgetItem(
                controls.floatToString(taxProfitPerYear[year][taxCoinName] + rewardPerYear[year][taxCoinName], 5) + ' ' + taxCoinName))
            self.profitTable.setItem(row, 2, QTableWidgetItem(
                controls.floatToString(paidFeesPerYear[year][taxCoinName], 5) + ' ' + taxCoinName))
            self.profitTable.setItem(row, 3, QTableWidgetItem(
                controls.floatToString(fiatPerYear[year][taxCoinName], 5) + ' ' + taxCoinName))


        # pie chart
        pieSeries = QPieSeries()
        sortedModelIndex = sorted(range(len(self.model)),
                                  key=lambda x: self.model.coins[x].getCurrentValue()[taxCoinName], reverse=True)
        otherssum = core.CoinValue()
        try:
            topvalue = self.model.coins[sortedModelIndex[0]].getCurrentValue()[taxCoinName]
        except IndexError:
            topvalue = 0
        for index in sortedModelIndex:
            coin = self.model.coins[index]
            if not coin.isFiat():
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
            slice.setBrush(QColor(*tuple(color)))
            slice.setLabelColor(QColor(*tuple(color)))
            slice.setLabelPosition(QPieSlice.LabelOutside)

        pieSeries.setHoleSize(0.6)
        self.portfolioChart.setSeries(pieSeries)
        portfolioChartLabels = []
        for coin in hypotheticalCoinValueNoFiat:
            portfolioChartLabels.append(controls.floatToString(hypotheticalCoinValueNoFiat[coin],
                                                               numberOfDecimals) + ' ' + coin)
        self.portfolioChart.chartView.setText(portfolioChartLabels, Qt.AlignCenter)
        self.portfolioChart.chartView.setColor(self.neutrColor, False)

    def displayCurrenciesChangedSlot(self):
        # todo: update ui layout and trigger value update
        self.portfolioChart.chartView.setLabelCount(len(settings.mySettings.displayCurrencies()))


# %% portfolio showing all the coins and there current value ...
class PortfolioPage(Page):
    def __init__(self, parent, controller):
        super(PortfolioPage, self).__init__(parent=parent, controller=controller)

        self.layoutUI()

    # initial layout ob the Page
    def layoutUI(self):
        # main layout
        self.mainLayout = QHBoxLayout(self)

        # portfolio coinDataFrame
        # adding parent here causes crash in setStyleSheet call??!
        # exit code -1073741819 (0xC0000005), very strange
        # todo: check out error
        # for now no parent is given, seems to work fine
        self.coinDataFrame = PortfolioOverview(self.controller, height=200)
        self.controller.settingsModel.displayCurrenciesChanged.connect(
            self.coinDataFrame.displayCurrenciesChangedSlot)
        # self.coinDataFrame.setFixedHeight(200)
        self.coinDataFrame.setModel(self.controller.coinList)

        self.coinTableView = ptable.QPortfolioTableView(self)
        self.coinProxyModel = ptable.QTableSortingModel()
        self.coinProxyModel.setSourceModel(self.controller.coinList)
        self.coinTableView.setModel(self.coinProxyModel)
        guiSettings = settings.mySettings.getGuiSettings()
        self.coinTableView.sortByColumn(guiSettings['portfolio_sort_row'], guiSettings['portfolio_sort_dir'])

        self.coinTableView.show()
        self.controller.coinList.triggerViewReset.connect(self.createNewView)
        self.coinDataFrame.expandTable.connect(self.coinTableView.expandAll)
        self.coinDataFrame.collapseTable.connect(self.coinTableView.collapseAll)
        self.coinDataFrame.hideLowBalanceChanged.connect(lambda: self.filterCoinTable())
        self.coinDataFrame.hideLowValueChanged.connect(lambda: self.filterCoinTable())
        self.coinDataFrame.searchBoxTextChanged.connect(
            lambda text: self.coinTableView.model().setFilterByColumn(0, text))

        # layout
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.addWidget(self.coinDataFrame)
        self.verticalLayout.addWidget(self.coinTableView)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)

        self.mainLayout.addLayout(self.verticalLayout)

    # refresh page every time it is activated
    def refresh(self):
        self.controller.coinList.triggerPriceUpdate()

    def getGuiProps(self):
        gui = {'portfolio_sort_row': str(self.coinProxyModel.sortedColumn),
               'portfolio_sort_dir': str(self.coinProxyModel.sortedDir),
               'performancechartindex': self.coinDataFrame.perfChartCont.chartIndex}
        return gui

    def filterCoinTable(self):
        self.coinTableView.model().invalidateFilter()

    def createNewView(self):
        self.coinDataFrame.expandTable.disconnect(self.coinTableView.expandAll)
        self.coinDataFrame.collapseTable.disconnect(self.coinTableView.collapseAll)
        self.verticalLayout.removeWidget(self.coinTableView)
        self.coinTableView.setStyleSheet("")
        self.coinTableView.deleteLater()

        self.coinTableView = ptable.QPortfolioTableView(self)
        self.coinTableView.setModel(self.coinProxyModel)
        guiSettings = settings.mySettings.getGuiSettings()
        self.coinTableView.sortByColumn(guiSettings['portfolio_sort_row'], guiSettings['portfolio_sort_dir'])

        self.coinTableView.show()

        self.coinDataFrame.expandTable.connect(self.coinTableView.expandAll)
        self.coinDataFrame.collapseTable.connect(self.coinTableView.collapseAll)

        self.verticalLayout.addWidget(self.coinTableView)

