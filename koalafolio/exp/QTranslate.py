# -*- coding: utf-8 -*-
"""
Created on Fri May 31 08:17:21 2019

@author: Martin
"""

import configparser
import koalafolio.gui.helper.QLogger as logger
import os

localLogger = logger.globalLogger

class ExportTranslator(configparser.ConfigParser):
    def __init__(self, dataPath="", *args, **kwargs):
        super(ExportTranslator, self).__init__(self, *args, **kwargs)

        if dataPath:
            self.setPath(dataPath)

    def setPath(self, path):
        self.filePath = os.path.join(path, 'translation.txt')
        # init settings
        self.initTranslation()
        if not os.path.isfile(self.filePath):
            self.saveTranslation()
        else:
            self.readTranslation()
            self.saveTranslation()
        return self

    def initTranslation(self):
        # set default settings
        # en
        self['en'] = {}
        self['en']['Profit'] = 'Profit'
        self['en']['Timeframe'] = 'Timeframe'
        self['en']['in'] = 'in'
        self['en']['of'] = 'of'
        self['en']['Group'] = 'Group'
        self['en']['Buy'] = 'Buy'
        self['en']['Sell'] = 'Sell'
        self['en']['Date'] = 'Date'
        self['en']['Amount'] = 'Amount'
        self['en']['Price'] = 'Price'
        self['en']['Value'] = 'Value'
        self['en']['tax_relevant'] = 'tax relevant'
        self['en']['Trades'] = 'Trades'
        self['en']['Trade'] = 'Trade'
        self['en']['Fees'] = 'Fees'
        self['en']['Fee'] = 'Fee'
        self['en']['Rewards'] = 'Rewards'
        self['en']['Reward'] = 'Reward'
        self['en']['pc'] = 'pc'
        self['en']['Page'] = 'Page'
        # de
        self['de'] = {}
        self['de']['Profit'] = 'Gewinn'
        self['de']['Timeframe'] = 'Zeitraum'
        self['de']['in'] = 'in'
        self['en']['of'] = 'von'
        self['de']['Group'] = 'Gruppe'
        self['de']['Buy'] = 'Ankauf'
        self['de']['Sell'] = 'Verkauf'
        self['de']['Date'] = 'Datum'
        self['de']['Amount'] = 'Anzahl'
        self['de']['Price'] = 'Preis'
        self['de']['Value'] = 'Wert'
        self['de']['tax_relevant'] = 'zu versteuern'
        self['de']['Trades'] = 'Trades'
        self['de']['Trade'] = 'Trade'
        self['de']['Fees'] = 'Gebühren'
        self['de']['Fee'] = 'Gebühr'
        self['de']['Rewards'] = 'Entlohnungen'
        self['de']['Reward'] = 'Entlohnung'
        self['de']['pc'] = 'stk'
        self['en']['Page'] = 'Seite'

    def saveTranslation(self):
        try:
            with open(self.filePath, 'w') as configfile:
                self.write(configfile)
            logger.globalLogger.info('translation saved')
            return True
        except Exception as ex:
            logger.globalLogger.error('error in saveTranslation: ' + str(ex))
            return False

    def readTranslation(self):
        try:
            self.read(self.filePath)
            logger.globalLogger.info('translation loaded')
        except Exception as ex:
            logger.globalLogger.error('translations can not be loaded: ' + str(ex))
            self.resetDefault()

    def resetDefault(self):
        try:
            os.remove(self.filePath)
            self.initTranslation()
            self.saveTranslation()
            logger.globalLogger.info('translations reset to default')
        except Exception as ex:
            localLogger.warning('error resetting translations: ' + str(ex))

    def getLanguages(self):
        return [l for l in self if l != "DEFAULT"]

    def translate(self, text, lang):
        try:
            return self[lang][text.replace(' ', '_')]
        except KeyError:
            return text