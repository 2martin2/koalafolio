# -*- coding: utf-8 -*-
"""
Created on Thu Aug 23 21:45:16 2018

@author: Martin
"""

# from IPython import get_ipython
# get_ipython().magic('reset -sf')

import Import.TradeImporter as importer
import PcpCore.settings as settings
import sys
import os
import Import.Models as models
import PcpCore.core as core
import exp.profitExport as export
import datetime

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    running_mode = 'Frozen/executable'
else:
    try:
        app_full_path = os.path.realpath(__file__)
        application_path = os.path.dirname(app_full_path)
        running_mode = "Non-interactive"
    except NameError:
        application_path = os.getcwd()
        running_mode = 'Interactive'

settings = settings.mySettings.setPath(os.path.join(application_path, 'Data'))

# %% import data
basePath = os.path.dirname(application_path)
importPath = os.path.join(basePath, 'importdata')
exportPath = os.path.join(basePath, 'exportdata')

files, content = importer.loadTrades(importPath)

headings = [frame.columns.tolist() for frame in content]
# fileheadings = []
# for i in range(len(files)):
#    fileheadings.append([files[i],headings[i]])


# %% convert data
fileindex = 17
content2 = [content[fileindex]]
file = files[fileindex]
tradeList, feeList, matches = importer.convertTrades(models.IMPORT_MODEL_LIST, content2, [file])
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
