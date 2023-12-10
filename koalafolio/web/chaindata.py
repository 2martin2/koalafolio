# -*- coding: utf-8 -*-
"""
Created on 29.11.2020

@author: Martin
"""

import pandas


def getCardanoRewardsForAddress(address, start, end):
    # pass None as database for now. Can cause errors. Will be catched in getApiHistory
    # api = binance.Binance(api_key=key, secret=secret.encode(),
    #                              database=None, msg_aggregator=user_messages.MessagesAggregator())
    # return getTradesFromApi(api, start, end)
    return pandas.DataFrame()