# -*- coding: utf-8 -*-
"""
Created on Sun Sep 16 20:17:51 2018

@author: Martin
"""

import PyQt5.QtGui as qtgui
import PyQt5.QtWidgets as qtwidgets
import PyQt5.QtCore as qtcore
import gui.Qcontrols as controls
import gui.QPortfolioTable as ptable
import Import.TradeImporter as importer
import PcpCore.core as core
import gui.QTradeTable as ttable
import gui.QThreads as threads
import Import.Models as models
import os
import re
import gui.QSettings as settings
import datetime
from pathlib import Path
import gui.QLogger as logger
import exp.profitExport as profex

qt = qtcore.Qt
localLogger = logger.globalLogger


# %% styled Page
class Page(qtwidgets.QFrame):
    def __init__(self, parent, controller):
        super(Page, self).__init__(parent=parent)
        self.controller = controller
        self.setObjectName("QPage")
        self.setFrameShape(qtwidgets.QFrame.StyledPanel)
        self.setFrameShadow(qtwidgets.QFrame.Raised)
        self.setContentsMargins(0, 0, 0, 10)
        self.setLineWidth(2)
        self.setMidLineWidth(3)


# sub page
class SubPage(Page):
    def __init__(self, parent, controller):
        super(SubPage, self).__init__(parent=parent, controller=controller)
        self.setObjectName("QSubPage")


# %% portfolio showing all the coins and there current value ...
class PortfolioPage(Page):
    def __init__(self, parent, controller):
        super(PortfolioPage, self).__init__(parent=parent, controller=controller)

        self.layoutUI()

    # initial layout ob the Page
    def layoutUI(self):
        # main layout
        self.mainLayout = qtwidgets.QHBoxLayout(self)

        # portfolio coinDataFrame
                            # adding parent here causes crash in setStyleSheet call??!
                            # exit code -1073741819 (0xC0000005), very strange
                            # todo: check out error
                            # for now no parent is given, seems to work fine
        self.coinDataFrame = ptable.PortfolioOverview(self.controller, height=200)
        # self.coinDataFrame.setFixedHeight(200)
        self.coinDataFrame.setModel(self.controller.coinList)


        self.coinTableView = ptable.QPortfolioTableView(self)
        self.coinProxyModel = ptable.QTableSortingModel()
        self.coinProxyModel.setSourceModel(self.controller.coinList)
        self.coinTableView.setModel(self.coinProxyModel)

        self.coinTableView.show()

        # layout
        self.verticalLayout = qtwidgets.QVBoxLayout()
        self.verticalLayout.addWidget(self.coinDataFrame)
        self.verticalLayout.addWidget(self.coinTableView)
        #        self.verticalLayout.addWidget(self.coinTable)

        self.mainLayout.addLayout(self.verticalLayout)

    # refresh page every time it is activated
    def refresh(self):
        pass


# %% trades page showing all the imported trades
class TradesPage(Page):
    def __init__(self, parent, controller):
        super(TradesPage, self).__init__(parent=parent, controller=controller)

        self.layoutUI()

    # initial layout of page
    def layoutUI(self):
        # base layout
        self.horizontalLayout = qtwidgets.QHBoxLayout(self)

        # table for tradeList        
        self.tradeTableView = ttable.QTradeTableView(self)
        self.tradeProxyModel = qtcore.QSortFilterProxyModel()
        self.tradeProxyModel.setSourceModel(self.controller.tradeList)
        self.tradeTableView.setModel(self.tradeProxyModel)
        self.tradeTableView.show()

        # layout
        self.verticalLayout = qtwidgets.QVBoxLayout()
        self.verticalLayout.addWidget(self.tradeTableView)

        self.horizontalLayout.addLayout(self.verticalLayout)

        # refresh page

    def refresh(self):
        pass


