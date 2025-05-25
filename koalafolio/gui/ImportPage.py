# -*- coding: utf-8 -*-
"""
Created on 11.04.2021

@author: Martin
"""

import PyQt5.QtWidgets as qtwidgets
import PyQt5.QtCore as qtcore
import koalafolio.gui.Qcontrols as controls
import koalafolio.Import.TradeImporter as importer
import koalafolio.Import.Models as models
import koalafolio.gui.QTradeTable as ttable
import koalafolio.gui.FilterableTable as ftable
import os
import re
import pandas
import koalafolio.gui.QSettings as settings
import datetime
from pathlib import Path
import koalafolio.gui.QLogger as logger
import koalafolio.Import.apiImport as apiImport
import koalafolio.gui.QApiImport as qApiImport
import koalafolio.gui.QStyle as style
from koalafolio.gui.Qpages import Page, SubPage
import koalafolio.gui.ScrollableTable as sTable

qt = qtcore.Qt
localLogger = logger.globalLogger

# %% import page for importing csv, txt, xls ...
class ImportPage(Page):
    IMPORTSELECTPAGEINDEX = 0
    IMPORTPREVIEWPAGEINDEX = 1
    IMPORTFINISHPAGEINDEX = 2

    def __init__(self, parent, controller):
        super(ImportPage, self).__init__(parent=parent, controller=controller)

        self.initData()

        # %%  stacked Layout for import pages
        self.importSelectPage = ImportSelectPage(parent=self, controller=self)
        self.importPreviewPage = ImportPreviewPage(parent=self, controller=self)
        self.controller.startRefresh.connect(self.importPreviewPage.clearLabelStyle)
        self.controller.endRefresh.connect(self.importPreviewPage.setLabelStyle)
        self.importFinishPage = ImportFinishPage(parent=self, controller=self)
        self.controller.startRefresh.connect(self.importFinishPage.clearLabelStyle)
        self.controller.endRefresh.connect(self.importFinishPage.setLabelStyle)
        self.pages = [self.importSelectPage, self.importPreviewPage, self.importFinishPage]
        self.stackedContentLayout = qtwidgets.QStackedLayout(self)
        for page in self.pages:
            # stacked content layout
            self.stackedContentLayout.addWidget(page)

        self.refresh()

    def initData(self):
        self.newTradesBuffer = ttable.QImportTradeTableModel(baseModel=self.controller.tradeList)
        self.newTradesBuffer.showPrices(False)
        self.newTradesBuffer.columnNotEditable = [0, 1]
        self.skippedRows = 0
        self.importedRows = 0
        self.filesNotImported = 0
        self.filesImported = 0
        self.allFilesPath = []

    # refresh page whenever it gets activated
    def refresh(self):
        self.clearNewTrades()
        self.skippedRows = 0
        self.importedRows = 0
        self.filesNotImported = 0
        self.filesImported = 0
        self.showFrame(self.IMPORTSELECTPAGEINDEX)

    # show a frame by index
    def showFrame(self, pageIndex):
        '''Show a frame for the given page name'''
        frame = self.pages[pageIndex]
        frame.refresh()
        self.stackedContentLayout.setCurrentIndex(pageIndex)

    # get selected path
    def getPath(self):
        return self.importSelectPage.getPath()

    def getFilesPath(self):
        return self.allFilesPath

    def setFilesPath(self, files):
        self.allFilesPath = files

    def getNewTrades(self):
        return self.newTradesBuffer

    def clearNewTrades(self):
        self.newTradesBuffer.clearTrades()

    def finishImport(self):
        self.controller.tradeList.addTrades(self.getNewTrades())
        # jump to TradesPage
        self.controller.showFrame(self.controller.TRADESPAGEINDEX)



