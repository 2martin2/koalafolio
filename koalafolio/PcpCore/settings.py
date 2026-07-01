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

VERSION = '0.12.9'

class Settings(configparser.ConfigParser):
    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)

        self.initDescriptions()
            
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
        self['general']['version'] = VERSION
        self['general']['initversion'] = VERSION
        self['general']['timemodedaywise'] = 'True'
        self['general']['priceupdateinterval(s)'] = '100'
        self['general']['priceapiswitch(ccxt/coingecko/mixed)'] = 'coingecko'
        self['general']['histpriceapiswitch(ccxt/cryptocompare/mixed)'] = 'ccxt'
        self['general']['iconapiswitch(cryptocompare/coingecko/mixed)'] = 'mixed'
        self['general']['ccxt_exchanges'] = 'binance,mexc,gate'
        # proxy settings
        self['proxies'] = {}
        self['proxies']['http'] = ''
        self['proxies']['https'] = ''
        # import settings
        self['import'] = {}
        self['import']['ignoretradeids'] = 'False'
        self['import']['importfiletypes'] = '(csv|txt|xlsx|xlsm|xls|json)'
        # coin settings
        self['currency'] = {}
        self['currency']['defaultreportcurrency'] = 'EUR'
        self['currency']['defaultdisplaycurrencies'] = 'EUR,USD,BTC'
        self['currency']['isfiat'] = 'EUR,USD,GBP,JPY,CNY,RUB,AUD,CAD,SGD,PLN,HKD,CHF,INR,BRL,KRW,NZD,ZAR'
        self['currency']['coinswapdict'] = "{'XBT':'BTC'}"
        self['currency']['coinswapdictcryptocompareapi'] = "{'dummy':'dummy'}"
        self['currency']['coinswapdictcoingeckoapi'] = "{'dummy':'dummy'}"
        self['currency']['coinswapdict_ccxt_api'] = "{'dummy':'dummy'}"
        self['currency']['coinswapdictcoingeckosymboltoid'] = "{'ETH':'ethereum'}"
        # tax settings
        self['tax'] = {}
        self['tax']['taxfreelimit'] = 'True'
        self['tax']['taxfreelimityears'] = '1'
        self['tax']['exportlanguage'] = 'en'
        self['tax']['usewallettaxfreelimityears'] = 'False'
        # auth settings
        self['auth'] = {}
        self['auth']['cryptocompareapikey'] = ''

    def initDescriptions(self):
        self.descriptions = {}
        # general settings
        self.descriptions['general'] = {}
        self.descriptions['general']['version'] = 'current version'
        self.descriptions['general']['initversion'] = 'first version which created this settings'
        self.descriptions['general']['timemodedaywise'] = 'True: use avarage day prices for tax'
        self.descriptions['general']['priceupdateinterval(s)'] = 'interval of price update in seconds'
        self.descriptions['general']['priceapiswitch(ccxt/coingecko/mixed)'] = 'which api should be used for prices'
        self.descriptions['general']['histpriceapiswitch(ccxt/cryptocompare/mixed)'] = 'which api should be used for historical prices'
        self.descriptions['general']['iconapiswitch(cryptocompare/coingecko/mixed)'] = 'which api should be used for icons, mixed is recommended'
        self.descriptions['general']['ccxt_exchanges'] = 'which exchanges to use for CCXT prices, comma separated list. Only exchanges that are supported by CCXT and have a public API can be used. Examples: binance, mexc, bingx, gate, htx, kucoin, kraken'
        # proxy settings
        self.descriptions['proxies'] = {}
        self.descriptions['proxies']['http'] = ''
        self.descriptions['proxies']['https'] = ''
        # import settings
        self.descriptions['import'] = {}
        self.descriptions['import']['ignoretradeids'] = 'True: trade Ids are ignored during import. Trade Ids can help to prevent double import of same trade but some exchanges use the same id for subtrades/ partial execution.'
        self.descriptions['import']['importfiletypes'] = 'file endings that shell be considered for file import'
        # coin settings
        self.descriptions['currency'] = {}
        self.descriptions['currency']['defaultreportcurrency'] = 'default currency for portfolio and tax reporting'
        self.descriptions['currency']['defaultdisplaycurrencies'] = 'display currencies for portfolio. defaultReportCurrency has to be included'
        self.descriptions['currency']['isfiat'] = 'coin symbols that should be considered fiat money'
        self.descriptions['currency']['coinswapdict'] = "coin symbols that should be switched during import (e.g. XBT to BTC)"
        self.descriptions['currency']['coinswapdictcryptocompareapi'] = "swap coin symbol when loading prices from cryptocompare"
        self.descriptions['currency']['coinswapdictcoingeckoapi'] = "swap coin symbol when loading prices from coingecko"
        self.descriptions['currency']['coinswapdict_ccxt_api'] = "swap coin symbol when loading prices from ccxt"
        self.descriptions['currency']['coinswapdictcoingeckosymboltoid'] = "manual mapping of coin symbol to coingecko id. some coin symbols are not exclusive on coingecko"
        # tax settings
        self.descriptions['tax'] = {}
        self.descriptions['tax']['taxfreelimit'] = 'global switch to enable hodl limit after that trades are tax free. (e.g. 1 year in Germany)'
        self.descriptions['tax']['taxfreelimityears'] = 'number of years until trades are tax free. (e.g. 1 year in Germany). Only used if usewallettaxfreelimityears is False'
        self.descriptions['tax']['exportlanguage'] = 'default language of tax report'
        self.descriptions['tax']['usewallettaxfreelimityears'] = 'True: use seperate taxfreelimityears for every wallet. False: use global setting taxfreelimityears.'
        # auth settings
        self.descriptions['auth'] = {}
        self.descriptions['auth']['cryptocompareapikey'] = 'api key for cryptocompare api. can be generated on https://min-api.cryptocompare.com/pricing. without api key cryptocompare api is not working anymore'

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
            self['general']['version'] = VERSION
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
            logger.globalLogger.error('error resetting settings: ' + str(ex))