#    def tradesChanged(self):
#        self.tradeTable.setTradeList(self.controller.tradeList)


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
        self.importFinishPage = ImportFinishPage(parent=self, controller=self)
        self.pages = [self.importSelectPage, self.importPreviewPage, self.importFinishPage]
        self.stackedContentLayout = qtwidgets.QStackedLayout(self)
        for page in self.pages:
            # stacked content layout
            self.stackedContentLayout.addWidget(page)

        self.refresh()

    def initData(self):
        self.newTradesBuffer = ttable.QTradeTableModel()
        self.newTradesBuffer.showPrices(False)
        self.newTradesBuffer.columnNotEditable = [0, 1]
        self.newFeesBuffer = ttable.QTradeTableModel()
        self.newFeesBuffer.showPrices(False)
        self.newFeesBuffer.columnNotEditable = [0, 1]
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

    def getNewFees(self):
        return self.newFeesBuffer

    def clearNewTrades(self):
        self.newTradesBuffer.clearTrades()
        self.newFeesBuffer.clearTrades()

    def finishImport(self):
        newTrades = self.getNewTrades()
        self.controller.tradeList.addTrades(newTrades)
        self.controller.tradeList.addTrades(self.getNewFees())
        # jump to TradesPage
        self.controller.showFrame(self.controller.TRADESPAGEINDEX)



class ImportSelectPage(SubPage):
    def __init__(self, parent, controller):
        super(ImportSelectPage, self).__init__(parent=parent, controller=controller)

        # empty file buffer
        filetypes = settings.mySettings['import']['importFileTypes']
        self.filePattern = re.compile("^.*\." + filetypes + "$", re.IGNORECASE)

        # enter path
        self.pathEntry = controls.PathInput(self)
        self.pathEntry.textChanged.connect(self.pathChanged)

        # file system view
        self.fileSystemModel = qtwidgets.QFileSystemModel()
        self.fileSystemModel.setRootPath(qtcore.QDir.currentPath())

        self.treeView = qtwidgets.QTreeView(self)
        self.treeView.setModel(self.fileSystemModel)
        self.treeView.setSelectionMode(qtwidgets.QAbstractItemView.ExtendedSelection)
        self.treeView.header().setSectionResizeMode(qtwidgets.QHeaderView.ResizeToContents)
        self.treeView.selectionModel().selectionChanged.connect(self.selectionChangedCallback)

        self.treeView.setRootIndex(self.fileSystemModel.index(qtcore.QDir.currentPath()))

        # display path details
        self.feedBackFrame = controls.StyledFrame(self)
        self.feedBackLabel = qtwidgets.QLabel('selected Files: ', self.feedBackFrame)
        self.fileTextBox = qtwidgets.QTextEdit(self.feedBackFrame)
        self.fileTextBox.setReadOnly(True)

        self.previewButton = qtwidgets.QPushButton("Preview", self)
        self.previewButton.clicked.connect(lambda: self.showPreviewFrame())

        self.fastImportButton = qtwidgets.QPushButton("Fast import", self)
        self.fastImportButton.clicked.connect(lambda: self.showImportFinishedFrame())

        self.horzButtonLayout = qtwidgets.QHBoxLayout()
        self.horzButtonLayout.addStretch()
        self.horzButtonLayout.addWidget(self.previewButton)
        self.horzButtonLayout.addWidget(self.fastImportButton)
        self.horzButtonLayout.addStretch()

        # layout
        self.feedbackLayout = qtwidgets.QVBoxLayout(self.feedBackFrame)
        self.feedbackLayout.addWidget(self.feedBackLabel)
        self.feedbackLayout.addWidget(self.fileTextBox)
        self.verticalLayout = qtwidgets.QVBoxLayout(self)
        self.verticalLayout.addWidget(self.pathEntry)

        self.horzLayout = qtwidgets.QHBoxLayout()
        self.horzLayout.addWidget(self.treeView)
        self.horzLayout.addWidget(self.feedBackFrame)

        self.verticalLayout.addLayout(self.horzLayout)
        self.verticalLayout.addLayout(self.horzButtonLayout)

        self.pathEntry.setPath(qtcore.QDir.currentPath())

    def refresh(self):
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
                print("pathChanged callback failed: " + str(ex))

    def selectionChangedCallback(self):
        self.fileTextBox.clear()
        self.controller.allFilesPath = []
        indexes = self.treeView.selectionModel().selectedIndexes()
        self.filePaths = []
        for index in indexes:
            if index.column() == 0:
                path = Path(self.fileSystemModel.filePath(index))
                if path.is_file():
                    self.controller.allFilesPath.append(str(path))
                    self.fileTextBox.insertPlainText(os.path.basename(path) + '\n')
                if path.is_dir():
                    files = [os.path.join(str(path), str(f)) for f in path.iterdir() if self.filePattern.match(str(f))]
                    self.controller.allFilesPath += files
                    for file in files:
                        self.fileTextBox.insertPlainText(os.path.basename(file) + '\n')

    # show preview frame and refresh data
    def showPreviewFrame(self):
        if (self.controller.getFilesPath()):
            self.controller.showFrame(self.controller.IMPORTPREVIEWPAGEINDEX)
        else:
            localLogger.info('please select at least one valid file')

    # skip preview and shoe import finished page
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
                        self.controller.newFeesBuffer.mergeTradeList(feeListTemp)
                        self.controller.importedRows += len(tradeListTemp.trades) + len(feeListTemp.trades)
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