class ImportSelectPage(SubPage):
    def __init__(self, parent, controller):
        super(ImportSelectPage, self).__init__(parent=parent, controller=controller)

        # file types
        filetypes = settings.mySettings['import']['importFileTypes']
        self.filePattern = re.compile(r"^.*\." + filetypes + "$", re.IGNORECASE)

        # Left Frame
        self.fileFrame = controls.StyledFrame(self)
        self.fileImportLabel = controls.Heading('File import', self.fileFrame)

        # enter path
        self.pathEntry = controls.PathInput(self.fileFrame)
        self.pathEntry.textChanged.connect(self.pathChanged)

        # file system view
        self.fileSystemModel = qtwidgets.QFileSystemModel()
        self.fileSystemModel.setRootPath(qtcore.QDir.currentPath())

        self.treeView = sTable.QScrollableTreeView(self.fileFrame)
        self.treeView.setModel(self.fileSystemModel)
        self.treeView.setSelectionMode(qtwidgets.QAbstractItemView.ExtendedSelection)
        self.treeView.header().setSectionResizeMode(qtwidgets.QHeaderView.ResizeToContents)
        self.treeView.selectionModel().selectionChanged.connect(self.selectionChangedCallback)

        self.treeView.setRootIndex(self.fileSystemModel.index(qtcore.QDir.currentPath()))

        # controls
        self.templateFileDialog = qtwidgets.QFileDialog(self.fileFrame)
        self.templateButton = qtwidgets.QPushButton("create template", self.fileFrame)
        self.templateButton.clicked.connect(self.createTemplate)

        self.previewButton = qtwidgets.QPushButton("preview", self.fileFrame)
        self.previewButton.clicked.connect(self.showPreviewFrame)

        self.fastImportButton = qtwidgets.QPushButton("fast import", self.fileFrame)
        self.fastImportButton.clicked.connect(self.showImportFinishedFrame)

        self.horzButtonLayout = qtwidgets.QHBoxLayout()
        self.horzButtonLayout.addStretch()
        self.horzButtonLayout.addWidget(self.templateButton)
        self.horzButtonLayout.addWidget(self.previewButton)
        self.horzButtonLayout.addWidget(self.fastImportButton)
        self.horzButtonLayout.addStretch()

        # file import layout
        self.fileLayout = qtwidgets.QVBoxLayout(self.fileFrame)
        self.fileLayout.addWidget(self.fileImportLabel)
        self.fileLayout.addWidget(self.pathEntry)
        self.fileLayout.addWidget(self.treeView)
        self.fileLayout.addLayout(self.horzButtonLayout)

        # api import
        self.apiModel = qApiImport.ApiKeyModel(controller.controller.apiUserDatabase,
                                               controller.controller.apiDefaultDatabase.data)
        self.apiView = qApiImport.ApiKeyView(parent=self)
        self.apiView.setModel(self.apiModel)
        self.apiView.importFromApi.connect(self.importFromApi)
        self.apiView.saveFromApi.connect(self.saveFromApi)

        self.saveCsvFileDialog = qtwidgets.QFileDialog(self)

        # page layout
        self.horzLayout = qtwidgets.QHBoxLayout(self)
        self.horzLayout.addWidget(self.fileFrame)
        self.horzLayout.addWidget(self.apiView)

        self.pathEntry.setPath(qtcore.QDir.currentPath())

    def refresh(self):
        # file types
        filetypes = settings.mySettings['import']['importFileTypes']
        self.filePattern = re.compile(r"^.*\." + filetypes + "$", re.IGNORECASE)

        self.controller.skippedRows = 0
        self.controller.importedRows = 0
        self.controller.filesNotImported = 0
        self.controller.filesImported = 0
        self.controller.clearNewTrades()

    def pathChanged(self):
        if (self.pathEntry.pathIsValid()):
            try:
                path = self.getPath()
                if (path.is_file()):
                    self.treeView.selectionModel().select(qtcore.QModelIndex(), qtcore.QItemSelectionModel.Clear)
                    self.fileSystemModel.setRootPath(str(os.path.dirname(path)))
                    self.treeView.setRootIndex(self.fileSystemModel.index(str(os.path.dirname(path))))
                    self.treeView.header().setSectionResizeMode(qtwidgets.QHeaderView.ResizeToContents)
                    self.treeView.selectionModel().select(self.fileSystemModel.index(str(path)),
                                                          qtcore.QItemSelectionModel.Select)
                elif (path.is_dir()):
                    self.treeView.selectionModel().select(qtcore.QModelIndex(), qtcore.QItemSelectionModel.Clear)
                    self.fileSystemModel.setRootPath(str(path))
                    self.treeView.setRootIndex(self.fileSystemModel.index(str(path)))
                    self.treeView.header().setSectionResizeMode(qtwidgets.QHeaderView.ResizeToContents)
                    self.treeView.selectionModel().select(self.fileSystemModel.index(str(path)),
                                                          qtcore.QItemSelectionModel.Select)
                else:
                    self.controller.setFilesPath([])
            except Exception as ex:
                localLogger.warning("pathChanged callback failed: " + str(ex))

    def selectionChangedCallback(self):
        self.controller.allFilesPath = []
        indexes = self.treeView.selectionModel().selectedIndexes()
        self.filePaths = []
        for index in indexes:
            if index.column() == 0:
                path = Path(self.fileSystemModel.filePath(index))
                if path.is_file():
                    self.controller.allFilesPath.append(str(path))
                if path.is_dir():
                    files = [os.path.join(str(path), str(f)) for f in path.iterdir() if self.filePattern.match(str(f))]
                    self.controller.allFilesPath += files

    # show preview frame and refresh data
    def showPreviewFrame(self):
        if (self.controller.getFilesPath()):
            self.controller.showFrame(self.controller.IMPORTPREVIEWPAGEINDEX)
        else:
            localLogger.info('please select at least one valid file')

    def importFromApi(self, api, apitype, start, end, apikey, secret, addressList):
        self.controller.skippedRows = 0
        self.controller.importedRows = 0
        self.controller.filesNotImported = 0
        self.controller.filesImported = 0
        self.controller.clearNewTrades()
        content = self.getApiContent(api, apitype, start, end, apikey, secret, addressList)

        if not content.empty:
            tradeListTemp, feeListTemp, match, skippedRows = importer.convertTradesSingle(
                models.IMPORT_MODEL_LIST, content, api)
            # check import
            if match:
                self.controller.newTradesBuffer.mergeTradeList(tradeListTemp)
                self.controller.newTradesBuffer.mergeTradeList(feeListTemp)
                self.controller.importedRows += len(tradeListTemp.trades)
                self.controller.skippedRows += skippedRows
                self.controller.filesImported += 1

                if not (self.controller.getNewTrades().isEmpty()):
                    self.controller.showFrame(self.controller.IMPORTFINISHPAGEINDEX)
                else:
                    localLogger.info("no valid data received from api")
            else:
                localLogger.info("data from API could not be converted")
        else:
            localLogger.info("no data received from api")

    def saveFromApi(self, api, apitype, start, end, apikey, secret, addressList):
        content = self.getApiContent(api, apitype, start, end, apikey, secret, addressList)
        if not content.empty:
            self.saveCsvFileDialog.setDefaultSuffix("csv")
            filename = api + '_api.csv'
            pathReturn = self.saveCsvFileDialog.getSaveFileName(self, "save file", filename, "CSV (*.csv *.txt)")
            if pathReturn[0]:
                content.to_csv(pathReturn[0])
            else:
                localLogger.warning("invalid path: " + str(pathReturn[0]))
        else:
            localLogger.info("no data received from api")

    def getApiContent(self, api, apitype, start, end, apikey, secret, addressList):
        if apitype == "chaindata":
            content = None
            for address in addressList:
                newContent = apiImport.getApiHistory(api, apitype, start, end, apikey=apikey, secret=secret,
                                                  address=address)
                if not newContent.empty:
                    if content is None:
                        content = newContent
                    else:
                        content = content.merge(newContent)
            if content is None:
                content = pandas.DataFrame()
        else:
            content = apiImport.getApiHistory(api, apitype, start, end, apikey=apikey, secret=secret, address="")
        return content

    # skip preview and show import finished page
    def showImportFinishedFrame(self):
        self.controller.skippedRows = 0
        self.controller.importedRows = 0
        self.controller.filesNotImported = 0
        self.controller.filesImported = 0
        self.controller.clearNewTrades()
        if self.controller.getFilesPath():
            # import files
            for file in self.controller.getFilesPath():
                content = importer.loadTradesFromFile(file)
                if not content.empty:
                    tradeListTemp, feeListTemp, match, skippedRows = importer.convertTradesSingle(
                        models.IMPORT_MODEL_LIST, content, file)
                    # check import
                    if match:
                        self.controller.newTradesBuffer.mergeTradeList(tradeListTemp)
                        self.controller.newTradesBuffer.mergeTradeList(feeListTemp)
                        self.controller.importedRows += len(tradeListTemp.trades)
                        self.controller.skippedRows += skippedRows
                        self.controller.filesImported += 1
                    else:
                        self.controller.filesNotImported += 1
                else:
                    self.controller.filesNotImported += 1
            if not (self.controller.getNewTrades().isEmpty()):
                self.controller.showFrame(self.controller.IMPORTFINISHPAGEINDEX)
            else:
                localLogger.info('please select at least one valid file')

        else:
            localLogger.info('please select at least one valid file')

    def getPath(self):
        return self.pathEntry.getPath()

    def createTemplate(self):
        self.templateFileDialog.setDefaultSuffix("txt")
        filename = 'template.txt'
        pathReturn = self.templateFileDialog.getSaveFileName(self, "save file", filename, "CSV (*.csv *.txt)")
        if pathReturn[0]:
            with open(pathReturn[0], 'w') as file:
                for model in models.IMPORT_MODEL_LIST:
                    if model.modelName == 'Template1':
                        file.write(','.join([x for x in model.modelHeaders]) + '\n')
                        break
                #"date", "type", "buy amount", "buy cur", "sell amount", "sell cur", ("exchange"),
                # ("fee amount"), ("fee currency"), ("buy_wallet"), ("sell_wallet")
                rows = []
                rows.append([datetime.datetime.now(), 'trade', 10, 'ETH', 0.5, 'BTC', 'binance', 0.01, 'ETH', '', ''])
                rows.append([datetime.datetime.now(), 'trade', 5, 'ETH', 0.25, 'BTC', '', '', '', ''])
                rows.append([datetime.datetime.now(), 'trade', 20, 'ETH', 1, 'BTC', '', 0.0001, 'BTC', '', ''])
                rows.append([datetime.datetime.now(), 'fee', '', '', '', '', '', 0.0015, 'ETH', '', ''])
                rows.append([datetime.datetime.now(), 'trade', 50000, 'ADA', 20000, 'USD', 'kraken', '', '', 'Hodl_1', ''])
                rows.append([datetime.datetime.now(), 'trade', 100000, 'ADA', 50000, 'USD', 'kraken', '', '', 'Staking_1', ''])
                rows.append([datetime.datetime.now(), 'reward', 1000, 'ADA', 1000, 'USD', '', '', '', 'Staking_1', ''])
                for row in rows:
                    file.write(','.join([str(x) for x in row]) + '\n')
                file.close()



