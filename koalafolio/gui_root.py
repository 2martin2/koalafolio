# -*- coding: utf-8 -*-
"""
Created on Sun Sep 16 09:57:14 2018

@author: Martin
"""

import PyQt5.QtGui as qtgui
import PyQt5.QtWidgets as qtwidgets
import PyQt5.QtCore as qtcore
import PyQt5.QtChart as qtchart

import koalafolio.gui.Qpages as pages
import koalafolio.gui.Qcontrols as controls
import koalafolio.gui.QPortfolioTable as ptable
import koalafolio.gui.QTradeTable as ttable
import koalafolio.gui.QThreads as threads
import koalafolio.PcpCore.logger as coreLogger
import koalafolio.gui.QLogger as logger
import sys
import os
import koalafolio.PcpCore.settings as coreSettings
import koalafolio.gui.QSettings as settings
import koalafolio.gui.QStyle as style

qt = qtcore.Qt
# %% constants


# %% variables
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


# %% classes
class PortfolioApp(qtwidgets.QWidget):
    PORTFOLIOPAGEINDEX = 0
    TRADESPAGEINDEX = 1
    IMPORTPAGEINDEX = 2
    EXPORTPAGEINDEX = 3
    SETTINGSPAGEINDEX = 4
    startRefresh = qtcore.pyqtSignal()
    endRefresh = qtcore.pyqtSignal()

    def __init__(self, parent=None):
        super(PortfolioApp, self).__init__(parent=parent)

        self.setObjectName("MainWindow")

        self.initEnv()
        self.initWindow()

        # init data
        self.initData()
        self.initStyle()

        # init gui
        self.layoutUI()
        self.show()
        self.showFrame(self.PORTFOLIOPAGEINDEX)
        # gui and data initialized

        # start the background threads
        self.startThreads()
        self.tradeList.restoreTrades()

        self.logger.info('application initialized')

    def reinit(self):
        self.startRefresh.emit()
        # delete button styles before style update, otherwise qt will crash
        self.buttonPortfolio.setStyleSheet("")
        self.buttonTrades.setStyleSheet("")
        self.buttonImport.setStyleSheet("")
        self.buttonExport.setStyleSheet("")
        self.buttonSettings.setStyleSheet("")
        self.initStyle()
        self.buttonPortfolio.setStyleSheet("QPushButton {border-image: url(" +
                                           os.path.join(self.appPath, 'graphics', 'portfolio.png').replace('\\', '/') +
                                           ") 0 15 0 15 stretch;}")
        self.buttonTrades.setStyleSheet("QPushButton {border-image: url(" +
                                        os.path.join(self.appPath, 'graphics', 'trades.png').replace('\\', '/') +
                                        ") 0 15 0 15 stretch;}")
        self.buttonImport.setStyleSheet("QPushButton {border-image: url(" +
                                        os.path.join(self.appPath, 'graphics', 'import.png').replace('\\', '/') +
                                        ") 0 15 0 15 stretch;}")
        self.buttonExport.setStyleSheet("QPushButton {border-image: url(" +
                                        os.path.join(self.appPath, 'graphics', 'export.png').replace('\\', '/') +
                                        ") 0 15 0 15 stretch;}")
        self.buttonSettings.setStyleSheet("QPushButton {border-image: url(" +
                                          os.path.join(self.appPath, 'graphics', 'settings.png').replace('\\', '/') +
                                          ") 0 15 0 15 stretch;}")
        self.endRefresh.emit()

    # load environment/ settings
    def initEnv(self):
        # handle paths
        self.appPath = application_path
        self.dataPath = os.path.join(self.appPath, 'Data')
        # check for DataFolder
        try:
            os.stat(self.dataPath)
        except:
            try:
                os.mkdir(self.dataPath)
            except:
                print('creating data folder failed')
                # todo: critical error should be handled somehow (exit app, inform user)
        # create and read Settings
        self.logger = logger.globalLogger.setPath(self.dataPath)
        self.settings = settings.mySettings.setPath(self.dataPath)
        self.styleSheetHandler = style.StyleSheetHandler(self)
        self.styleSheetHandler.setPath(self.appPath)
        style.myStyle = self.styleSheetHandler


    # setup window style
    def initWindow(self):
        self.logger.info('initializing window ...')
        #        self.setWindowFlags(qtcore.Qt.FramelessWindowHint)
        windowProps = self.settings.getWindowProperties()
        self.setWindowState(windowProps['state'])
        self.setGeometry(windowProps['geometry'])
        self.logger.info('window initialized')

    def initStyle(self):
        self.logger.info('initializing style ...')
        self.setWindowTitle(self.settings['window']['windowTitle'] + ' ' + self.settings['general']['version'])
        try:
            app_icon = qtgui.QIcon()
            app_icon.addFile(os.path.join(self.appPath, 'KoalaIcon.png'), qtcore.QSize(256, 256))
            self.setWindowIcon(app_icon)
        except Exception as ex:
            print(str(ex))
        try:
            self.setStyle(qtwidgets.QStyleFactory.create(self.settings['window']['windowstyle']))
        except Exception as ex:
            self.logger.error('window style is invalid: ' + str(ex))
            self.logger.info('using window style Fusion')
            self.setStyle(qtwidgets.QStyleFactory.create('Fusion'))
        # load stylesheet
        self.styleSheetHandler.loadSheet(self.settings['window']['stylesheetname'])
        self.logger.info('style initialized')

    def initData(self):
        self.logger.info('initializing data ...')
        self.logList = logger.QLogModel()
        self.settingsModel = settings.SettingsModel(self.settings)
        self.tradeList = ttable.QTradeTableModel(self.dataPath)
        self.coinList = ptable.QPortfolioTableModel()


        self.logger.newLogMessage.connect(lambda status, statusType: self.logList.addString(status, statusType))
        self.tradeList.tradesAdded.connect(lambda tradeList: self.coinList.addTrades(tradeList))
        self.tradeList.tradesRemoved.connect(lambda tradeList: self.coinList.deleteTrades(tradeList))
        self.tradeList.pricesUpdated.connect(self.coinList.histPricesChanged)
        self.tradeList.histPriceUpdateFinished.connect(self.coinList.histPriceUpdateFinished)
        self.logger.info('data initialized')


    # setup layout
    def layoutUI(self):
        self.logger.info('initializing gui layout ...')
        self.mainLayout = qtwidgets.QHBoxLayout(self)
        self.setContentsMargins(0, 0, 0, 0)

        # sidebar with buttons for pagecontrol
        self.sidebarFrame = qtwidgets.QFrame(self)
        self.sidebarFrame.setFrameShape(qtwidgets.QFrame.StyledPanel)
        self.sidebarFrame.setFrameShadow(qtwidgets.QFrame.Raised)
        self.sidebarFrame.setFixedWidth(120)

        # buttons sidebar
        self.buttonPortfolio = qtwidgets.QPushButton("", self.sidebarFrame)
        self.buttonTrades = qtwidgets.QPushButton("", self.sidebarFrame)
        self.buttonImport = qtwidgets.QPushButton("", self.sidebarFrame)
        self.buttonExport = qtwidgets.QPushButton("", self.sidebarFrame)
        self.buttonSettings = qtwidgets.QPushButton("", self.sidebarFrame)

        self.buttonPortfolio.setStyleSheet("QPushButton {border-image: url(" +
                                           os.path.join(self.appPath, 'graphics', 'portfolio.png').replace('\\', '/') +
                                           ") 0 15 0 15 stretch;}")
        self.buttonTrades.setStyleSheet("QPushButton {border-image: url(" +
                                           os.path.join(self.appPath, 'graphics', 'trades.png').replace('\\', '/') +
                                           ") 0 15 0 15 stretch;}")
        self.buttonImport.setStyleSheet("QPushButton {border-image: url(" +
                                           os.path.join(self.appPath, 'graphics', 'import.png').replace('\\', '/') +
                                           ") 0 15 0 15 stretch;}")
        self.buttonExport.setStyleSheet("QPushButton {border-image: url(" +
                                           os.path.join(self.appPath, 'graphics', 'export.png').replace('\\', '/') +
                                           ") 0 15 0 15 stretch;}")
        self.buttonSettings.setStyleSheet("QPushButton {border-image: url(" +
                                           os.path.join(self.appPath, 'graphics', 'settings.png').replace('\\', '/') +
                                           ") 0 15 0 15 stretch;}")

        self.buttonPortfolio.setToolTip('portfolio')
        self.buttonTrades.setToolTip('trades')
        self.buttonImport.setToolTip('import')
        self.buttonExport.setToolTip('export')
        self.buttonSettings.setToolTip('settings')

        self.buttonPortfolio.clicked.connect(lambda: self.showFrame(self.PORTFOLIOPAGEINDEX))
        self.buttonTrades.clicked.connect(lambda: self.showFrame(self.TRADESPAGEINDEX))
        self.buttonImport.clicked.connect(lambda: self.showFrame(self.IMPORTPAGEINDEX))
        self.buttonExport.clicked.connect(lambda: self.showFrame(self.EXPORTPAGEINDEX))
        self.buttonSettings.clicked.connect(lambda: self.showFrame(self.SETTINGSPAGEINDEX))
        buttonHeight = 120
        self.sidebarButtons = [self.buttonPortfolio, self.buttonTrades, self.buttonImport, self.buttonExport, self.buttonSettings]
        self.sidebarLayout = qtwidgets.QVBoxLayout(self.sidebarFrame)
        for button in (self.sidebarButtons):
            button.setFixedHeight(buttonHeight)
            #            button.setCheckable(True)
            self.sidebarLayout.addWidget(button)

        self.sidebarLayout.addStretch()

        # %% statusbar for displaying status and progress of ongoing actions
        self.statusbar = controls.StatusBar(self, height=80)
        self.statusbar.setModel(self.logList)

        # %%  stacked Layout for content frames
        self.portfolioPage = pages.PortfolioPage(parent=self, controller=self)
        self.tradesPage = pages.TradesPage(parent=self, controller=self)
        self.importPage = pages.ImportPage(parent=self, controller=self)
        self.exportPage = pages.ExportPage(parent=self, controller=self)
        self.settingsPage = pages.SettingsPage(parent=self, controller=self)
        self.pages = [self.portfolioPage, self.tradesPage, self.importPage, self.exportPage, self.settingsPage]
        self.stackedContentLayout = qtwidgets.QStackedLayout()
        for page in self.pages:
            # stacked content layout
            self.stackedContentLayout.addWidget(page)

        # put frames in vertical layout
        self.verticalFrameLayout = qtwidgets.QVBoxLayout()
        self.verticalFrameLayout.setSpacing(0)
        self.verticalFrameLayout.addLayout(self.stackedContentLayout)
        self.verticalFrameLayout.addWidget(self.statusbar)

        # put frames in horizontal layout
        self.horizontalFrameLayout = qtwidgets.QHBoxLayout()
        self.horizontalFrameLayout.addWidget(self.sidebarFrame)
        self.horizontalFrameLayout.addLayout(self.verticalFrameLayout)

        # put subLayouts in main layout
        self.mainLayout.addLayout(self.horizontalFrameLayout)

        self.logger.info('gui layout initialized')

    def startThreads(self):
        self.logger.info('starting threads ...')
        self.priceThread = threads.UpdatePriceThread(self.coinList, self.tradeList)
        self.priceThread.coinPricesLoaded.connect(lambda prices: self.coinList.setPrices(prices))
        self.priceThread.historicalPricesLoaded.connect(lambda prices, tradesLeft:
                                                        self.tradeList.setHistPrices(prices, tradesLeft))
        self.priceThread.start()
        self.logger.info('threads started')

    def showFrame(self, pageIndex):
        """Show a frame for the given page index"""
        frame = self.pages[pageIndex]
        frame.refresh()
        self.stackedContentLayout.setCurrentIndex(pageIndex)
        # reset color of all buttons in sidebar
        for buttonIndex in range(len(self.sidebarButtons)):
            button = self.sidebarButtons[buttonIndex]
            if buttonIndex == pageIndex:
                # do something with selected button
                #                button.config(bg=controls.changeColorBrightness(self.sidebar['bg'], 40))
                pass
            else:
                # do something with not selected buttons
                #                button.config(bg = self.sidebar['bg'])
                pass

    def closeEvent(self, event):
        # save window props
        geometry = self.geometry()
        state = self.windowState()
        self.settings.setWindowProperties(geometry, state)
        # save gui props
        self.settings.setGuiSettings(self.tradesPage.getGuiProps())
        self.settings.setGuiSettings(self.portfolioPage.getGuiProps())
        self.settings.saveSettings()
        event.accept()

    def printStatus(self, status, statusType='i'):
        self.logList.addString(status)

    # get TradeList
    def getTradeList(self):
        return self.tradeList()

    # get CoinList
    def getCoinList(self):
        return self.coinList


def main():
    coreLogger.globalLogger = logger.globalLogger
    coreSettings.mySettings = settings.mySettings
    app = qtwidgets.QApplication(sys.argv)
    #    app.setStyle(qtwidgets.QStyleFactory.create('Fusion'))
    window = PortfolioApp()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
