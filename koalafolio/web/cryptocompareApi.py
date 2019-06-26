# -*- coding: utf-8 -*-


import koalafolio.web.cryptocompare as cryptcomp
# import datetime
import koalafolio.PcpCore.core as core
import koalafolio.PcpCore.settings as settings
import time
import koalafolio.PcpCore.logger as logger
from PIL import Image
from io import BytesIO
import requests


# coinList = cryptcomp.get_coin_list(format=True)
#
# price = cryptcomp.get_price(['BTC', 'ETH', 'EOS'], ['USD','EUR','BTC'])
#
# pricehist = cryptcomp.get_historical_price('ETH', ['USD','EUR','BTC'], datetime.datetime(2017,6,6))

def getHistoricalPrice(trade):
    if settings.mySettings.proxies():
        proxies = settings.mySettings.proxies()
    else:
        proxies = {}
    if trade.date:
        failedCounter = 0
        response = cryptcomp.get_historical_price(trade.coin, [key for key in settings.mySettings.displayCurrencies()], trade.date,
                                               calculationType='Close', proxies=proxies, errorCheck=False, timeout=10)
        if response:
            # check if wrong symbol
            if 'Message' in response and 'no data for the symbol' in response['Message']:
                logger.globalLogger.warning('invalid coinName: ' + str(trade.coin))
                return {}
            try:
                return response[trade.coin]
            except KeyError:
                logger.globalLogger.warning('error loading historical price for ' + str(trade.coin))
    return {}

def getCoinPrices(coins):
    if settings.mySettings.proxies():
        proxies = settings.mySettings.proxies()
    else:
        proxies = {}
    # try to load price from cryptocompare
    try:
        response = cryptcomp.get_price(coins, [key for key in core.CoinValue()], full=True, proxies=proxies, timeout=10)
    except Exception as ex:
        logger.globalLogger.warning('error loading prices: ' + str(ex))
        return {}
    if response and 'RAW' in response:
        return response['RAW']
    else:
        if response:
            logger.globalLogger.warning('error loading prices: ' + str(response))
        else:
            logger.globalLogger.warning('error loading prices')
        return {}

def getIcon(coin, *args, **kwargs):
    if settings.mySettings.proxies():
        proxies = settings.mySettings.proxies()
    else:
        proxies = {}
    coinInfo = cryptcomp.get_coin_general_info(coin, *args, **kwargs)
    try:
        imageResponse = requests.get(cryptcomp.URL_CRYPTOCOMPARE + coinInfo['Data'][0]['CoinInfo']['ImageUrl'], proxies=proxies, timeout=10)
    except:
        return None
    return Image.open(BytesIO(imageResponse.content))

def getIcons(coins, *args, **kwargs):
    if settings.mySettings.proxies():
        proxies = settings.mySettings.proxies()
    else:
        proxies = {}
    coinInfo = cryptcomp.get_coin_general_info(coins, *args, **kwargs)
    icons = {}
    try:
        for data in coinInfo['Data']:
            imageResponse = requests.get(cryptcomp.URL_CRYPTOCOMPARE + data['CoinInfo']['ImageUrl'], proxies=proxies, timeout=10)
            icons[data['CoinInfo']['Name']] = Image.open(BytesIO(imageResponse.content))
    except Exception as ex:
        logger.globalLogger.warning('error in getIcons: ' + str(ex))
    return icons
