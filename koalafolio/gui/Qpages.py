# -*- coding: utf-8 -*-
"""
Created on Sun Sep 16 20:17:51 2018

@author: Martin
"""

import PyQt5.QtWidgets as qtwidgets
import PyQt5.QtCore as qtcore
import koalafolio.gui.QPortfolioTable as ptable
import koalafolio.gui.QSettings as settings
import koalafolio.gui.SettingsPage as settingsPage
import koalafolio.gui.QLogger as logger
import webbrowser

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
        self.controller.settingsModel.displayCurrenciesChanged.connect(
            self.coinDataFrame.displayCurrenciesChangedSlot)
        # self.coinDataFrame.setFixedHeight(200)
        self.coinDataFrame.setModel(self.controller.coinList)

        self.coinTableView = ptable.QPortfolioTableView(self)
        self.coinProxyModel = ptable.QTableSortingModel()
        self.coinProxyModel.setSourceModel(self.controller.coinList)
        self.coinTableView.setModel(self.coinProxyModel)
        guiSettings = settings.mySettings.getGuiSettings()
        self.coinTableView.sortByColumn(guiSettings['portfolio_sort_row'], guiSettings['portfolio_sort_dir'])

        self.coinTableView.show()
        self.controller.coinList.triggerViewReset.connect(self.createNewView)
        self.coinDataFrame.expandTable.connect(self.coinTableView.expandAll)
        self.coinDataFrame.collapseTable.connect(self.coinTableView.collapseAll)

        # layout
        self.verticalLayout = qtwidgets.QVBoxLayout()
        self.verticalLayout.addWidget(self.coinDataFrame)
        self.verticalLayout.addWidget(self.coinTableView)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)

        self.mainLayout.addLayout(self.verticalLayout)

    # refresh page every time it is activated
    def refresh(self):
        self.controller.coinList.triggerPriceUpdate()

    def getGuiProps(self):
        gui = {}
        gui['portfolio_sort_row'] = str(self.coinProxyModel.sortedRow)
        gui['portfolio_sort_dir'] = str(self.coinProxyModel.sortedDir)
        gui['performancechartindex'] = self.coinDataFrame.perfChartCont.chartIndex
        return gui

    def createNewView(self):
        self.coinDataFrame.expandTable.disconnect(self.coinTableView.expandAll)
        self.coinDataFrame.collapseTable.disconnect(self.coinTableView.collapseAll)
        self.verticalLayout.removeWidget(self.coinTableView)
        self.coinTableView.setStyleSheet("")
        self.coinTableView.deleteLater()

        self.coinTableView = ptable.QPortfolioTableView(self)
        self.coinTableView.setModel(self.coinProxyModel)
        guiSettings = settings.mySettings.getGuiSettings()
        self.coinTableView.sortByColumn(guiSettings['portfolio_sort_row'], guiSettings['portfolio_sort_dir'])

        self.coinTableView.show()

        self.coinDataFrame.expandTable.connect(self.coinTableView.expandAll)
        self.coinDataFrame.collapseTable.connect(self.coinTableView.collapseAll)

        self.verticalLayout.addWidget(self.coinTableView)



# %% settings page
class SettingsPage(Page):
    def __init__(self, parent, controller):
        super(SettingsPage, self).__init__(parent=parent, controller=controller)

        self.vertLayout = qtwidgets.QVBoxLayout(self)

        # path label
        self.appPathPreButton = qtwidgets.QPushButton("app path: ")
        self.appPathPreButton.clicked.connect(lambda: webbrowser.open('file:///' + controller.appPath))
        self.appPathLabel = qtwidgets.QLabel(controller.appPath)
        self.dataPathPreButton = qtwidgets.QPushButton("data path: ")
        self.dataPathPreButton.clicked.connect(lambda: webbrowser.open('file:///' + controller.dataPath))
        self.dataPathLabel = qtwidgets.QLabel(controller.dataPath)
        self.appPathLabel.setTextInteractionFlags(qt.TextSelectableByMouse)
        self.dataPathLabel.setTextInteractionFlags(qt.TextSelectableByMouse)
        self.appPathPreButton.setContentsMargins(10, 0, 0, 0)
        self.dataPathPreButton.setContentsMargins(10, 0, 0, 0)
        self.appPathLabel.setContentsMargins(0, 0, 10, 0)
        self.dataPathLabel.setContentsMargins(0, 0, 10, 0)

        self.githubButton = qtwidgets.QPushButton("github")
        self.githubButton.clicked.connect(lambda: webbrowser.open('https://github.com/2martin2/koalafolio'))

        self.labelLayout = qtwidgets.QHBoxLayout()
        self.labelLayout.addWidget(self.appPathPreButton)
        self.labelLayout.addWidget(self.appPathLabel)
        self.labelLayout.addWidget(self.dataPathPreButton)
        self.labelLayout.addWidget(self.dataPathLabel)
        self.labelLayout.addWidget(self.githubButton)
        self.labelLayout.addStretch()
        self.vertLayout.addLayout(self.labelLayout)

        # content
        self.settingsView = settingsPage.SettingsTreeView(self)
        self.settingsView.setModel(self.controller.settingsModel)
        self.settingsView.expandAll()
        self.settingsView.setColumnWidth(0, 350)
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
        self.controller.settingsModel.resetDefault()
        self.settingsView.expandAll()
        self.controller.reinit()

    def reloadSettings(self):
        self.controller.settingsModel.restoreSettings()
        self.controller.reinit()

    def saveSettings(self):
        settings.mySettings.saveSettings()

    def saveRefreshSettings(self):
        settings.mySettings.saveSettings()
        self.controller.reinit()
# %% functions
