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
    k = pykrakenapi.KrakenAPI(api, retry=0, crl_sleep=0)
    return k

def getTradeHistory(key, secret, start, end):
    k = initApi(key, secret)
    trades = []
    tradeHistory = k.get_trades_history(start=start, end=end)
    trades.append(tradeHistory[0])
    numTrades = len(trades[0])
    while(numTrades < tradeHistory[1]):
        tradeHistory = k.get_trades_history(start=start, end=end, ofs=numTrades)
        trades.append(tradeHistory[0])
        numTrades += len(trades[-1])
    newTradeHistory = pd.concat(trades).reset_index()

    def removeNs(date):
        return str(date)[:-3]
    try:
        newTradeHistory['dtime'] = newTradeHistory['dtime'].apply(removeNs)
    except KeyError:  # ignore key error, nothing to do in this case
        pass
    return newTradeHistory




# k = initApi(apiKey, privateKey)

# balances = k.get_account_balance()
# assets = k.get_asset_info()
# closed_orders = k.get_closed_orders()
# ledgers = k.get_ledgers_info()
# servertime = k.get_server_time()
# trade_history = k.get_trades_history()