# get/set methods
    def timeModeDaywise(self):
        return self.getboolean('general', 'timemodedaywise')

    def priceUpdateInterval(self):
        priceUpdateInterval = self.getfloat('general', 'priceupdateinterval(s)')
        return 2 if priceUpdateInterval <= 2 else priceUpdateInterval

    def priceApiSwitch(self):
        return self['general']['priceapiswitch(ccxt/coingecko/mixed)']

    def iconApiSwitch(self):
        return self['general']['iconapiswitch(cryptocompare/coingecko/mixed)']
    
    def ccxtExchanges(self):
        return self['general']['ccxt_exchanges'].split(',')

    def histPriceApiSwitch(self):
        return self['general']['histpriceapiswitch(ccxt/cryptocompare/mixed)']

    def proxies(self):
        if self['proxies']['http'] and self['proxies']['https']:
            return {'http': self['proxies']['http'], 'https': self['proxies']['https']}
        return {}

    def ignoreTradeIds(self):
        return self.getboolean('import', 'ignoretradeids')

    def displayCurrencies(self):
        return self['currency']['defaultdisplaycurrencies'].upper().split(',')
    
    def setDisplayCurrencies(self, currencies):
        self['currency']['defaultdisplaycurrencies'] = ','.join(currencies)

    def reportCurrency(self):
        # report currency should be included in display currencies, otherwise prices are not available
        if self['currency']['defaultreportcurrency'] in self.displayCurrencies():
            return self['currency']['defaultreportcurrency']
        logger.globalLogger.warning('defaultreportcurrency is not part of defaultdisplaycurrencies. First displayCurrency will be used for reports.')
        return self.displayCurrencies()[0]

    def setReportCurrency(self, cur):
        if cur in self.displayCurrencies():
            self['currency']['defaultreportcurrency'] = cur

    def fiatList(self):
        return self['currency']['isFiat'].split(',')

    def setFiatList(self, fiatList):
        self['currency']['isFiat'] = ','.join(fiatList)

    def coinSwapDict(self):
        try:
            if dictRegex.match(self['currency']['coinswapdict']):
                return ast.literal_eval(self['currency']['coinswapdict'])
            else:
                raise SyntaxError('coinswapdict in settings.txt has invalid Syntax')
        except Exception as ex:
            logger.globalLogger.warning('error while parsing coinswapdict from settings: ' + str(ex))
        return dict()

    def coinSwapDictCryptocompare(self):
        try:
            if dictRegex.match(self['currency']['coinswapdictcryptocompareapi']):
                return ast.literal_eval(self['currency']['coinswapdictcryptocompareapi'])
            else:
                raise SyntaxError('coinswapdictcryptocompareapi in settings.txt has invalid Syntax')
        except Exception as ex:
            logger.globalLogger.warning('error while parsing coinswapdictcryptocompareapi from settings: ' + str(ex))
        return dict()

    def coinSwapDictCoinGecko(self):
        try:
            if dictRegex.match(self['currency']['coinswapdictcoingeckoapi']):
                return ast.literal_eval(self['currency']['coinswapdictcoingeckoapi'])
            else:
                raise SyntaxError('coinswapdictcoingeckoapi in settings.txt has invalid Syntax')
        except Exception as ex:
            logger.globalLogger.warning('error while parsing coinswapdictcoingeckoapi from settings: ' + str(ex))
        return dict()
    
    def coinSwapDictCcxt(self):
        try:
            if dictRegex.match(self['currency']['coinswapdict_ccxt_api']):
                return ast.literal_eval(self['currency']['coinswapdict_ccxt_api'])
            else:
                raise SyntaxError('coinswapdict_ccxt_api in settings.txt has invalid Syntax')
        except Exception as ex:
            logger.globalLogger.warning('error while parsing coinswapdict_ccxt_api from settings: ' + str(ex))
        return dict()

    def coinSwapDictCoinGeckoSymbolToId(self):
        try:
            if dictRegex.match(self['currency']['coinswapdictcoingeckosymboltoid']):
                return ast.literal_eval(self['currency']['coinswapdictcoingeckosymboltoid'])
            else:
                raise SyntaxError('coinswapdictcoingeckosymboltoid in settings.txt has invalid Syntax')
        except Exception as ex:
            logger.globalLogger.warning('error while parsing coinswapdictcoingeckosymboltoid from settings: ' + str(ex))
        return dict()

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
        try:
            tax['usewallettaxfreelimityears'] = self.getboolean('tax', 'usewallettaxfreelimityears')
        except ValueError:
            tax['usewallettaxfreelimityears'] = False
        return tax

    def getTaxSetting(self, key):
        tax = self.taxSettings()
        return tax[key]

    def setTaxSettings(self, tax):
        for key in tax:
            self['tax'][key] = str(tax[key])

    def cryptocompareApiKey(self):
        return self['auth']['cryptocompareapikey']

mySettings = Settings()