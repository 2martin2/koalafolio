# -*- coding: utf-8 -*-
"""
Created on Tue Nov 27 21:03:59 2018

@author: Martin
"""
import threading

from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QIcon
import koalafolio.gui.helper.QSettings as settings
import koalafolio.web.prices as pricesApi
import koalafolio.web.coingeckoApi as coinGecko
import koalafolio.web.cryptocompareApi as ccapi
import koalafolio.PcpCore.core as core
import koalafolio.gui.helper.QLogger as logger
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
        self.coinIconUrls = {"ccapi": {}, "coingecko": {}, "merged": {}}

        self.histApiFailedCounter = 0

    def loadPrices(self, coins: list):
        localLogger.info('loading new prices for coins: ' + str(len(coins)))
        if coins:
            if settings.mySettings.priceApiSwitch() == 'ccxt':
                prices = pricesApi.getCoinPrices(coins)     
            elif settings.mySettings.priceApiSwitch() == 'coingecko':
                prices = coinGecko.getCoinPrices(coins)
            else: # mixed
                # try coingecko first an fall back to ccxt if coingecko fails
                prices = coinGecko.getCoinPrices(coins)
                missing_coins = [coin for coin in coins if coin not in prices or not prices[coin]]
                if missing_coins:
                    localLogger.warning(f"coingecko missing prices for coins: {missing_coins}, falling back to ccxt")
                    ccxt_prices = pricesApi.getCoinPrices(missing_coins)
                    prices.update(ccxt_prices)

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
                        imagedata = None
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
                                f'error loading Icon for : {coin}, exception: {ex}')
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
            if settings.mySettings.iconApiSwitch() == 'coingecko':
                UrlTemp = coinGecko.getIconUrls(coins)
                for coin in UrlTemp:
                    self.coinIconUrls["coingecko"][coin] = UrlTemp[coin]
            elif settings.mySettings.iconApiSwitch() == 'cryptocompare':
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
            logger.globalLogger.warning(f'error in getImage for {coin}: {ex}')
            return None
        if imageResponse.status_code == 200:
            # request successful
            return imageResponse.content
        if imageResponse.status_code == 429:
            raise ConnectionRefusedError(
                f"response code: {imageResponse.status_code}, reason: {imageResponse.reason}")
        raise ConnectionError(
            f"response code: {imageResponse.status_code}, reason: {imageResponse.reason}")

    def imageToQIcon(self, imagedata):
        # Convert to QImage
        q_image = QImage()
        q_image.loadFromData(imagedata)
        # Convert to QPixmap
        qpix = QPixmap.fromImage(q_image)
        return QIcon(qpix)

    def loadHistoricalPricesEvent(self, tradeList):
        self.loadHistoricalPrices(tradeList)

    def loadHistoricalPricesTimer(self, tradeList):
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
                    if settings.mySettings.histPriceApiSwitch() == 'ccapi':
                        histPrices[trade.tradeID] = ccapi.getHistoricalPrice(trade)
                    elif settings.mySettings.histPriceApiSwitch() == 'ccxt':
                        histPrices[trade.tradeID] = pricesApi.getHistoricalPrice(trade)
                    else:  # mixed
                        histPrices[trade.tradeID] = ccapi.getHistoricalPrice(trade)
                        if not histPrices[trade.tradeID]:
                            histPrices[trade.tradeID] = pricesApi.getHistoricalPrice(trade)
                    counter += 1
            except ConnectionRefusedError:
                self.histApiFailedCounter += 1
                # save failed trade for next time
                self.tradeBuffer.trades.append(trade)
                # todo: set dynamic timer interval depending on current rate limit values
                if self.histApiFailedCounter >= 10:
                    # log
                    localLogger.warning("connectionRefused while loading historical prices repeatetly, retry api call in 10min")
                    # increase histTimerInterval to 10min
                    self.changeHistTimerInterval.emit(600000)
                else:
                    # log
                    localLogger.warning("connectionRefused while loading historical prices, retry api call in 30s")
                    # increase histTimerInterval to 30s
                    self.changeHistTimerInterval.emit(30000)
                # stop here and retry next time
                loadingStopped = True
            if counter >= 50:
                self.histApiFailedCounter = 0
                # decrease histTimerInterval to 10s
                self.changeHistTimerInterval.emit(10000)
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
                            localLogger.warning(f'no priceChartData available for {coin}')  # ignore invalid key
                        except Exception as ex:
                            localLogger.error(f'error converting priceChartData: {ex}')

                    self.coinPriceChartsLoaded.emit(coinPriceCharts)


# %% threads

class PriceUpdateThreadController(QObject):
    coinPricesLoaded = pyqtSignal(dict, list)
    coinPriceChartsLoaded = pyqtSignal(dict)

    def __init__(self, coinList):
        super().__init__()

        self.thread = QThread()
        self.worker = PriceUpdateWorker(coinList)
        self.worker.moveToThread(self.thread)

        # Thread‑Start/Stop
        self.thread.started.connect(self.worker.start)
        self.thread.finished.connect(self.worker.stop)

        # Signale weiterleiten
        self.worker.coinPricesLoaded.connect(self.coinPricesLoaded)
        self.worker.coinPriceChartsLoaded.connect(self.coinPriceChartsLoaded)

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread.quit()
        self.thread.wait()


