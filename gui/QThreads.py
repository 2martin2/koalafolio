# -*- coding: utf-8 -*-
"""
Created on Tue Nov 27 21:03:59 2018

@author: Martin
"""
import PyQt5.QtGui as qtgui
import PyQt5.QtWidgets as qtwidgets
import PyQt5.QtCore as qtcore
import time
import gui.QSettings as settings


# %% threads
class UpdateCoinPriceThread(qtcore.QThread):
    updateFinished = qtcore.pyqtSignal()

    def __init__(self, coinList):
        super(UpdateCoinPriceThread, self).__init__()
        self.coinList = coinList

    def __del__(self):
        self.wait()

    def run(self):
        while 1:
            time.sleep(2)
            if not (self.coinList.isEmpty()):
                self.coinList.updateCurrentValues()
                self.coinList.update24hChange()
                self.updateFinished.emit()
            time.sleep(settings.mySettings.priceUpdateInterval() - 2)

class UpdateCoinPriceThreadSingle(qtcore.QThread):
    updateFinished = qtcore.pyqtSignal()

    def __init__(self, coinList):
        super(UpdateCoinPriceThreadSingle, self).__init__()
        self.coinList = coinList

    def run(self):
            if not (self.coinList.isEmpty()):
                self.coinList.updateCurrentValues()
                self.coinList.update24hChange()
                self.updateFinished.emit()


class UpdateTradePriceThread(qtcore.QThread):
    tradePricesUpdated = qtcore.pyqtSignal()

    def __init__(self, tradeList):
        super(UpdateTradePriceThread, self).__init__()
        self.tradeList = tradeList

    def run(self):
        if not (self.tradeList.isEmpty()):
            self.tradeList.updateValues()
            self.tradePricesUpdated.emit()
