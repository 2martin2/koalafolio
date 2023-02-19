# -*- coding: utf-8 -*-
"""
Created on Tue Nov 27 21:03:59 2018

@author: Martin
"""
import PyQt5.QtGui as qtgui
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
    coinPricesLoaded = qtcore.pyqtSignal([dict, list])
    coinIconsLoaded = qtcore.pyqtSignal([dict, list])
    coinPriceChartsLoaded = qtcore.pyqtSignal([dict])
    historicalPricesLoaded = qtcore.pyqtSignal([dict, int])
    changeHistTimerInterval = qtcore.pyqtSignal([int])
    # historicalPriceUpdateFinished = qtcore.pyqtSignal()

    def __init__(self):
        super(WebApiInterface, self).__init__()

        # self.histPrices = {}
        self.tradeBuffer = core.TradeList()

        self.histApiFailedCounter = 0

    def loadPrices(self, coins: list):
        localLogger.info('loading new prices for coins: ' + str(len(coins)))
        if coins:
            if settings.mySettings.priceApiSwitch() == 'coingecko':
                prices = coinGecko.getCoinPrices(coins)
            else:
                prices = ccapi.getCoinPrices(coins)

            self.coinPricesLoaded.emit(prices, coins)

    def loadCoinIcons(self, coins: list):
        # localLogger.info('loading new Icons for coins: ' + str(len(coins)))
        if coins:
            if settings.mySettings.priceApiSwitch() == 'coingecko':
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
                    # localLogger.warning('no icon returned for ' + key)  # ignore invalid key
                    pass
                except Exception as ex:
                    localLogger.error('error converting icon: ' + str(ex))
            self.coinIconsLoaded.emit(qicons, coins)

    def loadHistoricalPricesEvent(self, tradeList):
        #print("histPrices event trigger next call")
        self.loadHistoricalPrices(tradeList)

    def loadHistoricalPricesTimer(self, tradeList):
        #print("histPrices time trigger next call")
        self.loadHistoricalPrices(tradeList)

    def loadHistoricalPrices(self, tradeList):
        localLogger.info("loading next 100 hist prices")
        newTrades = False
        # copy trades to buffer
        for trade in tradeList:
            if not trade.valueLoaded:
                if not trade in self.tradeBuffer:
                    self.tradeBuffer.addTrade(trade)
                    newTrades = True
        histPrices = {}
        counter = 0
        loadingStopped = False
        while not self.tradeBuffer.isEmpty() and not loadingStopped:
            trade = self.tradeBuffer.trades.pop()
            try:
                if not trade.valueLoaded:
                    if settings.mySettings.priceApiSwitch() == 'coingecko':
                        histPrices[trade.tradeID] = coinGecko.getHistoricalPrice(trade)
                    else:
                        histPrices[trade.tradeID] = ccapi.getHistoricalPrice(trade)
                    counter += 1
            except ConnectionRefusedError:
                self.histApiFailedCounter += 1
                # save failed trade for next time
                self.tradeBuffer.trades.append(trade)
                # todo: set dynamic timer interval depending on current rate limit values
                if self.histApiFailedCounter >= 10:
                    # log
                    localLogger.warning("connectionRefused while loading historical prices repeatetly, retry api call in 10min")
                    # increase histTimerInterval to 5min
                    self.changeHistTimerInterval.emit(600000)
                else:
                    # log
                    localLogger.warning("connectionRefused while loading historical prices, retry api call in 30s")
                    # increase histTimerInterval to 30s
                    self.changeHistTimerInterval.emit(30000)
                # stop here and retry next time
                loadingStopped = True
            if counter >= 100:
                self.histApiFailedCounter = 0
                # decrease histTimerInterval to 21s
                self.changeHistTimerInterval.emit(21000)
                loadingStopped = True
        if histPrices or newTrades:
            self.historicalPricesLoaded.emit(histPrices, len(self.tradeBuffer))

    def loadcoinPriceCharts(self, coins: list, coinList: core.CoinList):
        if settings.mySettings.getGuiSetting(key='loadpricehistorychart'):
            if coins:
                coinPriceCharts = {}
                for coinwallets in coins:
                    for coin in coinwallets:
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
    coinPricesLoaded = qtcore.pyqtSignal([dict, list])
    coinIconsLoaded = qtcore.pyqtSignal([dict, list])
    coinPriceChartsLoaded = qtcore.pyqtSignal([dict])
    historicalPricesLoaded = qtcore.pyqtSignal([dict, int])

    def __init__(self, coinList, tradeList):
        super(UpdatePriceThread, self).__init__()
        self.coinList = coinList
        self.tradeList = tradeList

        self.priceTimer = qtcore.QTimer()
        self.priceChartTimer = qtcore.QTimer()
        self.histTimer = qtcore.QTimer()

        self.webApiInterface = WebApiInterface()

    def __del__(self):
        self.wait()

    def setHistTimerInterval(self, interval):
        print("set histPriceTimer: " + str(interval))
        self.histTimer.setInterval(interval)

    def run(self):
        # return current price
        self.webApiInterface.coinPricesLoaded.connect(self.coinPricesLoaded)
        self.webApiInterface.coinIconsLoaded.connect(self.coinIconsLoaded)
        self.webApiInterface.coinPriceChartsLoaded.connect(self.coinPriceChartsLoaded)
        # return hist prices
        self.webApiInterface.historicalPricesLoaded.connect(self.historicalPricesLoaded)
        self.webApiInterface.changeHistTimerInterval.connect(self.setHistTimerInterval)
        # load hist prices for trades
        self.tradeList.triggerHistPriceUpdate.connect(
            lambda tradeList: self.webApiInterface.loadHistoricalPricesEvent(tradeList))

        # load current prices for coins
        self.coinList.triggerPriceUpdateForCoins.connect(lambda coins: self.webApiInterface.loadPrices(coins))
        self.coinList.triggerApiUpdateForCoins.connect(lambda coins: self.webApiInterface.loadPrices(coins))
        self.coinList.triggerApiUpdateForCoins.connect(lambda coins: self.webApiInterface.loadCoinIcons(coins))
        self.coinList.triggerApiUpdateForCoins.connect(lambda coins: self.webApiInterface.loadcoinPriceCharts(coins, self.coinList))
        self.priceTimer.timeout.connect(lambda: self.webApiInterface.loadPrices(self.coinList.getCoinNames()))
        self.priceChartTimer.timeout.connect(
            lambda: self.webApiInterface.loadcoinPriceCharts(self.coinList.getCoinNames(), self.coinList))
        self.histTimer.timeout.connect(
            lambda: self.webApiInterface.loadHistoricalPricesTimer(self.webApiInterface.tradeBuffer))

        self.priceTimer.start(int(settings.mySettings.priceUpdateInterval() * 1000))
        self.priceChartTimer.start(int(settings.mySettings.priceUpdateInterval() * 1000))
        # trigger hist timer every 1s
        self.histTimer.start(1000)
        self.exec()
        self.deleteLater()
