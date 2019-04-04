# -*- coding: utf-8 -*-
"""
Created on Tue Nov 27 21:03:59 2018

@author: Martin
"""
import PyQt5.QtGui as qtgui
import PyQt5.QtWidgets as qtwidgets
import PyQt5.QtCore as qtcore
import gui.QSettings as settings
import web.cryptocompareApi as ccapi
import PcpCore.core as core


class CryptoCompare(qtcore.QObject):
    coinPricesLoaded = qtcore.pyqtSignal([dict])
    historicalPricesLoaded = qtcore.pyqtSignal([dict, int])
    # historicalPriceUpdateFinished = qtcore.pyqtSignal()

    def __init__(self):
        super(CryptoCompare, self).__init__()

        # self.histPrices = {}
        self.tradeBuffer = core.TradeList()

    def loadPrices(self, coins):
        if coins:
            prices = ccapi.getCoinPrices(coins)
            self.coinPricesLoaded.emit(prices)

    def loadHistoricalPrices(self, tradeList):
        newTrades = False
        # copy trades to buffer
        if self.tradeBuffer != tradeList:
            for trade in tradeList:
                if not trade.valueLoaded:
                    self.tradeBuffer.addTrade(trade)
            # self.tradeBuffer.trades += tradeList.trades[:]
            newTrades = True
        histPrices = {}
        counter = 0
        while not self.tradeBuffer.isEmpty():
            trade = self.tradeBuffer.trades.pop()
            try:
                if not trade.valueLoaded:
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


# %% threads
class UpdatePriceThread(qtcore.QThread):
    coinPricesLoaded = qtcore.pyqtSignal([dict])
    historicalPricesLoaded = qtcore.pyqtSignal([dict, int])

    def __init__(self, coinList, tradeList):
        super(UpdatePriceThread, self).__init__()
        self.coinList = coinList
        self.tradeList = tradeList


    def __del__(self):
        self.wait()

    def run(self):
        self.cryptocompare = CryptoCompare()
        # retrun current price
        self.cryptocompare.coinPricesLoaded.connect(self.coinPricesLoaded)
        # return hist prices
        self.cryptocompare.historicalPricesLoaded.connect(self.historicalPricesLoaded)
        # load hist prices for trades
        self.tradeList.triggerHistPriceUpdate.connect(lambda tradeList: self.cryptocompare.loadHistoricalPrices(tradeList))
        # load current prices for coins
        self.coinList.coinAdded.connect(lambda coins: self.cryptocompare.loadPrices(coins))
        self.priceTimer = qtcore.QTimer()
        self.histTimer = qtcore.QTimer()
        self.priceTimer.timeout.connect(lambda: self.cryptocompare.loadPrices(self.coinList.getCoinNames()))
        self.histTimer.timeout.connect(lambda: self.cryptocompare.loadHistoricalPrices(self.cryptocompare.tradeBuffer))
        self.priceTimer.start(settings.mySettings.priceUpdateInterval()*1000)
        self.histTimer.start(100)
        self.exec()
        self.deleteLater()
