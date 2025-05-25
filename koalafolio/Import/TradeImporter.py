# -*- coding: utf-8 -*-
"""
Created on Fri Aug 24 09:44:38 2018

@author: Martin
"""
import os, pandas, re
import koalafolio.PcpCore.core as core
import koalafolio.PcpCore.settings as settings
import koalafolio.Import.Converter as converter
import json
import koalafolio.PcpCore.logger as logger

localLogger = logger.globalLogger


def loadTrades(mypath):
    allfiles = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
    filetypes = settings.mySettings['import']['importFileTypes']
    filePattern = re.compile(r"^.*\." + filetypes + "$", re.IGNORECASE)
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
        # get encoding
        encodings = ['utf_8', 'utf_7', 'utf_16', 'utf_16_le', 'utf_16_be', 'utf_32', 'utf_32_le', 'utf_32_be']
        encodingError = True
        for encoding in encodings:
            try:
                testread = pandas.read_csv(filepath, encoding=encoding)  # try reading with , seperation
                if len(testread.columns) < 2:  # if less than 2 columns something went wrong
                    testread = pandas.read_csv(filepath, sep=';',
                                               encoding=encoding)  # try reading with ; seperation
                if len(testread.columns) < 2:  # if less than 2 columns something went wrong
                    raise SyntaxError('columns of csv could not be detected')
                return testread
            except UnicodeDecodeError as ex:
                pass
            except Exception as ex:
                encodingError = False
                localLogger.warning('error reading ' + filepath + ' as csv: ' + str(ex))
        if encodingError:
            localLogger.warning('encoding of ' + str(filepath) + ' is not supported')
            localLogger.info('supported encodings: ' + str(encodings))

    if filepath.endswith('.xls') or filepath.endswith('xlsx'):
        # try reading as excelsheet
        try:
            testread = pandas.read_excel(filepath)
            if len(testread.columns) < 2:
                raise SyntaxError('file cannot be imported as excelsheet')
            return testread
        except:
            pass
    if filepath.endswith('.json') or filepath.endswith('.txt'):
        # try reading as excelsheet
        try:
            with open(filepath, "r") as read_file:
                jsonData = json.load(read_file)
            try:
                dataFrame = converter.exodusJsonToDataFrame(jsonData)
                if dataFrame.shape[0] == 0:
                    raise SyntaxError('file cannot be converted as exodus json')
                return dataFrame
            except:  # try other converters
                pass
        except:
            pass

    return pandas.DataFrame()


def convertTrades(modelList, data, files):  # convert all read csv data to tradelist
    tradeList = core.TradeList()
    feeList = core.TradeList()
    matches = []
    i = 0
    for frame in data:  # convert every DataFrame
        localLogger.info('convert ' + files[i])
        heading = frame.columns.tolist()
        trades, fees, frameMatched, skippedRows = convertTradesSingle(modelList, frame, files[i])
        if skippedRows > 0:
            localLogger.info(str(skippedRows) + ' skiped in ' + str(heading))
        if frameMatched == False:
            localLogger.info('no match for ' + str(heading))
        elif trades.isEmpty():
            localLogger.info('no trades converted for ' + str(heading))
        else:
            tradeList.mergeTradeList(trades)
        if fees.isEmpty():
            localLogger.info('no fees converted for ' + str(heading))
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
                #if exception occurs, try other models
                localLogger.warning('converting ' + str(filename) + ' failed with model :' + str(model.modelCallback) + '; ' + str(ex))

    return trades, fees, frameMatched, skippedRows
