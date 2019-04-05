# -*- coding: utf-8 -*-


import koalafolio.web.cryptocompare as cryptcomp
# import datetime
import koalafolio.PcpCore.core as core
import koalafolio.PcpCore.settings as settings
import time
import koalafolio.PcpCore.logger as logger


# coinList = cryptcomp.get_coin_list(format=True)
#
# price = cryptcomp.get_price(['BTC', 'ETH', 'EOS'], ['USD','EUR','BTC'])
#
# pricehist = cryptcomp.get_historical_price('ETH', ['USD','EUR','BTC'], datetime.datetime(2017,6,6))

def updateTradeValue(trade):
    if settings.mySettings.proxies():
        proxies = settings.mySettings.proxies()
    else:
        proxies = {}
    if trade.date:
        failedCounter = 0
        price = None
        while (failedCounter <= 10):
            price = cryptcomp.get_historical_price(trade.coin, [key for key in trade.value.value], trade.date,
                                                   calculationType='Close', proxies=proxies, errorCheck=False)
            if trade.coin in price:
                coinPrice = core.CoinValue()
                coinPrice.fromDict(price[trade.coin])
                if 0 in coinPrice.value.values():
                    print('price update failed for ' + str(trade.toList()))
                    return False
                trade.value = coinPrice.mult(trade.amount)
                trade.valueLoaded = True
                return True
            else:
                # check if wrong symbol
                if 'Message' in price and 'no data for the symbol' in price['Message']:
                    logger.globalLogger.warning('invalid coinName: ' + str(trade.coin))
                    break
                else:
                    # if there is an error try again
                    failedCounter += 1
                    # wait some time until next try
                    time.sleep(10)
        print('price update failed for ' + str(trade.toList()))
        return False

def getHistoricalPrice(trade):
    if settings.mySettings.proxies():
        proxies = settings.mySettings.proxies()
    else:
        proxies = {}
    if trade.date:
        failedCounter = 0
        response = cryptcomp.get_historical_price(trade.coin, [key for key in trade.value.value], trade.date,
                                               calculationType='Close', proxies=proxies, errorCheck=False)
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


def updateCurrentCoinValues(coinList):
    if settings.mySettings.proxies():
        proxies = settings.mySettings.proxies()
    else:
        proxies = {}
    failedCounter = 0
    prices = None
    while (failedCounter <= 10):
        # try to load price from cryptocompare
        prices = cryptcomp.get_price(coinList.getCoinNames(), [key for key in core.CoinValue()],
                                     proxies=proxies)
        if prices:
            for coin in coinList:
                try:
                    price = core.CoinValue().fromDict(prices[coin.coinname])
                except Exception as ex:
                    print('error in updateCurrentCoinValues: ' + str(ex) + '; ' + str(prices))
                else:
                    coin.currentValue.value = price.mult(coin.balance)
            return True
        else:
            # if there is an error try again
            failedCounter += 1
            # wait some time until next try
            time.sleep(10)
    print('price update failed')
    return False

def getCoinPrices(coins):
    if settings.mySettings.proxies():
        proxies = settings.mySettings.proxies()
    else:
        proxies = {}
    # try to load price from cryptocompare
    try:
        response = cryptcomp.get_price(coins, [key for key in core.CoinValue()], full=True, proxies=proxies)
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
def update24hChange(coinList):
    if settings.mySettings.proxies():
        proxies = settings.mySettings.proxies()
    else:
        proxies = {}
    failedCounter = 0
    data = None
    while (failedCounter <= 10):
        # try to load price from cryptocompare
        data = cryptcomp.get_price(coinList.getCoinNames(), [key for key in core.CoinValue()], full=True, proxies=proxies)
        if data:
            for coin in coinList:
                try:
                    coindata = data['RAW'][coin.coinname]
                    for key in core.CoinValue():
                        coin.change24h[key] = coindata[key]['CHANGEPCT24HOUR']
                except Exception as ex:
                    print('error in get24hChange: ' + str(ex))
            return True
        else:
            # if there is an error try again
            failedCounter += 1
            # wait some time until next try
            time.sleep(10)
    print('price update failed')
    return False