class ImportPreviewPage(SubPage):
    def __init__(self, parent, controller):
        super(ImportPreviewPage, self).__init__(parent=parent, controller=controller)

        # create empty buffer for file path
        self.initData()

        # create info frame
        self.infoFrame = controls.StyledFrame(self, height=20)
        self.fileNameLabel = qtwidgets.QLabel("FileName", self.infoFrame)
        self.infoLabel = qtwidgets.QLabel("", self.infoFrame)

        self.infoLayout = qtwidgets.QVBoxLayout(self.infoFrame)
        self.infoLayout.addWidget(self.fileNameLabel)
        self.infoLayout.addWidget(self.infoLabel)

        # create options frame
        self.optionsFrame = controls.StyledFrame(self, height=20)
        self.exchangeLabel = qtwidgets.QLabel("exchange:", self.optionsFrame)
        self.exchangeInput = qtwidgets.QLineEdit(self.optionsFrame)
        self.exchangeInputButton = qtwidgets.QPushButton("set exchange", self.optionsFrame)
        self.exchangeInputButton.clicked.connect(self.exchangeChanged)

        self.optionsLayout = qtwidgets.QHBoxLayout(self.optionsFrame)
        self.optionsLayout.addWidget(self.exchangeLabel)
        self.optionsLayout.addWidget(self.exchangeInput)
        self.optionsLayout.addWidget(self.exchangeInputButton)

        # header layout
        self.headerHorzLayout = qtwidgets.QHBoxLayout()
        self.headerHorzLayout.addWidget(self.infoFrame)
        self.headerHorzLayout.addStretch()
        self.headerHorzLayout.addWidget(self.optionsFrame)

        # create trade table
        self.tableView = ttable.QTradeTableView(self)
        self.tradeProxyModel = qtcore.QSortFilterProxyModel()
        self.tradeProxyModel.setSourceModel(self.tradeListTemp)
        self.tableView.setModel(self.tradeProxyModel)
        self.tableView.show()

        # create fee table
        self.feeTableView = ttable.QTradeTableView(self)
        self.feeProxyModel = qtcore.QSortFilterProxyModel()
        self.feeProxyModel.setSourceModel(self.feeListTemp)
        self.feeTableView.setModel(self.feeProxyModel)
        self.feeTableView.show()

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
        self.verticalLayout.addWidget(self.tableView)
        self.verticalLayout.addWidget(self.feeTableView)
        self.verticalLayout.addLayout(self.horzButtonLayout)

    # create empty buffer for file path  
    def initData(self):
        self.filePathIndex = 0
        self.tradeListTemp = ttable.QTradeTableModel()
        self.tradeListTemp.showPrices(False)
        self.tradeListTemp.columnNotEditable = [0, 1]
        self.feeListTemp = ttable.QTradeTableModel()
        self.feeListTemp.showPrices(False)
        self.feeListTemp.columnNotEditable = [0, 1]

    # refresh data
    def refresh(self):
        self.filePathIndex = 0
        self.controller.skippedRows = 0
        self.controller.importedRows = 0
        self.controller.filesNotImported = 0
        self.controller.filesImported = 0
        self.showFile(self.filePathIndex)

    def cancelImport(self):
        self.controller.showFrame(self.controller.IMPORTSELECTPAGEINDEX)

    def skipImport(self):
        if (self.filePathIndex < len(self.controller.getFilesPath()) - 1):
            self.exchangeInput.setText("")
            self.filePathIndex += 1
            self.showFile(self.filePathIndex)
        else:
            self.finishImportPreview()

    def nextImport(self):
        # merge new trades
        self.controller.newTradesBuffer.mergeTradeList(self.tradeListTemp)
        self.controller.newFeesBuffer.mergeTradeList(self.feeListTemp)
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
                self.feeListTemp.copyFromTradeList(importedFeeList)
                importedRows = len(self.tradeListTemp.trades) + len(self.feeListTemp.trades)
                self.controller.importedRows += importedRows
                self.controller.skippedRows += skippedRows
                self.controller.filesImported += 1
                self.infoLabel.setText(
                    'header is valid, ' + str(skippedRows) + ' rows skipped, ' + str(importedRows) + ' rows imported')
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
        self.tradeListTemp.setExchange(self.exchangeInput.text())
        self.feeListTemp.setExchange(self.exchangeInput.text())


