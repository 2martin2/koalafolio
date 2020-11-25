# -*- coding: utf-8 -*-
"""
Created on Sun Sep  15 15:15:19 2019

@author: Martin
"""
import pandas as pd
import krakenex
import pykrakenapi
import datetime

# help(pykrakenapi.KrakenAPI)

def initApi(key, secret):
    api = krakenex.API(key=key, secret=secret)
    k = pykrakenapi.KrakenAPI(api)
    return k

def getTradeHistory(key, secret):
    k = initApi(key, secret)
    today = datetime.datetime.now()
    trades = []
    # get last 5 years
    for year in range(today.year-5, today.year):
        tradeHistory = k.get_trades_history(start=datetime.datetime(year=year, month=1, day=1).timestamp(),
                                            end=datetime.datetime(year=year+1, month=1, day=1).timestamp())[0]
        trades.append(tradeHistory)

    tradeHistory = k.get_trades_history(start=datetime.datetime(year=today.year, month=1, day=1).timestamp(),
                                        end=datetime.datetime.now().timestamp())[0]
    trades.append(tradeHistory)
    newTradeHistory = pd.concat(trades).reset_index()

    def removeNs(date):
        return str(date)[:-3]
    newTradeHistory['dtime'] = newTradeHistory['dtime'].apply(removeNs)
    return newTradeHistory




# k = initApi(apiKey, privateKey)

# balances = k.get_account_balance()
# assets = k.get_asset_info()
# closed_orders = k.get_closed_orders()
# ledgers = k.get_ledgers_info()
# servertime = k.get_server_time()
# trade_history = k.get_trades_history()