class PriceUpdateWorker(QObject):
    coinPricesLoaded = pyqtSignal(dict, list)
    coinPriceChartsLoaded = pyqtSignal(dict)

    def __init__(self, coinList):
        super().__init__()
        self.coinList = coinList

        # Timer für Preise
        self.priceTimer = QTimer(self)
        self.priceTimer.setInterval(int(settings.mySettings.priceUpdateInterval() * 1000))

        # Timer für Charts
        self.priceChartTimer = QTimer(self)
        self.priceChartTimer.setInterval(int(settings.mySettings.priceUpdateInterval() * 1000))

    def start(self):
        # API Interface
        self.webApiInterface = WebApiInterface()

        # Signale weiterleiten
        self.webApiInterface.coinPricesLoaded.connect(self.coinPricesLoaded)
        self.webApiInterface.coinPriceChartsLoaded.connect(self.coinPriceChartsLoaded)

        # Trigger aus coinList
        self.coinList.triggerPriceUpdateForCoins.connect(self.webApiInterface.loadPrices)
        self.coinList.triggerApiUpdateForCoins.connect(self.webApiInterface.loadPrices)
        self.coinList.triggerApiUpdateForCoins.connect(
            lambda coins: self.webApiInterface.loadcoinPriceCharts(coins, self.coinList)
        )

        # Timer‑Timeouts
        self.priceTimer.timeout.connect(
            lambda: self.webApiInterface.loadPrices(self.coinList.getCoinNames())
        )
        self.priceChartTimer.timeout.connect(
            lambda: self.webApiInterface.loadcoinPriceCharts(
                self.coinList.getCoinNames(), self.coinList
            )
        )
        self.priceTimer.start()
        self.priceChartTimer.start()

    def stop(self):
        self.priceTimer.stop()
        self.priceChartTimer.stop()


class IconUpdateThreadController(QObject):
    coinIconsLoaded = pyqtSignal(dict, list)

    def __init__(self, coinList):
        super().__init__()

        self.thread = QThread()
        self.worker = IconUpdateWorker(coinList)
        self.worker.moveToThread(self.thread)

        # Thread‑Start/Stop
        self.thread.started.connect(self.worker.start)
        self.thread.finished.connect(self.worker.stop)

        # Signale weiterleiten
        self.worker.coinIconsLoaded.connect(self.coinIconsLoaded)

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread.quit()
        self.thread.wait()


class IconUpdateWorker(QObject):
    coinIconsLoaded = pyqtSignal(dict, list)

    def __init__(self, coinList):
        super().__init__()
        self.coinList = coinList

        # Timer
        self.iconTimer = QTimer(self)
        self.iconTimer.setInterval(10000)

    def start(self):
        # API Interface
        self.webApiInterface = WebApiInterface()

        # Signale weiterleiten
        self.webApiInterface.coinIconsLoaded.connect(self.coinIconsLoaded)
        self.webApiInterface.changeIconTimerInterval.connect(self.setIconTimerInterval)

        # Trigger aus coinList
        self.coinList.triggerApiUpdateForCoins.connect(self.webApiInterface.loadCoinIconUrls)

        # Timer‑Timeout
        self.iconTimer.timeout.connect(self.webApiInterface.loadCoinIcons)
        self.iconTimer.start()

    def stop(self):
        self.iconTimer.stop()

    def setIconTimerInterval(self, interval):
        self.iconTimer.setInterval(interval)


class HistoricalPriceUpdateThreadController(QObject):
    historicalPricesLoaded = pyqtSignal(dict, int)

    def __init__(self, tradeList):
        super().__init__()

        # Thread erzeugen
        self.thread = QThread()

        # Worker erzeugen
        self.worker = HistoricalPriceWorker(tradeList)

        # Worker in Thread verschieben
        self.worker.moveToThread(self.thread)

        # Thread-Start/Stop verbinden
        self.thread.started.connect(self.worker.start)
        self.thread.finished.connect(self.worker.stop)

        # Ergebnis-Signal weiterleiten
        self.worker.historicalPricesLoaded.connect(self.historicalPricesLoaded)

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread.quit()
        self.thread.wait()


class HistoricalPriceWorker(QObject):
    historicalPricesLoaded = pyqtSignal(dict, int)

    def __init__(self, tradeList):
        super().__init__()
        self.tradeList = tradeList

        # Timer lebt im Worker-Thread
        self.histTimer = QTimer(self)
        self.histTimer.setInterval(1000)

    def start(self):
        # API Interface lebt ebenfalls im Worker-Thread
        self.webApiInterface = WebApiInterface()

        # Verbindungen
        self.webApiInterface.historicalPricesLoaded.connect(self.historicalPricesLoaded)
        self.webApiInterface.changeHistTimerInterval.connect(self.setHistTimerInterval)

        self.tradeList.triggerHistPriceUpdate.connect(
            lambda tradeList: self.webApiInterface.loadHistoricalPricesEvent(tradeList)
        )

        self.histTimer.timeout.connect(
            lambda: self.webApiInterface.loadHistoricalPricesTimer(self.webApiInterface.tradeBuffer)
        )
        
        self.histTimer.start()

    def stop(self):
        self.histTimer.stop()

    def setHistTimerInterval(self, interval):
        self.histTimer.setInterval(interval)