class ImportFinishPage(SubPage):
    def __init__(self, parent, controller):
        super(ImportFinishPage, self).__init__(parent=parent, controller=controller)

        self.statusLabel = qtwidgets.QLabel('status', self)

        # trade table view
        self.tableView = ttable.QTradeTableView(self)
        self.tradeProxyModel = qtcore.QSortFilterProxyModel()
        self.tableView.setModel(self.tradeProxyModel)

        # fee table view
        self.feeTableView = ttable.QTradeTableView(self)
        self.feeProxyModel = qtcore.QSortFilterProxyModel()
        self.feeTableView.setModel(self.feeProxyModel)

        self.cancelButton = qtwidgets.QPushButton("Cancel", self)
        self.cancelButton.clicked.connect(lambda: self.cancelTrades())
        self.acceptButton = qtwidgets.QPushButton("Accept", self)
        self.acceptButton.clicked.connect(lambda: self.acceptTrades())

        self.horzButtonLayout = qtwidgets.QHBoxLayout()
        self.horzButtonLayout.addStretch()
        self.horzButtonLayout.addWidget(self.cancelButton)
        self.horzButtonLayout.addWidget(self.acceptButton)
        self.horzButtonLayout.addStretch()

        self.verticalLayout = qtwidgets.QVBoxLayout(self)
        self.verticalLayout.addWidget(self.statusLabel)
        self.verticalLayout.addWidget(self.tableView)
        self.verticalLayout.addWidget(self.feeTableView)
        self.verticalLayout.addLayout(self.horzButtonLayout)

    def refresh(self):
        self.tradeProxyModel.setSourceModel(self.controller.getNewTrades())
        self.feeProxyModel.setSourceModel(self.controller.getNewFees())
        self.tableView.show()
        if not (self.controller.getNewTrades().isEmpty()):
            selectedFiles = len(self.controller.getFilesPath())
            status = 'selected Files: ' + str(selectedFiles) + '; '
            status += 'filesImported: ' + str(self.controller.filesImported) + '; '
            status += 'filesNotImported: ' + str(self.controller.filesNotImported) + '; '
            status += 'skippedRows: ' + str(self.controller.skippedRows) + '; '
            status += 'importedRows: ' + str(self.controller.importedRows)
            self.statusLabel.setText(status)

    def acceptTrades(self):
        # merge trades with database
        self.controller.finishImport()

    def cancelTrades(self):
        # delete trades and go back to file selection
        self.controller.showFrame(self.controller.IMPORTSELECTPAGEINDEX)


