# -*- coding: utf-8 -*-
"""
Created on Tue Nov 27 21:03:59 2018

@author: Martin
"""
import PyQt5.QtGui as qtgui
import PyQt5.QtWidgets as qtwidgets
import PyQt5.QtCore as qtcore
import koalafolio.gui.QSettings as settings
import koalafolio.web.cryptocompareApi as ccapi
import koalafolio.web.coingeckoApi as coinGecko
import koalafolio.PcpCore.core as core
from PIL.ImageQt import ImageQt
import koalafolio.gui.QLogger as logger
import datetime

localLogger = logger.globalLogger


class WebApiInterface(qtcore.QObject):
    coinPricesLoaded = qtcore.pyqtSignal([dict])
    coinIconsLoaded = qtcore.pyqtSignal([dict])
    coinPriceChartsLoaded = qtcore.pyqtSignal([dict])
    historicalPricesLoaded = qtcore.pyqtSignal([dict, int])
    # historicalPriceUpdateFinished = qtcore.pyqtSignal()

    def __init__(self):
        super(WebApiInterface, self).__init__()

        # self.histPrices = {}
        self.tradeBuffer = core.TradeList()

    def loadPrices(self, coins: list):
        if coins:
            if settings.mySettings.priceApiSwitch() == 'coinGecko':
                prices = coinGecko.getCoinPrices(coins)
            else:
                prices = ccapi.getCoinPrices(coins)

            self.coinPricesLoaded.emit(prices)

    def loadCoinIcons(self, coins: list):
        if coins:
            if settings.mySettings.priceApiSwitch() == 'coinGecko':
                icons = coinGecko.getIcons(coins)
            else:
                icons = ccapi.getIcons(coins)
            qicons = {}
            for key in coins:  # convert images to QIcon
                try:
                    if icons[key]:
                        im = icons[key].convert("RGBA")
                        qim = ImageQt(im)
                        qpix = qtgui.QPixmap.fromImage(qim)
                        qicons[key] = qtgui.QIcon(qpix)
                except KeyError:
                    localLogger.warning('no icon available for ' + key)  # ignore invalid key
                except Exception as ex:
                    localLogger.error('error converting icon: ' + str(ex))
            self.coinIconsLoaded.emit(qicons)

    def loadHistoricalPrices(self, tradeList):
        newTrades = False
        # copy trades to buffer
        for trade in tradeList:
            if not trade.valueLoaded:
                if not trade in self.tradeBuffer:
                    self.tradeBuffer.addTrade(trade)
                    newTrades = True
        histPrices = {}
        counter = 0
        while not self.tradeBuffer.isEmpty():
            trade = self.tradeBuffer.trades.pop()
            try:
                if not trade.valueLoaded:
                    if settings.mySettings.priceApiSwitch() == 'coinGecko':
                        histPrices[trade.tradeID] = coinGecko.getHistoricalPrice(trade)
                    else:
                        histPrices[trade.tradeID] = ccapi.getHistoricalPrice(trade)
                    counter += 1
            except ConnectionRefusedError:
                # save failed trade for next time
                trade.tradeBuffer.append(trade)
                # stop here and retry next time
                break
            if counter >= 100:
                break
        if histPrices or newTrades:
            self.historicalPricesLoaded.emit(histPrices, len(self.tradeBuffer))

    def loadcoinPriceCharts(self, coins: list, coinList: core.CoinList):
        if coins:
            coinPriceCharts = {}
            for coin in coins:
                try:
                    trades = coinList.getCoinByName(coin).tradeMatcher.buysLeft
                    if trades:
                        minDate = datetime.datetime.combine(min([trade.date for trade in trades]), datetime.datetime.min.time())
                        coinPriceCharts[coin] = coinGecko.getPriceChartData(coin, startTime=minDate)
                except KeyError:
                    localLogger.warning('no priceChartData available for ' + coin)  # ignore invalid key
                except Exception as ex:
                    localLogger.error('error converting priceChartData: ' + str(ex))

            self.coinPriceChartsLoaded.emit(coinPriceCharts)


# %% threads
class UpdatePriceThread(qtcore.QThread):
    coinPricesLoaded = qtcore.pyqtSignal([dict])
    coinIconsLoaded = qtcore.pyqtSignal([dict])
    coinPriceChartsLoaded = qtcore.pyqtSignal([dict])
    historicalPricesLoaded = qtcore.pyqtSignal([dict, int])

    def __init__(self, coinList, tradeList):
        super(UpdatePriceThread, self).__init__()
        self.coinList = coinList
        self.tradeList = tradeList


    def __del__(self):
        self.wait()

    def run(self):
        self.webApiInterface = WebApiInterface()
        # retrun current price
        self.webApiInterface.coinPricesLoaded.connect(self.coinPricesLoaded)
        self.webApiInterface.coinIconsLoaded.connect(self.coinIconsLoaded)
        self.webApiInterface.coinPriceChartsLoaded.connect(self.coinPriceChartsLoaded)
        # return hist prices
        self.webApiInterface.historicalPricesLoaded.connect(self.historicalPricesLoaded)
        # load hist prices for trades
        self.tradeList.triggerHistPriceUpdate.connect(lambda tradeList: self.webApiInterface.loadHistoricalPrices(tradeList))
        # load current prices for coins
        self.coinList.PriceUpdateRequest.connect(lambda coins: self.webApiInterface.loadPrices(coins))
        self.coinList.coinAdded.connect(lambda coins: self.webApiInterface.loadPrices(coins))
        self.coinList.coinAdded.connect(lambda coins: self.webApiInterface.loadCoinIcons(coins))
        self.coinList.coinAdded.connect(lambda coins: self.webApiInterface.loadcoinPriceCharts(coins, self.coinList))
        self.priceTimer = qtcore.QTimer()
        self.priceChartTimer = qtcore.QTimer()
        self.histTimer = qtcore.QTimer()
        self.priceTimer.timeout.connect(lambda: self.webApiInterface.loadPrices(self.coinList.getCoinNames()))
        self.priceChartTimer.timeout.connect(lambda: self.webApiInterface.loadcoinPriceCharts(self.coinList.getCoinNames(), self.coinList))
        self.histTimer.timeout.connect(lambda: self.webApiInterface.loadHistoricalPrices(self.webApiInterface.tradeBuffer))
        self.priceTimer.start(settings.mySettings.priceUpdateInterval()*1000)
        self.priceChartTimer.start(settings.mySettings.priceUpdateInterval() * 100000)
        self.histTimer.start(100)
        self.exec()
        self.deleteLater()