class ImportPreviewPage(SubPage):
    def __init__(self, parent, controller):
        super(ImportPreviewPage, self).__init__(parent=parent, controller=controller)

        # create empty buffer for file path
        self.initData()

        # create info frame
        self.infoFrame = controls.StyledFrame(self, height=20)
        self.fileNameLabel = qtwidgets.QLabel("FileName", self.infoFrame)
        self.infoLabel = qtwidgets.QLabel("", self.infoFrame)

        self.infoLayout = qtwidgets.QHBoxLayout(self.infoFrame)
        self.infoLayout.addWidget(self.fileNameLabel)
        self.infoLayout.addSpacerItem(qtwidgets.QSpacerItem(10, 10))
        self.infoLayout.addWidget(self.infoLabel)
        self.legendWhiteLabel = qtwidgets.QLabel("white: new trades", self)
        self.legendGrayLabel = qtwidgets.QLabel("gray: trades that are already existent", self)
        self.legendRedLabel = qtwidgets.QLabel("red: new trades that are very similar to existent trades (make sure you really want to import them!)", self)
        self.setLabelStyle()

        self.legendLayout = qtwidgets.QHBoxLayout()
        self.legendLayout.addWidget(self.legendWhiteLabel)
        self.legendLayout.addSpacerItem(qtwidgets.QSpacerItem(10, 10))
        self.legendLayout.addWidget(self.legendGrayLabel)
        self.legendLayout.addSpacerItem(qtwidgets.QSpacerItem(10, 10))
        self.legendLayout.addWidget(self.legendRedLabel)
        self.legendLayout.addStretch()

        # create options frame
        self.optionsFrame = controls.StyledFrame(self, height=20)
        self.exchangeLabel = qtwidgets.QLabel("exchange:", self.optionsFrame)
        self.exchangeInput = qtwidgets.QLineEdit(self.optionsFrame)
        self.exchangeInputButton = qtwidgets.QPushButton("set exchange", self.optionsFrame)
        self.exchangeInputButton.clicked.connect(self.exchangeChanged)
        self.walletLabel = qtwidgets.QLabel("wallet:", self.optionsFrame)
        self.walletInput = qtwidgets.QLineEdit(self.optionsFrame)
        self.walletInputButton = qtwidgets.QPushButton("set wallet", self.optionsFrame)
        self.walletInputButton.clicked.connect(self.walletChanged)

        self.optionsLayout = qtwidgets.QHBoxLayout(self.optionsFrame)
        self.optionsLayout.addWidget(self.exchangeLabel)
        self.optionsLayout.addWidget(self.exchangeInput)
        self.optionsLayout.addWidget(self.exchangeInputButton)
        self.optionsLayout.addWidget(self.walletLabel)
        self.optionsLayout.addWidget(self.walletInput)
        self.optionsLayout.addWidget(self.walletInputButton)

        # header layout
        self.headerHorzLayout = qtwidgets.QHBoxLayout()
        self.headerHorzLayout.addWidget(self.infoFrame)
        self.headerHorzLayout.addStretch()
        self.headerHorzLayout.addWidget(self.optionsFrame)

        # create trade table
        self.tableView = ttable.QTradeTableView(self)
        self.importProxyModel = ftable.SortFilterProxyModel()
        self.importProxyModel.setSourceModel(self.tradeListTemp)
        self.tableView.setModel(self.importProxyModel)
        self.tableView.show()

        self.cancelButton = qtwidgets.QPushButton("Cancel", self)
        self.cancelButton.clicked.connect(lambda: self.cancelImport())
        self.skipButton = qtwidgets.QPushButton("Skip", self)
        self.skipButton.clicked.connect(lambda: self.skipImport())
        self.nextButton = qtwidgets.QPushButton("Next", self)
        self.nextButton.clicked.connect(lambda: self.nextImport())

        self.horzButtonLayout = qtwidgets.QHBoxLayout()
        self.horzButtonLayout.addStretch()
        self.horzButtonLayout.addWidget(self.cancelButton)
        self.horzButtonLayout.addWidget(self.skipButton)
        self.horzButtonLayout.addWidget(self.nextButton)
        self.horzButtonLayout.addStretch()

        self.verticalLayout = qtwidgets.QVBoxLayout(self)
        self.verticalLayout.addLayout(self.headerHorzLayout)
        self.verticalLayout.addLayout(self.legendLayout)
        self.verticalLayout.addWidget(self.tableView)
        self.verticalLayout.addLayout(self.horzButtonLayout)

    # create empty buffer for file path
    def initData(self):
        self.filePathIndex = 0
        self.tradeListTemp = ttable.QImportTradeTableModel(baseModel=self.controller.controller.tradeList)
        self.tradeListTemp.showPrices(False)
        self.tradeListTemp.columnNotEditable = [0, 1]

    # refresh data
    def refresh(self):
        self.tradeListTemp.clearTrades()
        self.filePathIndex = 0
        self.controller.skippedRows = 0
        self.controller.importedRows = 0
        self.controller.filesNotImported = 0
        self.controller.filesImported = 0
        self.showFile(self.filePathIndex)

    def cancelImport(self):
        self.controller.showFrame(self.controller.IMPORTSELECTPAGEINDEX)

    def skipImport(self):
        self.tradeListTemp.clearTrades()
        if (self.filePathIndex < len(self.controller.getFilesPath()) - 1):
            self.exchangeInput.setText("")
            self.walletInput.setText("")
            self.filePathIndex += 1
            self.showFile(self.filePathIndex)
        else:
            self.finishImportPreview()

    def nextImport(self):
        # merge new trades
        self.controller.newTradesBuffer.mergeTradeList(self.tradeListTemp)
        # go to next import using the skip function
        self.skipImport()

    def showFile(self, index):
        # display filename
        allFilesPath = self.controller.getFilesPath()
        self.fileNameLabel.setText(os.path.basename(allFilesPath[index]))
        # import file
        content = importer.loadTradesFromFile(allFilesPath[index])
        # convert imported file to tradeList
        if not content.empty:
            importedTradeList, importedFeeList, match, skippedRows = importer.convertTradesSingle(
                models.IMPORT_MODEL_LIST, content, allFilesPath[index])
            # check import
            if match:
                self.tradeListTemp.copyFromTradeList(importedTradeList)
                self.tradeListTemp.mergeTradeList(importedFeeList)
                importedRows = len(self.tradeListTemp.trades)
                self.controller.importedRows += importedRows
                self.controller.skippedRows += skippedRows
                self.controller.filesImported += 1
                self.infoLabel.setText(
                    'header is valid, ' + str(skippedRows) + ' rows skipped, ' + str(importedRows) + ' elements imported')
            else:
                self.controller.filesNotImported += 1
                self.infoLabel.setText('unknowen header, no trades imported')
        else:
            self.controller.filesNotImported += 1
            self.infoLabel.setText('fileimport failed')

    def finishImportPreview(self):
        if not (self.controller.getNewTrades().isEmpty()):
            self.controller.showFrame(self.controller.IMPORTFINISHPAGEINDEX)
        else:
            self.controller.showFrame(self.controller.IMPORTSELECTPAGEINDEX)

    def exchangeChanged(self):
        self.tableView.addExchangeToSelectedTrades(self.exchangeInput.text())

    def walletChanged(self):
        self.tableView.addWalletToSelectedTrades(self.walletInput.text())

    def clearLabelStyle(self):
        self.legendGrayLabel.setStyleSheet("")
        self.legendRedLabel.setStyleSheet("")

    def setLabelStyle(self):
        color = style.myStyle.getQColor('TEXT_HIGHLIGHTED_MIDLIGHT')
        self.legendGrayLabel.setStyleSheet('QLabel {color: ' + color.name() + '}')
        color = style.myStyle.getQColor('NEGATIV')
        self.legendRedLabel.setStyleSheet('QLabel {color: ' + color.name() + '}')


