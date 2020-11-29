# -*- coding: utf-8 -*-
"""
Created on 29.11.2020

@author: Martin
"""

import rotkehlchen.exchanges.binance as binance
import rotkehlchen.exchanges.bittrex as bittrex
import rotkehlchen.exchanges.bitmex as bitmex
import rotkehlchen.exchanges.coinbase as coinbase
import rotkehlchen.exchanges.coinbasepro as coinbasepro
import rotkehlchen.exchanges.gemini as gemini
import rotkehlchen.exchanges.poloniex as poloniex
import rotkehlchen.exchanges.kraken as kraken
import rotkehlchen.user_messages as user_messages
import pandas
import core
import datetime

def getTradeHistoryBinance(key, secret, start, end):
    # pass None as database for now. Can cause errors. Will be catched in getApiHistory
    api = binance.Binance(api_key=key, secret=secret.encode(),
                                 database=None, msg_aggregator=user_messages.MessagesAggregator())
    return getTradesFromApi(api, start, end)


def getTradeHistoryBittrex(key, secret, start, end):
    # pass None as database for now. Can cause errors. Will be catched in getApiHistory
    api = bittrex.Bittrex(api_key=key, secret=secret.encode(),
                                 database=None, msg_aggregator=user_messages.MessagesAggregator())
    return getTradesFromApi(api, start, end)


def getTradeHistoryBitmex(key, secret, start, end):
    # pass None as database for now. Can cause errors. Will be catched in getApiHistory
    api = bitmex.Bitmex(api_key=key, secret=secret.encode(),
                                 database=None, msg_aggregator=user_messages.MessagesAggregator())
    return getTradesFromApi(api, start, end)


def getTradeHistoryCoinbase(key, secret, start, end):
    # pass None as database for now. Can cause errors. Will be catched in getApiHistory
    api = coinbase.Coinbase(api_key=key, secret=secret.encode(),
                                 database=None, msg_aggregator=user_messages.MessagesAggregator())
    return getTradesFromApi(api, start, end)


def getTradeHistoryCoinbasepro(key, secret, start, end):
    # pass None as database for now. Can cause errors. Will be catched in getApiHistory
    api = coinbasepro.Coinbasepro(api_key=key, secret=secret.encode(),
                                 database=None, msg_aggregator=user_messages.MessagesAggregator())
    return getTradesFromApi(api, start, end)


def getTradeHistoryGemini(key, secret, start, end):
    # pass None as database for now. Can cause errors. Will be catched in getApiHistory
    api = gemini.Gemini(api_key=key, secret=secret.encode(),
                                 database=None, msg_aggregator=user_messages.MessagesAggregator())
    return getTradesFromApi(api, start, end)


def getTradeHistoryPoloniex(key, secret, start, end):
    # pass None as database for now. Can cause errors. Will be catched in getApiHistory
    api = poloniex.Poloniex(api_key=key, secret=secret.encode(),
                                 database=None, msg_aggregator=user_messages.MessagesAggregator())
    return getTradesFromApi(api, start, end)


def getTradeHistoryKraken(key, secret, start, end):
    # pass None as database for now. Can cause errors. Will be catched in getApiHistory
    api = kraken.Kraken(api_key=key, secret=secret.encode(),
                                 database=None, msg_aggregator=user_messages.MessagesAggregator())
    return getTradesFromApi(api, start, end)


def getTradesFromApi(api, start, end):
    # test api key
    if api.validate_api_key()[0]:
        trades = api.query_online_trade_history(start_ts=start, end_ts=end)
        tradesDF = tradesToDataframe(trades)
        return tradesDF
    return pandas.DataFrame()


# timestamp,  location,   pair,   trade_type, amount, rate,   fee,    fee_currency,   link
def tradesToDataframe(rotkiTrades):
    trades = []
    for rotkiTrade in rotkiTrades:
        trade = {}
        trade['timestamp'] = datetime.datetime.fromtimestamp(rotkiTrade.timestamp)
        trade['location'] = rotkiTrade.location
        trade['pair'] = rotkiTrade.pair
        trade['trade_type'] = rotkiTrade.trade_type
        trade['amount'] = rotkiTrade.amount
        trade['rate'] = rotkiTrade.rate
        trade['fee'] = rotkiTrade.fee
        trade['fee_currency'] = rotkiTrade.fee_currency.symbol
        trade['link'] = rotkiTrade.link
        trades.append(trade)
    return pandas.DataFrame(trades)