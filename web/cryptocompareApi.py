# -*- coding: utf-8 -*-


import cryptocompare.cryptocompare as cryptcomp
# import datetime
import PcpCore.core as core
import PcpCore.settings as settings
import time


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
                                                   calculationType='Close', proxies=proxies)
            if price:
                coinPrice = core.CoinValue()
                coinPrice.fromDict(price[trade.coin])
                if 0 in coinPrice.value.values():
                    print('price update failed for ' + str(trade.toList()))
                    return False
                trade.value = coinPrice.mult(trade.amount)
                trade.valueLoaded = True
                return True
            else:
                # if there is an error try again
                failedCounter += 1
                # wait some time until next try
                time.sleep(10)
        print('price update failed for ' + str(trade.toList()))
        return False


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
                    print('error in updateCurrentCoinValues: ' + str(ex))
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

def get24hChange(coinList):
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