class ImportFinishPage(SubPage):
    def __init__(self, parent, controller):
        super(ImportFinishPage, self).__init__(parent=parent, controller=controller)

        self.statusLabel = qtwidgets.QLabel('status', self)

        # trade table view
        self.tableView = ttable.QTradeTableView(self)
        self.importProxyModel = ftable.SortFilterProxyModel()
        self.tableView.setModel(self.importProxyModel)

        self.cancelButton = qtwidgets.QPushButton("cancel", self)
        self.cancelButton.clicked.connect(self.cancelTrades)
        self.acceptButton = qtwidgets.QPushButton("accept", self)
        self.acceptButton.clicked.connect(self.acceptTrades)
        self.removeSelectButton = qtwidgets.QPushButton("remove selected", self)
        self.removeSelectButton.clicked.connect(self.deleteSelectedTrades)
        self.removeSimilarButton = qtwidgets.QPushButton("remove similar", self)
        self.removeSimilarButton.clicked.connect(self.deleteSimilarTrades)

        self.horzButtonLayout = qtwidgets.QHBoxLayout()
        self.horzButtonLayout.addStretch()
        self.horzButtonLayout.addWidget(self.cancelButton)
        self.horzButtonLayout.addWidget(self.removeSelectButton)
        self.horzButtonLayout.addWidget(self.removeSimilarButton)
        self.horzButtonLayout.addWidget(self.acceptButton)
        self.horzButtonLayout.addStretch()

        self.legendWhiteLabel = qtwidgets.QLabel("white: new trades", self)
        self.legendGrayLabel = qtwidgets.QLabel("gray: trades that are already existent (will not be imported)", self)
        self.legendRedLabel = qtwidgets.QLabel("red: new trades that are very similar to existent trades (make sure you really want to import them!)", self)
        self.setLabelStyle()

        self.legendLayout = qtwidgets.QHBoxLayout()
        self.legendLayout.addWidget(self.legendWhiteLabel)
        self.legendLayout.addSpacerItem(qtwidgets.QSpacerItem(10, 10))
        self.legendLayout.addWidget(self.legendGrayLabel)
        self.legendLayout.addSpacerItem(qtwidgets.QSpacerItem(10, 10))
        self.legendLayout.addWidget(self.legendRedLabel)
        self.legendLayout.addStretch()

        self.verticalLayout = qtwidgets.QVBoxLayout(self)
        self.verticalLayout.addWidget(self.statusLabel)
        self.verticalLayout.addLayout(self.legendLayout)
        self.verticalLayout.addWidget(self.tableView)
        self.verticalLayout.addLayout(self.horzButtonLayout)


    def refresh(self):
        self.importProxyModel.setSourceModel(self.controller.getNewTrades())
        self.tableView.show()
        if not (self.controller.getNewTrades().isEmpty()):
            selectedFiles = len(self.controller.getFilesPath())
            status = 'selected Files: ' + str(selectedFiles) + '; '
            status += 'filesImported: ' + str(self.controller.filesImported) + '; '
            status += 'filesNotImported: ' + str(self.controller.filesNotImported) + '; '
            status += 'skippedRows: ' + str(self.controller.skippedRows) + '; '
            status += 'importedElements: ' + str(self.controller.importedRows)
            self.statusLabel.setText(status)

    def acceptTrades(self):
        # merge trades with database
        self.controller.finishImport()

    def deleteSelectedTrades(self):
        # remove all trades that are selected
        self.tableView.deleteSelectedTrades()

    def deleteSimilarTrades(self):
        self.tableView.deleteSimilarTrades()

    def cancelTrades(self):
        # delete trades and go back to file selection
        self.controller.showFrame(self.controller.IMPORTSELECTPAGEINDEX)

    def clearLabelStyle(self):
        self.legendGrayLabel.setStyleSheet("")
        self.legendRedLabel.setStyleSheet("")

    def setLabelStyle(self):
        color = style.myStyle.getQColor('TEXT_HIGHLIGHTED_MIDLIGHT')
        self.legendGrayLabel.setStyleSheet('QLabel {color: ' + color.name() + '}')
        color = style.myStyle.getQColor('NEGATIV')
        self.legendRedLabel.setStyleSheet('QLabel {color: ' + color.name() + '}')

