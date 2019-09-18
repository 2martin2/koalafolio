# -*- coding: utf-8 -*-
"""
Created on Sun Sep  15 15:15:19 2019

@author: Martin
"""
import koalafolio.gui.QLogger as logger
import koalafolio.web.krakenApi as krakenApi
import pandas

localLogger = logger.globalLogger

apiNames = ["kraken"]
apiHandle = {}
apiHandle["kraken"] = lambda key, secret: krakenApi.getTradeHistory(key, secret)

def getApiHistory(apiname, key, secret):
    if apiname not in apiNames:
        raise KeyError("invalid api name")
    else:
        try:
            return apiHandle[apiname](key, secret)
        except Exception as ex:
            localLogger.warning("could not load data from api: " + str(ex))
            return pandas.DataFrame()
