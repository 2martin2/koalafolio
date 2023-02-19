# -*- coding: utf-8 -*-


import koalafolio.web.cryptocompare as cryptcomp
# import datetime
import koalafolio.PcpCore.core as core
import koalafolio.PcpCore.settings as settings
import koalafolio.PcpCore.logger as logger
from PIL import Image
from io import BytesIO
import requests
import koalafolio.web.coingeckoApi as coinGecko


# coinList = cryptcomp.get_coin_list(format=True)
#
# price = cryptcomp.get_price(['BTC', 'ETH', 'EOS'], ['USD','EUR','BTC'])
#
# pricehist = cryptcomp.get_historical_price('ETH', ['USD','EUR','BTC'], datetime.datetime(2017,6,6))

def coinSwapToCryptocompare(coin):
    if coin in settings.mySettings.coinSwapDictCryptocompare():
        return settings.mySettings.coinSwapDictCryptocompare()[coin]
    else:
        return coin

def coinSwapFromCryptoCompare(coin):
    invCoinSwapDictCryptoCompare = {v: k for k, v in settings.mySettings.coinSwapDictCryptocompare().items()}
    if coin in invCoinSwapDictCryptoCompare:
        return invCoinSwapDictCryptoCompare[coin]
    else:
        return coin

def getHistoricalPrice(trade):
    coin = coinSwapToCryptocompare(trade.coin)
    if settings.mySettings.proxies():
        proxies = settings.mySettings.proxies()
    else:
        proxies = {}
    if trade.date:
        failedCounter = 0
        response = cryptcomp.get_historical_price(coin, [key for key in settings.mySettings.displayCurrencies()], trade.date,
                                               calculationType='Close', proxies=proxies, errorCheck=False, timeout=10)
        if response:
            # check if wrong symbol
            if 'Message' in response and 'no data for the symbol' in response['Message']:
                logger.globalLogger.warning('invalid coinName: ' + str(coin))
                return {}
            try:
                return response[coin]
            except KeyError:
                if 'Message' in response and'rate limit' in response['Message']:
                    calls = response['RateLimit']['calls_made']
                    max_calls = response['RateLimit']['max_calls']
                    dif = {}
                    rateString = ""
                    for key in max_calls:
                        dif[key] = max_calls[key] - calls[key]
                        rateString += str(key) + " " + str(dif[key]) + ', '
                    logger.globalLogger.warning('cryptocompare rate limit exceeded. calls left: ' + rateString)
                    raise ConnectionRefusedError
                logger.globalLogger.warning('error loading historical price for ' + str(coin))
    return {}

def getCoinPrices(coins: list):
    ccCoins = []
    for coin in coins:
        ccCoins.append(coinSwapToCryptocompare(coin))
    if settings.mySettings.proxies():
        proxies = settings.mySettings.proxies()
    else:
        proxies = {}

    if len(ccCoins) >= 200:
        print("to many coins for cryptocompare api, using first 200")
        ccCoins = ccCoins[:200]
    # try to load price from cryptocompare
    prices = {}
    try:
        response = cryptcomp.get_price(ccCoins, [key for key in core.CoinValue()], full=True, proxies=proxies, timeout=10)
    except Exception as ex:
        logger.globalLogger.warning('error loading current prices with exception: ' + str(ex))
        return {}
    if response and 'RAW' in response:
        for ccCoin in response['RAW']:
            coin = coinSwapFromCryptoCompare(ccCoin)
            prices[ccCoin] = response['RAW'][ccCoin]
            prices[coin] = response['RAW'][ccCoin]
    else:
        if response:
            logger.globalLogger.warning('error loading current prices, api response: ' + str(response))
        else:
            logger.globalLogger.warning('error loading current prices, no response from cryptocompare api')

    return prices

def getIcon(coin, *args, **kwargs):
    if settings.mySettings.proxies():
        proxies = settings.mySettings.proxies()
    else:
        proxies = {}
    coinInfo = cryptcomp.get_coin_general_info(coinSwapToCryptocompare(coin), *args, **kwargs)
    try:
        imageResponse = requests.get(cryptcomp.URL_CRYPTOCOMPARE + coinInfo['Data'][0]['CoinInfo']['ImageUrl'], proxies=proxies, timeout=100)
    except Exception as ex:
        logger.globalLogger.warning('error in getIcon: ' + str(ex))
        return None
    return Image.open(BytesIO(imageResponse.content))

def getIcons(coins, *args, **kwargs):
    if settings.mySettings.proxies():
        proxies = settings.mySettings.proxies()
    else:
        proxies = {}
    iconUrls = getIconUrls(coins)
    icons = {}
    try:
        for coin in iconUrls:
                imageResponse = requests.get(iconUrls[coin], proxies=proxies, timeout=100)
                icons[coin] = Image.open(BytesIO(imageResponse.content))
    except Exception as ex:
        logger.globalLogger.warning('error in getIcons: ' + str(ex))
    return icons

def getIconUrls(coins, *args, **kwargs):
    ccCoins = []
    for coin in coins:
        ccCoins.append(coinSwapToCryptocompare(coin))
    if settings.mySettings.proxies():
        proxies = settings.mySettings.proxies()
    else:
        proxies = {}
    iconUrls = {}
    if len(ccCoins) >= 200:
        print("to many coins for cryptocompare api, using first 200")
        ccCoins = ccCoins[:200]
    # get icons from cryptocompare
    coinInfo = cryptcomp.get_coin_general_info(ccCoins, *args, **kwargs)
    try:
        for data in coinInfo['Data']:
            coin = coinSwapFromCryptoCompare(data['CoinInfo']['Name'])
            iconUrls[coin] = cryptcomp.URL_CRYPTOCOMPARE + data['CoinInfo']['ImageUrl']
    except Exception as ex:
        logger.globalLogger.warning('error in getIcons: ' + str(ex))
    return iconUrls