# %% export page for exporting csv, txt, xls ...
class ExportPage(Page):
    def __init__(self, parent, controller):
        super(ExportPage, self).__init__(parent=parent, controller=controller)

        self.fileDialog = qtwidgets.QFileDialog(self)
        # self.fileDialog.setDirectory(self.controller.appPath)

        self.exportProfitFrame = controls.StyledFrame(self)
        self.exportProfitFrame.setFixedWidth(275)

        # heading
        self.exportProfitLabel = qtwidgets.QLabel("export profit", self.exportProfitFrame)
        font = self.exportProfitLabel.font()
        font.setPointSize(14)
        self.exportProfitLabel.setFont(font)

        self.headingLayout = qtwidgets.QHBoxLayout()
        self.headingLayout.addStretch()
        self.headingLayout.addWidget(self.exportProfitLabel)
        self.headingLayout.addStretch()

        # start and end date
        self.fromDateLabel = qtwidgets.QLabel("start: ", self.exportProfitFrame)
        self.toDateLabel = qtwidgets.QLabel("end: ", self.exportProfitFrame)
        self.fromDateEdit = qtwidgets.QDateEdit(self.exportProfitFrame)
        self.fromDateEdit.setCalendarPopup(True)
        self.toDateEdit = qtwidgets.QDateEdit(self.exportProfitFrame)
        self.toDateEdit.setCalendarPopup(True)

        self.dateLayout = qtwidgets.QHBoxLayout()
        self.dateLayout.addWidget(self.fromDateLabel)
        self.dateLayout.addWidget(self.fromDateEdit)
        self.dateLayout.addStretch()
        self.dateLayout.addWidget(self.toDateLabel)
        self.dateLayout.addWidget(self.toDateEdit)
        # self.dateLayout.addStretch()

        # year
        self.yearLabel = qtwidgets.QLabel("year: ", self.exportProfitFrame)
        self.yearDateEdit = qtwidgets.QSpinBox(self.exportProfitFrame)
        self.yearDateEdit.valueChanged.connect(self.yearChanged)
        self.yearDateEdit.setMinimum(0)
        self.yearDateEdit.setMaximum(datetime.datetime.now().year)
        self.yearDateEdit.setValue(datetime.datetime.now().year)

        self.yearLayout = qtwidgets.QHBoxLayout()
        self.yearLayout.addStretch()
        self.yearLayout.addWidget(self.yearLabel)
        self.yearLayout.addWidget(self.yearDateEdit)
        self.yearLayout.addStretch()

        # currency
        self.currencyLabel = qtwidgets.QLabel("currency", self.exportProfitFrame)
        self.currencyBox = qtwidgets.QComboBox(self.exportProfitFrame)
        listModel = qtcore.QStringListModel()
        currencys = list(core.CoinValue())
        listModel.setStringList(currencys)
        self.currencyBox.setModel(listModel)
        defaultCurrency = settings.mySettings['currency']['defaultReportCurrency']
        self.currencyBox.setCurrentIndex(currencys.index(defaultCurrency))

        self.currencyLayout = qtwidgets.QHBoxLayout()
        self.currencyLayout.addWidget(self.currencyLabel)
        self.currencyLayout.addWidget(self.currencyBox)
        self.currencyLayout.addStretch()

        # tax timelimit
        self.timeLimitLabel = qtwidgets.QLabel("tax year limit", self.exportProfitFrame)
        self.timeLimitBox = qtwidgets.QCheckBox(self.exportProfitFrame)
        self.timeLimitEdit = qtwidgets.QSpinBox(self.exportProfitFrame)
        self.timeLimitEdit.setValue(1)
        self.timeLimitEdit.setMinimum(0)
        self.timeLimitBox.stateChanged.connect(self.timeLimitCheckBoxChanged)
        self.timeLimitBox.setCheckState(qt.Unchecked)

        self.timeLimitLayout = qtwidgets.QHBoxLayout()
        self.timeLimitLayout.addWidget(self.timeLimitLabel)
        self.timeLimitLayout.addWidget(self.timeLimitBox)
        self.timeLimitLayout.addWidget(self.timeLimitEdit)
        self.timeLimitLayout.addStretch()

        # include tax free trades
        self.taxFreeTradesLabel = qtwidgets.QLabel("include tax free trades", self.exportProfitFrame)
        self.taxFreeTradesBox = qtwidgets.QCheckBox(self.exportProfitFrame)
        self.taxFreeTradesBox.setCheckState(qt.Checked)

        self.taxFreeTradesLayout = qtwidgets.QHBoxLayout()
        self.taxFreeTradesLayout.addWidget(self.taxFreeTradesLabel)
        self.taxFreeTradesLayout.addWidget(self.taxFreeTradesBox)
        self.taxFreeTradesLayout.addStretch()

        # todo: add export checkboxes

        # include fees
        # label
        # checkbox

        # include exchanges
        # label
        # checkbox

        # daywise matching
        # label
        # checkbox

        self.timeLimitCheckBoxChanged()

        # export button
        self.exportProfitButton = qtwidgets.QPushButton("export", self.exportProfitFrame)
        self.exportProfitButton.clicked.connect(self.exportProfit)

        self.buttonLayout = qtwidgets.QHBoxLayout()
        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.exportProfitButton)
        self.buttonLayout.addStretch()


        self.vertLayout = qtwidgets.QVBoxLayout(self.exportProfitFrame)
        self.vertLayout.addLayout(self.headingLayout)
        self.vertLayout.addLayout(self.yearLayout)
        self.vertLayout.addLayout(self.dateLayout)
        self.vertLayout.addLayout(self.currencyLayout)
        self.vertLayout.addLayout(self.timeLimitLayout)
        self.vertLayout.addLayout(self.taxFreeTradesLayout)
        # self.vertLayout.addLayout(self.)
        self.vertLayout.addStretch()
        self.vertLayout.addLayout(self.buttonLayout)

        self.horzLayout = qtwidgets.QHBoxLayout(self)
        self.horzLayout.addWidget(self.exportProfitFrame)
        self.horzLayout.addStretch()



    def refresh(self):
        pass

    def yearChanged(self):
        year = self.yearDateEdit.value()
        self.fromDateEdit.setDate(qtcore.QDate(year, 1, 1))
        self.toDateEdit.setDate(qtcore.QDate(year, 12, 31))

    def timeLimitCheckBoxChanged(self):
        if self.timeLimitBox.isChecked():
            self.timeLimitEdit.setEnabled(True)
            self.taxFreeTradesBox.setEnabled(True)
        else:
            self.timeLimitEdit.setEnabled(False)
            self.taxFreeTradesBox.setEnabled(False)

    def exportProfit(self):
        self.fileDialog.setDefaultSuffix("xlsx")

        datestr = str(datetime.datetime.now()).replace(' ', '_').replace(':', '_').replace('-', '_').replace('.', '_')
        filename = 'profit' + '-' + datestr + '.xlsx'
        pathReturn = self.fileDialog.getSaveFileName(self, "save file", filename, "Excel (*.xlsx *.xls)")
        if pathReturn[0]:
            minDate = self.fromDateEdit.date().toPyDate()
            maxDate = self.toDateEdit.date().toPyDate()
            currency = self.currencyBox.currentText()
            taxyearlimit = None
            if self.timeLimitBox.isChecked():
                taxyearlimit = self.timeLimitEdit.value()
            includeTaxFreeTrades = self.taxFreeTradesBox.isChecked()
            profex.createProfitExcel(self.controller.coinList, pathReturn[0], minDate, maxDate, currency=currency, taxyearlimit=taxyearlimit, includeTaxFreeTrades=includeTaxFreeTrades)



