# -*- coding: utf-8 -*-
"""
Created on 05.09.2020

@author: Martin
"""

import datetime

import koalafolio.web.coingeckoApi as coinGeckoApi
import koalafolio.PcpCore.core as core
import koalafolio.PcpCore.settings as settings
import timeit

cg = coinGeckoApi.cg
#/simple/price endpoint with the required parameters
# cg.get_price(ids='bitcoin', vs_currencies='usd')
#
# ping = cg.ping()

vsCurrencies = cg.get_supported_vs_currencies()

coinsList = cg.get_coins_list()
coinSymbolToId = {} # id=bitcoin, symbol=btc
for coin in coinsList:
    coinSymbolToId[coin['symbol']] = coin['id']
coinIdToSymbol = {}
for coin in coinsList:
    coinSymbolToId[coin['id']] = coin['symbol']

coinsMarkets = cg.get_coins_markets(vs_currency='eur')

myDatetime = datetime.datetime(year=2018, month=12, day=30, hour=12, minute=0, second=0)
priceHistory = cg.get_coin_history_by_id(id='bitcoin', date=myDatetime.date().strftime('%d-%m-%Y'), vsCurrencies=['eur', 'btc', 'eth'])
priceHistDict = priceHistory['market_data']['current_price']
price = cg.get_price(ids=['bitcoin', 'litecoin', 'ethereum'], vs_currencies=['usd', 'eur', 'btc'],
                     include_market_cap='true', include_24hr_vol='true', include_24hr_change='true', include_last_updated_at='true')

marketData = cg.get_coin_by_id(id='bitcoin', localization='false', tickers='false', market_data='false',
                                  community_data='false', developer_data='false', sparkline='false')

today = datetime.datetime.now()
marketChartData = cg.get_coin_market_chart_range_by_id(id='bitcoin', vs_currency='eur', from_timestamp=myDatetime.timestamp(), to_timestamp=today.timestamp())

# settings.mySettings.initSettings()
# #
# # myTrade = core.Trade()
# # myTrade.coin = 'HOLO'
# # myTrade.amount = 1
# # myTrade.date = datetime.datetime(year=2019, month=12, day=30, hour=12, minute=0, second=0)
# # apiHistPrice = coinGeckoApi.getHistoricalPrice(myTrade)
# #
# # # coins = ['BTC', 'ETH', 'ASDF', 'EUR']
# # allcoins = ['ETH','EUR','BTC','LTC','ADA','HOLO','EOS','LOOM','BNB','MTH','LRC','TRX','REQ','MIOTA','LINK','QSP','SUB','ZRX','DNT','ICX','NXS','STRAT','SC','DGB','XVG','SYS','DOGE','NXT','DASH','WAVES','XEM','PAY','OMG','BCH','NEO','GNT','CVC','MUSIC','BAT','RISE','SAFEX','CFI','PIVX','QTUM','XMR','LUN','NXC','SALT','KMD','BURST','POWR','XCP','BLOCK','ARDR','REP','ANT','CAS','USDT','BCN','DATA','KCS','NANO','KEY','MKR']
# # apiPrices = coinGeckoApi.getCoinPrices(allcoins)
# #
# # switch = settings.mySettings.priceApiSwitch()

# print('icons')
# start = timeit.timeit()
# icons = coinGeckoApi.getIcons(allcoins)
# end = timeit.timeit()
# print(end-start)
# print('iconsLoop')
# start = timeit.timeit()
# iconsLoop = coinGeckoApi.getIconsLoop(allcoins)
# end = timeit.timeit()
# print(end-start)
print('finish')