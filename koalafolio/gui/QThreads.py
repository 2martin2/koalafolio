# -*- coding: utf-8 -*-
"""
Created on Tue Nov 27 21:03:59 2018

@author: Martin
"""
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QIcon
import koalafolio.gui.QSettings as settings
import koalafolio.web.cryptocompareApi as ccapi
import koalafolio.web.coingeckoApi as coinGecko
import koalafolio.PcpCore.core as core
import koalafolio.gui.QLogger as logger
import datetime
import requests

localLogger = logger.globalLogger


class WebApiInterface(QObject):
    coinPricesLoaded = pyqtSignal([dict, list])
    coinIconsLoaded = pyqtSignal([dict, list])
    coinPriceChartsLoaded = pyqtSignal([dict])
    historicalPricesLoaded = pyqtSignal([dict, int])
    changeHistTimerInterval = pyqtSignal([int])
    changeIconTimerInterval = pyqtSignal([int])
    # historicalPriceUpdateFinished = pyqtSignal()

    def __init__(self):
        super(WebApiInterface, self).__init__()

        # self.histPrices = {}
        self.tradeBuffer = core.TradeList()
        self.coinIconUrls = {}
        self.coinIconUrls["ccapi"] = {}
        self.coinIconUrls["coingecko"] = {}
        self.coinIconUrls["merged"] = {}

        self.histApiFailedCounter = 0

    def loadPrices(self, coins: list):
        localLogger.info('loading new prices for coins: ' + str(len(coins)))
        if coins:
            if settings.mySettings.priceApiSwitch() == 'coingecko':
                prices = coinGecko.getCoinPrices(coins)
            else:
                prices = ccapi.getCoinPrices(coins)

            self.coinPricesLoaded.emit(prices, coins)

    def loadCoinIcons(self):
        qicons = {}
        coins = []
        # loop all iconUrl Dicts (coingecko, ccapi)
        for api in self.coinIconUrls:
            # check if buffer is not empty
            if self.coinIconUrls[api]:
                localLogger.info("loading coin Icons")
                coinsInDict = list(self.coinIconUrls[api].keys())
                # loop all coins in this url Dict
                for coin in coinsInDict:
                    # only load image if not already loaded
                    if coin not in qicons:
                        # get url and remove from buffer
                        url = self.coinIconUrls[api].pop(coin)
                        # load Image from url
                        image = None
                        try:
                            imagedata = self.getImage(url, coin)
                        except ConnectionRefusedError:
                            localLogger.info("ratelimit reached loading coin Icons, continue in 20s")
                            # rate limit, readd coin to buffer and try again next time
                            self.coinIconUrls[api][coin] = url
                            # increase iconTimerInterval to 10s
                            self.changeIconTimerInterval.emit(20000)
                            # end this loop
                            break
                        except Exception as ex:
                            # unknown error, ignore this url
                            logger.globalLogger.warning(
                                'error loading Icon for : ' + str(coin) + ", exception: " + str(ex))
                        # save coin
                        coins.append(coin)
                        # convert image
                        if imagedata:
                            qicons[coin] = self.imageToQIcon(imagedata)
        # if new qicons return them to main thread
        if qicons:
            self.coinIconsLoaded.emit(qicons, coins)

    def loadCoinIconUrls(self, coins: list):
        localLogger.info('adding coins to loadIconBuffer: ' + str(len(coins)))
        # localLogger.info('loading new Icons for coins: ' + str(len(coins)))
        if coins:
            if settings.mySettings.priceApiSwitch() == 'coingecko':
                UrlTemp = coinGecko.getIconUrls(coins)
                for coin in UrlTemp:
                    self.coinIconUrls["coingecko"][coin] = UrlTemp[coin]
            elif settings.mySettings.priceApiSwitch() == 'cryptocompare':
                UrlTemp = ccapi.getIconUrls(coins)
                for coin in UrlTemp:
                    self.coinIconUrls["ccapi"][coin] = UrlTemp[coin]
            else: # mixed
                UrlTemp = ccapi.getIconUrls(coins)
                for coin in UrlTemp:
                    self.coinIconUrls["merged"][coin] = UrlTemp[coin]
                UrlTemp = coinGecko.getIconUrls(coins)
                for coin in UrlTemp:
                    if coin not in self.coinIconUrls["merged"]:
                        self.coinIconUrls["merged"][coin] = UrlTemp[coin]
        self.loadCoinIcons()


    def getImage(self, url, coin):
        try:
            imageResponse = requests.get(url, proxies=settings.mySettings.proxies(), timeout=100)
        except Exception as ex:
            logger.globalLogger.warning('error in getImage for ' + str(coin) + ': ' + str(ex))
            return None
        if imageResponse.status_code == 200:
            # request successful
            return imageResponse.content
        if imageResponse.status_code == 429:
            raise ConnectionRefusedError(
                "response code: " + str(imageResponse.status_code) + ", reason: " + str(imageResponse.reason))
        raise ConnectionError(
            "response code: " + str(imageResponse.status_code) + ", reason: " + str(imageResponse.reason))

    def imageToQIcon(self, imagedata):
        # Convert to QImage
        q_image = QImage()
        q_image.loadFromData(imagedata)
        # Convert to QPixmap
        qpix = QPixmap.fromImage(q_image)
        return QIcon(qpix)

    def loadHistoricalPricesEvent(self, tradeList):
        #print("histPrices event trigger next call")
        self.loadHistoricalPrices(tradeList)

    def loadHistoricalPricesTimer(self, tradeList):
        #print("histPrices time trigger next call")
        self.loadHistoricalPrices(tradeList)

    def loadHistoricalPrices(self, tradeList):
        newTrades = False
        # copy trades to buffer
        for trade in tradeList:
            if not trade.valueLoaded:
                if not trade in self.tradeBuffer:
                    self.tradeBuffer.addTrade(trade)
                    newTrades = True
        numTradesToLoad = len(self.tradeBuffer)
        if numTradesToLoad > 100:
            localLogger.info("loading next 100 hist prices")
        elif numTradesToLoad > 0:
            localLogger.info("loading next " + str(numTradesToLoad) + " hist prices")
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
class UpdatePriceThread(QThread):
    coinPricesLoaded = pyqtSignal([dict, list])
    coinIconsLoaded = pyqtSignal([dict, list])
    coinPriceChartsLoaded = pyqtSignal([dict])
    historicalPricesLoaded = pyqtSignal([dict, int])

    def __init__(self, coinList, tradeList):
        super(UpdatePriceThread, self).__init__()
        self.coinList = coinList
        self.tradeList = tradeList

        self.priceTimer = QTimer()
        self.priceChartTimer = QTimer()
        self.histTimer = QTimer()
        self.iconTimer = QTimer()

        self.webApiInterface = WebApiInterface()

    def __del__(self):
        self.wait()

    def setHistTimerInterval(self, interval):
        print("set histPriceTimer: " + str(interval))
        self.histTimer.setInterval(interval)

    def setIconTimerInterval(self, interval):
        print("set iconPriceTimer: " + str(interval))
        self.iconTimer.setInterval(interval)

    def run(self):
        # return current price
        self.webApiInterface.coinPricesLoaded.connect(self.coinPricesLoaded)
        self.webApiInterface.coinIconsLoaded.connect(self.coinIconsLoaded)
        self.webApiInterface.coinPriceChartsLoaded.connect(self.coinPriceChartsLoaded)
        # return hist prices
        self.webApiInterface.historicalPricesLoaded.connect(self.historicalPricesLoaded)
        self.webApiInterface.changeHistTimerInterval.connect(self.setHistTimerInterval)
        self.webApiInterface.changeIconTimerInterval.connect(self.setIconTimerInterval)
        # load hist prices for trades
        self.tradeList.triggerHistPriceUpdate.connect(
            lambda tradeList: self.webApiInterface.loadHistoricalPricesEvent(tradeList))

        # load current prices for coins
        self.coinList.triggerPriceUpdateForCoins.connect(lambda coins: self.webApiInterface.loadPrices(coins))
        self.coinList.triggerApiUpdateForCoins.connect(lambda coins: self.webApiInterface.loadPrices(coins))
        self.coinList.triggerApiUpdateForCoins.connect(lambda coins: self.webApiInterface.loadCoinIconUrls(coins))
        self.coinList.triggerApiUpdateForCoins.connect(lambda coins: self.webApiInterface.loadcoinPriceCharts(coins, self.coinList))
        self.priceTimer.timeout.connect(lambda: self.webApiInterface.loadPrices(self.coinList.getCoinNames()))
        self.priceChartTimer.timeout.connect(
            lambda: self.webApiInterface.loadcoinPriceCharts(self.coinList.getCoinNames(), self.coinList))
        self.histTimer.timeout.connect(
            lambda: self.webApiInterface.loadHistoricalPricesTimer(self.webApiInterface.tradeBuffer))
        self.iconTimer.timeout.connect(self.webApiInterface.loadCoinIcons)

        self.priceTimer.start(int(settings.mySettings.priceUpdateInterval() * 1000))
        self.priceChartTimer.start(int(settings.mySettings.priceUpdateInterval() * 1000))
        self.iconTimer.start(10000)
        # trigger hist timer every 1s
        self.histTimer.start(1000)
        self.exec()
        self.deleteLater()