# %% settings page
class SettingsPage(Page):
    def __init__(self, parent, controller):
        super(SettingsPage, self).__init__(parent=parent, controller=controller)

        self.vertLayout = qtwidgets.QVBoxLayout(self)

        # content
        self.settingsView = settings.SettingsTreeView(self)
        self.settingsView.setModel(self.controller.settingsModel)
        self.settingsView.expandAll()
        self.settingsView.setColumnWidth(0, 200)
        self.settingsView.header().setStretchLastSection(True)

        # buttons
        self.resetDefaultButton = qtwidgets.QPushButton("reset to default", self)
        self.reloadButton = qtwidgets.QPushButton("reload", self)
        self.saveButton = qtwidgets.QPushButton("save", self)
        self.saveRefreshButton = qtwidgets.QPushButton("save and reload", self)

        self.resetDefaultButton.clicked.connect(self.resetDefaultSettings)
        self.reloadButton.clicked.connect(self.reloadSettings)
        self.saveButton.clicked.connect(self.saveSettings)
        self.saveRefreshButton.clicked.connect(self.saveRefreshSettings)

        self.horzButtonLayout = qtwidgets.QHBoxLayout()
        self.horzButtonLayout.addStretch()
        self.horzButtonLayout.addWidget(self.resetDefaultButton)
        self.horzButtonLayout.addWidget(self.reloadButton)
        self.horzButtonLayout.addWidget(self.saveButton)
        self.horzButtonLayout.addWidget(self.saveRefreshButton)
        self.horzButtonLayout.addStretch()

        self.vertLayout.addWidget(self.settingsView)
        # self.vertLayout.addStretch()
        self.vertLayout.addLayout(self.horzButtonLayout)


    def refresh(self):
        pass

    def resetDefaultSettings(self):
        settings.mySettings.resetDefault()
        self.controller.reinit()

    def reloadSettings(self):
        settings.mySettings.readSettings()
        self.controller.reinit()

    def saveSettings(self):
        settings.mySettings.saveSettings()

    def saveRefreshSettings(self):
        settings.mySettings.saveSettings()
        self.controller.reinit()
# %% functions