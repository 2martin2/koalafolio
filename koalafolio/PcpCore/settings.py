# -*- coding: utf-8 -*-
"""
Created on Thu Oct  4 15:15:19 2018

@author: VOL4ABT
"""

# todo: check why default section is written to file ?!
# todo: reinit view and data when displaycurrencies are changed during runtime

import os, ast, re
import configparser
import koalafolio.PcpCore.logger as logger


dictRegex = re.compile(r'^\{ *(\'.+\' *\: *\'.+\' *\, *)* *\'.+\' *\: *\'.+\'\ *}$')


class Settings(configparser.ConfigParser):
    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
            
    def setPath(self, path):
        self.filePath = os.path.join(path, 'settings.txt')
        # init settings
        self.initSettings()
        if not os.path.isfile(self.filePath):
            self.saveSettings()
        else:
            self.readSettings()
            self.saveSettings()
        return self

    def initSettings(self):
        # set default settings
        # general settings
        self['general'] = {}
        self['general']['version'] = '0.7.6'
        self['general']['timeModeDaywise'] = 'True'
        self['general']['priceUpdateInterval(s)'] = '100'
        # proxy settings
        self['proxies'] = {}
        self['proxies']['http'] = ''
        self['proxies']['https'] = ''
        # import settings
        self['import'] = {}
        self['import']['ignoreTradeIDs'] = 'False'
        self['import']['importFileTypes'] = '(csv|txt|xlsx|xlsm|xls|json)'
        # coin settings
        self['currency'] = {}
        self['currency']['defaultReportCurrency'] = 'EUR'
        self['currency']['defaultDisplayCurrencies'] = 'EUR,USD,BTC'
        self['currency']['isFiat'] = 'EUR,USD,GBP,JPY,CNY,RUB,AUD,CAD,SGD,PLN,HKD,CHF,INR,BRL,KRW,NZD,ZAR'
        self['currency']['coinswapdict'] = "{'HOT':'HOT*','XBT':'BTC','IOTA':'IOT'}"
        # tax settings
        self['tax'] = {}
        self['tax']['taxfreelimit'] = 'True'
        self['tax']['taxfreelimityears'] = '1'
        self['tax']['exportLanguage'] = 'en'

    def saveSettings(self):
        try:
            with open(self.filePath, 'w') as configfile:
                self.write(configfile)
            logger.globalLogger.info('settings saved')
            return True
        except Exception as ex:
            logger.globalLogger.error('error in saveSettings: ' + str(ex))
            return False

    def readSettings(self):
        try:
            self.read(self.filePath)
            self['general']['version'] = '0.7.6'
            logger.globalLogger.info('settings loaded')
        except Exception as ex:
            logger.globalLogger.error('settings can not be loaded: ' + str(ex))
            self.resetDefault()

    def resetDefault(self):
        try:
            os.remove(self.filePath)
            self.initSettings()
            self.saveSettings()
            logger.globalLogger.info('settings reset to default')
        except Exception as ex:
            print('error resetting settings: ' + str(ex))

# get/set methods
    def timeModeDaywise(self):
        return self.getboolean('general', 'timeModeDaywise')

    def priceUpdateInterval(self):
        priceUpdateInterval = self.getfloat('general', 'priceUpdateInterval(s)')
        return 2 if priceUpdateInterval <= 2 else priceUpdateInterval

    def proxies(self):
        if self['proxies']['http'] and self['proxies']['https']:
            return {'http': self['proxies']['http'], 'https': self['proxies']['https']}
        return {}

    def ignoreTradeIds(self):
        return self.getboolean('import', 'ignoreTradeIDs')

    def displayCurrencies(self):
        return self['currency']['defaultDisplayCurrencies'].split(',')
    
    def setDisplayCurrencies(self, currencies):
        self['currency']['defaultDisplayCurrencies'] = ','.join(currencies)

    def reportCurrency(self):
        # report currency should be included in display currencies, otherwise prices are not available
        if self['currency']['defaultReportCurrency'] in self.displayCurrencies():
            return self['currency']['defaultReportCurrency']
        return self.displayCurrencies()[0]

    def setReportCurrency(self, cur):
        if cur in self.displayCurrencies():
            self['currency']['defaultReportCurrency'] = cur

    def fiatList(self):
        return self['currency']['isFiat'].split(',')

    def setFiatList(self, fiatList):
        self['currency']['isFiat'] = ','.join(fiatList)

    def coinSwapDict(self):
        try:
            if dictRegex.match(self['currency']['coinswapdict']):
                return ast.literal_eval(self['currency']['coinswapdict'])
            else:
                raise SyntaxError('coinSwapList in settings.txt has invalid Syntax')
        except Exception as ex:
            return dict()
            logger.globalLogger.warning('error while parsing coinswapdict from settings: ' + str(ex))

    def taxSettings(self):
        tax = {}
        try:
            tax['taxfreelimit'] = self.getboolean('tax', 'taxfreelimit')
        except ValueError:
            tax['taxfreelimit'] = True
        try:
            tax['taxfreelimityears'] = self.getint('tax', 'taxfreelimityears')
        except ValueError:
            tax['taxfreelimityears'] = 1
        tax['exportLanguage'] = self['tax']['exportLanguage']
        return tax

    def getTaxSetting(self, key):
        tax = self.taxSettings()
        return tax[key]

    def setTaxSettings(self, tax):
        for key in tax:
            self['tax'][key] = str(tax[key])

mySettings = Settings()