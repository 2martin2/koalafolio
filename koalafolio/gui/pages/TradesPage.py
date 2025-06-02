# -*- coding: utf-8 -*-
"""
Created on 11.04.2021

@author: Martin
"""


from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt
import koalafolio.gui.widgets.QTradeTable as ttable
import koalafolio.gui.widgets.FilterableTable as ftable
import koalafolio.gui.helper.QSettings as settings
import koalafolio.gui.helper.QLogger as logger
from pages.Qpages import Page

localLogger = logger.globalLogger


# %% trades page showing all the imported trades
class TradesPage(Page):
    def __init__(self, parent, controller):
        super(TradesPage, self).__init__(parent=parent, controller=controller)

        self.layoutUI()

    # initial layout of page
    def layoutUI(self):
        # base layout
        self.horizontalLayout = QHBoxLayout(self)

        # table for tradeList
        self.proxyModel = ftable.SortFilterProxyModel()
        self.proxyModel.setSourceModel(self.controller.tradeList)
        self.tradeTableView = ttable.QTradeTableView(parent=self)
        self.tradeTableView.setModel(self.proxyModel)
        self.tradeTableView.show()

        gui = settings.mySettings.getGuiSettings()
        self.tradeTableView.sortByColumn(gui['trade_sort_row'], gui['trade_sort_dir'])

        # properties line , contains gui elements to control table behavior (buttons, checkboxes, ...)

        # controls
        self.resetFilterButton = QPushButton('Reset Filter', self)
        self.resetFilterButton.clicked.connect(lambda checked: self.tradeTableView.clearFilters(checked))

        self.useRegexCheckbox = QCheckBox(text='use regex', parent=self)
        if settings.mySettings.getGuiSetting('filteruseregex'):
            self.useRegexCheckbox.setCheckState(Qt.Checked)
        else:
            self.useRegexCheckbox.setCheckState(Qt.Unchecked)
        self.useRegexCheckbox.stateChanged.connect(lambda state: self.switchRegexFilter(state))


        self.deleteSelectedTradesButton = QPushButton('delete selected', self)
        self.deleteSelectedTradesButton.clicked.connect(self.deleteSelectedTrades)
        self.deleteTradesButton = QPushButton('delete all', self)
        self.deleteTradesButton.clicked.connect(self.deleteAllTrades)
        self.undoButton = QPushButton('undo', self)
        self.undoButton.clicked.connect(self.undoRemoveAddTrades)
        self.reloadPricesButton = QPushButton('reload prices', self)
        self.reloadPricesButton.clicked.connect(self.reloadPrices)
        self.recalculateIdsButton = QPushButton('recalculate Ids', self)
        self.recalculateIdsButton.clicked.connect(self.recalcIds)

        self.hButtonLayout = QHBoxLayout()
        self.hButtonLayout.addWidget(self.resetFilterButton)
        self.hButtonLayout.addWidget(self.useRegexCheckbox)
        self.hButtonLayout.addStretch()
        self.hButtonLayout.addWidget(self.deleteSelectedTradesButton)
        self.hButtonLayout.addWidget(self.deleteTradesButton)
        self.hButtonLayout.addWidget(self.undoButton)
        self.hButtonLayout.addStretch()
        self.hButtonLayout.addWidget(self.reloadPricesButton)
        self.hButtonLayout.addWidget(self.recalculateIdsButton)
        self.hButtonLayout.addStretch()

        # layout
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.addWidget(self.tradeTableView)
        self.verticalLayout.addLayout(self.hButtonLayout)
        self.verticalLayout.setContentsMargins(5, 2, 5, 5)

        self.horizontalLayout.addLayout(self.verticalLayout)

    # refresh page
    def refresh(self):
        self.controller.tradeList.enableEditMode(not settings.mySettings.getGuiSetting('tradeseditlock'))

    def undoRemoveAddTrades(self):
        self.undoButton.clicked.disconnect(self.undoRemoveAddTrades)
        self.controller.tradeList.undoRemoveAddTrades()
        self.undoButton.clicked.connect(self.undoRemoveAddTrades)

    def deleteAllTrades(self):
        self.deleteTradesButton.clicked.disconnect(self.deleteAllTrades)
        self.controller.tradeList.deleteAllTrades()
        self.deleteTradesButton.clicked.connect(self.deleteAllTrades)

    def deleteSelectedTrades(self):
        self.deleteSelectedTradesButton.clicked.disconnect(self.deleteSelectedTrades)
        self.tradeTableView.deleteSelectedTrades()
        self.deleteSelectedTradesButton.clicked.connect(self.deleteSelectedTrades)

    def reloadPrices(self):
        self.controller.tradeList.clearPriceFlag()
        self.controller.tradeList.updateHistPrices(self.controller.tradeList)

    def recalcIds(self):
        self.controller.tradeList.recalcIds()

    def switchRegexFilter(self, state):
        if state == Qt.Checked:
            settings.mySettings.setGuiSetting('filteruseregex', True)
            self.proxyModel.useRegex = True
        else:  # not checked
            settings.mySettings.setGuiSetting('filteruseregex', False)
            self.proxyModel.useRegex = False

    def getGuiProps(self):
        """get current gui properties, is called by closeEvent of main window """
        gui = {'trade_sort_row': str(self.proxyModel.sortedColumn),
               'trade_sort_dir': str(self.proxyModel.sortedDir)}
        return gui

