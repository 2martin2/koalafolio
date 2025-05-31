# -*- coding: utf-8 -*-
"""
Created on Thu Aug 23 21:45:16 2018

@author: Martin
"""

# from IPython import get_ipython
# get_ipython().magic('reset -sf')

import koalafolio.Import.TradeImporter as importer
import koalafolio.Import.Converter as converter
import koalafolio.PcpCore.settings as settings
from sys import frozen, executable, argv
from os import path as os_path, dirname, getcwd, join as os_join
import koalafolio.Import.Models as models
import koalafolio.PcpCore.core as core
import koalafolio.exp.profitExport as export
from datetime import datetime

import sys
if getattr(sys, 'frozen', False):
    application_path = dirname(sys.executable)
    running_mode = 'Frozen/executable'
else:
    try:
        app_full_path = os_path.realpath(__file__)
        application_path = dirname(app_full_path)
        running_mode = "Non-interactive"
    except NameError:
        application_path = getcwd()
        running_mode = 'Interactive'

basePath = dirname(application_path)
settings = settings.mySettings.setPath(os_join(basePath, 'Data'))

# date = converter.convertDate('Fri May 19 2017 12:11:49 GMT+0200 (Mitteleuropäische Sommerzeit)')

# %% import data

importPath = os_join(basePath, 'importdata')
importPath = os_join(importPath, 'exodus_txs')
exportPath = os_join(basePath, 'exportdata')

files, content = importer.loadTrades(importPath)

headings = [frame.columns.tolist() for frame in content]
# fileheadings = []
# for i in range(len(files)):
#    fileheadings.append([files[i],headings[i]])


# %% convert data
fileindex = 0
content2 = [content[fileindex]]
file = [files[fileindex]]
tradeList, feeList, matches = importer.convertTrades(models.IMPORT_MODEL_LIST, content, files)
# tradeList.updateValues()
tradeFrame = tradeList.toDataFrameComplete()
feeFrame = feeList.toDataFrameComplete()
#
coinList = core.CoinList()
coinList.addTrades(tradeList)
coinList.addTrades(feeList)
coinList.updateCurrentValues()

coinFrame = coinList.toDataFrameComplete()
coinDict = coinFrame.to_dict('index')
