# -*- coding: utf-8 -*-
"""
Created on Fri Aug 24 09:44:38 2018

@author: Martin
"""
import os, pandas, re
import PcpCore.core as core
import PcpCore.settings as settings
import json


def loadTrades(mypath):
    allfiles = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
    filetypes = settings.mySettings['import']['importFileTypes']
    filePattern = re.compile("^.*\." + filetypes + "$", re.IGNORECASE)
    allfilespath = [os.path.join(mypath, f) for f in allfiles if filePattern.match(str(f))]

    return loadTradesFromFiles(allfilespath)


def loadTradesFromFiles(allfilespath):
    data = []
    for i in range(len(allfilespath)):
        testread = loadTradesFromFile(allfilespath[i])
        data.append(testread)

    return [os.path.basename(file) for file in allfilespath], data


def loadTradesFromFile(filepath):
    if filepath.endswith('.txt') or filepath.endswith('.csv'):
        # try reading as csv\txt
        try:
            testread = pandas.read_csv(filepath)  # try reading with , seperation
            if len(testread.columns) < 2:  # if less than 2 columns something went wrong
                testread = pandas.read_csv(filepath, sep=';')  # try reading with ; seperation
            if len(testread.columns) < 2:  # if less than 2 columns semething went wrong
                return pandas.DataFrame()  # return empty DataFrame
            return testread
        except:
            return pandas.DataFrame()
    elif filepath.endswith('.xls') or filepath.endswith('xlsx'):
        # try reading as excelsheet
        try:
            testread = pandas.read_excel(filepath)
            if len(testread.columns) < 2:
                return pandas.DataFrame()
            return testread
        except:
            return pandas.DataFrame()
    elif filepath.endswith('.json'):
        # try reading as excelsheet
        try:
            with open(filepath, "r") as read_file:
                return json.load(read_file)
        except:
            return pandas.DataFrame()
    else:
        return pandas.DataFrame()


def convertTrades(modelList, data, files):  # convert all read csv data to tradelist
    tradeList = core.TradeList()
    feeList = core.TradeList()
    matches = []
    i = 0;
    for frame in data:  # convert every DataFrame
        print('convert ' + files[i])
        heading = frame.columns.tolist()
        trades, fees, frameMatched, skippedRows = convertTradesSingle(modelList, frame, files[i])
        if skippedRows > 0:
            print(str(skippedRows) + ' skiped in ' + str(heading))
        if frameMatched == False:
            print('no match for ' + str(heading))
        elif trades.isEmpty():
            print('no trades converted for ' + str(heading))
        else:
            tradeList.mergeTradeList(trades)
        if fees.isEmpty():
            print('no fees converted for ' + str(heading))
        else:
            feeList.mergeTradeList(fees)
        matches.append(frameMatched)
        i += 1
    return tradeList, feeList, matches


def convertTradesSingle(modelList, frame, filename):  # convert one row of read csv data to tradelist
    heading = frame.columns.tolist()
    trades = core.TradeList()
    fees = core.TradeList()
    skippedRows = 0
    frameMatched = False
    for model in modelList:  # match with every model until a match is found
        if model.isMatch(heading):
            frameMatched = True
            try:
                trades, fees, skippedRows = model.convertDataFrame(frame)  # convert frame using first matching model
                # if trades could be extracted skip other models, otherwise keep trying
                if not (trades.isEmpty() and fees.isEmpty()):
                    break
            except Exception as ex:
                # if exception occurs, try other models
                print('converting ' + str(filename) + ' failed with model :' + str(model.modelCallback) + '; ' + str(ex))

    return trades, fees, frameMatched, skippedRows
